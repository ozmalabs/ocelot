# Linear P7 evaluation preregistration v1

Status: frozen before the held-out draw. The runner evaluates episode-grounded acquisition and synthetic sensor-signal numerosity mechanisms. It does not establish human perceptual accuracy or downstream behavioral transfer.

## Frozen artifacts and provenance

- Phase: `linear-p7-v1`; runner `evaluation/process_mastery/linear_p7_v1.py`; analyzer `evaluation/process_mastery/analyze_linear_p7_v1.py`.
- Freeze commit: `7109f46f1ed8cad9447ebe02742c7d139584c977`.
- Runner SHA256: `b52e7034cc941cb18c2d0cddc312bbc71ac24be8751277e6a6da50d8253facd5`.
- Analyzer SHA256: `2c60c2a516cfb0a2bbec82a6ba9a1cd0d74ae29862e73fb4d9946b91e18f56f0`.
- Profile/seed/contract bundle SHA256: `abc5004efbd0d7a2af516a75b0de3fc00f6ae76993d0a0e637592767a9d3fc7a`.
- Engine source bundle SHA256: `516e30d5902c21b683f90e9ff7d1251f85b2e451256ccafaced094271cdd4749`.
- Native engine binary SHA256: `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`.
- Development self-check scorecard SHA256: `49545432e6fec5b160770ad209bdf5a61ead6b559d145eb55aade577249c1348` (outside git at `/tmp/linear-p7-dev-selfcheck.json`).
- Runtime: Python 3.13.5. Rule fixpoint cap: 2,000 steps; 30 outer iterations. Small-set cap: four objects; perceptual input cap: 4,096 regions; declared graph cap: 512 objects.

The development runner and analyzer self-checks passed. Seven development rows produced concrete outcomes: baseline and experience-built tool/contact, shuffled-label, exposure-only, orthogonal, small-set, and ratio-comparison adapters. The held-out allocation is fixed below. The source bundle hash is checked by the runner metadata; any source change invalidates this freeze and requires a new version, not a silent rerun.

## Allocation

Use split `heldout` and exactly 200 per registered scene/comparison bin. Seed intervals are non-overlapping:

| Panel | Seeds | Allocation |
|---|---:|---:|
| Tool/contact acquisition | 2,000,000–2,000,039 | 40 candidate trials × 5 observed episodes = 200 episodes per arm |
| Social request/repair acquisition | 2,000,040–2,000,079 | 40 candidate trials × 5 observed episodes = 200 episodes per arm |
| Tool label-shuffled controls | 2,000,080–2,000,179 | 100 three-episode bundles |
| Tool exposure-only controls | 2,000,180–2,000,279 | 100 three-episode bundles, without outcome receipts |
| Tool orthogonal controls | 2,000,280–2,000,379 | 100 three-episode bundles with no recurring feature→outcome mapping |
| Social label-shuffled controls | 2,000,380–2,000,479 | 100 three-episode bundles |
| Social exposure-only controls | 2,000,480–2,000,579 | 100 three-episode bundles, without outcome receipts |
| Social orthogonal controls | 2,000,580–2,000,679 | 100 three-episode bundles with no recurring feature→outcome mapping |
| Clear small-set comparisons | 2,001,000–2,001,199 | 200 graph comparisons; hidden cardinalities are scorer-only |
| Ratio 1.1 | 2,001,200–2,001,399 | 200 aggregate comparisons |
| Ratio 1.25 | 2,001,400–2,001,599 | 200 aggregate comparisons |
| Ratio 1.5 | 2,001,600–2,001,799 | 200 aggregate comparisons |
| Ratio 2.0 | 2,001,800–2,001,999 | 200 aggregate comparisons |

Each ratio bin splits evenly between scale 1 and scale 10, with equal area ratios and the same density signal. The experience-built and frozen-space arms receive the same owner-scoped five-episode sequence, action IDs, source/model/frame epochs and 2,000-step rule cap. The graph receives no target dimension, expected class, hidden count or shuffled scorer label. Shuffled labels remain only in detached scorecard data.

## Measures and decision rules

1. **Acquisition mechanism:** report proposal/adoption, source-receipt agreement, and candidate status in each arm. Controls require zero candidates for exposure-only and orthogonal evidence. Label-shuffled labels must not alter graph outcomes or enter graph nodes. Count source/grounding leaks; any nonzero leak fails the safety criterion.
2. **Transfer benefit:** the build plan's proposed primary remains ≥20 percentage points on a later task requiring the acquired distinction over frozen space under identical experience and compute. This runner has no downstream action-selection/prediction adapter that consumes acquired axes. Therefore this criterion is preregistered as `NOT_ESTABLISHED` for this draw; candidate validation rate is a mechanism measure and cannot substitute for transfer.
3. **Small sets:** score exact relation against detached exact cardinalities and report coverage and abstentions. Proposed criterion: ≥95% on clear small-set inputs.
4. **Approximate ratios:** report accuracy and coverage for each bin. Proposed criterion: ≥75% at ratios ≥1.5, with results for 1.1 and 1.25 retained regardless. Compare relation accuracy between scale-1 and scale-10 conditions within each equal-ratio bin; proposed maximum difference is 10 percentage points.
5. **Status accounting:** missing adapters, invalid epochs and no-outcome cases remain `UNSUPPORTED`/`NOT_ESTABLISHED`; they are not scored as correct or wrong answers. Do not pool the synthetic sensory fixture with human or physical perception results.

The numerosity runner supplies synthetic area and density signals to exercise the frozen graph calculation. Its outcomes test rule mechanics and scale bookkeeping only. No calibrated visual sensor, psychophysical protocol, human comparator, or real-image ingestion path is available. Accordingly, the registered numerical thresholds are reported as mechanism-fixture results and remain `NOT_ESTABLISHED` as perceptual-capability claims.

## Reproduction

```bash
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p7_v1.py --self-check --output /tmp/linear-p7-selfcheck.json
.venv/bin/python evaluation/process_mastery/analyze_linear_p7_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p7_v1.py --split heldout --n 200 --output /tmp/linear-p7-heldout.json
.venv/bin/python evaluation/process_mastery/analyze_linear_p7_v1.py /tmp/linear-p7-heldout.json
```

Keep raw held-out scorecard and analysis outside git and record SHA256 in the results ledger. Do not modify seeds, allocations, criteria or analyzer after the draw begins.
