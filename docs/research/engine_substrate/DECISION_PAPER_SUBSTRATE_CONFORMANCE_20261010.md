# Decision paper (02c, revisions 3–10) against the substrate: conformance, census and one fix (2026-10-10)

Paper 02c (`papers/formal/02c_seldon_manifolds_decision_making.tex`) was rewritten in revisions 3–10. Most of the rewrite is conceptual: decision as operative continuation, deliberative decision as inferred attribution, and the evolution, woodlouse and language-model examples. Those parts need no substrate counterpart. Its formal core (Definition `def:finite-policy`) makes checkable claims about selection: an argmin over a non-empty feasible set, a declared tie rule, termination on an empty set, and **an undefined cost makes the minimum undefined, never silently 0 or ∞**. This note records how the substrate compares and what was changed.

## Summary

| Paper claim | Substrate | Outcome |
|---|---|---|
| Undefined cost must not become 0 or ∞ | `cmp_value` orders `None` below every number, so a missing cost wins Argmin. | **Census added; 0 exposure measured** on 5 workloads (315,728 selector firings). No behaviour change warranted (§1). |
| Self-revision is authorised by the present organisation (`prop:self`) | `mark_adopt_ready_*` marked adopt-ready on a provisional verdict that a family judge then overrode, and `perform_adoptions` adopted it anyway (tranche 23: `adopted=True`, `outcome='refuted'`). | **Fixed:** `adoption_safety` v1.1.0 (§2). |
| Declared deterministic tie rule | First-encountered, documented in the fold. Already measured: ties are inconsequential in conversation and load-bearing in routing, with a preregistered NO-GO (`TIE_CONSEQUENTIALITY_RESULTS.md`). | Conforms; no change. |
| Pareto comparison does not select; an empty set terminates | `cognitive_pareto` only flags dominance. `commitment_gate` refuses `no_unique_decision`. Argmin returns null on an empty source and live callers check for it. | Conforms. |
| Narrative default and reopening; expected non-occurrence | No counterpart: conversation turns are arbitrated afresh. | Not implemented. The paper proposes these and does not validate them. |

## 1. Null-candidate census

**Instrument.** `runners/dsl/src/argmin_tie.rs`, `term.rs` and `py.rs` gain three counters in the existing tie-audit instrument, active in `OZMA_ARGMIN_UNIQUE=count`:
- `null_mixed`: at least one `None`-valued candidate *and* at least one defined candidate. This is the only case where the `None` ordering decides anything.
- `null_wins`: a mixed firing whose returned element's value is `None`.
- `null_all`: every candidate's value is `None`.

Each count is attributed per site through `argmin_null_sites()`. Behaviour is unchanged in every mode. With the audit off, the cost is the existing single atomic load.

**Positive control.** `tests/test_argmin_null_census_migrated.py` has 6 tests. They cover:
- a missing cost wins Argmin over 3.0 (the ordering fact);
- the census counts and attributes it;
- an Argmax mixed firing is counted without a win;
- an all-null firing is counted;
- defined costs and empty sources count nothing;
- off mode counts nothing.

**Measurement** (`count` mode). Conversation: `evaluation/substrate_capability/argmin_null_census_v1.py 40`, the production daemon loop on the conversation profile with self-improvement on (report: `evaluation/reports/argmin_null_census_v1_conversation_n40_20261010.json`). The other domains used the tie census's per-domain pytest workloads via `scripts/argmin_tie_report.py`.

| Workload | Firings | Ties | Empties | null_mixed | null_wins | null_all |
|---|---|---|---|---|---|---|
| Conversation, production loop (40 turns, 2 adoptions) | 29,827 | 12,852 | 5 | 0 | 0 | 0 |
| ARC (23 test files) | 261,966 | 1,428 | 13,104 | 0 | 0 | 0 |
| ls20 (4 files) | 13,487 | 1,274 | 0 | 0 | 0 | 0 |
| quanta navigation (1 file) | 1,556 | 122 | 0 | 0 | 0 | 0 |
| embodied (16 files) | 8,892 | 417 | 4 | 0 | 0 | 0 |
| **Total** | **315,728** | | | **0** | **0** | **0** |

No live selector on these workloads ever compares a missing cost. The seed authors guard costs with explicit `IfThenElse(Eq(x, null), …)` defaults, which are declared rather than silent. Under the agreed condition, the comparison fix is therefore **not warranted**. The census stays in place as a guard.

**Scope limits.**
- The census covers the Argmin/Argmax/ArgminUnique fold only. It does not cover `Min`/`Max` value folds, `numeric_argmin`, or comparison Terms. The one recorded real bug of this class was a comparison: `Lt(null, 0.0)` is True (`PROGRAM_SYNTHESIS_ARC6_ARC_GOALS.md:473`). Comparisons are unmeasured.
- Coverage is limited to these workloads. In the ARC run, 22 `test_arc_executor` tests errored for the known environmental reason (`results/` is untracked), so their paths were not exercised.

## 2. No adoption on an overridden verdict

**The race.** `mark_adopt_ready_*` marks an experiment adopt-ready when the generic judge writes `supported`. In the same fixpoint, `self_optimisation.judge_performance_experiment_outcome` can override the verdict to `refuted`. `perform_adoptions` reads only `adopt_ready`, so it adopted the change. Tranche 23 exempted only the `deep_reader_edit` family. The general race remained for every performance-objective experiment.

**Fix.** `seeds/adoption_safety.json` v1.1.0 (`scripts/gen_adoption_overridden_verdict_veto.py`) adds the standing veto `adopt_denied_on_overridden_verdict`. When `adopt_ready` is set, the experiment is not adopted, and its outcome is present but no longer `supported`, the veto sets `adopt_denied` with a reason. `perform_adoptions` already honours `adopt_denied`. The authored `mark_adopt_ready_*` bodies are unchanged, as with the regression veto. An experiment with no outcome is left alone.

**Tests.** `tests/test_adoption_overridden_verdict_migrated.py` has 4 tests:
- the race reproduced in-graph on the conversation profile: the generic `supported`, then adopt-ready, then the speed judge's `refuted`, ends denied and not adopted, and the original rule stays live;
- a supported final verdict is not denied;
- an experiment without an outcome is untouched;
- the rule round-trips through the engine.

`test_adoption_safety_migrated` now pins two rules.

## Regression (targeted)

Scope: 19 files covering adoption, experiments, self-improvement, selectors and engine provenance.
- **0 attributable failures.**
- `test_argmin_unique_migrated` has two failures that predate this work: it pins `term_variants.rs` index text and "no seed binds ArgminUnique". Neither file was touched, and seeds have bound `ArgminUnique` since an earlier commit.
- The 4 embodied/pybullet failures in the census run also fail on the HEAD engine.
- `test_engine_provenance_migrated` passes on the rebuilt engine.
