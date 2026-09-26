from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


DOCS = Path(__file__).resolve().parent
W, H = 1920, 1080

NAVY = "#12324a"
TEAL = "#2b8a7e"
BG = "#eef3f7"
TEXT = "#1d2b3a"
MUTED = "#44546a"
LINE = "#c8d2df"
HEADER = "#dbeafe"
WHITE = "#ffffff"


def font(name="arial.ttf", size=32):
    for base in (Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/dejavu")):
        path = base / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F_TITLE = font("arialbd.ttf", 58)
F_SUB = font("arialbd.ttf", 30)
F_H = font("arialbd.ttf", 44)
F_CARD_H = font("arialbd.ttf", 28)
F_BODY = font("arial.ttf", 25)
F_BODY_B = font("arialbd.ttf", 25)
F_SMALL = font("arial.ttf", 21)
F_SMALL_B = font("arialbd.ttf", 22)
F_TABLE = font("arial.ttf", 20)
F_TABLE_B = font("arialbd.ttf", 21)


def wrap(value, width):
    return "\n".join(textwrap.wrap(value, width=width, break_long_words=False))


def mtext(draw, xy, value, fill=TEXT, fnt=F_BODY, spacing=5, anchor=None):
    draw.multiline_text(xy, value, font=fnt, fill=fill, spacing=spacing, anchor=anchor)


def rounded(draw, box, fill=WHITE, outline=LINE, radius=8, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def slide_base(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 148), fill=NAVY)
    draw.rectangle((0, 136, W, 148), fill=TEAL)
    mtext(draw, (70, 36), title, WHITE, F_TITLE)
    mtext(draw, (72, 105), subtitle, "#cce7f0", F_SUB)
    rounded(draw, (1490, 42, 1820, 92), "#e7f6ef", None, 18, 0)
    draw.text((1655, 67), "First Review Slide", font=F_SMALL_B, fill=NAVY, anchor="mm")
    return img, draw


def footer(draw, note):
    draw.rectangle((0, 1048, W, H), fill=NAVY)
    mtext(draw, (70, 1057), note, "#d7edf2", font("arial.ttf", 18))


def literature_review():
    img, draw = slide_base("Literature Review", "Poultry Carcass Defect Detection")
    mtext(draw, (70, 190), "Related Work Summary", NAVY, F_H)

    rows = [
        (
            "Automated detection for chicken carcass quality control",
            "Biosystems Engineering",
            "2026",
            "Improved YOLOv7 for carcass-part localization + ResNet50 for defect recognition.",
            "Strong multiscale localization and recognition for broken wings, severed heads, swollen joints, and exposed leg bone.",
        ),
        (
            "Detecting wing fractures in chickens using deep learning",
            "Poultry Science; Libera et al.",
            "2025",
            "3D ResNet34 on CT scans; EfficientNetV2 on photographs.",
            "Shows poultry injury detection can be automated, but bruise detection is harder than fracture detection.",
        ),
        (
            "Applications of computer vision systems for meat safety assurance in abattoirs",
            "Food Control; Sandberg et al.",
            "2023",
            "Systematic review of carcass/organ lesion and contamination CVS.",
            "Found many promising systems, but few real-time abattoir validations, creating a deployment gap.",
        ),
        (
            "The application of computer vision systems in meat science and industry",
            "Meat Science; Modzelewska-Kapitula & Jun",
            "2022",
            "Review of computer vision for meat and carcass quality.",
            "Confirms CVS is fast, objective, non-contact, and suitable for quality and defect assessment.",
        ),
    ]
    headers = ["Journal Title", "Journal / Authors", "Year", "Technology Used", "Key Findings"]
    col_w = [430, 340, 110, 410, 490]
    x, y = 70, 270
    row_h, head_h = 142, 58
    table_w = sum(col_w)
    rounded(draw, (x, y, x + table_w, y + head_h + row_h * len(rows)), WHITE, LINE)
    draw.rectangle((x + 1, y + 1, x + table_w - 1, y + head_h), fill=HEADER)

    cx = x
    for i, width in enumerate(col_w):
        draw.line((cx, y, cx, y + head_h + row_h * len(rows)), fill=LINE, width=2)
        mtext(draw, (cx + 12, y + 17), headers[i], NAVY, F_TABLE_B)
        cx += width
    draw.line((x + table_w, y, x + table_w, y + head_h + row_h * len(rows)), fill=LINE, width=2)
    draw.line((x, y + head_h, x + table_w, y + head_h), fill=LINE, width=2)

    wrap_widths = [31, 25, 6, 31, 39]
    for r, row in enumerate(rows):
        ry = y + head_h + r * row_h
        if r % 2:
            draw.rectangle((x + 1, ry, x + table_w - 1, ry + row_h), fill="#f8fbff")
        draw.line((x, ry, x + table_w, ry), fill="#d9e2ec", width=1)
        cx = x
        for c, value in enumerate(row):
            mtext(draw, (cx + 12, ry + 12), wrap(value, wrap_widths[c]), TEXT, F_TABLE, spacing=4)
            cx += col_w[c]

    rounded(draw, (70, 920, 1850, 1018), WHITE, LINE)
    mtext(draw, (96, 942), "Project Fit", NAVY, F_CARD_H)
    mtext(
        draw,
        (270, 942),
        wrap(
            "Your project applies this direction as a YOLO26-based web system with image upload, video upload, live frame detection, annotated outputs, and 11 poultry carcass defect classes.",
            118,
        ),
        MUTED,
        F_BODY,
    )
    footer(draw, "Defect classes: bile, bruise, dislocation, feather, fracture, hematoma, scratch, skin-rash, abnormal-carcass, technical-failure, fecal-contamination.")
    img.save(DOCS / "literature_review.png", quality=95)


def research_gaps():
    img, draw = slide_base("Research Gaps", "What current work misses for your implemented system")
    mtext(draw, (70, 190), "Research Gaps Identified", NAVY, F_H)

    gaps = [
        ("1", "Static-image focus", "Many studies work on still images or controlled lab samples. Your project needs image, video, and live camera/frame inference through a web interface."),
        ("2", "Small and similar-looking defects", "Bruise, hematoma, scratch, skin-rash, bile, and fecal-contamination can be subtle or visually similar, so class confusion is a real project risk."),
        ("3", "Production-line variation", "Carcass pose, blur, reflections, camera angle, and lighting changes can reduce detection quality outside a prepared dataset."),
        ("4", "Deployment gap", "Research often reports model metrics only. Your project also needs Flask APIs, output storage, confidence control, and browser-side usability."),
        ("5", "Traceability and analysis", "The current system returns detection JSON and summaries, but long-term database logging and inspection history are not yet implemented."),
        ("6", "Model portability", "The repo includes PyTorch weights and ONNX output, but edge-device benchmarking and hardware-specific optimization remain future work."),
    ]

    positions = [(70, 285), (680, 285), (1290, 285), (70, 550), (680, 550), (1290, 550)]
    colors = ["#1f5f8b", "#2b8a7e", "#7a5cbd", "#b85757", "#6b7d2b", "#4b6475"]
    for (num, title, body), (x, y), color in zip(gaps, positions, colors):
        rounded(draw, (x, y, x + 560, y + 215), WHITE, LINE)
        draw.ellipse((x + 24, y + 24, x + 76, y + 76), fill=color)
        draw.text((x + 50, y + 50), num, font=F_BODY_B, fill=WHITE, anchor="mm")
        mtext(draw, (x + 96, y + 25), title, NAVY, F_CARD_H)
        mtext(draw, (x + 96, y + 68), wrap(body, 43), MUTED, F_SMALL, spacing=5)

    rounded(draw, (70, 850, 1850, 1015), WHITE, LINE)
    mtext(draw, (98, 874), "How the project addresses them", NAVY, F_CARD_H)
    points = [
        "YOLO26-family detection for object localization.",
        "Image upload, video upload, and live frame routes.",
        "Confidence and IoU threshold tuning.",
        "Annotated media, JSON detections, summary, and inference time.",
    ]
    for idx, point in enumerate(points):
        y = 928 + (idx % 2) * 48
        x = 105 + (idx // 2) * 860
        draw.rectangle((x, y + 5, x + 12, y + 17), fill=TEAL)
        mtext(draw, (x + 24, y), point, TEXT, F_SMALL_B)

    footer(draw, "Gap analysis is aligned with the repo's Flask API, OpenCV processing, YOLO model artifacts, and 11-class poultry defect dataset.")
    img.save(DOCS / "research_gaps.png", quality=95)


def proposed_system():
    img, draw = slide_base("Proposed System", "YOLO-based poultry carcass defect detection web platform")
    mtext(draw, (70, 190), "System Workflow", NAVY, F_H)

    steps = [
        ("Raw Datasets", "Roboflow / merged poultry defect datasets"),
        ("Dataset Prep", "prepare_yolo26_dataset.py creates YOLO train/valid/test"),
        ("Model Training", "YOLO26_model.ipynb trains detector on 11 classes"),
        ("Model Artifacts", "best.pt, last.pt, and best.onnx stored under runs/"),
        ("Flask Backend", "/api/detect/image, /frame, /video routes"),
        ("Inference Engine", "Ultralytics YOLO + OpenCV frame/video processing"),
        ("Frontend", "Browser UI for upload, camera, threshold controls"),
        ("Results", "Annotated output, boxes, confidence, summary, inference time"),
    ]
    positions = [(120, 300), (520, 300), (920, 300), (1320, 300), (120, 610), (520, 610), (920, 610), (1320, 610)]
    colors = ["#1f5f8b", "#2b8a7e", "#7a5cbd", "#b85757", "#6b7d2b", "#4b6475", "#2f8077", "#8a5d3b"]
    box_w, box_h = 320, 170

    for i, ((title, desc), (x, y), color) in enumerate(zip(steps, positions, colors)):
        rounded(draw, (x, y, x + box_w, y + box_h), color, "#ffffff", 8, 2)
        draw.text((x + 22, y + 22), f"{i + 1}", font=F_CARD_H, fill="#e8f6ff")
        mtext(draw, (x + 70, y + 25), title, WHITE, F_CARD_H)
        mtext(draw, (x + 24, y + 78), wrap(desc, 28), "#eef8ff", F_SMALL, spacing=5)

    arrows = [
        ((440, 385), (520, 385)),
        ((840, 385), (920, 385)),
        ((1240, 385), (1320, 385)),
        ((1480, 470), (1480, 610)),
        ((1320, 695), (1240, 695)),
        ((920, 695), (840, 695)),
        ((520, 695), (440, 695)),
    ]
    for (x0, y0), (x1, y1) in arrows:
        draw.line((x0, y0, x1, y1), fill="#708497", width=6)
        if x1 > x0:
            draw.polygon([(x1, y1), (x1 - 18, y1 - 10), (x1 - 18, y1 + 10)], fill="#708497")
        elif x1 < x0:
            draw.polygon([(x1, y1), (x1 + 18, y1 - 10), (x1 + 18, y1 + 10)], fill="#708497")
        else:
            draw.polygon([(x1, y1), (x1 - 10, y1 - 18), (x1 + 10, y1 - 18)], fill="#708497")

    rounded(draw, (70, 842, 1850, 1015), WHITE, LINE)
    mtext(draw, (98, 865), "Technologies Used", NAVY, F_CARD_H)
    tech = [
        "YOLO26 / Ultralytics",
        "OpenCV",
        "Flask + CORS",
        "PyTorch weights",
        "ONNX export",
        "HTML, CSS, JavaScript",
        "Confidence: 0.35",
        "IoU: 0.45",
    ]
    for i, item in enumerate(tech):
        x = 100 + (i % 4) * 430
        y = 925 + (i // 4) * 48
        rounded(draw, (x, y, x + 350, y + 34), "#eaf4f2", None, 16, 0)
        draw.text((x + 175, y + 17), item, font=F_SMALL_B, fill=NAVY, anchor="mm")

    footer(draw, "Actual repo flow: dataset preparation -> YOLO training -> Flask/OpenCV inference -> browser results.")
    img.save(DOCS / "proposed_system.png", quality=95)


def main():
    literature_review()
    research_gaps()
    proposed_system()
    print(DOCS / "literature_review.png")
    print(DOCS / "research_gaps.png")
    print(DOCS / "proposed_system.png")


if __name__ == "__main__":
    main()
