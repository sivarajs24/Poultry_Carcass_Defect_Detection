import pytest
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prepare_yolov8_dataset import yolo_polygon_to_box, convert_label_line

def test_yolo_polygon_to_box():
    # Regular polygon: bounds are (0.1, 0.1) to (0.5, 0.5)
    polygon = ["0.1", "0.1", "0.5", "0.1", "0.5", "0.5", "0.1", "0.5"]
    box = yolo_polygon_to_box(polygon)
    assert box is not None
    x, y, w, h = box
    assert pytest.approx(x) == 0.3
    assert pytest.approx(y) == 0.3
    assert pytest.approx(w) == 0.4
    assert pytest.approx(h) == 0.4

    # Out of bounds polygon (should clip to 1.0)
    # bounds are (0.5, 0.5) to (1.5, 1.5)
    polygon_oob = ["0.5", "0.5", "1.5", "0.5", "1.5", "1.5", "0.5", "1.5"]
    box_oob = yolo_polygon_to_box(polygon_oob)
    assert box_oob is not None
    x, y, w, h = box_oob
    assert pytest.approx(x) == 0.75  # Center of 0.5 and 1.0
    assert pytest.approx(y) == 0.75
    assert pytest.approx(w) == 0.5   # 1.0 - 0.5
    assert pytest.approx(h) == 0.5
    
    # Invalid polygon (0 width)
    polygon_inv = ["0.1", "0.1", "0.1", "0.5"]
    assert yolo_polygon_to_box(polygon_inv) is None

def test_convert_label_line():
    # class_map maps source class ID to target class name
    class_map = {0: "bruise", 1: "bile"}
    
    # Valid box line: "class_id x y w h"
    # "bruise" is target class ID 1
    line = "0 0.5 0.5 0.2 0.2"
    res = convert_label_line(line, class_map)
    assert res == "1 0.500000 0.500000 0.200000 0.200000"
    
    # Polygon line
    # "bile" is target class ID 0
    poly_line = "1 0.1 0.1 0.5 0.1 0.5 0.5 0.1 0.5"
    res2 = convert_label_line(poly_line, class_map)
    assert res2 == "0 0.300000 0.300000 0.400000 0.400000"

    # Out of bounds box (x=1.2) - it should clip x to 1.0
    oob_line = "0 1.2 0.5 0.2 0.2"
    res3 = convert_label_line(oob_line, class_map)
    assert res3 == "1 1.000000 0.500000 0.200000 0.200000"
    
    # Negative values (w=-0.2) - clipped to 0, which makes it invalid, returns None
    inv_line = "0 0.5 0.5 -0.2 0.2"
    assert convert_label_line(inv_line, class_map) is None
    
    # Unknown source class
    unknown_class_line = "99 0.5 0.5 0.2 0.2"
    assert convert_label_line(unknown_class_line, class_map) is None
