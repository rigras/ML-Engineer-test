"""Person-name normalization shared by matching and evaluation (TRD ADR-005)."""

import unicodedata

HONORIFICS = frozenset({"dr", "prof", "mr", "mrs", "ms"})


def normalize_name(name: str) -> str:
    """Fold case/accents/punctuation and drop leading honorifics: ``Dr. María`` → ``maria``."""
    decomposed = unicodedata.normalize("NFKD", name.casefold())
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    spaced = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in without_marks)
    tokens = spaced.split()
    while tokens and tokens[0] in HONORIFICS:
        tokens.pop(0)
    return " ".join(tokens)
