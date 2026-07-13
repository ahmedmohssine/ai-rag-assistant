from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


class Source(BaseModel):
    document: str
    url: str | None = None


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    conversation_id: int
    assistant_message_id: int
    sources: list[Source]

class FeedbackRequest(BaseModel):
    conversation_id: int
    message_id: int
    rating: str
    comment: str = ""   

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
