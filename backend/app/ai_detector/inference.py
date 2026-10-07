from pathlib import Path

import torch
import torch.nn.functional as F

from app.ai_detector.model import create_model
from app.ai_detector.preprocessing import preprocess_image


MODEL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "models"
    / "aide_tampering_resnet18_balanced.pth"
)


class AIDetector:

    def __init__(self, model_path=None, device=None):

        if model_path is None:
            model_path = MODEL_PATH

        model_path = Path(model_path)

        self.model, self.device = create_model(
            pretrained=True,
            device=device
        )

        if not model_path.exists():
            raise FileNotFoundError(
                f"AI model checkpoint not found: {model_path}"
            )

        checkpoint = torch.load(
            model_path,
            map_location=self.device
        )

        if "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
        else:
            state_dict = checkpoint

        self.model.load_state_dict(
            state_dict
        )

        self.model.eval()

        self.checkpoint_epoch = checkpoint.get(
            "epoch",
            None
        )

        self.validation_f1 = checkpoint.get(
            "validation_f1",
            None
        )

    def predict(self, image_path):

        image_tensor = preprocess_image(
            image_path,
            device=self.device
        )

        with torch.no_grad():

            outputs = self.model(
                image_tensor
            )

            probabilities = F.softmax(
                outputs,
                dim=1
            )

        original_probability = float(
            probabilities[0][0].item()
        )

        tampered_probability = float(
            probabilities[0][1].item()
        )

        if tampered_probability >= original_probability:
            prediction = "Tampered"
        else:
            prediction = "Original"

        return {
            "status": "success",
            "prediction_available": True,
            "prediction": prediction,
            "model": "ResNet18",
            "device": self.device,
            "original_probability": round(
                original_probability,
                4
            ),
            "tampered_probability": round(
                tampered_probability,
                4
            ),
            "checkpoint_epoch": self.checkpoint_epoch,
            "validation_f1": (
                round(self.validation_f1, 4)
                if self.validation_f1 is not None
                else None
            ),
            "warning": (
                "AI prediction is a model-based forensic "
                "indication and is not a definitive "
                "forensic verdict."
            )
        }