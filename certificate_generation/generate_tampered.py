"""Create tampered copies of synthetic certificates for model training.

The original files are never modified. Each tampered image is derived from one
synthetic genuine certificate and receives a label in its filename.
"""

from pathlib import Path
import argparse
import random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parent
REAL = ROOT / "dataset" / "real"
TAMPERED = ROOT / "dataset" / "tampered"

OPERATIONS = (
    "name_edit",
    "date_edit",
    "id_edit",
    "grade_edit",
    "copy_patch",
    "blur_region",
    "compression",
    "signature_edit",
)


def edit_text(image: Image.Image, operation: str, rng: random.Random) -> Image.Image:
    image = image.copy()
    draw = ImageDraw.Draw(image)
    w, h = image.size

    if operation == "name_edit":
        box = (w // 2 - 330, 340, w // 2 + 330, 425)
        draw.rectangle(box, fill=(248, 246, 238))
        draw.text((w // 2 - 250, 355), "MODIFIED RECIPIENT", fill=(170, 30, 30))
    elif operation == "date_edit":
        box = (w // 2 - 260, 720, w // 2 + 260, 775)
        draw.rectangle(box, fill=(248, 246, 238))
        draw.text((w // 2 - 210, 730), "Issue Date: 31-12-2030", fill=(170, 30, 30))
    elif operation == "id_edit":
        box = (w // 2 - 300, 665, w // 2 + 300, 720)
        draw.rectangle(box, fill=(248, 246, 238))
        draw.text((w // 2 - 250, 675), "Certificate ID: FAKE-999999", fill=(170, 30, 30))
    elif operation == "grade_edit":
        box = (w // 2 - 170, 590, w // 2 + 170, 645)
        draw.rectangle(box, fill=(248, 246, 238))
        draw.text((w // 2 - 120, 600), "Grade: F", fill=(170, 30, 30))
    elif operation == "copy_patch":
        crop_w, crop_h = 230, 120
        x = rng.randint(150, w - crop_w - 150)
        y = rng.randint(150, h - crop_h - 150)
        patch = image.crop((w // 2 - crop_w // 2, 300, w // 2 + crop_w // 2, 300 + crop_h))
        image.paste(patch, (x, y))
    elif operation == "blur_region":
        crop_w, crop_h = 360, 100
        x = rng.randint(120, w - crop_w - 120)
        y = rng.randint(250, h - crop_h - 150)
        region = image.crop((x, y, x + crop_w, y + crop_h)).filter(ImageFilter.GaussianBlur(7))
        image.paste(region, (x, y))
    elif operation == "compression":
        # Re-encoding with low JPEG quality creates a realistic, non-local artifact.
        temp = ROOT / ".tamper_temp.jpg"
        image.save(temp, format="JPEG", quality=25)
        image = Image.open(temp).convert("RGB")
        temp.unlink(missing_ok=True)
    elif operation == "signature_edit":
        draw.line((145, 915, 460, 900), fill=(170, 30, 30), width=8)
        draw.line((180, 900, 430, 930), fill=(170, 30, 30), width=5)

    return image


def generate(limit: int | None = None, seed: int = 42) -> None:
    TAMPERED.mkdir(parents=True, exist_ok=True)
    sources = sorted(REAL.glob("*.png"))
    if limit is not None:
        sources = sources[:limit]
    if not sources:
        raise SystemExit("No genuine certificates found. Run generate_certificates.py first.")

    rng = random.Random(seed)
    created = 0
    for source in sources:
        original = Image.open(source).convert("RGB")
        # Four variants per original gives useful diversity without changing the originals.
        selected = rng.sample(OPERATIONS, k=min(4, len(OPERATIONS)))
        for operation in selected:
            tampered = edit_text(original, operation, rng)
            output = TAMPERED / f"{source.stem}__{operation}.png"
            tampered.save(output)
            created += 1

    print(f"Created {created} tampered images in {TAMPERED}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate tampered certificate variants")
    parser.add_argument("--limit", type=int, default=None, help="Optional number of genuine source certificates")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.limit, args.seed)
