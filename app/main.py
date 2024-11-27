from fastapi import FastAPI, Request, Form, Depends, Response
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

# Questions and their placeholders
questions_data = [
    {
        "question": "What's the story of how you met, and what was the first gift you ever exchanged? How did they react to it?",
        "placeholder": "We met at a coffee shop and I gave them a book they mentioned. Their eyes lit up when they saw it was a first edition..."
    },
    {
        "question": "Think about the music you share - what concert or artist would they drop everything to see live? Any specific memories attached to certain songs?",
        "placeholder": "They're obsessed with Taylor Swift and we always sing 'All Too Well' together. They've never seen her live..."
    },
    {
        "question": "When it comes to their interests, what hobby or activity makes them completely light up? What gear or tools are they constantly researching?",
        "placeholder": "They're really into film photography lately and keep browsing vintage cameras online..."
    },
    {
        "question": "Tell me about their workspace or creative space - what tools or items do they use daily? What do they wish they had to make their process better?",
        "placeholder": "They work from home and always complain about their desk chair. They've mentioned wanting a standing desk..."
    },
    {
        "question": "What's that one inside joke or shared experience that defines your relationship? How could that be translated into a tangible item?",
        "placeholder": "We always joke about that time we got lost hiking and saw that weird purple mushroom..."
    },
    {
        "question": "Think about their daily routines and habits - what's something they consistently enjoy or a problem they frequently mention wanting to solve?",
        "placeholder": "They're always running late in the mornings and wish they had a better coffee setup at home..."
    },
    {
        "question": "What's the most successful gift you've given them in the past? Why did it resonate so well?",
        "placeholder": "The custom playlist I made them last year - they loved how personal it was and still listen to it..."
    },
    {
        "question": "When you're hanging out together, what activities or experiences bring out their most genuine joy?",
        "placeholder": "They're happiest when we're cooking together, especially trying new recipes..."
    },
    {
        "question": "What's a skill or interest they've mentioned wanting to explore but haven't taken the plunge on yet?",
        "placeholder": "They keep talking about wanting to learn to paint but haven't bought any supplies yet..."
    },
    {
        "question": "Consider their style and aesthetic preferences - what brands or designs consistently catch their eye?",
        "placeholder": "They love minimalist Scandinavian design and always stop to look at Marimekko patterns..."
    },
    {
        "question": "What's a challenge or goal they're currently working towards? How could a gift support that journey?",
        "placeholder": "They're training for their first marathon and need better gear for running in winter..."
    },
    {
        "question": "Think about your shared memories - what location, activity, or experience holds special meaning for both of you?",
        "placeholder": "That beach where we had our first date - we always talk about going back there..."
    },
    {
        "question": "What's their relationship with technology? Are they early adopters, minimalists, or somewhere in between?",
        "placeholder": "They love trying new gadgets but prefer ones that solve real problems rather than just being flashy..."
    },
    {
        "question": "In your shared history, what's a moment they frequently reference or a story they love retelling?",
        "placeholder": "They always talk about that time we spontaneously drove to that midnight movie premiere..."
    },
    {
        "question": "What's their approach to self-care and relaxation? What helps them unwind after a long day?",
        "placeholder": "They love taking long baths with fancy bath bombs and reading mystery novels..."
    }
]

@app.get("/up")
async def health_check():
    """Health check endpoint that always returns 200 OK"""
    return Response(status_code=200)


@app.get("/")
async def home(request: Request):
    saved_answers = {}
    saved_budget = None
    saved_step = 1
    
    # Try to get existing session
    session_id = cookie(request)
    if session_id:
        session_data = await backend.read(session_id)
        if session_data:
            saved_answers = session_data.answers
            saved_budget = session_data.budget
            saved_step = session_data.current_step
        else:
            # Create new session if we have ID but no data
            session_data = SessionData()
            await backend.create(session_id, session_data)
    else:
        # Create new session if no ID exists
        session_id = uuid4()
        session_data = SessionData()
        await backend.create(session_id, session_data)

    print("FUUUUUUUUUU")
    print(session_id, session_data)
    
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "questions_data": questions_data,
            "saved_answers": saved_answers,
            "saved_budget": saved_budget,
            "saved_step": saved_step
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
    
    # Extract answers, budget and current step
    answers = {}
    budget = None
    current_step = 1
    
    for key, value in form_data.items():
        if key == "budget":
            try:
                budget = int(value)
            except (ValueError, TypeError):
                pass
        elif key == "current_step":
            try:
                current_step = int(value)
            except (ValueError, TypeError):
                pass
        else:
            answers[key] = value
    
    # Create or update session
    session_data = SessionData(answers=answers, budget=budget, current_step=current_step)
    
    if not session_id:
        session_id = uuid4()
        await backend.create(session_id, session_data)
    else:
        try:
            await backend.update(session_id, session_data)
        except:
            # If update fails, create new session
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
        await backend.create(session_id, session_data)
    else:
        try:
            await backend.update(session_id, session_data)
        except:
            # If update fails, create new session
            await backend.create(session_id, session_data)
    
    # Get suggestions and summary
    result = process_answers(answers, budget)
    
    # Clear all form state from session
    if session_id:
        # Create empty session data with default values
        empty_session = SessionData()
        await backend.update(session_id, empty_session)
    
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
