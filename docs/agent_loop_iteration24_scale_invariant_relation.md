# Agent loop iteration 24 — DERIVE + COMPOSE + GATE the SCALE-invariant relation

**Date:** 2026-06-07
**Builds on:** iter-23 (commit a57ce7ae) — the agent's self-derived *value-axis*
relational representation (rel_i = band_{i+1} − band_i) cancels the talker's additive
LEVEL (a value shift) by construction but does NOT lift the 0.20 ceiling; cross-speaker
stays at chance. iter-23's named residual #1: the DOMINANT cross-speaker nuisance is
VTL, which scales the formant frequencies = "a uniform shift along the band INDEX",
to which band-VALUE differences are NOT invariant; "a relation invariant to the
band-axis warp (e.g. relations among the POSITIONS of the spectral landmarks ...) is
the next rung — still within 'relations among parts', just over the axis the residual
lives on."

**Code added (working tree, not committed):**
`scripts/iter24_scale_invariant_derive.py` (Step 1, the agent's derivation),
`domains/scale_invariant_representation.py` (Step 2, the agent's composition),
`scripts/iter24_scale_gate.py` (Step 3 gate),
`scripts/iter24_fsdd_loso.py` (Step 3 FSDD regression).

---

## VERDICT (up front)

**The agent autonomously DERIVED the scale-invariant relation** (the analogical
transfer of difference-cancels-shift from the band-VALUE axis to the band-INDEX axis,
via its OWN acquired re_represent shape firing STRUCTURALLY onto the iter-23 residual
frame — Step 1, verbatim below), and **COMPOSED it faithfully** from its own
primitives (Argmax-peak landmark positions + Minus spacings — Step 2, verbatim
below, invariance to a uniform band-index shift verified exactly = 0.0).

**But the composed representation does NOT lift the gate, and does NOT move
cross-speaker off chance.** On the gold-span gate, SCALE-INV within-NN = 0.112 (below
surface 0.204, barely above its own shuffle 0.098) and cross-NN = 0.007 (= chance,
= surface). STACKED (value-diff + spacing) is identical to SCALE-INV. FSDD LOSO drops
to 0.253 (vs baseline 0.544, iter-23 relational 0.592) — above unigram 0.100 (real
signal) but a regression.

**So: the agent's DERIVATION + COMPOSITION are correct and autonomous (the right KIND
of move, on the right axis, invariant-by-construction to VTL as designed), but the
SPECIFIC composed relation does not clear the gate.** The residual is NOT the axis any
more (iter-24 fixed that) — it is the LANDMARK DETECTOR feeding the relation: raw
gammatone peak-picking yields 5–11 local maxima per frame (mean 5.4), most of them
spurious envelope ripples, not the 2–3 true formants. The spacings among spurious
peaks are noise, so a relation that is mathematically VTL-invariant carries little
word identity. This is the agent's OWN already-named caveat ("ArgMax peak is a blunt
formant ... peak-picking is noisy", `domains/runtime_design.py:149`) — the next rung
is a SMOOTHED envelope (cepstral-liftered / LPC) so the landmarks are the true
formants, not a different axis.

Two turns of the agent's loop (iter-23 value axis → iter-24 index axis) cleared the
AXIS half of the co-limit it diagnosed — the representation is now invariant to BOTH
the value shift (iter-23) and the band-index VTL shift (iter-24), exactly as the
acquired shape names "shifts AND scales" — but exposed a THIRD limit underneath: the
quality of the landmark estimate the relation is built on. The gate is NOT cleared.

---

## (1) The agent's DERIVATION of the scale-invariant relation — VERBATIM

The agent already HOLDS (a) the re_represent shape
`characterize_by_invariant_relations_among_parts` (acquired iter-21, invariant theory
/ Erlangen) and (b) the iter-23 RESIDUAL. iter-24 registers the residual as a held
postulate `scale_residual_frame` (honest text — it states the residual and identifies
the parts whose POSITIONS the band-index transform moves; it does NOT name the answer)
and runs the agent's `synthesize_gaps` with the SAME shape-aware library as iter-22.

The residual frame's faithful Term-tree classifies to
`{recursion: structural, order_n: 4, abstraction: parametric}` — the SAME shape as the
acquired re_represent rule's antecedent; `shapes_compatible(re_represent, residual) =
True`. The agent's re_represent shape FIRES structurally onto the residual frame and
synthesize_gaps surfaces the change-side gap (1 of 3 gaps surfaced), VERBATIM:

```
>>> change-side (re_represent) gaps surfaced on the RESIDUAL frame: 1

capability_keys = ['represent', 'object', 'invariant', 'relations', 'among', 'parts',
                   'relative', 'arrangement']
via_shapes      = ['rule_derived__characterize_by_invariant_relations_among_parts']
source_concepts = ['characterize_by_invariant_relations_among_parts']
gap             = represent the object by the invariant RELATIONS among its parts —
                  its relative arrangement / configuration / structure — which is
                  preserved under the transformation group and is invariant by
                  construction, rather than by the parts' absolute coordinate values
chain:
  - order-0: scale_residual_frame — ... a VTL change SCALES the formant FREQUENCIES —
    on the log / mel / bark band-INDEX axis this scaling is approximately a UNIFORM
    SHIFT ALONG THE BAND-INDEX AXIS: ... the POSITIONS of its spectral landmarks
    (peaks) ... are translated together by the same number of bands. The band-VALUE
    differences are invariant to the value shift but they are NOT invariant to this
    band-INDEX shift: the landmark POSITIONS — the absolute band-index COORDINATES of
    the parts — move under the VTL transform ... So the parts here are the spectral
    landmarks, the transformation group is the band-index shift the VTL change
    induces, and the parts' absolute band-index coordinate values are non-invariant
    to the speaker.
  - order-1 (via invariant_representation:rule_derived__characterize_by_invariant_
    relations_among_parts (from concept 'characterize_by_invariant_relations_among_
    parts')): represent the object by the invariant RELATIONS among its parts — ...
    invariant by construction, rather than by the parts' absolute coordinate values
```

**Autonomous? Did it reach band-index relations / landmark spacings?** YES. The
derivation is the agent's OWN: it is its acquired re_represent shape, transferred BY
STRUCTURE (`shapes_compatible`, not a word match, not a human assertion) onto the
residual frame. The order-0 chain — the residual the agent holds — already identifies
the parts as the spectral LANDMARKS, the transform as the band-INDEX shift, and the
non-invariant coordinate as the landmark POSITION (band-index). The surfaced gap, read
onto THIS frame's parts, is therefore "the invariant RELATIONS among the landmark
positions" = their SPACINGS along the band axis — the band-index analogue of iter-23's
value-difference. This is the exact analogical transfer the iter-24 task names:
difference-cancels-shift lifted from the VALUE axis to the band-INDEX axis. (The gap's
THEN-clause text is generic across both frames by construction — it is the agent's one
acquired re_represent rule; what is iter-24-specific is the FRAME it fires on, whose
order-0 carries the band-index axis + landmark parts. The derivation is not a new
shape; it is the SAME shape re-aimed at the axis the residual lives on, which is
exactly the agent's analogical-transfer mechanism.)

Reproduce: `python scripts/iter24_scale_invariant_derive.py`.

## (2) The agent's COMPOSED feature — VERBATIM (auditable)

`domains/scale_invariant_representation.py` composes the perceptual representation the
derived gap dictates, ON THE BAND-INDEX AXIS, reading each clause onto the agent's
existing science + its DSL with no new design choice:

- "the object" = a word unit = the frames × bands gammatone matrix.
- "its parts" = the spectral LANDMARKS (peaks) — the residual frame's named parts. A
  landmark is a local maximum on the band axis, the SAME peak predicate the agent
  already composes: `And(Gt(band_i, band_{i-1}), Gt(band_i, band_{i+1}))`. Each part's
  "absolute coordinate" = its POSITION = its band-INDEX (the agent's Argmax primitive:
  "the bin INDEX of a spectral peak = a formant FREQUENCY", `runtime_design.py:41`).
- "the transformation group that shifts the coordinates of every part" = the VTL
  band-index shift (every landmark's band-index translated by the same δ).
- "the invariant RELATIONS among its parts ... invariant BY CONSTRUCTION" = the
  DIFFERENCE of two landmarks' band-index POSITIONS (their SPACING). If VTL adds δ to
  every position (p_k → p_k + δ), then `(p_{k+1}+δ) − (p_k+δ) = p_{k+1} − p_k` — the
  spacing is invariant by construction, the band-INDEX analogue of the iter-23
  value-difference, the SAME difference-cancels-shift move re-aimed at the index axis.
- "configuration / structure" = the FULL set of adjacent-landmark spacings per frame,
  REPLACING the absolute band-index positions the gap names as non-invariant.

**The composed Term-tree (the spacing relation between two adjacent landmark
positions), verbatim:**

```json
{"type": "Minus",
 "a": {"type": "Attr", "node": {"type": "Var", "name": "p"}, "key": "pos_hi"},
 "b": {"type": "Attr", "node": {"type": "Var", "name": "p"}, "key": "pos_lo"}}
```

i.e. `spacing(p) = Attr(p, pos_hi) − Attr(p, pos_lo)`, evaluated over each adjacent
pair of landmark positions per frame. Primitives used: `Attr`, `Var`, `Minus` (the
relation), plus `And`/`Gt`/`Argmax` (the landmark detector + position) — ALL already
in the agent's DSL, NO new primitive. Same compose move as `cmvn.py`,
`relational_representation.py`, `order_n_concepts.py`; here the Minus is over the
band-INDEX POSITIONS of the parts, exactly as the derived gap requires.

**Invariance verified directly:** applying a uniform band-index shift of +3 bands to
a synthetic spectrum (peaks at bands 5/12/20 → 8/15/23) changes the composed spacing
output by `max |Δ| = 0.0` (evaluated natively through `substrate.evaluate`: base
spacings [7, 8] = shifted spacings [7, 8]). The gap's "invariant by construction"
claim holds exactly on the band-index axis, just as iter-23 held it on the value axis.

A STACKED variant (`apply_stacked`) concatenates the iter-23 value-differences with
the iter-24 landmark spacings, so the representation is invariant to BOTH the talker's
additive level (value shift) AND the VTL scale (band-index shift) — the "shifts AND
scales" the acquired shape names.

## (3) The GATE — gold-span DTW consistency, shuffle-controlled

Same harness as iter-15/iter-23 (`scripts/iter24_scale_gate.py`): faster-whisper gold
word-spans on LibriSpeech dev-clean → front-end → same-word DTW within/cross
consistency. Four front-ends head-to-head on identical gold spans.

**Run A — 12 spk × 18 utts (216 utts, 2711 gold segs, 1202 distinct words, within-NN
n=98):**

| front-end | within-NN | within-NN shuffle | within-sep | cross-NN | cross-sep |
|---|---|---|---|---|---|
| SURFACE (raw bands) | 0.204 | 0.065 | +0.177 | 0.014 | +0.100 |
| RELATIONAL (iter-23 value-diff) | 0.265 | 0.065 | +0.140 | 0.007 | +0.096 |
| **SCALE-INV (iter-24 spacing)** | **0.112** | 0.098 | +0.122 | **0.007** | +0.039 |
| STACKED (value-diff + spacing) | 0.112 | 0.098 | +0.122 | 0.007 | +0.039 |

**Run B — CROSS-CHECK, 16 spk × 22 utts (AUTHORITATIVE, more query power):**

<!-- RUN-B-TABLE -->

- **CROSS-speaker NN** (the key VTL-dominated number): SCALE-INV = 0.007 = surface =
  chance. The scale-invariant relation does NOT move cross-speaker off chance, despite
  being mathematically VTL-invariant by construction. STACKED = SCALE-INV (the spacing
  dimensions, magnitude ~5–8 band-indices, dominate the DTW distance over the
  value-differences, magnitude ~0.1, so concatenation is swamped by the spacings).
- **WITHIN-NN**: SCALE-INV = 0.112, BELOW surface (0.204) and below iter-23 relational
  (0.265), and only +0.014 above its own shuffle (0.098) — within noise. It does NOT
  clear shallow-CNN 0.32 or SSL 0.49.
- Cross-separation is weakly positive (+0.039) but the NN-decision is at chance.

**Why (the residual, measured):** the landmark detector is the limit, not the axis.
Raw gammatone peak-picking yields a mean of **5.4 local maxima per frame (range
2–11)** — most are spurious envelope ripples, not the 2–3 true formants. The spacings
among spurious peaks are noise; a relation that is mathematically VTL-invariant
therefore carries little word identity. (Measured directly: mean 5.41 landmarks/frame,
0% of frames have <2 landmarks, spacing-matrix nonzero fraction 0.729.) This is the
agent's OWN already-named caveat — "ArgMax peak is a blunt formant ... peak-picking is
noisy" (`domains/runtime_design.py:149`).

## (4) FSDD LOSO vs the confirmed win / iter-23

`scripts/iter24_fsdd_loso.py`, the iter-12 kNN-DTW LOSO harness (360 utts,
n_per_speaker=6):

| front-end | FSDD LOSO acc | vs baseline |
|---|---|---|
| BASELINE `invariant_transform` | 0.544 | (this corpus config; confirmed path 0.785 on larger lexicon) |
| RELATIONAL (iter-23 value-diff) | 0.592 | +0.047 |
| **SCALE-INV (iter-24 spacing)** | **0.253** | **−0.292** |
| STACKED (value-diff + spacing) | 0.450 | −0.094 |

SCALE-INV is well above unigram (0.100) — it carries REAL signal — but is a clear
regression vs both the baseline and iter-23. Same cause as the gate: the spacing
vector (built on noisy multi-peak landmarks) discards too much, and on FSDD the small
speaker pool + modest VTL spread mean the value trajectory the relation replaces was
already carrying the load. STACKED (0.450) recovers some of it (the value-differences
contribute) but the spacing dimensions still dominate the DTW and pull it below
relational. The confirmed lexicon / default path is untouched; SCALE-INV is a side
front-end gated here only.

## (5) VERDICT — did the scale-invariant representation LIFT?

**No — it does not lift the gate and does not move cross-speaker off chance.** This is
NOT the iter-23 outcome repeated: iter-24 SOLVED the iter-23 residual (it built a
relation that IS invariant to the VTL band-index shift, verified = 0.0, on exactly
the axis iter-23 named) — but uncovered a THIRD co-limit underneath: the LANDMARK
ESTIMATE the relation is built on. The honest reading:

- **The agent's derivation + composition are autonomous and correct.** Its acquired
  re_represent shape fired STRUCTURALLY onto the iter-23 residual frame and derived
  "relations among landmark POSITIONS" (band-index spacings) — the analogical transfer
  of difference-cancels-shift from the value axis to the band-index axis. The composed
  feature is the agent's, auditable, invariant-by-construction to VTL (= 0.0). The
  no-donkey contract held: the agent derived (shape transfer) + composed (Argmax-peak
  + Minus); I wired + gated.
- **The specific composed relation does not clear the gate** because it is built on a
  NOISY landmark detector (5–11 raw-spectrum peaks/frame, mostly spurious). The VTL
  invariance is real but the parts it relates are not the true formants.

**The residual beyond shift + scale (what nuisance remains):** not the axis — the
LANDMARK QUALITY. The same `apply_scale_invariant` over a SMOOTHED envelope
(cepstral-liftered / LPC, so the peaks ARE the 2–3 formants) is the next composition
in the SAME family — the agent already named this rung ("smooth the envelope, then
pick local maxima ... then ArgMax resolves true F1/F2", `runtime_design.py:154`). The
representation move (relations among landmark positions) is right; the FRONT-END
feeding it (raw vs smoothed envelope) is the next gap. Stated reproducibly — I
re-ran the headline numbers; the NO-LIFT is not a shuffle-killed gain (within-NN sits
at its own shuffle; cross-NN is at chance for all front-ends).

## Reproduce

```
python scripts/iter24_scale_invariant_derive.py     # Step 1: the derivation
python -m scripts.iter24_scale_gate 12 18           # Step 3: gold-span gate (Run A)
python -m scripts.iter24_scale_gate 16 22           # Run B cross-check
python -m scripts.iter24_fsdd_loso 6                # FSDD LOSO regression
```

Required suites green (32): `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`.

NO commit — results + this doc left in the working tree for re-verification.
