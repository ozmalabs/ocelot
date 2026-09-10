# Multi-hop transport chain — does the native graph compose? — RESULTS

**Block**: 325000. Pre-reg: `NATIVE_GRAPH_CHAIN_PREREG.md`.
Build: `domains/llm_native_graph.py` (`export_chain_structure`,
`build_chain_factor_graph`); measure: `scripts/llm_transport_chain_measure.py`.
Substrate BP: protected `can_native_bp.py::run_loopy_bp` (read-only, built-to).

**POSITIVE, with a precise mechanism. The native graph COMPOSES across depth
when run in the substrate's DIRECTED FEED-FORWARD mode — held-out deep-layer
covariance holds at ~0.80 across all four hops (= the single-hop result, no
degradation to depth). A JOINT undirected settle (one graph, one clamped end)
degrades to chance by ~4 hops; that is a property of the joint relaxation, not
of the transport, and the mechanism is understood.**

## Setup

Chain L10 → L11 → L12 → L13 → L14 (5 layers, 4 hops), per-hop transports fit on
60 train queries, per-depth mode-sign covariance on 10 DISJOINT held-out queries,
input clamped at L10, N = 8 modes; chance = 0.50.

| depth | linear | BP feed-forward | BP joint | joint shuffle |
|---|---|---|---|---|
| L10 | 1.00 | 1.00 | 0.93 | 0.97 |
| L11 | 0.88 | 0.78 | 0.65 | 0.45 |
| L12 | 0.89 | 0.82 | 0.59 | 0.44 |
| L13 | 0.91 | 0.80 | 0.61 | 0.24 |
| L14 | 0.93 | 0.80 | 0.51 | 0.51 |

## Claim 1 — linear composition holds: HOLDS

Composing the per-hop transports and propagating the L10 coefficients reproduces
the deep-layer mode signs at 0.88 → 0.93 across 1 → 4 hops — it does NOT decay;
it slightly IMPROVES with depth. Error does not compound in the linear
composition (adjacent-layer mode transitions are near-linear and well-
conditioned, and deeper layers are more "decided", giving cleaner signs).

## Claim 2/3 — the substrate carries it in FEED-FORWARD, not JOINT: HOLDS (with the distinction)

**Feed-forward (directed).** Settling one hop on the substrate, reading the
settled destination states, and re-clamping them as the next hop's input holds
at 0.78 → 0.82 → 0.80 → 0.80 across all four hops — matching the single-hop
block-324 result with NO degradation to depth. The native graph composes across
depth when the substrate respects the directionality of the computation.

**Joint (undirected).** One graph with all layers' mode-nodes and only L10
clamped, settled once, degrades: 0.65 → 0.59 → 0.61 → 0.51 (chance) by L14, and
by L14 it equals its own shuffle control. The joint settle does NOT carry the
composition to depth.

**Mechanism.** It is not the transport that fails — the same transports carry
the feed-forward chain to 0.80. It is the JOINT UNDIRECTED relaxation: with only
one clamped end, the far layers are under-constrained, and the per-hop
discretisation loss (the 0.95 → 0.80 gap of block 324) compounds multiplicatively
through a simultaneous relaxation of every layer. The LLM's computation is
DIRECTED (L → L+1), and the substrate reproduces it faithfully only when the
graph is run in that directed, feed-forward mode — settle-and-clamp per hop —
not as one big joint energy minimisation.

## Verdict

The native, multi-layer graph reading COMPOSES: the recovered per-hop transports,
run as directed feed-forward settle-and-clamp on the substrate's own BP,
propagate the mode configuration from L10 all the way to L14 at ~0.80 held-out —
the same fidelity as a single hop, with no decay to depth. This is genuinely
native multi-layer cognition on the CAN substrate: each layer's mode-config is
carried forward by the recovered transport as the substrate's own message-
passing. The honest caveat is that the substrate must be run in feed-forward
mode; a joint undirected relaxation of the whole chain under-constrains the deep
layers and washes the signal out — a property of the inference mode, not of the
recovered structure, and the mechanism is understood.

## Anti-faking / method

- Transports FIT on 60-prompt train; per-depth covariance on DISJOINT held-out.
- Deeper-layer nodes carry NO self-field — their state comes only through the
  transport (no self-reading).
- Shuffle-transport control on the joint chain (collapses to chance / below)
  confirms the recovered transport carries the covariance.
- All three readings (linear / joint / feed-forward) reported side by side; the
  joint degradation is reported, not hidden behind the feed-forward success.
- Propagation on the substrate's OWN BP (protected `run_loopy_bp`, read-only,
  built-to; no new node/edge types; bidirectional edges are the Ising form).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.

## Honest bounds and where this lands the arc

- One small model (0.6B), one 5-layer chain (L10–L14), N = 8 modes, 60 train /
  10 held-out. Load-bearing claims: linear holds across depth; feed-forward
  substrate holds at ~0.80 across depth; joint degrades to chance — and the
  directed-vs-joint distinction, not the exact fractions.
- The feed-forward ~0.80 inherits the single-hop discretisation gap (linear
  0.9x vs BP 0.80); a finer-vocab or MAP-fit transport (block 323's within-layer
  lever) would raise the per-hop fidelity and hence the whole chain.
- This completes the native-graph sub-arc: within-layer incidence
  (323: 0.88), single-hop transport (324: 0.80), and now MULTI-HOP composition
  (325: ~0.80 across depth, feed-forward). A native, multi-layer graph reading
  of the recovered LLM exists, composes across depth, and carries its cognition
  on the CAN substrate as message-passing — demonstrated in part, with the
  residual a named discretisation quantity and the inference-mode caveat stated.
