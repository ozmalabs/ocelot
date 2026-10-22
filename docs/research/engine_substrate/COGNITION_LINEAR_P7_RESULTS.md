# Linear P7 results — mechanism panels and limits

Status: frozen P7 held-out draw reported. This report preserves fixture results and explicitly separates them from perceptual or behavioral capability claims.

## Provenance

The preregistration is [`COGNITION_LINEAR_P7_PREREG.md`](COGNITION_LINEAR_P7_PREREG.md), frozen at `60546572`. The runner metadata reports engine commit `605465728e320cde6d1321853419e8fea6d1d988`, source bundle SHA256 `abc5004efbd0d7a2af516a75b0de3fc00f6ae76993d0a0e637592767a9d3fc7a`, engine source bundle `516e30d5902c21b683f90e9ff7d1251f85b2e451256ccafaced094271cdd4749`, and native binary `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`. The draw used Python 3.13.5 and completed all 1,760 rows.

Raw artifacts are outside the repository:

- `/tmp/linear-p7-heldout.json` — SHA256 `f45da0922ab84e2c2e72d605cc4490d1499ff8a7499de4b458b6640b3a973177`.
- `/tmp/linear-p7-analysis.json` — SHA256 `83e09dff16577199c643dfc5a0760e0b02ef7fa1d21456d173c3d4ea421c42c2`.

Every row completed; there were no missing adapters, unsupported rows, timeouts or source-leak flags. The pre-draw self-check and analyzer self-check passed.

## Results

| Panel | Frozen space | Experience-built / mechanism result | Classification |
|---|---:|---:|---|
| Tool/contact candidate validation | 0/40 | 40/40 | `MECHANISM_PASS`; not downstream transfer |
| Social request/repair candidate validation | 0/40 | 40/40 | `MECHANISM_PASS`; not downstream transfer |
| Tool label-shuffled controls | — | candidate in 100/100; labels detached | `MECHANISM_PASS`; scorer labels did not enter graph |
| Social label-shuffled controls | — | candidate in 100/100; labels detached | `MECHANISM_PASS`; scorer labels did not enter graph |
| Tool exposure-only controls | — | no candidate in 100/100 | `MECHANISM_PASS` |
| Social exposure-only controls | — | no candidate in 100/100 | `MECHANISM_PASS` |
| Tool orthogonal controls | — | no candidate in 100/100 | `MECHANISM_PASS` |
| Social orthogonal controls | — | no candidate in 100/100 | `MECHANISM_PASS` |
| Clear small-set comparisons | — | 200/200 fixture relations correct | `MECHANISM_PASS`; perceptual accuracy `NOT_ESTABLISHED` |
| Ratio 1.1 | — | 200/200 fixture relations correct | `MECHANISM_PASS`; perceptual accuracy `NOT_ESTABLISHED` |
| Ratio 1.25 | — | 200/200 fixture relations correct | `MECHANISM_PASS`; perceptual accuracy `NOT_ESTABLISHED` |
| Ratio 1.5 | — | 200/200 fixture relations correct | `MECHANISM_PASS`; perceptual accuracy `NOT_ESTABLISHED` |
| Ratio 2.0 | — | 200/200 fixture relations correct | `MECHANISM_PASS`; perceptual accuracy `NOT_ESTABLISHED` |
| Equal-ratio scale comparison | — | 0 percentage-point difference for every bin | `MECHANISM_PASS`; synthetic signals only |
| Source/grounding leaks | — | 0 across all 1,760 rows | `PASS` for this fixture audit |

The candidate-creation panel uses the same five observed episodes in both arms. The experience-built graph reaches validated status after three recurrence witnesses and two fresh contexts. The frozen-space profile receives the same evidence but its acquisition policy remains off. Label-shuffle controls attach annotations only to detached scorer data; they do not change the source evidence, and the graph still acquires from the observed feature/outcome relation. Exposure-only and orthogonal controls remain candidate-free.

Numerosity rows use synthetic area and density signals supplied directly by the fixture adapter. The native rules apply the frozen aggregate interval comparison and small-set token comparison. The 100 scale-1 and 100 scale-10 comparisons in each ratio bin returned the same outcome, giving a 0-point difference. These inputs are not camera images, calibrated sensor readings or human trials; the proposed 95% and 75% thresholds are therefore not established as perceptual capability claims.

## Criteria and next entry

The planned ≥20 percentage-point later-task transfer criterion is `NOT_ESTABLISHED`: neither profile includes a downstream action or prediction consumer that uses the learned axis. Candidate validation is only acquisition-mechanism evidence. The proposed perceptual numerosity thresholds are also `NOT_ESTABLISHED` beyond the synthetic mechanism fixture. No human comparison was available. These limits do not invalidate the observed graph-rule acceptance and source-isolation results.

Phase 7 authorizes Phase 8 only for source-bound observed episode learning and the supported acquired-axis interface. Phase 8 must not assume a calibrated visual model, downstream acquired-axis behavior, standing significance learning, general finer-grain search, or candidate retirement. These remain explicit open criteria rather than inferred capabilities.
