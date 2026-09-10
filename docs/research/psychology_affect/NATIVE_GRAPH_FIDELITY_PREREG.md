# Incidence-map fidelity — closing the aperture gap — PRE-REG

**Block**: 323000. Build target: `domains/llm_native_graph.py` (`fit_incidence`,
`incidence_override` on `build_mode_neuron_factor_graph`); measure:
`scripts/llm_native_graph_fidelity_measure.py`. Substrate BP is the PROTECTED
`can_native_bp.py` (`run_loopy_bp`), read-only — built TO.

## Motivation

Block 322 reached PARTIAL aperture-covariance: the explicit incidence map (mode
as a first-class node joined to its neurons by the raw loadings `modes[m,i]`)
gave held-out covariance ~0.75, well above chance/shuffle. Lever (c) proved the
ceiling is STRUCTURAL, not the solver (exact MAP == loopy-BP). Block 322 named
the residual as incidence-map FIDELITY — the raw-loading bipartite graph only
approximately encodes the mode reading. This block attacks the fidelity.

## Claims (falsifiable)

**Claim 1 — fitting the incidence lifts covariance.** Incidence weights FIT on
TRAIN (so the mode-node settle reproduces the mode reading), instead of raw
loadings, raise held-out aperture-covariance above the raw ~0.75. Prediction:
fitted > raw held-out. FALSIFIED IF fitted ≤ raw held-out (raw loadings already
capture what is generalisable).

**Claim 2 — the ceiling is generalisation, not representation.** With fitted
weights, TRAIN covariance approaches 1.0 (full aperture-covariance is
representable) while held-out plateaus below it. Prediction: train ≈ 1.0,
held-out < train, the gap moving with regularisation. FALSIFIED IF train also
caps well below 1.0 (then the incidence cannot represent the reading at all —
a true structural wall).

**Claim 3 — vocab is not the ceiling.** The discrete-state resolution (2state
vs 3state) does not materially move held-out covariance. FALSIFIED IF finer/
coarser vocab shifts it (then discretisation was part of the ceiling).

## Method

- `fit_incidence(modes, mean, Wc, train_x, neuron_idx, n_modes, ridge)`: per
  mode, ridge-regress the neuron states `sign(field)` → the true mode
  coefficient over TRAIN queries; the fitted `W_inc[m,i]` become the incidence
  edge weights (frozen; a recovered incidence, never held-out).
- Build the bipartite mode↔neuron factor graph with `incidence_override=W_inc`,
  settle on the substrate's own `run_loopy_bp`, read the mode-node states
  directly (`read_mode_nodes`), measure held-out covariance vs raw loadings.
- Ridge sweep (regularisation) and a no-BP direct-readout ceiling to separate
  representability (train) from generalisation (held-out).
- Vocab sweep (2state vs 3state) on the raw incidence.

## Anti-faking

- Incidence FIT on the 60-prompt train corpus; covariance on DISJOINT held-out.
- The mode-node self-field is 0, so the reading comes ONLY through the incidence
  (a mode-node carrying its own coefficient self-reads trivially — excluded).
- Train-vs-held-out reported explicitly so "representable" (train) is never
  conflated with "achieved held-out".
- Fine-aperture propagation runs on the substrate's OWN BP (protected,
  read-only, built-to; no new node/edge types).
- Honest whichever way — a partial lift is reported as partial, and the residual
  named (generalisation at this data scale; the between-layer transport
  incidence as the structural next axis).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.
