# Repeated P4 acquisition resource diagnostic (2026-09-25)

**Status:** discovery diagnostic on an already inspected task family; not a confirmatory generalization or scaling study.

## Question

Across repeated real P4 acquisitions on a varied fixed task set, what route outcomes, TermArena logical-node counts, graph sizes, and process RSS are observed? This extends the one-task IR cleanup probe by measuring actual synthesis requests and per-task fresh-substrate lifecycles.

## Locked procedure

Use all 18 tasks in fixture order from `tests/fixtures/substrate_string_pbe_contrast/tasks.json`. Each task gets a new substrate from `prog_synthesis_battery.boot(frozen=False)` and the standard `domains.prog_synthesis.synthesize_from_request` route, with the fixture request and four revealed examples, without retries or budget changes. Held-out rows are used only to score an accepted IR. Record status, construction/rungs where present, gap reason, route wall/CPU time, TermArena logical length and graph node count before/after acquisition, current RSS before/after acquisition, and process peak RSS. For accepted IRs, evaluate all seven rows through the substrate ProgEval path and record per-row outcomes. Non-accepted results remain observations rather than harness failures.

The runner, task fixture, P4 boot/route sources, synthesis adapter, retrieval adapter, seed, preregistration, and native extension are hash-locked before execution. The runner also verifies the native build is current. The run is serialized in fixture order in one process; current RSS is a point measurement per task while peak RSS is process-wide and cumulative. Fresh Substrates do not imply allocator or OS page reclamation between tasks.

## Interpretation

This measures the existing route on one known, previously inspected string-task family. It can reveal within-family variability and whether logical arena counts or observed RSS grow over repeated fresh-substrate acquisitions. It does not establish asymptotic complexity, natural-task prevalence, independent generalization, allocator reclamation, memory isolation per task, or rung 3/4 induction capability. TermArena length is a logical-node count, not allocated capacity. Accepted held-out scores are descriptive only.
