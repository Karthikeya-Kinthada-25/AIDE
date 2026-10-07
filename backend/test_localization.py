from pathlib import Path

from app.localization import (
    generate_suspicious_region_map
)


# =========================================================
# TEST IMAGE
# =========================================================

IMAGE_PATH = (
    Path(__file__).resolve().parent
    / "uploads"
    / "0c97f813e4214c4a991c4e6ff251f54a.jpg"
)


# =========================================================
# MAIN TEST
# =========================================================

def main():

    print("=" * 60)

    print(
        "AIDE SUSPICIOUS-REGION LOCALIZATION TEST"
    )

    print("=" * 60)


    print(
        f"Image: {IMAGE_PATH.name}"
    )


    if not IMAGE_PATH.exists():

        print()

        print(
            "ERROR: Test image was not found."
        )

        print(
            f"Expected path: {IMAGE_PATH}"
        )

        return


    print()

    print(
        "Running localization..."
    )


    result = generate_suspicious_region_map(
        IMAGE_PATH
    )


    print()

    print(
        "RESULT"
    )

    print("-" * 60)


    print(
        f"Status: "
        f"{result.get('status')}"
    )


    if result.get("status") != "success":

        print(
            f"Message: "
            f"{result.get('message')}"
        )

        return


    print(
        f"Method: "
        f"{result.get('method')}"
    )


    print(
        f"Threshold: "
        f"{result.get('threshold_value')}"
    )


    print(
        f"Candidate regions: "
        f"{result.get('candidate_region_count')}"
    )


    print(
        f"Mean difference: "
        f"{result.get('mean_difference')}"
    )


    print(
        f"Maximum difference: "
        f"{result.get('maximum_difference')}"
    )


    print(
        f"Difference standard deviation: "
        f"{result.get('difference_standard_deviation')}"
    )


    print()

    print(
        "REGIONS"
    )

    print("-" * 60)


    regions = result.get(
        "regions",
        []
    )


    if not regions:

        print(
            "No candidate regions detected."
        )

    else:

        for index, region in enumerate(
            regions,
            start=1
        ):

            print(
                f"Region {index}: "
                f"x={region['x']}, "
                f"y={region['y']}, "
                f"width={region['width']}, "
                f"height={region['height']}, "
                f"area={region['area']}"
            )


    print()

    print(
        "Visualization:"
    )

    print(
        result.get(
            "localization_image"
        )
    )


    print()

    print(
        "Warning:"
    )

    print(
        result.get(
            "warning"
        )
    )


    print()

    print("=" * 60)

    print(
        "LOCALIZATION TEST COMPLETED"
    )

    print("=" * 60)


if __name__ == "__main__":

    main()