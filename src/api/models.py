from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    source_filter: str | None = None
    date_filter: str | None = None
    conversation_id: int | None = None
    user_id: int | None = None
    top_k: int | None = None



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
    user_id: int | None = None 

class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str
