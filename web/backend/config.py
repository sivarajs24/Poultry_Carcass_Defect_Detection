from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = Path(__file__).resolve().parents[1]
DATA_YAML = ROOT / "datasets" / "merged_detection_yolov8" / "data.yaml"

MODEL_CANDIDATES = [
    ROOT / "runs" / "poultry_carcass_yolo26_detect" / "weights" / "best.onnx",
    ROOT / "yolov8n.onnx",
    ROOT / "runs" / "poultry_carcass_yolo26_detect" / "weights" / "best.pt",
    ROOT / "runs" / "poultry_carcass_yolo26_detect" / "weights" / "last.pt",
    ROOT / "yolov8n.pt",
]

DEFAULT_CONF = 0.15
DEFAULT_IOU = 0.45
MAX_UPLOAD_MB = 120
UPLOAD_DIR = WEB_ROOT / "uploads"
OUTPUT_DIR = WEB_ROOT / "outputs"

CLASS_NAMES = [
    "bile",
    "bruise",
    "dislocation",
    "feather",
    "fracture",
    "hematoma",
    "scratch",
    "skin-rash",
    "abnormal-carcass",
    "technical-failure",
    "fecal-contamination",
]

CLASS_COLORS = [
    "#e74c3c",
    "#9b59b6",
    "#3498db",
    "#1abc9c",
    "#f39c12",
    "#e67e22",
    "#2ecc71",
    "#16a085",
    "#c0392b",
    "#7f8c8d",
    "#8e44ad",
]
