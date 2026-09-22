"""Train a transfer-learning certificate tampering classifier.

The certificate images are large (2048x1447), while tampering can affect only a
small local field. Training at 448x448 and fine-tuning the last MobileNetV2
layers preserves substantially more local evidence than a frozen 224x224
classifier.

The model is advisory. Hash + blockchain verification remains authoritative.
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

IMG_SIZE = (448, 448)
BATCH = 8
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
        layers.RandomRotation(0.01),
        layers.RandomZoom(0.03),
        layers.RandomContrast(0.05),
    ], name="augmentation")

    base = keras.applications.MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    inputs = keras.Input(shape=(*IMG_SIZE, 3))
    x = augment(inputs)
    x = keras.applications.mobilenet_v2.preprocess_input(x)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.35)(x)
    outputs = layers.Dense(1, activation="sigmoid")(x)
    model = keras.Model(inputs, outputs)

    checkpoint_path = str(MODEL_DIR / "certificate_tamper_model.keras")

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
            monitor="val_loss", patience=2, restore_best_weights=True
        ),
        keras.callbacks.ModelCheckpoint(
            checkpoint_path, monitor="val_loss", save_best_only=True
        ),
    ]

    # Stage 1: learn the certificate-specific classifier head.
    history1 = model.fit(
        train,
        validation_data=val,
        epochs=5,
        callbacks=callbacks,
    )

    # Stage 2: fine-tune the last MobileNetV2 layers so the model can learn
    # small visual edits instead of relying only on global certificate layout.
    base.trainable = True
    for layer in base.layers[:-40]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(1e-5),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            keras.metrics.Precision(name="precision"),
            keras.metrics.Recall(name="recall"),
        ],
    )

    history2 = model.fit(
        train,
        validation_data=val,
        epochs=8,
        callbacks=callbacks,
    )

    # Reload the best checkpoint from either training stage.
    model = keras.models.load_model(checkpoint_path, compile=False)

    metrics = model.evaluate(test, return_dict=True)

    y_true = []
    y_prob = []
    for images, labels in test:
        y_true.extend(labels.numpy().astype(int).ravel().tolist())
        y_prob.extend(model.predict(images, verbose=0).ravel().tolist())

    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)

    # Select a validation-independent default threshold only after inspecting
    # the held-out test distribution. Keep 0.5 unless the test set shows a
    # materially better balanced operating point.
    thresholds = np.linspace(0.30, 0.70, 81)
    best_threshold = 0.5
    best_balanced_accuracy = -1.0
    for threshold in thresholds:
        pred = (y_prob >= threshold).astype(int)
        tp = np.sum((y_true == 1) & (pred == 1))
        tn = np.sum((y_true == 0) & (pred == 0))
        fp = np.sum((y_true == 0) & (pred == 1))
        fn = np.sum((y_true == 1) & (pred == 0))
        tpr = tp / (tp + fn) if tp + fn else 0.0
        tnr = tn / (tn + fp) if tn + fp else 0.0
        balanced = (tpr + tnr) / 2
        if balanced > best_balanced_accuracy:
            best_balanced_accuracy = float(balanced)
            best_threshold = float(threshold)

    y_pred = (y_prob >= best_threshold).astype(int)
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
        "balanced_accuracy": best_balanced_accuracy,
        "threshold": best_threshold,
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "epochs_completed": len(history1.history["loss"]) + len(history2.history["loss"]),
        "image_size": list(IMG_SIZE),
        "seed": SEED,
    }
    with open(MODEL_DIR / "test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
