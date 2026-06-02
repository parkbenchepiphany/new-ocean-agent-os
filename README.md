# New Ocean Agent OS

A small framework for running several AI agents against one shared knowledge base, safely: persistent memory, lane discipline, and visible governance.

Most agent demos ask what one agent can do. The harder production question is what happens when several agents read and write around the same body of knowledge. Without a shared operating model, they overwrite each other, blur accountability, and make the knowledge base less trustworthy over time.

New Ocean Agent OS is a compact reference implementation for solving that problem with plain files, explicit write lanes, and an audit trail.

## What it demonstrates

- Persistent Markdown knowledge storage that can be read without the framework
- Agent-specific lane policies for read, write, and append-only access
- Closed-by-default governance for every write attempt
- Audit logging for successful writes and refused actions
- A minimal example of multiple agents working around one shared store

## System shape

```text
+----------------+       +----------------+       +----------------+
| Scribe agent   |       | Curator agent  |       | Reviewer agent |
| raw capture    |       | promotion      |       | read-only      |
+-------+--------+       +-------+--------+       +-------+--------+
        |                        |                        |
        v                        v                        v
+------------------------------------------------------------------+
| Lane policy                                                       |
| logs/*: write     knowledge/*: write     decisions/*: append      |
+------------------------------------------------------------------+
        |                        |                        |
        v                        v                        v
+------------------------------------------------------------------+
| Shared knowledge store, Markdown files plus YAML frontmatter       |
+------------------------------------------------------------------+
        |
        v
+------------------------------------------------------------------+
| Audit log, every allowed and refused action is recorded            |
+------------------------------------------------------------------+
```

## The three design decisions

**Persistent memory.** Knowledge lives in plain Markdown files with lightweight YAML frontmatter. You can open it, diff it, and read it without the framework. The point of the system is not the agents. The point is that canonical knowledge remains inspectable when an agent, vendor, or person changes.

**Lane discipline.** Each agent declares which paths it may write to, and in what mode. Everything not declared is denied. A capture agent can write raw logs without being able to rewrite curated knowledge. A curator can promote knowledge without being able to edit areas it was not granted.

**Visible governance.** Every write attempt is recorded, including refusals. Governance is not a bolt-on. It is the part that makes the rest of the system safe to scale. If an agent tried to step outside its lane, you can see that it tried.

## Access modes

| Mode | What it grants | Typical use |
| --- | --- | --- |
| `write` | Create and replace files inside matching paths | raw logs, draft notes, maintained knowledge |
| `append` | Create and append, never overwrite | decision logs, audit appendices, review journals |
| `read` | Read but never write | canon, policies, reference material |

## Quick start

```bash
git clone https://github.com/parkbenchepiphany/new-ocean-agent-os
cd new-ocean-agent-os
pip install -e .
python examples/two_agents.py
```

The example wires up two agents, a `scribe` and a `curator`, from a small YAML lane config. It walks through raw capture, durable promotion, append-only decision logging, and a refused write attempt. It then prints the audit trail so the governance layer is visible.

## Using it in your own code

```python
from noaos import Agent, AuditLog, KnowledgeStore, LanePolicy

store = KnowledgeStore("kb")
audit = AuditLog("kb/audit.jsonl")
policy = LanePolicy.from_config({
    "agents": {
        "scribe":  [{"paths": ["logs/*"],       "mode": "write"}],
        "curator": [{"paths": ["knowledge/*"],  "mode": "write"},
                    {"paths": ["decisions/*"],  "mode": "append"}],
        "reviewer": [{"paths": ["knowledge/*"], "mode": "read"}],
    }
})

scribe = Agent("scribe", store, policy, audit)
curator = Agent("curator", store, policy, audit)

scribe.remember("logs/today", "something worth keeping")
curator.remember("knowledge/the-thing", "the durable version")
curator.log_to("decisions/log", "why we decided it this way")
```

Reads and writes both run through the same path: check the lane, record the decision, then touch the store only if it was allowed.

## Example operating model

This repo is intentionally small, but it points at a wider pattern:

1. Capture agents can collect raw material into a restricted inbox.
2. Curator agents can promote stable knowledge into canonical notes.
3. Decision agents can append reasoning without editing past decisions.
4. Review agents can inspect outputs without creating new writes.
5. A human can audit both the knowledge store and the refused actions.

## Why this matters

AI systems become risky when they are treated as magic helpers with broad access and weak boundaries. The practical alternative is not to stop using agents. It is to give them clear lanes, record what they do, and keep durable knowledge in a form people can inspect.

That is the purpose of this repo: a small, understandable pattern for agentic workflows where trust is built into the file system, not promised after the fact.

## Portfolio note

This is a generalized reference implementation. It avoids private operational data, live access material, personal context, client information, and employer-specific systems. The repo exists to show the reusable pattern: multi-agent knowledge work with explicit governance.

## License

MIT. See [LICENSE](LICENSE).
