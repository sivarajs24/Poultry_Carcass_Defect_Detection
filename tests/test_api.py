import pytest
from pathlib import Path

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from web.backend.app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_endpoint(client):
    response = client.get("/api/health")
    # Health returns either 200 or 503 depending on model availability
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert "status" in data

def test_detect_image_missing_image(client):
    # Testing missing payload
    response = client.post("/api/detect/image")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "No image provided"
    
    # Testing json without image field
    response = client.post("/api/detect/image", json={"conf": 0.5})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "No image provided"

def test_detect_frame_missing_image(client):
    response = client.post("/api/detect/frame", json={"conf": 0.5})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "No frame provided"

def test_detect_video_missing_file(client):
    response = client.post("/api/detect/video")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "No video file provided"

import io

def test_detect_video_invalid_format(client):
    # Simulate uploading a txt file instead of video
    data = {
        'file': (io.BytesIO(b'fake data'), 'test.txt')
    }
    response = client.post("/api/detect/video", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    data = response.get_json()
    assert "Unsupported video type" in data["error"]
