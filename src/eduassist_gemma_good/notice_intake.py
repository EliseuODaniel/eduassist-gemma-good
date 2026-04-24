from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from eduassist_gemma_good.action_outputs import ActionOutput

IMAGE_NOTICE_SUFFIXES = {".jpeg", ".jpg", ".png"}
SUPPORTED_NOTICE_SUFFIXES = {".md", ".txt", ".pdf", *IMAGE_NOTICE_SUFFIXES}

DATE_RE = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|"
    r"\d{1,2}\s+(?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)[a-z]*\.?\s+\d{4})\b",
    re.IGNORECASE,
)

DEADLINE_TERMS = (
    "before",
    "by ",
    "deadline",
    "due",
    "until",
    "ate ",
    "prazo",
    "entrega",
)

DOCUMENT_TERMS = (
    "birth certificate",
    "certificate",
    "proof of address",
    "address",
    "id",
    "notebook",
    "feedback sheet",
    "photo",
    "vaccination",
    "medical certificate",
    "document",
    "certidao",
    "comprovante",
    "identidade",
    "vacina",
    "atestado",
    "documento",
)

CONTACT_TERMS = (
    "office",
    "secretary",
    "support channel",
    "secretaria",
    "canal",
)


@dataclass(frozen=True)
class NoticeFacts:
    title: str
    source_name: str
    dates: tuple[str, ...]
    deadlines: tuple[str, ...]
    required_documents: tuple[str, ...]
    contacts: tuple[str, ...]
    actions: tuple[str, ...]
    extracted_text: str


def sample_notice_paths(data_dir: Path) -> tuple[Path, ...]:
    notice_dir = data_dir / "notices"
    if not notice_dir.exists():
        return ()
    return tuple(
        sorted(
            path
            for path in notice_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_NOTICE_SUFFIXES
        )
    )


def extract_notice_text(file_name: str, content: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(content)
    if suffix in {".md", ".txt"}:
        return content.decode("utf-8", errors="replace").strip()
    if suffix in IMAGE_NOTICE_SUFFIXES:
        return _extract_image_text(content)
    raise ValueError(f"Unsupported notice file type: {suffix or 'unknown'}")


def extract_notice_facts(text: str, source_name: str = "notice") -> NoticeFacts:
    cleaned = _clean_text(text)
    lines = tuple(line.strip(" -\t") for line in cleaned.splitlines() if line.strip())
    title = _notice_title(lines, source_name)
    dates = _unique(DATE_RE.findall(cleaned))
    deadlines = _matching_lines(lines, DEADLINE_TERMS)
    required_documents = _matching_lines(lines, DOCUMENT_TERMS, skip_headings=True)
    contacts = _matching_lines(lines, CONTACT_TERMS, skip_headings=True)
    actions = _build_actions(dates, deadlines, required_documents, contacts)
    return NoticeFacts(
        title=title,
        source_name=source_name,
        dates=dates,
        deadlines=deadlines,
        required_documents=required_documents,
        contacts=contacts,
        actions=actions,
        extracted_text=cleaned,
    )


def action_output_from_notice(facts: NoticeFacts) -> ActionOutput:
    checklist = facts.actions or (
        "Review the notice with the family.",
        "Confirm dates, required documents, and support channel with the school.",
    )
    date_hint = facts.dates[0] if facts.dates else "the next school deadline"
    message = (
        f"Hello, I need help with '{facts.title}'. "
        f"Can the school confirm the required steps before {date_hint}?"
    )
    return ActionOutput(
        title="Notice checklist output",
        checklist=checklist,
        plan=(),
        message=message,
        safety_note="Generated locally from the uploaded or selected school notice.",
    )


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    page_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(page_text).strip()


def _extract_image_text(content: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise ValueError(
            "Image OCR is optional and is not installed locally. "
            "Use PDF/TXT/MD for this demo path, or install local OCR support."
        ) from exc
    image = Image.open(BytesIO(content))
    return str(pytesseract.image_to_string(image)).strip()


def _clean_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").splitlines()).strip()


def _notice_title(lines: tuple[str, ...], source_name: str) -> str:
    if not lines:
        return Path(source_name).stem.replace("-", " ").title()
    first = lines[0].lstrip("#").strip()
    return first or Path(source_name).stem.replace("-", " ").title()


def _matching_lines(
    lines: tuple[str, ...],
    terms: tuple[str, ...],
    *,
    skip_headings: bool = False,
) -> tuple[str, ...]:
    matches: list[str] = []
    for line in lines:
        normalized = line.lower()
        if skip_headings and _looks_like_heading(normalized):
            continue
        if any(_has_term(normalized, term) for term in terms):
            matches.append(line)
    return _unique(matches)


def _has_term(normalized_line: str, term: str) -> bool:
    normalized_term = term.strip().lower()
    if len(normalized_term) <= 2:
        return re.search(rf"\b{re.escape(normalized_term)}\b", normalized_line) is not None
    return normalized_term in normalized_line


def _looks_like_heading(normalized_line: str) -> bool:
    stripped = normalized_line.strip().rstrip(":")
    return stripped in {
        "required documents",
        "required documents for office support",
        "documents",
        "documentos",
    }


def _build_actions(
    dates: tuple[str, ...],
    deadlines: tuple[str, ...],
    required_documents: tuple[str, ...],
    contacts: tuple[str, ...],
) -> tuple[str, ...]:
    actions: list[str] = []
    if deadlines:
        actions.append(f"Confirm the deadline: {deadlines[0]}")
    elif dates:
        actions.append(f"Write down the key date: {dates[0]}")
    if required_documents:
        actions.append(f"Collect required document: {required_documents[0]}")
    if contacts:
        actions.append(f"Use the listed school contact: {contacts[0]}")
    actions.append("Ask the school office for in-person support if internet access fails.")
    return tuple(actions)


def _unique(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        normalized = " ".join(str(value).split())
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        unique_values.append(normalized)
    return tuple(unique_values)
