"""Optional runtime loader for the trained certificate tampering model."""
from pathlib import Path
import numpy as np
from PIL import Image

MODEL_PATH = Path(__file__).resolve().parent / "models" / "certificate_tamper_model.keras"
_model = None


def load_model():
    global _model
    if _model is not None:
        return _model
    if not MODEL_PATH.exists():
        return None
    import tensorflow as tf
    _model = tf.keras.models.load_model(MODEL_PATH)
    return _model


def predict(image: Image.Image):
    model = load_model()
    if model is None:
        return None
    arr = np.asarray(image.convert("RGB").resize((224, 224)), dtype=np.float32)[None, ...]
    probability = float(model.predict(arr, verbose=0)[0][0])
    classification = "TAMPERED" if probability >= 0.5 else "GENUINE"
    confidence = probability if classification == "TAMPERED" else 1.0 - probability
    return {
        "classification": classification,
        "confidence": round(confidence, 4),
        "tamper_probability": round(probability, 4),
    }
