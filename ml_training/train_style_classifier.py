"""
ml_training/train_style_classifier.py

Module 2 — Jewelry Style Recognition
Fine-tunes EfficientNet-B0 on the binary Traditional vs Modern split
produced by prepare_style_dataset.py. Same two-phase transfer-learning
approach as Module 1 (train_type_classifier.py) — see that file for more
detailed comments on the training loop itself.

Usage:
    python ml_training/prepare_dataset.py        # Module 1 — run first
    python ml_training/prepare_style_dataset.py
    python ml_training/train_style_classifier.py
    python ml_training/evaluate_style.py

Outputs:
    backend/ml/checkpoints/style_classifier.pt
    backend/ml/checkpoints/style_class_to_idx.json
    ml_training/results/style_training_log.csv
"""

import json
import time
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

DATA_DIR = Path(__file__).parent / "data_style"
CHECKPOINT_DIR = Path(__file__).parent.parent / "backend" / "ml" / "checkpoints"
RESULTS_DIR = Path(__file__).parent / "results"

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS_HEAD = 5
EPOCHS_FINE_TUNE = 10
LR_HEAD = 1e-3
LR_FINE_TUNE = 1e-4

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)


def get_dataloaders():
    train_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    eval_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_ds = datasets.ImageFolder(DATA_DIR / "train", transform=train_transform)
    val_ds = datasets.ImageFolder(DATA_DIR / "val", transform=eval_transform)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    return train_loader, val_loader, train_ds.class_to_idx


def build_model(num_classes: int) -> nn.Module:
    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
    for param in model.features.parameters():
        param.requires_grad = False
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    return model.to(DEVICE)


def run_epoch(model, loader, criterion, optimizer=None):
    is_train = optimizer is not None
    model.train() if is_train else model.eval()

    total_loss, correct, total = 0.0, 0, 0
    with torch.set_grad_enabled(is_train):
        for images, labels in loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            if is_train:
                optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            if is_train:
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            total += images.size(0)

    return total_loss / total, correct / total


def main():
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    train_loader, val_loader, class_to_idx = get_dataloaders()
    print(f"Classes: {class_to_idx}")
    print(f"Device: {DEVICE}")

    model = build_model(num_classes=len(class_to_idx))
    criterion = nn.CrossEntropyLoss()

    log_rows = ["phase,epoch,train_loss,train_acc,val_loss,val_acc,time_sec"]
    best_val_acc = 0.0

    optimizer = optim.Adam(model.classifier.parameters(), lr=LR_HEAD)
    for epoch in range(1, EPOCHS_HEAD + 1):
        t0 = time.time()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = run_epoch(model, val_loader, criterion)
        dt = time.time() - t0
        print(f"[head]     epoch {epoch}/{EPOCHS_HEAD}   train_acc={train_acc:.3f}  val_acc={val_acc:.3f}  ({dt:.1f}s)")
        log_rows.append(f"head,{epoch},{train_loss:.4f},{train_acc:.4f},{val_loss:.4f},{val_acc:.4f},{dt:.1f}")
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), CHECKPOINT_DIR / "style_classifier.pt")

    for param in model.features.parameters():
        param.requires_grad = True
    optimizer = optim.Adam(model.parameters(), lr=LR_FINE_TUNE)

    for epoch in range(1, EPOCHS_FINE_TUNE + 1):
        t0 = time.time()
        train_loss, train_acc = run_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc = run_epoch(model, val_loader, criterion)
        dt = time.time() - t0
        print(f"[finetune] epoch {epoch}/{EPOCHS_FINE_TUNE}  train_acc={train_acc:.3f}  val_acc={val_acc:.3f}  ({dt:.1f}s)")
        log_rows.append(f"finetune,{epoch},{train_loss:.4f},{train_acc:.4f},{val_loss:.4f},{val_acc:.4f},{dt:.1f}")
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), CHECKPOINT_DIR / "style_classifier.pt")

    with open(CHECKPOINT_DIR / "style_class_to_idx.json", "w") as f:
        json.dump(class_to_idx, f, indent=2)
    with open(RESULTS_DIR / "style_training_log.csv", "w") as f:
        f.write("\n".join(log_rows))

    print(f"\nBest val accuracy: {best_val_acc:.3f}")
    print(f"Checkpoint saved to {CHECKPOINT_DIR / 'style_classifier.pt'}")


if __name__ == "__main__":
    main()
