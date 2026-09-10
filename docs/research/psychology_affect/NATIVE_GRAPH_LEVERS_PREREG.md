# Native-graph levers — signed coupling, incidence map, exact inference — PRE-REG

**Block**: 322000. Build target: `domains/llm_native_graph.py`
(`refine_to_neurons_signed`, `build_mode_neuron_factor_graph`,
`read_mode_nodes`); measure: `scripts/llm_native_graph_levers_measure.py`.
Substrate BP / junction-tree are PROTECTED (`can_native_bp.py`,
`can_junction_tree.py`), read-only — built TO, never modified.

## Motivation

Block 321 tested whether the recovered LLM structure is a NATIVE GRAPH by the
aperture-covariance criterion (the same object read at the mode aperture,
refined to the neuron aperture and propagated on the substrate's own BP,
reproduces the mode reading). It was a NEGATIVE: covariance ≈ chance (0.47),
with two diagnosed causes — the orthogonal-mode Gram is edgeless, and the
positive coactivation coupling is a ferromagnet whose Ising settle collapses to
consensus. It named three levers. This block runs them IN ORDER, each result
informing the next.

## Claims (falsifiable)

**Claim A — signed/frustrated coupling breaks the consensus collapse.** Coupling
whose magnitude is real cofiring but whose SIGN is the neurons' agreement on the
dominant modes prevents the ferromagnetic consensus, and lifts aperture-
covariance above chance and above a shuffled-J control. Prediction: covariance >
0.5 and > shuffle; consensus fraction < 1.0. FALSIFIED IF covariance stays ≈
chance/shuffle (coupling sign is not the issue → the incidence map is).

**Claim B — an explicit incidence map lifts covariance further.** Making the
mode a FIRST-CLASS node joined to its neuron-variables by the loading
`modes[m,i]` (a bipartite factor graph), and reading the mode-node's OWN settled
state (no projection) with the mode-node's self-field OFF, re-expresses the
coarse mode reading above shuffle. Prediction: incidence-only covariance >
shuffle-incidence, and ≥ lever A. FALSIFIED IF incidence-only ≈ shuffle (the
loadings carry no more than a scrambled bipartite graph).

**Claim C — is the ceiling the inference or the structure?** Exact inference
(brute-force MAP / junction-tree) on the best structure either lifts covariance
above loopy-BP (loopy was the limiter) or matches it (the ceiling is
structural). Prediction reported honestly either way.

**Framing claim — partial vs full.** If any lever reaches covariance ≈ 1.0 above
shuffle, the structure is aperture-covariant (native graph / substrate
independence for that construction). If the levers move covariance up but plateau
below 1.0, that is an honest PARTIAL positive: the recovered structure is
partially aperture-covariant, and the residual gap names the next axis.

## Method

- Modes fit on the 60-prompt train corpus (offline export); covariance measured
  on DISJOINT held-out queries. Coarse reading = `sign(Wc·x)` per mode.
- Lever A: `refine_to_neurons_signed` — J = sign(mode-agreement) · |cofiring|.
- Lever B: `build_mode_neuron_factor_graph` — mode nodes + neuron nodes,
  incidence edges weight `modes[m,i]`; `read_mode_nodes` reads mode-node state.
  The mode-node self-field is set to 0 so the reading comes ONLY through the
  incidence (a mode-node carrying its own coefficient as field self-reads
  trivially — covariance and shuffle both 1.0 — so that regime is excluded).
- Lever C: exact `brute_force_map` (small graph) vs `run_loopy_bp` on the
  bipartite structure.
- Shuffle controls: shuffle-J (A), shuffle-incidence (B/C) — destroy the
  recovered structure while preserving its value distribution.

## Anti-faking

- Fit on train, covariance on DISJOINT held-out; no prompt→output memory.
- Fine-aperture propagation runs on the substrate's OWN BP / exact inference
  (protected, read-only, built-to; no new node/edge types minted).
- Every lever reported against its shuffle control; the trivial
  self-reading regime (mode self-field on) is explicitly excluded and stated.
- Partial positive reported as partial — no scaling/tuning to claim full
  covariance.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.
