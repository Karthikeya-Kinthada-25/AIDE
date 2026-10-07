from pathlib import Path

import cv2
import numpy as np


# =========================================================
# AIDE MANIPULATION-TYPE INDICATION ENGINE
# =========================================================
#
# IMPORTANT:
# This is a heuristic forensic indication module.
#
# It is NOT a trained multi-class manipulation classifier.
# It does NOT establish the actual manipulation type.
#
# It combines observable image characteristics such as:
# - self-similar feature matches
# - ELA behaviour
# - suspicious-region distribution
# - image texture / edge characteristics
#
# Output should be treated as a forensic review indication.
# =========================================================


def _clamp(value, minimum=0.0, maximum=100.0):
    return max(
        minimum,
        min(maximum, float(value))
    )


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# COPY-MOVE ANALYSIS
# =========================================================

def detect_copy_move_indication(image_path: Path):
    """
    Look for repeated local visual structures using ORB
    feature matching.

    This is a preliminary self-similarity analysis.
    It is not a validated copy-move detector.
    """

    try:

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_GRAYSCALE
        )

        if image is None:
            return {
                "status": "error",
                "score": 0.0,
                "matched_pairs": 0,
                "message": "Unable to read image."
            }

        # Resize extremely large images for efficient analysis.
        max_dimension = 1600

        height, width = image.shape

        scale = min(
            1.0,
            max_dimension / max(
                height,
                width
            )
        )

        if scale < 1.0:

            image = cv2.resize(
                image,
                (
                    int(width * scale),
                    int(height * scale)
                ),
                interpolation=cv2.INTER_AREA
            )

        # Slight blur reduces insignificant pixel noise.
        image = cv2.GaussianBlur(
            image,
            (3, 3),
            0
        )

        orb = cv2.ORB_create(
            nfeatures=1500,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=31,
            patchSize=31
        )

        keypoints, descriptors = orb.detectAndCompute(
            image,
            None
        )

        if descriptors is None or len(keypoints) < 20:

            return {
                "status": "success",
                "score": 0.0,
                "matched_pairs": 0,
                "keypoints": len(keypoints),
                "message": "Insufficient local features for self-similarity analysis."
            }

        matcher = cv2.BFMatcher(
            cv2.NORM_HAMMING,
            crossCheck=False
        )

        knn_matches = matcher.knnMatch(
            descriptors,
            descriptors,
            k=2
        )

        good_matches = []

        for pair in knn_matches:

            if len(pair) < 2:
                continue

            first, second = pair

            # Lowe-style ratio filtering.
            if first.distance < 0.72 * second.distance:

                # Do not count a feature matching itself.
                if first.queryIdx == first.trainIdx:
                    continue

                kp1 = keypoints[first.queryIdx]
                kp2 = keypoints[first.trainIdx]

                x1, y1 = kp1.pt
                x2, y2 = kp2.pt

                distance = np.sqrt(
                    (x1 - x2) ** 2 +
                    (y1 - y2) ** 2
                )

                # Ignore very close points.
                # Copy-move duplication should generally produce
                # spatially separated repeated structures.
                if distance > 40:

                    good_matches.append(
                        first
                    )

        matched_pairs = len(good_matches)

        # Conservative heuristic scoring.
        if matched_pairs >= 35:
            score = 90.0

        elif matched_pairs >= 25:
            score = 75.0

        elif matched_pairs >= 15:
            score = 55.0

        elif matched_pairs >= 8:
            score = 30.0

        else:
            score = 10.0

        return {
            "status": "success",
            "score": round(
                _clamp(score),
                2
            ),
            "matched_pairs": matched_pairs,
            "keypoints": len(keypoints),
            "message": (
                "Self-similar local features were examined "
                "as a preliminary copy-move indication."
            )
        }

    except Exception as error:

        return {
            "status": "error",
            "score": 0.0,
            "matched_pairs": 0,
            "message": str(error)
        }


# =========================================================
# ELA / SPLICING INDICATION
# =========================================================

def calculate_splicing_indication(
    ela_analysis,
    localization
):
    """
    Estimate a preliminary splicing indication using:
    - ELA variation
    - candidate-region count
    - maximum ELA error
    """

    mean_error = _safe_float(
        ela_analysis.get(
            "mean_error"
        )
    )

    standard_deviation = _safe_float(
        ela_analysis.get(
            "standard_deviation"
        )
    )

    maximum_error = _safe_float(
        ela_analysis.get(
            "maximum_error"
        )
    )

    region_count = int(
        localization.get(
            "candidate_regions",
            0
        ) or 0
    )

    score = 0.0

    # ELA variation contribution.
    if mean_error >= 0.5:
        score += 30

    elif mean_error >= 0.3:
        score += 20

    elif mean_error >= 0.15:
        score += 10

    # Standard deviation contribution.
    if standard_deviation >= 1.5:
        score += 30

    elif standard_deviation >= 0.8:
        score += 20

    elif standard_deviation >= 0.4:
        score += 10

    # Maximum difference contribution.
    if maximum_error >= 20:
        score += 20

    elif maximum_error >= 10:
        score += 15

    elif maximum_error >= 5:
        score += 8

    # Candidate-region contribution.
    if region_count >= 8:
        score += 20

    elif region_count >= 5:
        score += 15

    elif region_count >= 3:
        score += 10

    return round(
        _clamp(score),
        2
    )


# =========================================================
# OBJECT REMOVAL INDICATION
# =========================================================

def calculate_object_removal_indication(
    localization,
    image_width,
    image_height
):
    """
    Estimate a preliminary object-removal indication from
    suspicious-region geometry.

    Large irregular regions may be worth examining for
    object-removal/inpainting behaviour.

    This is NOT an object-removal detector.
    """

    regions = localization.get(
        "regions",
        []
    )

    if not isinstance(regions, list):
        return 0.0

    if image_width <= 0 or image_height <= 0:
        return 0.0

    image_area = (
        image_width *
        image_height
    )

    largest_area_ratio = 0.0

    irregular_region_count = 0

    for region in regions:

        width = _safe_float(
            region.get("width")
        )

        height = _safe_float(
            region.get("height")
        )

        area = _safe_float(
            region.get("area")
        )

        if area <= 0:
            area = width * height

        ratio = (
            area /
            image_area
        )

        largest_area_ratio = max(
            largest_area_ratio,
            ratio
        )

        if width > 0 and height > 0:

            aspect_ratio = max(
                width / height,
                height / width
            )

            if aspect_ratio > 3.0:
                irregular_region_count += 1

    score = 0.0

    if largest_area_ratio >= 0.08:
        score += 50

    elif largest_area_ratio >= 0.04:
        score += 35

    elif largest_area_ratio >= 0.02:
        score += 20

    if irregular_region_count >= 3:
        score += 30

    elif irregular_region_count >= 1:
        score += 15

    if len(regions) >= 5:
        score += 20

    return round(
        _clamp(score),
        2
    )


# =========================================================
# COMPRESSION INCONSISTENCY
# =========================================================

def calculate_compression_indication(
    ela_analysis
):
    """
    Estimate whether compression behaviour itself deserves
    additional examination.
    """

    mean_error = _safe_float(
        ela_analysis.get(
            "mean_error"
        )
    )

    standard_deviation = _safe_float(
        ela_analysis.get(
            "standard_deviation"
        )
    )

    score = 0.0

    if mean_error >= 0.5:
        score += 50

    elif mean_error >= 0.3:
        score += 35

    elif mean_error >= 0.15:
        score += 20

    if standard_deviation >= 1.5:
        score += 50

    elif standard_deviation >= 0.8:
        score += 35

    elif standard_deviation >= 0.4:
        score += 20

    return round(
        _clamp(score),
        2
    )


# =========================================================
# MAIN CLASSIFICATION / INDICATION FUNCTION
# =========================================================

def classify_manipulation_type(
    image_path: Path,
    ela_analysis: dict,
    localization: dict,
    image_width: int,
    image_height: int
):
    """
    Generate a preliminary manipulation-type indication.

    The output is intentionally labelled as an indication and
    not a definitive classification.
    """

    copy_move = detect_copy_move_indication(
        image_path
    )

    splicing_score = calculate_splicing_indication(
        ela_analysis,
        localization
    )

    object_removal_score = (
        calculate_object_removal_indication(
            localization,
            image_width,
            image_height
        )
    )

    compression_score = (
        calculate_compression_indication(
            ela_analysis
        )
    )

    scores = {
        "Copy-Move Indication": copy_move["score"],
        "Splicing Indication": splicing_score,
        "Object-Removal Indication": object_removal_score,
        "Compression Inconsistency": compression_score,
    }

    primary_type = max(
        scores,
        key=scores.get
    )

    primary_score = scores[
        primary_type
    ]

    # Avoid claiming a manipulation type when
    # the evidence is too weak.
    if primary_score < 30:

        primary_type = (
            "No Strong Manipulation-Type "
            "Indication"
        )

    # Build ordered evidence list.
    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    indications = []

    for name, score in ranked:

        if score >= 30:

            indications.append(
                {
                    "type": name,
                    "score": round(
                        score,
                        2
                    )
                }
            )

    return {
        "status": "success",
        "analysis_type": (
            "Heuristic Manipulation-Type "
            "Indication"
        ),
        "primary_indication": primary_type,
        "primary_score": round(
            primary_score,
            2
        ),
        "indications": indications,
        "scores": {
            key: round(
                value,
                2
            )
            for key, value in scores.items()
        },
        "copy_move_analysis": copy_move,
        "warning": (
            "This is a preliminary heuristic indication "
            "based on image forensic characteristics. "
            "It is not a trained multi-class classifier "
            "and does not establish the actual manipulation "
            "type. Results require further forensic review."
        )
    }