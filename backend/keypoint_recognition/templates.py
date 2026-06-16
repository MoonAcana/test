from pathlib import Path

SIGN_TEMPLATE_RESPONSES = {
    "hello": {
        "meaning": "你好",
        "spoken_text": "你好，很高兴见到你。",
    },
    "thanks": {
        "meaning": "谢谢",
        "spoken_text": "谢谢大家的建议。",
    },
    "agree": {
        "meaning": "我同意这个方案",
        "spoken_text": "我同意这个方案，可以继续推进。",
    },
    "disagree": {
        "meaning": "我不同意这个方案",
        "spoken_text": "我不太同意这个方案，可能还需要重新评估。",
    },
    "repeat": {
        "meaning": "请再说一遍",
        "spoken_text": "不好意思，我没有完全理解，可以请你再解释一遍吗？",
    },
    "question": {
        "meaning": "我想提问",
        "spoken_text": "我有一个问题，想请大家一起讨论一下。",
    },
    "supplement": {
        "meaning": "我想补充一个想法",
        "spoken_text": "我想补充一个想法，也许我们可以从用户体验的角度再优化一下。",
    },
    "start": {
        "meaning": "我们可以开始了",
        "spoken_text": "我们可以开始今天的讨论了。",
    },
    "modify": {
        "meaning": "这个部分需要修改",
        "spoken_text": "我觉得这个部分还需要修改，尤其是交互流程可以更清楚。",
    },
    "think": {
        "meaning": "我需要一点时间思考",
        "spoken_text": "我需要一点时间思考，稍后再回答这个问题。",
    },
}

UNKNOWN_RESULT = {
    "meaning": "无法识别，请重新录制",
    "confidence": 0.0,
    "spoken_text": "无法识别，请重新录制。",
}

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "sign_templates"


def response_for_label(label: str, confidence: float) -> dict:
    response = SIGN_TEMPLATE_RESPONSES.get(label)
    if response is None:
        return UNKNOWN_RESULT.copy()
    return {
        "meaning": response["meaning"],
        "confidence": max(0.0, min(1.0, float(confidence))),
        "spoken_text": response["spoken_text"],
    }


def allowed_labels() -> set[str]:
    return set(SIGN_TEMPLATE_RESPONSES)
