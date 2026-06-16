from __future__ import annotations

from pathlib import Path

TARGET_FRAMES = 40
POINTS_PER_HAND = 21
VALUES_PER_POINT = 3
HANDS = 2
FEATURE_SIZE = HANDS * POINTS_PER_HAND * VALUES_PER_POINT


class NoHandsDetectedError(RuntimeError):
    pass


def load_keypoint_dependencies():
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "opencv-python, mediapipe and numpy are required for AI_PROVIDER=keypoint. "
            "Please run setup.bat or run.bat to install dependencies."
        ) from exc
    return cv2, mp, np


def resample_sequence(sequence, target_frames: int = TARGET_FRAMES):
    _, _, np = load_keypoint_dependencies()
    sequence = np.asarray(sequence, dtype=np.float32)
    if sequence.size == 0:
        return np.zeros((target_frames, FEATURE_SIZE), dtype=np.float32)
    if len(sequence) == target_frames:
        return sequence.astype(np.float32)
    if len(sequence) == 1:
        return np.repeat(sequence, target_frames, axis=0).astype(np.float32)

    source_x = np.linspace(0, 1, len(sequence))
    target_x = np.linspace(0, 1, target_frames)
    resampled = np.zeros((target_frames, sequence.shape[1]), dtype=np.float32)
    for feature_index in range(sequence.shape[1]):
        resampled[:, feature_index] = np.interp(target_x, source_x, sequence[:, feature_index])
    return resampled


def extract_keypoint_sequence(video_path: str, target_frames: int = TARGET_FRAMES):
    cv2, mp, np = load_keypoint_dependencies()
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video file: {video_path}")

    frames = []
    detected_frame_count = 0
    hands_module = mp.solutions.hands

    try:
        with hands_module.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as hands:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = hands.process(rgb_frame)
                frame_vector, has_hand = keypoints_from_result(result, np)
                if has_hand:
                    detected_frame_count += 1
                frames.append(frame_vector)
    finally:
        capture.release()

    if detected_frame_count == 0:
        raise NoHandsDetectedError("No hands detected in uploaded video.")

    sequence = normalize_sequence(np.asarray(frames, dtype=np.float32), np)
    return resample_sequence(sequence, target_frames=target_frames)


def keypoints_from_result(result, np):
    zero_hand = np.zeros(POINTS_PER_HAND * VALUES_PER_POINT, dtype=np.float32)
    hands_by_label = {
        "Left": zero_hand.copy(),
        "Right": zero_hand.copy(),
    }
    filled_labels = set()

    if not result.multi_hand_landmarks:
        return np.concatenate([hands_by_label["Left"], hands_by_label["Right"]]), False

    for index, hand_landmarks in enumerate(result.multi_hand_landmarks[:2]):
        label = hand_label(result, index)
        if label in filled_labels:
            label = "Right" if label == "Left" else "Left"
        hand_vector = []
        for landmark in hand_landmarks.landmark:
            hand_vector.extend([landmark.x, landmark.y, landmark.z])
        hands_by_label[label] = np.asarray(hand_vector, dtype=np.float32)
        filled_labels.add(label)

    frame_vector = np.concatenate([hands_by_label["Left"], hands_by_label["Right"]])
    return frame_vector, True


def hand_label(result, index: int) -> str:
    if not result.multi_handedness or index >= len(result.multi_handedness):
        return "Left" if index == 0 else "Right"
    label = result.multi_handedness[index].classification[0].label
    return "Left" if label == "Left" else "Right"


def normalize_sequence(sequence, np):
    normalized = sequence.copy()
    hand_size = POINTS_PER_HAND * VALUES_PER_POINT
    for frame_index in range(normalized.shape[0]):
        for hand_index in range(HANDS):
            start = hand_index * hand_size
            end = start + hand_size
            hand = normalized[frame_index, start:end].reshape(POINTS_PER_HAND, VALUES_PER_POINT)
            if not np.any(hand):
                continue
            wrist = hand[0].copy()
            hand -= wrist
            scale = np.max(np.linalg.norm(hand[:, :2], axis=1))
            if scale > 1e-6:
                hand /= scale
            normalized[frame_index, start:end] = hand.reshape(-1)
    return normalized.astype(np.float32)
