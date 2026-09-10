"""Run the trained tampering model on one certificate image."""
from pathlib import Path
import argparse
import json
import tensorflow as tf
from PIL import Image
import numpy as np

MODEL = Path(__file__).resolve().parent / "models" / "certificate_tamper_model.keras"


def predict(image_path: str):
    if not MODEL.exists():
        raise SystemExit(f"Model not found: {MODEL}. Train it first.")
    model = tf.keras.models.load_model(MODEL)
    image = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.asarray(image, dtype=np.float32)[None, ...]
    probability = float(model.predict(arr, verbose=0)[0][0])
    # image_dataset_from_directory sorts labels alphabetically: real=0, tampered=1.
    classification = "TAMPERED" if probability >= 0.5 else "GENUINE"
    confidence = probability if classification == "TAMPERED" else 1 - probability
    return {"classification": classification, "confidence": round(confidence, 4), "tamper_probability": round(probability, 4)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    args = parser.parse_args()
    print(json.dumps(predict(args.image), indent=2))
