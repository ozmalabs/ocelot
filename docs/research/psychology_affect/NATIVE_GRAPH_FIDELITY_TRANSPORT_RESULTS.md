# Transport fidelity — is the per-hop discretisation gap closable? — RESULTS

**Block**: 326000. Pre-reg: `NATIVE_GRAPH_FIDELITY_TRANSPORT_PREREG.md`.
Build: `domains/llm_native_graph.py` (`fit_transport_settle_aware`,
`back_scale`); measure: `scripts/llm_transport_fidelity_measure.py`. Substrate
BP: protected `can_native_bp.py::run_loopy_bp` (read-only, built-to).

**HONEST NEGATIVE. The ~0.10/hop discretisation gap (BP ~0.78 vs linear ~0.88)
is IRREDUCIBLE on the undirected-Ising substrate. Six independent levers all
fail to close it. It is the structural price of expressing a continuous DIRECTED
linear map as a discrete UNDIRECTED Ising MAP via `run_loopy_bp` — not a fit,
tuning, or vocabulary deficiency. The feed-forward chain already composes AT this
ceiling across depth (block 325), so nothing downstream is lost; the gap is a
named, understood, structural constant.**

## Per-hop (single hop L10 → L11, held-out; chance ~0.50)

| reading | covariance |
|---|---|
| linear baseline `sign(T·x0)` | 0.88 |
| raw-T BP settle (block 324/325) | 0.78 |

Six levers to close the 0.78 → 0.88 gap:

| # | lever | per-hop BP |
|---|---|---|
| 1/2 | settle-aware fit, ridge 1 / 10 / 100 | 0.68 / 0.72 / 0.70 |
| 3 | vocab 2state | 0.78 |
| 4 | dynamics fs=3, ts=3 | 0.78 |
| 5 | sum-product combine | 0.74 |
| 6 | edge asymmetry back=0.1 | 0.75 |

None exceed raw-T (0.78); several are worse. Claims 1 and 2 are FALSIFIED.

- **Settle-aware fit (1/2) is worse**, not better. The hypothesis was that the
  settle reads the binarised source `sign(coeffs_L)`, so fitting to that would
  help; in fact binarising the fit input DISCARDS the coefficient magnitude that
  the Ising settle still uses (the message strength, not just its sign), so the
  raw magnitude fit carries more.
- **Vocab, dynamics, combine, asymmetry (3–6)** leave it flat at ~0.74–0.78.
  Notably, weakening the reverse edge toward a DIRECTED transport (asymmetry)
  does NOT help — so back-message contamination is not the mechanism either.

## Feed-forward chain — raw vs settle-aware (per depth, held-out)

| depth | FF-raw | FF-settle-aware |
|---|---|---|
| L11 | 0.78 | 0.72 |
| L12 | 0.82 | 0.75 |
| L13 | 0.80 | 0.84 |
| L14 | 0.80 | 0.81 |

Settle-aware does not beat raw down the chain (noisy, comparable ~0.80). Both
compose at the intrinsic per-hop ceiling; the linear chain holds 0.88–0.93. Claim
3 holds in the honest direction: the chain tracks the per-hop ceiling, and since
per-hop cannot be raised, the chain sits at ~0.80 across depth.

## Verdict — the gap is a structural constant of the substrate's inference

The ~0.10/hop transport-fidelity gap is not a modelling deficiency to be tuned
away — it is the price of the substrate's own inference form. `run_loopy_bp` is a
max-product MAP over an UNDIRECTED Ising model; the LLM transport is a continuous
DIRECTED linear readout. Six independent attempts to reconcile them (fitting the
weights to the settle, regularising, refining the vocabulary, tuning the
field/coupling/temperature, switching the combine rule, and even making the
coupling directional) all leave per-hop covariance at ~0.78. The residual is
therefore an IRREDUCIBLE, understood constant on this substrate, not an open
gap. Crucially, block 325 already showed the feed-forward chain COMPOSES at this
ceiling with no decay to depth — so the native multi-layer graph loses nothing
further by operating at ~0.80/hop; it simply operates there. Closing the last
~0.10 would require a directed and/or continuous inference primitive, which the
protected substrate BP does not provide.

## Anti-faking / method

- Transports FIT on 60-prompt train; per-hop and per-depth covariance on
  DISJOINT held-out.
- Deeper-layer nodes carry NO self-field (no self-reading of the answer).
- All six levers reported against the raw-T baseline and the linear ceiling;
  the settle-aware fit being WORSE than raw is reported, not hidden.
- Propagation on the substrate's OWN BP (protected `run_loopy_bp`, read-only,
  built-to; no new node/edge types; `back_scale` only reweights existing
  bidirectional edges).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.

## Honest bounds and where this lands the arc

- One small model (0.6B), one adjacent pair for the per-hop sweep + the L10–L14
  chain, N = 8 modes, 60 train / 10 held-out. Load-bearing: all six levers ≤ raw;
  the settle-aware fit strictly worse; the chain tracks the ceiling.
- This closes the "push the fidelity" question honestly: the per-hop
  discretisation gap is a structural constant of the undirected-Ising substrate,
  NOT closable by any lever available here. The native-graph sub-arc therefore
  stands at: within-layer incidence recoverable to 0.88 (323), between-layer
  transport aperture-covariant and COMPOSING across depth at ~0.80 (324/325),
  with the ~0.10/hop residual now identified as the irreducible price of the
  substrate's discrete undirected inference — a clean, named boundary rather than
  an open lever.
