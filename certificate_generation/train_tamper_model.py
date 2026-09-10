"""Train a transfer-learning certificate tampering classifier.

Expected dataset layout:
  dataset/split/train/{real,tampered}
  dataset/split/validation/{real,tampered}
  dataset/split/test/{real,tampered}

Outputs the trained Keras model and evaluation metrics. This is a research
prototype classifier; blockchain/hash verification remains authoritative.
"""

from pathlib import Path
import json
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
        path, labels="inferred", label_mode="binary", image_size=IMG_SIZE,
        batch_size=BATCH, shuffle=shuffle, seed=SEED,
    )


def main():
    train = load(DATA / "train", True)
    val = load(DATA / "validation", False)
    test = load(DATA / "test", False)

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
        metrics=["accuracy", keras.metrics.Precision(name="precision"), keras.metrics.Recall(name="recall")],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        keras.callbacks.ModelCheckpoint(MODEL_DIR / "certificate_tamper_model.keras", monitor="val_loss", save_best_only=True),
    ]
    model.fit(train, validation_data=val, epochs=12, callbacks=callbacks)

    metrics = model.evaluate(test, return_dict=True)
    with open(MODEL_DIR / "test_metrics.json", "w", encoding="utf-8") as f:
        json.dump({k: float(v) for k, v in metrics.items()}, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
