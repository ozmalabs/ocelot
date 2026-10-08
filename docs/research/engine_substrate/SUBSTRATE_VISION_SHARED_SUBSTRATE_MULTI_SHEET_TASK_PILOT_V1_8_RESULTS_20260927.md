# Shared-substrate closure-pass state trace v1.8 results

## Method validation

The source-locked passwise instrument passes all seven analysis checks. Before collecting the full panel, one-pass slices were compared with ordinary full closure on two independent cells: root-scoped B-only (cyclic) and global both-gratings (fixed point). Each matched the full run exactly in terminal graph digest, status, total progress work, and pass count. The complete trace then covers all four conditions under both rule variants from the v1.7 checkpoint.

The export order is the same except for the settling rule name:

| Slot | Root-scoped rule | Global rule |
|---:|---|---|
| 149 | `st_latch_aff` | `st_latch_aff` |
| 150 | `st_settle_root_scoped_benchmark` | `st_settle` |
| 151 | `st_commit` | `st_commit` |
| 152 | `st_burst_bubble` | `st_burst_bubble` |
| 154 | `oo_sunit_activate` | `oo_sunit_activate` |
| 155 | `oo_sunit_rate` | `oo_sunit_rate` |

This is an export-order readback from the same source closure as the captured run. The pass trace itself records per-unit field transitions; it does not directly attribute each native mutation to a RuleUid.

## Exact termination outcomes

| Scope | Condition | Passes | Outcome |
|---|---|---:|---|
| Root-scoped | Both blank | 4 | Fixed point |
| Root-scoped | B only | 168 | Cycle, start after pass 160, period 8 |
| Root-scoped | A only | 190 | Cycle, start after pass 184, period 6 |
| Root-scoped | Both gratings | 208 | Cycle, start after pass 184, period 24 |
| Global | Both blank | 4 | Fixed point |
| Global | B only | 166 | Cycle, start after pass 158, period 8 |
| Global | A only | 171 | Fixed point |
| Global | Both gratings | 169 | Fixed point |

Each cycle was detected by exact recurrence of the complete serialized graph digest, not inferred from an `act` trace alone. Root-scoped and global rules therefore have different dynamical outcomes on this one identical learned state: the global A-only and both-stimulated conditions reach fixed points where their root-scoped counterparts cycle.

## Field timing

For every condition in both scopes, `act` and `act_step` first change on pass 2; `rate` and `rate_step` first change on pass 3. `theta` never changes during these frozen probes. After the rate write, `act` continues changing in later settling passes: 82–103 later passes per nonblank condition have at least one unit's `act` change. The rate field and its stamp do not change again. That directly explains why current `rate_step` can coexist with a `rate` value that does not match final `act`: the stamp describes the Retina step, not the closure pass at which the value was computed.

The observed schedule plus rule order shows that a same-step rate value is not a reliable proxy for the final settling activation. This does not by itself make the rule incorrect; it establishes that capability reports must name the field and phase being measured. A post-settle firing rate would require an explicitly different update contract.

## What this changes in the programme

The v1.7 endpoint contrast is now properly bounded: there is a reproducible cross-sheet/dynamical difference on the shared adapted state, and the exact cycles or fixed points can be reported rather than collapsed into a single “settled” label. The two-cell slicing preflight validates the passwise capture method for one cycle and one fixed point. The remaining uncertainty is semantic and broader than this fixture: which response field is the task outcome, whether the observed cycles are intended under these stimuli, and whether scope differences persist across seeds, anatomies, and independently defined visual tasks.

Next preregister a response contract that records pre-settling drive, post-settling activation, rate, and termination class as separate outcomes. Then repeat a multi-seed and stimulus panel, preserving cycles as outcomes. Do not report a single CPU tractability class from operation counts until fixed-point prevalence, cycle prevalence, and total trace/closure cost are measured over independently authored cases.

## Evidence

- [Raw summary with all pass snapshots](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_20260927.json)
- [Passwise JSONL trace](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_20260927.trace.jsonl)
- [Independent analysis](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8_analysis_20260927.json)
- [Runner](../../../scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_8.py)
- [Analyzer](../../../scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_8.py)
- [Preregistration](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_8_PREREG_20260927.md)
- [Source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_8_lock_20260927.json)

The measurement remains one seed, one learned graph state, four presentations per scope, and a 4×4-unit Retina. It is not a prevalence or scale estimate.
