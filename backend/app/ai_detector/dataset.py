from pathlib import Path

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import (
    Dataset,
    DataLoader,
    WeightedRandomSampler
)
from torchvision import transforms


# --------------------------------------------------
# ImageNet normalization
# --------------------------------------------------

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


# --------------------------------------------------
# Training transform
#
# Mild augmentation only.
# We don't want aggressive transformations because
# forensic image characteristics can be important.
# --------------------------------------------------

def get_train_transform():

    return transforms.Compose([

        transforms.Resize(
            (224, 224)
        ),

        transforms.RandomHorizontalFlip(
            p=0.5
        ),

        transforms.RandomRotation(
            degrees=5
        ),

        transforms.ColorJitter(
            brightness=0.08,
            contrast=0.08,
            saturation=0.05,
            hue=0.02
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=IMAGE_MEAN,
            std=IMAGE_STD
        )
    ])


# --------------------------------------------------
# Validation / test transform
# --------------------------------------------------

def get_eval_transform():

    return transforms.Compose([

        transforms.Resize(
            (224, 224)
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=IMAGE_MEAN,
            std=IMAGE_STD
        )
    ])


# --------------------------------------------------
# Dataset
# --------------------------------------------------

class IMD2020Dataset(Dataset):

    def __init__(
        self,
        csv_file,
        dataset_root,
        transform=None
    ):

        self.csv_file = Path(
            csv_file
        )

        self.dataset_root = Path(
            dataset_root
        )

        self.data = pd.read_csv(
            self.csv_file
        )

        self.transform = transform

    def __len__(self):

        return len(
            self.data
        )

    def __getitem__(
        self,
        index
    ):

        row = self.data.iloc[
            index
        ]

        image_path = (
            self.dataset_root
            / row["image_path"]
        )

        image = Image.open(
            image_path
        ).convert("RGB")

        if self.transform is not None:

            image = self.transform(
                image
            )

        label = torch.tensor(
            int(row["label"]),
            dtype=torch.long
        )

        return image, label


# --------------------------------------------------
# Balanced sampler
# --------------------------------------------------

def create_balanced_sampler(
    dataset
):

    labels = dataset.data[
        "label"
    ].to_numpy()

    class_counts = torch.bincount(
        torch.tensor(
            labels,
            dtype=torch.long
        )
    )

    class_weights = (
        1.0
        / class_counts.float()
    )

    sample_weights = (
        class_weights[
            torch.tensor(
                labels,
                dtype=torch.long
            )
        ]
    )

    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(
            sample_weights
        ),
        replacement=True
    )

    return sampler


# --------------------------------------------------
# DataLoaders
# --------------------------------------------------

def create_dataloaders(
    batch_size=16,
    num_workers=0
):

    dataset_root = Path(
        r"C:\Users\karthikeya\OneDrive\Desktop\IMD2020"
    )

    split_root = Path(
        r"C:\Users\karthikeya\OneDrive\Desktop\AIDE\backend\dataset_tools\splits"
    )

    # --------------------------------------------------
    # Training dataset
    # --------------------------------------------------

    train_dataset = IMD2020Dataset(
        csv_file=(
            split_root
            / "train.csv"
        ),
        dataset_root=dataset_root,
        transform=get_train_transform()
    )

    # --------------------------------------------------
    # Validation dataset
    # --------------------------------------------------

    validation_dataset = IMD2020Dataset(
        csv_file=(
            split_root
            / "validation.csv"
        ),
        dataset_root=dataset_root,
        transform=get_eval_transform()
    )

    # --------------------------------------------------
    # Test dataset
    # --------------------------------------------------

    test_dataset = IMD2020Dataset(
        csv_file=(
            split_root
            / "test.csv"
        ),
        dataset_root=dataset_root,
        transform=get_eval_transform()
    )

    # --------------------------------------------------
    # Balanced training sampler
    # --------------------------------------------------

    train_sampler = create_balanced_sampler(
        train_dataset
    )

    # --------------------------------------------------
    # DataLoaders
    # --------------------------------------------------

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        sampler=train_sampler,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )

    return (
        train_loader,
        validation_loader,
        test_loader
    )