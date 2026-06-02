# Approval-gated research workflow

This example shows how New Ocean Agent OS can be used with an approval gateway for research tasks that may lead to consequential actions.

## Scenario

A user asks an agent to research a topic and prepare an external-facing recommendation. The agent can gather context and draft notes freely inside its lane, but it cannot publish, email, or modify an external system without approval.

## Flow

1. The user submits a research task.
2. A research agent writes raw findings to `logs/*`.
3. A curator agent promotes durable findings to `knowledge/*`.
4. The agent proposes a consequential action, such as publishing a summary or updating a public repository.
5. The approval gateway records the proposal with action, payload, rationale, and risk level.
6. A human approves, rejects, or asks for revision.
7. Only approved proposals reach registered execution handlers.
8. The lane policy and approval gateway both write audit events.

## Example proposal

```json
{
  "action": "publish_summary",
  "title": "Publish weekly research summary",
  "requested_by": "research_agent",
  "risk_level": "medium",
  "rationale": "The summary is ready for external review and contains no private source material.",
  "payload": {
    "source": "knowledge/weekly-research-summary.md",
    "destination": "public/research-summary.md"
  }
}
```

## Lanes

| Agent | Paths | Mode | Purpose |
| --- | --- | --- | --- |
| `research_agent` | `logs/*` | `write` | Capture raw findings. |
| `curator` | `knowledge/*` | `write` | Maintain durable knowledge. |
| `decision_logger` | `decisions/*` | `append` | Record rationale. |
| `reviewer` | `knowledge/*` | `read` | Inspect for gaps and contradictions. |

## Result

The system can move quickly inside safe knowledge lanes while keeping public or irreversible actions behind an explicit human approval step.
