"""Train a transfer-learning certificate tampering classifier.

Expected dataset layout:
  dataset/split/train/{real,tampered}
  dataset/split/validation/{real,tampered}
  dataset/split/test/{real,tampered}

Outputs the trained Keras model and evaluation metrics. Blockchain/hash
verification remains authoritative; the model is advisory.
"""

from pathlib import Path
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset" / "split"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)

IMG_SIZE = (224, 224)
BATCH = 16
SEED = 42


def load(path: Path, shuffle: bool):
    return keras.utils.image_dataset_from_directory(
        path,
        labels="inferred",
        label_mode="binary",
        image_size=IMG_SIZE,
        batch_size=BATCH,
        shuffle=shuffle,
        seed=SEED,
    )


def main():
    tf.keras.utils.set_random_seed(SEED)

    train = load(DATA / "train", True)
    val = load(DATA / "validation", False)
    test = load(DATA / "test", False)

    class_names = train.class_names
    if class_names != ["real", "tampered"]:
        raise ValueError(f"Unexpected class order: {class_names}")

    autotune = tf.data.AUTOTUNE
    train = train.prefetch(autotune)
    val = val.prefetch(autotune)
    test = test.prefetch(autotune)

    augment = keras.Sequential([
        layers.RandomRotation(0.02),
        layers.RandomZoom(0.05),
        layers.RandomContrast(0.08),
    ], name="augmentation")

    base = keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False

    inputs = keras.Input(shape=(*IMG_SIZE, 3))
    x = augment(inputs)
    x = keras.applications.mobilenet_v2.preprocess_input(x)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)
    model = keras.Model(inputs, outputs)

    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
        ],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=3, restore_best_weights=True
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_DIR / "certificate_tamper_model.keras",
            monitor="val_loss",
            save_best_only=True,
        ),
    ]
    history = model.fit(train, validation_data=val, epochs=12, callbacks=callbacks)

    metrics = model.evaluate(test, return_dict=True)

    y_true = []
    y_prob = []
    for images, labels in test:
        y_true.extend(labels.numpy().astype(int).ravel().tolist())
        y_prob.extend(model.predict(images, verbose=0).ravel().tolist())

    y_true = np.asarray(y_true, dtype=int)
    y_pred = (np.asarray(y_prob) >= 0.5).astype(int)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    report = {
        "class_names": class_names,
        "test_metrics": {k: float(v) for k, v in metrics.items()},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "epochs_completed": len(history.history["loss"]),
        "image_size": list(IMG_SIZE),
        "seed": SEED,
    }
    with open(MODEL_DIR / "test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
