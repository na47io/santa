from pydantic import BaseModel


class GiftSuggestion(BaseModel):
    summary: str
    suggestions: list[str]
