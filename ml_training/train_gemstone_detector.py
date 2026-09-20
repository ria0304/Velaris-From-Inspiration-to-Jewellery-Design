"""
ml_training/train_gemstone_detector.py

Module 3 — Gemstone Detection
Fine-tunes a pretrained YOLOv8n (nano — fast, CPU-trainable in reasonable
time; bump to yolov8s if you have a GPU and want more accuracy) on the
Roboflow gemstone dataset downloaded by prepare_gemstone_dataset.py.

Usage:
    pip install ultralytics
    python ml_training/prepare_gemstone_dataset.py   # run first
    python ml_training/train_gemstone_detector.py

Outputs:
    runs/detect/train/weights/best.pt   <- ultralytics' own run directory
    backend/ml/checkpoints/gemstone_detector.pt   <- copied here for the app to use

ultralytics logs its own precision/recall/mAP metrics per epoch and a
confusion matrix under runs/detect/train/ — that's your evaluation story
for this module's section of the report, no separate eval script needed.
"""

import shutil
from pathlib import Path

from ultralytics import YOLO

DATA_YAML = Path(__file__).parent / "data_gemstone" / "data.yaml"
CHECKPOINT_DIR = Path(__file__).parent.parent / "backend" / "ml" / "checkpoints"

EPOCHS = 50
IMG_SIZE = 640
BATCH_SIZE = 16


def main():
    if not DATA_YAML.exists():
        raise SystemExit(
            f"{DATA_YAML} not found. Run ml_training/prepare_gemstone_dataset.py first."
        )

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO("yolov8n.pt")  # pretrained on COCO, fine-tune from here
    model.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        patience=10,  # early stopping if val mAP plateaus
        project="runs/detect",
        name="gemstone",
    )

    best_weights = Path("runs/detect/gemstone/weights/best.pt")
    if best_weights.exists():
        shutil.copy(best_weights, CHECKPOINT_DIR / "gemstone_detector.pt")
        print(f"\nCopied best weights to {CHECKPOINT_DIR / 'gemstone_detector.pt'}")
    else:
        print(f"\n⚠️  Expected {best_weights} but it wasn't found — check the run output above.")

    print("Full training metrics (precision/recall/mAP, confusion matrix, PR curves) "
          "are under runs/detect/gemstone/")


if __name__ == "__main__":
    main()
