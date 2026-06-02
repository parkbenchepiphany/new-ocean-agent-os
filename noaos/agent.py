"""The agent: an identity that reads and writes under a lane, on the record.

This is the layer a developer actually uses. An :class:`Agent` ties together
the three pieces that are kept separate everywhere else:

* a shared :class:`~noaos.knowledge.KnowledgeStore` (the memory),
* a :class:`~noaos.lanes.LanePolicy` (who may write where),
* an :class:`~noaos.governance.AuditLog` (the record of what happened).

Every write goes through the same path: check the lane, record the decision,
then, only if allowed, touch the store. Reads are checked and recorded too, so
the trail answers not just "who changed this" but "who looked".
"""

from __future__ import annotations

from .governance import AuditLog
from .knowledge import KnowledgeStore, Note
from .lanes import LanePolicy, LaneViolation


class Agent:
    """A named worker bound to one store, one policy, and one audit log.

    Several agents typically share the same store, policy, and log. That
    sharing is the point: they are colleagues working a common knowledge base
    under a common set of rules, not isolated processes.
    """

    def __init__(
        self,
        name: str,
        store: KnowledgeStore,
        policy: LanePolicy,
        audit: AuditLog,
    ):
        self.name = name
        self.store = store
        self.policy = policy
        self.audit = audit

    def _guard(self, action: str, path: str) -> None:
        """Check the lane and record the decision. Raise if denied."""

        try:
            self.policy.check(self.name, path, action)
        except LaneViolation as violation:
            self.audit.record(
                self.name, action, path, allowed=False, reason=str(violation)
            )
            raise
        self.audit.record(self.name, action, path, allowed=True)

    def remember(self, name: str, body: str, **metadata) -> Note:
        """Write a new note, or overwrite an existing one. Needs a write lane."""

        self._guard("write", name)
        note = Note(name=name, body=body, metadata={"author": self.name, **metadata})
        self.store.write(note)
        return note

    def log_to(self, name: str, body: str) -> None:
        """Append to a note without rewriting its history. Needs append or write."""

        self._guard("append", name)
        self.store.append(name, body)

    def read(self, name: str) -> Note:
        """Read a note. Needs at least a read lane covering it."""

        self._guard("read", name)
        return self.store.read(name)

    def recall(self, query: str, limit: int = 10) -> list[Note]:
        """Recall across the whole store by keyword. Recall is not lane-scoped.

        Reading the index of what exists is allowed for any agent; the lanes
        govern writing and direct reads of specific notes. This mirrors how a
        real team works: everyone can see the shelf, not everyone can edit the
        books.
        """

        return self.store.recall(query, limit=limit)
