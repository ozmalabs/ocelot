# Bigville owner-frame and boundary-index construction/update cost preregistration

**Lock date:** 2026-09-26, before capture. **Question:** on the same 100-resident Bigville graph and ring/star/random-connected link sequence as the locked dynamic-boundary study, what is the host-side cost to rediscover owner frames, rebuild the boundary index, and incrementally update it as links change?

## Design

Use `bigville_cast100.json`, the authored CAN builder, and the same baseline CAN rule family as the source capture. Each fresh process builds a full authored graph and derives 100 runtime owner frames of five Concepts each. Then it inserts 100 ring or random-connected links, or 99 star links, at the `world_safe` Concept of each endpoint resident; removes one third; reweights the remainder; reinserts removed links; and removes all links. There are three deterministic link topologies × three fresh-process replicates = 9 workers. This is a structural-cost probe; it does not run closure and does not estimate natural cross-resident topology frequency.

Partition semantics are fixed by live `has_concept` Microtheory ownership. The linked study's baseline `causal_influence` component discovery is repeated at baseline only as an invariant check; after cross-resident links, those graph components would merge and are not used as the owner-frame definition. Each mutation is applied to the native graph and to the caller-side directed-edge / weight projections used by the source boundary queue.

## Timed operations

Each worker records:

1. Full graph build and initial runtime-component verification time (combined; loading and graph construction cannot be separated in the existing builder).
2. Repeated live owner-map discovery via `has_concept` (median of 31 calls) at baseline and all six subsequent checkpoints; each map must equal the original 100-frame owner map.
3. Full boundary-index rebuild from the current live owner map and directed edge projection (median of 31 rebuilds per checkpoint).
4. Incremental boundary-index update from the previous checkpoint's index for insert, delete, reinsert, and remove-all operations (median of 31 cloned-index update batches). Reweighting does not change topology, so the preregistered index update is empty and must preserve equality.
5. Raw graph/array mutation time, recorded separately from index work; this includes native edge API calls and caller projection/list updates.

The boundary index reports directed and undirected cross-frame edges, boundary Concept IDs per owner frame, per-frame cross-link degree, and owner-pair edge multiplicities. Incremental and rebuilt structures must match exactly at every checkpoint. The trial count is fixed at 31 after one warmup. These in-process medians are construction/update micro-measures, not closure latency or total application cost.

## Integrity and interpretation gates

Require 9 workers and unique PIDs; 100 frames × five Concepts and a bijection to live Microtheory owners; zero baseline cross-frame edges; correct topology link counts; exact mutation/checkpoint sequence; 7 checkpoint profiles per worker; exact incremental/full rebuild parity for every field; exact owner-map parity after every mutation; native/source/lock hashes; and no stale native build. Construction/update timings are outcomes, not pass thresholds. Preserve all per-worker timings and profiles. Report medians and ranges across three processes and label timing uncertainty.

No closure, state parity, notification completeness, boundary-conditioned factorisation, or natural-task prevalence claim follows from this probe. The source dynamic-link capture remains the semantic control and retains its full/event/omission outcomes.

## Provenance and execution

The runner lock covers this protocol, runner/analyzer, v3.1 graph/partition builder, cast/seed/world builder, engine source, and installed native extension. Save exact `--lock` JSON to `evaluation/substrate_capability/bigville_boundary_index_cost_lock_20260926.json` before execution. Output is separate from the original dynamic-link capture.

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_bigville_boundary_index_cost_v1.py --lock
# Save exact JSON to evaluation/substrate_capability/bigville_boundary_index_cost_lock_20260926.json
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_bigville_boundary_index_cost_v1.py
python3 scripts/analyze_substrate_bigville_boundary_index_cost_v1.py
```
