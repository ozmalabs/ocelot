# Native-graph levers — signed coupling, incidence map, exact inference — RESULTS

**Block**: 322000. Pre-reg: `NATIVE_GRAPH_LEVERS_PREREG.md`.
Build: `domains/llm_native_graph.py` (`refine_to_neurons_signed`,
`build_mode_neuron_factor_graph`, `read_mode_nodes`); measure:
`scripts/llm_native_graph_levers_measure.py`. Substrate BP / junction-tree:
protected `can_native_bp.py` / `can_junction_tree.py` (read-only, built-to).

**HONEST PARTIAL POSITIVE. Block 321's aperture negative is substantially
recovered: the three named levers move aperture-covariance from chance to well
above its shuffle control, and localise exactly what does the work. The
recovered structure is PARTIALLY aperture-covariant — the explicit incidence map
is the axis that moves it, and it moves it a lot.**

## The progression (layer 12, held-out, aperture-covariance vs shuffle; chance = 0.50)

| stage | covariance | shuffle control | note |
|---|---|---|---|
| block 321 — positive coactivation, flat projection | 0.47–0.48 | ≈ same | chance; ferromagnet consensus collapse |
| lever (a) — signed / frustrated coupling | 0.67–0.69 | 0.56–0.58 | consensus 1.0 → ~0.76–0.80 |
| lever (b) — explicit incidence map, incidence-only | 0.70–0.88 | 0.54–0.62 | mode as first-class node |
| lever (c) — exact inference, same structure | = loopy | — | structural ceiling, not inference |

(Ranges span the N=24-neuron/8-mode and N=8-neuron/4-mode settings; the smaller,
more-dominant-mode graph reads cleaner — 0.88 at N=8/4 modes.)

## Claim A — signed coupling breaks the consensus collapse: HOLDS

`refine_to_neurons_signed` sets the edge MAGNITUDE to real cofiring but the edge
SIGN to whether two neurons load the SAME way on the query's dominant modes.
Aperture-covariance rises to 0.67–0.69, above its shuffled-J control (0.56–0.58),
and the settle's consensus fraction drops from ~1.0 (block 321's ferromagnet) to
~0.76–0.80 — the frustration prevents the all-same-sign collapse. Coupling sign
was a real part of the problem; fixing it helped but did not reach full
covariance, pointing (as the pipeline predicted) at the incidence map.

## Claim B — the explicit incidence map lifts covariance further: HOLDS

`build_mode_neuron_factor_graph` makes the mode a FIRST-CLASS node joined to its
neuron-variables by the loading `modes[m,i]`; `read_mode_nodes` reads the
mode-node's OWN settled state — no lossy projection. With the mode-node's
self-field set to 0, the reading comes ONLY through the incidence, so this is
the true test that the graph structure carries the mode. Incidence-only
covariance is 0.70–0.88, well above shuffle-incidence (0.54–0.62). Making the
incidence explicit — a mode is a node joined to its neurons by the loadings, not
a flat neuron-support — is the right structure and is the axis that moves
covariance most.

METHOD NOTE (stated so the result is not overclaimed): if the mode-node instead
carries its own coefficient as its field, covariance AND shuffle both read 1.0 —
the node self-reads and the graph does nothing. That regime is excluded; the
load-bearing numbers are all incidence-only (self-field 0).

## Claim C — the ceiling is structural, not the inference: HOLDS

On the bipartite incidence structure (small enough for exact inference: 8
neurons + 4 modes, 3^12 states), exact brute-force MAP gives IDENTICAL
covariance to loopy-BP (0.75 = 0.75 at N=8; 0.88 = 0.88 on the 6-query subset).
Loopy BP was already finding the right MAP — the inference algorithm is NOT the
limiter. The residual gap to full covariance (1.0) is therefore the incidence
map's own FIDELITY: how much of the linear `sign(Wc·x)` reading the
loading-weighted bipartite graph can encode as a discrete Ising MAP. That is the
next axis, and it cannot be closed by a better solver.

## Verdict — partial positive

Block 321's negative was not a wall; it was a mis-specified refinement. Fixing
the two diagnosed causes (consensus collapse via signed coupling; assumed-support
via an explicit incidence map) moves aperture-covariance from chance (0.47) to
0.70–0.88, consistently above shuffle, and exact inference confirms this is the
structure's own ceiling, not the solver's. So the recovered structure IS
partially aperture-covariant — a substantial fraction of the mode reading
survives being lifted onto the substrate's own message-passing, read off a
first-class mode-node driven only through the recovered incidence. It is not yet
FULL covariance (~1.0), so substrate independence is demonstrated in PART, not in
full: the cognition partially survives the lift, and the remaining gap is a
concrete, named quantity (incidence-map fidelity), not a mystery.

## Anti-faking / method

- Modes fit on 60-prompt train (offline); covariance on DISJOINT held-out.
- Fine-aperture propagation and exact inference run on the substrate's OWN
  machinery (protected `run_loopy_bp` / `brute_force_map`), read-only, built-to,
  no new node/edge types minted.
- Every lever reported against its shuffle control; the trivial self-reading
  regime (mode self-field on) is excluded and stated.
- Exact == loopy is reported as the finding that isolates the ceiling as
  structural.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.

## Honest bounds and named next lever

- One small model (0.6B), one layer, small held-out (6–10) — the load-bearing
  claims are the monotone progression (chance → signed → incidence), the
  above-shuffle margin at each lever, and exact == loopy; not the exact
  fractions, which move with N (0.70 at N=24, 0.88 at N=8).
- The result is a PARTIAL positive: covariance is well above chance/shuffle but
  below 1.0. Substrate independence is shown in part, not in full.
- Named next lever (future block): raise the incidence-map FIDELITY — the
  bipartite loading graph currently encodes a linear `sign(Wc·x)` reading only
  approximately as a discrete Ising MAP. Candidates: multi-state (finer vocab)
  mode-nodes; incidence weights fit to maximise MAP-agreement rather than taken
  raw from the loadings; the between-layer transport incidence (this block used
  a single layer's within-aperture incidence only).
