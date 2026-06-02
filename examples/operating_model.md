# Example operating model

This example describes a fictional team using New Ocean Agent OS.

## Agents

- `scribe`: captures raw notes into `logs/*`.
- `curator`: promotes durable knowledge into `knowledge/*`.
- `decision_logger`: appends rationale into `decisions/*`.
- `reviewer`: reads curated knowledge and reports issues.

## Safety rules

- All agents are denied by default.
- Append-only areas are used for decisions and audit material.
- Human review is required before any material leaves the local knowledge base.
- Credentials, personal information, and private operational details are never stored in examples.

## Governance loop

1. Agent requests an action.
2. Lane policy checks the path and mode.
3. The action is recorded as allowed or refused.
4. The knowledge store is touched only when the policy allows it.
5. A human can review the audit trail later.
