"""Split paired genuine/tampered certificates without leakage.

Every certificate ID must have exactly one genuine image and exactly one
tampered image. The pair is always assigned to the same split.
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


def index_unique(paths, label):
    mapping = {}
    duplicates = []
    for path in paths:
        cid = source_id(path)
        if cid in mapping:
            duplicates.append(cid)
        mapping[cid] = path

    if duplicates:
        sample = ", ".join(sorted(set(duplicates))[:5])
        raise SystemExit(f"Duplicate {label} files for certificate IDs: {sample}")
    return mapping


def main(seed: int = 42):
    real = sorted((DATASET / "real").glob("*.png"))
    tampered = sorted((DATASET / "tampered").glob("*.png"))

    real_map = index_unique(real, "genuine")
    tampered_map = index_unique(tampered, "tampered")

    real_ids = set(real_map)
    tampered_ids = set(tampered_map)
    if real_ids != tampered_ids:
        missing_real = sorted(tampered_ids - real_ids)
        missing_tampered = sorted(real_ids - tampered_ids)
        raise SystemExit(
            "Dataset pairing error. "
            f"Missing genuine for {len(missing_real)} IDs; "
            f"missing tampered for {len(missing_tampered)} IDs."
        )

    ids = sorted(real_ids)
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

    if any(not split_ids for split_ids in assignments.values()):
        raise SystemExit(f"Dataset is too small for train/validation/test: {n} pairs.")

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
