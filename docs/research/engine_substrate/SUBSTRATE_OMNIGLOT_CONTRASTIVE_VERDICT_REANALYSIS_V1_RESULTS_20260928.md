# Omniglot contrastive-verdict historical reanalysis v1 results

**Analysis date:** 2026-09-28. This is a retrospective reanalysis, not a new model run.  
**Protocol:** [reanalysis specification](SUBSTRATE_OMNIGLOT_CONTRASTIVE_VERDICT_REANALYSIS_V1_PROTOCOL_20260928.md).  
**Evidence:** [independent reanalysis](../../../evaluation/reports/omniglot_contrastive_historical_reanalysis_v1_20260928.json), [input lock](../../../evaluation/substrate_capability/omniglot_contrastive_historical_reanalysis_v1_lock_20260928.json), [analyzer](../../../scripts/analyze_omniglot_contrastive_historical_reanalysis_v1.py), [historical execution log](../../../results/omniglot_gate_run37a.log), [historical raw records](../../../results/run37a_checkpoints/eval_run37a.json), [historical report](../../../results/run37a_checkpoints/report.json).

## Reanalysis result

All 15 integrity and arithmetic checks pass. The archived evaluation is complete at 400 paired episodes, with 40 episodes in each of 10 alphabets. The baseline arm exactly matches all 400 paired global predictions in the run-26 baseline checkpoint, and the block-0 guard records exact global-arm parity plus 20/20 agreement between `top2_candidates()[0]` and the global verdict.

| Verdict | Correct | Accuracy | Wilson 95% interval |
|---|---:|---:|---:|
| Global SC+TPS parse-marginal baseline | 322/400 | 80.5% | 76.3–84.1% |
| Top-two contrastive verdict | 256/400 | 64.0% | 59.2–68.6% |

The paired comparison has 16 fixed cases and 82 broken cases (98 discordant), with an exact two-sided McNemar/binomial p-value of `7.38e-12`. The true class was rank 2 on 33 of the 78 global errors, setting a reported top-two recovery ceiling; the method fixed 16 and broke 82. The contrastive path used its one-sided decision in 242/400 episodes and its two-sided decision in 158/400.

## Interpretation and limits

On this historical Omniglot panel, the standalone “focus on where the two candidates differ” verdict was substantially harmful. It is not a generally useful classifier result, despite being a plausible compositional strategy. The arc report's next lever—using the focused verdict only when it agrees with the full-evidence verdict—remains a separate, unmeasured hypothesis.

The source record attributes run 37A to commit `cca938fd`, but this checkout contains an imported Git snapshot without that historical object, and the raw episode file lacks a complete source/input hash lock. The reanalysis locks the archived artifacts and notes hashes of current source for context; those hashes do not prove they are the source used for the original run. Treat this as verified historical output arithmetic, not current-source reproduction. The result concerns the separate host-side Omniglot contrastive algorithm; it is not an evaluation of the generated `judge_experiment_outcome_*` rule, which reads `Run.score / frames`.
