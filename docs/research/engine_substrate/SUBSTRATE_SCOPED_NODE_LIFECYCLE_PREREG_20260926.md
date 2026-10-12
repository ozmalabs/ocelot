# Scoped native node-lifecycle notification preregistration

**Lock date:** 2026-09-26, before the diagnostic capture  
**Question:** Do native scoped write reports notify every owning Microtheory when a scoped rule creates an owned node with a cross-frame dependency edge, or deletes that node and its incident cross-frame edge? Does consuming those notifications preserve the full-closure result?

## Fixture

Construct two Microtheories, A and B, each owning one Concept. A has a one-shot mint trigger; B starts with integer state 0. Three graph-authored rules implement the state transition:

1. In response to A's trigger, mint one new A-owned Concept, connect it to B's Concept by a directed `causal_influence` edge, and mark the trigger consumed.
2. In B's frame, set B's state to 1 when it has an incoming `causal_influence` edge and its state is 0.
3. In B's frame, set B's state back to 0 when it has no incoming `causal_influence` edge and its state is 1.

The event worker begins each external intervention with A in its queue, calls `run_rules_scoped_delta_report`, and enqueues every reported affected Microtheory not already queued. It repeats until the queue is empty, failing on deferred effects, unknown owners, or the progress cap. After minting, the worker sets a deletion request on the new A-owned Concept and starts another queue settlement at A. The deletion rule removes that node, its ownership edge, and the cross-frame influence edge.

## Arms and checks

- **Full reference:** run monolithic native closure after the mint trigger, then after the deletion request.
- **Native event queue:** execute the two interventions with scoped delta reports and queue only their reported Microtheory owners, starting each intervention at the externally mutated A frame.
- **Omitted initial seed:** do not queue A for the initial trigger. The resulting projection must fail to match the full reference, proving that the trigger is causally effective.

Required checks: birth and deletion each produce the expected exact owner set `{A,B}`; the event and full arms agree on minted-node count, ownership, cross-frame edge presence, A's consumed trigger, B's state, terminal fixed-point status, and zero outstanding queue/deferred work; the omission arm remains detectably stale after the initial intervention. Candidate/Term counts may be reported but are not success criteria. The runner uses fresh native substrates for each arm and hashes its source, preregistration, native library/build record, and Rust mutation/reporting paths.

## Claim boundary

This is a controlled two-frame rule/effect mechanism probe. It tests rule-authored node birth and deletion, ownership-edge changes, incident-edge mutation logging, owner mapping, and queue consumption. It does not establish automatic discovery of the initial externally mutated frame, arbitrary effects such as rule edits or deferred framebuffer work, runtime partition rebuilding after a frame root itself is deleted, general scheduler correctness, natural workload prevalence, or a scaling/runtime advantage.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_node_lifecycle_probe_v1.py
python3 scripts/analyze_substrate_scoped_node_lifecycle_probe_v1.py
```
