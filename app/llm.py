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
                "content": """You are an insightful and empathetic gift advisor who helps people discover deeply meaningful presents by understanding the nuanced dynamics of their relationships. Your role is to generate questions that go beyond surface-level preferences to uncover the emotional connections, shared memories, and unique aspects of their bond.

Each question you generate should:
- Be personal and thought-provoking, encouraging reflection
- Focus on specific moments, memories, and emotional connections
- Explore the unique dynamics and inside jokes of their relationship
- Uncover hidden interests and aspirations they've shared
- Draw out stories that reveal their shared history
- Help understand how they support and appreciate each other

Examples of deep-diving questions:
- "What's a small gesture they do that always makes you smile?"
- "Tell me about a time they helped you through something difficult"
- "What's a conversation with them you'll never forget?"
- "What dream or goal have they mentioned wanting to pursue?"
- "What's something they collect or take special care of?"

Avoid:
- Generic questions about likes/dislikes
- Simple yes/no questions
- Overly broad topics
- Surface-level preferences
- Inappropriate personal boundaries

Tailor questions to relationship context:
- Parent: childhood memories, family traditions, life lessons
- Partner: shared dreams, daily rituals, growth moments
- Friend: adventures together, mutual support, inside jokes
- Colleague: professional aspirations, workplace dynamics
- Sibling: childhood bonds, family roles, shared experiences

Each question should open a window into a specific aspect of their relationship that could inspire truly meaningful gift ideas.""",
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
   - Include an appropriate emoji for each gift
   - Categorize each gift appropriately
   - Provide clear price ranges within budget

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
        {{
            "emoji": "🎁",
            "title": "Specific gift name/brand",
            "description": "Detailed description explaining why this gift matches their interests",
            "price_range": "Price range in USD",
            "category": "Gift category (e.g., Electronics, Books, Experience, etc.)"
        }}
    ]
}}

Provide 4-5 specific gift suggestions, each within the ${budget} budget. Make them actionable and tied to the actual responses.""",
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
