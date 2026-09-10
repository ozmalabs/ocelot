# Transport fidelity — is the per-hop discretisation gap closable? — PRE-REG

**Block**: 326000. Build target: `domains/llm_native_graph.py`
(`fit_transport_settle_aware`, `back_scale` on `build_chain_factor_graph`);
measure: `scripts/llm_transport_fidelity_measure.py`. Substrate BP is the
PROTECTED `can_native_bp.py` (`run_loopy_bp`), read-only — built TO.

## Motivation

Block 324/325 established that the between-layer transport is aperture-covariant
on the substrate's own BP at ~0.80 held-out per hop, and the feed-forward chain
composes there across depth. But the LINEAR transport reads ~0.90 per hop — a
~0.10/hop DISCRETISATION gap between the continuous directed linear map and its
discrete undirected Ising MAP settle. This block asks whether that gap is
CLOSABLE by the block-323 fidelity lever (fit the incidence to the settle) and
five further levers.

## Claims (falsifiable)

**Claim 1 — settle-aware fitting closes the gap.** Fitting the transport to what
the settle actually reads (regress the BINARISED source `sign(coeffs_L)` →
`coeffs_{L+1}`, well regularised) lifts per-hop BP covariance above the raw-T
~0.80 toward the linear ~0.90. FALSIFIED IF settle-aware ≤ raw.

**Claim 2 — some lever closes it.** If Claim 1 fails, one of: regularisation,
vocab (2 vs 3 state), field/transport/temperature dynamics, max vs sum-product
combine, or edge asymmetry (weaken the reverse Ising edge toward a directed
transport) lifts per-hop BP toward the linear. FALSIFIED IF none exceed raw.

**Claim 3 — chain follows per-hop.** Whatever the best per-hop transport, the
feed-forward chain covariance tracks it across depth (raising per-hop fidelity
raises the whole chain; if per-hop cannot be raised, the chain sits at the
ceiling). Reported honestly.

## Method

- `fit_transport_settle_aware`: ridge regress the binarised source
  `sign(coeffs_L)` → `coeffs_{L+1}` on TRAIN (fit to the discrete input the
  settle reads).
- Per-hop BP covariance on DISJOINT held-out for: raw-T; settle-aware (ridge
  sweep); vocab; dynamics; combine; `back_scale` edge asymmetry. Linear baseline
  and shuffle for reference.
- Feed-forward chain (block 325) with raw vs settle-aware transports, per depth.

## Anti-faking

- Transports FIT on the 60-prompt train corpus; covariance on DISJOINT held-out.
- Deeper-layer nodes carry NO self-field (no self-reading).
- Every lever reported against the raw-T baseline and the linear ceiling; a
  negative on all six is a real, reportable structural finding.
- Propagation on the substrate's OWN BP (protected `run_loopy_bp`, read-only,
  built-to; no new node/edge types minted).
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals untouched; models + venv under `/applications`, NOT
  committed.
