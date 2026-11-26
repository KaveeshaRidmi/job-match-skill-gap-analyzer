"""Text cleaning and skill extraction."""
import re
import unicodedata
from functools import lru_cache

from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from skills_db import ALIASES, SKILL_TO_CATEGORY

_URL = re.compile(r"https?://\S+|www\.\S+")
_EMAIL = re.compile(r"\S+@\S+\.\S+")
_BULLETS = re.compile(r"[•●▪◦·■□▶►|]")


def clean_text(text: str) -> str:
    """Normalise unicode, drop URLs/emails/bullets, lowercase, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text or "")
    text = _URL.sub(" ", text)
    text = _EMAIL.sub(" ", text)
    text = _BULLETS.sub(" ", text)
    return re.sub(r"\s+", " ", text.lower()).strip()


_TOKENIZER = RegexpTokenizer(r"[a-z0-9]+")
_STEMMER = PorterStemmer()


@lru_cache(maxsize=None)
def _stem(token: str) -> str:
    return _STEMMER.stem(token)


def for_tfidf(text: str) -> str:
    """NLP pipeline (NLTK): tokenize -> remove stop-words -> Porter stemming.
    'developing', 'developed' and 'develops' all become 'develop'."""
    tokens = _TOKENIZER.tokenize(text)
    return " ".join(_stem(t) for t in tokens if t not in ENGLISH_STOP_WORDS and len(t) > 1)


def _pattern(term: str):
    # Boundaries that also behave for terms like c++, c#, node.js
    return re.compile(r"(?<![\w+#.])" + re.escape(term) + r"(?![\w+#])")


_TERMS = {s: s for s in SKILL_TO_CATEGORY}
_TERMS.update(ALIASES)
_PATTERNS = [(_pattern(t), canon) for t, canon in _TERMS.items()]


def extract_skills(clean: str) -> dict:
    """Return {skill: mention_count} for every known skill found in cleaned text."""
    found = {}
    for pat, canon in _PATTERNS:
        n = len(pat.findall(clean))
        if n:
            found[canon] = found.get(canon, 0) + n
    return found
