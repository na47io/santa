from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# Mount static files
static_path = Path(__file__).parent / "static"
templates_path = Path(__file__).parent / "templates"

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
templates = Jinja2Templates(directory=str(templates_path))

# Sample questions - in real app this might come from a database
questions = [
    "What is your main business challenge?",
    "What solutions have you tried before?",
    "What is your ideal outcome?",
]

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "questions": questions}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
