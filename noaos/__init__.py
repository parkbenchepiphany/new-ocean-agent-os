"""New Ocean Agent OS.

A small framework for running several AI agents against one shared knowledge
base, safely. Three ideas, kept deliberately separate:

* persistent memory   plain Markdown files with frontmatter (knowledge.py)
* lane discipline      who may write where, closed by default (lanes.py)
* no black box         an append-only record of every action (governance.py)

The :class:`Agent` in agent.py ties them together into the API you use.
"""

from .agent import Agent
from .governance import AuditEvent, AuditLog
from .knowledge import KnowledgeStore, Note
from .lanes import Lane, LanePolicy, LaneViolation

__all__ = [
    "Agent",
    "AuditEvent",
    "AuditLog",
    "KnowledgeStore",
    "Note",
    "Lane",
    "LanePolicy",
    "LaneViolation",
]

__version__ = "0.1.0"
