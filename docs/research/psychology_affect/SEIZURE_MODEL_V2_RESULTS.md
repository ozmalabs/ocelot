# SEIZURE MODEL V2 — RESULTS

Two re-tests of the V1 limits named in `SEIZURE_SCIENCE.md` (P4/P5), on the REAL
engine. Prereg: `SEIZURE_MODEL_V2_PREREG.md` (committed `29687335dd`, **before**
these numbers). Branch `seizure-model-v2`, base `a9fc82eed2`. Data:
`results/seizure_v2.json`, `results/seizure_v2_p6.json`; figure
`results/seizure_v2_figure.png`. **No new Rust Term** (zero `.rs` changes; the
recruitment term is added DSL data in `sz_settle_next_residual`; the harness is a
world adapter). Every number is the engine settling a 41×41 `CognitiveArea`
lattice via `run_rules` + `fold_clock_edge`.

give\* := the largest give in the grid at which the seizure persists
(`persists`: mean final-60-substep n_active > 5.0), the V1 metric. Seizure regime
= give < give\*, so a HIGHER give\* means "seizes more easily" (pro-ictal).

---

## V2-P4 — recruitment coupling FLIPS the sign: PRO-ICTAL. **Prediction confirmed.**

Homogeneous lattice, everything identical to the published central-onset fold
(N=41, α=0.5, D=3, g=0.8, θ=1, r_focus=3), **only `g_rec` varied**. Seeds {5,6,7}.

| recruitment g_rec | give\* (median of 3 seeds) | per-seed |
|---|---|---|
| **0.0** (= V1) | **0.5375** | [0.575, 0.5375, 0.5375] |
| 0.025 | 0.60 | [0.65, 0.60, 0.60] |
| 0.05 | 0.70 | [0.70, 0.70, 0.70] |
| 0.10 | 0.80 | [0.80, 0.80, 0.80] |
| 0.20 | **1.00 (saturated)** | [1.0, 1.0, 1.0] |
| 0.40 | **1.00 (saturated)** | [1.0, 1.0, 1.0] |

give\* is **strictly monotonically increasing** in `g_rec`. At g_rec ≥ 0.2 the
seizure persists **even at give = 1.0** (full graceful shed) — something the
symmetric-diffusive channel `g` **never** does at any drive (V1: "give=1 never
seizes to D=60"). Recruitment overwhelms the give.

**Matched control (the sign flip, side by side).** The published V1 diffusion
sweep and the V2 recruitment sweep are the SAME lattice/onset with a single
coupling knob moved:

| coupling knob | give\* trajectory | direction |
|---|---|---|
| V1 diffusive `g` 0.40→1.00 | 0.65 → 0.60 → 0.55 → 0.50 | **protective** (falls) |
| V2 recruitment `g_rec` 0→0.40 | 0.5375 → 0.60 → 0.70 → 0.80 → 1.0 | **pro-ictal** (rises) |

The give-fold slides monotonically toward higher give as recruitment rises
(figure panel B): at g_rec=0 the fold sits at give≈0.55; at g_rec=0.1 it is at
give≈0.8; at g_rec≥0.2 it is off the top of the valid give range.

**VERDICT: P4 flipped.** More excitatory-recruitment coupling makes the seizure
EASIER — the sign the connectivity / hyperconnectivity literature reports
(Epileptor / VEP; critical-dynamics spread models). The V1 refutation was
correctly diagnosed as *wrong kind of coupling*: swapping the conservative
diffusive channel for a non-conservative, gain-bearing, degree-scaling
recruitment channel reverses the sign, with `g_rec=0` reproducing V1 exactly.

---

## V2-P5 — high-degree HUBS are the preferred onset locus. **Prediction confirmed, modestly.**

Heterogeneous lattice: one HUB (hub_k=16 long-range bidirectional `recruits`
edges) and one matched NON-HUB at **equal eccentricity** (both dist 14.14 from
center), identical tight onset (r_onset=1) placed at each on the **same** lattice
(only the onset locus differs — the clean within-lattice matched control, phases
held fixed). g_rec=0.1. Seeds {5,6,7,8,9} × hub-side swap (hub at each corner).

| onset locus | median give\* |
|---|---|
| **HUB** | **0.85** |
| NON-HUB | 0.80 |
| homogeneous control (no hub, same locus) | 0.80 |

**Within-lattice paired difference** give\*(hub onset) − give\*(nonhub onset),
over 10 (corner × seed) pairs: **median +0.05**, **6/10 positive**, 3/10 tie,
**1/10 reversal** (−0.05). The homogeneous control (give\*=0.80) matches the
non-hub onset, confirming the hub — not the location — raises give\*.

The give\* difference is one grid step (0.05), but the **recruited-tissue**
difference is larger and consistent across the whole give range (figure panel D,
final_active mean over seeds):

| give | HUB onset | NON-HUB onset |
|---|---|---|
| 0.85 | **22.6** (persists) | 5.2 (borderline) |
| 0.80 | **170.5** | 60.5 |
| 0.75 | **730.1** | 290.3 |
| 0.70 | **1217.5** | 613.7 |

Hub onset recruits **~2–3× more tissue at matched give** than a non-hub onset.

**VERDICT: P5 confirmed but modest and honest about it.** A high-degree hub IS
the preferred onset locus (seizes at higher give, recruits more), the direction
the hub-onset literature reports. The effect is **small (one give-grid step,
median +0.05) and at the resolution limit**, with one reversal under the
hub-side-swap control — position/phase noise is comparable to the effect in
give\* terms, though the ~2–3× tissue-recruitment gap is robust. The honest
mechanistic reason the effect is not larger: my hubs wire to **scattered random
singletons**, and recruitment needs LOCAL coherence to build a self-sustaining
focus, so scattered long-range seeds mostly die. A hub wired to a coherent
cluster (or a finer give grid) would sharpen it — named as the next tightening,
not claimed here. The homogeneous-lattice limit is **addressed in direction**;
its magnitude is bounded by the hub topology chosen.

---

## V2-P6 (EXPLORATORY) — one escalation term, two pathologies. **Prediction confirmed.**

The SAME escalation ingredient (alpha: over-threshold residual regenerates more
residual). Whether it is allowed to COUPLE laterally decides the pathology.
Central onset D=3, give=0.5, seed 5. (Exploratory; reported as-is.)

| regime | params | persists | max_front | onset-prop | post-onset rank-1 | final_active |
|---|---|---|---|---|---|---|
| **SEIZURE** (recruitment) | g=0.8, g_rec=0.2, α=0.5 | yes | **22.80** | **2.23** | **0.418** | 1681 (whole lattice) |
| **HALLUCINATION** (source-only) | g=0, g_rec=0, α=2.0 | yes | **3.00** (= onset radius) | **0.00** | **0.965** | 29 (= onset footprint) |
| control: full give | g=0, α=2.0, give=1.0 | **no** | 3.00 | 0.00 | 0.734 | 0.0 |
| control: no escalation | g=0, α=0, give=0.5 | **no** | 3.00 | 0.00 | 0.966 | 0.0 |

- **Seizure**: a SPREADING traveling wave — recruits the whole 41×41 lattice
  (final 1681), front grows to 22.8, propagates (onset-prop 2.23), and the
  spatial profile CHANGES as it travels (post-onset rank-1 drops to 0.42).
- **Hallucination**: a persistent, spatially **STATIONARY** confabulated pattern
  — locked to the onset footprint (final 29, front stays at the onset radius 3,
  zero propagation), self-sustained **after the input drive is removed**, with a
  **fixed** spatial profile (post-onset rank-1 = 0.965). A percept with no input.
- Both are genuine **give-failures** (full give → dies) and both require the
  **escalation** term (α=0 → dies).

**VERDICT: the unifying link holds.** From ONE term (surprise-driven
escalation), coupling it laterally gives a seizure (spreading wave); pointing it
at the source with no lateral spread gives a hallucination (stationary
self-sustained pattern) — the aberrant-precision pathology. Two distinct,
measurably different failure signatures from one mechanism.

---

## Blunt bottom line

**V2 now speaks to the connectivity/hub literature that V1 structurally could
not.** The two named V1 limits both resolved in the predicted direction with
matched controls: (P4) excitatory-recruitment coupling is **pro-ictal** (give\*
rises 0.5375→1.0 with g_rec; the sign flip vs the protective diffusive g is
clean and monotone) — the model can now represent epileptogenic
hyperconnectivity; (P5) high-degree **hubs are the preferred onset locus**
(give\* +0.05, ~2–3× more recruited tissue), modest and honestly at the grid
limit but directionally correct and controlled. Exploratory P6 delivers a second
pathology (hallucination) from the same escalation term. `g_rec=0` reproduces the
published V1 fold byte-identically; the seizure byte-identity-when-off test is
green; no new Rust Term. The remaining honesty: P5's magnitude is bounded by the
scattered-singleton hub topology; thresholds stay model-internal ratios, not
neural units; this is still a hypothesis platform, now with a wider reach.
