from fastapi import FastAPI, Request, Form, Depends, Response
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.encoders import jsonable_encoder
from pathlib import Path
from uuid import UUID, uuid4
from .session import SessionData, cookie, backend, verifier
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
async def questions(request: Request, recipient: str):
    saved_answers = {}
    saved_budget = None
    saved_step = 1

    # Try to get existing valid session
    session_id = None
    session_data = None

    try:
        existing_id = cookie(request)
        if existing_id:
            try:
                session_data = await backend.read(existing_id)
                if session_data:
                    session_id = existing_id
                    saved_answers = session_data.answers
                    saved_budget = session_data.budget
                    saved_step = session_data.current_step
            except:
                pass
    except:
        pass

    # Create new session if we don't have a valid one
    if not session_id or not session_data:
        session_id = uuid4()
        session_data = SessionData()
        await backend.create(session_id, session_data)

    questions_resp = create_questions(recipient)

    response = templates.TemplateResponse(
        "questions.html",
        {
            "request": request,
            "questions_data": jsonable_encoder(questions_resp.questions),
            "saved_answers": saved_answers,
            "saved_budget": saved_budget,
            "saved_step": saved_step,
        },
    )
    cookie.attach_to_response(response, session_id)
    return response


@app.post("/autosave")
async def autosave(request: Request, session_id: UUID | None = Depends(cookie)):
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
    session_data = SessionData(
        answers=answers, budget=budget, current_step=current_step
    )

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
async def submit_answers(request: Request, session_id: UUID | None = Depends(cookie)):
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

    response = RedirectResponse(url="/results", status_code=303)
    cookie.attach_to_response(response, session_id)
    return response


@app.get("/results")
async def view_results(request: Request, session_id: UUID = Depends(cookie)):
    session_data = await backend.read(session_id)
    if not session_data:
        return RedirectResponse(url="/")

    result = process_answers(session_data.answers, session_data.budget)

    # Clear all form state from session
    if session_id:
        # Create empty session data with default values
        empty_session = SessionData()
        await backend.update(session_id, empty_session)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "summary": result.summary,
            "suggestions": result.suggestions,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
