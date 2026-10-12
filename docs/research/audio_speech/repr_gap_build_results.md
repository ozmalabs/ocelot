# Representation-Gap Build — results log (Step C)

Step A settled the gap is REAL (wav2vec2 dominates the from-scratch encoders at a fair pool). Step C
asks whether matched-compute APC variants can close ≥50% of that fair gap (APC ~0.27 → wav2vec2
~0.82), scored on Step A's locked metric/pool (3000 held-out dev-clean tokens, identical Rust
NN-recall kernel, bootstrap CIs).

## Levers built

- **(ii) OBJECTIVE — masked-frame contrastive predictive coding** (new Rust `apc_train_masked_cpc`,
  `apc.rs`): mask ~15% of frames (spans of 3), encode with a bidirectional RNN over the masked
  input, and predict each masked frame's TRUE-frame target CONTRASTIVELY via in-batch InfoNCE over
  frames (query = `Wq·[h_fwd;h_bwd]`, key = `Wk·x_true`) — the specific mechanism wav2vec2 has that
  AR-APC lacks. New InfoNCE-QK math **numerically gradient-checked** (`cpc_tests::qk_grad_numeric`).
  CONTROL: shuffled positive assignment. Emits the same model layout as `apc_train`, so the
  `ApcEncode` graph Term encodes it unchanged (donkey=0 at inference).
- **(i) DATA — 6.7× larger UNLABELED train pool** (1200 vs 180 utts). Masked-CPC is label-free, so
  extra audio is cheap (torch-free `av` decode + Rust cochleagram, no MMS_FA). Tests the data-bound
  hypothesis.
- **(iii) DEPTH — NOT built** in this bounded first pass. A 2-layer recurrence needs the `ApcEncode`
  Term + model layout extended to multi-layer (single-layer only today). Reported honestly as
  deferred.

Baseline = AR-APC (`apc_train`, next-frame L2, bidir), matched epochs/dim. Harness:
`scripts/apc_repr_gap_build.py`.

## Results (held-out dev-clean, 3000-token pool, 10 spk, 1239 words; LOCKED metric cap_q=300, boot=2000)

| variant | recall [95% CI] | AUC [95% CI] | Δ recall | gap closed |
|---|---|---|---|---|
| AR-APC (baseline) | 0.237 [0.190, 0.287] | 0.716 | — | — |
| masked-CPC (objective) | 0.220 [0.173, 0.267] | 0.702 | −0.017 | −2.9% |
| masked-CPC SHUFFLED (ctrl) | 0.257 [0.210, 0.310] | 0.720 | +0.020 | +3.4% |
| masked-CPC +DATA (6.7×) | 0.233 [0.187, 0.283] | 0.642 | −0.003 | −0.6% |
| **wav2vec2 L6** (eval-only) | **0.817 [0.773, 0.857]** | 0.989 | — | — |

fair gap: AR-APC 0.237 → wav2vec2 0.817 (gap +0.580). All from-scratch variants cluster at
0.22–0.26 — their CIs overlap each other heavily and are all **disjoint from** wav2vec2's
[0.773, 0.857]. donkey=0 at inference (no torch imported). Peak RSS 9.55 GiB. (A cheaper first pass
at cap_q=150/boot=400 gave the same qualitative NULL.)

## Verdict

**GATE: NO — no variant closes ≥50% of the fair gap.** In fact none improved cross-speaker NN-recall
over the AR-APC baseline; the masked-CPC objective and the 6.7× data lever both landed at/below
baseline recall.

Honest reading of the internals:
- The masked-CPC **objective genuinely learns its own task** — InfoNCE-frame loss falls sharply
  (6.8→4.1 in ~30 epochs on labeled train; 4.6→2.3 on the 6.7× DATA pool).
- **But it does not transfer to strict cross-speaker word NN-recall.** All from-scratch variants
  land at 0.22–0.26, statistically indistinguishable from the AR-APC baseline (overlapping CIs) and
  far below wav2vec2. Solving masked-frame prediction with a single-layer bidirectional RNN on
  CPU-scale data produces a context-smoothed representation that is not better (marginally worse)
  for fine word discrimination than AR-APC.
- The **shuffled-mask control check reads WEAK/vacuous** on recall for a mechanical reason: there is
  no recall gain to collapse (objective ≤ baseline), so "shuffle collapses the gain" has nothing to
  act on. (The gradient-check test confirms the objective's math is correct; the null is about
  transfer at this scale, not a training bug.)

**Conclusion.** The wav2vec2 gap is real (Step A) but is **NOT** closed by a matched-compute
masked-CPC frame objective or a 6.7× unlabeled-data lever at this (single-layer, CPU, minutes)
scale. What wav2vec2 buys is not just the objective family — it is objective × depth × scale ×
pretraining-compute together. The remaining untested lever is DEPTH (multi-layer), which requires
extending the encode Term; that, plus much larger scale, is the honest next step if closing the
frame-level gap is judged worth the compute. The complementary path the corrected note now
emphasises — higher orders (sequence/syntax/grounding) compensating for a weak frame — remains the
cheaper route to understanding continuous speech.

## Reanalysis capture support (2026-10-03)

The scoring harness now accepts `--output PATH` and writes an atomic, versioned JSON capture for
future runs. It records source and native-extension hashes, hashes for the labeled train, held-out
test, and optional large-train cache, the ordered token/speaker pool, effective configuration,
deterministic bootstrap seed, all summary metrics and gap-gate outcome, peak RSS, and raw Rust
recall-detail vectors. Example:

```sh
PYTHONPATH=runners/dsl/python:.:scripts VENV_PY scripts/apc_repr_gap_build.py \
  --output evaluation/reports/apc_repr_gap_run_<date>.json
```

This enables prospective reanalysis without retraining, but does not recreate the missing raw
records for the historical result above. The source and cache digests are recorded when the new
run is made; the old prose log remains insufficient for independent reconstruction.
