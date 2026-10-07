from pathlib import Path
from PIL import Image, ImageChops
import numpy as np
import cv2


def perform_ela(file_path: Path, quality: int = 90):

    # ELA is primarily intended for JPEG images
    if file_path.suffix.lower() not in {".jpg", ".jpeg"}:
        return {
            "status": "not_applicable",
            "message": (
                "ELA is primarily designed for JPEG compression analysis. "
                "A JPEG image is required."
            )
        }

    original = Image.open(file_path).convert("RGB")

    # --------------------------------------------------
    # RECOMPRESS IMAGE
    # --------------------------------------------------

    temp_path = file_path.parent / f"{file_path.stem}_ela_temp.jpg"

    original.save(
        temp_path,
        "JPEG",
        quality=quality
    )

    recompressed = Image.open(temp_path).convert("RGB")

    # --------------------------------------------------
    # PIXEL DIFFERENCE
    # --------------------------------------------------

    difference = ImageChops.difference(
        original,
        recompressed
    )

    difference_gray = difference.convert("L")

    diff_array = np.asarray(
        difference_gray
    ).astype(np.float32)

    # --------------------------------------------------
    # FORENSIC STATISTICS
    # --------------------------------------------------

    mean_error = float(np.mean(diff_array))
    max_error = float(np.max(diff_array))
    standard_deviation = float(np.std(diff_array))

    # --------------------------------------------------
    # ROBUST NORMALIZATION
    # --------------------------------------------------

    lower = np.percentile(diff_array, 1)
    upper = np.percentile(diff_array, 99.5)

    if upper <= lower:
        upper = lower + 1

    normalized = np.clip(
        (diff_array - lower) / (upper - lower),
        0,
        1
    )

    # Slight gamma correction
    normalized = np.power(
        normalized,
        0.75
    )

    ela_gray = (
        normalized * 255
    ).astype(np.uint8)

    # --------------------------------------------------
    # SMOOTH SMALL PIXEL NOISE
    # --------------------------------------------------

    ela_gray = cv2.GaussianBlur(
        ela_gray,
        (3, 3),
        0
    )

    # --------------------------------------------------
    # APPLY FORENSIC HEATMAP
    # --------------------------------------------------

    ela_heatmap = cv2.applyColorMap(
        ela_gray,
        cv2.COLORMAP_JET
    )

    # Convert BGR → RGB
    ela_heatmap = cv2.cvtColor(
        ela_heatmap,
        cv2.COLOR_BGR2RGB
    )

    ela_image = Image.fromarray(
        ela_heatmap
    )

    # --------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------

    ela_path = file_path.parent / f"{file_path.stem}_ela.png"

    ela_image.save(
        ela_path
    )

    # Remove temporary JPEG
    temp_path.unlink(
        missing_ok=True
    )

    return {
        "status": "success",
        "analysis_type": "Error Level Analysis",
        "compression_quality": quality,
        "mean_error": round(mean_error, 4),
        "maximum_error": round(max_error, 4),
        "standard_deviation": round(
            standard_deviation,
            4
        ),
        "visualization": "ELA heatmap",
        "ela_image": ela_path.name
    }