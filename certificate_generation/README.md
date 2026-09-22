# Certificate dataset

The project uses a reproducible synthetic certificate dataset generator.

It creates:
- 500 genuine certificate images
- 500 tampered variants
- 500 unique certificate IDs and student records
- metadata.csv mapping each genuine image to its tampered image and tamper type

## Dataset integrity rules

The certificate **template/layout is fixed**. The images themselves never contain
class labels such as `ORIGINAL`, `TAMPERED`, `FAKE`, `ALTERED`, or
`MODIFIED`.

Tampered certificates use plausible local edits such as:
- student-name replacement
- issue-date replacement
- certificate-ID replacement
- roll-number replacement
- marks/grade changes
- subject replacement
- signature variation
- QR replacement
- seal variation
- photo replacement
- academic-year replacement

For text edits, the replacement is rendered with the same field position,
font family/size, alignment and normal document color rather than using a
warning color. Dataset labels exist only in folders, filenames and metadata.

## Generate

```bash
pip install Pillow qrcode[pil]
python generate_500_certificate_dataset.py
```

Output:

```
dataset/certificates/
  real/       # genuine images; no class text inside images
  tampered/   # tampered images; no class text inside images
  metadata.csv
```

These are synthetic documents for model development/testing only.

The PNG binaries are intentionally generated rather than committed to Git
history; this keeps the repository usable while making the dataset exactly
reproducible from the committed generator.
