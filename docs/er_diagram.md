# Entity Relationship Diagram

The current project does not use a database. It uses file-based storage for datasets, trained models, uploads, and outputs. This ER diagram is a conceptual database model for the system.

```mermaid
erDiagram
    DATASET ||--o{ IMAGE : contains
    DATASET ||--o{ VIDEO : contains
    IMAGE ||--o{ ANNOTATION : has
    ANNOTATION }o--|| DEFECT_CLASS : belongs_to

    TRAINING_RUN ||--|| DATASET : uses
    TRAINING_RUN ||--o{ MODEL_ARTIFACT : produces

    MODEL_ARTIFACT ||--o{ INFERENCE_REQUEST : used_for
    INFERENCE_REQUEST ||--o{ DETECTION_RESULT : returns
    DETECTION_RESULT }o--|| DEFECT_CLASS : classified_as
    DETECTION_RESULT ||--|| BOUNDING_BOX : has

    INFERENCE_REQUEST ||--o| OUTPUT_FILE : generates

    DATASET {
        string dataset_id
        string name
        string path
        string split
    }

    IMAGE {
        string image_id
        string filename
        string path
        string split
        string format
    }

    VIDEO {
        string video_id
        string filename
        string path
        string format
        float fps
        int total_frames
    }

    ANNOTATION {
        string annotation_id
        string image_id
        int class_id
        float x_center
        float y_center
        float width
        float height
    }

    DEFECT_CLASS {
        int class_id
        string class_name
        string color
    }

    TRAINING_RUN {
        string run_id
        string model_name
        int epochs
        int batch_size
        int image_size
        string optimizer
        string save_dir
    }

    MODEL_ARTIFACT {
        string artifact_id
        string filename
        string path
        string format
        boolean active
    }

    INFERENCE_REQUEST {
        string request_id
        string input_type
        string input_filename
        float confidence_threshold
        float iou_threshold
        datetime created_at
    }

    DETECTION_RESULT {
        string detection_id
        string request_id
        int class_id
        float confidence
    }

    BOUNDING_BOX {
        string bbox_id
        string detection_id
        float x1
        float y1
        float x2
        float y2
    }

    OUTPUT_FILE {
        string output_id
        string request_id
        string file_path
        string output_type
    }
```

