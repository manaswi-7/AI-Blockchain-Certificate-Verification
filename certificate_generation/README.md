# Certificate AI dataset pipeline

This folder contains the synthetic-data and model-training pipeline for the certificate tampering component.

## Pipeline

```text
Generate genuine certificates
        ↓
Generate tampered variants
        ↓
Leakage-safe train/validation/test split
        ↓
MobileNetV2 transfer learning
        ↓
Evaluate on held-out test data
        ↓
Export Keras model + metrics
```

## Local setup

```bash
cd certificate_generation
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

For model training, install TensorFlow separately if it is not available in your environment:

```bash
pip install tensorflow
```

## Generate data

```bash
python generate_certificates.py --count 200
python generate_tampered.py
python split_dataset.py
```

The split script keeps all variants of the same source certificate in one split to reduce data leakage.

## Train

```bash
python train_tamper_model.py
```

Outputs:

- `models/certificate_tamper_model.keras`
- `models/test_metrics.json`

Do not report accuracy/precision/recall until the model has actually been trained and evaluated. The current AI service remains advisory until this trained model is integrated into the FastAPI service.
