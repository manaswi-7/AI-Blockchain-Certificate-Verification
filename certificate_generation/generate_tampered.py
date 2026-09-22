"""Compatibility entry point for regenerating the paired tampered set.

The canonical generator is the only source of certificate layout and tamper
logic. This script deliberately does not contain a second renderer.
"""
import argparse
from pathlib import Path
import shutil

from generate_500_certificate_dataset import generate


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=None)
    args = parser.parse_args()

    real = sorted((DATASET / "real").glob("*.png"))
    count = args.count if args.count is not None else len(real)
    if count < 1:
        raise SystemExit("No genuine certificates found. Run generate_certificates.py first.")

    # Rebuild the complete paired dataset from the same canonical template.
    generate(count)
