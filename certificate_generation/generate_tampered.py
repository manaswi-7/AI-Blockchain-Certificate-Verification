"""Create realistic tampered copies without visual labels.

Tampered images keep the certificate template/layout and use neutral, plausible
edits. No image contains labels such as ORIGINAL, TAMPERED, FAKE or ALTERED.
The class label exists only in the filename/folder/metadata.
"""
from pathlib import Path
import argparse
import random
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REAL = ROOT / "dataset" / "real"
TAMPERED = ROOT / "dataset" / "tampered"

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BLUE = (10, 20, 130)
BLACK = (25, 25, 25)
WHITE = (255, 255, 255)

def font(size):
    return ImageFont.truetype(FONT_PATH, size) if Path(FONT_PATH).exists() else ImageFont.load_default()

def replacement_name(rng, old):
    first = ["Aarav","Aadhya","Abhinav","Aditya","Akash","Ananya","Arjun","Bhavana","Chaitanya","Diya","Harini","Ishita","Karthik","Meghana","Nandini","Neha","Nikhil","Pranav","Priya","Rahul","Riya","Rohit","Sanjana","Shreya","Sneha","Tanvi","Vaishnavi","Varun","Vignesh","Yash"]
    last = ["Reddy","Rao","Sharma","Patel","Kumar","Singh","Nair","Iyer","Varma","Naidu","Goud","Gupta","Mehta","Joshi","Das","Mishra","Khan","Bose","Naidu","Jain"]
    while True:
        value = f"{rng.choice(first)} {rng.choice(last)}"
        if value != old:
            return value

def edit(image, operation, rng):
    out = image.copy()
    d = ImageDraw.Draw(out)
    w, h = out.size

    if operation == "name_edit":
        # Same field, same blue ink, same font size; only content changes.
        d.rectangle((410, 300, 930, 334), fill=WHITE)
        d.text((416, 304), replacement_name(rng, ""), fill=BLUE, font=font(18))

    elif operation == "date_edit":
        d.rectangle((410, 260, 700, 294), fill=WHITE)
        d.text((416, 265), f"{rng.randint(1,28):02d}-{rng.randint(1,12):02d}-{rng.choice([2025,2026,2027])}", fill=BLUE, font=font(18))

    elif operation == "id_edit":
        d.rectangle((410, 220, 760, 254), fill=WHITE)
        d.text((416, 225), f"CERT2025{rng.randint(501,999):06d}", fill=BLUE, font=font(18))

    elif operation == "roll_edit":
        d.rectangle((410, 338, 760, 373), fill=WHITE)
        d.text((416, 343), f"FTU24{rng.randint(5000,9999):04d}", fill=BLUE, font=font(18))

    elif operation == "grade_edit":
        row = rng.randrange(6)
        y = 704 + 45 + row * 45
        d.rectangle((1061, y+8, 1158, y+38), fill=WHITE)
        value = rng.choice(["O","A+","A","B+","B"])
        d.text((1090, y+14), value, fill=BLACK, font=font(12))

    elif operation == "marks_edit":
        row = rng.randrange(6)
        y = 704 + 45 + row * 45
        value = str(rng.randint(35, 70))
        d.rectangle((865, y+8, 963, y+38), fill=WHITE)
        d.text((900, y+14), value, fill=BLACK, font=font(12))

    elif operation == "course_edit":
        row = rng.randrange(6)
        y = 704 + 45 + row * 45
        courses = ["Machine Learning","Database Systems","Artificial Intelligence","Computer Networks","Data Mining","Software Engineering"]
        d.rectangle((147, y+8, 667, y+38), fill=WHITE)
        d.text((190, y+14), rng.choice(courses), fill=BLACK, font=font(12))

    elif operation == "signature_edit":
        # Alternate blue signature strokes; no warning marks.
        d.arc((1450,1112,1575,1158),195,355,fill=(65,95,165),width=2)
        d.line((1455,1144,1568,1120),fill=(65,95,165),width=2)
        d.arc((1490,1100,1540,1150),190,320,fill=(65,95,165),width=2)

    elif operation == "photo_edit":
        d.rectangle((1428,248,1593,493),fill=(255,250,220),outline=(40,40,40),width=2)
        skin = rng.choice([(230,170,120),(205,140,95),(245,190,145)])
        shirt = rng.choice([(20,70,120),(70,60,130),(110,70,40)])
        d.ellipse((1480,267,1540,327),fill=skin,outline=(20,20,20))
        d.rectangle((1460,330,1560,455),fill=shirt)

    else:
        # Conservative visual manipulation: small local crop-and-replace.
        crop_w, crop_h = 180, 70
        x = rng.randint(180, w-crop_w-180)
        y = rng.randint(180, h-crop_h-180)
        patch = out.crop((x, y, x+crop_w, y+crop_h))
        target_x = min(w-crop_w-20, x + rng.randint(20, 80))
        target_y = min(h-crop_h-20, y + rng.randint(20, 80))
        out.paste(patch, (target_x, target_y))

    return out

OPERATIONS = ("name_edit","date_edit","id_edit","roll_edit","marks_edit","grade_edit","course_edit","signature_edit","photo_edit")

def generate(limit=None, seed=42):
    TAMPERED.mkdir(parents=True, exist_ok=True)
    sources = sorted(REAL.glob("*.png"))
    if limit is not None:
        sources = sources[:limit]
    if not sources:
        raise SystemExit("No genuine certificates found. Generate the genuine dataset first.")

    rng = random.Random(seed)
    created = 0
    for source in sources:
        original = Image.open(source).convert("RGB")
        selected = rng.sample(OPERATIONS, k=min(4, len(OPERATIONS)))
        for operation in selected:
            out = edit(original, operation, rng)
            out.save(TAMPERED / f"{source.stem}__{operation}.png")
            created += 1
    print(f"Created {created} tampered images in {TAMPERED}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.limit, args.seed)
