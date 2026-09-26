from __future__ import annotations

import base64
import io
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .config import (
    CLASS_COLORS,
    CLASS_NAMES,
    DEFAULT_CONF,
    DEFAULT_IOU,
    MODEL_CANDIDATES,
)
from .db import log_detections

_model = None
_model_path: Path | None = None


def resolve_model_path() -> Path:
    for candidate in MODEL_CANDIDATES:
        if candidate.exists():
            return candidate
    return MODEL_CANDIDATES[-1]


def get_model():
    global _model, _model_path
    from ultralytics import YOLO

    path = resolve_model_path()
    if _model is None or _model_path != path:
        _model = YOLO(str(path))
        _model_path = path
    return _model


def model_info() -> dict:
    path = resolve_model_path()
    return {
        "path": str(path),
        "exists": path.exists(),
        "classes": CLASS_NAMES,
        "num_classes": len(CLASS_NAMES),
    }


def _boxes_from_result(result) -> list[dict]:
    detections: list[dict] = []
    if result.boxes is None or len(result.boxes) == 0:
        return detections

    names = result.names or {}
    for box in result.boxes:
        cls_id = int(box.cls.item())
        label = names.get(cls_id, CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else str(cls_id))
        xyxy = box.xyxy[0].tolist()
        
        track_id = int(box.id.item()) if box.id is not None else None

        detections.append(
            {
                "class_id": cls_id,
                "label": label,
                "confidence": round(float(box.conf.item()), 4),
                "track_id": track_id,
                "bbox": {
                    "x1": round(xyxy[0], 1),
                    "y1": round(xyxy[1], 1),
                    "x2": round(xyxy[2], 1),
                    "y2": round(xyxy[3], 1),
                },
                "color": CLASS_COLORS[cls_id % len(CLASS_COLORS)],
            }
        )
    return detections


def predict_image(
    image: np.ndarray,
    conf: float = DEFAULT_CONF,
    iou: float = DEFAULT_IOU,
) -> tuple[np.ndarray, list[dict], float]:
    model = get_model()
    start = time.perf_counter()
    results = model.predict(
        source=image,
        conf=conf,
        iou=iou,
        verbose=False,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    result = results[0]
    annotated = result.plot()
    return annotated, _boxes_from_result(result), elapsed_ms


def decode_image_bytes(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image")
    return image


def decode_base64_image(payload: str) -> np.ndarray:
    if "," in payload:
        payload = payload.split(",", 1)[1]
    raw = base64.b64decode(payload)
    return decode_image_bytes(raw)


def encode_image_jpeg(image: np.ndarray, quality: int = 88) -> str:
    ok, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise ValueError("Failed to encode image")
    encoded = base64.b64encode(buffer.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def summarize(detections: list[dict]) -> dict:
    by_class: dict[str, int] = {}
    for det in detections:
        by_class[det["label"]] = by_class.get(det["label"], 0) + 1
    return {
        "total": len(detections),
        "by_class": by_class,
    }


def process_video_file(
    input_path: Path,
    output_path: Path,
    conf: float = DEFAULT_CONF,
    iou: float = DEFAULT_IOU,
    progress_callback=None,
) -> dict:
    model = get_model()
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise ValueError("Could not open video file")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    frame_idx = 0
    total_detections = 0
    class_hits: dict[str, int] = {}
    tracked_unique_defects: dict[int, dict] = {}
    start = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        results = model.track(source=frame, conf=conf, iou=iou, persist=True, verbose=False)
        annotated = results[0].plot()
        writer.write(annotated)

        dets = _boxes_from_result(results[0])
        total_detections += len(dets)
        
        for det in dets:
            tid = det.get("track_id")
            if tid is not None:
                if tid not in tracked_unique_defects:
                    tracked_unique_defects[tid] = det
                    class_hits[det["label"]] = class_hits.get(det["label"], 0) + 1
            else:
                class_hits[det["label"]] = class_hits.get(det["label"], 0) + 1

        frame_idx += 1
        if progress_callback and total_frames > 0:
            progress_callback(frame_idx, total_frames)

    cap.release()
    writer.release()
    
    if tracked_unique_defects:
        log_detections(list(tracked_unique_defects.values()), source="video")

    elapsed = time.perf_counter() - start
    return {
        "frames_processed": frame_idx,
        "fps_source": round(fps, 2),
        "duration_sec": round(frame_idx / fps, 2) if fps else 0,
        "processing_sec": round(elapsed, 2),
        "total_detections": total_detections,
        "by_class": class_hits,
    }
