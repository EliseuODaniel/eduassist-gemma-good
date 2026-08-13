from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from .schema import Evidence
from .text_utils import compact_excerpt, normalize_text, tokens

SYNONYM_GROUPS = (
    frozenset(
        {
            "enrollment",
            "reenrollment",
            "matricula",
            "rematricula",
            "document",
            "documents",
            "documento",
            "documentos",
        }
    ),
    frozenset({"office", "secretary", "secretaria", "desk", "kiosk", "presencial"}),
    frozenset(
        {
            "internet",
            "connectivity",
            "conectividade",
            "offline",
            "access",
            "acesso",
            "kiosk",
        }
    ),
    frozenset(
        {
            "recovery",
            "recover",
            "recuperacao",
            "recuperar",
            "exam",
            "prova",
            "calendar",
            "calendario",
            "reuniao",
        }
    ),
    frozenset(
        {
            "health",
            "medical",
            "certificate",
            "atestado",
            "saude",
            "attendance",
            "frequencia",
        }
    ),
    frozenset({"portal", "family", "familia", "guardian", "responsavel", "visitor", "public"}),
    frozenset({"plain", "language", "simple", "explicacao", "explicacoes", "clara", "simples"}),
)
RETRIEVAL_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "como",
    "da",
    "de",
    "do",
    "e",
    "for",
    "how",
    "is",
    "o",
    "of",
    "para",
    "the",
    "to",
    "what",
    "when",
    "where",
}


class PublicSearchDocument(Protocol):
    source_id: str
    title: str
    body: str


@dataclass(frozen=True)
class RetrievedDocument:
    evidence: Evidence
    score: float
    matched_terms: tuple[str, ...]

    def payload(self, rank: int) -> dict:
        return {
            **self.evidence.__dict__,
            "rank": rank,
            "score": round(self.score, 3),
            "matched_terms": list(self.matched_terms),
        }


def retrieve_public_documents(
    query: str,
    documents: tuple[PublicSearchDocument, ...],
    *,
    limit: int = 3,
) -> tuple[RetrievedDocument, ...]:
    if not documents:
        return ()
    query_terms = expand_query_tokens(tokens(query) - RETRIEVAL_STOPWORDS)
    document_count = len(documents)
    document_frequency = _document_frequency(documents, query_terms)
    scored = [
        _score_document(query, query_terms, document, document_frequency, document_count)
        for document in documents
    ]
    matches = [item for item in scored if item.score > 0]
    if not matches:
        matches = [
            RetrievedDocument(
                evidence=Evidence(
                    source_id=document.source_id,
                    title=document.title,
                    excerpt=compact_excerpt(document.body, query),
                    access="public",
                ),
                score=0,
                matched_terms=(),
            )
            for document in documents[:limit]
        ]
    matches.sort(key=lambda item: (-item.score, item.evidence.title))
    return tuple(matches[:limit])


def expand_query_tokens(query_tokens: set[str]) -> set[str]:
    expanded = set(query_tokens)
    for group in SYNONYM_GROUPS:
        if expanded & group:
            expanded.update(group)
    return expanded


def _score_document(
    query: str,
    query_terms: set[str],
    document: PublicSearchDocument,
    document_frequency: dict[str, int],
    document_count: int,
) -> RetrievedDocument:
    title_terms = tokens(document.title)
    body_terms = tokens(document.body)
    all_terms = title_terms | body_terms
    matched_terms = tuple(sorted(query_terms & all_terms))
    score = 0.0
    document_count = max(1, document_count)
    for term in matched_terms:
        idf = math.log((1 + document_count) / (1 + document_frequency.get(term, 0))) + 1
        title_weight = 2.5 if term in title_terms else 0.0
        body_weight = 1.0 if term in body_terms else 0.0
        score += idf * (title_weight + body_weight)
    score += _phrase_bonus(query, document)
    return RetrievedDocument(
        evidence=Evidence(
            source_id=document.source_id,
            title=document.title,
            excerpt=compact_excerpt(document.body, query),
            access="public",
        ),
        score=score,
        matched_terms=matched_terms,
    )


def _document_frequency(
    documents: tuple[PublicSearchDocument, ...],
    query_terms: set[str],
) -> dict[str, int]:
    frequency = dict.fromkeys(query_terms, 0)
    for document in documents:
        document_terms = tokens(f"{document.title} {document.body}")
        for term in query_terms & document_terms:
            frequency[term] += 1
    return frequency


def _phrase_bonus(query: str, document: PublicSearchDocument) -> float:
    normalized_query = normalize_text(query)
    normalized_document = normalize_text(f"{document.title}\n{document.body}")
    bonus = 0.0
    for phrase in _significant_phrases(normalized_query):
        if phrase in normalized_document:
            bonus += 2.0
    return bonus


def _significant_phrases(normalized_query: str) -> tuple[str, ...]:
    words = normalized_query.split()
    phrases: list[str] = []
    for size in (3, 2):
        for index in range(len(words) - size + 1):
            phrase = " ".join(words[index : index + size])
            if len(phrase) >= 12:
                phrases.append(phrase)
    return tuple(phrases)
