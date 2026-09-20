# Certificate dataset

The project uses a reproducible synthetic dataset generator.

It creates exactly:
- 500 genuine certificates
- 500 tampered copies, one derived from each genuine certificate
- 500 unique certificate IDs and student records
- metadata.csv mapping each genuine image to its tampered image and tamper type

Tamper classes include name, date, certificate ID, roll number, marks, grade, signature, QR code, seal, photo, course/subject, and academic year.

## Generate

```bash
pip install Pillow qrcode[pil]
python generate_500_certificate_dataset.py
```

Output:

```
dataset/certificates/
  real/       # 500 original images
  tampered/   # 500 tampered images
  metadata.csv
```

These are synthetic documents for model development/testing only.

The PNG binaries are intentionally generated rather than committed to Git history; this keeps the repository usable while making the dataset exactly reproducible from the committed Python generator.
