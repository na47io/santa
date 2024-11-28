import json
from fastapi import FastAPI, Request, Form, Depends, Response, Cookie, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy.orm import Session
from .session import SessionData, SessionManager, attach_session_id, get_session_id
from .database import get_db, SessionStore
from .llm import process_answers, create_questions

app = FastAPI()

# Mount static files
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))


@app.get("/up")
async def health_check():
    """Health check endpoint that always returns 200 OK"""
    return Response(status_code=200)


@app.get("/")
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/questions")
async def questions(
    request: Request,
    recipient: str,
    session_id: Optional[UUID] = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    session_manager = SessionManager(db)
    session_id, session_data = await session_manager.get_session(
        str(session_id) if session_id else None
    )

    # Generate questions if not in session or recipient changed
    if not session_data.questions or session_data.recipient != recipient:
        questions_resp = create_questions(recipient)
        session_data.questions = jsonable_encoder(questions_resp.questions[:1])
        session_data.recipient = recipient
        await session_manager.update_session(session_id, session_data)

    response = templates.TemplateResponse(
        "questions.html",
        {
            "request": request,
            "questions_data": session_data.questions,
            "saved_answers": session_data.answers or {},
            "saved_budget": session_data.budget or 10,
            "saved_step": session_data.current_step or 1,
        },
    )
    attach_session_id(response, session_id)
    return response


@app.post("/autosave")
async def autosave(
    request: Request,
    session_id: Optional[UUID] = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    if not session_id:
        raise Exception("Session ID missing")

    form_data = await request.json()
    session_manager = SessionManager(db)
    _, session_data = await session_manager.get_session(str(session_id))

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

    # Update session data
    session_data.answers = answers
    session_data.budget = budget
    session_data.current_step = current_step

    await session_manager.update_session(session_id, session_data)

    response = JSONResponse(content={"status": "success"})
    attach_session_id(response, session_id)
    return response


@app.post("/submit")
async def submit_answers(
    request: Request,
    session_id: Optional[UUID] = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    if not session_id:
        raise Exception("Session ID missing")

    form_data = await request.form()
    session_manager = SessionManager(db)
    _, session_data = await session_manager.get_session(str(session_id))

    # Extract answers and budget
    answers = {}
    budget = None

    for key, value in form_data.items():
        if key == "budget":
            budget = int(value)
        else:
            answers[key] = value

    # Update session data
    session_data.answers = answers
    session_data.budget = budget

    await session_manager.update_session(session_id, session_data)

    response = RedirectResponse(url="/results", status_code=303)
    attach_session_id(response, session_id)
    return response


@app.get("/results")
async def view_results(
    request: Request,
    session_id: Optional[UUID] = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    if not session_id:
        return RedirectResponse(url="/")

    session_manager = SessionManager(db)
    _, session_data = await session_manager.get_session(str(session_id))

    if not session_data:
        return RedirectResponse(url="/")

    # Only process answers if we haven't already
    if not session_data.summary:
        result = process_answers(session_data.answers, session_data.budget)
        session_data.summary = result.summary
        session_data.suggestions = result.suggestions
        await session_manager.update_session(session_id, session_data)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "summary": session_data.summary,
            "suggestions": session_data.suggestions,
        },
    )


@app.get("/sessions")
async def view_sessions(request: Request, db: Session = Depends(get_db)):
    """Debug endpoint to view all stored sessions"""

    sessions = db.query(SessionStore).all()
    session_data = []

    for session in sessions:
        data = json.loads(session.data)
        session_data.append(
            {
                "id": session.id,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "data": data,
            }
        )

    return templates.TemplateResponse(
        "debug_sessions.html", {"request": request, "sessions": session_data}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
