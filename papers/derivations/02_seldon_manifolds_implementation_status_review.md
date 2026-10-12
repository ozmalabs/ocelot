# Seldon manifold implementation-status review

Reviewed 12 October 2026. Updates Paper 02 to revision 33 and Paper 02a to revision 16.

## Finding

Paper 02 described the construction as implementable without documenting the software instance. Paper 02a's abstract said “the composite is not”, and its limitations said “the composite is not evidenced”. Their context is biological, but the abbreviated wording could imply no constructed composite exists. Retain the biological limitation explicitly and add a separately scoped software status section to Paper 02.

## Source evidence

| Paper statement | Inspected implementation | Scope |
|---|---|---|
| Finite coordinate projection and signed escape residuals | `runners/dsl/src/future_manifold.rs::projection_field` | Caller supplies geometry, dimensions and candidates; no complete future-family discovery |
| Support, resolution, assessed loss and unassessed cells are distinct | Same function, aperture mask and horizon/budget accounting | Escape can decide exclusion before complete coverage; retention needs coverage |
| Candidate deformation records and per-dimension counting | `reachable_deformation_set`, `counting_narrativium_by_dimension` | Deduplicates supplied traces; admissible family bound, not exhaustive/selectable reachability; no universal measure |
| Feasibility, minimum intervention, goal ordering and withholding | `feasible_selection`, `feasible_selection_with_projector` | One supplied policy; ties retained; missing feasible intervention valuation rejects the selection |
| Connected graph and application interfaces | `runners/dsl/src/term.rs` projection/selection arms; `runners/dsl/src/py.rs::feasible_selection`; `runners/dsl/src/p4_readiness.rs` | Callable implementation, not a claim every application uses every feature |
| Temporal adaptation and conservative enclosures | `runners/dsl/src/motor_compose.rs`, interval certification and subdivision | Inspected path explicitly declares first-order certification, not general order N |
| Finite structural tube representation | `domains/future_option_risk.py`, `ShapeSlice`, `FutureManifold`, `evaluate_future_manifold` | Separate finite representation with identified cells/links; do not conflate its information residual with the generic auditor's unassessed-cell count |
| Existing verification cases | `tests/test_future_manifold_projection_native.py`; unit modules in `future_manifold.rs` | Read only. No tests were executed for this update |

One comment preceding `reachable_deformation_set` says selection machinery does not exist. That comment is historical: implemented selection functions follow it in the same file and are called from other modules. The paper relies on the inspected functions and call sites, not that stale comment. No implementation changes are included in this manuscript task.

The general coordinate auditor accepts machine numeric coordinates; it does not itself establish every adaptive quantisation or dimension-instantiation claim in the theory. An aperture mask over supplied slots is not universal dimension discovery. Candidate counting uses represented numeric identity, not an independently calibrated equivalence relation over all possible futures. Muchness and Narrativium remain different quantities; these functions provide a particular candidate deformation counting grounding rather than prove their identity.

## Recorded run evidence

Inspected the local `results/future_manifold_path_abs_f16_paired_v5/README.md` and retained comparison artifact alongside `docs/research/flight_control/FUTURE_MANIFOLD_ABS_F16_PREREG.md`. The results directory is not tracked in Git. It remains an internal record, not a public reproducibility package; no raw results or executable substrate are added to the paper release.

The record reports three paired episodes, each 1,000 steps, completed in both arms. Its aggregate metrics show both improvements and regressions. It explicitly limits its temporal claim: 2,697 ordinary treatment decisions found an earliest escape at horizon one, and the remaining reported decision was a single-action probe. This supports deployment of the dense projection gate within that experiment, not extended retained trajectories or sparse/adaptive-order performance. The later sparse implementation and its verification source must not be retroactively attributed to that earlier run.

No new experimental run, independent reproduction, human validation, or universal performance claim was made. Paper 02's formal and empirical falsifiability commitments remain intact. The source review establishes present construction; it is not a proof of model correctness or safety in all inputs.

## Evidence fingerprints

SHA-256 at inspection:

```text
2ac72e630db37169a10672d6e9c0b199ec145efbe6be011790deab4a23c9f021  runners/dsl/src/future_manifold.rs
057981a362653d9de6f249eb2da2674d473e247fd27f244875292d810ea8c8e2  runners/dsl/src/motor_compose.rs
63ea7ca9cd44226fd1b04a356470c87d7aa816d825fe2c5e3fe7d17fe265e786  domains/future_option_risk.py
3fa2da267279d9fd9a93ec13e5b08bb35f6c667293bacb0b77de2cc33835d666  tests/test_future_manifold_projection_native.py
2bd36dca2140096389f04de34a1cc24a16a6a5d669f45d07858f04da1375ce96  results/future_manifold_path_abs_f16_paired_v5/README.md
cbfc43c2cdd8a34f683ff748db683bec566eea988afef2219c7fb30929479b8d  results/future_manifold_path_abs_f16_paired_v5/comparison.json
```
