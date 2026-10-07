from pathlib import Path
from PIL import Image
import numpy as np
import cv2


def calculate_entropy(gray_image):
    """
    Calculate Shannon entropy of a grayscale image.
    """

    histogram = cv2.calcHist(
        [gray_image],
        [0],
        None,
        [256],
        [0, 256]
    )

    histogram = histogram.flatten()

    total = histogram.sum()

    if total == 0:
        return 0.0

    probabilities = histogram / total

    probabilities = probabilities[
        probabilities > 0
    ]

    entropy = -np.sum(
        probabilities *
        np.log2(probabilities)
    )

    return float(entropy)


def calculate_noise(gray_image):
    """
    Estimate high-frequency image noise by subtracting
    a Gaussian-smoothed version from the original.
    """

    blurred = cv2.GaussianBlur(
        gray_image,
        (5, 5),
        0
    )

    noise = (
        gray_image.astype(np.float32)
        - blurred.astype(np.float32)
    )

    noise_mean = float(
        np.mean(np.abs(noise))
    )

    noise_std = float(
        np.std(noise)
    )

    return {
        "noise_mean": round(
            noise_mean,
            4
        ),
        "noise_standard_deviation": round(
            noise_std,
            4
        )
    }


def calculate_edge_density(gray_image):
    """
    Calculate the percentage of pixels that belong
    to detected edges.
    """

    edges = cv2.Canny(
        gray_image,
        100,
        200
    )

    edge_pixels = np.count_nonzero(edges)

    total_pixels = edges.size

    if total_pixels == 0:
        return 0.0

    density = (
        edge_pixels /
        total_pixels
    ) * 100

    return float(density)


def calculate_laplacian_variance(gray_image):
    """
    Measure high-frequency detail/sharpness.
    """

    laplacian = cv2.Laplacian(
        gray_image,
        cv2.CV_64F
    )

    return float(
        laplacian.var()
    )


def extract_forensic_features(
    file_path: Path
):

    image = cv2.imread(
        str(file_path)
    )

    if image is None:
        raise ValueError(
            "Unable to read image"
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    entropy = calculate_entropy(
        gray
    )

    noise = calculate_noise(
        gray
    )

    edge_density = calculate_edge_density(
        gray
    )

    laplacian_variance = (
        calculate_laplacian_variance(
            gray
        )
    )

    return {
        "entropy": round(
            entropy,
            4
        ),

        "noise": noise,

        "edge_density_percent": round(
            edge_density,
            4
        ),

        "laplacian_variance": round(
            laplacian_variance,
            4
        )
    }