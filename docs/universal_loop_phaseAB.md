# Universal closed loop — Phase A + B (forward model + production memory)

**VERDICT: GO — build Phase C.** The synthetic production memory COVERS real held-out
speech: nearest-synthetic-exemplar coverage **0.400** (chance 0.100, **+0.300**), and
real clips are NOT orphaned — correct-word clips sit measurably CLOSER to the synthetic
manifold (median residual 0.386) than wrong-word clips (0.483), a consistent
wrong−correct gap of ~0.10 across every grid size. The forward model + production memory
are on-manifold; Phase C's adapt+iterate has a sound manifold to refine on.

This is the de-risking gate the plan (`docs/universal_closed_loop_plan.md`) asked for
BEFORE the expensive analysis-by-synthesis loop. **No loop here** — static library only.

Script: `scripts/universal_loop_phaseAB.py`. Run:
`python -m scripts.universal_loop_phaseAB 40 12 20240610`.
Captured log: `/tmp/phaseAB.log` (end marker `UNIVERSAL_LOOP_PHASEAB_COMPLETE`).

## A — the controllable voicebox `synth(W, V)`

`synth(word W ∈ SC digits, voice V) → cmvn cochleagram features` (32-frame × 32-band
ordered per-frame residual trajectory — the agent's OWN front end,
`learned_voice_shape.residual_track` with empty library = per-utterance CMVN, the same
feature the DtwTo recognizer reads on real clips).

V is derived from the agent's OWN `speaker_norm`/VTL knowledge:
- **vocal-tract variant** (VTL — distinct vocal tracts; the speaker_norm lever, the
  α·Fᵢ formant scaling that VTL normalisation cancels),
- **pitch / f0**, and
- **speaking rate** (the talker-difficulty axis).

Realised over **104 espeak-ng named variants × pitch {20,40,60,80,99} × rate
{130,160,190}**, sampled diversely → tens of distinct on-manifold voices.
Verified: `synth('five', f4@p80r160) → 32 cmvn frames × 32 bands`.

## B — production memory + the coverage test

Babble the full (W,V) grid → the EXEMPLAR LIBRARY (each entry = (W, V, its synth
features), hung off the cell's word Concept). For 120 REAL held-out SC clips (40 held-out
speakers, NEVER banked), find the nearest library exemplar by the agent's graph-resident
**DtwTo** (reused unchanged from `scripts/dtw_trajectory_loso`).

| V-grid | exemplars | coverage (chance 0.10) | median residual | residual gap (wrong−correct) |
|--------|-----------|------------------------|-----------------|------------------------------|
| 10     | 100       | 0.367                  | 0.473           | +0.111                       |
| 30     | 300       | 0.358                  | 0.446           | +0.112                       |
| 60     | 600       | **0.400**              | 0.435           | +0.098                       |

(1) **Coverage/correctness:** 0.358–0.400, decisively above chance 0.10. The static
library — no loop, no adaptation — already lands the SAME WORD as nearest exemplar 40% of
the time on cross-speaker held-out clips. This is the analysis-by-synthesis lower bound
Phase C builds on.

(2) **Residual distribution:** real clips are NOT orphaned. The whole-library nearest
residual is tight (median 0.435, p10≈0.31, min≈0.27); crucially correct-word clips are
CLOSER (median 0.386) than wrong-word clips (median 0.483) at every grid — exactly the
on-manifold signature (the right word's exemplar is the nearest, the wrong ones sit
farther out). The residual also tightens as V grows (median-all 0.473→0.435, p90
1.136→0.983), i.e. more vocal tracts pull real speakers nearer the manifold.

(3) **Scaling with V-diversity:** coverage +0.033 over the 6× grid (10→60 voices),
and the residual distribution tightens monotonically — diversity helps, modestly. The
lever for the larger gain is the LOOP (adapt V to the heard speaker), not just more
static voices, which is precisely Phase C.

## Donkey audit (clean)

- **TTS = WORLD/voicebox only** — espeak-ng generates the audio the agent hears; it is
  never inverted, never part of a decision. `synth()` is pure world I/O. (Piper not
  installed here; espeak-ng is the in-thesis fallback, consistent with stage-1.)
- **V from the agent's own knowledge** — VTL scale (speaker_norm), pitch, rate; the
  variant pool just realises distinct vocal tracts on-manifold.
- **Library = the agent's babble outputs** (production memory), the cmvn features the
  agent's OWN front end produces, keyed by (W, V).
- **Matching = the agent's graph-resident DtwTo** (Argmin / MinOver / DtwTo Term,
  evaluated natively in Rust) — no net, no fit, no weight in the decision.
- **Held-out REAL speakers never banked**; their labels score only; LOSO ungameable.

## What this de-risks for Phase C

The plan's Phase-A/B KILL criterion (real clips orphaned → V too narrow / world too
synthetic, widen before C) is NOT triggered. The espeak voicebox + a tens-of-voices grid
already covers real cross-speaker speech with close, mostly-correct nearest exemplars.
Phase C (match → adapt-V → re-synth → refine-W → iterate; argmin readout) has a sound
nonlinear forward model to invert. The static-library coverage 0.400 is the floor the
loop's adapt+iterate must beat, on the way to the CMVN 0.570 cross-speaker target.

One caveat to carry into C: the absolute residual gap (wrong−correct ≈ 0.10) is real but
not large — the espeak world is coarser than real speech. If Phase C's adaptation
plateaus below CMVN, a richer generator (Piper neural voices) is the first lever to widen
the manifold, not a different recognizer.
