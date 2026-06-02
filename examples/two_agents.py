"""Two agents, one knowledge base, under lane discipline and on the record.

Run it:

    python examples/two_agents.py

It builds a throwaway knowledge base in a temp directory, wires up two agents
from examples/agents.yaml, and walks through:

1. the scribe writing a raw log (inside its lane, allowed),
2. the curator promoting that into durable knowledge (inside its lane),
3. the curator recording a decision in append-only mode,
4. the scribe trying to edit curated knowledge (outside its lane, refused),

then prints the audit trail so you can see that every step, including the
refusal, was recorded. Nothing happened unseen.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from noaos import Agent, AuditLog, KnowledgeStore, LanePolicy, LaneViolation


def main() -> None:
    workdir = Path(tempfile.mkdtemp(prefix="noaos-demo-"))
    print(f"knowledge base: {workdir}\n")

    store = KnowledgeStore(workdir / "kb")
    audit = AuditLog(workdir / "audit.jsonl")

    config = yaml.safe_load((Path(__file__).parent / "agents.yaml").read_text())
    policy = LanePolicy.from_config(config)

    scribe = Agent("scribe", store, policy, audit)
    curator = Agent("curator", store, policy, audit)

    # 1. The scribe captures something raw. Inside its lane.
    scribe.remember(
        "logs/2026-06-02-onboarding-note",
        "New users were unsure where to find the onboarding checklist.",
        description="Raw note from a support call",
    )
    print("scribe wrote logs/2026-06-02-onboarding-note  (allowed)")

    # 2. The curator promotes it into durable, named knowledge.
    curator.remember(
        "knowledge/onboarding-checklist-gap",
        "Mobile password reset is broken. Workaround: reset on web, then sign "
        "in on mobile. Tracked for a real fix.",
        description="Known issue for onboarding checklist discovery",
    )
    print("curator wrote knowledge/onboarding-checklist-gap  (allowed)")

    # 3. The curator records the decision, append-only.
    curator.log_to(
        "decisions/log",
        "2026-06-02: treat the mobile reset gap as a known issue with a "
        "documented web workaround until the fix ships.",
    )
    print("curator appended to decisions/log  (allowed)")

    # 4. The scribe tries to edit curated knowledge. Outside its lane.
    try:
        scribe.remember(
            "knowledge/onboarding-checklist-gap",
            "scribe trying to overwrite the curated note",
        )
    except LaneViolation as violation:
        print(f"scribe blocked from knowledge/  (refused: {violation})")

    # The record. Every line, including the refusal.
    print("\naudit trail")
    print("-" * 60)
    for event in audit.events():
        mark = "ok " if event.allowed else "DENY"
        line = f"[{mark}] {event.agent:8} {event.action:7} {event.path}"
        if not event.allowed:
            line += f"\n        reason: {event.reason}"
        print(line)


if __name__ == "__main__":
    main()
