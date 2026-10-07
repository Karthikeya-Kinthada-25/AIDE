from pathlib import Path
from collections import Counter


# IMD2020 location
DATASET_DIR = Path(
    r"C:\Users\karthikeya\OneDrive\Desktop\IMD2020"
)


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff"
}


def main():

    if not DATASET_DIR.exists():
        print("ERROR: IMD2020 folder not found.")
        print(DATASET_DIR)
        return

    folders = [
        folder
        for folder in DATASET_DIR.iterdir()
        if folder.is_dir()
    ]

    print("=" * 60)
    print("IMD2020 DATASET INSPECTION")
    print("=" * 60)

    print(f"Dataset path : {DATASET_DIR}")
    print(f"Folders found: {len(folders)}")
    print()

    original_count = 0
    tampered_count = 0
    mask_count = 0

    extension_counter = Counter()

    incomplete_folders = []

    for folder in folders:

        files = [
            file
            for file in folder.iterdir()
            if file.is_file()
        ]

        image_files = [
            file
            for file in files
            if file.suffix.lower() in IMAGE_EXTENSIONS
        ]

        for file in image_files:
            extension_counter[
                file.suffix.lower()
            ] += 1

        originals = [
            file
            for file in image_files
            if "_orig" in file.stem.lower()
        ]

        masks = [
            file
            for file in image_files
            if "_mask" in file.stem.lower()
        ]

        tampered = [
            file
            for file in image_files
            if "_mask" not in file.stem.lower()
            and "_orig" not in file.stem.lower()
        ]

        original_count += len(originals)
        tampered_count += len(tampered)
        mask_count += len(masks)

        # Expected basic structure:
        # at least one original,
        # one manipulated image,
        # and one mask.

        if (
            len(originals) == 0
            or len(tampered) == 0
            or len(masks) == 0
        ):
            incomplete_folders.append(
                folder.name
            )

    print("-" * 60)
    print("SUMMARY")
    print("-" * 60)

    print(
        f"Original images   : {original_count}"
    )

    print(
        f"Tampered images   : {tampered_count}"
    )

    print(
        f"Mask images       : {mask_count}"
    )

    print()

    print("File extensions:")

    for extension, count in sorted(
        extension_counter.items()
    ):
        print(
            f"  {extension}: {count}"
        )

    print()

    print(
        f"Folders with unexpected structure: "
        f"{len(incomplete_folders)}"
    )

    if incomplete_folders:

        print()
        print("First 20 problematic folders:")

        for folder in incomplete_folders[:20]:
            print(
                f"  - {folder}"
            )

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()