from backend.ai_clients.base import BaseAIClient


class MockAIClient(BaseAIClient):
    async def analyze_sign_video(self, video_path: str) -> dict:
        return {
            "meaning": "你好",
            "confidence": 0.92,
            "spoken_text": "你好，很高兴见到你。",
        }
