"""Lane discipline: which agent is allowed to write where.

The interesting problems in a multi-agent system do not start with what one
agent can do. They start when several agents write into the same knowledge
base. Without a rule, they overwrite each other, and you lose the thing that
made the shared store valuable in the first place: trust that what is written
is what was meant.

A lane is a declaration: "this agent may write to these paths, in this mode."
Everything not declared is denied. The default posture is closed, not open.

Three modes:

* ``write``       full read and write inside the matched paths.
* ``append``      may create new notes and append to existing ones, but may
                  not overwrite an existing note. Right for a decision log or
                  any append-only history.
* ``read``        may read but never write. Right for canon an agent should
                  consult but never edit.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from typing import Literal

Mode = Literal["write", "append", "read"]


class LaneViolation(Exception):
    """Raised when an agent attempts an action outside its declared lane."""


@dataclass(frozen=True)
class Lane:
    """One grant: an agent, a set of path patterns, and a mode."""

    agent: str
    patterns: tuple[str, ...]
    mode: Mode = "write"

    def matches(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pattern) for pattern in self.patterns)


class LanePolicy:
    """The full set of lanes across all agents.

    Closed by default: if no lane grants an action, it is denied. The policy
    only decides; it does not perform the write and it does not log. Recording
    the decision is governance's job, kept separate on purpose.
    """

    def __init__(self, lanes: list[Lane] | None = None):
        self.lanes: list[Lane] = list(lanes or [])

    @classmethod
    def from_config(cls, config: dict) -> "LanePolicy":
        """Build a policy from a plain dict (typically loaded from YAML).

        Expected shape::

            agents:
              scribe:
                - paths: ["logs/*"]
                  mode: write
              curator:
                - paths: ["knowledge/*"]
                  mode: write
                - paths: ["decisions/*"]
                  mode: append
        """

        lanes: list[Lane] = []
        for agent, grants in (config.get("agents") or {}).items():
            for grant in grants:
                patterns = tuple(grant.get("paths", []))
                mode: Mode = grant.get("mode", "write")
                lanes.append(Lane(agent=agent, patterns=patterns, mode=mode))
        return cls(lanes)

    def _lanes_for(self, agent: str) -> list[Lane]:
        return [lane for lane in self.lanes if lane.agent == agent]

    def permitted_mode(self, agent: str, path: str) -> Mode | None:
        """Return the most permissive mode this agent has for a path, or None.

        write is more permissive than append, which is more permissive than
        read. Returning None means no lane matched and the action is denied.
        """

        order: dict[Mode, int] = {"read": 0, "append": 1, "write": 2}
        best: Mode | None = None
        for lane in self._lanes_for(agent):
            if lane.matches(path):
                if best is None or order[lane.mode] > order[best]:
                    best = lane.mode
        return best

    def check(self, agent: str, path: str, action: Mode) -> None:
        """Raise :class:`LaneViolation` if the agent may not perform action.

        ``action`` is what the agent is trying to do. A ``write`` action needs
        a ``write`` lane. An ``append`` action is satisfied by either an
        ``append`` or a ``write`` lane. A ``read`` action is satisfied by any
        lane that matches.
        """

        granted = self.permitted_mode(agent, path)
        if granted is None:
            raise LaneViolation(
                f"{agent!r} has no lane covering {path!r}; denied by default"
            )

        order = {"read": 0, "append": 1, "write": 2}
        if order[granted] < order[action]:
            raise LaneViolation(
                f"{agent!r} may only {granted!r} at {path!r}, "
                f"but tried to {action!r}"
            )
