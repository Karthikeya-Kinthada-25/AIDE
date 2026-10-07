from typing import Dict


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0
) -> float:
    return max(minimum, min(maximum, value))


def calculate_ela_indicator(ela: Dict) -> float:
    """
    Prototype indicator derived from ELA mean error.

    Lower reconstruction error generally indicates greater
    consistency with the current JPEG compression pattern.

    This is NOT a tampering probability.
    """

    mean_error = float(ela.get("mean_error", 0.0))

    # Prototype normalization.
    # Values are intentionally capped rather than treated
    # as a probability of authenticity.
    indicator = 100.0 - (mean_error * 10.0)

    return round(clamp(indicator), 2)


def calculate_noise_indicator(noise: Dict) -> float:
    """
    Prototype indicator based on noise standard deviation.

    This represents consistency of the measured noise pattern.
    It is not an independent tampering detector.
    """

    noise_std = float(
        noise.get("noise_standard_deviation", 0.0)
    )

    indicator = 100.0 - (noise_std * 5.0)

    return round(clamp(indicator), 2)


def calculate_image_statistics_indicator(
    features: Dict
) -> float:
    """
    Supporting image-statistics indicator derived from entropy.

    Entropy is treated only as an image statistic and is NOT
    interpreted as image authenticity or image quality.
    """

    entropy = float(features.get("entropy", 0.0))

    indicator = (entropy / 8.0) * 100.0

    return round(clamp(indicator), 2)


def calculate_fusion_score(
    ela_indicator: float,
    noise_indicator: float,
    image_statistics_indicator: float
) -> float:
    """
    Calculate a prototype forensic consistency index.

    IMPORTANT:
    This weighted score is a research prototype and has not
    been statistically calibrated against a forensic dataset.
    It must NOT be interpreted as probability of authenticity
    or probability of tampering.
    """

    weights = {
        "ela": 0.45,
        "noise": 0.30,
        "image_statistics": 0.25
    }

    score = (
        ela_indicator * weights["ela"]
        + noise_indicator * weights["noise"]
        + image_statistics_indicator * weights["image_statistics"]
    )

    return round(clamp(score), 2)


def classify_consistency(score: float) -> Dict:
    """
    Classify the prototype forensic consistency index.

    The classification describes consistency of the measured
    indicators only. It is NOT an authenticity classification.
    """

    if score >= 75:
        return {
            "level": "HIGH CONSISTENCY",
            "description": (
                "The measured forensic indicators show "
                "relatively high consistency with the current "
                "analysis conditions."
            )
        }

    if score >= 50:
        return {
            "level": "MODERATE CONSISTENCY",
            "description": (
                "The measured forensic indicators show "
                "moderate consistency. Additional examination "
                "is recommended."
            )
        }

    return {
        "level": "LOW CONSISTENCY",
        "description": (
            "The measured forensic indicators show lower "
            "consistency. Additional examination is recommended."
        )
    }


def generate_fusion_analysis(
    ela: Dict,
    features: Dict
) -> Dict:

    noise = features.get("noise", {})

    ela_indicator = calculate_ela_indicator(ela)

    noise_indicator = calculate_noise_indicator(noise)

    image_statistics_indicator = (
        calculate_image_statistics_indicator(features)
    )

    fusion_score = calculate_fusion_score(
        ela_indicator,
        noise_indicator,
        image_statistics_indicator
    )

    classification = classify_consistency(fusion_score)

    return {
        "score_type": "Prototype Forensic Consistency Index",

        "score": fusion_score,

        "indicators": {
            "ela": ela_indicator,
            "noise": noise_indicator,
            "image_statistics": image_statistics_indicator
        },

        "weights": {
            "ela": 0.45,
            "noise": 0.30,
            "image_statistics": 0.25
        },

        "assessment": classification,

        "warning": (
            "This is a prototype forensic consistency index "
            "based on multiple image indicators. It is not a "
            "validated probability of authenticity or tampering "
            "and should not be interpreted as a final forensic verdict."
        )
    }