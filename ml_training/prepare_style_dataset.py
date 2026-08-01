"""
ml_training/prepare_style_dataset.py

Module 2 — Jewelry Style Recognition, dataset prep.

There's no public dataset with clean style labels, so this derives WEAK
binary labels from the caption text that ships with the same
sidd707/jewelry-design-dataset used for Module 1, instead of hand-labeling
anything:

    traditional/temple bucket  <- captions mentioning: temple, traditional,
                                   kundan, polki, antique, heritage, ethnic
    modern/minimal bucket      <- captions mentioning: minimal, modern,
                                   contemporary, sleek, geometric, simple

Images whose captions don't clearly match either bucket are skipped rather
than guessed at — a smaller, cleaner dataset beats a larger noisy one here.

This is a WEAK LABELING approach — call it that explicitly in your report.
It's a legitimate and common technique (distant supervision), but it's not
the same as human-verified ground truth, and accuracy numbers should be
read with that caveat. Expect this to be your report's best "limitations"
discussion (CO5).

Usage:
    python ml_training/prepare_dataset.py         # Module 1's script — run first,
                                                    # this reuses its raw download
    python ml_training/prepare_style_dataset.py

Produces:
    ml_training/data_style/train/{traditional,modern}/*.jpg
    ml_training/data_style/val/{...}/*.jpg
    ml_training/data_style/test/{...}/*.jpg
"""

import json
import random
import shutil
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"          # from Module 1's prepare_dataset.py
RAW_DIR = DATA_DIR / "raw"
STYLE_DATA_DIR = Path(__file__).parent / "data_style"
SPLIT_RATIOS = {"train": 0.8, "val": 0.1, "test": 0.1}
SEED = 42

TRADITIONAL_KEYWORDS = (
    "temple", "traditional", "kundan", "polki", "antique", "heritage", "ethnic", "vintage",
)
MODERN_KEYWORDS = (
    "minimal", "modern", "contemporary", "sleek", "geometric", "simple", "clean lines",
)


def _load_captions() -> dict:
    """
    The dataset ships captions alongside the images (per the HF dataset card).
    The exact file/field name can vary by revision — check a couple of likely
    spots. If none match what actually downloaded, inspect RAW_DIR yourself
    and adjust this function; the bucketing logic below doesn't need to change.
    """
    candidates = [
        RAW_DIR / "captions.json",
        RAW_DIR / "metadata.json",
        RAW_DIR / "metadata.jsonl",
    ]
    for c in candidates:
        if c.exists():
            if c.suffix == ".jsonl":
                rows = [json.loads(line) for line in c.read_text().splitlines() if line.strip()]
                return {r.get("file_name") or r.get("image"): r.get("caption") or r.get("text") for r in rows}
            data = json.loads(c.read_text())
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {r.get("file_name") or r.get("image"): r.get("caption") or r.get("text") for r in data}

    raise SystemExit(
        f"Couldn't find a captions/metadata file under {RAW_DIR}. "
        "List the raw download's files and point this function at the real one — "
        "the dataset card documents where per-image captions live."
    )


def _bucket_for_caption(caption: str) -> Optional[str]:
    caption_lower = (caption or "").lower()
    is_traditional = any(kw in caption_lower for kw in TRADITIONAL_KEYWORDS)
    is_modern = any(kw in caption_lower for kw in MODERN_KEYWORDS)

    if is_traditional and not is_modern:
        return "traditional"
    if is_modern and not is_traditional:
        return "modern"
    return None  # ambiguous or no match — skip


def main():
    captions = _load_captions()
    print(f"Loaded {len(captions)} captions.")

    buckets = {"traditional": [], "modern": []}
    all_images = list(RAW_DIR.rglob("*.jpg")) + list(RAW_DIR.rglob("*.jpeg")) + list(RAW_DIR.rglob("*.png"))
    image_by_name = {p.name: p for p in all_images}

    matched, skipped = 0, 0
    for file_name, caption in captions.items():
        if not file_name:
            continue
        img_path = image_by_name.get(Path(file_name).name)
        if img_path is None:
            continue
        bucket = _bucket_for_caption(caption)
        if bucket is None:
            skipped += 1
            continue
        buckets[bucket].append(img_path)
        matched += 1

    print(f"Matched {matched} images to a style bucket, skipped {skipped} (ambiguous/no keyword match).")
    for name, imgs in buckets.items():
        print(f"  {name}: {len(imgs)} images")

    if min(len(v) for v in buckets.values()) < 50:
        print(
            "\n⚠️  One bucket has under 50 images — that's thin for training. "
            "Consider widening the keyword lists above, or accept a smaller/noisier "
            "dataset and note it as a limitation in your report."
        )

    random.seed(SEED)
    for bucket_name, images in buckets.items():
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
            out_dir = STYLE_DATA_DIR / split_name / bucket_name
            out_dir.mkdir(parents=True, exist_ok=True)
            for img_path in split_images:
                shutil.copy(img_path, out_dir / img_path.name)

    print(f"\nDone. Data is ready in {STYLE_DATA_DIR}/{{train,val,test}}/")


if __name__ == "__main__":
    main()
