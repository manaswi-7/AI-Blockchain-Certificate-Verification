"""Generate exactly one realistic tampered image for each genuine image.

Use generate_500_certificate_dataset.py for a full clean rebuild. This file is
kept only as a convenience for re-tampering an already generated real folder.
No class labels are written into pixels.
"""
from pathlib import Path
import argparse
import csv
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
REAL = DATASET / "real"
TAMPERED = DATASET / "tampered"

sys.path.insert(0, str(ROOT))
from generate_500_certificate_dataset import record, tamper, SEED


def generate(limit=None):
    sources = sorted(REAL.glob("*.png"))
    if limit is not None:
        sources = sources[:limit]
    if not sources:
        raise SystemExit("No genuine certificates found. Run generate_500_certificate_dataset.py first.")

    TAMPERED.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, source in enumerate(sources):
        image = Image.open(source).convert("RGB")
        r = record(i)
        edited, kind = tamper(image, r, i)
        target = TAMPERED / f"{source.stem}__{kind}.png"
        edited.save(target, optimize=True)
        rows.append((source.name, target.name, kind))

    print(f"Created exactly {len(rows)} tampered images.")
    print(f"Real images: {len(sources)}")
    print(f"Tampered images: {len(rows)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    generate(args.limit)
