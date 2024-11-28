import os
from openai import OpenAI
from dotenv import load_dotenv
from .schema import GiftSuggestion, QuestionResponse

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def create_questions(relationship_type: str) -> QuestionResponse:
    """
    Provide a set of questions based on the relationship type
    """

    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": """You are an empathetic gift advisor helping people find meaningful presents. Your role is to generate questions that uncover gift ideas by understanding relationships and shared experiences.

Each question you generate should:
- Be brief and conversational (max 15 words)
- Focus on discovering shared experiences, habits, and interests
- Help surface potential gift ideas naturally
- Include realistic example answers showing desired detail level
- Avoid overly personal topics inappropriate for the relationship type

Consider relationship-specific elements like:
- Typical shared activities for this relationship type
- Common interaction patterns and boundaries
- Appropriate gift price ranges
- Relationship-specific traditions
""",
            },
            {
                "role": "user",
                "content": f"""Generate 10 questions to help someone find a gift for their {relationship_type}.""",
            },
        ],
        response_format=QuestionResponse,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    return response.choices[0].message.parsed


def process_answers(answers: dict, budget: int) -> dict:
    """Process the answers using OpenAI API and return structured gift suggestions"""

    # Combine all answers into a coherent prompt
    answers_text = "\n".join([f"Q{k[1:]}: {v}" for k, v in answers.items()])

    # Call OpenAI API
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": """You are a thoughtful gift advisor who carefully analyzes the provided answers to suggest meaningful gifts. Follow these strict guidelines:

1. ONLY use information explicitly mentioned in the answers - do not make assumptions
2. Focus on specific items, brands, or experiences directly referenced
3. Pay special attention to:
   - Concrete examples of things they enjoy
   - Past gifts that worked well
   - Specific items they've mentioned wanting
   - Activities they've explicitly shown interest in
4. When suggesting gifts:
   - Each suggestion must directly link to information provided in the answers
   - Stay within the specified budget
   - Be specific with suggestions (brands, models, types)
   - Explain how each gift connects to their stated interests

Do not infer traits or interests that aren't directly supported by the answers. If insufficient information is provided, acknowledge this in your suggestions.""",
                },
                {
                    "role": "user",
                    "content": f"""Based on these responses about a gift recipient:
{answers_text}

Budget: ${budget}

Analyze these responses and provide gift suggestions in this exact JSON format:
{{
    "summary": "A brief 2-3 sentence analysis of the recipient's personality and interests",
    "suggestions": [
        "4-5 specific gift ideas, each within the ${budget} budget"
    ]
}}

Make suggestions specific, actionable, and tied to the actual responses. Include price ranges.""",
                },
            ],
            response_format=GiftSuggestion,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        # Parse and return the response
        return response.choices[0].message.parsed

    except Exception as e:
        raise e
