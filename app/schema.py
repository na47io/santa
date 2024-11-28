from pydantic import BaseModel


class GiftItem(BaseModel):
    emoji: str
    title: str
    description: str
    price_range: str
    category: str

class GiftSuggestion(BaseModel):
    summary: str
    suggestions: list[GiftItem]


class Question(BaseModel):
    question: str
    placeholder: str

    def dict(self, *args, **kwargs):
        return {
            "question": self.question,
            "placeholder": self.placeholder
        }


class QuestionResponse(BaseModel):
    questions: list[Question]

    def dict(self, *args, **kwargs):
        return {
            "questions": [q.dict() for q in self.questions]
        }
