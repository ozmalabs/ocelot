# Full-seed GenInfer scaling v1 preregistration (2026-10-03)

## Question

How do full-seed GenInfer acquisition and held-out reuse costs change with
relation count and the data-derived integer-matrix bound, and how often does
the path accept structured perturbations as explained transformations?

## Scope and task selection

The direct native-Term sweep already measures the kernel's fourth-power
candidate growth through B=12, but omits graph closure, generator minting,
re-decode, and relation-count variation. This panel measures those full-seed
stages on fresh processes. It is still one authored synthetic 2-D linear
operator family and does not support a general substrate complexity claim.

Before this preregistration, one-run task-development probes using the v2
runner tested `[B-1,1,1,1]` for B=3,4,5,6. All four were acquired and reused
on the v2 four-relation fixture. Those probes selected a scaling family and
are not counted as confirmatory evidence. Relation count is varied separately
by adding uniquely labelled relations over a fixed four-point training
geometry, so the coordinate-derived bound remains the declared B. The target
matrices are locked as `[B-1,1,1,1]`.

## Design

There are 60 positive workers: relation counts N in `{4,8,16,32,64}`, bounds
B in `{3,4,5,6}`, and three repeats per cell. Each fresh process boots the
production core and `shape_decode_loop`, observes the N-relation training
transform, records graph growth and resource use, then adds a distinct
held-out base/target signature and applies the learned generator. It also
observes a corrupted held-out target with one coordinate changed. Every
positive worker therefore reports acquisition, clean transfer, and
perturbation handling.

There are 24 control workers: three GenInfer-disabled controls and three
one-relation predicate-corruption controls at N=8 for each B. The controls
are diagnostic: disabled runs test acquisition dependence on the learner;
predicate-corrupt training tests whether a non-exact observation is accepted
as a generator-plus-residual explanation. The evaluation does not assume all
non-exact residual explanations are errors. It records exact oracle agreement,
recognition status, route receipts, and residuals separately.

The GenInfer search enumerates `(2B+1)^4-1` nonidentity 2×2 integer matrices
per eligible codebook part. The runner records that derived kernel work
volume alongside native rule-closure work, wall time, process CPU time,
process peak RSS before and after closure, and graph size. Each case runs in a
fresh process; peak RSS delta is a process high-water estimate, not an
allocator-specific or system-wide peak-memory measurement.

## Locked gates

1. Exactly 84 unique cases run, with three repeats for each of the 20 positive
   N×B cells and each declared control arm.
2. Every worker is source/native stable against the lock and runs in its own
   process.
3. Every positive target is absent from the initial linear-generator
   inventory, acquired during training, and attributed on the distinct
   held-out receipt; exact held-out outputs match the locked matrix.
4. Disabled controls acquire no target generator. Predicate-corruption and
   corrupted-heldout outcomes are reported without silently treating a
   decomposed residual as exact matrix recovery.
5. For every case the runner's derived per-part candidate count equals the
   locked formula; all timing, CPU, RSS, and graph-size fields are present and
   nonnegative.

The scaling study passes only if all five gates pass. Performance trends and
false-acceptance rates are descriptive, not post-hoc pass criteria. No
outliers or failed cases will be excluded. Any workload or criterion change
requires a new version and lock.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_fullseed_scaling_v1.py`
- Source lock: `evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1_lock_20261003.json`
- Raw capture: `evaluation/reports/substrate_geninfer_fullseed_scaling_v1_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_fullseed_scaling_v1_analysis_20261003.json`
