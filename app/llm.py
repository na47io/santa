def process_answers(answers: dict, budget: int) -> dict:
    """Process the answers and return gift suggestions with summary"""
    # This is a pass-through function for now
    # Later it will process the answers and generate real suggestions
    return {
        "summary": "Based on your responses, it seems like your recipient is creative, tech-savvy, and appreciates meaningful experiences. They have a strong connection to music and enjoy both practical and sentimental gifts. Here are some suggestions that align with their interests and your budget:",
        "suggestions": [
            f"A high-quality digital drawing tablet (within ${budget} budget)",
            f"Concert tickets for their favorite band's next tour (within ${budget} budget)",
            f"A custom photo album of your shared memories (within ${budget} budget)",
            f"A premium subscription to their favorite creative software (within ${budget} budget)",
        ],
    }
