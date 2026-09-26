import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "analytics.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS detections (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp TEXT,
                          class_name TEXT,
                          confidence REAL,
                          source TEXT
                      )''')

def log_detections(detections, source="image"):
    if not detections:
        return
    with sqlite3.connect(DB_PATH) as conn:
        now = datetime.now().isoformat()
        rows = [(now, d["label"], d["confidence"], source) for d in detections]
        conn.executemany(
            "INSERT INTO detections (timestamp, class_name, confidence, source) VALUES (?, ?, ?, ?)",
            rows
        )

def get_analytics():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT class_name, COUNT(*) as count FROM detections GROUP BY class_name")
        class_counts = {row["class_name"]: row["count"] for row in cur.fetchall()}
        return {"class_counts": class_counts}
