from pathlib import Path

import torch
import torch.nn.functional as F
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

from app.ai_detector.model import create_model
from app.ai_detector.dataset import create_dataloaders


MODEL_PATH = Path(
    r"C:\Users\Karthikeya\OneDrive\Desktop\AIDE\backend\models\aide_tampering_resnet18_balanced.pth"
)


def main():

    print("=" * 60)
    print("AIDE AI TAMpering DETECTION - TEST EVALUATION")
    print("=" * 60)

    # Load test data
    _, _, test_loader = create_dataloaders(
        batch_size=16
    )

    # Create model
    model, device = create_model(
        pretrained=True
    )

    # Load trained checkpoint
    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.eval()

    print(f"Device: {device}")
    print(f"Checkpoint epoch: {checkpoint['epoch']}")
    print(
        f"Validation F1 at checkpoint: "
        f"{checkpoint['validation_f1']:.4f}"
    )

    all_labels = []
    all_predictions = []

    with torch.no_grad():

        for images, labels in test_loader:

            images = images.to(device)

            outputs = model(images)

            probabilities = F.softmax(
                outputs,
                dim=1
            )

            predictions = torch.argmax(
                probabilities,
                dim=1
            )

            all_labels.extend(
                labels.numpy()
            )

            all_predictions.extend(
                predictions.cpu().numpy()
            )

    # Metrics
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

    print()
    print("-" * 60)
    print("TEST RESULTS")
    print("-" * 60)

    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print(f"F1 Score  : {f1:.4f}")

    # Confusion matrix
    cm = confusion_matrix(
        all_labels,
        all_predictions
    )

    print()
    print("-" * 60)
    print("CONFUSION MATRIX")
    print("-" * 60)

    print(
        "                 Predicted"
    )
    print(
        "              Original  Tampered"
    )

    print(
        f"Actual Original     "
        f"{cm[0][0]:4d}      "
        f"{cm[0][1]:4d}"
    )

    print(
        f"Actual Tampered     "
        f"{cm[1][0]:4d}      "
        f"{cm[1][1]:4d}"
    )

    # Detailed report
    print()
    print("-" * 60)
    print("CLASSIFICATION REPORT")
    print("-" * 60)

    print(
        classification_report(
            all_labels,
            all_predictions,
            target_names=[
                "Original",
                "Tampered"
            ],
            zero_division=0
        )
    )


if __name__ == "__main__":
    main()