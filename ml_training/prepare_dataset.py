"""
ml_training/prepare_dataset.py

Downloads and splits the jewelry type dataset used for Module 1.

Dataset: sidd707/jewelry-design-dataset (Hugging Face, MIT licensed)
https://huggingface.co/datasets/sidd707/jewelry-design-dataset
~6,100 images across 4 categories: bracelet, earring, necklace, ring.
Note: ring is the smallest class (~230 images) — expect it to be the
hardest to classify and the one worth discussing in your report's
"limitations" section.

Usage:
    pip install huggingface_hub pillow
    python ml_training/prepare_dataset.py

Produces an ImageFolder-compatible layout:
    ml_training/data/train/{bracelet,earring,necklace,ring}/*.jpg
    ml_training/data/val/{...}/*.jpg
    ml_training/data/test/{...}/*.jpg

Note on folder names: Hugging Face dataset repos occasionally reorganize
their internal folder layout between revisions. If CLASS_FOLDERS below
doesn't match what actually gets downloaded, run:
    python -c "from huggingface_hub import list_repo_files; \
        print(list_repo_files('sidd707/jewelry-design-dataset', repo_type='dataset'))"
and update the CLASS_FOLDERS mapping to match the real paths.
"""

import random
import shutil
from pathlib import Path
from typing import Optional

from huggingface_hub import snapshot_download

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR = DATA_DIR / "raw"
SPLIT_RATIOS = {"train": 0.8, "val": 0.1, "test": 0.1}
SEED = 42

# raw dataset folder name -> the class name we train on
CLASS_FOLDERS = {
    "bracelet": "bracelet",
    "earring": "earring",
    "necklace": "necklace",
    "ring": "ring",
}


def download() -> Path:
    print("Downloading sidd707/jewelry-design-dataset from Hugging Face...")
    path = snapshot_download(
        repo_id="sidd707/jewelry-design-dataset",
        repo_type="dataset",
        local_dir=str(RAW_DIR),
    )
    print(f"Downloaded to {path}")
    return Path(path)


def _find_class_dir(raw_path: Path, folder_hint: str) -> Optional[Path]:
    """The dataset's exact directory nesting can vary by revision — search
    a couple of likely spots instead of hardcoding one path."""
    candidates = [
        raw_path / folder_hint,
        raw_path / "images" / folder_hint,
        raw_path / "data" / folder_hint,
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    # last resort: search recursively for a directory with a matching name
    matches = [p for p in raw_path.rglob(folder_hint) if p.is_dir()]
    return matches[0] if matches else None


def split_and_copy(raw_path: Path):
    random.seed(SEED)
    any_found = False

    for folder_hint, class_name in CLASS_FOLDERS.items():
        src_dir = _find_class_dir(raw_path, folder_hint)
        if src_dir is None:
            print(f"⚠️  Could not find a '{folder_hint}' folder under {raw_path}. Skipping.")
            print("    Run the list_repo_files snippet in this file's docstring to check the real layout.")
            continue

        any_found = True
        images = sorted(
            p for p in src_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        )
        random.shuffle(images)

        n = len(images)
        n_train = int(n * SPLIT_RATIOS["train"])
        n_val = int(n * SPLIT_RATIOS["val"])

        splits = {
            "train": images[:n_train],
            "val": images[n_train : n_train + n_val],
            "test": images[n_train + n_val :],
        }

        for split_name, split_images in splits.items():
            out_dir = DATA_DIR / split_name / class_name
            out_dir.mkdir(parents=True, exist_ok=True)
            for img_path in split_images:
                shutil.copy(img_path, out_dir / img_path.name)

        print(
            f"{class_name}: {n} images -> "
            f"train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}"
        )

    if not any_found:
        raise SystemExit(
            "No class folders matched. Inspect the downloaded dataset under "
            f"{raw_path} manually and update CLASS_FOLDERS in this script."
        )


if __name__ == "__main__":
    raw_path = download()
    split_and_copy(raw_path)
    print("\nDone. Data is ready in ml_training/data/{train,val,test}/")
