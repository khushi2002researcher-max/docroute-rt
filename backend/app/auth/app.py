from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pytesseract
from PIL import Image
import os
from database import SessionLocal, engine
from models import Base, OCRHistory
from docx import Document

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

Base.metadata.create_all(bind=engine)

# OCR Upload API
@app.route("/api/ocr", methods=["POST"])
def ocr_upload():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    text = pytesseract.image_to_string(Image.open(path))

    db = SessionLocal()
    record = OCRHistory(filename=file.filename, extracted_text=text)
    db.add(record)
    db.commit()

    return jsonify({"text": text})

# Fetch OCR History
@app.route("/api/ocr/history", methods=["GET"])
def ocr_history():
    db = SessionLocal()
    records = db.query(OCRHistory).order_by(OCRHistory.id.desc()).all()

    return jsonify([
        {
            "id": r.id,
            "filename": r.filename,
            "text": r.extracted_text,
            "date": r.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for r in records
    ])

# Delete OCR Record
@app.route("/api/ocr/delete/<int:id>", methods=["DELETE"])
def delete_ocr(id):
    db = SessionLocal()
    record = db.query(OCRHistory).filter(OCRHistory.id == id).first()
    db.delete(record)
    db.commit()
    return jsonify({"message": "Deleted"})

# DOCX Download
@app.route("/api/ocr/docx", methods=["POST"])
def download_docx():
    text = request.json["text"]
    doc = Document()
    doc.add_paragraph(text)
    path = "ocr_result.docx"
    doc.save(path)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
