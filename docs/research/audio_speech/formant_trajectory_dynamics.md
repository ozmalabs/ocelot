# The DYNAMICS rung — formant TRAJECTORY + order-N motion separates coarticulated digits

**Question.** The static 3-formant nucleus frame provably cannot separate
coarticulated FSDD digits: measured at 8 kHz the steady-nucleus formant frame is
an order-0 SNAPSHOT that throws the MOTION away, and the high-front/high-back
vowels collapse (six↔two share their estimated nucleus, the locus is buried). The
named fix (commit `666ea267`): recognise digits by their formant **TRAJECTORY**
and its **order-N-over-time** motion — the way F1/F2/F3 sweep INTO and OUT of the
vowel across the consonant↔vowel transitions is a speaker-invariant gesture
(locus equations / formant transitions carry identity), matched by alignment, not
by a single frame. Use the session's OWN order-N operator
(`domains.order_n_concepts`).

**Verdict: YES — motion clears the static-formant ceiling decisively.** On the
identical FSDD full-token cross-speaker LOSO split, the formant TRAJECTORY +
order-N dynamics (DTW-matched, the agent's native graph-resident decision) lifts
recognition from the static single-nucleus frame's **29.2%** to **58.9%**
(**+29.7 points**, n=3000, chance 0.100). It does **not** reach the full-envelope
DTW exemplar bank (83.5%, the prior ~0.76–0.79 cross-speaker baseline reproduced)
— it recovers **71%** of that bank from three formants + their order-1/order-2
motion alone. The static→dynamics jump is the predicted structural lift: the
order-0 formant snapshot was leaving the formant MOTION — the largest piece of
speaker-invariant identity in a thin formant feature — on the floor.

---

## (1) Formant trajectory + order-N dynamics wired (order_n_concepts REUSED; donkey audit)

The representation is the agent's owned DSP; the recognition is the agent's
graph-resident decision evaluated natively. `scripts/formant_trajectory_dynamics.py`.

**Formant trajectory (owned DSP, no fit).** F1,F2,F3 are estimated **per frame
across the whole token** (32 ms frame / 12 ms hop, voiced frames only — the
transitions INCLUDED, not just the steady nucleus) via
`scripts/solve_for_n_vowel.estimate_formants` — the agent's LPC-root all-pole
inversion (pre-emphasis → autocorrelation → Levinson-Durbin → pole-angle
frequencies), the SAME owned estimator the vowel rung uses. No trained net, no
`.fit()`, no gradient descent.

**Speaker-relative (VTL-invariant).** Each frame's formants → log-formants minus
the per-token mean. A vocal-tract-length change is a multiplicative shift on all
formants = additive in log = removed by the mean subtraction; what survives is the
speaker-invariant formant PATTERN. The same invariant the vowel rung established.

**Order-N dynamics (the agent's OWN operator, native eval).** The agent's
`domains.order_n_concepts.nth_order_terms` (recursive `Minus` Term-trees)
differences each speaker-relative formant channel **down the TIME axis** →
order-1 (velocity = the formant TRANSITION) and order-2 (curvature = the
acceleration of the glide). Each scalar is evaluated by `substrate.evaluate`
(NATIVE Rust Term-tree), **not** numpy — numpy `np.diff` is run only as a donkey
**audit** cross-check, which **PASSED for every one of the 3000 tokens** (the
build raises if native ≠ numpy). Each trajectory frame is a 9-vector
`[F1,F2,F3 | dF1,dF2,dF3 | ddF1,ddF2,ddF3]`. This is the exact operator the
order-N-over-frequency frame and the time-energy syllable frame use, pointed down
the formant-time axis — "every frame is order-N over a dimension."

**Recognition (the agent's graph-resident decision).** The DECISION is a graph
Term-tree evaluated natively in one `substrate.evaluate` per query:

```
predict(query) = Argmin over digit-Concepts w of
                   MinOver e in has_exemplar(w) of DtwTo(query_traj, traj(e))
```

`DtwTo` (the agent's banded Sakoe-Chiba alignment Rust Term — verified:
identical→0.0, warped-same-shape→0.18, far→3.89), `MinOver` (nearest banked
exemplar of the digit), `Argmin` (the digit decision), over the agent's own digit
Concepts + banked Exemplar trajectories. The DTW warp absorbs rate + speaker
timing and scores the residual SHAPE of the gesture (the speaker-invariant
motion). Exemplars are from TRAIN speakers only; the held-out speaker is NEVER
banked; the exemplar-bank wiring (`has_exemplar` edges) is mechanical
world-adapter scaffolding, not an agent decision.

**Donkey boundary held.** Trajectory = LPC-root formants (owned DSP). Dynamics =
`order_n_concepts.nth_order_terms` (the agent's operator, native eval, audited).
Recognition = `DtwTo`/`MinOver`/`Argmin` Term (native, no learned weight, no net).
The flat `solve_for_n.py` engine and the CortexLoop are untouched.

## (2) The three recognisers on the SAME FSDD full-token LOSO — VERDICT

FSDD 3000 tokens (300/digit), full token, 6-speaker leave-one-speaker-out,
held-out speaker never banked, chance 0.100. All three recognisers run on the
identical split. The full-envelope baseline reuses the confirmed
`scripts.mcu_infer` pipeline (16-band log-mel, per-utterance VTLN, per-speaker
CMVN, predict-remove, k-NN banded DTW) verbatim.

```
                                                       (10-way, chance 0.100)
  recogniser                                            acc      n
  (a) STATIC single-nucleus formant 1-NN  (order-0)    0.292   3000
  (NEW) FORMANT-TRAJECTORY + order-N dynamics (DTW)    0.589   3000
  (b) FULL-ENVELOPE DTW exemplar 1-NN  (the ~0.76 bank) 0.835   3000
```

Per-speaker DYNAMICS LOSO acc: george 0.430, jackson 0.704, lucas 0.680,
nicolas 0.454, theo 0.698, yweweler 0.568.

Reading the decisive comparisons:

- **Dynamics vs the SAME formant front-end as a static frame: +0.297**
  (0.292 → 0.589). The ONLY difference between (a) and (NEW) is static-nucleus
  snapshot vs full trajectory + order-N motion — same LPC formant estimator, same
  speaker-relative space. The formant MOTION carries +0.297 of cross-speaker
  identity the single frame cannot see. This isolates the motion as the lever.
- **Dynamics vs the full-envelope exemplar bank: 0.589 vs 0.835 (71%).** The
  trajectory + dynamics over three formants reaches 71% of the rich 16-band
  log-mel DTW bank. It does NOT catch it — three formants + velocity + curvature
  is a far thinner feature than the full source-normalized spectral trajectory,
  and the LPC formant track is noisy on 8 kHz FSDD (consistent with the SC
  formant-DTW finding `docs/dtw_trajectory_loso.md`: the formant-only trajectory
  is "too thin"; alignment helps but the rich CMVN spectrum wins).

### Did the coarticulated confusions separate? (the static collapse)

The new confusion matrix vs the static one shows the motion separating the
coarticulated pairs the static frame collapsed:

| pair | static (off-diag/total) | dynamics | verdict |
|---|---|---|---|
| **six → two** | 40/300 | **19/300** | halved |
| **two → six** | 41/300 | **34/300** | reduced |
| **six → nine** | 5/300 | **0/300** | cleared |
| **nine → six** | 7/300 | 9/300 | unchanged |

More broadly, the static matrix is diffuse (its strongest "diagonal" entries are
only ~90–152/300, with mass smeared across three/eight/four/five) — the
single-formant snapshot genuinely cannot separate the digits. The dynamics matrix
sharpens the diagonal dramatically: zero 227, one 207, two 208, four 202, five
215 correct/300, and the six↔two coarticulated collapse is halved. The residual
errors concentrate where the formant trajectory is intrinsically ambiguous or
LPC-noisy: **three↔eight** (121 three→eight, 67 eight→three — both end in a
similar vowel→stop glide) and **six↔eight↔seven** in the sibilant-onset cluster
(the LPC formant track is unreliable through the /s/ frication, so the voiced
trajectory alone under-separates them).

## (3) VERDICT — does motion clear the static ceiling? YES. Does it catch the exemplar? NO.

**Motion separates the coarticulated digits and clears the static-formant
ceiling (+29.7 points, 0.292 → 0.589), exactly as predicted — but does NOT reach
the full-envelope exemplar bank (0.835).** The prediction is **half right**: the
trajectory/dynamics climbs well above the static frame toward the exemplar
baseline (71% of it), and the named coarticulated collapse (six↔two) is halved
and six↔nine cleared — but the thin three-formant feature does not catch the rich
16-band envelope.

**The remaining limiter (honest).** It is the **formant front-end resolution at
8 kHz**, not the recognition cognition:

1. **The LPC formant track is noisy / under-resolved on 8 kHz FSDD.** Order-10 LPC
   roots on a 4 kHz-Nyquist signal cannot reliably separate closely-spaced upper
   formants, and the track is unreliable through frication (the sibilant onsets of
   six/seven). The residual three↔eight and the sibilant-cluster confusions are
   front-end noise, not match failure — the same gammatone/8 kHz "wall"
   (`docs/vowel_formant_match.md`, `ozma_wall_is_self_imposed`).
2. **Three formants + motion is a thinner feature than the full spectral
   trajectory.** The full-envelope bank aligns a ~16-band source-normalized
   spectral path; the dynamics rung aligns a 3-formant path. The SC programme
   already measured this asymmetry: DTW alignment lifts whatever feature it is
   given, but the rich CMVN spectral trajectory beats the thin formant one
   (`docs/dtw_trajectory_loso.md`).

The next rung is therefore a **sharper / richer trajectory** — a real continuity
formant *tracker* (band-assigned F1/F2/F3, not naive lowest-3 roots), a
frequency-sharp second "ear" for the upper formants, or fusing the formant-motion
stream with the source-normalized spectral trajectory in a multi-stream DTW — so
the path the agent's `DtwTo` aligns is less blurry. The recogniser architecture
(trajectory + order-N motion, aligned) is correct and is the structural jump that
clears the static ceiling; what remains is the sharpness of the trajectory it
aligns.

## Reproduce

```
python -m scripts.formant_trajectory_dynamics            # full FSDD LOSO (n=3000)
python -m scripts.formant_trajectory_dynamics --quick    # 6/speaker smoke (n=360)
```

Full captured output: `/tmp/formant_trajectory_dynamics.txt`, ending with the
`FORMANT_TRAJECTORY_DYNAMICS_COMPLETED` marker; the run was pgrep-verified to
completion (python PID exited cleanly, elapsed 2125 s). The smoke run (n=360,
6-speaker LOSO) reproduces the direction: static 33.9%, dynamics 55.8%,
full-envelope 76.4%. Nothing committed; `scripts/formant_trajectory_dynamics.py`
is left in the working tree.
