from pathlib import Path
from PIL import Image
import exifread


def analyze_image(file_path: Path):

    result = {
        "image": {},
        "metadata": {},
        "metadata_status": "Not Available"
    }

    # -----------------------------------------
    # BASIC IMAGE INFORMATION
    # -----------------------------------------

    with Image.open(file_path) as image:

        result["image"] = {
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "file_size_bytes": file_path.stat().st_size,
            "megapixels": round(
                (image.width * image.height) / 1_000_000,
                2
            )
        }

    # -----------------------------------------
    # EXIF METADATA
    # -----------------------------------------

    with open(file_path, "rb") as image_file:

        tags = exifread.process_file(
            image_file,
            details=False
        )

    metadata = {}

    interesting_tags = {
        "Image Make": "camera_make",
        "Image Model": "camera_model",
        "Image DateTime": "capture_datetime",
        "EXIF DateTimeOriginal": "original_datetime",
        "GPS GPSLatitude": "gps_latitude",
        "GPS GPSLongitude": "gps_longitude",
        "Image Software": "software",
        "Image Orientation": "orientation"
    }

    for tag, key in interesting_tags.items():

        if tag in tags:

            metadata[key] = str(tags[tag])

    result["metadata"] = metadata

    if metadata:
        result["metadata_status"] = "Available"
    else:
        result["metadata_status"] = "No EXIF metadata detected"

    return result