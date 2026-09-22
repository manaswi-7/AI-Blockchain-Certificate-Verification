"""Run the trained certificate-tampering model on one image."""
from pathlib import Path
import argparse
import json
import numpy as np
import tensorflow as tf
from PIL import Image

MODEL = Path(__file__).resolve().parent / "models" / "certificate_tamper_model.keras"


def predict(image_path: str):
    if not MODEL.exists():
        raise SystemExit(f"Model not found: {MODEL}. Train it first.")

    model = tf.keras.models.load_model(MODEL)
    image = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.asarray(image, dtype=np.float32)[None, ...]

    # Match the exact preprocessing used by train_tamper_model.py.
    arr = tf.keras.applications.mobilenet_v2.preprocess_input(arr)
    probability = float(model.predict(arr, verbose=0)[0][0])

    classification = "TAMPERED" if probability >= 0.5 else "GENUINE"
    confidence = probability if probability >= 0.5 else 1.0 - probability

    return {
        "classification": classification,
        "confidence": round(confidence, 4),
        "tamper_probability": round(probability, 4),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    args = parser.parse_args()
    print(json.dumps(predict(args.image), indent=2))
