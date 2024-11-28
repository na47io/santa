import os
from typing import Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def process_answers(answers: dict, budget: int) -> dict:
    """Process the answers using OpenAI API and return structured gift suggestions"""

    # Combine all answers into a coherent prompt
    answers_text = "\n".join([f"Q{k[1:]}: {v}" for k, v in answers.items()])

    prompt = f"""Based on these responses about a gift recipient:

{answers_text}

Budget: ${budget}

Analyze these responses and provide gift suggestions in this exact JSON format:
{{
    "summary": "A brief 2-3 sentence analysis of the recipient's personality and interests",
    "suggestions": [
        "4-5 specific gift ideas, each within the ${budget} budget"
    ]
}}

Make suggestions specific, actionable, and tied to the actual responses. Include price ranges."""

    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a thoughtful gift advisor who carefully analyzes relationships to suggest meaningful gifts. Follow this step-by-step process:

1. First, identify key personality traits and interests from the answers
2. Look for emotional connections and shared experiences
3. Note any specific mentions of brands, items, or wishes
4. Consider their daily habits and routines
5. Think about both practical and sentimental value
6. Match gift ideas to their exact interests and the given budget
7. Ensure suggestions are specific (include brands, models, or types)
8. Consider how each gift connects to the information provided

Aim for suggestions that show you've really understood their personality and relationship dynamics."""
                },
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "gift_suggestions",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "A brief 2-3 sentence analysis of the recipient's personality and interests",
                            },
                            "suggestions": {
                                "type": "array",
                                "description": "Specific gift ideas within the budget",
                                "items": {"type": "string"},
                                "minItems": 4,
                                "maxItems": 5,
                            },
                        },
                        "required": ["summary", "suggestions"],
                        "additionalProperties": False,
                    },
                },
            },
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        # Parse and return the response
        return response.choices[0].message.content

    except Exception as e:
        # Fallback response in case of API error
        raise e
