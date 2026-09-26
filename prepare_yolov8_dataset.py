from pathlib import Path
from shutil import copy2, rmtree


ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / "datasets"
OUTPUT = DATASETS / "merged_detection_yolov8"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLITS = ("train", "valid", "test")

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

CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}


def source_configs():
    return {
        "Poultry Defects.v6i.yolov8": {
            0: "bile",
            1: "bruise",
            2: "dislocation",
            3: "feather",
            4: "fracture",
            5: "hematoma",
            6: "scratch",
            7: "skin-rash",
        },
        "Chicken bruise.v1i.yolov8": {
            # This dataset exports class names as 1..7. The project is a bruise
            # dataset, so the grades/classes are merged into one bruise class.
            0: "bruise",
            1: "bruise",
            2: "bruise",
            3: "bruise",
            4: "bruise",
            5: "bruise",
            6: "bruise",
        },
        "IS - Carcacas de frango-3classes-.v3-v1.2_inst_seg_fotoeframe_comcontraste.yolov8": {
            # 0 is chicken-carcass, which is the whole carcass and not a defect.
            1: "abnormal-carcass",
            2: "technical-failure",
            3: "bile",
            4: "fecal-contamination",
            5: "fracture",
        },
    }


def yolo_polygon_to_box(values):
    points = [float(v) for v in values]
    xs = points[0::2]
    ys = points[1::2]
    x_min, x_max = max(0.0, min(xs)), min(1.0, max(xs))
    y_min, y_max = max(0.0, min(ys)), min(1.0, max(ys))
    w = max(0.0, x_max - x_min)
    h = max(0.0, y_max - y_min)
    if w <= 0.0 or h <= 0.0:
        return None
    return ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0, w, h)


def convert_label_line(line, class_map):
    tokens = line.strip().split()
    if len(tokens) < 5:
        return None

    source_class = int(float(tokens[0]))
    target_name = class_map.get(source_class)
    if target_name is None:
        return None

    target_class = CLASS_TO_ID[target_name]
    values = tokens[1:]

    if len(tokens) == 5:
        box = tuple(float(v) for v in values)
    else:
        box = yolo_polygon_to_box(values)

    if box is None:
        return None

    x, y, w, h = box
    if not all(0.0 <= v <= 1.0 for v in (x, y, w, h)):
        x = min(1.0, max(0.0, x))
        y = min(1.0, max(0.0, y))
        w = min(1.0, max(0.0, w))
        h = min(1.0, max(0.0, h))

    if w <= 0.0 or h <= 0.0:
        return None

    return f"{target_class} {x:.6f} {y:.6f} {w:.6f} {h:.6f}"


def image_files(split_dir):
    if not split_dir.exists():
        return []
    return sorted(
        p for p in split_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def write_yaml():
    names = ", ".join(f"'{name}'" for name in CLASS_NAMES)
    content = (
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n\n"
        f"nc: {len(CLASS_NAMES)}\n"
        f"names: [{names}]\n"
    )
    (OUTPUT / "data.yaml").write_text(content, encoding="utf-8")


def prepare():
    configs = source_configs()

    if OUTPUT.exists():
        rmtree(OUTPUT)

    for split in SPLITS:
        (OUTPUT / split / "images").mkdir(parents=True, exist_ok=True)
        (OUTPUT / split / "labels").mkdir(parents=True, exist_ok=True)

    stats = {
        "images": 0,
        "labels_written": 0,
        "objects_written": 0,
        "objects_skipped": 0,
    }
    per_class = {name: 0 for name in CLASS_NAMES}

    for dataset_name, class_map in configs.items():
        dataset_dir = DATASETS / dataset_name
        if not dataset_dir.exists():
            print(f"Missing dataset, skipped: {dataset_name}")
            continue

        prefix = "".join(ch if ch.isalnum() else "_" for ch in dataset_name.lower())

        for split in SPLITS:
            for image_path in image_files(dataset_dir / split / "images"):
                out_stem = f"{prefix}_{image_path.stem}"
                out_image = OUTPUT / split / "images" / f"{out_stem}{image_path.suffix.lower()}"
                out_label = OUTPUT / split / "labels" / f"{out_stem}.txt"
                in_label = dataset_dir / split / "labels" / f"{image_path.stem}.txt"

                copy2(image_path, out_image)
                stats["images"] += 1

                converted = []
                if in_label.exists():
                    for line in in_label.read_text(encoding="utf-8", errors="ignore").splitlines():
                        if not line.strip():
                            continue
                        converted_line = convert_label_line(line, class_map)
                        if converted_line is None:
                            stats["objects_skipped"] += 1
                            continue
                        converted.append(converted_line)
                        class_id = int(converted_line.split()[0])
                        per_class[CLASS_NAMES[class_id]] += 1

                out_label.write_text("\n".join(converted) + ("\n" if converted else ""), encoding="utf-8")
                stats["labels_written"] += 1
                stats["objects_written"] += len(converted)

    write_yaml()

    print(f"Prepared: {OUTPUT}")
    print(f"Images copied: {stats['images']}")
    print(f"Label files written: {stats['labels_written']}")
    print(f"Objects written: {stats['objects_written']}")
    print(f"Objects skipped: {stats['objects_skipped']}")
    print("Objects per class:")
    for name, count in per_class.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    prepare()
