from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
import pytesseract
import os
from pathlib import Path
import uuid

router = APIRouter(prefix="/ocr", tags=["OCR"])

# ❌ REMOVE Windows-only path
# pytesseract.pytesseract.tesseract_cmd = ...

UPLOAD_DIR = Path("/tmp/ocr_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # ✅ Validate image type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files allowed")

        # ✅ Unique filename (avoid overwrite)
        file_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{file.filename}"

        contents = await file.read()

        # ✅ Limit file size (5MB)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")

        with open(file_path, "wb") as f:
            f.write(contents)

        image = Image.open(file_path)

        text = pytesseract.image_to_string(image)

        return {
            "filename": file.filename,
            "extracted_text": text.strip()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
