from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .retrieval import retrieve_public_documents
from .schema import Evidence
from .text_utils import tokens


@dataclass(frozen=True)
class PublicDocument:
    source_id: str
    title: str
    body: str


class DemoDataStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.public_documents = self._load_public_documents()
        self.students = self._load_students()

    def search_public(self, query: str, *, limit: int = 3) -> tuple[Evidence, ...]:
        return tuple(
            result.evidence
            for result in retrieve_public_documents(query, self.public_documents, limit=limit)
        )

    def search_public_with_metadata(self, query: str, *, limit: int = 3) -> tuple[dict, ...]:
        return tuple(
            result.payload(rank=index)
            for index, result in enumerate(
                retrieve_public_documents(query, self.public_documents, limit=limit),
                start=1,
            )
        )

    def get_student(self, student_id: str) -> dict:
        try:
            return self.students[student_id]
        except KeyError as exc:
            raise KeyError(f"Unknown synthetic student id: {student_id}") from exc

    def find_student_by_text(self, text: str) -> str | None:
        matched = self.find_students_by_text(text)
        return matched[0] if matched else None

    def find_students_by_text(self, text: str) -> tuple[str, ...]:
        text_tokens = tokens(text)
        matched: list[str] = []
        for student_id, student in self.students.items():
            name_tokens = tokens(student["name"])
            if name_tokens and name_tokens <= text_tokens:
                matched.append(student_id)
                continue
            first_name = student["name"].split()[0]
            if first_name.lower() in text_tokens:
                matched.append(student_id)
        return tuple(matched)

    def _load_public_documents(self) -> tuple[PublicDocument, ...]:
        public_dir = self.data_dir / "public"
        documents: list[PublicDocument] = []
        for path in sorted(public_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            title = path.stem.replace("-", " ").title()
            for line in text.splitlines():
                if line.startswith("# "):
                    title = line.removeprefix("# ").strip()
                    break
            documents.append(PublicDocument(path.stem, title, text))
        return tuple(documents)

    def _load_students(self) -> dict[str, dict]:
        path = self.data_dir / "protected" / "students.json"
        return json.loads(path.read_text(encoding="utf-8"))
