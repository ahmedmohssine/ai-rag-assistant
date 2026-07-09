from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class Source(BaseModel):
    document: str


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    conversation_id: int
    sources: list[Source]
