# P23 search remedy decision

**Date:** 2026-10-24. **Evidence:** P23 hash-bound diagnosis only. **Decision:** no larger search ceiling; repair exact effect deduplication and protect independent-goal trial headroom inside the existing cap. This document selects development work and does not amend or freeze the P22 efficacy protocol.

## Measured barriers

| Barrier | Bound evidence | Measurement | Decision |
|---|---|---|---|
| Per-request saturation prevents independent-goal trials in Loopover g1 | `p22_training_panel_registered_root_loopover_g1_0980_0983_ticks120_depth3.json`; P23 funnel artifact `evaluation/process_mastery/results/p23_search_funnel_audit_20261024.json` | Four fresh task requests each used 15,000/15,000 attempts; request headroom 0. The restored graph used 80,000/120,000 cumulative attempts, leaving 40,000 global headroom. Candidate transfer depth was 3, but 0 independent-goal trials were issued. | Reserve up to 5,000 attempts per target request for transfer, funded from the same fixed global ceiling. Do not raise the ceiling. |
| D4 candidate minting spends slots on held and repeated effects | `p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json`; P23 feasibility artifact `evaluation/process_mastery/results/p23_search_feasibility_audit_20261024.json` | 20,000 new attempts produced 2 candidate nodes and 2 distinct new candidate effects; one matched an active held effect and one repeated a prior candidate effect. There were 0 new legal unique effects, 0 qualifications, approvals, or receipts. | Deduplicate by exact native effect digest before minting a new candidate; preserve syntax-level receipts as provenance, not as a new effect. Identity, active, adopted, and duplicate effects remain ineligible. |
| Historical results cannot attribute most attempts to expression/effect stages | `p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json`; P23 funnel artifact above | For D4 g2 0992/0993, 19,998 of 20,000 attempt IDs have no candidate-summary expression link. Historical artifacts therefore support attempt-status totals and candidate-bearing lower bounds, not a complete expression funnel. | Add a separately opt-in, read-only attempt detail export for future development runs. Keep it disabled by default and record this historical gap as unresolved. |
| D4 finite source/child coverage is sparse in the inspected training corpus | `p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json`; P23 feasibility artifact above | At generation two, three novel nonidentity effects remain: two have distinct-goal finite composition witnesses; one has no matching source task in the inspected training tasks. Native qualification remains unestablished. | Preserve the distinction between finite mathematical feasibility and actual native qualification. Do not spend larger search budgets before candidate/attempt tracing is repaired. |

## Fixed resource experiment for the later P26 search repair

The first bounded reserve experiment uses four distinct training goals and the immutable Loopover invention g1 checkpoint. Its inherited attempt count is 20,000. Keep the existing cumulative ceiling at 120,000 and cap this development branch at 60,000 new attempts:

| Allocation | Per target | Targets | Total |
|---|---:|---:|---:|
| Ordinary discovery search | 10,000 | 4 | 40,000 |
| Independent-goal transfer reserve | 5,000 | 4 | 20,000 |
| **New work cap** | **15,000** | **4** | **60,000** |

The maximum cumulative attempt count is 80,000, below 120,000. Transfer requests must be distinct training-goal contexts linked to the exact candidate and source parent. If the reserve is unused, report it unused; do not reallocate it to discovery within this experiment. Candidate-specific approval remains required for any adoption and is not included in this budget.

## Implementation contract and disposition

P26.02 may implement these as bounded subtasks:

1. Exact-effect deduplication before candidate minting: generator + regenerated seed form one ≤3-file touch group; add a focused native regression/control test in a separate group. Check identity, active, adopted, same-effect/different-syntax, and true novel effects.
2. The 10,000/5,000 request split: keep the existing 120,000 global ceiling; add an explicit transfer-request path with candidate/source/goal provenance and no held-out inputs. Test both saturation and available-headroom cases. The experiment above is a single development draw, never a benchmark result.
3. Optional attempt-detail export: extract only existing native graph records into an external report behind an explicit CLI flag; no solver, candidate, qualification, approval, or world policy changes. Verify disabled-by-default behavior and no agent-output channel.

Original P22 remains DRAFT and its held-out gate remains closed. P23 evidence does not prove global unreachability, establish efficacy, complete a candidate qualification, authorize an approval, or justify weakening novelty. Phase 27 must choose original-protocol re-entry only if all original gates are met; otherwise define a versioned successor.
