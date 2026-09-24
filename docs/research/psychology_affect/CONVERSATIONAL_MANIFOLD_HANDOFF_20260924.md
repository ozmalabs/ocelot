# Conversational Manifold Cognition Upgrade — Handoff

Date: 2026-09-24  
Workspace: `/home/matt/ozmadev/ocelot`

## Resume prompt

Continue the conversational manifold cognition upgrade from this handoff. Work
phase-by-phase from the canonical execution plan and use the repository `.venv`
for verification. Preserve the cognition-first, language-agnostic,
non-inherently-turn-based architecture. Do not solve cognition failures with
surface conversation wording. Python remains a mechanical world/semantic
boundary; graph/native rules remain authoritative for cognition and outcomes.

First inspect this file, the execution plan, both progress trackers, `git
status`, and the last commit. Verify the unverified changes listed below before
doing further work. Commit bounded work regularly with detailed messages.

## Current verified state

- Last completed commit before this handoff:
  `10e2220c test: reconcile conversational cognition evidence`.
- Earlier correction commit:
  `47114424 fix: reject unverified kind fast path`.
- The rejected `run_rules_prefix` native optimization is removed from source
  and the installed native extension was rebuilt from restored source.
- Native authority audit: **183 bound / 0 unbound / 183 total**, clean.
- Indexed referent equivalence/compatibility battery: **10 passed** in the local
  `.venv` (`tests/test_concept_indexed_referent_ingress.py`,
  `tests/test_canonical_discourse_referent_seam.py`,
  `tests/test_conversational_intent_arbitration.py`, and
  `tests/test_conversation_intent_arbitration_measurement.py`).
- Conversation loop, aliasing, and output-null gates: **20 passed**.
- Speech parity remains at the known baseline: **7 passed, 3 pre-existing
  failures** (fixture/seed drift around instruction content, `Focus on...`, and
  the additional speech-act seed rule); the rejected optimization did not add
  those failures.
- Phase 8H raw-reference audit is incomplete by design: ELIZA floor, small LLM,
  and modern LLM are case-complete; base-human and advanced-human references
  are missing. Comparative release remains blocked.
- Production envelope remains over the nominal resource budget: cold RSS and
  latency are substrate/runtime allocation issues, not conversation-surface
  issues. The dominant measured first-event cost is the native kind-rule
  selective readback/serialization boundary and cold substrate allocation.
- `noted` is forbidden as a conversational fallback. The canonical failure
  surface is exactly:
  `ERROR: no communicative response could be generated.`

## Unverified work at handoff

The user requested an immediate stop after the following patch was applied but
before tests were rerun:

- `domains/conversation_action.py`: `satisfiable_reply()` now returns the
  graph-minted goal in its result for rule/self-organisation answers.
- `substrate/world_adapter.py`: the existing conversation-action bridge now
  invokes the existing `satisfiable_reply()` and `honest_no_world_reply()`
  faculties for their already-selected comprehension dispatch paths, and the
  release bridge accepts those existing routes.
- `tests/test_comprehension_robustness.py`: the stale statement assertion was
  changed from `noted` to the mandated explicit diagnostic error.

These changes are intended to repair two real cognition-routing regressions:
`Name one of your rules.` and `Describe what you perceive.` were reaching
existing faculties but falling through to the generic error because the live
bridge only invoked action handling for `instruction` kinds. They must be
verified before being committed.

## Immediate next actions

1. Run:

   ```bash
   source .venv/bin/activate
   pytest -q tests/test_comprehension_robustness.py
   ```

2. Run the focused regression slice covering conversation gates and the changed
   production boundary:

   ```bash
   pytest -q \
     tests/test_conversation_loop.py \
     tests/test_utterance_conversation_unification.py \
     tests/test_output_null_gate.py \
     tests/test_phase6_production_gate.py \
     tests/test_phase6a_production_gate.py
   ```

3. If green, run `git diff --check`, inspect the diff, and commit the routing
   fix separately with a detailed message. If not green, diagnose from graph
   commitments and native production-gate evidence; do not restore `noted` or
   add a surface-only exception.

4. Reconcile the progress tracker after verification. The tracker must retain
   the distinction between completed authority/equivalence gates and open
   resource/comparative-human gates.

5. Continue with the next documented cognition/resource increment. Do not mark
   the overall objective complete while the resource envelope, substantive
   Phase 6 cognition gaps, and human comparative references remain open.

## Files and constraints

- Canonical plan:
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md`
- Main cognition tracker:
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_TRACKER.md`
- Progress tracker:
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_PROGRESS_TRACKER.md`
- Use `/home/matt/ozmadev/ocelot/.venv/bin/python` and
  `/home/matt/ozmadev/ocelot/.venv/bin/pytest` explicitly when needed.
- Rust rebuilds, if required, run from `runners/dsl` after sourcing the
  absolute root `.venv`; do not accept a parity-breaking optimization.
- There are many unrelated untracked P5, attestation, semantic-review, and
  deployment artifacts. Do not stage secrets, credentials, or unrelated work.
