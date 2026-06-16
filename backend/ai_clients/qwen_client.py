import asyncio
import json
import re
from pathlib import Path

from backend.ai_clients.base import BaseAIClient
from backend.config import Settings
from backend.sign_phrases import SIGN_PHRASES


class QwenAIClient(BaseAIClient):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def analyze_sign_video(self, video_path: str) -> dict:
        if not self.settings.dashscope_api_key:
            return {
                "error": "DASHSCOPE_API_KEY is missing. Please set it in .env or switch AI_PROVIDER=mock."
            }

        try:
            return await asyncio.to_thread(self._call_dashscope, video_path)
        except ImportError:
            return {
                "error": "dashscope package is not installed. Please run setup.bat to install dependencies."
            }
        except Exception as exc:
            return {"error": f"Qwen API request failed: {exc}"}

    def _call_dashscope(self, video_path: str) -> dict:
        import dashscope
        from dashscope import MultiModalConversation

        dashscope.api_key = self.settings.dashscope_api_key
        prompt = self._build_prompt()
        video_uri = Path(video_path).resolve().as_uri()

        messages = [
            {
                "role": "user",
                "content": [
                    {"video": video_uri},
                    {"text": prompt},
                ],
            }
        ]

        response = MultiModalConversation.call(
            model=self.settings.qwen_model,
            messages=messages,
            result_format="message",
        )

        status_code = self._get_response_value(response, "status_code", 200)
        if status_code != 200:
            code = self._get_response_value(response, "code", "unknown")
            message = self._get_response_value(response, "message", str(response))
            raise RuntimeError(f"{code}: {message}")

        content = self._get_message_content(response)
        text = self._extract_text(content)
        parsed = self._parse_json(text)
        return self._normalize_result(parsed)

    def _build_prompt(self) -> str:
        candidates = "\n".join(
            f"{index}. {phrase}" for index, phrase in enumerate(SIGN_PHRASES, start=1)
        )
        return f"""你是 SignX 桌面式手语语音翻译终端的程序模式识别模块。

请观察视频中用户的手部动作、手臂动作、身体姿态和面部表情，判断这段手语表达最接近下面哪一个含义。

候选含义：

{candidates}

要求：

* 只能从候选含义中选择一个。
* 如果动作不清楚、画面中没有明显手语动作，返回“无法识别，请重新录制”。
* 不要输出分析过程。
* 不要输出 Markdown。
* 只返回 JSON。
* JSON 必须包含 meaning、confidence、spoken_text 三个字段。
* confidence 是 0 到 1 之间的小数。
* spoken_text 是适合电脑扬声器播报的自然中文句子。

返回格式示例：

{{
  "meaning": "我同意这个方案",
  "confidence": 0.86,
  "spoken_text": "我同意这个方案，可以继续推进。"
}}"""

    def _get_response_value(self, response, key: str, default=None):
        if isinstance(response, dict):
            return response.get(key, default)
        return getattr(response, key, default)

    def _get_message_content(self, response):
        if isinstance(response, dict):
            return response["output"]["choices"][0]["message"]["content"]
        return response.output.choices[0].message.content

    def _extract_text(self, content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        parts.append(str(item["text"]))
                    elif "content" in item:
                        parts.append(str(item["content"]))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    def _parse_json(self, text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.S)
            if not match:
                raise ValueError(f"Qwen returned non-JSON content: {text}")
            return json.loads(match.group(0))

    def _normalize_result(self, result: dict) -> dict:
        meaning = str(result.get("meaning", "无法识别，请重新录制")).strip()
        if meaning not in SIGN_PHRASES:
            meaning = "无法识别，请重新录制"

        try:
            confidence = float(result.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        spoken_text = str(result.get("spoken_text", "")).strip()
        if not spoken_text:
            spoken_text = meaning

        return {
            "meaning": meaning,
            "confidence": confidence,
            "spoken_text": spoken_text,
        }
