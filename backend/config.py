from dataclasses import dataclass
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    ai_provider: str
    dashscope_api_key: str
    qwen_model: str


def get_settings() -> Settings:
    return Settings(
        ai_provider=os.getenv("AI_PROVIDER", "qwen").strip().lower() or "qwen",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", "").strip(),
        # qwen-vl-plus is a convenient default for this demo. If it is unavailable
        # in your Alibaba Cloud Model Studio account, replace it with a supported
        # video-capable Qwen multimodal model name from the Bailian console/docs.
        qwen_model=os.getenv("QWEN_MODEL", "qwen-vl-plus").strip() or "qwen-vl-plus",
    )
