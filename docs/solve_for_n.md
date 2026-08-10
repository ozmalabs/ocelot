# solve-for-N — the GENERAL analysis-by-synthesis machine (domain-agnostic)

> Memory: `ozma_solve_for_n_is_general_not_speech` + `ozma_order_n_analysis_by_synthesis`.
> Perception = **inverting a forward model**. Don't read a linear transform off the
> signal — HYPOTHESISE params → SYNTHESISE → MATCH → REFINE, iterated ("n passes").
> The ENGINE is the agent's cognition (a principled search + match + a
> weighted-admissibility collapse). The FORWARD MODEL is a **plug-in** that carries the
> domain knowledge. Swap the plug-in (damped-sinusoids → speech source-filter) and the
> SAME engine perceives the new domain unchanged. This proves the MECHANISM on a clean
> synthetic domain where the forward model is EXACT and ground truth is known.

Files: `scripts/solve_for_n.py` (engine + plug-in + tests). Run:
`python -m scripts.solve_for_n` (full) / `--quick` (smoke). Not committed (coordinate).

---

## 1. The general engine, with the forward model as a clean PLUG-IN (donkey audit)

`solve_for_n(forward_model, signal, n=None, t=None, ...)` knows **nothing** about
sinusoids. The plug-in interface — the boundary speech swaps across unchanged:

```
fm.synthesise(params)                 -> signal              (exact generative fn)
fm.propose(residual, t)               -> [candidate components]   (what could explain this)
fm.refine_component(comp, target, t)  -> polished comp        (the AbS calculus)
fm.merge([c1, c2, ...])               -> full params dict
```

The engine is **matching pursuit to order N + joint back-fitting**:

1. residual ← input.
2. for each pass to order N: the plug-in PROPOSES an over-complete menu of candidate
   single components for the residual; the engine REFINES + SYNTHESISES each, scores it
   by **variance-explained** (a soft excluder, not a dot product), COLLAPSES the menu by
   **weighted admissibility**, admits the single best, SUBTRACTS it, recurses.
3. a JOINT BACK-FITTING loop ("the n passes") re-fits every admitted component against
   the input with the others held, until `||synthesise(params) − input||` converges —
   the order-N co-refinement that lets close components separate.

**Weighted-admissibility collapse** (cf. `domains/weighted_admissibility.py`): for menu
variance-explained `v_i`, `weight_i = clip((v_i − median(v)) / (1 − median(v)), 0, 1)`,
effective admissibility `= v_i · weight_i`; a floor-level (noise) candidate gets weight 0
→ abstains (can't win on noise), a real one keeps full say. NO free knob: floor = menu
median (derived), the map is the fixed reliability normalisation.

**DONKEY AUDIT (clean).** Engine = owned numpy search (matching pursuit + back-fitting)
+ match (L2 to the synthesised signal) + weighted-admissibility collapse. **NO neural
net, NO `.fit()`, NO gradient-descent training.** The refinement is a bounded local
coordinate polish (golden-section on continuous frequency + closed-form least-squares on
A/φ + a small damping grid) against the EXACT model — the AbS calculus, not weight
training. The match metric is `||synthesise(params) − input||` (the exact-model fit), NOT
a linear read-off — this is *why* it super-resolves.

The **only** domain-specific code is `DampedSinusoidModel`
(`f(t)=Σ A_i·exp(−d_i·t)·cos(2π f_i t + φ_i)`, params `{A,d,f,φ}`). A speech
source-filter model implementing the same 4 methods drops straight into `solve_for_n`.

---

## 2. RECOVERY vs ground truth + n  (200 trials, K=1..3, fs=1000 Hz, T=256, bin=1/T=3.906 Hz)

| metric | value |
|---|---|
| freq error (bins): median / mean / p95 | **0.0005** / 0.0009 / 0.0030 |
| amplitude rel. error: median / mean | 0.0168 / 0.0194 |
| recovery rate (freq within 0.5 bin) | **100.0%** |
| mean AbS passes (n) | 7.2 |

The engine recovers the K-component structure to ~5e-4 of a bin — far below the FFT grid.

## 3. SUPER-RESOLUTION — solve-for-n vs FFT  (two equal sinusoids, 20 dB, 60 trials/point)

Success ≥ 0.8 = resolvable. bin (1/T) = 3.906 Hz.

| spacing (bins) | spacing (Hz) | solve-for-n | FFT peak-pick |
|---:|---:|---:|---:|
| 0.20 | 0.781 | 50.0% | 0.0% |
| 0.30 | 1.172 | 55.0% | 3.3% |
| 0.40 | 1.562 | 63.3% | 5.0% |
| 0.50 | 1.953 | 76.7% | 3.3% |
| **0.60** | 2.344 | **100.0%** | 10.0% |
| 0.70 | 2.734 | 96.7% | 13.3% |
| 0.80 | 3.125 | 100.0% | 20.0% |
| 1.00 | 3.906 | 100.0% | 23.3% |
| 1.25 | 4.883 | 100.0% | 46.7% |
| 1.50 | 5.859 | 100.0% | 56.7% |
| 2.00 | 7.812 | 100.0% | 100.0% |

**MIN RESOLVABLE spacing — solve-for-n: 0.6 bins (2.34 Hz)  vs  FFT: 2.0 bins (7.81 Hz).**
solve-for-n separates sinusoids **3.3× closer** than the FFT, and reliably *inside* one
FFT bin (the FFT, with Hann windowing, can't hit 0.8 until a full 2 bins of separation).
Even at 0.2 bins solve-for-n succeeds half the time where the FFT is at 0%.

## 4. NOISE robustness  (two sinusoids 4 bins apart, success = both within 0.5 bin, 80 trials/point)

| SNR (dB) | success | median freq err (bins) |
|---:|---:|---:|
| 20 | 100.0% | 0.0037 |
| 15 | 100.0% | 0.0065 |
| 10 | 100.0% | 0.0111 |
| 5 | 100.0% | 0.0218 |
| 0 | 100.0% | 0.0381 |
| −5 | 100.0% | 0.0690 |

100% recovery clear down to −5 dB SNR; the frequency error degrades gracefully
(0.004 → 0.069 bins) but never breaks the 0.5-bin success criterion.

---

## 5. VERDICT

- **Recovers structure: YES** — 100% recovery, median frequency error 0.0005 bins.
- **Super-resolves: YES** — resolvable down to 0.6 bins vs the FFT's 2.0 bins (3.3×),
  reliably inside one FFT bin.
- **Noise-robust: YES** — 100% to −5 dB.

The **general solve-for-N machine recovers the structure AND super-resolves**, beating
the linear FFT read-off exactly as predicted, because it fits the EXACT forward model
rather than reading a linear transform. The forward model is a clean plug-in, so this
proves the analysis-by-synthesis MECHANISM **domain-agnostically** — the speech
source-filter model swaps in unchanged.

**Honest bounds.** (i) Proven on the synthetic domain where the forward model is exact;
a real domain's gain is bounded by how exactly its plug-in models the signal. (ii) The
super-resolution floor (~0.6 bins for 100%, 0.2 bins ~50%) is where the local refinement
starts hitting AbS-fit local minima — the residual after peeling the first of two very
close components is small and noise-corrupted, so the second proposal/refine occasionally
locks onto the wrong continuous frequency. A joint multi-start or a 2-D coupled refine
would push the floor lower; not needed to prove the mechanism. (iii) `n` (passes) here is
order-K matching pursuit + ≤6 back-fitting sweeps; harder/closer signals would take more.
