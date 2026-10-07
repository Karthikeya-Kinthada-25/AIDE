import torch
import torch.nn as nn
from torchvision import models


class TamperingDetectionModel(nn.Module):
    """
    CNN backbone for the AIDE AI tampering-detection module.

    The model uses ResNet18 as the feature extractor and
    replaces the final classification layer with a binary
    classifier:

        0 -> Non-tampered
        1 -> Tampered

    IMPORTANT:
    This architecture is not a trained forensic detector yet.
    It must be trained/fine-tuned on an appropriate image
    tampering dataset before its predictions can be used.
    """

    def __init__(self, pretrained: bool = True):
        super().__init__()

        if pretrained:
            weights = models.ResNet18_Weights.DEFAULT
        else:
            weights = None

        self.backbone = models.resnet18(
            weights=weights
        )

        # Number of features entering the original
        # ResNet classification layer.
        num_features = self.backbone.fc.in_features

        # Replace ImageNet's 1000-class classifier.
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(num_features, 2)
        )

    def forward(self, x):
        return self.backbone(x)


def create_model(
    pretrained: bool = True,
    device: str | None = None
):
    """
    Create the AIDE tampering-detection model.

    Returns:
        model: initialized PyTorch model
        device: selected computation device
    """

    if device is None:
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    model = TamperingDetectionModel(
        pretrained=pretrained
    )

    model = model.to(device)

    return model, device