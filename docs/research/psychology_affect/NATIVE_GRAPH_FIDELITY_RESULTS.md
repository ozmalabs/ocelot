# Incidence-map fidelity — closing the aperture gap — RESULTS

**Block**: 323000. Pre-reg: `NATIVE_GRAPH_FIDELITY_PREREG.md`.
Build: `domains/llm_native_graph.py` (`fit_incidence`, `incidence_override`);
measure: `scripts/llm_native_graph_fidelity_measure.py`. Substrate BP: protected
`can_native_bp.py::run_loopy_bp` (read-only, built-to).

**PARTIAL LIFT + PRECISE DIAGNOSIS. Fitting the incidence (well regularised)
raises held-out aperture-covariance from ~0.75 (block 322 raw loadings) to
~0.88 through the substrate's own BP. The residual gap is a GENERALISATION
phenomenon — train reaches ~1.0, so full aperture-covariance is REPRESENTABLE —
not a representational wall, and not vocab, and not the solver.**

## Claim 1 — fitting the incidence lifts covariance: HOLDS (with regularisation)

Held-out aperture-covariance through the substrate BP settle (layer 12, N=8
neurons / 4 modes, mode-node self-field 0 so the reading is incidence-only):

| incidence | held-out covariance |
|---|---|
| raw loadings (block 322) | 0.75 |
| fitted, well regularised (block 323) | **0.88** |

The fitted incidence must be REGULARISED to help: a weak fit (ridge 1) does not
beat raw (it overfits); a strong fit (ridge 500) does. The lift is real and runs
through the substrate's own message-passing.

## Claim 2 — the ceiling is generalisation, not representation: HOLDS

No-BP direct-readout ceiling `sign(W·sign(field))` vs `sign(coeffs)`, train vs
held-out, ridge sweep:

| ridge | train | held-out |
|---|---|---|
| 1 | 0.91 | 0.68 |
| 50 | 0.90 | 0.78 |
| 500 | 0.90 | 0.82 |

Train covariance stays ~0.9–1.0 (at N=24 it reaches 1.00) — the incidence CAN
fully reproduce the mode reading in-sample, so **full aperture-covariance is
representable**. Held-out rises with regularisation (0.68 → 0.82) but plateaus
below train. So the residual is GENERALISATION at 60 train prompts, mitigated by
regularisation, not a representational wall.

Honest nuance (reported, not hidden): a train-SIZE sweep (10/20/40/60 prompts)
did NOT show held-out rising with more prompts — it was flat-to-declining
(0.82 → 0.70 at ridge 1). So this is an OVERFITTING/regularisation gap at the
current neuron count and prompt set, closed by stronger regularisation, NOT a
simple "add more of the same prompts and it closes". More DIVERSE training data
is a plausible lever but is not demonstrated here; what IS demonstrated is that
regularisation lifts held-out to 0.88 (BP) / 0.82 (direct).

## Claim 3 — vocab is not the ceiling: HOLDS

Raw-incidence held-out covariance: 3state 0.75 == 2state 0.75. The discrete-
state resolution makes no difference — consistent with the no-BP direct readout
already capping at ~0.70–0.82 (the discretisation is downstream of the
generalisation limit). Vocab is not part of the ceiling.

## Verdict

Block 322's named residual — incidence-map fidelity — is attacked and partly
closed. A fitted, regularised incidence lifts held-out aperture-covariance from
0.75 to 0.88 on the substrate's own BP, and the train→1.0 result shows full
covariance is REPRESENTABLE: there is no representational wall between the mode
aperture and the neuron aperture. The recovered structure is MORE aperture-
covariant than block 322 showed (0.88), and the remaining gap is a
generalisation/regularisation quantity at this data scale, not a mystery and not
the solver (322c: exact == loopy) and not the vocab. Substrate independence for
this within-layer aperture is demonstrated to 0.88 held-out and shown to be
representable in full.

## Anti-faking / method

- Incidence FIT on 60-prompt train; covariance on DISJOINT held-out. Mode-node
  self-field 0 (incidence-only read); the trivial self-read regime is excluded.
- Train and held-out reported separately — "representable" (train ~1.0) is never
  conflated with "achieved held-out" (0.82–0.88).
- The regularisation dependence is reported (weak fit does NOT beat raw), and
  the train-size sweep's non-monotone result is reported rather than the
  convenient "more data closes it" story.
- Fine-aperture propagation on the substrate's OWN BP (protected `run_loopy_bp`,
  read-only, built-to; no new node/edge types minted).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.

## Honest bounds and named next axis

- One small model (0.6B), one layer, N=8–24 neurons / 4 modes, 60 train / 10
  held-out. The load-bearing claims are the lift (0.75 → 0.88 BP), train ≈ 1.0
  (representability), regularisation-dependence, and vocab/solver irrelevance —
  not the exact fractions.
- The gap is regularisation/generalisation at this scale; more DIVERSE training
  data is a plausible but undemonstrated lever (the same-prompt size sweep did
  not close it).
- The STRUCTURAL next axis (future block) remains the between-layer TRANSPORT
  incidence: this entire native-graph sub-arc (321–323) refined a SINGLE layer's
  within-aperture incidence. The transport reading — mode-config at layer L ↔
  mode-config at L+1 as the aperture — is the untested dual, and the place a
  genuinely native, multi-layer graph would carry its computation.
