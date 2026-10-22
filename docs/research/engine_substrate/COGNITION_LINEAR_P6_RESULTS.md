# Linear Phase 6 results

Status: **executed; evidence classified, capability claims limited**. The frozen draw was run once after [`COGNITION_LINEAR_P6_PREREG.md`](COGNITION_LINEAR_P6_PREREG.md) was committed. Raw scorecards are retained outside git at `/tmp/linear-p6-heldout.json` and `/tmp/linear-p6-heldout-analysis.json`.

## Frozen run and integrity

- Preregistration commit: `f31f17ae`.
- Source commit: `3178ee20`; held-out scorecard metadata records the preregistration commit `f31f17ae` as the current checkout HEAD.
- Command: `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p6_v1 --split heldout --output /tmp/linear-p6-heldout.json`.
- Analyzer: `.venv/bin/python -m evaluation.process_mastery.analyze_linear_p6_v1 /tmp/linear-p6-heldout.json`.
- Raw scorecard SHA-256: `2f7d77c604c66442a6e89ad8f732e11f93511da57c8f183fd1a692ada5bc5329`.
- Analysis SHA-256: `f503283f8462092208eeb637fb04aa54d1af056c42ef8926067f6d8b0dbb9259`.
- Source, profile, engine and MBPP fixture hashes match the preregistration. The draw produced 1,780 records: 400 Loopover, 400 D4, 400 mechanism, 100 controls and 480 program-arm rows.
- The exact 240 MBPP test task IDs and world/control seed blocks are in the preregistration. Baseline and Track I received paired world rows in isolated graphs, with 3 ticks and at most 100 native rule steps per tick.

## Outcomes

| Family | Baseline | Track I | Result and limits |
|---|---:|---:|---|
| Loopover 2×2 | 0/200 solved (95% Wilson CI 0–1.8845%) | 200/200 solved (95% Wilson CI 98.1155–100%) | Same visible boards, goals and eight held moves. Track I emitted 400 ProcessSchema actions (2 per task); baseline emitted none. Mean ticks were 1.000 and 2.515 respectively. Mean measured runner time was 0.00019 s and 0.89305 s; mean graph growth was 10 and 1,769.755 nodes. This is a small supplied-process 2×2 result using the explicitly hand-written greedy process solver, not evidence of process invention or broad puzzle capability. |
| D4 transformations | 200 NOT_RUN | 200 NOT_RUN | No grounded D4 action/effect adapter. Both arms retain the scorer-side target digest only. Comparative claim blocked. |
| Finite mechanism discovery | 200 NOT_RUN | 200 NOT_RUN | No intervention/observation adapter. Both arms retain the scorer-side truth digest only. Comparative claim blocked. |
| Malformed/stale/opaque controls | — | 100/100 passed | 34 malformed, 33 stale-source, 33 opaque-transition cases returned unknown with serialized graph attributes unchanged. |
| MBPP test synthesis | 32/240 held-out passes | 32/240 held-out passes | The two arms emitted the same candidate IR and exact solver/external outcome on all 240 paired tasks. Each accepted 168 candidates; 32 passed all held-out assertions (13.33%, 95% Wilson CI 9.6054–18.2166%), 136 accepted candidates failed held-out assertions, 69 gapped, 1 ended `evaluated` without an accepted candidate, 1 request was not recognized, and task 237 raised a runner `TypeError` in both arms. Mean elapsed time was 0.11722 s baseline and 0.14127 s Track I; mean graph growth was 2,728.354 nodes in each. Track I supplied no synthesis improvement on this family. |

The MBPP adapter stripped test-split `code`, passed only the prompt and first parseable assertion into synthesis, kept remaining assertions in the detached scorer, and returned no `heldout_graph_leak` record. The one `TypeError` is retained as a runner failure; this protocol was not repaired or rerun against the same holdout. Human comparisons are unavailable for all families.

## Verification and inherited gates

Before the held-out draw, both evaluation self-check commands passed and the focused Phase 6 bundle passed **59 tests**:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p6_v1 --split development --self-check
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p6_v1 --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_pmb_execution_contract.py tests/test_process_native_views.py tests/test_track_i_foundation.py tests/test_cognition_profile_integration.py tests/test_pmb_program_adapter.py tests/test_program_synthesis_migrated.py -q -p no:cacheprovider
```

The inherited baseline verifier passed its accounting gate: 4 listed tests remain red, 0 listed tests are stale, and 0 new failures appeared. The 20-file sweep recorded 16 GREEN, 2 RED (`test_frozen_core_invariant.py`, `test_dual_process_core_migrated.py`), 1 NOT_ESTABLISHED (`test_capability_control_fabric_migrated.py`, 420-second timeout), and 1 ALL_SKIPPED (`test_staleness_decay_migrated.py`). These are inherited regression states, not P6 improvements. Orphan-signal lint reports 2,065 existing entries; P6 added no seed rules or new signal writers. Boot-status reporting covered 879 catalog entries. No Rust files changed, so no Rust rebuild was required.

## Phase disposition and next entry

P6.01–P6.06 and E1 integration are implemented and their focused assertions pass. Program views are bounded and detached; supported DimensionGenerator behavior remains probe-relative. TransitionHypothesis, CapabilityProgram, EmbodiedMotorProgram and FamilyProgram effects remain opaque. D4 and mechanism panels are explicitly NOT_RUN, so their comparative claims remain blocked. The 2×2 Loopover difference is measured but derives from enabling the existing greedy solver with supplied processes; MBPP is exactly unchanged between arms. No L1–L7 capability level is closed.

Phase 7 may begin with its registered episode-acquisition work, restricted to the tool/contact and social request/repair worlds in its plan. It must preserve held-out episode provenance, learn distinctions from experience, and may use only the supported detached process views described above. It inherits no D4, mechanism-discovery, physical-effect, or synthesis-gain claim from P6.
