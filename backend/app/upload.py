from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid

router = APIRouter(
    prefix="/api/upload",
    tags=["Image Upload"]
)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/")
async def upload_image(file: UploadFile = File(...)):

    # Check filename
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = Path(file.filename).suffix.lower()

    # Check extension
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG images are allowed"
        )

    # Generate unique filename
    file_id = uuid.uuid4().hex
    saved_filename = f"{file_id}{extension}"

    file_path = UPLOAD_DIR / saved_filename

    # Save file
    contents = await file.read()
    file_path.write_bytes(contents)

    return {
        "status": "success",
        "message": "Image uploaded successfully",
        "original_filename": file.filename,
        "stored_filename": saved_filename,
        "file_size": len(contents),
        "file_type": extension
    }