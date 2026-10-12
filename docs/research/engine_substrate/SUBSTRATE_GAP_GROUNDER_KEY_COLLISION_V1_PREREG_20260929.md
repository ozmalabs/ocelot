# Gap-grounder key collision v1 preregistration

**Date:** 2026-09-29. **Question:** when two structurally different `CapabilityGap` observations use the same faculty label, does `substrate_extension.extend_for_gap` reuse the first induced axis/grounding, and does that change the second gap's downstream result?

## Frozen cases

Use the public `WorldAdapter(seeds=())` + `extend_for_gap(..., verify=True)` path. Both gap fixtures have faculty label `shared_family`, so current source derives `name_hint="gap_shared_family"` for each.

- **A — composable handling chain:** three observation clauses: classify an item, route it to a handler, mark it handled. This mirrors the existing `test_substrate_extension.py::_compose_gap` fixture, with only its faculty label fixed to `shared_family`.
- **B — spectral computation:** two clauses (`spectral_value`, `log_scale`) and metadata `needed_primitive=spectral_value`, `n_samples=32`, `test_frequencies=[3,7,11]`, `inputs=[signal]`, `outputs=[spectrum]`, and the existing log-magnitude example. This mirrors `_spectral_gap`, with only its faculty label fixed to `shared_family`.

Run six fresh-graph sequences: isolated A, isolated B, A→A, B→B, A→B, and B→A. Each sequence is booted independently. Within a sequence, create a new `CapabilityGap` for each call and invoke the actual `extend_for_gap` entry point. Do not suppress the second call after the first accepted the first gap.

## Measurements

Record for each event: exact gap observation and attrs; derived `name_hint`; returned outcome/path/concern key; composition/primitive result and verification verdict; all newly added `CapabilityAxis`, `PrimitiveRequest`, `HeldPrimitive`, `Observation`, and `CapabilityGap` nodes; current rule names; axis mint/dedup/transform edges; gap status; `codebook_epoch`; native steps and wall/CPU time. Preserve first- and second-call graph snapshots or complete relevant node projections.

Primary comparisons are (a) isolated B versus B in A→B and B→A versus isolated A, and (b) exact repeats A→A/B→B. Verify source code derives the same hint for A and B, and verify A and B input signatures are structurally distinct. Report behavior without labeling a shared key harmful unless the downstream result changes relative to the isolated control or suppresses a distinct warranted axis.

## Gates and claim boundary

1. Six fresh graphs and ten total `extend_for_gap` calls complete under identical pre/post source locks.
2. A and B have the same `name_hint`, distinct observation signatures, and each isolated control reaches a terminal outcome.
3. Report all status/axis/outcome differences; retain incomplete/rejected cases.
4. Do not claim general composer reliability, global key collision rates, or natural gap distributions from these two authored fixtures.

## Lock and reproduction

Lock this protocol, runner, adapter, `substrate_extension`, `reflective_faculty`, relevant seed manifests, native evaluator source/binary/build metadata, fixed fixtures, and current git head before execution. Require identical pre/post locks.

```sh
python3 evaluation/substrate_capability/gap_grounder_key_collision_v1.py --lock
python3 evaluation/substrate_capability/gap_grounder_key_collision_v1.py
python3 evaluation/substrate_capability/analyze_gap_grounder_key_collision_v1.py
```
