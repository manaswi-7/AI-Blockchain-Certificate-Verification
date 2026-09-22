"""Generate a clean paired certificate-tampering dataset.

IMPORTANT:
- This script NEVER redraws the certificate template.
- It starts from the exact clean template image supplied by the project.
- It preserves the template dimensions and all fixed layout elements.
- It writes no class/tamper labels into certificate pixels.
- Every tampered image is derived from its corresponding genuine image.

Expected template:
    certificate_generation/template/real_name.png

Expected template size:
    2048 x 1447

Output:
    certificate_generation/dataset/real/*.png
    certificate_generation/dataset/tampered/*.png
    certificate_generation/dataset/metadata.csv
"""
from __future__ import annotations

from pathlib import Path
import argparse
import csv
import random
import shutil

from PIL import Image, ImageDraw, ImageFont
import qrcode

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "template" / "real_name.png"
DATASET = ROOT / "dataset"
REAL = DATASET / "real"
TAMPERED = DATASET / "tampered"

WIDTH, HEIGHT = 2048, 1447
SEED = 42

BLUE = (10, 20, 130)
BLACK = (25, 25, 25)
WHITE = (255, 255, 255)
GREEN = (0, 100, 0)

FONT_REGULAR = "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"

FIRST_NAMES = [
    "Aarav", "Aadhya", "Abhinav", "Aditya", "Akash", "Ananya", "Anirudh",
    "Anjali", "Arjun", "Ashwin", "Bhavana", "Chaitanya", "Charan", "Deepak",
    "Diya", "Divya", "Eesha", "Gautam", "Harini", "Harsha", "Ishita",
    "Jahnavi", "Karthik", "Keerthi", "Krishna", "Lakshmi", "Manoj",
    "Meghana", "Mohan", "Nandini", "Navya", "Neha", "Nikhil", "Nisha",
    "Pavan", "Pranav", "Pranitha", "Priya", "Rahul", "Rakesh", "Ravi",
    "Riya", "Rohit", "Sahana", "Saketh", "Sanjana", "Sanjay", "Shreya",
    "Siddharth", "Sneha", "Srinivas", "Srujana", "Swathi", "Tanvi",
    "Tejas", "Vaishnavi", "Varun", "Vasavi", "Vignesh", "Vijay",
    "Vishal", "Yash", "Yamini",
]
LAST_NAMES = [
    "Reddy", "Rao", "Sharma", "Patel", "Kumar", "Singh", "Nair", "Iyer",
    "Varma", "Verma", "Naidu", "Goud", "Gupta", "Mehta", "Joshi",
    "Deshmukh", "Das", "Mishra", "Khan", "Bose", "Chowdary", "Kandula",
    "Pothula", "Vemula", "Konda", "Yadav", "Bansal", "Agarwal", "Kapoor",
    "Malhotra", "Menon", "Pillai", "Shetty", "Hegde", "Kulkarni", "Jain",
]
DEPARTMENTS = [
    "Information Technology",
    "Computer Science",
    "Artificial Intelligence",
]
COURSES = [
    ("CS401", "Machine Learning", 4),
    ("CS402", "Database Systems", 3),
    ("CS403", "Artificial Intelligence", 4),
    ("CS404", "Computer Networks", 3),
    ("CS405", "Data Mining", 4),
    ("CS406", "Software Engineering", 3),
]
GRADE_POINTS = [("O", 10), ("A+", 9), ("A", 8), ("B+", 7), ("B", 6)]

# Exact text-field positions measured from the supplied 2048x1447 template.
FIELDS = {
    "certificate_id": (410, 218, 780, 256),
    "date": (410, 258, 700, 296),
    "name": (410, 299, 930, 335),
    "roll": (410, 337, 760, 375),
    "department": (410, 376, 760, 410),
    "semester": (410, 414, 650, 448),
    "academic_year": (410, 454, 760, 490),
}

# Table vertical boundaries from the supplied template.
COLS = [42, 147, 667, 767, 865, 963, 1061, 1159]
TABLE_TOP = 704
HEADER_HEIGHT = 45
ROW_HEIGHT = 45


def font(size: int, bold: bool = False):
    path = FONT_BOLD if bold else FONT_REGULAR
    if Path(path).exists():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def require_template() -> Image.Image:
    if not TEMPLATE.exists():
        raise FileNotFoundError(
            f"Exact template is missing: {TEMPLATE}\n"
            "Put the supplied clean certificate image at that path. "
            "Do not use a recreated/redrawn template."
        )
    image = Image.open(TEMPLATE).convert("RGB")
    if image.size != (WIDTH, HEIGHT):
        raise ValueError(
            f"Template size is {image.size}; expected {(WIDTH, HEIGHT)}. "
            "The template must not be resized."
        )
    return image


def clear_box(draw: ImageDraw.ImageDraw, box):
    draw.rectangle(box, fill=WHITE)


def put_left(draw, xy, text, size=18, color=BLUE):
    draw.text(xy, text, fill=color, font=font(size))


def put_center(draw, box, text, size=12, color=BLACK):
    x1, y1, x2, y2 = box
    f = font(size)
    bb = draw.textbbox((0, 0), str(text), font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = x1 + max(0, (x2 - x1 - tw) / 2)
    y = y1 + max(0, (y2 - y1 - th) / 2) - 1
    draw.text((int(x), int(y)), str(text), fill=color, font=f)


def random_name(rng: random.Random, current: str) -> str:
    while True:
        value = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if value != current:
            return value


def make_record(index: int):
    rng = random.Random(SEED + index)
    cert_id = f"CERT2025{index + 1:06d}"
    name = f"{FIRST_NAMES[index % len(FIRST_NAMES)]} {LAST_NAMES[(index * 7) % len(LAST_NAMES)]}"
    roll = f"FTU24{index + 1:04d}"
    day = index % 28 + 1
    month = index % 12 + 1
    date = f"{day:02d}-{month:02d}-2025"
    dept = DEPARTMENTS[index % len(DEPARTMENTS)]
    semester = ["IV", "V", "VI", "VII", "VIII"][index % 5]
    academic_year = f"{2024 + index % 3}-{2025 + index % 3}"

    rows = []
    grade_points = []
    for j, (code, subject, credits) in enumerate(COURSES):
        internal = 20 + ((index * 7 + j * 3) % 11)
        external = 35 + ((index * 11 + j * 5) % 36)
        total = internal + external
        grade, gp = GRADE_POINTS[(index + j) % len(GRADE_POINTS)]
        rows.append([code, subject, credits, internal, external, total, grade])
        grade_points.append((credits, gp))

    sgpa = round(
        sum(credits * gp for credits, gp in grade_points)
        / sum(credits for credits, _ in grade_points),
        2,
    )
    cgpa = round(6.85 + ((index * 37) % 140) / 100, 2)

    return {
        "certificate_id": cert_id,
        "name": name,
        "roll": roll,
        "date": date,
        "department": dept,
        "semester": semester,
        "academic_year": academic_year,
        "rows": rows,
        "sgpa": sgpa,
        "cgpa": cgpa,
        "seed": rng.randint(0, 10**9),
    }


def redraw_variable_fields(template: Image.Image, record: dict) -> Image.Image:
    """Create a genuine certificate by changing only variable content."""
    out = template.copy()
    d = ImageDraw.Draw(out)

    for key, value in [
        ("certificate_id", record["certificate_id"]),
        ("date", record["date"]),
        ("name", record["name"]),
        ("roll", record["roll"]),
        ("department", record["department"]),
        ("semester", record["semester"]),
        ("academic_year", record["academic_year"]),
    ]:
        clear_box(d, FIELDS[key])
        x = FIELDS[key][0] + 6
        y = FIELDS[key][1] + 5
        put_left(d, (x, y), value, 18, BLUE)

    # Table values only; borders/header remain untouched.
    for row_index, row in enumerate(record["rows"]):
        y1 = TABLE_TOP + HEADER_HEIGHT + row_index * ROW_HEIGHT
        y2 = y1 + ROW_HEIGHT
        for col_index, value in enumerate(row):
            if col_index == 2:
                size = 12
            else:
                size = 12
            put_center(
                d,
                (COLS[col_index] + 3, y1 + 3, COLS[col_index + 1] - 3, y2 - 3),
                value,
                size,
                BLACK,
            )

    # SGPA / CGPA value regions only.
    clear_box(d, (145, 1080, 220, 1115))
    put_left(d, (160, 1087), f"{record['sgpa']:.2f}", 17, GREEN)
    clear_box(d, (455, 1080, 525, 1115))
    put_left(d, (465, 1087), f"{record['cgpa']:.2f}", 17, GREEN)

    # Barcode text and bars are variable data, but their layout stays fixed.
    rng = random.Random(record["seed"])
    d.rectangle((690, 1118, 990, 1178), fill=WHITE)
    x = 700
    while x < 970:
        width = rng.choice([2, 3, 4])
        if rng.random() < 0.58:
            d.rectangle((x, 1125, x + width, 1165), fill=BLACK)
        x += width + rng.choice([2, 3, 4])
    d.text((700, 1173), record["certificate_id"], fill=BLACK, font=font(10))

    # QR value changes, QR frame/position/size does not.
    qr = qrcode.QRCode(version=2, box_size=4, border=1)
    qr.add_data(
        f"{record['certificate_id']}|{record['name']}|{record['roll']}"
    )
    qr.make(fit=True)
    q = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    q = q.resize((120, 120), Image.Resampling.NEAREST)
    out.paste(q, (740, 322))

    # Photo's printed roll number follows the record; frame/photo layout remains.
    clear_box(d, (1432, 466, 1560, 486))
    d.text((1435, 470), record["roll"], fill=BLACK, font=font(7))

    return out


def replace_text_field(image: Image.Image, field: str, value: str):
    out = image.copy()
    d = ImageDraw.Draw(out)
    box = FIELDS[field]
    clear_box(d, box)
    put_left(d, (box[0] + 6, box[1] + 5), value, 18, BLUE)
    return out


def replace_table_cell(image: Image.Image, row: int, col: int, value):
    out = image.copy()
    d = ImageDraw.Draw(out)
    y1 = TABLE_TOP + HEADER_HEIGHT + row * ROW_HEIGHT
    y2 = y1 + ROW_HEIGHT
    box = (COLS[col] + 3, y1 + 3, COLS[col + 1] - 3, y2 - 3)
    clear_box(d, box)
    put_center(d, box, value, 12, BLACK)
    return out


def tamper_one_field(genuine: Image.Image, record: dict, index: int):
    """Return exactly one realistic content manipulation per genuine image."""
    rng = random.Random(SEED * 1000 + index)
    kinds = [
        "name", "date", "certificate_id", "roll_number",
        "marks", "grade", "subject", "academic_year", "qr", "photo"
    ]
    kind = kinds[index % len(kinds)]

    if kind == "name":
        return replace_text_field(genuine, "name", random_name(rng, record["name"])), kind

    if kind == "date":
        new_date = f"{rng.randint(1,28):02d}-{rng.randint(1,12):02d}-{rng.choice([2025,2026,2027])}"
        return replace_text_field(genuine, "date", new_date), kind

    if kind == "certificate_id":
        new_id = f"CERT2025{rng.randint(900001,999999):06d}"
        return replace_text_field(genuine, "certificate_id", new_id), kind

    if kind == "roll_number":
        new_roll = f"FTU24{rng.randint(5000,9999):04d}"
        return replace_text_field(genuine, "roll", new_roll), kind

    if kind == "marks":
        row = rng.randrange(6)
        col = 4  # External
        old = int(record["rows"][row][col])
        delta = rng.choice([-9, -6, 6, 9])
        new_value = str(max(35, min(70, old + delta)))
        return replace_table_cell(genuine, row, col, new_value), kind

    if kind == "grade":
        row = rng.randrange(6)
        old = record["rows"][row][6]
        options = [g for g, _ in GRADE_POINTS if g != old]
        return replace_table_cell(genuine, row, 6, rng.choice(options)), kind

    if kind == "subject":
        row = rng.randrange(6)
        old = record["rows"][row][1]
        options = [subject for _, subject, _ in COURSES if subject != old]
        return replace_table_cell(genuine, row, 1, rng.choice(options)), kind

    if kind == "academic_year":
        start = rng.choice([2023, 2025, 2026])
        return replace_text_field(genuine, "academic_year", f"{start}-{start + 1}"), kind

    if kind == "qr":
        out = genuine.copy()
        qr = qrcode.QRCode(version=2, box_size=4, border=1)
        qr.add_data(f"{record['certificate_id']}|{random_name(rng, record['name'])}|{record['roll']}")
        qr.make(fit=True)
        q = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        q = q.resize((120, 120), Image.Resampling.NEAREST)
        out.paste(q, (740, 322))
        return out, kind

    # photo: keep the exact frame, size and position; change only the image content.
    out = genuine.copy()
    d = ImageDraw.Draw(out)
    d.rectangle((1429, 249, 1592, 492), fill=(255, 250, 220), outline=(40, 40, 40), width=2)
    skin = rng.choice([(230, 170, 120), (205, 140, 95), (245, 190, 145)])
    shirt = rng.choice([(20, 70, 120), (70, 60, 130), (110, 70, 40)])
    d.ellipse((1480, 267, 1540, 327), fill=skin, outline=(20, 20, 20))
    d.rectangle((1460, 330, 1560, 455), fill=shirt)
    d.text((1435, 470), record["roll"], fill=BLACK, font=font(7))
    return out, kind


def validate_pair(genuine: Image.Image, tampered: Image.Image):
    if genuine.size != (WIDTH, HEIGHT) or tampered.size != (WIDTH, HEIGHT):
        raise ValueError("A generated image changed the template dimensions.")
    # The pair must differ; there must be no full-image replacement.
    if genuine.tobytes() == tampered.tobytes():
        raise ValueError("Tampered image is identical to genuine image.")


def generate(count: int = 500, seed: int = SEED):
    global SEED
    SEED = seed

    template = require_template()
    if REAL.exists():
        shutil.rmtree(REAL)
    if TAMPERED.exists():
        shutil.rmtree(TAMPERED)
    REAL.mkdir(parents=True, exist_ok=True)
    TAMPERED.mkdir(parents=True, exist_ok=True)

    metadata_path = DATASET / "metadata.csv"
    with metadata_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "certificate_id", "real_file", "tampered_file",
            "tamper_type", "name", "roll_number", "date",
            "department", "semester", "academic_year"
        ])

        for i in range(count):
            record = make_record(i)
            genuine = redraw_variable_fields(template, record)
            tampered, tamper_type = tamper_one_field(genuine, record, i)
            validate_pair(genuine, tampered)

            real_name = f"{record['certificate_id']}.png"
            tampered_name = f"{record['certificate_id']}__{tamper_type}.png"

            genuine.save(REAL / real_name, optimize=True)
            tampered.save(TAMPERED / tampered_name, optimize=True)

            writer.writerow([
                record["certificate_id"], real_name, tampered_name,
                tamper_type, record["name"], record["roll"],
                record["date"], record["department"], record["semester"],
                record["academic_year"],
            ])

    print(f"Generated {count} genuine + {count} tampered images.")
    print(f"Real: {REAL}")
    print(f"Tampered: {TAMPERED}")
    print(f"Metadata: {metadata_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(max(1, args.count), args.seed)
