from pathlib import Path

import torch
import torch.nn as nn
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from app.ai_detector.model import create_model
from app.ai_detector.dataset import create_dataloaders


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BATCH_SIZE = 16
EPOCHS = 5
LEARNING_RATE = 0.0001

MODEL_OUTPUT = Path(
    r"C:\Users\Karthikeya\OneDrive\Desktop\AIDE\backend\models\aide_tampering_resnet18_balanced.pth"
)


# --------------------------------------------------
# Validation function
# --------------------------------------------------

def evaluate(model, data_loader, device):

    model.eval()

    all_labels = []
    all_predictions = []

    with torch.no_grad():

        for images, labels in data_loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            predictions = torch.argmax(
                outputs,
                dim=1
            )

            all_labels.extend(
                labels.cpu().numpy()
            )

            all_predictions.extend(
                predictions.cpu().numpy()
            )

    accuracy = accuracy_score(
        all_labels,
        all_predictions
    )

    precision = precision_score(
        all_labels,
        all_predictions,
        zero_division=0
    )

    recall = recall_score(
        all_labels,
        all_predictions,
        zero_division=0
    )

    f1 = f1_score(
        all_labels,
        all_predictions,
        zero_division=0
    )

    return accuracy, precision, recall, f1


# --------------------------------------------------
# Main training
# --------------------------------------------------

def main():

    print("=" * 60)
    print("AIDE AI TAMpering DETECTION - BALANCED TRAINING")
    print("=" * 60)

    train_loader, validation_loader, test_loader = create_dataloaders(
        batch_size=BATCH_SIZE
    )

    model, device = create_model(
        pretrained=True
    )

    print(f"Device: {device}")
    print(f"Training batches: {len(train_loader)}")
    print(f"Validation batches: {len(validation_loader)}")
    print(f"Test batches: {len(test_loader)}")

    # --------------------------------------------------
    # Loss
    # --------------------------------------------------

    criterion = nn.CrossEntropyLoss()

    # --------------------------------------------------
    # Optimizer
    # --------------------------------------------------

    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-4
    )

    best_f1 = 0.0

    # --------------------------------------------------
    # Training loop
    # --------------------------------------------------

    for epoch in range(EPOCHS):

        model.train()

        running_loss = 0.0

        for images, labels in train_loader:

            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)

            loss = criterion(
                outputs,
                labels
            )

            loss.backward()

            optimizer.step()

            running_loss += loss.item()

        average_loss = (
            running_loss / len(train_loader)
        )

        # Validation
        accuracy, precision, recall, f1 = evaluate(
            model,
            validation_loader,
            device
        )

        print(
            f"Epoch {epoch + 1}/{EPOCHS} | "
            f"Loss: {average_loss:.4f} | "
            f"Val Accuracy: {accuracy:.4f} | "
            f"Val Precision: {precision:.4f} | "
            f"Val Recall: {recall:.4f} | "
            f"Val F1: {f1:.4f}"
        )

        # Save best model
        if f1 > best_f1:

            best_f1 = f1

            MODEL_OUTPUT.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "epoch": epoch + 1,
                    "validation_f1": f1
                },
                MODEL_OUTPUT
            )

            print(
                f"  -> Best model saved: {MODEL_OUTPUT}"
            )

    print()
    print("=" * 60)
    print(f"BEST VALIDATION F1: {best_f1:.4f}")
    print("=" * 60)

    print()
    print("Balanced training completed.")
    print("Checkpoint:")
    print(MODEL_OUTPUT)


if __name__ == "__main__":
    main()