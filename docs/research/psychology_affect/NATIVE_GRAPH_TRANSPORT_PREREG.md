# Between-layer transport aperture — native multi-layer graph — PRE-REG

**Block**: 324000. Build target: `domains/llm_native_graph.py`
(`export_transport_structure`, `fit_transport`, `build_transport_factor_graph`,
`read_transport_modes`); measure: `scripts/llm_transport_aperture_measure.py`.
Substrate BP is the PROTECTED `can_native_bp.py` (`run_loopy_bp`), read-only —
built TO.

## Motivation

Blocks 321–323 refined a SINGLE layer's WITHIN-aperture incidence (mode ⇄ its
neurons), reaching aperture-covariance ~0.75 (raw) → ~0.88 (fitted). But the
whole sub-arc left the structural DUAL untested: the between-layer TRANSPORT
aperture. In the user's framing (edge = node at a different aperture), the
transition between layers is itself a first-class object, and the transport
reading — mode-config at L ⇄ mode-config at L+1 — is where a genuinely native,
MULTI-LAYER graph would carry its computation. This block tests it.

## Claims (falsifiable)

**Claim 1 — the transport is recoverable and generalises.** A linear transport
map T: coeffs_L → coeffs_{L+1} (ridge on train) reproduces the L+1 mode signs on
DISJOINT held-out, well above the naive same-config baseline
(`sign(coeffs_L) == sign(coeffs_{L+1})`). Prediction: held-out sign-covariance
≫ naive. FALSIFIED IF T does no better than naive (the transition is not
recoverable as a low-dim map).

**Claim 2 — the transition is aperture-covariant on substrate BP.** Expressing T
as a bipartite factor graph (L-mode-nodes with external_field = coeffs_L; L+1-
mode-nodes with NO self-field, driven only through transport edges T[m1,m0]) and
settling on the substrate's OWN BP reproduces the true L+1 mode config on held-
out, far above a shuffle-T control. Prediction: BP covariance ≫ shuffle-T, near
the linear baseline. FALSIFIED IF BP ≈ shuffle-T (the substrate settle does not
carry the transport).

**Claim 3 — the transport aperture is a clean native-graph object.** If Claims 1
and 2 hold, the between-layer transport is a cleaner aperture-covariant reading
than the within-layer incidence (blocks 322/323), because the mode-coefficient
transition is low-dimensional (k×k) and strongly linear. Reported honestly.

## Method

- `export_transport_structure`: fit the mode router (all positions), export for
  adjacent layers (L, L+1) the modes/mean/Wc and per-query (train + held-out)
  true mode coefficients at both layers.
- `fit_transport`: ridge T: coeffs_L → coeffs_{L+1} on TRAIN (frozen; the
  recovered transport incidence).
- `build_transport_factor_graph`: L-mode-nodes (external_field = coeffs_L),
  L+1-mode-nodes (self-field 0), transport edges weight T[m1,m0]. NB the
  substrate BP is an UNDIRECTED Ising model, so the transport edges are made
  bidirectional (symmetric coupling) for the message passing to run.
- Settle on `run_loopy_bp`, read L+1-mode-node states (`read_transport_modes`),
  measure held-out covariance vs true `sign(coeffs_{L+1})`; compare to the
  linear-T baseline, a shuffle-T control, and the naive same-config baseline.

## Anti-faking

- Transport FIT on the 60-prompt train corpus; covariance on DISJOINT held-out.
- L+1-mode-nodes have NO self-field, so their settled state comes ONLY through
  the transport (they cannot self-read the answer).
- Shuffle-T control destroys the transport structure while preserving its value
  distribution — isolates that the recovered transport, not the field, carries
  the covariance.
- Naive same-config baseline shows the transition is non-trivial (L ≠ L+1).
- Propagation on the substrate's OWN BP (protected `run_loopy_bp`, read-only,
  built-to; no new node/edge types minted).
- Honest whichever way; the linear→BP discretisation gap is reported.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.
