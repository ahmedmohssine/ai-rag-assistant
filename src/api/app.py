import sys
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.api.services import rag
from src.api.models import (
    ChatRequest, 
    ChatResponse, 
    Source, 
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
)




app = FastAPI(
    title="AI RAG Assistant",
    version="1.0.0",
)

initialize_database()

@app.get("/conversations")
def conversations():
    return get_conversations()

@app.delete("/conversation/{conversation_id}")
def delete_chat(conversation_id: int):

    delete_conversation(conversation_id)

    return {"success": True}

@app.get("/history/{conversation_id}")
def history(conversation_id: int):
    return get_messages(conversation_id)

@app.post("/chat/stream")
def chat_stream(request: ChatRequest):

    results = rag.retriever.retrieve(request.question)

    if not results["is_confident"]:

        return StreamingResponse(
            iter(["I don't know based on the available documentation."]),
            media_type="text/plain",
        )

    context = ""

    for doc, meta in zip(
        results["documents"][0],
        results["metadatas"][0],
    ):

        context += (
            f"Document: {meta['path']}\n"
            f"{doc}\n\n"
        )

    def stream():
        for chunk in rag.generator.generate_stream(
            request.question,
            context,
        ):
            yield chunk

    return StreamingResponse(
        stream(),
        media_type="text/plain",
    )

@app.post("/chat", response_model=ChatResponse)

def chat(request: ChatRequest):
    if request.conversation_id is None:

        title = (
            request.question
            if len(request.question) <= 50
            else request.question[:47] + "..."
        )

        conversation_id = create_conversation(title)

    else:
        conversation_id = request.conversation_id

    user_message_id = add_message(
        conversation_id,
        "user",
        request.question,
    )
    results = rag.retriever.retrieve(request.question)

    if not results["is_confident"]:
        return ChatResponse(
            answer="I don't know based on the available documentation.",
            confidence=results["confidence"],
            sources=[],
        )

    context = ""

    for doc, meta in zip(
        results["documents"][0],
        results["metadatas"][0],
    ):
        context += (
            f"Document: {meta['path']}\n"
            f"{doc}\n\n"
        )

    answer = rag.generator.generate(
        request.question,
        context,
    )

    seen = set()
    sources = []

    for meta in results["metadatas"][0]:

        path = meta["path"]

        if path in seen:
            continue

        seen.add(path)

        sources.append(
            Source(document=path, url=meta.get("url"))
        )

    assistant_message_id = add_message(
        conversation_id,
        "assistant",
        answer,
        results["confidence"],
        sources=[
            {
                "document": source.document,
                "url": source.url,
            }
            for source in sources
        ],
    )
    
    

    return ChatResponse(
        answer=answer,
        confidence=results["confidence"],
        conversation_id=conversation_id,
        assistant_message_id=assistant_message_id,
        sources=sources,
    )
@app.post("/feedback")
def feedback(request: FeedbackRequest):

    add_feedback(
        conversation_id=request.conversation_id,
        message_id=request.message_id,
        rating=request.rating,
        comment=request.comment,
    )

    return {
        "success": True
    }

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

    return {
        "success": True,
        "user_id": user_id,
    }
