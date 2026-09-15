"""
ml_training/prepare_gemstone_dataset.py

Module 3 — Gemstone Detection, dataset prep.

Uses a Roboflow gemstone object-detection dataset (Diamond, Emerald, Ruby,
Sapphire), already labeled with bounding boxes — no manual labeling needed.
Roboflow exports directly in YOLO format, which ultralytics reads natively.

Setup:
    1. Create a free Roboflow account: https://roboflow.com
    2. Find a gemstone detection dataset in Roboflow Universe, e.g. search
       "gemstone detection" — there are a few with Diamond/Emerald/Ruby/
       Sapphire classes already. Open the one you like, note its workspace
       and project slug from the URL, and grab your API key from
       https://app.roboflow.com/settings/api
    3. Fill in ROBOFLOW_API_KEY, WORKSPACE, PROJECT, VERSION below.

Usage:
    pip install roboflow
    python ml_training/prepare_gemstone_dataset.py

Produces (Roboflow's standard YOLOv8 export layout):
    ml_training/data_gemstone/train/images/*.jpg
    ml_training/data_gemstone/train/labels/*.txt
    ml_training/data_gemstone/valid/images/ + labels/
    ml_training/data_gemstone/test/images/  + labels/
    ml_training/data_gemstone/data.yaml         <- points train_gemstone_detector.py at this
"""

from pathlib import Path

from roboflow import Roboflow

# ── Fill these in with your own Roboflow project details ──────────────────
ROBOFLOW_API_KEY = "YOUR_ROBOFLOW_API_KEY"
WORKSPACE = "your-workspace-slug"
PROJECT = "your-gemstone-project-slug"
VERSION = 1
# ────────────────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent / "data_gemstone"


def main():
    if ROBOFLOW_API_KEY == "YOUR_ROBOFLOW_API_KEY":
        raise SystemExit(
            "Fill in ROBOFLOW_API_KEY, WORKSPACE, PROJECT, and VERSION at the top of this "
            "file before running it — see the docstring for how to find a gemstone dataset "
            "and get your API key."
        )

    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace(WORKSPACE).project(PROJECT)
    version = project.version(VERSION)

    print(f"Downloading {WORKSPACE}/{PROJECT} v{VERSION} in YOLOv8 format...")
    dataset = version.download("yolov8", location=str(OUTPUT_DIR))
    print(f"Downloaded to {dataset.location}")
    print(f"data.yaml is at {OUTPUT_DIR / 'data.yaml'} — used directly by train_gemstone_detector.py")


if __name__ == "__main__":
    main()
