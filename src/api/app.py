import sys
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from src.api.models import ChatRequest, ChatResponse, Source
from src.api.services import rag
from src.api.database import (
    initialize_database,
    create_conversation,
    add_message,
    get_history,
    get_conversations,
    get_messages,
    delete_conversation,
)




app = FastAPI(
    title="AI RAG Assistant",
    version="1.0.0",
)

initialize_database()

@app.get("/history/{conversation_id}")
def history(conversation_id: int):
    return get_history(conversation_id)

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

    return StreamingResponse(
        rag.generator.generate_stream(
            request.question,
            context,
        ),
        media_type="text/plain",
    )

@app.post("/chat", response_model=ChatResponse)

def chat(request: ChatRequest):
    if request.conversation_id is None:
        conversation_id = create_conversation()
    else:
        conversation_id = request.conversation_id

    add_message(
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
    
    add_message(
        conversation_id,
        "assistant",
        answer,
        results["confidence"],
    )
    
    seen = set()
    sources = []

    for meta in results["metadatas"][0]:

        path = meta["path"]

        if path in seen:
            continue

        seen.add(path)

        sources.append(
            Source(document=path)
        )

    return ChatResponse(
        answer=answer,
        confidence=results["confidence"],
        conversation_id=conversation_id,
        sources=sources,
    )
