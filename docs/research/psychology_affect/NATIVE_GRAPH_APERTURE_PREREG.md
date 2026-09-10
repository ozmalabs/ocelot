# Native graph via aperture-covariance — substrate independence — PRE-REG

**Block**: 321000. Build target: `domains/llm_native_graph.py`; measure:
`scripts/llm_native_graph_measure.py`. Substrate BP is the PROTECTED
`domains/can_native_bp.py` (`run_loopy_bp`), read-only — built TO, never
modified.

## Motivation

Blocks 318–320 recovered the FFN's structure into an intermediate
representation: SVD modes + a coefficient map + per-position selection, executed
by the same numpy substrate doing the same matmul shapes. That is the model's
computation in the model's coordinates, factored cheaply — an IR, NOT a native
graph.

The user's framing of what a native graph is: *an edge is literally a node at a
different APERTURE*. There is one aperture-invariant object; "node" vs "edge" is
a movable readout, not a property of the thing. The recovered structure is a
native graph IFF it is APERTURE-COVARIANT — the same object, read at the mode
aperture and refined to the neuron-coactivation aperture and propagated on the
SUBSTRATE'S OWN belief propagation (an Ising/Boltzmann graphical model, not
numpy matmul replay), reproduces the same outcome. If it does, the cognition was
never in the model's coordinates — it lived in the aperture-invariant object,
and the weights were one aperture's encoding. **That is substrate independence,
demonstrated rather than asserted.**

## Claims (falsifiable)

**Claim 1 — the substrate BP interface is buildable-to.** A mode-refinement can
be expressed as a CAN Ising graph (Microtheory + Concept nodes with
`external_field`, `causal_influence` edges with `weight`) and settled by
`run_loopy_bp` without touching protected files. (Infrastructure claim.)

**Claim 2 — aperture-covariance (the native-graph claim).** For held-out
queries at a layer: the coarse mode-aperture reading `sign(Wc·x)` per mode, and
the read-back from the settled neuron-aperture Ising graph
`sign(modes[:,idx] · settled)`, AGREE well above chance and above a shuffled-J
control. Prediction: covariance → ~1.0, > shuffle. **FALSIFIED IF covariance ≈
chance (0.5) or ≈ shuffle** — then the fine graph does not re-express the coarse
reading and the structure is an IR at one aperture, not a native graph.

**Claim 3 — substrate independence follows from Claim 2.** If Claim 2 holds, the
cognition is reproduced by the substrate's own message-passing, not by the
model's coordinates — substrate independence. If Claim 2 fails, this claim is
not established (honest).

## Method

- EXPORT (model venv): fit the mode router (block 318/320), export per-layer
  `{modes, mean, Wc, held-out inputs, coefficients, top-loading neuron_idx,
  coactivation coupling coact_J}` to npz.
- Two aperture readings of the SAME object: coarse `sign(Wc·x)`; refine to the
  top-loading neurons with field = the modes' predicted drive and coupling J
  either (a) the modes' Gram over neurons or (b) the neurons' real cofiring
  (coactivation graph); settle on `run_loopy_bp`; read back `sign(modes·settled)`.
- Measure covariance (agreement on the dominant modes) across held-out, vs a
  shuffled-J control that destroys the coupling topology while preserving its
  value distribution.

## Anti-faking

- Modes FIT on the 60-prompt train corpus; covariance measured on 10 DISJOINT
  held-out queries. No prompt→output memory.
- The fine-aperture propagation runs on the substrate's OWN BP (protected
  `run_loopy_bp`), so "native" means it settles as the substrate's
  message-passing — not replayed matmuls.
- A shuffled-J control isolates whether the COUPLING structure (not the field
  alone) carries any covariance.
- The pre-reg explicitly admits the NEGATIVE outcome (Claim 2 falsified) as a
  real, reportable result — the recovered structure being an IR, not a native
  graph, is a finding, not a failure to report.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched (read-only, built-to); no new node/edge
  types minted; models + venv under `/applications`, NOT committed.
