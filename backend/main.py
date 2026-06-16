import random
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.ai_clients.mock_client import MockAIClient
from backend.ai_clients.qwen_client import QwenAIClient
from backend.config import get_settings
from backend.demo_sentences import MEETING_SENTENCES

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMP_DIR = BASE_DIR / "backend" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SignX-Demo")
_last_demo_sentence_index = None


def get_program_client():
    settings = get_settings()
    if settings.ai_provider == "mock":
        return MockAIClient()
    if settings.ai_provider == "qwen":
        return QwenAIClient(settings)
    return None


def clean_suffix(filename: str | None) -> str:
    suffix = Path(filename or "recording.webm").suffix.lower()
    return suffix if suffix in {".webm", ".mp4", ".mov", ".m4v"} else ".webm"


@app.post("/api/analyze-sign")
async def analyze_sign(file: UploadFile = File(...)):
    suffix = clean_suffix(file.filename)
    save_path = TEMP_DIR / f"program_upload{suffix}"

    content = await file.read()
    save_path.write_bytes(content)

    try:
        client = get_program_client()
        if client is None:
            settings = get_settings()
            return {
                "error": f"Unsupported AI_PROVIDER '{settings.ai_provider}'. Please use AI_PROVIDER=qwen or AI_PROVIDER=mock."
            }
        return await client.analyze_sign_video(str(save_path))
    finally:
        save_path.unlink(missing_ok=True)


@app.post("/api/demo-meeting")
async def demo_meeting(file: UploadFile = File(...)):
    suffix = clean_suffix(file.filename)
    save_path = TEMP_DIR / f"latest_demo_upload{suffix}"

    content = await file.read()
    save_path.write_bytes(content)

    global _last_demo_sentence_index
    sentence_index = random.randrange(len(MEETING_SENTENCES))
    if len(MEETING_SENTENCES) > 1:
        while sentence_index == _last_demo_sentence_index:
            sentence_index = random.randrange(len(MEETING_SENTENCES))

    _last_demo_sentence_index = sentence_index
    return MEETING_SENTENCES[sentence_index]


@app.get("/api/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "program_provider": settings.ai_provider,
        "demo_mode": "available",
    }


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")
