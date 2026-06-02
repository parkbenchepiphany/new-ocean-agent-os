"""Persistent, file-based knowledge store.

The store is a directory of Markdown files, each carrying a small block of
YAML frontmatter. This is deliberately boring: the knowledge lives in plain
files you can open, diff, and read without the framework. The point of the
system is not the agents. The point is that canonical knowledge stops walking
out of the building when an agent, or a person, goes away.

A note looks like this on disk:

    ---
    name: onboarding-runbook
    description: How a new hire gets access on day one
    author: curator
    ---

    The body of the note, in Markdown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml


@dataclass
class Note:
    """A single unit of knowledge: one file, one fact."""

    name: str
    body: str
    metadata: dict = field(default_factory=dict)

    @property
    def description(self) -> str:
        return str(self.metadata.get("description", ""))


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Split a Markdown file into (metadata, body).

    Returns an empty metadata dict if the file has no frontmatter block, so a
    plain Markdown file is still a valid note.
    """

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, parts[2].lstrip("\n")


def _render(note: Note) -> str:
    """Render a note back to frontmatter + body for writing to disk."""

    metadata = dict(note.metadata)
    metadata.setdefault("name", note.name)
    front = yaml.safe_dump(metadata, sort_keys=False).strip()
    return f"---\n{front}\n---\n\n{note.body.rstrip()}\n"


class KnowledgeStore:
    """A directory of Markdown notes with frontmatter.

    The store knows how to read and write notes by name and to recall notes by
    a simple keyword match over their name and description. It does not enforce
    who is allowed to write where; that is the job of the lane policy, applied
    one level up in :class:`noaos.agent.Agent`. Keeping the two separate is the
    whole design: storage is dumb and honest, governance is explicit.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, name: str) -> Path:
        """Resolve a note name (which may contain subfolders) to a file path."""

        return self.root / f"{name}.md"

    def exists(self, name: str) -> bool:
        return self.path_for(name).exists()

    def read(self, name: str) -> Note:
        path = self.path_for(name)
        if not path.exists():
            raise KeyError(f"no note named {name!r}")
        metadata, body = _split_frontmatter(path.read_text(encoding="utf-8"))
        # rstrip the trailing newline that rendering adds, so a write/read
        # round-trip returns exactly the body that went in.
        return Note(name=name, body=body.rstrip("\n"), metadata=metadata)

    def write(self, note: Note) -> Path:
        path = self.path_for(note.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render(note), encoding="utf-8")
        return path

    def append(self, name: str, body: str) -> Path:
        """Append to an existing note, or create it if it does not exist.

        Used for append-only lanes such as a decision log, where history is
        sacred and prior entries are never rewritten.
        """

        if self.exists(name):
            note = self.read(name)
            note.body = f"{note.body.rstrip()}\n\n{body.strip()}"
        else:
            note = Note(name=name, body=body.strip())
        return self.write(note)

    def names(self) -> list[str]:
        return sorted(
            str(p.relative_to(self.root).with_suffix("")).replace("\\", "/")
            for p in self.root.rglob("*.md")
        )

    def all_notes(self) -> Iterable[Note]:
        for name in self.names():
            yield self.read(name)

    def recall(self, query: str, limit: int = 10) -> list[Note]:
        """Return notes whose name or description matches the query terms.

        This is a small, transparent keyword search, not a vector index. It is
        the right altitude for a v1: easy to reason about, no hidden ranking,
        no embedding model to trust. A semantic recall backend is a clean
        extension point, not a v1 blocker.
        """

        terms = [t.lower() for t in query.split() if t]
        scored: list[tuple[int, Note]] = []
        for note in self.all_notes():
            haystack = f"{note.name} {note.description}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, note))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [note for _, note in scored[:limit]]
