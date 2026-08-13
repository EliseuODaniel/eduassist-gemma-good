from eduassist_gemma_good.config import DATA_DIR
from eduassist_gemma_good.data_store import DemoDataStore
from eduassist_gemma_good.retrieval import expand_query_tokens


def test_public_retrieval_expands_portuguese_enrollment_terms() -> None:
    store = DemoDataStore(DATA_DIR)

    documents = store.search_public_with_metadata("matricula sem internet")

    assert documents[0]["source_id"] == "enrollment"
    assert documents[0]["rank"] == 1
    assert documents[0]["score"] > 0
    assert "enrollment" in documents[0]["matched_terms"]


def test_public_retrieval_finds_calendar_from_portuguese_recovery_question() -> None:
    store = DemoDataStore(DATA_DIR)

    documents = store.search_public_with_metadata("quando acontece a recuperacao?")

    assert documents[0]["source_id"] == "calendar-2026"
    assert "a" not in documents[0]["matched_terms"]


def test_public_retrieval_finds_health_document_from_atestado_query() -> None:
    store = DemoDataStore(DATA_DIR)

    documents = store.search_public_with_metadata("como enviar atestado medico?")

    assert documents[0]["source_id"] == "health-and-attendance"


def test_public_retrieval_metadata_is_exposed_in_tool_payload() -> None:
    store = DemoDataStore(DATA_DIR)

    document = store.search_public_with_metadata("plain-language explanations")[0]

    assert document["source_id"] == "accessibility-and-inclusion"
    assert set(document) >= {
        "access",
        "excerpt",
        "matched_terms",
        "rank",
        "score",
        "source_id",
        "title",
    }


def test_query_expansion_is_auditable_and_local() -> None:
    expanded = expand_query_tokens({"matricula"})

    assert {"documentos", "enrollment", "reenrollment"} <= expanded
