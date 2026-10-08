# Adequacy-gated adoption boundary v1 — results

Date: 2026-10-02

## Result

The source-locked three-worker panel passes all **8/8** independent checks. The rejected signed label adjudicates as `rejected`, does not enter `code_write_growth._teach_shape`, and leaves the code-write shape inventory and epoch unchanged. The accepted label is independently replayed and authenticated, the adoption returns success, and the codebook contains one new shape at epoch 1.

The full graph snapshot taken exactly around `_teach_shape` shows the same semantic delta in every worker:

- one new `ShapeSignature` with kind `code_write_construction`;
- one new pending `ShapeObservation`;
- one existing Agent record updated with `write_codebook_epoch = 1` (and the expected default `meta_codebook_epoch = 0`); and
- no removed nodes or edges, no other changed nodes, and no added edges.

The median measured `_teach_shape` transaction was **0.437 ms** across three workers. This boundary includes `teach()` and the codebook epoch update. It excludes provider evidence creation, parsing and Term construction, conversation bootstrap and the rest of `WorldAdapter.converse`; it is not a full-route latency estimate.

## Relation to the cold live-route result

The [v1.2 full-conversation panel](SUBSTRATE_ADEQUACY_LIVE_ROUTE_COST_V1_2_RESULTS_20261002.md) found hundreds of nodes added between the beginning and end of the first `converse` call. Source inspection locates lazy manifest installation in `_ensure_comprehension_seeds`, which is invoked when comprehension succeeds, as well as normal per-turn graph writes. Those cold-route mutations are outside `_teach_shape`; they explain why a call-level graph diff cannot attribute state changes to code-shape adoption.

The focused boundary result narrows the uncertainty: the tested adoption function itself has a small, reproducible graph delta, while cold initialization remains a distinct cost and mutation surface. No claim is made about every caller, every graph mutation route, or arbitrary task adoption.

## Limits and next gate

One host, one authored square task, one deterministic test provider, and three fresh workers. Provider authentication does not establish truth. Expand the boundary audit to independently authored task families and other teaching callers; separately compare cold initialization with a warmed full `converse` route and capture per-turn graph changes outside adoption. Retain the v1.2 failure as evidence about the cold path.

The preregistered [v2 cross-family panel](SUBSTRATE_ADEQUACY_ADOPTION_BOUNDARY_V2_RESULTS_20261002.md) now extends this invariant to parity and clamp as well as square. Its 8/8 checks pass across nine fresh workers, with the same exact adoption delta and 303/303 native held-outs. This remains three authored families, not broad induction or all-caller evidence.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_ADOPTION_BOUNDARY_V1_PREREG_20261002.md)
- [Adoption implementation](../../../domains/code_write_growth.py) and [authenticated adapter](../../../domains/adequacy_provider_auth.py)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_adoption_boundary_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_adoption_boundary_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_adoption_boundary_v1_analysis_20261002.json)
