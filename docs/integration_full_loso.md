# Integration on the whitened matched filter — the FULL cross-speaker LOSO

Does **INTEGRATION** (average the whitened-match evidence over multiple independent
looks to boost SNR — the third signal-from-noise tool) on top of the whitened matched
filter push the audio cross-speaker LOSO **past the canonical CMVN**, on the **full**
run (all 400 cross-speaker probes, not the 80-clip subsample)?

**Verdict up front: NO, and the prior subsample win did not hold.** Integration lifts the
whitened 1-best by only **+0.010** (0.472 → 0.482), the multi-scale fusion *hurts*, and on
the full run the whitened matched filter falls **below** the CMVN-class baseline on this
split — the subsample +0.015 over CMVN was within noise. The independent "looks" turn out
to be **correlated** (they share the same within-word nuisance), so averaging them does not
cancel it. Honest kill of the integration hypothesis at full n.

> Caveat on the script's auto-verdict: `scripts/integration_full_loso.py` compares against
> an *in-script* CMVN-DTW baseline that banks only 60-train / 400 exemplars and lands at
> **0.300**; its printed "INTEGRATION PAYS, exceeds canonical CMVN 0.300" is therefore
> against the *wrong* number. The canonical-config CMVN (reproduced separately, below) is
> **BAG 0.500 / DTW-traj 0.273** on this seed. Read the verdict here, not the script's line.

## Build (donkey-clean — `CortexLoop` + `hat.py` UNTOUCHED, git-diff empty; verified)

`scripts/integration_full_loso.py`. On top of the whitened+smoothed compare (sf=1.5,
shrink=0.1, α=0.75 — the commit f0f2350e best), three independent **looks** are gathered
per held-out clip and integrated with **owned ops only** (z-standardise over words, sum,
mean / softmin — NO net), in the script over the hat's owned `encode`/`compare`/`library`:

1. **LOOP look** — the `CortexLoop` matched-filter adapt at the primary scale (the prior
   whitened 1-best). The loop and the Rust `DtwTo` are untouched.
2. **K-NEAREST look** — integrate the per-word evidence over the K-nearest library
   exemplars (mean / softmin of the K smallest whitened residuals per word) instead of the
   1-best, so style-dependent noise across the K cancels. K swept ∈ {3,5,8}.
3. **MULTI-SCALE looks** — the K-nearest evidence at several smoothing scales (sf ∈
   {1.0,1.5,2.5}, the blur pyramid / two-ears), each whitened by its own re-fit `W` (no
   leakage), so scale-dependent noise cancels.

Readout = `argmin_word [ Σ z-standardised per-look evidence ]`. Owned averaging/sum/softmin;
whitening from the prior commit. `git diff` on `domains/cortex_loop.py`,
`domains/audio_hat.py`, `domains/hat.py` is **empty** (audited).

## Test (robust SC 40-speaker LOSO — held-out REAL never banked; FULL probe)

40 HELD-OUT speakers (LOSO probe, never banked) DISJOINT from 60 TRAIN speakers (whitening
fit only). **n = 400 real held-out cross-speaker clips** (the full run, `n_loso_per=40`),
10 digits, chance 0.100. Whitening `S_n` re-fit per scale from within-word scatter over
10 words / 12 800 TRAIN frames; word labels ONLY, no speaker labels. Total wall 10 032 s
(≈ 2 h 47 m), single core.

### Baselines on this split (same 40 held-out speakers, seed 20240610)

| baseline | config | LOSO (n=400) |
|---|---|---|
| CMVN 6-cue **BAG** (the real CMVN-class recognizer) | canonical 120-train / 200-bank | **0.500** |
| CMVN DTW-trajectory | canonical 120-train / 200-bank | 0.273 |
| CMVN DTW (in-script, 60-train / 400-bank) | the script's baseline | 0.300 |
| documented "canonical" DTW-traj 0.570 | — | **did NOT reproduce on this seed** |

The documented 0.570 is seed/sampling-specific; on seed 20240610 the canonical-config
DTW-trajectory recognizer lands at 0.273 and the per-frame 6-cue BAG at **0.500**. The
honest CMVN-class bar on this split is therefore **≈ 0.50**.

### Whitened matched filter + integration (full run)

| config | LOSO (n=400) | separation (wrong−true)* |
|---|---|---|
| whitened 1-best (loop only, no integration) | **0.472** | −0.298 |
| + K-nearest K=3 mean | 0.477 | −0.253 |
| + K-nearest K=3 softmin | 0.475 | −0.296 |
| + K-nearest K=5 mean | 0.480 | −0.245 |
| + K-nearest K=5 softmin | 0.477 | −0.232 |
| **+ K-nearest K=8 mean (best)** | **0.482** | −0.139 |
| + K-nearest K=8 softmin | 0.482 | −0.185 |
| + multi-scale (loop + knn@K8 fused over {1.0,1.5,2.5}) | 0.475 | −0.002 |
| + multi-scale, no loop (pure library integration) | 0.468 | −0.126 |

\* separation here is over the **z-standardised integrated** evidence (centred per clip), so
it is not comparable to the raw-residual separation in `whitened_matched_filter.md`; the
load-bearing quantity is the LOSO accuracy.

## Findings

- **Integration does NOT boost SNR here. Best lift = +0.010** (whitened 1-best 0.472 → K=8
  mean 0.482). The K-nearest sweep is faintly monotone (K=3→5→8 mean: 0.477→0.480→0.482),
  i.e. real but tiny — nowhere near the 1/√N detector gain integration promises when the
  looks are independent.
- **The looks are correlated.** Multi-scale fusion *hurts* (0.475 with the loop, 0.468
  without), and the integrated separation collapses toward zero (−0.002 at multi-scale).
  Different smoothing scales / K-nearest exemplars of the same word carry the **same**
  within-word nuisance (speaker + synthetic-vs-real domain), so averaging them cancels
  signal as much as noise. Integration is the wrong tool for a *correlated* nuisance.
- **The subsample win did not hold.** On the full run the whitened 1-best is **0.472**,
  *below* the same-split CMVN-class BAG (0.500) and below the 80-clip subsample's 0.525.
  The prior +0.015-over-CMVN was within noise at n=80; at n=400 the whitened matched filter
  sits under the CMVN-class baseline.
- **Nothing clears the CMVN-class bar.** Best integrated 0.482 < BAG 0.500 on this split.
  The script's "exceeds canonical CMVN 0.300, integration pays" is an artefact of comparing
  to its own under-banked (60-train) CMVN-DTW; against the genuine CMVN-class recognizer the
  loop+integration is still behind.

## Verdict

**Honest kill.** Integration (the third signal-from-noise tool) does **not** push the
analysis-by-synthesis loop past CMVN on the full cross-speaker LOSO, and the whitened
matched filter's modest subsample edge over CMVN does **not** survive at full n. The
within-word remainder that stayed entangled after whitening is **correlated across looks**,
so averaging cannot remove it — the residual is genuinely entangled with the word, deeper
than any of the three signal-from-noise tools (matched filter → whitening → integration)
can separate. The loop is at ≈ 0.47–0.48 cross-speaker; CMVN-class is ≈ 0.50 on this split.

## Reproduce

```bash
# the full integration run (n=400; ~2h47m single core)
python -m scripts.integration_full_loso 40 40 60 0 60
# capture: /tmp/integration_full_loso.log, end marker INTEGRATION_FULL_LOSO_COMPLETED

# the canonical-config CMVN baseline on the same seed (BAG 0.500 / DTW-traj 0.273)
python -m scripts.dtw_trajectory_loso 120 40 20 20240610
```

Donkey boundary: integration = owned averaging/sum/softmin (no net); whitening from commit
f0f2350e; `CortexLoop` + `hat.py` git-diff empty; held-out REAL never banked; LOSO
ungameable. Required suites green: `test_stt_pipeline` + `test_frontend_effect_gate`
(11 passed).
