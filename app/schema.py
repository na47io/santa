from pydantic import BaseModel


class GiftSuggestion(BaseModel):
    summary: str
    suggestions: list[str]


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
