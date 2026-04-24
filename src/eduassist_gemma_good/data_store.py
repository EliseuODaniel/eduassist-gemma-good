from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .schema import Evidence
from .text_utils import compact_excerpt, tokens


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
        query_tokens = tokens(query)
        scored: list[tuple[int, PublicDocument]] = []
        for doc in self.public_documents:
            doc_tokens = tokens(f"{doc.title} {doc.body}")
            score = len(query_tokens & doc_tokens)
            if score:
                scored.append((score, doc))
        if not scored:
            scored = [(0, doc) for doc in self.public_documents[:limit]]
        scored.sort(key=lambda item: (item[0], item[1].title), reverse=True)
        return tuple(
            Evidence(
                source_id=doc.source_id,
                title=doc.title,
                excerpt=compact_excerpt(doc.body, query),
                access="public",
            )
            for _, doc in scored[:limit]
        )

    def get_student(self, student_id: str) -> dict:
        try:
            return self.students[student_id]
        except KeyError as exc:
            raise KeyError(f"Unknown synthetic student id: {student_id}") from exc

    def find_student_by_text(self, text: str) -> str | None:
        text_tokens = tokens(text)
        for student_id, student in self.students.items():
            name_tokens = tokens(student["name"])
            if name_tokens and name_tokens <= text_tokens:
                return student_id
            first_name = student["name"].split()[0]
            if first_name.lower() in text_tokens:
                return student_id
        return None

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
