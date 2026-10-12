# Recursive self-improvement, tranche 13: results (2026-10-09)

Follows the [tranche 12 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE12_RESULTS_20261009.md).

## Summary

| Item | Result |
|---|---|
| Child-runner storage | **Done.** `convo_child_run` writes `final_graph.json` (several GB per run, read by nothing for the conversation family) only when the delta sets `keep_final_graph` or `OZMA_CHILD_KEEP_GRAPH=1`. A conversation run directory now holds about 109 MB (the parent snapshot), down from several GB. This was the cause of the tranche-12 disk-full. |
| Structural grain signal source | **Done (opt-in).** `_knob_signal_types` derives the node types a gated signal lives on from the gating rule's own match pattern and the live graph. It returns `["SentenceParse"]` for both reform knobs, matching the held list. It is opt-in (`grain_signal_source="structural"`) because the exact full-graph scan costs about 5 s on a full boot. |
| **Mixed-kind credit gate** ([prereg](SUBSTRATE_VARIATION_CREDIT_MIXED_KIND_V1_PREREG_20261009.md)) | **FAIL (M1, M2).** Credit and no-credit handled the same on both kinds: instruction 3/4, reported 4/4. M3 (0 false adoptions) and M4 (credit steered 3/4 later first picks to each kind's working family) passed. **The cause is a finding:** since tranche 11, the misordered prior costs nothing, so there is nothing for credit to save. |
| Regression | **0 new failures** across 221 files; 2 fixed relative to tranche 12. |

## 1. Child-runner storage

Nothing reads the conversation child's variant graph:
- adoption re-applies the delta to the parent;
- `experiment_dispatch` ingests `result.json` and `trace.jsonl` only;
- the only test that checks `final_graph.json` is for the ARC child runner, which is unchanged.

The write is now opt-in, and `result.json` records `final_graph_written: false`.

Measured on one real condense experiment, the run directory holds `parent_snapshot.json` (109 MB), `delta.json`, `trace.jsonl`, `result.json` and `log.txt`. The verdict is unchanged (refuted, as before).

## 2. Structural grain signal source

`_knob_signal_types(native, sub, knob_attr)` works in four steps:
1. find the active rule comparisons that gate a signal on the knob;
2. take the Var on the signal side;
3. find the rule's own match triples that bind that Var;
4. return the node types that the triple's edge actually binds in the live graph.

This is an exact graph read, and it returns `[]` when the signal source cannot be derived.

Configuration:
- When `knob_edit.grain_signal_source == "structural"`, the builder uses the derived types, with the held `grain_signal_types` as fallback.
- Otherwise the held list is used, which is the default and unchanged.

Test: `test_knob_signal_types_derived_structurally`. With the held list emptied, the structural path alone still steps the residual knob 1→3.

## 3. Mixed-kind credit gate

Setup:
- a lab boot that loads `variation_credit` explicitly; the production default is unchanged;
- one agent per arm;
- an interleaved stream of 4 instruction gaps and 4 reported reform-knob concerns;
- the misordered prior `reply_ablation.priority=8`.

| Arm | Instruction handled (experiments) | Reported handled (experiments) | False adoptions | Late first pick = working family |
|---|---|---|---|---|
| A, no credit | 3/4 (5) | 4/4 (4) | 0 | 0/4 |
| C, credit + tranche-9 policy | 3/4 (5) | 4/4 (4) | 0 | **3/4** |

| Gate | Condition | Result |
|---|---|---|
| M1 | C > A on instruction | **FAIL** |
| M2 | C > A on reported | **FAIL** |
| M3 | 0 false adoptions in C | pass |
| M4 | late first pick correct ≥ 3/4 | pass |

**What happened.** In both arms, every concern's first attempt was the misordered family `reply_ablation`. Its builder abstained, because these concerns name no acting reply rule. Since tranche 11, an abstained variant is closed before dispatch, at no replay cost and no credit, and the agent's retry moves to the next family.

So the misordered prior now costs zero experiments, and the arms differ only in *what is picked first*: credit makes the working family the first pick (M4), while the no-credit arm reaches it one free abstain later. The prereg assumed the wrong prior would cost real replays, as it did in tranches 8–10, where `reply_ablation` produced dispatched inconclusive trials. That assumption no longer holds. The gate measured a cost that the tranche-11 abstain-close had already removed.

This is reported as a failure of the preregistered gates, not re-scored. Two consequences follow:
- **Outcome credit's measured value on this pipeline is now in ordering, not in saving replays,** whenever the misordered family abstains.
- **A mixed-kind gate that tests replay savings** needs a misordered family that does *not* abstain, for example one that builds a variant which is judged inconclusive.

One miss is common to both arms: `alphabetise` (concern 7). Its first attempt authored no requested experiment and no retry followed. This was not diagnosed in this tranche. In earlier gates `alphabetise` was repaired, so this looks like interaction state from the stream, not the verb itself.

## 4. Regression

Scope: 221 files, compared against `pf_t12.failed`.
- 0 new failures.
- 2 fixed: the two fixed-step tests updated at the end of tranche 12.
- The run rewrote `tests/fixtures/comprehension_divergence/divergence.json` (latency values only). It was restored.
- `test_residual_promote` timed out, as in every tranche.

The seeds the probes could write to were byte-identical after the run.

## Next

- A mixed-kind gate v2 whose misordered family builds and dispatches (it does not abstain), to test replay savings across kinds.
- Diagnose the `alphabetise` no-experiment at stream position 7.
- Make the structural signal scan cheap: index by edge type, not a full node scan, then consider making it the default.
