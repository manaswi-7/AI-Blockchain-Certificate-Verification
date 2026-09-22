"""Canonical certificate dataset generator.

There is exactly one certificate renderer in this project: `template()`.
Both genuine and tampered samples are created from that same rendered
certificate, so the layout, dimensions, typography, QR area, photo area,
marks table, and footer never change.

Tampering changes only one local field/region. No class label or warning text
is ever drawn into an image.
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
DATASET = ROOT / "dataset"
REAL = DATASET / "real"
TAMPERED = DATASET / "tampered"

W, H = 2048, 1447
SEED = 42

BLUE = (10, 20, 130)
BLACK = (25, 25, 25)
WHITE = (255, 255, 255)
GREEN = (0, 100, 0)

REGULAR = "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"

FIRST_NAMES = [
    "Aarav","Aadhya","Abhinav","Aditya","Akash","Ananya","Anirudh","Anjali",
    "Arjun","Ashwin","Bhavana","Chaitanya","Charan","Deepak","Diya","Divya","Eesha",
    "Gautam","Harini","Harsha","Ishita","Jahnavi","Karthik","Keerthi","Krishna",
    "Lakshmi","Manoj","Meghana","Mohan","Nandini","Navya","Neha","Nikhil","Nisha",
    "Pavan","Pranav","Pranitha","Priya","Rahul","Rakesh","Ravi","Riya","Rohit",
    "Sahana","Saketh","Sanjana","Sanjay","Shreya","Siddharth","Sneha","Srinivas",
    "Srujana","Swathi","Tanvi","Tejas","Vaishnavi","Varun","Vasavi","Vignesh",
    "Vijay","Vishal","Yash","Yamini"
]
LAST_NAMES = [
    "Reddy","Rao","Sharma","Patel","Kumar","Singh","Nair","Iyer","Varma",
    "Verma","Naidu","Goud","Gupta","Mehta","Joshi","Deshmukh","Das","Mishra","Khan",
    "Bose","Chowdary","Kandula","Pothula","Vemula","Konda","Yadav","Bansal","Agarwal",
    "Kapoor","Malhotra","Menon","Pillai","Shetty","Hegde","Kulkarni","Jain"
]
DEPARTMENTS = ["Information Technology", "Computer Science", "Artificial Intelligence"]
COURSES = [
    ("CS401","Machine Learning",4), ("CS402","Database Systems",3),
    ("CS403","Artificial Intelligence",4), ("CS404","Computer Networks",3),
    ("CS405","Data Mining",4), ("CS406","Software Engineering",3)
]
GRADES = [("O",10),("A+",9),("A",8),("B+",7),("B",6)]


def fnt(size, bold=False):
    path = BOLD if bold else REGULAR
    return ImageFont.truetype(path, size) if Path(path).exists() else ImageFont.load_default()


def center(d, box, value, size=12, color=BLACK, bold=False):
    x1, y1, x2, y2 = box
    ft = fnt(size, bold)
    bb = d.textbbox((0, 0), str(value), font=ft)
    d.text(
        (x1 + (x2 - x1 - (bb[2] - bb[0])) / 2,
         y1 + (y2 - y1 - (bb[3] - bb[1])) / 2 - 1),
        str(value), fill=color, font=ft
    )


def qr_image(value):
    q = qrcode.QRCode(version=2, box_size=4, border=1)
    q.add_data(value)
    q.make(fit=True)
    return q.make_image(fill_color="black", back_color="white").convert("RGB").resize(
        (120, 120), Image.Resampling.NEAREST
    )


def record(i):
    rows = []
    points = []
    for j, (code, subject, credits) in enumerate(COURSES):
        internal = 20 + ((i * 7 + j * 3) % 11)
        external = 35 + ((i * 11 + j * 5) % 36)
        total = internal + external
        grade, gp = GRADES[(i + j) % len(GRADES)]
        rows.append([code, subject, credits, internal, external, total, grade])
        points.append((credits, gp))

    return {
        "id": f"CERT2025{i + 1:06d}",
        "name": f"{FIRST_NAMES[i % len(FIRST_NAMES)]} {LAST_NAMES[(i * 7) % len(LAST_NAMES)]}",
        "roll": f"FTU24{i + 1:04d}",
        "date": f"{i % 28 + 1:02d}-{i % 12 + 1:02d}-2025",
        "dept": DEPARTMENTS[i % len(DEPARTMENTS)],
        "sem": ["IV", "V", "VI", "VII", "VIII"][i % 5],
        "year": f"{2024 + i % 3}-{2025 + i % 3}",
        "rows": rows,
        "sgpa": round(sum(c * g for c, g in points) / sum(c for c, _ in points), 2),
        "cgpa": round(6.85 + ((i * 37) % 140) / 100, 2),
        "seed": random.Random(SEED + i).randint(0, 10**9),
    }


def template(s):
    """Render the fixed certificate layout. Never add dataset labels."""
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)

    d.rectangle((23, 23, W - 23, H - 23), outline=(20, 20, 20), width=3)
    d.rounded_rectangle(
        (35, 42, W - 35, 173), radius=12, fill=(235, 244, 255),
        outline=(55, 110, 245), width=2
    )
    d.ellipse((74, 72, 170, 168), outline=(25, 75, 170), width=3)
    d.ellipse((88, 86, 156, 154), outline=(25, 75, 170), width=2)
    d.polygon(
        [(122, 96), (151, 110), (143, 143), (122, 157), (101, 143), (94, 110)],
        fill=(224, 237, 255), outline=(130, 155, 200)
    )
    d.text((197, 64), "FUTURETECH UNIVERSITY", fill=(8, 28, 130), font=fnt(36, True))
    d.text((198, 111), "Autonomous | NAAC A++ | UGC Approved", fill=BLACK, font=fnt(17))
    d.text((798, 176), "ACADEMIC GRADE MEMORANDUM", fill=BLACK, font=fnt(25, True))

    d.rectangle((42, 195, 1005, 628), outline=(155, 155, 155), width=2)
    info = [
        ("Certificate ID", s["id"]), ("Issue Date", s["date"]),
        ("Student Name", s["name"]), ("Roll Number", s["roll"]),
        ("Department", s["dept"]), ("Semester", s["sem"]),
        ("Academic Year", s["year"])
    ]
    ys = [228, 267, 306, 345, 384, 423, 462]
    for (label, value), y in zip(info, ys):
        d.text((75, y), label, fill=BLACK, font=fnt(18, True))
        d.text((378, y), ":", fill=BLACK, font=fnt(18))
        d.text((416, y), value, fill=BLUE, font=fnt(18))

    d.rectangle((1018, 300, 1182, 464), fill=WHITE, outline=(40, 40, 40), width=2)
    im.paste(qr_image(f'{s["id"]}|{s["name"]}|{s["roll"]}'), (1040, 322))

    d.rectangle((1360, 198, 1660, 528), outline=(70, 70, 70), width=2)
    d.rectangle((1428, 248, 1593, 493), fill=(255, 250, 220), outline=(40, 40, 40), width=2)
    d.ellipse((1480, 267, 1540, 327), fill=(255, 190, 120), outline=BLACK)
    d.rectangle((1460, 330, 1560, 455), fill=(0, 105, 0))
    d.text((1435, 470), s["roll"], fill=BLACK, font=fnt(7))

    x0, y0 = 42, 704
    widths = [105, 520, 100, 98, 98, 98, 98]
    xs = [x0]
    for width in widths:
        xs.append(xs[-1] + width)
    headers = ["Course", "Subject Name", "Credits", "Internal", "External", "Total", "Grade"]
    d.rectangle((x0, y0, xs[-1], y0 + 315), outline=(80, 80, 80), width=2)
    d.rectangle((x0, y0, xs[-1], y0 + 45), fill=(220, 235, 255))
    for x in xs[1:-1]:
        d.line((x, y0, x, y0 + 315), fill=(100, 100, 100), width=1)
    for k, h in enumerate(headers):
        center(d, (xs[k], y0, xs[k + 1], y0 + 45), h, 13, BLACK, True)
    for r, row in enumerate(s["rows"]):
        yy = y0 + 45 + r * 45
        d.line((x0, yy, xs[-1], yy), fill=(205, 205, 205), width=1)
        for k, value in enumerate(row):
            center(d, (xs[k], yy, xs[k + 1], yy + 45), value, 12)

    d.line((42, 1055, 1985, 1055), fill=(150, 150, 150), width=1)
    d.text((70, 1090), "SGPA:", fill=BLACK, font=fnt(17, True))
    d.text((160, 1090), f'{s["sgpa"]:.2f}', fill=GREEN, font=fnt(17, True))
    d.text((375, 1090), "CGPA:", fill=BLACK, font=fnt(17, True))
    d.text((465, 1090), f'{s["cgpa"]:.2f}', fill=GREEN, font=fnt(17, True))

    rng = random.Random(s["seed"])
    x = 700
    while x < 970:
        width = rng.choice([2, 3, 4])
        if rng.random() < 0.55:
            d.rectangle((x, 1125, x + width, 1165), fill=BLACK)
        x += width + rng.choice([2, 3, 4])
    d.text((700, 1173), s["id"], fill=BLACK, font=fnt(10))

    d.ellipse((1010, 1095, 1090, 1175), outline=(40, 100, 230), width=3)
    d.ellipse((1023, 1108, 1077, 1162), outline=(80, 130, 240), width=1)
    d.arc((1450, 1110, 1570, 1160), 180, 350, fill=(60, 90, 160), width=2)
    d.line((1455, 1148, 1560, 1122), fill=(60, 90, 160), width=2)
    d.line((1430, 1170, 1610, 1170), fill=(40, 40, 40), width=1)
    d.text((1450, 1183), "Controller of Examinations", fill=BLACK, font=fnt(12, True))
    return im


def replacement_name(rng, current):
    while True:
        value = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if value != current:
            return value


def replace_field(im, box, value, size=18, color=BLUE):
    out = im.copy()
    d = ImageDraw.Draw(out)
    d.rectangle(box, fill=WHITE)
    d.text((box[0] + 6, box[1] + 5), value, fill=color, font=fnt(size))
    return out


def replace_cell(im, row, col, value):
    out = im.copy()
    d = ImageDraw.Draw(out)
    xs = [42, 147, 667, 767, 865, 963, 1061, 1159]
    y = 704 + 45 + row * 45
    box = (xs[col] + 3, y + 3, xs[col + 1] - 3, y + 42)
    d.rectangle(box, fill=WHITE)
    center(d, box, value, 12)
    return out


def tamper(im, s, i):
    rng = random.Random(SEED * 1000 + i)
    kind = [
        "name", "date", "certificate_id", "roll_number", "marks",
        "grade", "subject", "academic_year", "qr", "photo"
    ][i % 10]

    if kind == "name":
        return replace_field(im, (410, 299, 930, 335), replacement_name(rng, s["name"])), kind
    if kind == "date":
        value = f"{rng.randint(1, 28):02d}-{rng.randint(1, 12):02d}-{rng.choice([2025, 2026, 2027])}"
        return replace_field(im, (410, 258, 700, 296), value), kind
    if kind == "certificate_id":
        value = f"CERT2025{rng.randint(900001, 999999):06d}"
        return replace_field(im, (410, 218, 780, 256), value), kind
    if kind == "roll_number":
        value = f"FTU24{rng.randint(5000, 9999):04d}"
        return replace_field(im, (410, 337, 760, 375), value), kind
    if kind == "marks":
        row = rng.randrange(6)
        old = s["rows"][row][4]
        value = str(max(35, min(70, int(old) + rng.choice([-9, -6, 6, 9]))))
        return replace_cell(im, row, 4, value), kind
    if kind == "grade":
        row = rng.randrange(6)
        old = s["rows"][row][6]
        value = rng.choice([g for g, _ in GRADES if g != old])
        return replace_cell(im, row, 6, value), kind
    if kind == "subject":
        row = rng.randrange(6)
        old = s["rows"][row][1]
        value = rng.choice([x[1] for x in COURSES if x[1] != old])
        return replace_cell(im, row, 1, value), kind
    if kind == "academic_year":
        start = rng.choice([2023, 2025, 2026])
        return replace_field(im, (410, 454, 760, 490), f"{start}-{start + 1}"), kind
    if kind == "qr":
        out = im.copy()
        out.paste(
            qr_image(f'{s["id"]}|{replacement_name(rng, s["name"])}|{s["roll"]}|verification'),
            (1040, 322)
        )
        return out, kind

    out = im.copy()
    d = ImageDraw.Draw(out)
    d.rectangle((1428, 248, 1593, 493), fill=(255, 250, 220), outline=(40, 40, 40), width=2)
    skin = rng.choice([(230, 170, 120), (205, 140, 95), (245, 190, 145)])
    shirt = rng.choice([(20, 70, 120), (70, 60, 130), (110, 70, 40)])
    d.ellipse((1480, 267, 1540, 327), fill=skin, outline=BLACK)
    d.rectangle((1460, 330, 1560, 455), fill=shirt)
    d.text((1435, 470), s["roll"], fill=BLACK, font=fnt(7))
    return out, kind


def validate_pair_count(count):
    real = sorted(REAL.glob("*.png"))
    tampered = sorted(TAMPERED.glob("*.png"))
    real_ids = [p.stem for p in real]
    tampered_ids = [p.stem.split("__", 1)[0] for p in tampered]
    if len(real) != count or len(tampered) != count:
        raise RuntimeError(
            f"Expected {count} genuine + {count} tampered images; "
            f"found {len(real)} + {len(tampered)}."
        )
    if len(set(real_ids)) != count or len(set(tampered_ids)) != count:
        raise RuntimeError("Certificate IDs are not unique.")
    if set(real_ids) != set(tampered_ids):
        raise RuntimeError("Genuine/tampered certificate IDs are not a complete one-to-one pairing.")


def generate(count=500):
    if count < 1:
        raise ValueError("count must be at least 1")

    if REAL.exists():
        shutil.rmtree(REAL)
    if TAMPERED.exists():
        shutil.rmtree(TAMPERED)
    REAL.mkdir(parents=True, exist_ok=True)
    TAMPERED.mkdir(parents=True, exist_ok=True)
    DATASET.mkdir(parents=True, exist_ok=True)

    metadata_path = DATASET / "metadata.csv"
    with metadata_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow([
            "certificate_id", "real_file", "tampered_file", "tamper_type",
            "name", "roll_number", "date", "department", "semester", "academic_year"
        ])

        for i in range(count):
            s = record(i)
            genuine = template(s)
            edited, kind = tamper(genuine, s, i)

            if genuine.size != (W, H) or edited.size != (W, H):
                raise RuntimeError(f"Unexpected image size for {s['id']}")

            real_name = f'{s["id"]}.png'
            tampered_name = f'{s["id"]}__{kind}.png'
            genuine.save(REAL / real_name, optimize=True)
            edited.save(TAMPERED / tampered_name, optimize=True)

            writer.writerow([
                s["id"], real_name, tampered_name, kind, s["name"], s["roll"],
                s["date"], s["dept"], s["sem"], s["year"]
            ])

    validate_pair_count(count)
    print(f"Generated {count} genuine + {count} tampered certificates.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500)
    args = parser.parse_args()
    generate(args.count)
