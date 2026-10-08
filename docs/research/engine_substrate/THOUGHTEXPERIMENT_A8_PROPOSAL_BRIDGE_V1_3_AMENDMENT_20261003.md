# A8 proposal bridge v1.3 amendment (2026-10-03)

## Reason for a new capture

The v1.2 order stage passed, but held-out scoring stopped before saving a score artifact. The source-control setup unpacked `task.build_agent()` incorrectly: its third return value is the reflective-faculty module, while the native rule interface is `agent.inner`. V1.3 corrects that binding. The failed v1.2 result and artifacts remain unchanged and are not evidence of held-out behavior.

## Frozen criteria

V1.3 retains v1.2's tasks, train/held-out split, prompts, candidate ordering, proposal gates, scoring, and analysis criteria. It creates a new source lock and fresh order capture before scoring; it does not reuse v1.2 order outcomes. It also retains the original protocol and failed v1.2 result in the source provenance list. The scoring worker now reconstructs the source-rule control from `task.build_agent()` and reads active rules from the returned agent's native interface.

This is a corrective replay of a known fixture, not a blind replication. A successful result would establish prompted A8 proposal behavior and held-out utility on the navigation task only; no-cue abstention remains the diagnosis boundary, and no result here establishes autonomous residual interpretation or open-ended repair discovery.
