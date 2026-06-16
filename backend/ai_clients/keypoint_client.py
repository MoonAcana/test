from backend.ai_clients.base import BaseAIClient
from backend.keypoint_recognition.extractor import NoHandsDetectedError, extract_keypoint_sequence
from backend.keypoint_recognition.matcher import NoTemplatesError, match_to_response
from backend.keypoint_recognition.templates import UNKNOWN_RESULT


class KeypointAIClient(BaseAIClient):
    async def analyze_sign_video(self, video_path: str) -> dict:
        try:
            sequence = extract_keypoint_sequence(video_path)
            return match_to_response(sequence)
        except NoHandsDetectedError:
            return UNKNOWN_RESULT.copy()
        except NoTemplatesError as exc:
            return {"error": str(exc)}
        except RuntimeError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            return {"error": f"Keypoint recognition failed: {exc}"}
