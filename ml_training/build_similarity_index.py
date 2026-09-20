"""
ml_training/build_similarity_index.py

Module 4 — builds the CLIP embedding index that backend/ml/similarity_search.py
searches against at request time. Nothing is trained here — CLIP is used
as a pretrained, frozen feature extractor. This script just embeds a pool
of reference jewelry images once and saves the vectors + metadata to disk.

Reuses the same reference pool as Module 1 (the sidd707/jewelry-design-dataset
images downloaded by prepare_dataset.py), so run that first.

Usage:
    pip install transformers torch pillow
    python ml_training/prepare_dataset.py         # if not already done
    python ml_training/build_similarity_index.py

Outputs:
    backend/ml/checkpoints/similarity_embeddings.npy   # (N, 512) float32, L2-normalized
    backend/ml/checkpoints/similarity_metadata.json    # [{"path": ..., "type": ...}, ...] parallel to embeddings
"""

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

DATA_DIR = Path(__file__).parent / "data"  # Module 1's train/val/test split
CHECKPOINT_DIR = Path(__file__).parent.parent / "backend" / "ml" / "checkpoints"
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

# Cap the reference pool so the index build and later searches stay fast.
# Bump this if you want a denser index and don't mind a slower one-time build.
MAX_IMAGES_PER_CLASS = 300


def main():
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading {CLIP_MODEL_NAME}...")
    model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
    model.eval()

    image_paths = []
    for class_dir in sorted((DATA_DIR / "train").iterdir()):
        if not class_dir.is_dir():
            continue
        class_images = sorted(class_dir.glob("*"))[:MAX_IMAGES_PER_CLASS]
        for img_path in class_images:
            image_paths.append((img_path, class_dir.name))

    if not image_paths:
        raise SystemExit(
            f"No images found under {DATA_DIR}/train/. Run ml_training/prepare_dataset.py first."
        )

    print(f"Embedding {len(image_paths)} reference images...")
    embeddings = []
    metadata = []

    for i, (img_path, class_name) in enumerate(image_paths):
        try:
            image = Image.open(img_path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt")
            with torch.no_grad():
                features = model.get_image_features(**inputs)
            # transformers>=5 returns an output object instead of a tensor —
            # unwrap whichever embedding field the installed version provides.
            embeds = features
            for attr in ("image_embeds", "pooler_output"):
                if hasattr(embeds, attr):
                    embeds = getattr(embeds, attr)
                    break
            else:
                if hasattr(embeds, "last_hidden_state"):
                    embeds = embeds.last_hidden_state.mean(dim=1)
            vec = embeds.squeeze(0) if isinstance(embeds, torch.Tensor) else torch.as_tensor(embeds).squeeze(0)
            vec = vec.detach().cpu().numpy()
            vec = vec / (np.linalg.norm(vec) + 1e-8)

            embeddings.append(vec)
            metadata.append({"path": str(img_path), "type": class_name})
        except Exception as exc:
            print(f"  skipping {img_path}: {exc}")

        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(image_paths)}")

    embeddings_arr = np.stack(embeddings).astype(np.float32)
    np.save(CHECKPOINT_DIR / "similarity_embeddings.npy", embeddings_arr)
    with open(CHECKPOINT_DIR / "similarity_metadata.json", "w") as f:
        json.dump(metadata, f)

    print(f"\nSaved {embeddings_arr.shape[0]} embeddings (dim={embeddings_arr.shape[1]}) to {CHECKPOINT_DIR}/")


if __name__ == "__main__":
    main()
