# Certificate dataset

This directory contains the reproducible synthetic dataset generator for the
certificate-verification project.

## What is fixed

The certificate is generated at exactly **2048 x 1447** using one fixed layout:
header, information box, QR block, photo block, marks table, SGPA/CGPA row,
barcode, seal and signature.

The generator does **not** write any class labels into the image.

There must be NO:
- ORIGINAL
- TAMPERED
- FAKE
- ALTERED
- MODIFIED
- red warning text
- arrows/circles/highlights that reveal the edited location

Those labels exist only outside the pixels through folder names, filenames and
metadata.

## Tampering

Each genuine certificate receives exactly one local manipulation in the paired
tampered image. Examples include:

- student-name replacement
- issue-date replacement
- certificate-ID replacement
- roll-number replacement
- marks replacement
- grade replacement
- subject replacement
- academic-year replacement
- QR-content replacement
- photo replacement

The edited content uses the normal document styling. The purpose is to make the
model learn document inconsistencies rather than a visible "tampered" marker.

## Generate

From this directory:

```bash
pip install -r requirements.txt
python generate_500_certificate_dataset.py --count 500
python split_dataset.py
python train_tamper_model.py
```

Output:

```
dataset/
  real/                 # 500 genuine PNGs
  tampered/             # 500 paired tampered PNGs
  metadata.csv
  split/
    train/real
    train/tampered
    validation/real
    validation/tampered
    test/real
    test/tampered
```

The split script groups each certificate ID together, so its genuine image and
tampered counterpart cannot leak into different splits.

The images are synthetic and are for model development/testing only.
