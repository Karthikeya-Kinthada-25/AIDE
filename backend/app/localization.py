from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageChops


# =========================================================
# AIDE SUSPICIOUS-REGION LOCALIZATION
# =========================================================
#
# Preliminary suspicious-region localization based on
# ELA-derived pixel-difference information.
#
# IMPORTANT:
# The detected regions are candidate regions for further
# forensic examination.
#
# They are NOT definitive proof of image manipulation.
#
# Large connected components are filtered because broad
# JPEG/compression variations are not useful as localized
# suspicious regions.
# =========================================================


def generate_suspicious_region_map(
    file_path: Path,
    quality: int = 90,
    threshold_percentile: float = 99.0
):
    """
    Generate a preliminary suspicious-region
    visualization using ELA-derived differences.
    """

    file_path = Path(file_path)


    # =====================================================
    # 1. Validate file type
    # =====================================================

    if file_path.suffix.lower() not in {
        ".jpg",
        ".jpeg"
    }:

        return {
            "status": "not_applicable",

            "message": (
                "Suspicious-region localization currently "
                "requires a JPEG image because it uses "
                "ELA-derived difference information."
            )
        }


    # =====================================================
    # 2. Load original image
    # =====================================================

    original = Image.open(
        file_path
    ).convert("RGB")


    # =====================================================
    # 3. JPEG recompression
    # =====================================================

    temp_path = (
        file_path.parent /
        f"{file_path.stem}_localization_temp.jpg"
    )


    original.save(
        temp_path,
        "JPEG",
        quality=quality
    )


    recompressed = Image.open(
        temp_path
    ).convert("RGB")


    # =====================================================
    # 4. Calculate ELA-derived difference
    # =====================================================

    difference = ImageChops.difference(
        original,
        recompressed
    )


    difference_gray = difference.convert(
        "L"
    )


    diff_array = np.asarray(
        difference_gray
    ).astype(
        np.float32
    )


    # =====================================================
    # 5. Remove temporary file
    # =====================================================

    temp_path.unlink(
        missing_ok=True
    )


    # =====================================================
    # 6. Difference statistics
    # =====================================================

    mean_difference = float(
        np.mean(diff_array)
    )


    max_difference = float(
        np.max(diff_array)
    )


    standard_deviation = float(
        np.std(diff_array)
    )


    # =====================================================
    # 7. Adaptive threshold
    # =====================================================

    threshold_value = float(
        np.percentile(
            diff_array,
            threshold_percentile
        )
    )


    # =====================================================
    # 8. Threshold fallback
    # =====================================================

    if threshold_value <= 0:

        positive_values = diff_array[
            diff_array > 0
        ]


        if positive_values.size > 0:

            threshold_value = float(
                np.percentile(
                    positive_values,
                    95
                )
            )

        else:

            threshold_value = 1.0


    if threshold_value <= 0:

        threshold_value = 1.0


    # =====================================================
    # 9. Create candidate mask
    # =====================================================

    candidate_mask = (

        diff_array >= threshold_value

    ).astype(

        np.uint8

    ) * 255


    # =====================================================
    # 10. Conservative morphological cleanup
    # =====================================================

    cleanup_kernel = cv2.getStructuringElement(

        cv2.MORPH_ELLIPSE,

        (3, 3)

    )


    candidate_mask = cv2.morphologyEx(

        candidate_mask,

        cv2.MORPH_CLOSE,

        cleanup_kernel

    )


    # =====================================================
    # 11. Image dimensions
    # =====================================================

    image_height, image_width = (
        candidate_mask.shape
    )


    image_area = (
        image_width *
        image_height
    )


    # =====================================================
    # 12. Find candidate contours
    # =====================================================

    contours, _ = cv2.findContours(

        candidate_mask,

        cv2.RETR_EXTERNAL,

        cv2.CHAIN_APPROX_SIMPLE

    )


    # =====================================================
    # 13. Candidate filtering limits
    # =====================================================
    #
    # These limits prevent broad compression differences
    # from becoming "suspicious regions".
    #
    # A candidate must:
    #
    #   1. Be larger than the minimum area.
    #   2. Be smaller than the maximum area.
    #   3. Not span an excessive portion of the image.
    #
    # These are visualization/filtering constraints,
    # not forensic proof thresholds.
    # =====================================================

    minimum_area = max(

        100.0,

        image_area * 0.000002

    )


    maximum_area = (

        image_area * 0.01

    )


    maximum_width = (

        image_width * 0.25

    )


    maximum_height = (

        image_height * 0.25

    )


    regions = []


    rejected_large_regions = 0


    # =====================================================
    # 14. Extract candidate regions
    # =====================================================

    for contour in contours:

        area = cv2.contourArea(
            contour
        )


        if area < minimum_area:

            continue


        x, y, width, height = (
            cv2.boundingRect(
                contour
            )
        )


        # -------------------------------------------------
        # Reject excessively large connected regions
        # -------------------------------------------------

        if area > maximum_area:

            rejected_large_regions += 1

            continue


        if width > maximum_width:

            rejected_large_regions += 1

            continue


        if height > maximum_height:

            rejected_large_regions += 1

            continue


        # -------------------------------------------------
        # Region mask
        # -------------------------------------------------

        region_mask = np.zeros(

            candidate_mask.shape,

            dtype=np.uint8

        )


        cv2.drawContours(

            region_mask,

            [contour],

            -1,

            255,

            -1

        )


        # -------------------------------------------------
        # Region statistics
        # -------------------------------------------------

        region_values = diff_array[
            region_mask > 0
        ]


        if region_values.size > 0:

            region_mean_difference = float(

                np.mean(
                    region_values
                )

            )


            region_max_difference = float(

                np.max(
                    region_values
                )

            )

        else:

            region_mean_difference = 0.0

            region_max_difference = 0.0


        candidate_pixel_count = cv2.countNonZero(

            cv2.bitwise_and(

                candidate_mask,

                region_mask

            )

        )


        regions.append({

            "x": int(x),

            "y": int(y),

            "width": int(width),

            "height": int(height),

            "area": round(

                float(area),

                2

            ),

            "candidate_pixel_count": int(

                candidate_pixel_count

            ),

            "relative_area_percent": round(

                (

                    float(area) /

                    float(image_area)

                ) * 100,

                4

            ),

            "mean_difference": round(

                region_mean_difference,

                4

            ),

            "maximum_difference": round(

                region_max_difference,

                4

            )

        })


    # =====================================================
    # 15. Sort candidate regions
    # =====================================================

    regions.sort(

        key=lambda region: (

            region["candidate_pixel_count"],

            region["maximum_difference"]

        ),

        reverse=True

    )


    # =====================================================
    # 16. Limit number of displayed candidates
    # =====================================================

    max_display_regions = 5


    regions = regions[
        :max_display_regions
    ]


    # =====================================================
    # 17. Read original image with OpenCV
    # =====================================================

    original_cv = cv2.imread(

        str(file_path)

    )


    if original_cv is None:

        raise ValueError(

            "Unable to read image for localization."

        )


    visualization = original_cv.copy()


    # =====================================================
    # 18. Draw candidate regions
    # =====================================================

    for index, region in enumerate(

        regions,

        start=1

    ):

        x = region["x"]

        y = region["y"]

        width = region["width"]

        height = region["height"]


        # -------------------------------------------------
        # Small visual expansion
        # -------------------------------------------------

        expansion_x = max(

            6,

            int(width * 0.08)

        )


        expansion_y = max(

            6,

            int(height * 0.08)

        )


        x1 = max(

            0,

            x - expansion_x

        )


        y1 = max(

            0,

            y - expansion_y

        )


        x2 = min(

            image_width - 1,

            x + width + expansion_x

        )


        y2 = min(

            image_height - 1,

            y + height + expansion_y

        )


        # -------------------------------------------------
        # Bounding box
        # -------------------------------------------------

        cv2.rectangle(

            visualization,

            (x1, y1),

            (x2, y2),

            (0, 0, 255),

            4

        )


        # -------------------------------------------------
        # Candidate label
        # -------------------------------------------------

        label = (

            f"Candidate {index}"

        )


        font = (
            cv2.FONT_HERSHEY_SIMPLEX
        )


        font_scale = max(

            0.55,

            image_width / 6500

        )


        thickness = 2


        (

            text_width,

            text_height

        ), baseline = cv2.getTextSize(

            label,

            font,

            font_scale,

            thickness

        )


        label_x = x1


        label_y = max(

            text_height + 10,

            y1

        )


        # -------------------------------------------------
        # Label background
        # -------------------------------------------------

        cv2.rectangle(

            visualization,

            (

                label_x,

                label_y - text_height - 10

            ),

            (

                label_x + text_width + 12,

                label_y + baseline - 4

            ),

            (0, 0, 255),

            -1

        )


        # -------------------------------------------------
        # Label text
        # -------------------------------------------------

        cv2.putText(

            visualization,

            label,

            (

                label_x + 6,

                label_y - 5

            ),

            font,

            font_scale,

            (255, 255, 255),

            thickness,

            cv2.LINE_AA

        )


    # =====================================================
    # 19. Information banner
    # =====================================================

    banner_height = max(

        80,

        int(image_height * 0.045)

    )


    banner = np.zeros(

        (

            banner_height,

            image_width,

            3

        ),

        dtype=np.uint8

    )


    title = (

        "AIDE - PRELIMINARY "

        "SUSPICIOUS-REGION LOCALIZATION"

    )


    subtitle = (

        f"Candidate regions: {len(regions)}"

    )


    title_scale = max(

        0.65,

        image_width / 5500

    )


    subtitle_scale = max(

        0.5,

        image_width / 7500

    )


    cv2.putText(

        banner,

        title,

        (

            20,

            int(banner_height * 0.43)

        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        title_scale,

        (255, 255, 255),

        2,

        cv2.LINE_AA

    )


    cv2.putText(

        banner,

        subtitle,

        (

            20,

            int(banner_height * 0.82)

        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        subtitle_scale,

        (190, 190, 190),

        1,

        cv2.LINE_AA

    )


    visualization = np.vstack(

        [

            banner,

            visualization

        ]

    )


    # =====================================================
    # 20. Save visualization
    # =====================================================

    output_path = (

        file_path.parent /

        f"{file_path.stem}_suspicious_regions.jpg"

    )


    success = cv2.imwrite(

        str(output_path),

        visualization,

        [

            cv2.IMWRITE_JPEG_QUALITY,

            92

        ]

    )


    if not success:

        raise ValueError(

            "Unable to save suspicious-region "

            "visualization."

        )


    # =====================================================
    # 21. Return result
    # =====================================================

    return {

        "status": "success",

        "analysis_type": (

            "Preliminary Suspicious-Region Localization"

        ),

        "method": (

            "ELA-derived high-difference "

            "region analysis"

        ),

        "compression_quality": quality,

        "threshold_percentile": (

            threshold_percentile

        ),

        "threshold_value": round(

            threshold_value,

            4

        ),

        "image_width": int(

            image_width

        ),

        "image_height": int(

            image_height

        ),

        "mean_difference": round(

            mean_difference,

            4

        ),

        "maximum_difference": round(

            max_difference,

            4

        ),

        "difference_standard_deviation": round(

            standard_deviation,

            4

        ),

        "candidate_region_count": len(

            regions

        ),

        "rejected_large_regions": int(

            rejected_large_regions

        ),

        "filtering": {

            "minimum_area": round(

                minimum_area,

                2

            ),

            "maximum_area": round(

                maximum_area,

                2

            ),

            "maximum_width": int(

                maximum_width

            ),

            "maximum_height": int(

                maximum_height

            )

        },

        "regions": regions,

        "visualization": (

            "Conservative ELA-derived candidate "

            "regions with oversized connected "

            "components filtered out."

        ),

        "localization_image": (

            output_path.name

        ),

        "warning": (

            "This is a preliminary suspicious-region "

            "localization based on ELA-derived difference "

            "information. Highlighted regions are candidate "

            "areas for further forensic examination and do "

            "not by themselves prove image manipulation."

        )

    }