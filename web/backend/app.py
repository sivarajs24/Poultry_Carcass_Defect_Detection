from __future__ import annotations

import uuid
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .config import (
    DEFAULT_CONF,
    DEFAULT_IOU,
    MAX_UPLOAD_MB,
    OUTPUT_DIR,
    UPLOAD_DIR,
    WEB_ROOT,
)
from .inference import (
    decode_base64_image,
    decode_image_bytes,
    encode_image_jpeg,
    get_model,
    model_info,
    predict_image,
    process_video_file,
    summarize,
)
from .db import init_db, log_detections, get_analytics

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_VIDEO = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
VIDEO_TASKS = {}


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(WEB_ROOT / "static"),
        static_url_path="/static",
    )
    CORS(app)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    init_db()

    @app.route("/")
    def index():
        return send_from_directory(WEB_ROOT, "index.html")

    @app.route("/api/health")
    def health():
        try:
            get_model()
            status = "ready"
        except Exception as exc:  # noqa: BLE001
            status = "error"
            return jsonify({"status": status, "error": str(exc)}), 503
        return jsonify({"status": status, "model": model_info()})

    @app.route("/api/detect/image", methods=["POST"])
    def detect_image():
        conf = float(request.form.get("conf", DEFAULT_CONF))
        iou = float(request.form.get("iou", DEFAULT_IOU))

        try:
            if "file" in request.files and request.files["file"].filename:
                raw = request.files["file"].read()
                image = decode_image_bytes(raw)
            elif request.is_json:
                payload = request.get_json(silent=True) or {}
                image_b64 = payload.get("image")
                if not image_b64:
                    return jsonify({"error": "No image provided"}), 400
                conf = float(payload.get("conf", conf))
                iou = float(payload.get("iou", iou))
                image = decode_base64_image(image_b64)
            else:
                return jsonify({"error": "No image provided"}), 400

            annotated, detections, elapsed_ms = predict_image(image, conf=conf, iou=iou)
            log_detections(detections, source="image")
            return jsonify(
                {
                    "success": True,
                    "image": encode_image_jpeg(annotated),
                    "detections": detections,
                    "summary": summarize(detections),
                    "inference_ms": round(elapsed_ms, 1),
                    "model": model_info(),
                }
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"success": False, "error": str(exc)}), 500

    @app.route("/api/detect/frame", methods=["POST"])
    def detect_frame():
        payload = request.get_json(silent=True) or {}
        image_b64 = payload.get("image")
        if not image_b64:
            return jsonify({"error": "No frame provided"}), 400

        conf = float(payload.get("conf", DEFAULT_CONF))
        iou = float(payload.get("iou", DEFAULT_IOU))

        try:
            image = decode_base64_image(image_b64)
            annotated, detections, elapsed_ms = predict_image(image, conf=conf, iou=iou)
            return jsonify(
                {
                    "success": True,
                    "image": encode_image_jpeg(annotated, quality=82),
                    "detections": detections,
                    "summary": summarize(detections),
                    "inference_ms": round(elapsed_ms, 1),
                }
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"success": False, "error": str(exc)}), 500

    @app.route("/api/detect/video", methods=["POST"])
    def detect_video():
        if "file" not in request.files or not request.files["file"].filename:
            return jsonify({"error": "No video file provided"}), 400

        upload = request.files["file"]
        suffix = Path(secure_filename(upload.filename)).suffix.lower()
        if suffix not in ALLOWED_VIDEO:
            return jsonify({"error": f"Unsupported video type: {suffix}"}), 400

        conf = float(request.form.get("conf", DEFAULT_CONF))
        iou = float(request.form.get("iou", DEFAULT_IOU))
        job_id = uuid.uuid4().hex[:12]
        input_path = UPLOAD_DIR / f"{job_id}_in{suffix}"
        output_path = OUTPUT_DIR / f"{job_id}_out.mp4"

        try:
            upload.save(input_path)
            VIDEO_TASKS[job_id] = {"status": "processing", "progress": 0}

            def async_process_video():
                try:
                    def progress_cb(frame_idx, total_frames):
                        VIDEO_TASKS[job_id]["progress"] = round((frame_idx / total_frames) * 100, 1) if total_frames else 0
                    
                    stats = process_video_file(input_path, output_path, conf=conf, iou=iou, progress_callback=progress_cb)
                    VIDEO_TASKS[job_id]["status"] = "done"
                    VIDEO_TASKS[job_id]["stats"] = stats
                    VIDEO_TASKS[job_id]["video_url"] = f"/api/outputs/{output_path.name}"
                except Exception as exc:
                    VIDEO_TASKS[job_id]["status"] = "error"
                    VIDEO_TASKS[job_id]["error"] = str(exc)
                finally:
                    if input_path.exists():
                        input_path.unlink(missing_ok=True)

            thread = threading.Thread(target=async_process_video)
            thread.daemon = True
            thread.start()

            return jsonify({
                "success": True,
                "job_id": job_id,
            })
        except Exception as exc:  # noqa: BLE001
            return jsonify({"success": False, "error": str(exc)}), 500

    @app.route("/api/detect/video/status/<job_id>")
    def video_status(job_id):
        if job_id not in VIDEO_TASKS:
            return jsonify({"error": "Job not found"}), 404
        return jsonify(VIDEO_TASKS[job_id])

    @app.route("/api/outputs/<path:filename>")
    def serve_output(filename):
        return send_from_directory(OUTPUT_DIR, filename, as_attachment=False)

    @app.route("/api/analytics")
    def analytics():
        try:
            return jsonify(get_analytics())
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    return app


app = create_app()
