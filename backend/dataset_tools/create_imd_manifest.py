from pathlib import Path
import csv


DATASET_DIR = Path(
    r"C:\Users\karthikeya\OneDrive\Desktop\IMD2020"
)

OUTPUT_FILE = Path(
    r"C:\Users\karthikeya\OneDrive\Desktop\AIDE\backend\dataset_tools\imd2020_manifest.csv"
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff"
}


def is_image(file):
    return (
        file.is_file()
        and file.suffix.lower()
        in IMAGE_EXTENSIONS
    )


def main():

    if not DATASET_DIR.exists():
        print("ERROR: Dataset directory not found.")
        print(DATASET_DIR)
        return

    rows = []

    folders = sorted(
        [
            folder
            for folder in DATASET_DIR.iterdir()
            if folder.is_dir()
        ],
        key=lambda x: x.name
    )

    for folder in folders:

        files = [
            file
            for file in folder.iterdir()
            if is_image(file)
        ]

        originals = [
            file
            for file in files
            if "_orig" in file.stem.lower()
        ]

        masks = {
            file.stem.lower().replace(
                "_mask", ""
            ): file
            for file in files
            if "_mask" in file.stem.lower()
        }

        tampered_images = [
            file
            for file in files
            if "_orig" not in file.stem.lower()
            and "_mask" not in file.stem.lower()
        ]

        if len(originals) != 1:
            print(
                f"WARNING: {folder.name} "
                f"has {len(originals)} original images."
            )
            continue

        original = originals[0]

        # Add one authentic/original row.
        rows.append({
            "case_id": folder.name,
            "image_path": str(
                original.relative_to(DATASET_DIR)
            ),
            "mask_path": "",
            "label": 0,
            "image_type": "original"
        })

        # Add manipulated rows.
        for tampered in tampered_images:

            tampered_key = tampered.stem.lower()

            mask = masks.get(
                tampered_key
            )

            if mask is None:
                print(
                    f"WARNING: No mask found for "
                    f"{tampered}"
                )
                continue

            rows.append({
                "case_id": folder.name,
                "image_path": str(
                    tampered.relative_to(DATASET_DIR)
                ),
                "mask_path": str(
                    mask.relative_to(DATASET_DIR)
                ),
                "label": 1,
                "image_type": "tampered"
            })

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        fieldnames = [
            "case_id",
            "image_path",
            "mask_path",
            "label",
            "image_type"
        ]

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    original_rows = sum(
        1
        for row in rows
        if row["label"] == 0
    )

    tampered_rows = sum(
        1
        for row in rows
        if row["label"] == 1
    )

    print("=" * 60)
    print("IMD2020 MANIFEST CREATED")
    print("=" * 60)

    print(
        f"Total rows      : {len(rows)}"
    )

    print(
        f"Original rows    : {original_rows}"
    )

    print(
        f"Tampered rows    : {tampered_rows}"
    )

    print(
        f"Output file     : {OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()