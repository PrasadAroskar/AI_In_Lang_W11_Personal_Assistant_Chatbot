"""Train and use the TensorFlow intent classifier."""

import json
import pickle
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.models import Sequential, load_model


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTENTS_PATH = PROJECT_ROOT / "data" / "intents.json"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "nlp_model.h5"
VECTORIZER_PATH = MODEL_DIR / "tokenizer.pickle"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.pickle"


def load_training_data(path: Path = INTENTS_PATH):
    """Read intent patterns and labels from the project's intents JSON."""
    with path.open(encoding="utf-8") as file:
        intent_data = json.load(file)

    patterns, tags = [], []
    for intent in intent_data.get("intents", []):
        if not isinstance(intent, dict):
            continue
        tag = intent.get("tag")
        if not tag:
            continue
        for pattern in intent.get("patterns", []) or []:
            if isinstance(pattern, str) and pattern.strip():
                patterns.append(pattern.strip())
                tags.append(str(tag).strip())

    if not patterns:
        raise ValueError(f"No training patterns found in {path}.")
    if len(set(tags)) < 2:
        raise ValueError("At least two distinct intent tags are required to train.")
    return patterns, tags


def build_model(input_size: int, class_count: int) -> Sequential:
    """Create the feed-forward intent classification network."""
    model = Sequential(
        [
            tf.keras.Input(shape=(input_size,)),
            Dense(128, activation="relu"),
            Dropout(0.5),
            Dense(64, activation="relu"),
            Dropout(0.5),
            Dense(class_count, activation="softmax"),
        ]
    )
    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    return model


def train_model(epochs: int = 100, batch_size: int = 8):
    """Train the classifier and save its model, vectorizer, and label encoder."""
    patterns, tags = load_training_data()
    label_encoder = LabelEncoder()
    labels = label_encoder.fit_transform(tags)
    vectorizer = TfidfVectorizer()
    features = vectorizer.fit_transform(patterns).toarray()
    # TF-IDF is normally finite, but sanitize the feature matrix before training
    # so missing or invalid numeric values cannot reach the network.
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    # The starter corpus is too small for a reliable holdout, so use all rows.
    class_counts = np.bincount(labels)
    can_hold_out = len(patterns) >= 10 and class_counts.min() >= 2
    if can_hold_out:
        x_train, x_validation, y_train, y_validation = train_test_split(
            features, labels, test_size=0.2, random_state=42, stratify=labels
        )
        validation_data = (x_validation, y_validation)
    else:
        x_train, y_train = features, labels
        validation_data = None

    # SMOTE requires at least two examples per class in the training partition.
    # Adjust k_neighbors for small classes and leave already balanced data alone.
    train_counts = np.bincount(y_train)
    present_counts = train_counts[train_counts > 0]
    if len(present_counts) > 1 and present_counts.min() >= 2 and present_counts.min() != present_counts.max():
        smote = SMOTE(random_state=42, k_neighbors=min(5, int(present_counts.min()) - 1))
        x_train, y_train = smote.fit_resample(x_train, y_train)

    model = build_model(features.shape[1], len(label_encoder.classes_))
    model.fit(
        x_train,
        y_train,
        epochs=epochs,
        batch_size=batch_size,
        verbose=1,
        validation_data=validation_data,
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)
    with VECTORIZER_PATH.open("wb") as file:
        pickle.dump(vectorizer, file)
    with LABEL_ENCODER_PATH.open("wb") as file:
        pickle.dump(label_encoder, file)
    return model


def predict_intent(text: str) -> dict:
    """Return the predicted intent tag and confidence for a message."""
    if not MODEL_PATH.exists() or not VECTORIZER_PATH.exists() or not LABEL_ENCODER_PATH.exists():
        raise FileNotFoundError("Model artifacts are missing. Run `python -m scripts.nlp_engine` first.")

    with VECTORIZER_PATH.open("rb") as file:
        vectorizer = pickle.load(file)
    with LABEL_ENCODER_PATH.open("rb") as file:
        label_encoder = pickle.load(file)
    model = load_model(MODEL_PATH)
    features = vectorizer.transform([text]).toarray()
    probabilities = model.predict(features, verbose=0)[0]
    index = int(np.argmax(probabilities))
    return {
        "tag": str(label_encoder.inverse_transform([index])[0]),
        "confidence": float(probabilities[index]),
    }


if __name__ == "__main__":
    train_model()
