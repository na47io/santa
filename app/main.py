from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.sessions import SessionMiddleware
from pathlib import Path
import json
from typing import Dict, Optional
import secrets

app = FastAPI()

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    session_cookie="gift_session",
    max_age=86400  # 24 hours
)

# Mount static files
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Sample questions - in real app this might come from a database
questions = [
    "What's the story of how you met, and what was the first gift you ever exchanged? How did they react to it?",
    
    "Think about the music you share - what concert or artist would they drop everything to see live? Any specific memories attached to certain songs?",
    
    "When it comes to their interests, what hobby or activity makes them completely light up? What gear or tools are they constantly researching?",
    
    "Tell me about their workspace or creative space - what tools or items do they use daily? What do they wish they had to make their process better?",
    
    "What's that one inside joke or shared experience that defines your relationship? How could that be translated into a tangible item?",
    
    "Think about their daily routines and habits - what's something they consistently enjoy or a problem they frequently mention wanting to solve?",
    
    "What's the most successful gift you've given them in the past? Why did it resonate so well?",
    
    "When you're hanging out together, what activities or experiences bring out their most genuine joy?",
    
    "What's a skill or interest they've mentioned wanting to explore but haven't taken the plunge on yet?",
    
    "Consider their style and aesthetic preferences - what brands or designs consistently catch their eye?",
    
    "What's a challenge or goal they're currently working towards? How could a gift support that journey?",
    
    "Think about your shared memories - what location, activity, or experience holds special meaning for both of you?",
    
    "What's their relationship with technology? Are they early adopters, minimalists, or somewhere in between?",
    
    "In your shared history, what's a moment they frequently reference or a story they love retelling?",
    
    "What's their approach to self-care and relaxation? What helps them unwind after a long day?"
]

@app.get("/")
async def home(request: Request):
    # Get existing answers from session
    session = request.session
    saved_answers = session.get("answers", {})
    saved_budget = session.get("budget")
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "questions": questions,
            "saved_answers": saved_answers,
            "saved_budget": saved_budget
        }
    )

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
            f"A premium subscription to their favorite creative software (within ${budget} budget)"
        ]
    }

@app.post("/submit")
async def submit_answers(request: Request):
    form_data = await request.form()
    
    # Extract answers and budget
    answers = {}
    budget = None
    
    for key, value in form_data.items():
        if key == "budget":
            budget = int(value)
        else:
            answers[key] = value
    
    # Store in session
    request.session["answers"] = answers
    request.session["budget"] = budget
    
    # Get suggestions and summary
    result = process_answers(answers, budget)
    
    return templates.TemplateResponse(
        "results.html",
        {"request": request, "summary": result["summary"], "suggestions": result["suggestions"]}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
