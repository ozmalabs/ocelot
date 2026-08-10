# Lever chain — the self-sustaining speech climb, run to its honest wall

## (0) VERDICT — LEAD

**The loop self-sustained and stayed honest the whole chain, and it STOPPED at a
real, named wall on the FIRST proposed rung.** I drove the lever the
forward_model_drive named — an explicit per-speaker VTL/rate WARP on the
generative forward model — and the grounding gate REOPENED it on **every
formulation**: the warp does not climb on this cohort. Zero ungrounded gains were
kept; every dud was caught by the do-contrast + world-measure and self-corrected.
The cumulative recognition stayed at the prior best (band-space baseline 0.3222).

This is the loop working as designed: I proposed the named lever, BUILT it three
ways, GROUNDED each against the prior best, and the gate refused all three because
the measured numbers contradicted the felt "a sharper forward-model frame should
help." A REOPEN is the loop succeeding, not failing — the only failure would have
been committing the warp on intuition. The honest result is that **on FSDD digits
the explicit VTL warp is redundant-to-harmful with the multi-exemplar manifold +
DTW**, and the real next lever is NEEDS-ACQUISITION (more speakers / a real
multi-speaker corpus / a sharper VTL estimate), not another warp.

Run (n=6, 360 recordings, 6-speaker LOSO — matching forward_model_drive's count)
captured to `/tmp/leverchain_full.log` (`===MARKER_LEVERCHAIN_COMPLETE===`,
`elapsed 72.0s`, pgrep-verified GONE). `scripts/solve_for_n.py` and CortexLoop
left UNTOUCHED.

---

## (1) THE CHAIN TABLE — read the numbers, not the booleans

All rungs in the **32-band log-frequency trajectory space** (the warp-able
representation — a VTL scale is a constant shift there; `warp_bands` is exact),
same ear, same native DtwTo recogniser, same FSDD LOSO data. Only the
forward-model template preparation changes per rung.

| rung | lever | grounded delta vs its baseline | cumulative recognition | verdict |
|---|---|---|---|---|
| 0 | multi-exemplar manifold, **no warp** (prior best, re-measured here) | — | **0.3222** | BASELINE |
| 1 | VTL warp — template **into the heard talker's frame** (AbS-correct) | **−0.0694** | 0.3222 | REOPEN |
| 2 | VTL warp — forward-VTLN **both sides to canonical** (speaker-neutral) | **−0.0611** | 0.3222 | REOPEN |
| 3 | VTL warp on the **single-mean** model (isolation arm, own baseline 0.2972) | **−0.0500** | 0.2472\* | REOPEN |
| 4 | global **rate warp** (time-normalise template to heard tempo) | **+0.0000** | 0.3222 | REOPEN |

\* rung 3 is the isolation arm; it has its own baseline (single-mean no-warp
0.2972) and does NOT advance the main cumulative.

**Grounded rungs the loop self-sustained: 0. Cumulative recognition: 0.3222
(unchanged — the gate kept the prior best).** Every warp arm regressed or was
flat; the two-sided gate (do-contrast delta > +0.005 AND world-measure agrees)
refused all of them, and the world-measure re-ran the actual recogniser on every
rung and AGREED with each claimed number (so the regressions are real, not a
broken instrument).

### Why the chain self-selected these rungs (it picks each lever)

- **R0 → R1:** R0's own residual error profile (worst words `eight` 0.06, `zero`
  0.19, `four` 0.28) plus the lever forward_model_drive explicitly named → the
  per-speaker VTL warp into the heard frame.
- **R1 → R2:** R1 regressed; the loop did NOT abandon the lever — it named the
  next *design* (the standard forward-VTLN-both-sides-to-canonical, instead of
  warping into one heard frame). Also regressed.
- **R2 → R3:** two warp regressions on the manifold → the loop named the
  ISOLATION arm: does the warp help where it has the MOST to do (the single-mean
  model, no manifold to absorb VTL)? **It hurts there too (−0.0500).** This is the
  decisive measurement — it rules out "the manifold already did the warp" and
  pins the cause on the warp itself.
- **R3 → R4:** the rate arm (the other half of "VTL/rate warp"). DTW already
  absorbs local rate; the residual global-tempo warp adds **exactly nothing**
  (+0.0000) — DTW had it covered.

---

## (2) WHERE / WHY it stalled — the NAMED wall

**DIMINISHING-RETURNS bottoming out into NEEDS-ACQUISITION.** Every warp arm came
in below the +0.005 non-noise floor, AND — the load-bearing evidence — the warp
did not even help the single-mean isolation arm. So the wall is not "the manifold
saturated the warp's value"; it is sharper:

> The explicit band-VTL warp is **counterproductive on FSDD digits**. The VTL
> estimate is read off the spectral centroid of short (~0.4 s) digit utterances on
> a coarse 32-band axis; that estimate is noisy, and `warp_bands`' band-axis
> interpolation further blurs an already-coarse spectrum. The multi-exemplar
> nearest-template DtwTo match already handles cross-speaker variation well enough
> that injecting a noisy warp **degrades** it rather than helping — on every
> formulation, on both the manifold and the single mean.

The honest floor is therefore **NEEDS-ACQUISITION**, two-pronged:
1. **More speakers / a real multi-speaker corpus.** With only 5 LOSO train
   speakers the medoid manifold spans the cohort cheaply, leaving the warp nothing
   to add; the warp's value (if any) only appears across a wider talker range than
   FSDD's 6 speakers provide.
2. **A sharper VTL estimate** than a centroid off a coarse band axis — itself a
   perception-side acquisition (formant tracking the blunt cochlea under-resolves).

This is consistent with the binary-admissibility thesis: the warp is not a smooth
knob that "helps a little"; on this venue it is simply not an admissible
improvement, and the gate reports exactly that — zero, with a regression.

---

## (3) Did it stay honest the whole chain?

**Yes — every gain was grounded, every dud self-corrected, no ungrounded gain
kept.**

- Each rung is a do-contrast vs the prior best (or, for the isolation arm, vs the
  single-mean no-warp baseline) on the SAME data / ear / recogniser — only the
  template prep changes.
- The `silent_failure_grounding.grounding_check` fired on stakes 0.9 every rung
  and the world-measure RE-RAN the actual recogniser; it AGREED with each claimed
  number to <0.001 (so the pipeline is not overclaiming — the regressions are
  real).
- The two-sided gate REOPENED all four warp arms (delta ≤ +0.005). Prior best
  never advanced on a felt "it's better"; it advanced zero times because nothing
  cleared the floor.
- The single failure mode the directive names — an ungrounded gain kept without
  measuring — **did not occur**. The chain's value is precisely the four caught
  REOPENs: the loop refused the lever its own prior step named, because the world
  said no.

One honesty note on absolute numbers: forward_model_drive measured its prior best
(0.325) in the **A1-patch** space; this chain runs in the **32-band log-freq**
space (the only cleanly warp-able representation), where the same multi-exemplar
model measures 0.3222. The chain is internally self-consistent (every rung
do-contrasted against the band-space baseline); the two baselines are close
(0.322 vs 0.325) and are NOT conflated — the warp deltas are all measured within
the band space.

---

## (4) Donkey / architecture audit

- **The recognition decision is NATIVE.** The per-exemplar synth-error is the
  graph `DtwTo` Term (`recognition_graph.synth_error_term`) evaluated by
  `substrate.evaluate` in Rust (`scripts/lever_chain.py:188`). The
  min-over-exemplars + argmin-over-words is a READOUT over native distances — a
  query, identical in kind to the existing AbS argmin-over-words winner.
- **The WARP is owned DSP at the world-adapter boundary**, reusing the agent's OWN
  VTL science: `invariant_units.estimate_vtl_logalpha` (forward α off the formant
  centre-of-mass) + `invariant_units.warp_bands` (the log-freq-axis shift). The
  medoid pick and the time-resample are mechanical signal ops (like the medoid /
  blunt-downsample in the prior harnesses). No graph decision in Python.
- **The grounding is the real round-trip measurement** — `world_measure` re-runs
  the actual recogniser on the held-out data; the fire / contradiction decisions
  are native Term-trees (`silent_failure_grounding.T_STAKES_FIRE` /
  `T_CONTRADICTION`).
- **Donkey-clean** (grep-audited, `scripts/lever_chain.py`): no `.fit`, no
  gradient, no loss, no optimiser, no net, no `torch`/`sklearn`, no Python
  softmax, **no sweep-to-maximise** — every warp arm is a FIXED structural choice
  and the FULL ablation is reported (into-heard, canonical-both-sides, single-mean
  isolation, rate), never a winning setting cherry-picked.
- `solve_for_n.py` and CortexLoop **untouched** (git-verified: no tracked changes
  to `scripts/solve_for_n.py` or `runners/dsl/`). Reused unchanged:
  `recognition_graph` (DtwTo composition), `silent_failure_grounding`,
  `invariant_units` (VTL science), `scripts/invariant_units_accept`
  (`band_trajectory_matrix`), `scripts/fsdd_learner_world`.

### Is the loop self-sustaining, and where is the honest floor?

The loop **is** self-sustaining as a process: it proposed each lever from its own
diagnosis, built it, grounded it, self-corrected the duds, and named the wall when
the grounding stopped supporting more rungs — without me committing anything on
intuition. What it did NOT do is climb the accuracy, because the first lever it
self-named turned out (when measured) to be a dud on this venue. **That is the
correct outcome to report**: the self-sustaining loop's job is to climb *only as
far as the grounding supports*, and here the grounding said the warp is not the
lever. The honest floor is acquisition — more talkers / a sharper VTL estimate —
not another warp on FSDD's six speakers.

### Files

- `scripts/lever_chain.py` — the chain harness: the warp signal ops (owned DSP),
  the native DtwTo recogniser, the per-rung grounded do-contrast, the
  self-directed rung sequence, the honest wall check. NEW.
- `docs/lever_chain.md` — this report. NEW.
- `/tmp/leverchain_full.log` — full n=6 captured run
  (`===MARKER_LEVERCHAIN_COMPLETE===`).

NOT committed (per directive — coordinate).
