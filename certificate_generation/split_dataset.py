"""Split paired genuine/tampered certificates without leakage.

A certificate ID must have exactly one genuine image and one tampered image.
Both images are kept in the same split.
"""
from pathlib import Path
import argparse
import random
import shutil

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
SPLIT = DATASET / "split"


def source_id(path: Path) -> str:
    return path.stem.split("__", 1)[0]


def main(seed: int = 42):
    real = sorted((DATASET / "real").glob("*.png"))
    tampered = sorted((DATASET / "tampered").glob("*.png"))
    real_map = {source_id(p): p for p in real}
    tampered_map = {source_id(p): p for p in tampered}

    ids = sorted(set(real_map) & set(tampered_map))
    missing_real = sorted(set(tampered_map) - set(real_map))
    missing_tampered = sorted(set(real_map) - set(tampered_map))

    if missing_real or missing_tampered:
        raise SystemExit(
            "Dataset pairing error. "
            f"Missing real for {len(missing_real)} IDs; "
            f"missing tampered for {len(missing_tampered)} IDs."
        )
    if len(ids) < 10:
        raise SystemExit(f"Need at least 10 complete pairs; found {len(ids)}.")

    rng = random.Random(seed)
    rng.shuffle(ids)
    n = len(ids)
    train_end = int(n * 0.70)
    val_end = train_end + int(n * 0.15)
    assignments = {
        "train": ids[:train_end],
        "validation": ids[train_end:val_end],
        "test": ids[val_end:],
    }

    if SPLIT.exists():
        shutil.rmtree(SPLIT)

    for split, split_ids in assignments.items():
        for label, mapping in (("real", real_map), ("tampered", tampered_map)):
            target = SPLIT / split / label
            target.mkdir(parents=True, exist_ok=True)
            for cid in split_ids:
                shutil.copy2(mapping[cid], target / mapping[cid].name)

    print("Dataset split complete:")
    for split, split_ids in assignments.items():
        print(f"  {split}: {len(split_ids)} certificate pairs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.seed)
