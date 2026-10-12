# Grounded concern-dispatch probe v1.2 preregistration

**Date:** 2026-09-28  
**Question:** Once an instruction is already represented with a grounded `compare` dispatch, does the current substrate route it into its concern-authoring faculty and return a non-null authoring result?  
**Scope:** source-locked direct-dispatch measurement; this bypasses and does not test natural-language comprehension.

## Conditions and schedule

Four fresh full-seed workers run two conditions twice each, in alternating order:

- **Grounded concern positive:** construct a minimal instruction comprehension with the original v1.4 text, `kind="instruction"`, and dispatch `{path:"instruction", predicate:"compare", object:null}`; pass it to `conversation_action.act_on_instruction`.
- **Matched non-concern control:** use the same text and representation, changing only the dispatch predicate to `walk`.

The positive oracle requires route `concern_authored`, goal kind `author_concern`, a non-null concern, a nonempty relation signature, and zero teacher calls. The control oracle requires route `goal_only`, no concern object, and zero teacher calls. Record the exact response, concern key, mint/ground verdict, goal identifier, graph counts, rule count, task CPU/wall time, and source locks.

## Integrity gates and claim boundary

Require four unique worker processes, two per condition, stable parent/worker locks, successful full-seed boot, one invocation per worker, and exact condition/oracle accounting. Preserve failures. This tests dispatch and faculty execution for one constructed representation only. It is not an end-to-end natural-language success, a general induction claim, or a prevalence estimate. A successful positive establishes that the faculty route is available once the instruction is grounded; a failure leaves that route unresolved.


## V1.1 harness amendment

V1.0 is partial due to a serialization defect. V1.1 captured a valid positive-route replication but its non-concern control was invalid because the raw text retained concern verbs. V1.2 uses the unchanged grounded-compare positive and a control with raw text “Walk to the door.” and predicate `walk`, isolating the surface and dispatch route. Native Goal handles serialize as integer IDs. See [v1.1 amendment](SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_1_AMENDMENT_20260928.md) and [v1.2 amendment](SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_2_AMENDMENT_20260928.md).
