# Example operating model

A fictional team uses three agents around one shared knowledge base.

## Agents

- `scribe`: captures raw notes into `logs/*`.
- `curator`: promotes durable knowledge into `knowledge/*`.
- `decision_logger`: appends rationale into `decisions/*`.
- `reviewer`: reads curated knowledge and reports issues.

## Governance loop

1. An agent requests an action.
2. The lane policy checks the path and mode.
3. The action is recorded as allowed or refused.
4. The knowledge store is touched only when the policy allows it.
5. The audit trail remains available for inspection.
