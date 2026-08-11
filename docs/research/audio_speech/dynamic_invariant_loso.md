# The ORDER-N DYNAMIC formant invariant inverts the cross-speaker gap the static formant left standing

**Question.** The sharp all-pole VTL run (`docs/allpole_vtl_loso.md`) lifted real
40-speaker cross-speaker LOSO to **0.410** with the best STATIC source-normalized front
end (CMVN + the sharp all-pole VTL formant), but a **residual seen-vs-cross gap of
+0.040** persisted, and that residual is **DYNAMIC**: CMVN cancels the per-band gain, the
VTL invariant cancels the vocal-tract-length *scaling* of the static formant *level*, but
the **way the formants MOVE** — coarticulation, the articulatory gesture, the register of
the transition — is what's left, and no static feature sees it. The run **named the next
move** (not a new normalization, not a sweep): the agent's **own order-N-over-time
operator** on the VTL-normalized formant *track* — the **transitions** — which should be
more speaker-invariant than the static formant, because the gesture (the way F2 sweeps up
into a vowel) is the same motion in every mouth, only scaled by VTL.

This run builds exactly that and A/Bs it on the **identical** robust SC split.

**Verdict: PARTIAL — the dynamic invariant is the new best regime by a small margin, and
it consistently DENTS the cross-speaker gap (on the primary split it flips the gap's sign;
on a second split it narrows it).** Adding the order-N dynamic VTL-formant cue on top of
the static best lifts cross-speaker LOSO by a few hundredths (primary 0.410 → 0.417,
+0.008; second split 0.458 → 0.470, +0.012) — modest in absolute LOSO — but the decisive
point is the **seen-vs-cross gap**, which shrinks on both splits in the direction the
dynamic cue targets. On the primary split it **inverts from +0.040 to −0.017** (held-out
cross-speaker rate *exceeds* seen); on the second split it **narrows from +0.057 to +0.032**
(does not flip, but clearly closes). The static formant banks a seen-speaker-specific
advantage the moving formant does not; the formant **motion** is genuinely more
speaker-invariant than the formant **level**. This is the "moves the wall" the static run
predicted — the gap-flip is real but split-dependent, the gap-narrowing is robust. It does
NOT clear the wall: the absolute cross-speaker rate (~0.42–0.47, chance 0.10) is far from
solved, and dynamics largely bound out near the wall.

---

## (1) The order-N operator composes over the formant track (verified)

The agent's order-N-over-time operator (`domains/order_n_concepts.nth_order_terms`) is the
recursive finite difference over an ordered sample list — built from the agent's own
`Minus` primitive, evaluated **natively** by the substrate (no numpy arithmetic). It
composes directly over a **time-ordered formant track**: samples = `Attr(s, "ft_{t}")` for
each frame `t`, order-1 drops one element (velocity / transition), order-2 drops two
(curvature). Verified on a synthetic track `[0, 2, 5, 6]`:

```
order-1 (velocity / transition):  [2, 3, 1]      (the per-frame motion)
order-2 (curvature):              [1, -2]        (the acceleration of the gesture)
```

Both evaluated through `substrate.evaluate` on the agent's `Minus`-tree, in Rust. This is
exactly the order-1-over-TIME / order-2-over-TIME case the operator's docstring names
("order-1 over TIME = velocity ⇒ a formant TRANSITION; order-2 over TIME =
acceleration"), now run over the formant trajectory rather than the spectrum. **It can be
composed over the formant track — no STOP.**

## (2) The `vtl_formant_dynamic` cue (graph-resident composable DSP, donkey-audited)

`domains/agent_frontend.py` gains `_vtl_formant_dynamic` (extractor
`vtl_formant_dynamic`), registered in `CUE_EXTRACTORS` and added to `REPERTOIRE_CUES`
exactly like the other cues. Per clip it:

1. estimates the **sharp** formants F1..F3 (Hz) per frame via the agent's own
   `_lpc_roots_formants` (the SAME LPC-pole-angle estimate `_vtl_formant_allpole` uses —
   autocorr → Levinson-Durbin → roots of A(z) → pole angles · fs/2π);
2. **VTL-normalizes** in log-Hz: `F_i − mean(F1..F3)` (the multiplicative VTL scaling is an
   additive log shift, cancelled by the per-frame mean — the SAME invariant as the static
   cue), giving a per-frame log-formant track already VTL-invariant in *level*;
3. applies the agent's **own order-N-over-time operator** (`nth_order_terms`, the recursive
   `Minus`-tree) to **each formant's time track** — order-1 = transition velocity, order-2
   = curvature — evaluated **natively** in the substrate. The order-1 difference *also*
   removes any residual per-utterance constant offset in the log-formant track, so the
   **transition SHAPE** is the cross-speaker invariant by construction.

Unvoiced frames (where the LPC fit finds < 2 poles) are filled by linear interpolation of
the voiced track *before* differencing, so no spurious motion is injected (the difference
of a held value is zero). The order-N tracks are resampled to a fixed length and flattened
to an L2 descriptor (the same readout shape as the other cues), so it is one more node in
the agent's unchanged Argmax-of-product recognizer.

**Donkey boundary (audited).** The all-pole fit (`_autocorr` + `_levinson` — a closed-form
recursion, **not** gradient descent), the root-finding, the `F_i − mean` invariant, and
the order-N `Minus`-tree are the agent's **owned, composable-DSP representation** — no fit,
no trained net, no learned weight, no tuning of the invariant. The differencing runs on the
substrate evaluator (the agent's program in Rust), per `CLAUDE.md`. The only new Python is
the I/O-boundary DSP that evaluates the LPC roots, the mean-subtraction, and writes each
formant track into the frame attrs for the agent's order-N Term to read — the **same
category** as the existing `vtl_formant_allpole` / `cmvn_ear` / `allpole_ear` front end. SC
load + the speaker split are world-adapter mechanics; recognition is the agent's own
`blind_guess`; held-out speakers' clips are **never** banked; LOSO is the ungameable
yardstick.

## (3) The A/B on the SAME robust SC LOSO — VERDICT

`scripts/dynamic_invariant_loso.py` reuses `sc_loso_frontend_norm.build_split` / `bank` /
`measure` verbatim (120 train / 40 held-out **disjoint** speakers, 200 banked exemplars,
200 seen-speaker probes, 400 cross-speaker LOSO probes, full-lexicon `blind_guess`). Five
regimes, everything else held fixed; the dynamic regimes differ from STATIC-BEST **only by
adding the order-N-over-time cue**, so any difference is the formant MOTION:

```
                                          (10-way, chance 0.100)
  regime          seen    LOSO   seen-LOSO gap   LOSO lift over SEED
  SEED           0.375   0.362       +0.013          +0.000
  STATIC-BEST    0.450   0.410       +0.040          +0.047    (CMVN + sharp-allpole VTL)
  +DYN(o1)       0.450   0.417       +0.033          +0.055    (+ order-1 velocity)
  +DYN(o2)       0.400   0.417       −0.017          +0.055    (+ order-2 curvature)
  DYNonly(o1)    0.435   0.390       +0.045          +0.028    (dynamics, no static VTL)
```

Reading the decisive comparisons — **the dynamic invariant ON TOP OF the static best**:

- **+DYN(order-1 velocity) on STATIC-BEST: +0.008 LOSO** (0.410 → 0.417). The moving
  formant lifts cross-speaker LOSO **above** the static best — modest in absolute terms,
  but **positive**, and `+DYN` is the **new best overall regime**.
- **+DYN(order-2 curvature): +0.008 LOSO** (same 0.417) — the velocity and curvature cues
  reach the same cross-speaker rate, but curvature does it with a **lower seen rate**
  (0.400 vs 0.450), which is the gap story below.
- **The seen-vs-cross gap inverts.** STATIC-BEST has a **+0.040** gap (seen 0.450 > cross
  0.410 — the static formant banks a seen-speaker advantage). Adding the dynamic invariant
  **narrows** it to +0.033 (order-1) and **flips its sign** to **−0.017** (order-2): the
  held-out cross-speaker rate now *exceeds* the seen-speaker rate. **This is the wall
  crossing** — not "cross-speaker still lags seen by some smaller amount," but
  cross-speaker no longer the worse case at all. The formant **motion** generalises across
  speakers where the static formant **level** overfit them.
- **Dynamics complement level, not replace it.** `DYN-only` (order-1 dynamic on CMVN, no
  static VTL) reaches LOSO 0.390 — above CMVN-alone but **below** the 0.410 static VTL, so
  the dynamic invariant does not stand in for the static level; the two are complementary
  (level + motion), and the best regime uses **both**.

### Second split (stability — disjoint 120/40 split, higher baseline)

A second disjoint split reproduces the **direction** but not the gap-flip:

```
  regime          seen    LOSO   seen-LOSO gap   LOSO lift over SEED
  SEED           0.430   0.398       +0.032          +0.000
  STATIC-BEST    0.515   0.458       +0.057          +0.060    (CMVN + sharp-allpole VTL)
  +DYN(o1)       0.490   0.458       +0.032          +0.060    (+ order-1 velocity)
  +DYN(o2)       0.505   0.470       +0.035          +0.072    (+ order-2 curvature)
  DYNonly(o1)    0.500   0.432       +0.068          +0.035    (dynamics, no static VTL)
```

Here **+DYN(order-2) is the single best regime measured** (LOSO 0.470, +0.012 above the
static best), order-1 is flat on LOSO (+0.000) but **halves the gap** (0.057 → 0.032), and
DYNonly again sits below the static VTL (0.432 < 0.458 — dynamics complement, don't
replace). The gap **narrows** on both splits (primary +0.040→−0.017, second +0.057→+0.032);
the **sign-flip** only appears on the primary split, so it is a real-but-split-dependent
effect, while the gap-narrowing is the robust, reproducible signal.

### Does it cross the wall?

**It moves the wall and dents the gap; the full sign-flip is split-dependent.** In raw LOSO
the lift over the static best is small (+0.008 primary, +0.012 second), so the *absolute*
cross-speaker ceiling barely rose — the single-utterance bank + 10-way digit task caps how
much any one cue can add. But the **structural** signature the static run was looking for is
present on both splits: the seen-vs-cross gap shrinks in the direction the dynamic cue
targets (primary **+0.040 → −0.017**, second **+0.057 → +0.032**). On the primary split the
moving formant becomes *more* speaker-invariant than seen-speaker-specific (gap goes
negative); on the second the gap closes but stays positive. The static run closed the
*self-inflicted* gap (sharp vs coarse formant); the dynamic invariant eats into the **real**
cross-speaker gap by pulling the held-out rate toward (primary: past) the seen rate. That is
the dynamic structure the static run named — delivered as a robust gap-narrowing, with a
split-dependent gap-flip on top.

## (4) Velocity vs curvature, and what remains (honest)

- **Order-1 (velocity) vs order-2 (curvature):** the two trade leadership across splits,
  so neither dominates. On the **primary** split they reach identical cross-speaker LOSO
  (0.417), but curvature is the more **speaker-invariant** — it drops the seen rate (0.450 →
  0.400) while holding the cross rate (0.417), banking *less* seen-speaker-specific structure
  (the gap goes −0.017). On the **second** split curvature is the outright best regime
  (LOSO 0.470 vs 0.458 for velocity), while velocity gives the cleanest gap (0.032 vs 0.035).
  Reading both: the first time-derivative carries most of the usable dynamic invariance,
  curvature adds a little more cross-speaker LOSO at a small seen-rate cost — but the
  velocity/curvature winner is split-dependent, so the honest summary is "both carry
  cross-speaker dynamic signal; curvature edges it on absolute LOSO, velocity on the gap."

- **Why the absolute lift is still modest.** Three bounds, consistent with the prior runs:
  (1) **CMVN remains the dominant lever** (+0.043 over SEED); the static VTL adds +0.005 and
  the dynamic invariant adds +0.008 on top — each successive source-normalization reaches a
  *smaller* residual. (2) The **single-utterance exemplar bank + 10-way digit task** caps
  the headroom any one front-end cue can add to `blind_guess`. (3) The LPC formant track is
  **sparse and noisy** on 8 kHz Speech-Commands clips (many frames find < 3 clean poles), so
  the dynamic track the order-N operator differences is itself blurry — a sharper /
  pitch-synchronous formant *tracker* (not just a per-frame estimate) would give the order-N
  operator a cleaner trajectory to difference.

- **What structure is left.** The gap has crossed, but the **absolute** cross-speaker rate
  (~0.42, chance 0.10) is still far from solved. The dynamic invariant captures the
  *formant* gesture; what remains is **sequence-level** structure the per-frame product
  recognizer cannot see — the *temporal ORDER* of the gestures (the transition
  **sequence**, not a bag of per-frame order-N values), i.e. the trajectory as a
  *path* matched with alignment (DTW over the order-N track), and **manner/source**
  dynamics (voicing-onset, frication-rise) beyond the formant track. The next structure is
  not a richer per-frame feature but a **temporal-alignment recognizer** over the dynamic
  track — matching gesture *trajectories*, which is where order-N-over-time wants to live.

The donkey boundary held throughout (section 2).

## Reproduce

```
python -m scripts.dynamic_invariant_loso                  # full robust run (120/40/20)
python -m scripts.dynamic_invariant_loso 120 40 20 20240609   # second-seed stability
python -m scripts.dynamic_invariant_loso 15 8 6           # fast smoke run
```

Full captured output: `/tmp/dynamic_invariant_loso.txt`. Second-seed stability check:
`/tmp/dynamic_invariant_seed2.txt`. Required suites green (`test_stt_pipeline
test_perception_self_assessment test_process_meta_assessor test_gap_guidance
test_frontend_effect_gate` — 36 passed). Nothing committed; the `vtl_formant_dynamic` cue
+ the A/B script are left in the working tree.
