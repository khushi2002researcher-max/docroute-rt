from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlalchemy.orm import Session
from PIL import Image
import pytesseract
import os
import pdfplumber
from pdf2image import convert_from_path
import docx
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from io import BytesIO
from PIL import ImageEnhance
from uuid import uuid4
from datetime import datetime, timedelta, timezone


from app.auth.schemas import ForgotPasswordSchema, ResetPasswordSchema
from app.email import send_reminder_email



from app.database import get_db
from app.auth.models import User, OCRHistory
from app.auth.schemas import RegisterSchema, LoginSchema
from app.auth.utils import (
    hash_password,
    verify_password,
    create_token,
    revoke_token,
    get_current_user,
)

# =====================================================
# ROUTER
# =====================================================
auth_router = APIRouter(prefix="/auth", tags=["Auth & OCR"])

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# =====================================================
# CONFIG
# =====================================================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

AVATAR_DIR = os.path.join("uploads", "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)


# ======================
# TESSERACT CONFIG (DEPLOY SAFE)
# ======================

if os.name == "nt":  # Only set for Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    POPPLER_PATH = r"C:\poppler\Library\bin"
else:
    # Render/Linux
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    POPPLER_PATH = None


# =====================================================
# OCR FUNCTION
# =====================================================
def perform_ocr(file_path: str, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    text = ""

    try:
        # ================= IMAGE =================
        if ext in ["jpg", "jpeg", "png"]:
            image = Image.open(file_path)
            text = ocr_handwritten(image)



        # ================= PDF =================
        elif ext == "pdf":
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception:
                text = ""

            if not text.strip():
                try:
                    images = convert_from_path(
                        file_path,
                        poppler_path=POPPLER_PATH,
                        dpi=300
                    )
                    for img in images:
                        text += pytesseract.image_to_string(img) + "\n"
                except Exception:
                    pass  # NEVER FAIL

        # ================= DOCX =================
        elif ext == "docx":
            doc = Document(file_path)

            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"

            if not text.strip():
                for rel_id in doc.part._rels:
                    rel = doc.part._rels[rel_id]
                    if rel.reltype == RT.IMAGE:
                        image = Image.open(BytesIO(rel.target_part.blob))
                        text += pytesseract.image_to_string(image) + "\n"

        # ================= TXT =================
        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

    except Exception as e:
        print("OCR ERROR:", e)

    # ✅ FINAL GUARANTEE (MOST IMPORTANT LINE)
    if not text or not text.strip():
        return "[OCR completed, but no readable text was detected]"

    return text.strip()



# =====================================================
# AUTH ROUTES
# =====================================================
@auth_router.post("/register")
def register(user: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Registration successful"}


@auth_router.post("/login")
def login(user: LoginSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(db_user.id)

    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": {
            "id": db_user.id,
            "name": db_user.full_name,
            "email": db_user.email,
        },
    }

# =====================================================
# CURRENT USER (USED BY DASHBOARD & ANALYTICS)
# =====================================================
@auth_router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.full_name,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }

@auth_router.put("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = ["image/jpeg", "image/png", "image/webp"]

    content_type = file.content_type or ""
    if not any(ct in content_type for ct in ["jpeg", "png", "webp"]):
        raise HTTPException(status_code=400, detail="Invalid image type")



    ext = file.filename.split(".")[-1]
    filename = f"user_{user.id}.{ext}"
    file_path = os.path.join(AVATAR_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    user.avatar_url = f"/uploads/avatars/{filename}"
    db.commit()

    return {
        "message": "Avatar updated successfully",
        "avatar": user.avatar_url,
    }


@auth_router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user)):
    return {"message": f"Welcome {user.full_name}"}


@auth_router.post("/logout")
def logout(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        revoke_token(token)

    return {"message": "Logged out successfully"}


from pydantic import BaseModel

class ChangePasswordSchema(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


@auth_router.put("/change-password")
def change_password(
    data: ChangePasswordSchema,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user.password_hash = hash_password(data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}



# =====================================================
# OCR ROUTES
# =====================================================
@auth_router.post("/ocr/upload")
async def upload_ocr(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_extensions = ["pdf", "png", "jpg", "jpeg", "docx", "txt"]
    ext = file.filename.rsplit(".", 1)[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")

    unique_filename = f"{uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)


    with open(file_path, "wb") as f:
        f.write(await file.read())

    extracted_text = perform_ocr(file_path, file.filename)

    record = OCRHistory(
        filename=file.filename,
        extracted_text=extracted_text,
        user_id=user.id,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record



def ocr_handwritten(image: Image.Image) -> str:
    image = image.convert("L")  # grayscale
    image = ImageEnhance.Contrast(image).enhance(2.0)

    return pytesseract.image_to_string(
        image,
        lang="eng",
        config="--psm 6"
    )


@auth_router.get("/ocr/history")
def get_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(OCRHistory)
        .filter(OCRHistory.user_id == user.id)
        .order_by(OCRHistory.id.desc())
        .all()
    )
@auth_router.get("/ocr/history/{record_id}")
def get_single_ocr_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(OCRHistory)
        .filter(
            OCRHistory.id == record_id,
            OCRHistory.user_id == user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="OCR record not found")

    return record



@auth_router.delete("/ocr/history/{record_id}")
def delete_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(OCRHistory)
        .filter(
            OCRHistory.id == record_id,
            OCRHistory.user_id == user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()

    return {"message": "Record deleted successfully"}


@auth_router.delete("/delete-account")
def delete_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = user.id

    # 🔥 DELETE AVATAR FILE
    if user.avatar_url:
        avatar_path = user.avatar_url.lstrip("/")
        if os.path.exists(avatar_path):
            os.remove(avatar_path)

    # 🔥 HARD DELETE USER (THIS IS CRITICAL)
    deleted = (
        db.query(User)
        .filter(User.id == user_id)
        .delete(synchronize_session=False)
    )

    # 🔥 REVOKE TOKENS
    from app.auth.utils import tokens
    for t in list(tokens.keys()):
        if tokens[t] == user_id:
            tokens.pop(t)

    db.commit()

    if deleted == 0:
        raise HTTPException(
            status_code=500,
            detail="User was NOT deleted from database",
        )

    return {"message": "Account permanently deleted"}



@auth_router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordSchema,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        return {"message": "If email exists, reset link sent"}

    token = str(uuid4())
    user.reset_token = token
    user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)

    db.commit()

    print("RESET TOKEN SAVED:", token)

    reset_link = f"{FRONTEND_URL}/reset-password/{token}"


    send_reminder_email(
        to=user.email,
        subject="Reset your password",
        text_body=f"Click the link to reset your password:\n{reset_link}",
    )

    return {"message": "Reset link sent"}

@auth_router.post("/reset-password/{token}")
def reset_password(
    token: str,
    data: ResetPasswordSchema,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    expiry = user.reset_token_expiry
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")

    user.password_hash = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()

    return {"message": "Password updated successfully"}
