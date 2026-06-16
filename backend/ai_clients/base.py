class BaseAIClient:
    async def analyze_sign_video(self, video_path: str) -> dict:
        raise NotImplementedError
