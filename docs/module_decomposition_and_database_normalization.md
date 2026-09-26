# Module Decomposition and Database Normalization

## Module Decomposition

| Module | Files/Folders | Responsibility |
|---|---|---|
| Dataset Preparation Module | `prepare_yolo26_dataset.py` | Merges multiple datasets, converts labels, creates final YOLO dataset |
| Dataset Storage Module | `datasets/merged_detection_yolo26/` | Stores `train`, `valid`, and `test` images and labels |
| Model Training Module | `YOLO26_model.ipynb` | Trains YOLO26 model using prepared dataset |
| Model Artifact Module | `runs/poultry_carcass_yolo26_detect/weights/` | Stores trained models such as `best.pt`, `last.pt`, and `best.onnx` |
| Backend API Module | `web/backend/app.py` | Defines Flask routes for image, video, and frame detection |
| Inference Module | `web/backend/inference.py` | Loads YOLO model, runs prediction, extracts detection results |
| Configuration Module | `web/backend/config.py` | Stores model paths, class names, thresholds, upload paths |
| Frontend UI Module | `web/index.html`, `web/static/` | Provides camera, image upload, video upload, and result display |
| Temporary File Module | `web/uploads/`, `web/outputs/` | Stores uploaded videos and processed output videos |

## Module Flow

```text
Raw Datasets
   |
   v
Dataset Preparation Module
   |
   v
Merged YOLO Dataset
   |
   v
Model Training Module
   |
   v
Model Artifact Module
   |
   v
Backend API + Inference Module
   |
   v
Frontend UI
```

## Backend Decomposition

`web/backend/app.py` handles HTTP-level work:

```text
/api/health
/api/detect/image
/api/detect/frame
/api/detect/video
/api/outputs/<filename>
```

`web/backend/inference.py` handles ML-level work:

```text
load model
decode image
run YOLO prediction
extract bounding boxes
summarize detections
process video frame by frame
```

`web/backend/config.py` centralizes constants:

```text
class names
class colors
model paths
confidence threshold
IoU threshold
upload/output folders
```

## Database Normalization

The current project does not use a database. It uses file-based storage:

```text
datasets/
runs/
web/uploads/
web/outputs/
```

So database normalization is conceptual. If this system were converted to a database-backed system, normalization would separate repeated information into independent tables.

## Unnormalized Data Example

| request_id | image_name | model_path | class_name | confidence | x1 | y1 | x2 | y2 | output_file |
|---|---|---|---|---|---|---|---|---|---|
| R001 | img1.jpg | best.pt | bruise | 0.91 | 120 | 45 | 220 | 140 | out1.jpg |
| R001 | img1.jpg | best.pt | fracture | 0.83 | 300 | 80 | 390 | 180 | out1.jpg |

This repeats `image_name`, `model_path`, and `output_file` for every detection.

## First Normal Form

Each field should contain one atomic value.

Bad:

```text
detections = "bruise:0.91, fracture:0.83"
```

Good:

| detection_id | request_id | class_id | confidence |
|---|---|---|---|
| D001 | R001 | 2 | 0.91 |
| D002 | R001 | 5 | 0.83 |

## Second Normal Form

Remove partial dependency. Detection data should not store request-level information repeatedly.

Bad:

| detection_id | request_id | image_name | class_name | confidence |
|---|---|---|---|---|
| D001 | R001 | img1.jpg | bruise | 0.91 |
| D002 | R001 | img1.jpg | fracture | 0.83 |

Good:

```text
InferenceRequest(request_id, input_file, model_id, conf_threshold, iou_threshold)
DetectionResult(detection_id, request_id, class_id, confidence)
```

## Third Normal Form

Remove transitive dependency. Class details should be stored separately.

Bad:

| detection_id | class_id | class_name | class_color |
|---|---|---|---|
| D001 | 1 | bruise | #9b59b6 |

Good:

```text
DetectionResult(detection_id, request_id, class_id, confidence)
DefectClass(class_id, class_name, class_color)
```

## Final Normalized Tables

```text
DefectClass
- class_id PK
- class_name
- class_color

Dataset
- dataset_id PK
- name
- path

Image
- image_id PK
- dataset_id FK
- filename
- path
- split

Annotation
- annotation_id PK
- image_id FK
- class_id FK
- x_center
- y_center
- width
- height

TrainingRun
- run_id PK
- dataset_id FK
- model_name
- epochs
- batch_size
- image_size
- optimizer
- save_dir

ModelArtifact
- model_id PK
- run_id FK
- filename
- path
- format
- active

InferenceRequest
- request_id PK
- model_id FK
- input_type
- input_path
- confidence_threshold
- iou_threshold
- created_at

DetectionResult
- detection_id PK
- request_id FK
- class_id FK
- confidence

BoundingBox
- bbox_id PK
- detection_id FK
- x1
- y1
- x2
- y2

OutputFile
- output_id PK
- request_id FK
- file_path
- output_type
```

## Summary

The current system is modular but file-based. The main decomposition is:

```text
Dataset preparation -> Training -> Model storage -> Flask inference API -> Web UI
```

If a database is added later, the design should be normalized by separating defect classes, images, annotations, training runs, model artifacts, inference requests, detection results, bounding boxes, and output files.
