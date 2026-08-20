"""Clip quality scoring and content tagging heuristics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from scripts.lib.analysis import find_peaks, motion_energy_curve


def blur_score(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Normalize: higher laplacian variance = sharper
    return min(1.0, lap_var / 500.0)


def exposure_score(frame: np.ndarray) -> float:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean = float(np.mean(gray))
    # Penalize too dark or blown out
    if mean < 40 or mean > 220:
        return 0.2
    if mean < 70 or mean > 200:
        return 0.5
    return 1.0


def sample_quality(path: Path, num_samples: int = 8) -> float:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return 0.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total_frames <= 0:
        cap.release()
        return 0.0

    indices = np.linspace(0, total_frames - 1, num=num_samples, dtype=int)
    blur_scores = []
    exposure_scores = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if not ret:
            continue
        blur_scores.append(blur_score(frame))
        exposure_scores.append(exposure_score(frame))

    cap.release()

    if not blur_scores:
        return 0.0

    return round(float(np.mean(blur_scores) * 0.7 + np.mean(exposure_scores) * 0.3), 4)


def infer_tags(path: Path, motion: list[dict[str, Any]], quality: float) -> list[str]:
    tags: list[str] = []

    if quality >= 0.7:
        tags.append("high_quality")

    if not motion:
        return tags or ["general"]

    peak_motion = max(p["motion"] for p in motion)
    avg_motion = float(np.mean([p["motion"] for p in motion]))

    if peak_motion > 0.2:
        tags.append("kick")
    if avg_motion < 0.05 and quality >= 0.5:
        tags.append("beauty_slowmo")
    if peak_motion > 0.15 and avg_motion > 0.08:
        tags.append("action")
    if 0.05 <= avg_motion <= 0.12:
        tags.append("reaction")
        if peak_motion < 0.12:
            tags.append("reaction_fail")
        else:
            tags.append("reaction_smug")

    # Face heuristic: center-weighted edge density (rough proxy)
    cap = cv2.VideoCapture(str(path))
    ret, frame = cap.read()
    cap.release()
    if ret:
        h, w = frame.shape[:2]
        center = frame[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
        edges = cv2.Canny(cv2.cvtColor(center, cv2.COLOR_BGR2GRAY), 50, 150)
        if np.mean(edges) > 15:
            tags.append("face_closeup")

    return list(dict.fromkeys(tags))  # dedupe preserve order


def best_segments(path: Path, duration: float) -> list[dict[str, Any]]:
    motion = motion_energy_curve(path, sample_interval=0.25)
    audio: list[dict[str, Any]] = []
    peaks = find_peaks(motion, audio, top_n=3)

    segments = []
    for p in peaks:
        start = max(0, p["start"])
        end = min(duration, p["end"])
        if end - start >= 0.4:
            segments.append(
                {
                    "start": start,
                    "end": end,
                    "reason": p["reason"],
                    "score": p.get("score", 0),
                }
            )
    return segments
