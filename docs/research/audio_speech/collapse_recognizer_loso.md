# Collapse recognizer LOSO — coherent partial trace over the speaker

**Verdict: KILL.** The genuinely-quantum **coherent collapse** `|Sum_V c(W,V)|^2` does
**not** beat the classical **incoherent** marginal `Sum_V |c(W,V)|^2` (the integration
that already failed, c44742a7), and does not clear the CMVN bar. Interference is
destructive-to-neutral, exactly as in the prior quantum recognizer (ac4acbce). The
(word, speaker) entanglement is beyond the coherent partial trace too. Reported plainly,
not rescued.

## What was built

`scripts/collapse_recognizer_loso.py` — on the whitened+smoothed compare (the
f0f2350e / c44742a7 best config: `smooth_f=1.5`, whitening `shrink=0.1`, `alpha=0.75`,
Mahalanobis DtwTo) over the hat's `(word W, voice V)` library (the joint entangled
state — each library entry *is* a (W,V) pair):

1. **Joint amplitudes** `|c(W,V)| = exp(-D(H, synth(W,V)) / 2T)` — Born-amplitude =
   sqrt of the classical likelihood; `D` is the hat's owned whitened DtwTo residual.
   Times a phase `e^{i phi(W,V)}`.
2. **Phase `phi(W,V)` — DERIVED, not fitted.** Three principled variants:
   (a) **margin** — signed margin of `D(W,V)` in robust-spread (MAD) units, `tanh`-squashed
   to `[0, pi/2)` (closest-fitting voices ~real-aligned, poor fits rotated; same family
   as ac4acbce); (b) **warp** — per-frame DTW cost `D / traj_len`, robust-z → `tanh` → angle
   (a warp signature); (c) **voice** — the speaker's own `(pitch, rate)` coordinate mapped
   to an angle (the speaker axis carries the phase).
3. **Collapse (coherent partial trace over speaker)** `A(W) = Sum_V c(W,V)` (complex,
   coherent), `P(W) = |A(W)|^2`, `argmax_W`. The control is the classical incoherent
   marginal `P(W) = Sum_V |c(W,V)|^2` — the failed integration.

**Donkey boundary (audited):** amplitudes / phases / coherent-sum / Born = owned complex
linear algebra in the script (no net / fit / gradient; phase derived). AudioHat readout
only (read-only `encode` / `compare` / `library`). **CortexLoop + audio_hat.py + hat.py +
dtw_trajectory_loso.py git-diff EMPTY** (verified). Held-out REAL never banked; LOSO
ungameable. The expensive `encode + compare` runs once per probe; the T × phase × mode
sweeps are derived from the cached joint-distance vectors for free.

## Results — robust SC 40-speaker LOSO, **full n = 661** held-out clips

Held-out 40 speakers disjoint from 60 train (whitening fit only). chance 0.100.
n = 661 (all available held-out digit clips; ≥ the n=400 target).

| recognizer | LOSO acc | notes |
|---|---|---|
| **COHERENT collapse** (best: voice, T=1.0, phase-ON) | **0.430** | the quantum partial trace |
| CLASSICAL incoherent marginal (best: T=4.0) | **0.433** | = the failed integration (control) |
| HARD min_V (loop one-best) | 0.437 | prior hard-collapse bar |
| CMVN-DTW canonical (this split) | 0.245 | BAG_CUES DtwTo, this seed |

The honest CMVN-class bar is **~0.50** (the 6-cue BAG, c44742a7); the documented 0.570 is
seed-specific and did not reproduce. The DTW-traj CMVN here is 0.245. **Nothing in the
collapse family clears ~0.50.**

### T sweep — incoherent marginal (the control)
`T = 0.25→8.0`: LOSO 0.428 / 0.431 / 0.431 / 0.428 / **0.433** / 0.431. Flat; best 0.433 @ T=4.0.

### Coherent collapse — phase-ON vs phase-OFF (interference isolation)

- **margin** & **warp** (identical here, both monotone in `D`): phase-ON peaks 0.427 @ T=0.25
  then **collapses** as T grows (0.404 → 0.380 → 0.188 → 0.085 → 0.059) with separation going
  hugely negative (−3.5 → −104). Phase-OFF stays ~0.431–0.433. Interference at the best T:
  **−0.005 (destructive)**.
- **voice**: phase-ON 0.427 / 0.425 / **0.430** / 0.428 / 0.427 / 0.427 across T; phase-OFF
  0.431 / 0.431 / 0.428 / **0.433** / 0.431 / 0.431. Interference at T=1.0: **+0.002**
  (nominally "constructive" but within noise at n=661, and still below both the incoherent
  marginal 0.433 and hard min_V 0.437).

## Why it fails — the honest crux

The crux from `ozma_entanglement_needs_collapse` held exactly: the proper partial trace =
the classical marginal = the integration that already failed. The only genuinely-quantum
move is the coherent sum with interference, and **the interference is not constructive**:

- At small T the amplitude `exp(-D/2T)` is peaked → effectively one voice dominates per word
  → no cross-terms → coherent ≈ incoherent ≈ hard-min (all ~0.43). The phase does nothing.
- At larger T, where multiple voices contribute and cross-terms exist, the phase makes the
  interference **destructive** — accuracy and separation collapse (down to 0.059, sep −104).
  Same signature ac4acbce found: on noisy cross-speaker features the phase amplifies
  unreliable directions, the cross-terms cancel signal.

The "voice" phase's +0.002 at T=1.0 is the only non-negative interference and is within
sampling noise; it does not lift the recognizer above the incoherent control, the hard
min_V, or the CMVN bar.

**Conclusion.** Collapse-not-factor was the right operation to *try* on an entangled state,
and it was built correctly (coherent partial trace, owned complex algebra, phase derived).
But the coherent collapse buys nothing here AGAIN — the entanglement is beyond it. The
cross-speaker residual remains the **feature/perception wall**, not a combine the quantum
framing can crack. (Note: the CortexLoop's own recognizer still functions — hard min_V 0.437
— but no member of the collapse family clears the CMVN-class ~0.50.)

Run: `python -m scripts.collapse_recognizer_loso 40 100 60 60` (total 881s, n=661).
