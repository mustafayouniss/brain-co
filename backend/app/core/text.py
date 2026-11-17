"""Text processing and normalization utilities."""

from __future__ import annotations

import re

# Arabic diacritics (tashkeel): fatha, damma, kasra, sukun, tanween, shadda, dagger alef
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670]")
# Alef variants: alef with hamza above/below, alef with madda -> plain alef
_ARABIC_ALEF_RE = re.compile(r"[إأآا]")


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for resilient lexical search.

    Transformations:
    - Strips tashkeel (vowel diacritics and shadda).
    - Normalizes alef variants (أ, إ, آ, ا) to plain bare alef (ا).
    - Normalizes taa marbuta (ة) to haa (ه).
    - Normalizes alif maqsura (ى) to yaa (ي).
    """
    if not text:
        return ""
    # Strip diacritics
    text = _ARABIC_DIACRITICS_RE.sub("", text)
    # Normalize alef variants
    text = _ARABIC_ALEF_RE.sub("ا", text)
    # Normalize taa marbuta
    text = text.replace("ة", "ه")
    # Normalize alif maqsura
    text = text.replace("ى", "ي")
    return text
