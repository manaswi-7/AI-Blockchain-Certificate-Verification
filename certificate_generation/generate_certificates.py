"""Generate synthetic certificate images for the AI training dataset.

The generated certificates are intentionally synthetic and should be used only
for model development/testing, not as real academic documents.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "generated"
REAL = ROOT / "dataset" / "real"

NAMES = [
    "Hasini Kandula", "Rahul Sharma", "Ananya Reddy", "Priya Nair",
    "Arjun Kumar", "Sneha Rao", "Aarav Singh", "Meghana Patel",
    "Karthik Varma", "Ishita Das", "Nikhil Reddy", "Sanjana Rao",
]
COURSES = [
    "Artificial Intelligence", "Python Programming", "Data Science",
    "Machine Learning", "Web Development", "Cloud Computing",
]
GRADES = ["A+", "A", "A-", "B+"]


def font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def centered(draw, text, y, fnt, width):
    box = draw.textbbox((0, 0), text, font=fnt)
    x = (width - (box[2] - box[0])) // 2
    draw.text((x, y), text, fill=(30, 30, 30), font=fnt)


def make_certificate(index: int, template: int = 0):
    width, height = 1600, 1100
    image = Image.new("RGB", (width, height), (248, 246, 238))
    draw = ImageDraw.Draw(image)

    margin = 55
    draw.rectangle((margin, margin, width - margin, height - margin), outline=(35, 55, 75), width=8)
    draw.rectangle((margin + 25, margin + 25, width - margin - 25, height - margin - 25), outline=(130, 100, 45), width=3)

    name = NAMES[index % len(NAMES)]
    course = COURSES[index % len(COURSES)]
    grade = GRADES[index % len(GRADES)]
    cert_id = f"CERT-2026-{index + 1:06d}"
    day = (index % 28) + 1
    month = (index % 12) + 1
    date = f"{day:02d}-{month:02d}-2026"

    if template == 1:
        issuer = "GNITS Institute of Technology"
        title_y = 155
    else:
        issuer = "G. Narayanamma Institute of Technology and Science"
        title_y = 145

    centered(draw, issuer, 95, font(36), width)
    centered(draw, "CERTIFICATE OF ACHIEVEMENT", title_y, font(58), width)
    centered(draw, "This is to certify that", 285, font(30), width)
    centered(draw, name, 350, font(52), width)
    centered(draw, "has successfully completed", 450, font(30), width)
    centered(draw, course, 510, font(45), width)
    centered(draw, f"Grade: {grade}", 600, font(30), width)
    centered(draw, f"Certificate ID: {cert_id}", 675, font(30), width)
    centered(draw, f"Issue Date: {date}", 730, font(30), width)

    draw.text((170, 880), "Authorized Signature", fill=(30, 30, 30), font=font(26))
    draw.line((150, 915, 460, 915), fill=(30, 30, 30), width=2)
    draw.text((1130, 880), "Institution Seal", fill=(30, 30, 30), font=font(26))
    draw.ellipse((1160, 915, 1370, 1025), outline=(60, 80, 100), width=4)
    centered(draw, "VALID", 945, font(22), width)

    return image, cert_id


def generate(count: int = 100):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REAL.mkdir(parents=True, exist_ok=True)

    for index in range(count):
        image, cert_id = make_certificate(index, template=index % 2)
        image.save(OUTPUT / f"{cert_id}.png", quality=95)
        image.save(REAL / f"{cert_id}.png", quality=95)

    print(f"Generated {count} genuine certificate images in {REAL}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic genuine certificate images")
    parser.add_argument("--count", type=int, default=100, help="Number of certificates to generate")
    args = parser.parse_args()
    generate(max(1, args.count))
