from io import BytesIO
from typing import Any
import re

from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

app = FastAPI(title="Certificate AI Analysis Service", version="1.0.0")

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
    required = ["certificate_id"]
    missing = [f for f in required if f not in fields]
    if missing:
        issues.append("Required field missing: " + ", ".join(missing))
    confidence = 0.95 if text.strip() and not issues else 0.55
    classification = "GENUINE" if not issues else "SUSPICIOUS"
    return {
        "classification": classification,
        "confidence": confidence,
        "extracted_fields": fields,
        "issues": issues,
        "recommendation": "Proceed to cryptographic and blockchain verification; AI is advisory only." if not issues else "Manual review and cryptographic verification required."
    }

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
    except Exception as exc:
        raise HTTPException(400, "Unsupported image document") from exc
    if pytesseract is None:
        raise HTTPException(503, "OCR engine is not installed")
    text = pytesseract.image_to_string(image)
    return analyze_text(text)
