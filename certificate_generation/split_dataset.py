"""Split genuine/tampered data into train/validation/test without source leakage.

Tampered files are grouped with their source certificate ID so variants of the
same original certificate never appear in different splits.
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


def split_grouped(files: list[Path], rng: random.Random, train_ratio: float, val_ratio: float):
    groups: dict[str, list[Path]] = {}
    for path in files:
        groups.setdefault(source_id(path), []).append(path)
    keys = list(groups)
    rng.shuffle(keys)
    n = len(keys)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    return (
        [p for k in keys[:train_end] for p in groups[k]],
        [p for k in keys[train_end:val_end] for p in groups[k]],
        [p for k in keys[val_end:] for p in groups[k]],
    )


def copy_files(files: list[Path], split: str, label: str):
    target = SPLIT / split / label
    target.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copy2(path, target / path.name)


def main(seed: int = 42):
    real = sorted((DATASET / "real").glob("*.png"))
    tampered = sorted((DATASET / "tampered").glob("*.png"))
    if not real or not tampered:
        raise SystemExit("Generate both real and tampered datasets first.")

    if SPLIT.exists():
        shutil.rmtree(SPLIT)
    rng = random.Random(seed)

    real_train, real_val, real_test = split_grouped(real, rng, 0.70, 0.15)
    tam_train, tam_val, tam_test = split_grouped(tampered, rng, 0.70, 0.15)

    copy_files(real_train, "train", "real")
    copy_files(real_val, "validation", "real")
    copy_files(real_test, "test", "real")
    copy_files(tam_train, "train", "tampered")
    copy_files(tam_val, "validation", "tampered")
    copy_files(tam_test, "test", "tampered")

    print("Dataset split complete:")
    for split, a, b in [("train", real_train, tam_train), ("validation", real_val, tam_val), ("test", real_test, tam_test)]:
        print(f"  {split}: real={len(a)}, tampered={len(b)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(args.seed)
