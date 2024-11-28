from pydantic import BaseModel, Field
from typing import List

class GiftSuggestion(BaseModel):
    summary: str = Field(
        description="A brief 2-3 sentence analysis of the recipient's personality and interests"
    )
    suggestions: List[str] = Field(
        description="Specific gift ideas within the budget",
        min_items=4,
        max_items=5
    )
