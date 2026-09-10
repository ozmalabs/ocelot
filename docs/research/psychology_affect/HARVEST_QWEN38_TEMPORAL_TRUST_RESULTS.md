# Harvest Qwen3.8 — Temporal-Trust Path (block 334000)

## What this closes

Block 331 seeded the reaped-LLM source `qwen3` with a **flat**
`self_published_calibrated` reliability band, and explicitly deferred the
**time-sliced DERIVED** trust path for want of the `communication_concepts`
installer — the JSON→graph materializer that turns a source's `timeline` into
`SourceEvent` graph nodes. The installer had been removed with the python-core
purge (so it could not be accidentally re-used as decision logic), and the
`SourceEvent` grammar looked absent from the checkout.

Block 334 recovers and re-authors that installer as an **additive seed-builder**
and confirms the reader half of the path was already live. The `qwen3` source's
trust band is now **DERIVED + time-sliced**, composed over its dated calibration
events, instead of a flat held tag.

## Provenance of the recovery

- `communication_concepts.py` was **never** tracked in the `ocelot` git history.
- It lived in the internal repo `/home/matt/ozmadev/internal` at
  `research/experiments/gamma-substrate/domains/communication_concepts.py`,
  and was **deleted in `c0288920c4`** ("gamma-substrate: OPERATOR CONSOLE + FOUR
  FRONTIERS …") — consistent with the python-core removal.
- Recovered from `c0288920c4^` (227 lines) and re-authored verbatim-adapted.

## Why re-authoring is additive, not a python-core resurrection

- The module is a **mechanical JSON→graph install** ("world-adapter mechanics
  only, no decisions" — its own docstring). It holds **no decision logic**.
- It is imported by **nothing** on any auto-load / daemon / core path — only by
  scripts that call `install_communication_concepts_seed(substrate)` explicitly.
  Several such scripts already import it, i.e. they were broken by its absence.
- The **reader** side it feeds was already present and live in the checkout:
  - `domains/source_provenance.py`: `context_for`, `_compose_trust`,
    `_source_events`, `_event_grounded_concepts` (read `has_event` /
    `built_from` off the graph);
  - `SourceEvent` / `has_event` are already registered node/edge types
    (`reflective_faculty.py`, `self_migration.py`).
  Only the **writer** (this installer) was missing.
- Dependencies resolve in-tree: `grounded_representation.open_grounding_
  productions` / `ground_concept` / `cone`, and `substrate.add_production`.

## Seed change (`seeds/communication_concepts.json`, NON-protected)

The `qwen3` concept gains `built_from += temporal_entity`, `default_trust =
self_published`, and a `timeline` of three dated, trust-relevant calibration
events — the honest per-tier block-330 calibration made structural:

| event | tier | calibration outcome | trust signal |
|---|---|---|---|
| `qwen3_calibration_knowledge_isa` | knowledge (is-a) | held-out transitive 1.00 (33/33), 0 self-loops, shuffle 0.54 | **earned**, `trust_dir +1` |
| `qwen3_calibration_concept_opposite` | concept (opposite) | AUC 0.59 vs control 0.52 | weak, **neutral** (`trust_relevant:false`) |
| `qwen3_calibration_process_negate` | process (negate) | apply 1.00 but shuffle control **also** 1.00 | **control failed**, `trust_dir −1` |

## Composed result (verified, model-free)

`source_provenance` composes the band by moving the `self_published` baseline
(weight 0.5) one coarse step per net trust event:

- **present cutoff** (whole cone in scope): raising = `[knowledge_isa]`,
  lowering = `[process_negate]`, net = 0 → status `self_published`, weight
  **0.5** — the earned knowledge tier and the failed process control **offset**
  to the calibrated self-published band, now DERIVED + auditable.
- **below attested**: qwen3 0.5 `<` wikipedia 0.9 (`consensus_tertiary`).
- **time-slice proven**: a `when="2020-01-01"` cutoff yields an **empty cone**
  (no calibration event has entered) → the bare baseline. The band is genuinely
  derived from dated events, not a flat constant.

This is the honest outcome: the temporal path does not inflate the source — it
makes the *same* calibrated band **derived, time-relative, and auditable**, with
the failed control visibly dragging against the earned tier rather than being
silently dropped.

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only; no
  Rust touched, no rebuild).
- Protected READ-ONLY files untouched: `runners/dsl/src/can_ops.rs`,
  `domains/can_junction_tree.py`, `domains/can_native_bp.py`,
  `domains/model_reader.py`.
- Models/venv under `/applications` not involved (pure graph verification).
- Committed block-334 only, add-by-name.

## Artifacts

- `domains/communication_concepts.py` (re-authored installer)
- `seeds/communication_concepts.json` (qwen3 timeline added)
- `scripts/llm_harvest_temporal_verify.py` (live verification)
- `tests/test_qwen3_temporal_source.py` (4 tests)
- `tests/test_qwen3_source.py` (stale deferral note corrected)
