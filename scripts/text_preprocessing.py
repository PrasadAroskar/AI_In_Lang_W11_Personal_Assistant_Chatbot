"""Text normalization shared by training and inference."""

import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


_lemmatizer = WordNetLemmatizer()
_stop_words = None


def _load_nltk_data() -> None:
    """Download the textbook's tokenizer, stopword, and WordNet resources once."""
    resources = {
        "tokenizers/punkt": "punkt",
        "tokenizers/punkt_tab": "punkt_tab",
        "corpora/stopwords": "stopwords",
        "corpora/wordnet": "wordnet",
    }
    for path, package in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(package, quiet=True)


def preprocess_text(text: str) -> str:
    """Lowercase, tokenize, remove punctuation/stopwords, and lemmatize text."""
    global _stop_words
    text = text.lower()
    try:
        _load_nltk_data()
        if _stop_words is None:
            _stop_words = set(stopwords.words("english"))
        tokens = nltk.word_tokenize(text)
        tokens = [word for word in tokens if word not in string.punctuation and word not in _stop_words]
        return " ".join(_lemmatizer.lemmatize(word) for word in tokens)
    except (LookupError, OSError):
        # Keep the local demo usable offline if NLTK's optional corpora are unavailable.
        return " ".join(re.findall(r"[a-z0-9]+", text))
