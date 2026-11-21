"""Evaluate intent classification and chatbot response latency."""

import time

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from scripts.chatbot_interface import chatbot_response
from scripts.nlp_engine import build_model, load_training_data
from scripts.text_preprocessing import preprocess_text


def evaluate_intent_model(epochs: int = 100) -> str:
    """Train on a training split and print per-intent precision/recall/F1."""
    patterns, tags = load_training_data()
    patterns = [preprocess_text(pattern) for pattern in patterns]
    encoder = LabelEncoder()
    labels = encoder.fit_transform(tags)
    counts = np.bincount(labels)
    if counts.min() < 2:
        raise ValueError("Each intent needs at least two patterns for a stratified evaluation split.")

    train_text, test_text, y_train, y_test = train_test_split(
        patterns, labels, test_size=0.2, random_state=42, stratify=labels
    )
    vectorizer = TfidfVectorizer()
    x_train = vectorizer.fit_transform(train_text).toarray()
    x_test = vectorizer.transform(test_text).toarray()
    model = build_model(x_train.shape[1], len(encoder.classes_))
    model.fit(x_train, y_train, epochs=epochs, batch_size=8, verbose=0)
    predicted = np.argmax(model.predict(x_test, verbose=0), axis=1)
    report = classification_report(
        y_test,
        predicted,
        labels=np.arange(len(encoder.classes_)),
        target_names=encoder.classes_,
        zero_division=0,
    )
    print(report)
    return report


def measure_response_time(user_input: str) -> float:
    """Measure elapsed seconds for a single chatbot response."""
    started = time.perf_counter()
    chatbot_response(user_input)
    return time.perf_counter() - started


def report_response_times() -> None:
    """Print latency for representative local prompts."""
    prompts = ["Hello", "Show my reminders", "Tell me a fun fact", "What's the weather like?"]
    for prompt in prompts:
        elapsed = measure_response_time(prompt)
        print(f"{prompt!r}: {elapsed:.4f} seconds")


if __name__ == "__main__":
    print("Intent classification report:")
    evaluate_intent_model()
    print("Response time samples:")
    report_response_times()
