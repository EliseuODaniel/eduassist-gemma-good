from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_submission_evidence_pack_is_versioned() -> None:
    evidence = ROOT / "docs" / "submission" / "evidence" / "sample-outputs.md"

    text = evidence.read_text(encoding="utf-8")

    assert "Document Intake" in text
    assert "Authorized Student Support" in text
    assert "Privacy Guardrail" in text
    assert "181/181" in text


def test_media_gallery_assets_exist() -> None:
    assets = ROOT / "docs" / "submission" / "assets"
    notices = ROOT / "data" / "demo" / "notices"

    assert (assets / "eduassist-local-cover.svg").exists()
    assert (assets / "field-kit-architecture.svg").exists()
    assert (assets / "field-kit-storyboard.svg").exists()
    assert (notices / "enrollment-support-notice.png").exists()
    assert (ROOT / "docs" / "submission" / "media-gallery.md").exists()
