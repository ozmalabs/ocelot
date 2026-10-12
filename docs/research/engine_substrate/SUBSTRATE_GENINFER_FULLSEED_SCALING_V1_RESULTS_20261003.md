# Full-seed GenInfer scaling v1 results (2026-10-03)

## Outcome

The 84-worker source-locked capture passes all preregistered integrity and
behavior gates. Across 60 positive cases (N=4, 8, 16, 32, 64 relations; B=3,
4, 5, 6; three repeats each), the full-seed rule closure acquired the exact
linear generator during training and reused it on a distinct held-out
signature in **60/60** cases. Disabled controls acquired no target generator
(0/12). All predicate-corrupted training controls refused acquisition
(0/12); each settled as `minted`, not `recognized_transformed`.

The coordinate-perturbed held-out control shows a different and informative
behavior: **60/60** were classified `recognized_transformed`, but none
matched the exact matrix-only oracle. Each receipt named the acquired matrix
and recorded a local `shift(+1)` residual on the corrupted relation. The
substrate therefore accepts a generator-plus-residual explanation while
preserving the mismatch in graph data; the result must not be summarized as
exact recovery of the corrupted target.

## Scaling measurements

The locked matrix family `[B-1,1,1,1]` gives candidate volumes of `(2B+1)^4-1`
per eligible 2-D codebook part. In this run there is one eligible training
part. Median **training closure wall time** in milliseconds is:

| Relations N | B=3 (2,400) | B=4 (6,560) | B=5 (14,640) | B=6 (28,560) |
|---:|---:|---:|---:|---:|
| 4 | 10.1 | 25.6 | 55.8 | 106.2 |
| 8 | 19.7 | 50.6 | 111.8 | 223.3 |
| 16 | 41.0 | 105.8 | 229.9 | 468.9 |
| 32 | 77.0 | 205.9 | 459.5 | 862.0 |
| 64 | 154.6 | 406.3 | 928.8 | 1,776.8 |

Within this measured range, acquisition cost grows approximately with
`N × ((2B+1)^4-1)`: median time per relation-candidate unit is 982 ns (range
923–1,287 ns). At N=64, increasing B from 3 to 6 raises median acquisition
time about 11.5× while candidate volume rises 11.9×. At B=6, increasing N
from 4 to 64 raises time about 16.7× for a 16× relation increase. The maximum
training closure is 1.78 s at N=64, B=6. For that cell, median held-out reuse
is 4.67 ms, roughly 380× cheaper than acquisition. Across the panel, median
held-out closure is 1.56 ms and the maximum is 6.32 ms.

Measured closure CPU time closely tracks wall time. Process high-water RSS
increased by 764–1,152 KiB across individual closures, with 960 KiB median.
This is a coarse process-level peak delta; it excludes memory already resident
after boot and does not measure allocator-specific peak usage. Graph nodes
remain almost constant because relation signatures are stored in attributes;
their serialized input size grows with N. Thus the time sweep captures
relation comparison work better than the graph-node count does.

## Interpretation and limitations

This supports a measured tractability envelope for one substrate operation:
within this synthetic 2-D family and tested bounds, full-seed acquisition
tracks the fourth-power matrix search multiplied approximately by relation
count, while reuse is much cheaper after minting. It also directly measures a
known semantic boundary: local residuals can preserve recognition under one
coordinate corruption, whereas the predicate-corruption control is refused.
The timings cover the native rule-settle closure only, not process startup,
core boot, data generation, memory serialization, or a natural task stream.
Only one eligible 2-D codebook part and one matrix family were measured;
higher dimensions, many simultaneous frames, broader nulls, and actual peak
memory remain open.

## Artifacts

- [Preregistration](SUBSTRATE_GENINFER_FULLSEED_SCALING_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_fullseed_scaling_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_fullseed_scaling_v1_20261003.json)
- [Analysis](../../../evaluation/reports/substrate_geninfer_fullseed_scaling_v1_analysis_20261003.json)
