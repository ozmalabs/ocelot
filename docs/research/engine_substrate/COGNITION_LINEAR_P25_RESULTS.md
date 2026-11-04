# P25 persistent retention results

**Phase:** `linear-p25-v1`
**Run date:** 2026-10-25 (Australia/Melbourne)
**Protocol:** [P25 preregistration](COGNITION_LINEAR_P25_PREREG.md), standalone commit `7b6855a1596ace3e42ba6ffa36968033abf32a13`; frozen source parent `45450a1fcb068409358560a0051d6d1822fab2a2`.
**Runtime:** Python 3.13.5; native runtime attestation `ATTESTED`; build sources matched and native symbols were bound.
**Allocation:** held-out digest `0865734f7558129c8cf8b0220cd30707186d920df94b5d2d6e485e581406c0ed`; one 1,200-stream draw, 4 arms, 4,800 stream-arm rows, 300 controls.

## Registered result

The analyzer reports `VALID`, with no structural failures. All 4,800 arm rows completed; no allocated stream was omitted or censored. All 300 controls passed: eviction 100/100, restart 100/100, absent source 100/100. Receipt parity and the preregistered action counts held across arms. Every row stayed under the 400,000-byte graph ceiling (maximum 77,370 bytes). The runner checked and enforced the 250,000-step ceiling for each learner, and all rows passed. Shared budget debit peaked at 11 units of 256.

The registered sleep-versus-replay primary passed: paired normalized delayed-success AUC gain **0.7222**, 99% paired bootstrap interval **[0.7103, 0.7336]**, `n=1,200`, 20,000 resamples, seed 25,010,241. This exceeds the preregistered 0.10 minimum. The preregistered new-task accuracy-loss contrast was **0.0000**, 99% interval **[0.0000, 0.0000]**, under the 0.02 maximum. Thus the registered decision is **PASS**.

The new-task result is at floor: all four arms scored 0/1,200 (0%). The non-loss criterion passed because sleep did not reduce the comparator's already-zero accuracy. This does not show useful transfer to the unseen ButtonWidget task, and the large registered retention effect must be read as preservation of the acquired target relation under this simulator's capacity and interference conditions.

## Family and capacity strata

Each row below has 200 paired streams. AUC gain is sleep consolidation minus replay only. All arms scored 0% on the unseen task in every stratum.

| Family | Capacity ratio | Capacity bytes | Sleep AUC | Replay AUC | Paired gain |
|---|---:|---:|---:|---:|---:|
| Thermal | 0.5 | 2,260 | 1.0000 | 0.1667 | 0.8333 |
| Thermal | 1.0 | 4,520 | 1.0000 | 0.1667 | 0.8333 |
| Thermal | 2.0 | 9,040 | 1.0000 | 0.5000 | 0.5000 |
| Latch | 0.5 | 2,219 | 1.0000 | 0.1667 | 0.8333 |
| Latch | 1.0 | 4,438 | 1.0000 | 0.1667 | 0.8333 |
| Latch | 2.0 | 8,876 | 1.0000 | 0.5000 | 0.5000 |

At the pre-delay point all arms scored 100%. At the first, second and third interference checkpoints, sleep consolidation scored 100% in both families and all capacity strata. The other three arms scored 33.3%, 0%, and 0% at those checkpoints for ratios 0.5 and 1.0; at ratio 2.0 they scored 66.7%, 33.3%, and 33.3%. `awake_matched` performed similarly to `replay_only` in every cell. Mean offline native work was 29 steps for sleep consolidation, 31 for replay, and 30 for the awake-matched work arm. The maximum graph sizes by arm were 77,370 bytes (sleep), 73,527 (replay), 73,312 (awake matched), and 69,455 (no offline). The runner enforced the 250,000-step ceiling for each learner and every row passed, but did not serialize the exact cumulative counter; only phase-local work fields are present in the raw ledger, so an exact maximum total cannot be recovered.

## Artifacts and hashes

- Raw held-out rows: `evaluation/process_mastery/results/p25_linear_v1_heldout_20261024.json` — SHA-256 `8986225f3a0f57741d4e8729734690ca7fde4f5109c4f55e6963f17d6c76bf4b` (24 MiB).
- Frozen analyzer output: `evaluation/process_mastery/results/p25_linear_v1_heldout_analysis_20261024.json` — SHA-256 `8d4094ef4bfef65fcfafd96a6e4d66ec7d0af4e1aaccce7a0375b2fac197a135`.
- Single-use run marker: `evaluation/process_mastery/results/.p25_v1_heldout_run_started`.
- Preregistration commit and frozen runtime/source/allocation hashes are recorded in the raw artifact.

## Interpretation and next phase

P25 establishes a strong, repeatable within-simulator retention effect for the consolidated target relation. It does not establish generalization: the unseen task is floor-level for every arm. The result does not support a broader claim about useful learning or human-equivalent extended thinking. P26 should use the demonstrated persistent learner and measured memory interfaces while preserving this transfer limitation; it must not count the P25 retention effect as evidence for evidence-selection or process-search improvement.
