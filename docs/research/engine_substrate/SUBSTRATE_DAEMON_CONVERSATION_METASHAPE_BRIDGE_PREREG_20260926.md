# Daemon conversation → MetaShape bridge probe preregistration (2026-09-26)

## Question

When the daemon's full seed profile has `meta_shape_growth` installed, do repeated ordinary public conversation turns create `ShapeObservation` inputs or new `MetaShape` nodes without an explicit caller invoking the `teach()` helper?

## Fixed protocol

1. Start one fresh `WorldAdapter(seeds=())` and call `load_all_seeds`, matching the daemon's fresh `full` branch. Preserve and report loader failures.
2. Set `OZMA_SEED_PERSIST_DISABLED=1` before submitting any turns. This prevents any incidental `teach()` call from changing real `seeds/*.json`; all other in-memory behavior remains enabled.
3. Record baseline counts and identities for `ShapeObservation`, `MetaShape`, `TaughtHint`, and `TeacherEvidence`.
4. Call the public `WorldAdapter.converse(text, speech_act="statement", speaker="user")` interface twice each, in this fixed order:
   - `A dax has a red shell.`
   - `A wug has a blue shell.`
   - `A dax has a red shell.`
   - `A wug has a blue shell.`
5. After each turn, record reply, total and added counts for the four node types, and `teach()` persistence guard state. Do not inject `TeacherRequest`, call `teach()` directly, attach an external teacher, or alter seed selection.
6. Hash the runner, daemon, `WorldAdapter`, boot loader, `teach`, `meta_shape`, and growth seed source; capture native extension hash and engine preamble.

## Adjudication

- **Bridge activated:** a conversation turn adds a `ShapeObservation` through the public conversation route; report whether any newly added observation reaches non-pending status and whether a new MetaShape appears.
- **Evidence-only/no bridge observed:** no ShapeObservation or MetaShape delta occurs across the four turns, regardless of ordinary conversation graph growth.
- Any turn error, persistence write attempt not blocked by the environment guard, incomplete boot profile, or source-hash mismatch invalidates interpretation and must be reported.

This is a single fixed authored interaction sequence. It measures route reachability and activation only; it does not estimate natural conversation prevalence, concept-learning accuracy, transfer, or performance. The protocol deliberately does not infer “no learning” from an empty observation count outside the measured MetaShape route.
