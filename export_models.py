from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent

MODEL_CANDIDATES = [
    ROOT / "runs" / "poultry_carcass_yolov8_detect" / "weights" / "best.pt",
    ROOT / "runs" / "poultry_carcass_yolov8_detect" / "weights" / "last.pt",
    ROOT / "yolov8n.pt",
]

for pt_path in MODEL_CANDIDATES:
    if pt_path.exists():
        print(f"Exporting {pt_path} to ONNX...")
        try:
            model = YOLO(str(pt_path))
            model.export(format="onnx", imgsz=640)
        except Exception as e:
            print(f"Failed to export {pt_path}: {e}")
