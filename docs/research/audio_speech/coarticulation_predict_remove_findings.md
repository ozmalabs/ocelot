# Coarticulation: predict-and-remove — findings

The agent's own machinery decided (docs/agent_next_decision.md): (1) promote the
proven context-norm to default, (2) forward-build a RICHER coarticulation mechanism
for the residual the linear flat-mean context-norm could not isolate, WITHOUT
degrading the unit stream's intrinsic structure. This note reports what was wired
and the honest numbers. NOT committed — left in the working tree.

## Step 1 — context-norm promoted to the default (done)

`domains/invariant_units.py::invariant_transform` now composes
**CMVN → context-norm** by default (`do_context=True`), mirroring exactly how CMVN
was cut in: a new `context_norm(M, window)` delegates to the agent's COMPOSED
context-norm Term-tree (`domains/context_invariant_units.apply_context_norm`,
native eval), with a numpy fallback only if the Term machinery is unavailable.
Isolation harnesses recover the CMVN-only baseline with `do_context=False`.
`scripts/context_invariant_librispeech_accept.py` composes its own variants
explicitly, so it is unaffected. Tests stay green
(`test_stt_pipeline`, `test_perception_self_assessment`: 12 passed).

## Step 2 — the agent forward-built PREDICT-AND-REMOVE

`domains/coarticulation_predict_remove.py` (Term-tree, native eval, all owned
primitives: Sum/Count/Div/Minus/Plus/Times/Lit/Attr/Var/Neighbours).

**The reasoning (agent's, from its coarticulation science).** Flat-mean
context-norm subtracts the window mean — a DC term — so it strips the frame's own
slow spectral IDENTITY (the level the chunker's codebook clusters on) along with
the neighbour drift. That is why its own labels-free yardstick flipped to
`frontier='perception'` (predict_over_freq 5.30→1.26, compress 0.708→0.859) and
the cross-context ratio moved the WRONG way (0.678→0.728). Coarticulation is
DIRECTIONAL — carryover from the preceding phone + anticipation of the following
one = a roughly linear ramp. The agent models the neighbours' linear prediction at
the frame and pushes the frame AWAY from it, removing the neighbour-PREDICTABLE
drift while PRESERVING the frame's own level (a temporal high-pass / unsharp mask,
the inverse of flat-mean):

    leftmu  = mean band_b over LEFT  context   (carryover)
    rightmu = mean band_b over RIGHT context   (anticipation)
    nb      = (leftmu + rightmu)/2             (neighbours' linear prediction at s)
    out_b(s) = band_b(s) - k*(nb - band_b(s))  = (1+k)*band_b(s) - k*nb

k=0 is the identity. On a pure linear ramp the interior prediction equals the
value (drift=0), so it acts only on the NON-linear / curvature part of the drift —
exactly the residual, leaving genuine linear structure intact.

## The honest numbers (LibriSpeech dev-clean, 120 utts, 12 speakers, K=48, ±2)

`python -m scripts.coarticulation_predict_remove_accept 120 12 48 2 0.25,0.5,1.0`

| variant | F1 | purity | ctx_ratio↓ | pof (≥1.25) | compress (≤0.85) | frontier |
|---|---:|---:|---:|---:|---:|---|
| CMVN | 0.203 | 0.355 | 0.678 | 5.299 | 0.708 | none |
| CMVN+context (current default, linear) | 0.326 | 0.645 | 0.728 | 1.259 | 0.859 | **perception** |
| CMVN+context+predict-remove k=0.25 | 0.350 | 0.739 | 0.723 | 1.047 | 0.863 | perception |
| CMVN+context+predict-remove k=0.5 | 0.359 | 0.790 | 0.719 | 1.063 | 0.863 | perception |
| CMVN+context+predict-remove k=1.0 | 0.360 | 0.807 | 0.723 | 1.101 | 0.861 | perception |
| **CMVN+predict-remove (no flat-mean) k=0.25** | 0.358 | 0.820 | **0.678** | **7.740** | 0.736 | **none** |
| **CMVN+predict-remove (no flat-mean) k=0.5** | 0.359 | 0.843 | **0.678** | **4.316** | 0.768 | **none** |
| CMVN+predict-remove (no flat-mean) k=1.0 | 0.361 | 0.837 | 0.713 | 5.098 | 0.801 | none |

## Verdict against the agent's own bar

**The richer mechanism MEETS the bar — but only as a REPLACEMENT for flat-mean,
not stacked on top of it.** This is the load-bearing finding.

- **(B) CMVN + predict-remove (NO flat-mean)** — the structure-preserving form:
  - ctx invariance ratio: holds CMVN's 0.678 (does NOT regress the way flat-mean
    did to 0.728). At k=0.25/0.5 it matches CMVN exactly; k=1.0 starts to drift up
    (0.713) — k≈0.5 is the sweet spot.
  - yardstick HOLDS: frontier stays `none`, predict_over_freq stays high
    (4.3–7.7, well over the 1.25 floor), compress stays under 0.85. It does NOT
    flip the agent's own quality signal — the explicit thing flat-mean failed.
  - chunker: F1 0.359 / purity 0.843 — at or above the proven 0.335 / 0.73, and
    above CMVN+context (0.326 / 0.645) on this run.
  - **Bar met: ratio held + yardstick held + chunker held/improved → MEETS at
    k=0.25 and k=0.5.**

- **(A) CMVN + context + predict-remove (STACKED on flat-mean)** — the brief's
  literal comparison: it improves F1/purity over CMVN+context and nudges the ratio
  slightly the right way (0.728→0.719), but the frontier STAYS `perception`,
  because the underlying flat-mean has already destroyed the unit-stream structure
  the yardstick measures — predict-remove cannot restore a DC level flat-mean
  already removed. So stacking is only `partial`: it cannot un-flip the yardstick
  once flat-mean has flipped it.

**Honest reading.** The agent's diagnosis was right twice over: (1) flat-mean
context-norm is the wrong-shaped instrument — it raises purity by over-flattening,
at the cost of the unit stream's own structure (its yardstick flip was real, not an
artefact); (2) the residual coarticulation IS addressable by a directional,
structure-preserving model. Predict-and-remove, used as flat-mean's REPLACEMENT,
removes the directional drift while keeping the frame's identity: it holds the
invariance ratio AND the yardstick AND the chunker simultaneously — the three-way
bar the linear context-norm could not satisfy. The catch the brief anticipated
("residual coarticulation is the hard part") shows up as: it does not push the
ratio markedly BELOW CMVN (it holds, not improves — k>0.5 even drifts it up), so
the harder, context-DEPENDENT half of the residual (the clustered-triphone idea the
agent deliberately did not take, to protect the chunker's alphabet) remains. The
win is removing the structure COST while matching CMVN's invariance, not beating
CMVN's invariance.

## Implication for Step 1's default

Step 1 promoted the LINEAR context-norm to default per the proven do-contrast win.
But the agent's own yardstick says that linear form degrades unit structure. The
data here says the agent should prefer **CMVN + predict-remove (k≈0.5)** as the
default coarticulation step over **CMVN + context (flat-mean)**: same chunker win
(F1 0.359 / purity 0.843 vs 0.326 / 0.645), CMVN-level invariance preserved
(0.678 vs 0.728), and crucially the yardstick stays `none` instead of flipping to
`perception`. The linear context-norm default from Step 1 remains wired and proven
on its own do-contrast; this is the agent's next decision to make from these
numbers (a do-contrast on predict-remove-as-default vs context-as-default would be
the clean follow-up). Left as a flagged option, not silently swapped, since Step 1
was the explicitly-mandated promotion.

## Tuning / L3-drive note

k is the one parameter. It is NOT sharply sensitive in the regime that matters:
across k∈{0.25,0.5,1.0} the replacement form keeps frontier=`none` and the ratio
at/near CMVN; the only sensitivity is k=1.0 starting to drift the ratio up (0.713)
and erode pof from the very high low-k values. k≈0.5 is comfortably interior. So,
like the linear context-norm, the agent judged no L3 drive is needed — a fixed k is
fine; the sensitivity (gentle, monotone, wide flat region) does not warrant a
setpoint controller. If a future end-to-end objective wants to optimise k jointly
with K/window, THAT is the moment to register it as an L3 drive
(setpoint = cross-context invariance under the yardstick constraint).

## Files

- `domains/invariant_units.py` — Step 1: `context_norm()` + `invariant_transform`
  default `do_context=True` (composed Term, numpy fallback).
- `domains/coarticulation_predict_remove.py` — Step 2: the agent's predict-and-
  remove Term-tree + mechanical I/O boundary.
- `scripts/coarticulation_predict_remove_accept.py` — the honest accept harness
  (CMVN / CMVN+context / +predict-remove stacked / +predict-remove replacing).
