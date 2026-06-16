import random
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.ai_clients.keypoint_client import KeypointAIClient
from backend.ai_clients.mock_client import MockAIClient
from backend.ai_clients.qwen_client import QwenAIClient
from backend.config import get_settings
from backend.demo_sentences import MEETING_SENTENCES
from backend.keypoint_recognition.extractor import NoHandsDetectedError, extract_keypoint_sequence
from backend.keypoint_recognition.templates import TEMPLATE_DIR, allowed_labels

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMP_DIR = BASE_DIR / "backend" / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SignX-Demo")
_last_demo_sentence_index = None


def get_program_client():
    settings = get_settings()
    if settings.ai_provider == "mock":
        return MockAIClient()
    if settings.ai_provider == "qwen":
        return QwenAIClient(settings)
    if settings.ai_provider == "keypoint":
        return KeypointAIClient()
    return None


def clean_suffix(filename: str | None) -> str:
    suffix = Path(filename or "recording.webm").suffix.lower()
    return suffix if suffix in {".webm", ".mp4", ".mov", ".m4v"} else ".webm"


def safe_label(label: str) -> str:
    return "".join(char for char in label.strip().lower() if char.isalnum() or char in {"-", "_"})


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
                "error": f"Unsupported AI_PROVIDER '{settings.ai_provider}'. Please use AI_PROVIDER=qwen, AI_PROVIDER=keypoint or AI_PROVIDER=mock."
            }
        return await client.analyze_sign_video(str(save_path))
    finally:
        save_path.unlink(missing_ok=True)


@app.post("/api/record-template")
async def record_template(label: str = Form(...), file: UploadFile = File(...)):
    normalized_label = safe_label(label)
    if normalized_label not in allowed_labels():
        return {
            "error": f"Unsupported label '{label}'. Allowed labels: {', '.join(sorted(allowed_labels()))}."
        }

    suffix = clean_suffix(file.filename)
    upload_path = TEMP_DIR / f"template_record_{normalized_label}{suffix}"

    content = await file.read()
    upload_path.write_bytes(content)

    try:
        sequence = extract_keypoint_sequence(str(upload_path))
        try:
            import numpy as np
        except ImportError as exc:
            return {"error": "numpy is required to save keypoint templates. Please run setup.bat or run.bat."}

        template_path = TEMPLATE_DIR / f"{normalized_label}_{int(time.time())}.npy"
        np.save(template_path, sequence)
        return {
            "label": normalized_label,
            "template_file": template_path.name,
            "frames": int(sequence.shape[0]),
            "features": int(sequence.shape[1]),
            "message": "Template recorded successfully.",
        }
    except NoHandsDetectedError:
        return {"error": "No hands detected in uploaded video. Please record a clearer template."}
    except RuntimeError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Template recording failed: {exc}"}
    finally:
        upload_path.unlink(missing_ok=True)


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
        "keypoint_templates": len(list(TEMPLATE_DIR.glob("*.npy"))),
    }


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")
