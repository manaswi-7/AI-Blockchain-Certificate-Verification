from io import BytesIO
from typing import Any
import re

from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import pytesseract
except ImportError:
    pytesseract = None

from model_loader import predict

app = FastAPI(title="Certificate AI Analysis Service", version="1.1.0")

FIELD_PATTERNS = {
    "certificate_id": r"(?:certificate\s*(?:id|no|number)|id)\s*[:#-]?\s*([A-Za-z0-9\-/]+)",
    "issue_date": r"(?:issue\s*date|date\s*of\s*issue)\s*[:#-]?\s*([A-Za-z0-9,\-/ ]+)",
}


def extract_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for name, pattern in FIELD_PATTERNS.items():
        match = re.search(pattern, text, re.I)
        if match:
            fields[name] = match.group(1).strip()
    return fields


def analyze_text(text: str) -> dict[str, Any]:
    fields = extract_fields(text)
    issues = []
    if not text.strip():
        issues.append("No readable text was extracted from the document.")
    if len(text.strip()) < 30:
        issues.append("Very little text was extracted; manual review is recommended.")
    if "certificate_id" not in fields:
        issues.append("Required field missing: certificate_id")
    return {"extracted_fields": fields, "ocr_issues": issues}


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    image = ImageOps.exif_transpose(image)
    max_width = 2400
    if image.width < max_width:
        scale = max_width / image.width
        image = image.resize((int(image.width * scale), int(image.height * scale)))
    gray = ImageOps.grayscale(image)
    gray = ImageEnhance.Contrast(gray).enhance(1.4)
    return gray.filter(ImageFilter.SHARPEN)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "A file is required")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 10 MB limit")
    try:
        image = Image.open(BytesIO(data))
        image.load()
        image = ImageOps.exif_transpose(image).convert("RGB")
    except Exception as exc:
        raise HTTPException(400, "Unsupported image document") from exc
    if pytesseract is None:
        raise HTTPException(503, "OCR engine is not installed")

    ocr_image = preprocess_for_ocr(image)
    text = pytesseract.image_to_string(ocr_image, config="--psm 6")
    ocr_result = analyze_text(text)
    model_result = predict(image)

    if model_result is None:
        ai_classification = "UNAVAILABLE"
        ai_confidence = None
        recommendation = "OCR completed. Train/deploy the tampering model before relying on visual AI analysis."
    else:
        ai_classification = model_result["classification"]
        ai_confidence = model_result["confidence"]
        recommendation = (
            "Potential visual tampering detected; continue with hash and blockchain verification."
            if ai_classification == "TAMPERED"
            else "No visual tampering detected by the model; continue with hash and blockchain verification."
        )

    return {
        "classification": ai_classification,
        "confidence": ai_confidence,
        "model_available": model_result is not None,
        "tamper_probability": None if model_result is None else model_result["tamper_probability"],
        "extracted_fields": ocr_result["extracted_fields"],
        "issues": ocr_result["ocr_issues"],
        "recommendation": recommendation,
    }
