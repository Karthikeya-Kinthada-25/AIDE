from pathlib import Path

from app.ai_detector.inference import AIDetector


IMAGE_PATH = Path(
    r"C:\Users\Karthikeya\OneDrive\Desktop\AIDE\backend\uploads"
)


def main():

    images = list(
        IMAGE_PATH.glob("*.jpg")
    ) + list(
        IMAGE_PATH.glob("*.jpeg")
    ) + list(
        IMAGE_PATH.glob("*.png")
    )

    if not images:
        print("No images found in uploads folder.")
        return

    image = images[0]

    print("=" * 60)
    print("AIDE AI INFERENCE TEST")
    print("=" * 60)

    print(f"Image: {image.name}")

    detector = AIDetector()

    result = detector.predict(
        image
    )

    print()
    print(result)


if __name__ == "__main__":
    main()