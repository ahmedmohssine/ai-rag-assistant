import sys
import os
import json
import shutil
import subprocess
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, status, UploadFile, File, FastAPI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.indexing.vector_store import VectorStore
from src.api.auth_utils import create_access_token
from src.api.services import rag
from src.api.models import (
    ChatRequest,
    FeedbackRequest,
    RegisterRequest,
    LoginRequest,
)
from src.api.database import (
    initialize_database,
    create_conversation,
    add_message,
    get_conversations,
    get_messages,
    delete_conversation,
    add_feedback,
    create_user,
    verify_user,
    delete_user,
    verify_conversation_owner,
)

app = FastAPI(
    title="AI RAG Assistant",
    version="1.0.0",
)

initialize_database()

@app.get("/conversations")
def conversations(user_id: int):
    return get_conversations(user_id)

@app.delete("/conversation/{conversation_id}")
def delete_chat(conversation_id: int, user_id: int):
    success = delete_conversation(conversation_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this conversation."
        )
    return {"success": True}

@app.get("/history/{conversation_id}")
def history(conversation_id: int, user_id: int):
    return get_messages(conversation_id, user_id)

@app.post("/chat")
def chat(request: ChatRequest):
    # Automatically generate an LLM title if this is a fresh conversation
    if request.conversation_id is None:
        title = rag.generator.generate_title(request.question)
        conversation_id = create_conversation(title, user_id=request.user_id)
    else:
        conversation_id = request.conversation_id

    # Save the user's raw question to the database
    add_message(
        conversation_id,
        "user",
        request.question,
    )

    source = getattr(request, "source_filter", None)
    top_k = getattr(request, "top_k", 5) or 5

    # If a path filter is active, fetch a larger batch size so we have matching chunks left
    fetch_k = top_k * 3 if (source and source.strip()) else top_k
    
    results = rag.retriever.retrieve(
        request.question, 
        top_k=fetch_k
    )

    if not results["is_confident"]:
        def fallback_stream():
            yield "I don't know based on the available documentation."
            yield f"\n__METADATA__:{json.dumps({'conversation_id': conversation_id, 'assistant_message_id': None, 'confidence': results['confidence'], 'sources': []})}"
        return StreamingResponse(fallback_stream(), media_type="text/plain")

    # FIXED: Added [0] index to safely step past ChromaDB's outer batch list layer
    raw_docs = results["documents"][0] if results.get("documents") else []
    raw_metas = results["metadatas"][0] if results.get("metadatas") else []

    # Post-Filtering loop: Keep chunks matching the requested document path string
    filtered_documents = []
    filtered_metadatas = []
    
    for doc, meta in zip(raw_docs, raw_metas):
        if source and source.strip():
            meta_path = meta.get("path", "") if isinstance(meta, dict) else ""
            if source.lower() not in meta_path.lower():
                continue  # Skip document chunk if it doesn't match the path keyword
                
        filtered_documents.append(doc)
        filtered_metadatas.append(meta)
        
        if len(filtered_documents) == top_k:
            break

    # If filters are too restrictive and nothing passes, fallback to baseline top results
    if not filtered_documents:
        filtered_documents = raw_docs[:top_k]
        filtered_metadatas = raw_metas[:top_k]

    context = ""
    for doc, meta in zip(filtered_documents, filtered_metadatas):
        context += f"Document: {meta['path']}\n{doc}\n\n"

    seen = set()
    sources = []
    for meta in filtered_metadatas:
        if isinstance(meta, dict) and "path" in meta:
            path = meta["path"]
            if path in seen:
                continue
            seen.add(path)
            sources.append({"document": path, "url": meta.get("url")})

    def stream_response():
        full_answer = ""
        for chunk in rag.generator.generate_stream(request.question, context):
            full_answer += chunk
            yield chunk

        assistant_message_id = add_message(
            conversation_id,
            "assistant",
            full_answer,
            results["confidence"],
            sources=sources,
        )

        metadata_payload = {
            "conversation_id": conversation_id,
            "assistant_message_id": assistant_message_id,
            "confidence": results["confidence"],
            "sources": sources
        }
        yield f"\n__METADATA__:{json.dumps(metadata_payload)}"

    return StreamingResponse(stream_response(), media_type="text/plain")

@app.post("/feedback")
def feedback(request: FeedbackRequest):
    is_owner = verify_conversation_owner(request.conversation_id, request.user_id)
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit feedback for this conversation."
        )

    add_feedback(
        conversation_id=request.conversation_id,
        message_id=request.message_id,
        rating=request.rating,
        comment=request.comment,
    )
    return {"success": True}

@app.post("/register")
def register(request: RegisterRequest):

    success = create_user(
        request.email,
        request.password,
    )

    if not success:
        return {
            "success": False,
            "message": "Email already exists.",
        }

    return {
        "success": True,
    }

@app.post("/login")
def login(request: LoginRequest):

    user_id = verify_user(
        request.email,
        request.password,
    )

    if user_id is None:
        return {
            "success": False,
            "message": "Invalid email or password.",
        }

    # Generate a secure JWT token for this user
    token = create_access_token(user_id)

    return {
        "success": True,
        "user_id": user_id,
        "token": token  # Return the token to the frontend
    }

@app.delete("/user/{user_id}")
def delete_account(user_id: int):

    delete_user(user_id)

    return {
        "success": True,
    }

@app.post("/admin/upload")
def upload_documents(files: list[UploadFile] = File(...)):
    # 1. Clean out the temporary document ingestion corpus folder safely
    if os.path.exists("docs"):
        try:
            shutil.rmtree("docs")
        except PermissionError:
            pass 
    os.makedirs("docs", exist_ok=True)

    def event_stream():
        try:
            # Save all incoming file streams into the docs staging folder
            yield f"PROGRESS:10|Saving {len(files)} uploaded folder documents onto server...\n"
            for file in files:
                file_path = os.path.join("docs", file.filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

            # FIXED - Call native internal reset to bypass Windows OS file locks
            yield "PROGRESS:20|Wiping old analytical indices and collections cleanly...\n"
            
            # Reset ChromaDB data internally via the provided VectorStore API method
            if hasattr(rag, 'store') and rag.store is not None:
                if hasattr(rag.store, 'reset'):
                    rag.store.reset()
            
            # Build structural text splits 
            yield "PROGRESS:30|Running structure-aware text chunking splits...\n"
            subprocess.run([sys.executable, "scripts/build_chunks.py"], check=True)
            
            # Compute local embeddings
            yield "PROGRESS:70|Computing local SentenceTransformer embeddings to ChromaDB...\n"
            subprocess.run([sys.executable, "scripts/build_index.py"], check=True)
            
            # Reload context memory boundaries
            yield "PROGRESS:100|Refreshing active memory context store instances...\n"
            from src.indexing.vector_store import VectorStore
            rag.store = VectorStore()
            if hasattr(rag, 'retriever') and rag.retriever is not None:
                rag.retriever.store = rag.store
            
            yield f"SUCCESS:Successfully initialized database with {len(files)} context sources!\n"
            
        except subprocess.CalledProcessError as e:
            yield f"ERROR:Pipeline compilation script failed: {str(e)}\n"
        except Exception as e:
            yield f"ERROR:Unexpected processing ingestion crash: {str(e)}\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")