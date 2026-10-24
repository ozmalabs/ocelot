# P23 search diagnosis results

**Date:** 2026-10-24. **Scope:** hash-bound archived P22 roots and training-only restored branches. **Held-out access:** none. **Agent graph mutation:** none. **P22 status:** draft remains unfrozen; this diagnostic neither qualifies candidates nor authorizes approvals.

## Input integrity and bounds

The read-only inventory and its raw input SHA-256 values are recorded in [the P23 diagnostic contract](COGNITION_SEARCH_DIAGNOSIS_CONTRACT.md). It binds the P22 implementation/seed sources, D4 and Loopover roots/ancestors, and 30 restored development artifacts, including no-candidate, replay and interrupted allocations. The hash-bound inventory tests verify every listed raw input; the funnel analyzer checks each branch against its listed digest before analyzing it. The two generated analysis artifacts and their hashes are:

| Artifact | SHA-256 | Scope |
|---|---|---|
| `evaluation/process_mastery/results/p23_search_feasibility_audit_20261024.json` | `d455feca1cf26b404c2e46cb657b36ed71b998fd776112f3359e4a901ddb0e6b` | D4 finite closure/qualification feasibility and depth-bounded Loopover witnesses |
| `evaluation/process_mastery/results/p23_search_funnel_audit_20261024.json` | `4fea7e6d2704cefa6c2a8a426bee483f49cb542b9a3579b1fef0d04673ce70d7` | Branch-increment funnel, resources, predicates and parent binding |

The P23.02 audit used only `training` tasks embedded in the bound graph snapshots. It enumerated the D4 effect closure from the exact `rot90` and `flip_r` transformations. Loopover search was limited to composition depth 3 and 100,000 visited effects. Bounded misses are reported as `UNKNOWN_OUTSIDE_BOUND`; no report makes a global unreachability claim.

## Findings

| Question | Evidence | Finding | Limit |
|---|---|---|---|
| Which D4 effects remain at each inspected root? | Feasibility artifact, `d4.generation_zero` and `d4.generation_two` | Both roots have the exact 8-effect D4 closure. After subtracting root-specific active/adopted and identity effects, generation zero has 5 novel nonidentity effects; generation two has 3. | Finite effect reachability does not show that a candidate expression was proposed, natively verified, or qualified. |
| Can remaining D4 effects pass mathematical source/child conditions on inspected training goals? | Feasibility artifact `records[].goal_pair_records` | At g0, 4/5 remaining effects have at least one distinct-goal finite composition witness; the fifth has no source goal in this training corpus. At g2, 2/3 have such witnesses; effect `[3,2,1,0]` has no matching source task in the inspected training goals. | Even a witness remains `NOT_ESTABLISHED_REQUIRES_NATIVE_VERIFIED_TRIALS`; one finite corpus miss is not global impossibility. |
| Which Loopover goals are expressible within the declared bound? | Feasibility artifact `loopover` | BFS visited 845 distinct effects and found 4 of 5 archived training goal effects by depth 3. One goal is `UNKNOWN_OUTSIDE_BOUND`. The node bound was not exhausted. | No conclusion is made about Loopover effects beyond depth 3 or about the full permutation group. |
| Where did restored search work go? | Funnel artifact, 30 bound branch rows | 20 unique completed restorations, 8 completed no-candidate restorations, 1 replay and 1 invalid interrupted allocation. Unique branch increments sum to 1,401,440 attempts; inherited graph counters are subtracted and the replay/interrupted rows add zero independent completed work. | Aggregate work is across separate graph restorations, not one graph counter or efficacy sample. |
| Why did Loopover g1 transfer receive no trial attempts in the four-goal 0980–0983 branch? | Funnel artifact row for `p22_training_panel_registered_root_loopover_g1_0980_0983_ticks120_depth3.json` | Four new goal requests each used 15,000/15,000 attempts. Request headroom was zero while cumulative graph work was 80,000/120,000, leaving 40,000 global headroom. Candidate transfer depth was 3, yet no independent-goal trials were issued. The source rule requires a distinct-goal request whose own count remains below its request ceiling. | This identifies per-request saturation in that branch; it does not show that every Loopover lineage has the same barrier. |
| Why did the D4 0992–0993 branch fail to create a legal new effect? | Funnel artifact row for `p22_training_panel_registered_root_d4_g2_0992_0993_ticks120_depth3.json` | Of 20,000 new attempts, 17,271 were residual and 2,729 verified. Two new candidates produced zero legal unique effects: `#46754` matched an active held effect; `#57642` repeated a prior candidate effect. There were 882 independent-goal attempts (801 residual, 81 verified), no new qualification, approval, receipt or checkpoint. | Candidate-borne expressions are a lower-bound view; see the unresolved historical instrumentation gap below. |
| Are historical attempt-to-expression counts complete? | Funnel artifact row above | No. 19,998 of those 20,000 D4 attempt IDs have no candidate-summary expression link. | The raw historical artifacts do not preserve enough per-attempt expression/effect detail to reconstruct this funnel stage. The gap is reported rather than imputed. |

## Barrier disposition and next entry

The measured barriers support exact-effect deduplication and a reserved transfer allocation within the existing 120,000 cumulative attempt ceiling. The proposed first P26 development experiment caps new work at 60,000 attempts: 40,000 ordinary discovery plus a 20,000 transfer reserve across four training goals. From the inspected immutable 20,000-attempt Loopover g1 checkpoint this yields at most 80,000 cumulative attempts, below the existing ceiling. P23 does not run that proposed experiment or claim it will improve performance.

The exact-effect feasibility findings do not justify a larger search ceiling. A future read-only optional attempt export is specified for expression/effect linkage; it must remain disabled by default and cannot feed diagnostic witnesses into the agent graph. The malformed historical qualification on D4 candidate `#9459` remains excluded and does not count as a valid qualification.

**P22 disposition:** keep `COGNITION_LINEAR_P22_PREREG.md` as `DRAFT — NOT FROZEN`. Its candidate descendant manifest and resource gates remain incomplete, and the two candidate-specific requests remain independent decisions. No validation or held-out IDs were used. P22 is not proved impossible; it is not currently freeze-ready.

**P24 entry:** proceed with the new common-target learner work. P24 is a separately specified implementation/evaluation path that addresses P20's unequal assimilation paths. It does not consume P23's finite witnesses as agent knowledge and does not change P20's negative result. Phases 25–27 remain gated in canonical order; P26 must implement the measured search repairs before P27 decides original P22 re-entry versus a versioned successor.
