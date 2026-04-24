from eduassist_gemma_good.config import DATA_DIR
from eduassist_gemma_good.notice_intake import (
    action_output_from_notice,
    extract_notice_facts,
    extract_notice_text,
    sample_notice_paths,
)


def test_sample_notice_produces_family_action_output() -> None:
    sample = DATA_DIR / "notices" / "recovery-exam-notice.md"

    text = extract_notice_text(sample.name, sample.read_bytes())
    facts = extract_notice_facts(text, sample.name)
    output = action_output_from_notice(facts)

    assert facts.title == "Recovery Exam and Family Support Notice"
    assert "August 12, 2026" in facts.dates
    assert facts.required_documents
    assert output.title == "Notice checklist output"
    assert "Recovery Exam and Family Support Notice" in output.message


def test_enrollment_notice_keeps_deadlines_and_documents_separate() -> None:
    sample = DATA_DIR / "notices" / "enrollment-support-notice.md"

    text = extract_notice_text(sample.name, sample.read_bytes())
    facts = extract_notice_facts(text, sample.name)

    assert facts.deadlines == ("The deadline to submit enrollment documents is February 2, 2026.",)
    assert "Birth certificate or student ID." in facts.required_documents
    assert "The deadline to submit enrollment documents is February 2, 2026." not in (
        facts.required_documents
    )


def test_sample_notice_paths_only_returns_supported_files() -> None:
    paths = sample_notice_paths(DATA_DIR)

    assert {path.name for path in paths} == {
        "enrollment-support-notice.md",
        "recovery-exam-notice.md",
    }


def test_pdf_notice_text_extraction() -> None:
    pdf = _minimal_pdf(("Recovery Exam Notice", "Deadline August 8, 2026"))

    text = extract_notice_text("notice.pdf", pdf)

    assert "Recovery Exam Notice" in text
    assert "August 8, 2026" in text


def test_rejects_unsupported_notice_type() -> None:
    try:
        extract_notice_text("notice.docx", b"")
    except ValueError as exc:
        assert "Unsupported notice file type" in str(exc)
    else:
        raise AssertionError("Expected unsupported notice type to raise ValueError")


def _minimal_pdf(lines: tuple[str, ...]) -> bytes:
    text_ops = []
    for index, line in enumerate(lines):
        y = 720 - (index * 24)
        text_ops.append(f"BT /F1 12 Tf 72 {y} Td ({line}) Tj ET")
    stream = "\n".join(text_ops).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(output)
