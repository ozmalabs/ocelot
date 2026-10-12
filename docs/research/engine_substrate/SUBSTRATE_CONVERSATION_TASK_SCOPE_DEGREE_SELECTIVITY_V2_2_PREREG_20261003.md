# Conversation matcher degree and partial-selectivity v2.2 preregistration

Date: 2026-10-03  
Status: preregistered before implementation and capture.  
Prior evidence: [verified v2.1.1 selectivity result](SUBSTRATE_CONVERSATION_TASK_SCOPE_SELECTIVITY_V2_1_RESULTS_20261003.md)

## Question

Does declared-anchor pruning retain its work advantage when irrelevant patterns have different relation degrees or are only partial matches, and which pattern relation drives the avoided work?

## Workload construction

Retain the v2.1.1 conversation panel, exact state/trace gates, source isolation fix, and cross-frame/orphan controls. Add unowned Goal/Event decoys to the two-goal task in these profiles:

- `isolated_complete`: 256 complete four-edge decoy components, each with its own Event.
- `shared_event_complete`: 32, 256, or 1,024 decoy Goals share one Event. Instantiate the four pattern relations; `state has_event event` is one shared edge and `event for_goal goal` has high out-degree. Every Goal remains lifecycle-ineligible.
- `missing_has_active_goal`, `missing_originated_in`, `missing_has_event`, and `missing_for_goal`: 256 decoy Goal/Event pairs per profile, with exactly the named relation omitted.

Retain the four existing aligned zero-decoy baselines and two ownership controls. Run three workers per each of three scope orders: 14 paired cases per worker, 126 paired cases total. Add decoy nodes and edges identically before closure in all four arms. They have no frame membership and no lifecycle rule may transition them.

## Measurements and gates

- The runner and independent analyzer must both verify the fallback arm has zero declared-anchor attempts and zero anchor-proof rejections, and positive full-fallback calls.
- Require exact checkpoint/final graph parity, lifecycle equality, trace-on/off equality, nine fresh workers, source stability, and control guard rejection.
- Attribute expansion calls and Candidate pairs by semantic rule edge; also report Candidate and Term totals, per-profile reductions, monolithic ratios, and wall time as secondary data.
- Report each nonzero profile separately. Claim robust benefit only if both Candidate and Term totals are lower for every profile cell than verified fallback. A failed profile is a boundary result, not grounds to drop the profile.

## Interpretation boundary

This controlled panel tests matcher sensitivity to relation degree and partial pattern structure. It is not sampled from natural tasks and cannot establish natural cheap-cut prevalence or general tractability. The shared-event profile deliberately violates the discourse rule's unique-event-owner predicate only for lifecycle-ineligible decoys; exact state parity is required to confirm these decoys remain inert.
