"""Video analysis helpers: scene detection, motion, audio energy."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import librosa
import numpy as np
from scenedetect import ContentDetector, SceneManager, open_video


def detect_scenes(path: Path, threshold: float = 27.0) -> list[float]:
    video = open_video(str(path))
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()
    times = [0.0]
    for _start, end in scene_list:
        times.append(end.get_seconds())
    return sorted(set(round(t, 3) for t in times))


def shot_lengths(cut_times: list[float]) -> list[float]:
    if len(cut_times) < 2:
        return []
    return [round(cut_times[i + 1] - cut_times[i], 3) for i in range(len(cut_times) - 1)]


def motion_energy_curve(path: Path, sample_interval: float = 0.5) -> list[dict[str, Any]]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_step = max(1, int(fps * sample_interval))
    prev_gray = None
    points: list[dict[str, Any]] = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            t = round(frame_idx / fps, 3)
            if prev_gray is not None:
                diff = cv2.absdiff(gray, prev_gray)
                energy = float(np.mean(diff)) / 255.0
                points.append({"time_s": t, "motion": round(energy, 4)})
            prev_gray = gray
        frame_idx += 1

    cap.release()
    return points


def audio_energy_curve(path: Path, hop_length: int = 512) -> list[dict[str, Any]]:
    try:
        y, sr = librosa.load(str(path), sr=None, mono=True)
    except Exception:
        return []

    if len(y) == 0:
        return []

    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    # Downsample to ~20 points max for profile
    step = max(1, len(times) // 20)
    points = []
    for i in range(0, len(times), step):
        points.append({"time_s": round(float(times[i]), 3), "audio_rms": round(float(rms[i]), 4)})
    return points


def bucket_energy(values: list[float]) -> list[str]:
    if not values:
        return []
    arr = np.array(values)
    q25, q75 = np.percentile(arr, [25, 75])
    labels = []
    for v in arr:
        if v >= q75:
            labels.append("high")
        elif v <= q25:
            labels.append("low")
        else:
            labels.append("mid")
    return labels


def find_peaks(
    motion: list[dict[str, Any]],
    audio: list[dict[str, Any]],
    top_n: int = 5,
) -> list[dict[str, Any]]:
    combined: dict[float, float] = {}

    for p in motion:
        combined[p["time_s"]] = combined.get(p["time_s"], 0) + p["motion"] * 2

    for p in audio:
        t = p["time_s"]
        combined[t] = combined.get(t, 0) + p["audio_rms"]

    if not combined:
        return []

    sorted_peaks = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_n]
    segments = []
    for t, score in sorted_peaks:
        segments.append(
            {
                "start": round(max(0, t - 0.4), 3),
                "end": round(t + 0.6, 3),
                "reason": "impact moment" if score > 0.5 else "energy peak",
                "score": round(score, 4),
            }
        )
    return sorted(segments, key=lambda s: s["start"])


def estimate_bpm(path: Path) -> int | None:
    try:
        y, sr = librosa.load(str(path), sr=22050, mono=True, duration=30)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if hasattr(tempo, "__len__"):
            tempo = tempo[0]
        return int(round(float(tempo)))
    except Exception:
        return None


def infer_hook_type(motion: list[dict[str, Any]], duration: float) -> dict[str, Any]:
    window = [p for p in motion if p["time_s"] <= 1.5]
    if not window:
        return {"type": "impact_first", "window_s": "0.0-1.2"}

    early = window[0]["motion"] if window else 0
    peak_early = max(p["motion"] for p in window) if window else 0

    if peak_early > 0.15 and early > 0.08:
        hook_type = "impact_first"
    elif peak_early > 0.08:
        hook_type = "motion_first"
    else:
        hook_type = "text_first"

    return {"type": hook_type, "window_s": "0.0-1.2"}


def infer_cut_pattern(avg_shot: float, shot_count: int) -> str:
    if shot_count >= 8 and avg_shot < 1.0:
        return "rapid_montage"
    if shot_count >= 5 and avg_shot < 1.2:
        return "triple_fail_then_payoff"
    if avg_shot > 2.0:
        return "slow_build_hold"
    return "beat_matched_cuts"


def infer_theme(motion_peaks: int, avg_shot: float, bpm: int | None) -> str:
    if avg_shot < 1.0 and (bpm or 0) > 120:
        return "skill_vs_chaos"
    if avg_shot > 2.0:
        return "soul_beauty"
    if (bpm or 0) > 130:
        return "hype_challenge"
    return "comedy_reaction"
