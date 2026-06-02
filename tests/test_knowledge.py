"""Tests for the knowledge store: round-trips, append, and recall."""

from noaos import KnowledgeStore, Note


def test_write_and_read_round_trip(tmp_path):
    store = KnowledgeStore(tmp_path)
    store.write(Note("greeting", "hello world", {"description": "a greeting"}))
    note = store.read("greeting")
    assert note.body == "hello world"
    assert note.description == "a greeting"


def test_plain_markdown_without_frontmatter_is_valid(tmp_path):
    store = KnowledgeStore(tmp_path)
    (tmp_path / "bare.md").write_text("just a body", encoding="utf-8")
    assert store.read("bare").body == "just a body"


def test_append_creates_then_extends(tmp_path):
    store = KnowledgeStore(tmp_path)
    store.append("log", "first entry")
    store.append("log", "second entry")
    body = store.read("log").body
    assert "first entry" in body
    assert "second entry" in body
    assert body.index("first entry") < body.index("second entry")


def test_names_includes_subfolders(tmp_path):
    store = KnowledgeStore(tmp_path)
    store.write(Note("logs/day-one", "x"))
    store.write(Note("knowledge/thing", "y"))
    assert store.names() == ["knowledge/thing", "logs/day-one"]


def test_recall_ranks_by_term_matches(tmp_path):
    store = KnowledgeStore(tmp_path)
    store.write(Note("a", "x", {"description": "onboarding checklist entry"}))
    store.write(Note("b", "y", {"description": "billing question"}))
    hits = store.recall("onboarding checklist")
    assert hits[0].name == "a"
    assert all(hit.name != "b" for hit in hits)
