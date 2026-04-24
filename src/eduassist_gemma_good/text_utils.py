from __future__ import annotations

import re
import unicodedata

TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize_text(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(normalize_text(value)))


def compact_excerpt(text: str, query: str, *, max_chars: int = 420) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    query_tokens = tokens(query)
    words = cleaned.split()
    best_index = 0
    best_score = -1
    for index, word in enumerate(words):
        score = 1 if normalize_text(word).strip(".,:;!?") in query_tokens else 0
        if score > best_score:
            best_index = index
            best_score = score
    start = max(0, best_index - 25)
    excerpt = " ".join(words[start : start + 75])
    if start > 0:
        excerpt = "... " + excerpt
    if len(excerpt) > max_chars:
        excerpt = excerpt[: max_chars - 3].rstrip() + "..."
    return excerpt
