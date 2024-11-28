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
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a thoughtful gift advisor who provides specific, personalized suggestions based on relationship details."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
            response_format={ "type": "json_object" }
        )
        
        # Parse and return the response
        return response.choices[0].message.content
        
    except Exception as e:
        # Fallback response in case of API error
        return {
            "summary": "We're having trouble processing your responses right now. Here are some general suggestions based on your input:",
            "suggestions": [
                f"A thoughtful experience or activity within ${budget}",
                f"A high-quality version of something they use daily (within ${budget})",
                f"A subscription to a service aligned with their interests",
                f"A customized or personalized item meaningful to your relationship"
            ]
        }