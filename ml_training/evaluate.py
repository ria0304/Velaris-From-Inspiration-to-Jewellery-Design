"""
ml_training/evaluate.py

Evaluates the trained type classifier on the held-out test set and
produces the metrics you'll want for the DSE3120 report: accuracy,
precision, recall, F1 (per-class + macro avg), and a confusion matrix.

Usage:
    python ml_training/evaluate.py

Outputs:
    ml_training/results/classification_report.txt
    ml_training/results/confusion_matrix.png
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from sklearn.metrics import classification_report, confusion_matrix

DATA_DIR = Path(__file__).parent / "data"
CHECKPOINT_DIR = Path(__file__).parent.parent / "backend" / "ml" / "checkpoints"
RESULTS_DIR = Path(__file__).parent / "results"

IMG_SIZE = 224
DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(CHECKPOINT_DIR / "class_to_idx.json") as f:
        class_to_idx = json.load(f)
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    class_names = [idx_to_class[i] for i in range(len(idx_to_class))]

    eval_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    test_ds = datasets.ImageFolder(DATA_DIR / "test", transform=eval_transform)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False)

    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(class_to_idx))
    model.load_state_dict(torch.load(CHECKPOINT_DIR / "type_classifier.pt", map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(DEVICE)
            outputs = model(images)
            preds = outputs.argmax(1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())

    report = classification_report(all_labels, all_preds, target_names=class_names, digits=3)
    print(report)
    with open(RESULTS_DIR / "classification_report.txt", "w") as f:
        f.write(report)

    cm = confusion_matrix(all_labels, all_preds)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Jewelry Type Classification — Confusion Matrix")
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            ax.text(
                j, i, str(cm[i, j]), ha="center", va="center",
                color="white" if cm[i, j] > cm.max() / 2 else "black",
            )
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "confusion_matrix.png", dpi=150)
    print(f"\nSaved classification_report.txt and confusion_matrix.png to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
