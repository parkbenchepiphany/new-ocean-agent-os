"""No black box: an append-only record of everything the agents do.

Governance is not a bolt-on. It is the part that makes the rest of it safe to
scale. The rule here is simple and absolute: every write attempt is recorded,
including the ones that were denied. If an agent tried to step outside its
lane, you can see that it tried. Nothing happens unseen.

The log is append-only JSON Lines. One event per line, easy to tail, easy to
grep, easy to ship somewhere else later. There is no update and no delete.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class AuditEvent:
    """One thing that happened, or was refused."""

    timestamp: str
    agent: str
    action: str
    path: str
    allowed: bool
    reason: str = ""


class AuditLog:
    """An append-only JSONL audit trail."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        agent: str,
        action: str,
        path: str,
        allowed: bool,
        reason: str = "",
    ) -> AuditEvent:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent=agent,
            action=action,
            path=path,
            allowed=allowed,
            reason=reason,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event)) + "\n")
        return event

    def events(self) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        events: list[AuditEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                events.append(AuditEvent(**json.loads(line)))
        return events

    def tail(self, n: int = 10) -> list[AuditEvent]:
        return self.events()[-n:]
