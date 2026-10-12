# Exact-linear GenInfer prefilter v1 results (2026-10-06)

## Outcome

The source-locked three-build panel completed all 480 workers with no worker
failures. The independent analyzer passed all 15 integrity, oracle,
acquisition/transfer, counter-conservation, and semantic-parity checks. Source
and native binary hashes stayed stable throughout capture. The schedule used
eight authored conditions, ten repeats, three native builds, and audit on/off.

For every condition, held-out rows matched the independent integer-map oracle.
Quadratic acquisition and reload/transfer passed on the registered positive
conditions; no false quadratic mint appeared in the controls. The prefilter
build matched the quadratic-only build semantically, and audit-on/off
projections matched for all three builds.

## Measured work and cost

The prefilter arm recorded 280 attempts in its 80 audit-on workers: 30 exact
solves, 220 proven no-fits, and 30 conservative fallbacks. The proof reasons
were relation-count mismatch (140) and row residual (80). Fallback reasons
were missing identity match (10), duplicate/ambiguous identity (10), and rank
deficiency (10). It counted 3,620 typed-key `Value` comparisons and 10,960
checked arithmetic primitives. Attempt outcomes and reason totals conserve
exactly.

Clean closure time is the median of training plus held-out closure across ten
audit-off repeats. Values below are milliseconds; speed ratios compare each
baseline with the prefilter arm.

| Condition | Feature off | Quadratic only | Prefilter | Off / prefilter |
|---|---:|---:|---:|---:|
| Linear positive | 78.3 | 80.8 | 2.5 | 31× |
| Coupled quadratic | 7,861.5 | 13,735.3 | 2.4 | 3,229× |
| Quadratic cross term | 158.9 | 169.9 | 2.6 | 62× |
| Corrupted training | 7,989.9 | 8,001.6 | 1.3 | 6,162× |
| Cubic out of family | 7,200.4 | 7,188.9 | 1.4 | 5,328× |
| Duplicate identity | 7,951.4 | 7,998.8 | 3,008.6 | 2.6× |
| Missing identity | 8,820.4 | 9,020.7 | 3,879.4 | 2.3× |
| Rank deficient | 111,052.1 | 112,634.8 | 70,221.9 | 1.6× |

These are large gains on this bounded benchmark, explained by the prefilter
proving most eligible bases cannot fit before the legacy matrix enumeration.
Where identity is ambiguous or source rank is deficient, the conservative
fallback remains expensive. The 30 exact solves are all in the linear-positive
condition; the no-fit path, rather than broad new induction, accounts for most
of the measured reduction. This result does not show that arbitrary graph
matching or rung-three learning is tractable.

## Reproduction artifacts

- Preregistration and amendments: [v1 preregistration](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_PREREG_20261006.md), [v1.1](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_1_AMENDMENT_20261006.md), [v1.2](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_2_AMENDMENT_20261006.md), [v1.3](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_V1_3_AMENDMENT_20261006.md)
- [Source lock](../../../evaluation/substrate_capability/geninfer_exact_linear_prefilter_v1_lock_20261006.json), SHA-256 `ece2d50b6925b25899a9bd56792cc9929825a9b6b8eba50a6b84a6efb48db59a`
- [Raw capture](../../../evaluation/reports/geninfer_exact_linear_prefilter_v1_raw_20261006.json), SHA-256 `6ba0df0f79611571fc31edda480725280b72cd5a8ea71aad28c95eda4105cd1d`
- [Independent analysis](../../../evaluation/reports/geninfer_exact_linear_prefilter_v1_analysis_20261006.json), SHA-256 `fb1e2dc5a0943cf04e90d16edf7e84b3a4c0c70710d387df5ffa3aa8d56da0c5`
- [Runner](../../../evaluation/substrate_capability/geninfer_exact_linear_prefilter_v1.py) and [analyzer](../../../evaluation/substrate_capability/analyze_geninfer_exact_linear_prefilter_v1.py)
- [Finite differential oracle result](SUBSTRATE_GENINFER_EXACT_LINEAR_PREFILTER_ORACLE_V1_RESULTS_20261006.md)

The capture took 7,946 seconds of runner time. This is dominated by the
feature-off and quadratic-only baselines on conditions that force exhaustive
matrix search, especially rank-deficient geometry. That cost is part of the
measured comparison and should not be confused with prefilter runtime.

## Next questions

1. Expand beyond these authored 2-D integer fixtures to independently sourced
   structures and larger relation sets, retaining a matched historical-search
   baseline.
2. Measure how often natural workloads present the complete typed identity
   join and full-rank coordinate basis needed for the fast exact solve.
3. Optimize or bound the expensive fallback path, especially rank-deficient
   frames, while preserving the conservative behavior verified here.
4. Keep rung-three hypothesis induction and open-ended primitive minting as
   separate unresolved capability questions; this panel does not address them.
