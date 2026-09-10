# Multi-hop transport chain — does the native graph compose? — PRE-REG

**Block**: 325000. Build target: `domains/llm_native_graph.py`
(`export_chain_structure`, `build_chain_factor_graph`); measure:
`scripts/llm_transport_chain_measure.py`. Substrate BP is the PROTECTED
`can_native_bp.py` (`run_loopy_bp`), read-only — built TO.

## Motivation

Block 324 showed one hop (L → L+1) of the between-layer transport is
aperture-covariant on the substrate's own BP (~0.80 held-out). A single hop
working is necessary but not sufficient for a native MULTI-LAYER graph: the real
question is whether the transport COMPOSES across depth. Chain
L → L+1 → … → L+H as one graph and ask whether the DEEP-layer mode configuration
is reproduced from the SHALLOW input, or whether error compounds and washes out.

## Claims (falsifiable)

**Claim 1 — linear composition holds.** Composing the per-hop transport maps
(fit on train) and propagating the shallow coefficients reproduces the deep
mode signs on held-out, without degrading toward chance as the chain lengthens.
Prediction: composed covariance ≈ single-hop across H = 1..4. FALSIFIED IF it
decays toward chance with depth.

**Claim 2 — the substrate carries the composition.** The chain, run on the
substrate's own BP, reproduces the deep mode config above a shuffle-transport
control. Prediction: substrate covariance ≫ shuffle across depth. FALSIFIED IF
substrate ≈ shuffle at depth (the substrate cannot carry the composed transport).

**Claim 3 — directed vs joint.** How the substrate is RUN matters. A directed
FEED-FORWARD chaining (settle a hop, clamp the result, settle the next) is
expected to hold across depth; a JOINT undirected settle (one graph, one clamped
end, relax all at once) may degrade because the far layers are under-constrained.
Reported honestly — this distinguishes "the transport fails" from "the joint
relaxation fails".

## Method

- `export_chain_structure`: export per-query mode coefficients across a chain of
  layers (e.g. L10..L14) for train + held-out.
- `fit_transport` per hop (train). Three readings of the deep-layer covariance:
  - LINEAR: compose the T maps, propagate coefficients, sign covariance.
  - JOINT BP: `build_chain_factor_graph` — all layers' mode-nodes, first layer
    clamped (external_field = coeffs_L), deeper layers self-field 0, adjacent
    transport edges (bidirectional); settle once; read every layer.
  - FEED-FORWARD BP: settle one hop, read the settled destination states,
    re-clamp as the next hop's input, repeat.
- Shuffle-transport control on the joint chain. Per-depth held-out covariance.

## Anti-faking

- Transports FIT on the 60-prompt train corpus; covariance on DISJOINT held-out.
- Deeper-layer nodes have NO self-field — their state comes only through the
  transport (they cannot self-read the answer).
- Shuffle-transport control isolates the recovered transport from the field.
- The three readings (linear / joint / feed-forward) are reported side by side
  so a degradation in one is not hidden by another.
- Honest whichever way — a depth-dependent failure of the joint settle is a
  real, reportable finding, and the mechanism is stated.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.
