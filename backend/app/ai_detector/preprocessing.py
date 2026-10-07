from PIL import Image
import torch
from torchvision import transforms


# ImageNet normalization used by the pretrained ResNet18 backbone.
IMAGE_MEAN = [
    0.485,
    0.456,
    0.406
]

IMAGE_STD = [
    0.229,
    0.224,
    0.225
]


def get_transform():
    """
    Preprocessing pipeline for AI inference.

    The image is:
    1. Converted to RGB
    2. Resized to 224 x 224
    3. Converted to a PyTorch tensor
    4. Normalized using ImageNet statistics
    """

    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=IMAGE_MEAN,
            std=IMAGE_STD
        )
    ])


def preprocess_image(
    image_path,
    device="cpu"
):
    """
    Load and preprocess an image for the AI model.

    Returns:
        Tensor with shape:
        [1, 3, 224, 224]
    """

    image = Image.open(
        image_path
    ).convert("RGB")

    transform = get_transform()

    tensor = transform(image)

    # Add batch dimension.
    tensor = tensor.unsqueeze(0)

    tensor = tensor.to(device)

    return tensor