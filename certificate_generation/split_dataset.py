"""Split genuine/tampered data into train/validation/test without source leakage.

All variants belonging to the same source certificate ID are assigned to one
split, so a genuine certificate and its tampered variants cannot leak across
train/validation/test.
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


def assign_groups(source_ids: list[str], rng: random.Random):
    ids = list(source_ids)
    rng.shuffle(ids)
    n = len(ids)
    train_end = int(n * 0.70)
    val_end = train_end + int(n * 0.15)
    return {
        "train": set(ids[:train_end]),
        "validation": set(ids[train_end:val_end]),
        "test": set(ids[val_end:]),
    }


def copy_by_assignment(files: list[Path], assignments: dict[str, set[str]], label: str):
    for split, ids in assignments.items():
        target = SPLIT / split / label
        target.mkdir(parents=True, exist_ok=True)
        for path in files:
            if source_id(path) in ids:
                shutil.copy2(path, target / path.name)


def main(seed: int = 42):
    real = sorted((DATASET / "real").glob("*.png"))
    tampered = sorted((DATASET / "tampered").glob("*.png"))
    if not real or not tampered:
        raise SystemExit("Generate both real and tampered datasets first.")

    if SPLIT.exists():
        shutil.rmtree(SPLIT)

    real_ids = {source_id(p) for p in real}
    tampered_ids = {source_id(p) for p in tampered}
    source_ids = sorted(real_ids | tampered_ids)
    assignments = assign_groups(source_ids, random.Random(seed))

    copy_by_assignment(real, assignments, "real")
    copy_by_assignment(tampered, assignments, "tampered")

    print("Dataset split complete (grouped by source certificate):")
    for split in ("train", "validation", "test"):
        real_count = sum(source_id(p) in assignments[split] for p in real)
        tampered_count = sum(source_id(p) in assignments[split] for p in tampered)
        print(f"  {split}: real={real_count}, tampered={tampered_count}, sources={len(assignments[split])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.seed)
