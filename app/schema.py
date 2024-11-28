from pydantic import BaseModel


class GiftSuggestion(BaseModel):
    summary: str
    suggestions: list[str]


class Question(BaseModel):
    question: str
    placeholder: str


class QuestionResponse(BaseModel):
    questions: list[Question]
