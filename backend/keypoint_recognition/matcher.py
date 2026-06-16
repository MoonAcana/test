from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

from backend.keypoint_recognition.extractor import TARGET_FRAMES, resample_sequence
from backend.keypoint_recognition.templates import TEMPLATE_DIR, response_for_label


@dataclass(frozen=True)
class MatchResult:
    label: str
    confidence: float
    distance: float
    template_file: str


class NoTemplatesError(RuntimeError):
    pass


def match_sequence(sequence, template_dir: Path = TEMPLATE_DIR) -> MatchResult:
    _, _, np = load_numpy()
    template_paths = sorted(Path(template_dir).glob("*.npy"))
    if not template_paths:
        raise NoTemplatesError(
            "No keypoint templates found. Please record templates via /api/record-template first."
        )

    best_label = ""
    best_path = ""
    best_distance = float("inf")

    for template_path in template_paths:
        label = template_path.stem.split("_")[0]
        template = np.load(template_path)
        if template.shape != sequence.shape:
            template = resample_sequence(template, target_frames=TARGET_FRAMES)
        distance = normalized_euclidean_distance(sequence, template, np)
        if distance < best_distance:
            best_distance = distance
            best_label = label
            best_path = template_path.name

    confidence = math.exp(-best_distance)
    return MatchResult(
        label=best_label,
        confidence=max(0.0, min(1.0, confidence)),
        distance=best_distance,
        template_file=best_path,
    )


def match_to_response(sequence, template_dir: Path = TEMPLATE_DIR) -> dict:
    match = match_sequence(sequence, template_dir=template_dir)
    response = response_for_label(match.label, match.confidence)
    response["match"] = {
        "label": match.label,
        "distance": round(match.distance, 4),
        "template_file": match.template_file,
    }
    return response


def normalized_euclidean_distance(sequence, template, np) -> float:
    sequence = np.asarray(sequence, dtype=np.float32)
    template = np.asarray(template, dtype=np.float32)
    diff = sequence - template
    return float(np.linalg.norm(diff) / math.sqrt(diff.size))


def load_numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "numpy is required for AI_PROVIDER=keypoint. Please run setup.bat or run.bat."
        ) from exc
    return None, None, np
