# Boot-time self-model mirror consumer audit

Date: 2026-09-25  
Status: source-path audit; no behavior was changed

## Boot contract

`substrate.boot_all.load_all_seeds` calls `domains.self_model.ensure_self_model` after installing the seed corpus. The full pass mirrors every native rule and graph-resident Rule not represented in the native rule store, and also mirrors programs. `RuleSummary` includes `rule_json`, `from_seed`, active status, read/write descriptions, and structural match text. This is the authoritative source evidence for the boot cost found by cProfile; the profile alone does not justify removing or deferring it.

## Consumers found

| Consumer | Use of the mirror | Consequence if missing/incomplete |
|---|---|---|
| Self-model question handlers in `domains/self_model.py` | Exact rule lookup; topic search over name/seed/match/read/write text; attribute reader/writer listing. | Queries return honest not-found or incomplete lists. Existing tests exercise the real question path. |
| `domains/conversation_action.py` | Picks a real held RuleSummary for a self-directed answer. | The response path can lack a real rule to name. |
| `domains/reflective_faculty.py` | Selects held rule JSON for threshold variants, action/reply composition, and edit-operation choices; other routines upgrade summaries with safety and applicability fields. | Reflection, safe editing, or composition may lose candidates or abstain. Some routines can lazily create a narrower summary, but that is not equivalent to the full mirror. |
| `domains/frozen_core.py`, `domains/collapse_model.py` | Resolve each held rule's `from_seed` and enforce provenance/frozen-core boundaries. | Unknown/missing provenance is denied or excluded; safety behavior is fail-closed, but coverage changes. |
| `domains/rule_signature.py`, `domains/seed_signature.py` | Derive or enrich structural signatures from the already-held rule population. | Signature/seed summaries can be absent or less complete. |

`tests/test_self_model.py` verifies full coverage against `export_rules`, idempotence, program coverage, self-query outcomes, and post-add-rule refresh. Other consumer-specific tests include the reflective composer and frozen-core suites; this audit links them by source search but does not claim they were run in this workstream or that they exhaust all paths. `reflective_faculty` can mint or upgrade selected `RuleSummary` nodes on demand, but that path is narrower than the boot mirror and does not itself prove parity for all consumers.

## Evaluation implication

An eager-versus-lazy experiment must preserve query and mutation semantics, including complete native-rule coverage, duplicate-name rank handling, graph-only meta-rules, program summaries, `from_seed` attribution, and downstream fields added by reflective routines. First measure actual demand and query quality on representative interactions. Any candidate must be evaluated as an architectural tradeoff with full consumer gates; this audit does not recommend changing the eager default.

## Source and test anchors

- Boot call: [`boot_all.py`](../../../substrate/boot_all.py)
- Mirror implementation and query contract: [`self_model.py`](../../../domains/self_model.py)
- Reflective rule consumers: [`reflective_faculty.py`](../../../domains/reflective_faculty.py)
- Conversation consumer: [`conversation_action.py`](../../../domains/conversation_action.py)
- Provenance gates: [`frozen_core.py`](../../../domains/frozen_core.py), [`collapse_model.py`](../../../domains/collapse_model.py)
- Focused self-model tests: [`test_self_model.py`](../../../tests/test_self_model.py)
- Profile cost evidence: [`boot profile result`](SUBSTRATE_SEED_BOOT_PROFILE_RESULTS.md)
