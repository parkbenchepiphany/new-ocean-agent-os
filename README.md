# New Ocean Agent OS

A small framework for running several AI agents against one shared knowledge base, safely.

Most discussions of AI agents focus on what one agent can do. The interesting problems start when you have several of them writing into the same knowledge base. Without a rule, they overwrite each other's work, and you lose the one thing that made a shared store worth building: trust that what is written is what was meant.

This is the working version of an idea I have been running in production for a while, generalised so anyone can pick it up. It rests on three decisions, kept deliberately separate.

## The three decisions

**Persistent memory.** Knowledge lives in plain Markdown files with a little YAML frontmatter. You can open it, diff it, and read it without the framework. The point of the system is not the agents. The point is that canonical knowledge stops walking out of the building when an agent, or a person, goes away.

**Lane discipline.** Each agent declares which paths it may write to, and in what mode. Everything not declared is denied. The default posture is closed, not open. A scribe that ingests raw material cannot reach in and rewrite curated knowledge, because it was never granted the lane.

**No black box.** Every write attempt is recorded, including the ones that were refused. Governance is not a bolt-on. It is the part that makes the rest of it safe to scale. If an agent tried to step outside its lane, you can see that it tried. Nothing happens unseen.

Three modes cover the cases that come up in practice:

| Mode | What it grants |
|---|---|
| `write` | full read and write inside the matched paths |
| `append` | create and append, but never overwrite. Right for a decision log |
| `read` | read but never write. Right for canon an agent should consult, not edit |

## Quick start

```bash
git clone https://github.com/parkbenchepiphany/new-ocean-agent-os
cd new-ocean-agent-os
pip install -e .
python examples/two_agents.py
```

The example wires up two agents, a `scribe` and a `curator`, from a small YAML lane config. It walks through the scribe capturing a raw log, the curator promoting it into durable knowledge, the curator recording a decision in append-only mode, and the scribe being refused when it reaches outside its lane. Then it prints the audit trail so you can see that every step, including the refusal, was on the record.

## Using it in your own code

```python
from noaos import Agent, AuditLog, KnowledgeStore, LanePolicy

store = KnowledgeStore("kb")
audit = AuditLog("kb/audit.jsonl")
policy = LanePolicy.from_config({
    "agents": {
        "scribe":  [{"paths": ["logs/*"],       "mode": "write"}],
        "curator": [{"paths": ["knowledge/*"],   "mode": "write"},
                    {"paths": ["decisions/*"],   "mode": "append"}],
    }
})

scribe  = Agent("scribe",  store, policy, audit)
curator = Agent("curator", store, policy, audit)

scribe.remember("logs/today", "something worth keeping")
curator.remember("knowledge/the-thing", "the durable version")
curator.log_to("decisions/log", "why we decided it this way")
```

Reads and writes both run through the same path: check the lane, record the decision, then touch the store only if it was allowed.

## How this was built

I built this the way I actually work now, with AI tooling in the loop and a human owning every decision. That is the honest description of how a senior operator ships software in 2026, and it is the point rather than a disclaimer. The design choices, the lane model, the closed-by-default posture, the insistence that refusals get logged, are mine, and I can defend every one of them, because I run a version of this every day.

It is deliberately small. There is a keyword recall rather than a vector index, file storage rather than a database, and no network layer. Those are extension points, not v1 blockers. The framework is the shape, and the shape is the part that matters.

## Where the thinking comes from

I write about this kind of work at [New Ocean](https://theoegginton.substack.com). The first post there, on building lane discipline into a multi-agent stack, is the essay this repository makes concrete.

## License

MIT. See [LICENSE](LICENSE).
