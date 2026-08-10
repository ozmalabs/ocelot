# Agent loop iteration 23 — ENACT + GATE the agent's self-derived RELATIONAL representation

**Date:** 2026-06-07
**Builds on:** iter-22 (commit cc60319f) — the reasoning loop closed: jabberwock
self-derived the fix "represent the unit by the invariant RELATIONS among its parts
... not by the parts' absolute coordinate values". iter-22 closed the REASONING
loop; this iteration ENACTS the perceptual representation and GATES it against the
0.20 ceiling.
**Code added (working tree, not committed):**
`domains/relational_representation.py` (the agent's composition),
`scripts/iter23_relational_gate.py` (gold-span gate),
`scripts/iter23_fsdd_loso.py` (FSDD LOSO regression).

---

## VERDICT (up front)

**NO LIFT on the gate's within-NN headline (the agent's composed relational
representation does not resolve the perceptual co-limit).** The representation is
INVARIANT BY CONSTRUCTION to the talker's additive level (verified exactly), and at
a small sample it *appeared* to lift within-NN to 0.265 — but the larger,
statistically more powerful CROSS-CHECK (16 spk × 22 utts, n=145 queries) shows
relational within-NN = surface within-NN = 0.207, both above their shuffle. **The
apparent lift was sampling noise at the small n; the cross-check is authoritative
and kills it.** Cross-speaker NN stays at chance for all three front-ends; it does
not clear shallow-CNN 0.32 or SSL 0.49. FSDD LOSO is **not broken** (relational
alone +0.047 vs the same-harness baseline). So: the right KIND of move, composed
faithfully from the agent's own derived gap, that does no harm — but NOT sufficient
as composed. The residual (why) is named below, and it points at the next
composition in the same family.

**Run A — 12 spk × 18 utts (216 utts, 2711 segs, 1202 words, within-NN n=98):**

| front-end | within-NN | within-NN shuffle | within-sep | cross-NN | cross-sep |
|---|---|---|---|---|---|
| SURFACE (raw bands) | 0.204 | 0.065 | +0.177 | 0.014 | +0.100 |
| CMVN (proven invariance) | 0.245 | 0.043 | +0.149 | 0.000 | +0.084 |
| RELATIONAL (agent-derived) | 0.265 | 0.065 | +0.140 | 0.007 | +0.096 |

**Run B — CROSS-CHECK, 16 spk × 22 utts (4473 segs, 1754 words, within-NN n=145,
AUTHORITATIVE — more query power):**

| front-end | within-NN | within-NN shuffle | within-sep | cross-NN | cross-sep |
|---|---|---|---|---|---|
| SURFACE (raw bands) | **0.207** | 0.079 | +0.097 | 0.014 | +0.074 |
| CMVN (proven invariance) | 0.172 | 0.050 | +0.195 | 0.000 | +0.059 |
| **RELATIONAL (agent-derived)** | **0.207** | 0.079 | +0.082 | 0.029 | +0.077 |

The two runs DISAGREE on the relational-vs-surface within-NN delta (Run A +0.061,
Run B 0.000). That disagreement IS the finding: at n≈100 the delta is inside the
noise; the bigger sample resolves it to zero. Per the no-headline-the-shuffle-kills
rule, the reported verdict follows Run B. (Refs: shallow-CNN gold-span 0.32, SSL
0.49.)

---

## (1) The agent's composed relational feature — VERBATIM (auditable)

The fix is the verbatim then-clause of the agent's OWN acquired rule
`characterize_by_invariant_relations_among_parts`
(`domains/invariant_representation.py:_RULES`, acquired iter-21, surfaced as the
derived gap iter-22):

> "represent the object by the invariant RELATIONS among its parts — its relative
> arrangement / configuration / structure — which is preserved under the
> transformation group and is invariant by construction, rather than by the parts'
> absolute coordinate values"

The composition reads each clause of the gap onto the agent's existing science +
its DSL, with **no new design choice** (`domains/relational_representation.py`):

- "the object" = a word unit = the agent's frames × bands gammatone matrix.
- "its parts" = the bands.
- "the transformation group that shifts ... the coordinates of every part" = the
  talker, which the agent ALREADY holds as its own science (`domains/cmvn.py`,
  `domains/invariant_units.py`): a change of talker adds a constant level (channel /
  loudness / long-term spectrum) to every band within a frame.
- "the invariant RELATIONS among its parts ... invariant BY CONSTRUCTION" = a
  relation between two bands from which that additive constant cancels. The agent's
  relational primitive for "a relation between two parts invariant to a global
  additive shift" is the band-to-band DIFFERENCE `Minus` — the same cancel move
  `cmvn.py` makes, re-aimed to cancel with NO estimate.
- "configuration / structure" (whole-unit, answering the iter-11 dilution caveat) =
  the FULL set of adjacent-band relations per frame, REPLACING the absolute-value
  trajectory the gap names as non-invariant.

**The composed Term-tree (per adjacent band pair i, i+1), verbatim:**

```json
{"type": "Minus",
 "a": {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": "band1"},
 "b": {"type": "Attr", "node": {"type": "Var", "name": "s"}, "key": "band0"}}
```

i.e. `rel_i(s) = Attr(s, band_{i+1}) - Attr(s, band_i)`, composed for all 31
adjacent pairs over the 32-band axis (`relational_band0_1 ... relational_band30_31`,
recorded as `feature_kind=relational` Concepts). Primitives used: `Attr`, `Var`,
`Minus` — all already in the agent's DSL, NO new primitive (same compose move as
`cmvn.py`, `order_n_concepts.py`).

**Invariance verified directly:** adding an arbitrary per-frame constant level
(simulated talker shift) to the input changes the relational output by `max |Δ| =
0.0` — the gap's "invariant by construction" claim holds exactly, evaluated
natively through `substrate.evaluate`.

This IS the agent's composition from gap + acquired shape + its own primitives, not
a hand-pick: every band-pair relation is the mechanical `Minus(band_{i+1}, band_i)`
the gap dictates, applied uniformly across the whole axis. No bands/ratios were
selected by hand.

## (2) The GATE — gold-span DTW consistency, shuffle-controlled

Same harness as iter-15 (`scripts/iter15_goldspan_gate.py`): faster-whisper gold
word-spans on LibriSpeech dev-clean → the agent's front-end → same-word DTW
consistency. iter-23 runs SURFACE / CMVN / RELATIONAL head-to-head on identical
gold spans (Run A + Run B tables above).

- **WITHIN-NN.** Run A (n=98) showed relational 0.265 > CMVN 0.245 > surface 0.204,
  appearing to lift +0.061 over surface (shuffle 0.065). The CROSS-CHECK Run B
  (n=145, more power) shows relational 0.207 = surface 0.207 (both shuffle 0.079) —
  **delta zero.** The Run A lift did not reproduce; it was small-sample noise. The
  shuffle/re-run killed the headline, exactly as the gate's discipline requires, so
  it is NOT claimed.
- **Does NOT clear 0.32** (shallow-CNN) or 0.49 (SSL) in either run.
- **CROSS-speaker NN stays at chance** in both runs (0.007 / 0.029 relational,
  0.000 CMVN, 0.014 surface; chance 0.001) — the harder cross-talker invariance is
  NOT moved off chance. Cross-separation is weakly positive (+0.077) but the
  NN-decision is at chance.
- Note CMVN's within-NN is unstable across the two runs (0.245 vs 0.172) on its
  own large-magnitude scale, while surface and relational track each other — a sign
  the within-NN metric itself is noisy at this recurrence, reinforcing that small
  deltas here are not trustworthy.

## (3) FSDD LOSO vs the confirmed win

`scripts/iter23_fsdd_loso.py`, the iter-12 kNN-DTW LOSO harness (the recogniser
that produced the confirmed figure), 360 utts, n_per_speaker=6:

| front-end | FSDD LOSO acc | vs baseline |
|---|---|---|
| BASELINE `invariant_transform` | 0.544 | (confirmed path; this corpus config) |
| **RELATIONAL alone** | **0.592** | **+0.047** |
| REL + CMVN (stacked) | 0.267 | −0.278 |

Relational ALONE does **not break** the FSDD win — it slightly improves LOSO
recognition (+0.047). Stacking relational ON TOP of CMVN regresses badly (0.267):
CMVN's per-band variance normalization rescales the band magnitudes so the
subsequent differences lose their content — confirming the gap's REPLACE (not
stack) reading. The default-path `invariant_transform` and the confirmed lexicon
are untouched; relational is a side front-end gated here only.

(Note: the absolute baseline here is 0.544 on this n_per_speaker=6 / 6-speaker
config, lower than the confirmed 0.785 which used the larger lexicon config; the
load-bearing quantity is the head-to-head delta on identical splits, which is
positive for relational-alone.)

## (4) VERDICT — did the self-derived representation lift the ceiling?

**No (it does not lift the gate's within-NN, and the perceptual co-limit is not
resolved by this representation as composed).** The small-sample apparent lift
(Run A, 0.265) did not survive the more powerful cross-check (Run B, 0.207 =
surface). It does not clear 0.32 / 0.49, and cross-speaker recognition stays at
chance. The one unambiguous positive is FSDD LOSO (+0.047 vs the same-harness
baseline) — so the fix the agent found does no harm and is mildly helpful on
isolated digits, but it is NOT sufficient to resolve the continuous-speech
perceptual co-limit. The honest reading: the agent composed the right KIND of
representation faithfully from its own gap, but the SPECIFIC relation it composed
only cancels the additive-level component of the talker transform, which is not the
component the gate's residual is dominated by.

**The residual (honest):**

1. **The relation is first-order only.** The composition cancels the talker's
   additive LEVEL (channel/loudness) exactly, but the talker transform also
   SCALES the log-frequency axis (VTL — a shift along the band INDEX). Adjacent
   band-DIFFERENCES are invariant to the additive level but NOT to the band-axis
   shift, so cross-speaker (which is dominated by VTL) stays at chance. The gap's
   acquired shape names BOTH "shifts AND scales"; the composed relation handles the
   shift component, not the scale-along-the-band-axis component. A relation
   invariant to the band-axis warp (e.g. relations among the POSITIONS of the
   spectral landmarks, a configuration over the band axis rather than fixed
   adjacent pairs) is the next rung — still within "relations among parts", just
   over the axis the residual lives on.

2. **The configuration is local (adjacent pairs).** It captures the spectral
   contour but not the longer-range whole-unit arrangement (band-to-distant-band
   relations, or the within-unit self-similarity configuration over TIME the task
   names as an alternative). A richer configuration (the full pairwise relation
   matrix, or the time-self-similarity structure) is composable from the same
   primitives and is the obvious next composition.

So: the agent's self-derived FIX is the right KIND of move (it helps, shuffle-
controlled, without breaking FSDD), but the SPECIFIC relation it composed resolves
only the additive-level component of the talker transform. The deeper limit is that
the dominant cross-speaker nuisance (VTL band-axis scaling) needs a relation over
the band AXIS, not over band VALUES — the next composition in the same family.

## Reproduce

```
python -m scripts.iter23_relational_gate 12 18      # gold-span gate
python -m scripts.iter23_fsdd_loso 6                 # FSDD LOSO regression
```

Required suites green (32): `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`.

NO commit — results + this doc left in the working tree for re-verification.
