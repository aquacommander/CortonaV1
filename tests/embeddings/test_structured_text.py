from core.canonical_schema import CanonicalObject
from embeddings.structured_text import build_structured_embedding_text


def test_structured_embedding_text_uses_only_required_fields() -> None:
    obj = CanonicalObject(
        canonical_id="co_abc",
        source_system="apple_notes",
        source_record_type="note",
        title="Weekly Plan",
        content="Finish architecture draft.",
        people=["Sam@example.com", "sam@example.com", "Lee@example.com"],
        labels=["internal"],
        domain="Work",
    )

    text = build_structured_embedding_text(obj)
    assert "title: Weekly Plan" in text
    assert "content: Finish architecture draft." in text
    assert "people: Lee@example.com, Sam@example.com" in text
    assert "domain: Work" in text
    assert "internal" not in text
