from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from uuid import UUID, uuid4
from .session import (
    SessionData,
    cookie,
    backend,
    verifier
)

app = FastAPI()

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
    saved_answers = {}
    saved_budget = None
    
    # Try to get existing session
    session_id = None
    try:
        session_id = await cookie(request)
        if session_id:
            session_data = await backend.read(session_id)
            if session_data:
                saved_answers = session_data.answers
                saved_budget = session_data.budget
    except:
        pass
    
    # Create new session if none exists
    if not session_id:
        session_id = uuid4()
        session_data = SessionData()
        await backend.create(session_id, session_data)

    
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "questions": questions,
            "saved_answers": saved_answers,
            "saved_budget": saved_budget
        }
    )
    cookie.attach_to_response(response, session_id)
    return response

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

@app.post("/autosave")
async def autosave(
    request: Request,
    session_id: UUID | None = Depends(cookie)
):
    form_data = await request.json()
    
    # Extract answers and budget
    answers = {}
    budget = None
    
    for key, value in form_data.items():
        if key == "budget":
            try:
                budget = int(value)
            except (ValueError, TypeError):
                pass
        else:
            answers[key] = value
    
    # Create or update session
    session_data = SessionData(answers=answers, budget=budget)
    
    if not session_id:
        session_id = uuid4()
    
    # Delete existing session if it exists
    try:
        await backend.delete(session_id)
    except:
        pass
        
    # Create new session
    await backend.create(session_id, session_data)
    
    response = JSONResponse(content={"status": "success"})
    cookie.attach_to_response(response, session_id)
    return response

@app.post("/submit")
async def submit_answers(
    request: Request,
    session_id: UUID | None = Depends(cookie)
):
    form_data = await request.form()
    
    # Extract answers and budget
    answers = {}
    budget = None
    
    for key, value in form_data.items():
        if key == "budget":
            budget = int(value)
        else:
            answers[key] = value
    
    # Create or update session
    session_data = SessionData(answers=answers, budget=budget)
    
    if not session_id:
        session_id = uuid4()
    
    # Delete existing session if it exists
    try:
        await backend.delete(session_id)
    except:
        pass
        
    # Create new session
    await backend.create(session_id, session_data)
    
    # Get suggestions and summary
    result = process_answers(answers, budget)
    
    response = RedirectResponse(url="/results", status_code=303)
    cookie.attach_to_response(response, session_id)
    return response

@app.get("/results")
async def view_results(
    request: Request,
    session_id: UUID = Depends(cookie)
):
    session_data = await backend.read(session_id)
    if not session_data:
        return RedirectResponse(url="/")
        
    result = process_answers(session_data.answers, session_data.budget)
    
    return templates.TemplateResponse(
        "results.html",
        {"request": request, "summary": result["summary"], "suggestions": result["suggestions"]}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
