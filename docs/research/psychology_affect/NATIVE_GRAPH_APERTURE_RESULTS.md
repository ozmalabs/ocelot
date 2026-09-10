# Native graph via aperture-covariance — substrate independence — RESULTS

**Block**: 321000. Pre-reg: `NATIVE_GRAPH_APERTURE_PREREG.md`.
Build: `domains/llm_native_graph.py`; measure:
`scripts/llm_native_graph_measure.py`. Substrate BP: protected
`domains/can_native_bp.py::run_loopy_bp` (read-only, built-to).

**HONEST NEGATIVE. The recovered structure is NOT aperture-covariant as
constructed. Pre-reg Claim 2 is FALSIFIED: the neuron-aperture Ising graph,
settled on the substrate's own belief propagation, does not re-express the
mode-aperture reading. What blocks 318–320 recovered is an IR at the mode
aperture, not a native graph — and substrate independence (Claim 3) is
therefore not established by this construction.**

## Claim 1 — substrate BP is buildable-to: HOLDS

A mode-refinement builds as a CAN Ising graph (Microtheory + Concept nodes with
`external_field`, `causal_influence` edges with `weight`) and settles under
`run_loopy_bp` (max-product) without touching any protected file. Smoke test:
two opposing-field concepts settle to +1/−1, converged. Infrastructure works.

## Claim 2 — aperture-covariance: FALSIFIED

Layer 12, 10 held-out queries; covariance = agreement between coarse mode state
`sign(Wc·x)` and read-back `sign(modes·settled)` on the dominant modes; chance =
0.50.

| coupling | top modes | covariance | shuffle-J control |
|---|---|---|---|
| mode-Gram | 4 | 0.82 | 0.82 |
| mode-Gram | 8 | 0.74 | 0.72 |
| coactivation | 4 | 0.47 | 0.47 |
| coactivation | 8 | 0.49 | 0.49 |

Neither coupling shows covariance above its shuffled-J control. Two distinct
failure mechanisms, both diagnosed:

**mode-Gram coupling is inert.** `|J_off| = 0.020` vs `|field| = 0.558` (28×
weaker). The SVD modes are ~orthogonal by construction, so their Gram over any
neuron subset is near-diagonal — the "edges" vanish. An orthogonal factorisation
is coordinate structure, not graph structure. The read-back tracks the field
alone (which is just the reconstructed activation), so it equals the shuffle. The
0.7–0.8 "covariance" here is the field re-expressing itself, NOT the graph doing
work.

**coactivation coupling collapses to consensus.** Real cofiring edges are dense
and positive (`|J_off| = 15.2`, 88% nonzero). But dense positive symmetric
coupling is a FERROMAGNET: the Ising settle drives all nodes to the same sign
(global consensus), which is topology-independent — a self-check found real-J
vs shuffled-J settles differ by 0 at strong coupling, and by only 0.10 at
balanced coupling. Consensus erases the per-neuron structure the modes encode,
so the read-back is at chance (0.47–0.49).

## Claim 3 — substrate independence: NOT ESTABLISHED

Because Claim 2 failed, the cognition was NOT reproduced by the substrate's own
message-passing. This construction does not demonstrate substrate independence.
Reported honestly: no positive claim is made.

## What the negative means (and why it is informative)

The mode→Ising-over-neurons refinement is a DIFFERENT object that merely shares
the neuron support — not the same object read at a finer aperture. The coarse
reading `sign(Wc·x)` is a LINEAR function of the query in the mode basis; the
fine reading is a DISCRETE Ising MAP settle governed by the coupling topology.
There is no reason these coincide, and they don't. **The incidence map between
the two apertures — the structure that would make them the same object — was
never recovered; it was assumed.** A mode is not just its neuron support, and a
coactivation count is not the coupling that would make the settle re-express the
mode. Assuming the refinement instead of recovering it is exactly what keeps the
object an IR at one aperture.

This is the precise sense in which blocks 318–320 stayed an IR: they recovered
one aperture (the mode/coefficient reading) and executed the transition as a map
WITHIN that aperture (matmul replay). The dual aperture and the incidence
between them — the thing that makes node and edge the same entity seen at two
apertures — is the missing piece, and this block shows that naively bolting a
substrate Ising graph onto the mode support does NOT supply it.

## Anti-faking / method

- Modes FIT on 60-prompt train; covariance on 10 DISJOINT held-out queries.
- Fine-aperture propagation runs on the substrate's OWN BP (protected
  `run_loopy_bp`) — "native" means it settles as the substrate's message-passing.
- Shuffled-J control isolates coupling structure from the field; here it shows
  the coupling carries nothing above chance (the load-bearing negative).
- The negative is reported as the result; no scaling/tuning was used to
  manufacture a positive.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched (read-only); no new node/edge types minted;
  models + venv under `/applications`, NOT committed.

## Honest bounds and named next levers (future blocks, not claimed here)

- One small model (0.6B), one layer, N=10 held-out — but the negative is
  mechanistic (orthogonal-mode inertness; ferromagnetic consensus collapse), not
  a small-N noise artifact, and the shuffle control confirms the coupling is
  doing no work.
- The result bounds THIS construction (mode support + cofiring/Gram coupling +
  loopy max-product). It does NOT prove the structure can never be lifted; it
  proves this refinement is not the incidence map.
- Named next levers: (a) recover the incidence map explicitly (the
  factor↔separator / transport structure) rather than assuming a mode = its
  neuron support; (b) SIGNED coupling from mode-disagreement (frustrated, not
  ferromagnetic) so the settle cannot collapse to consensus; (c) exact
  junction-tree inference instead of loopy BP. Each is a separate falsifiable
  block.
