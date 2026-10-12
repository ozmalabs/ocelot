# Multi-part codebook GenInfer scaling v1 preregistration (2026-10-03)

## Question

Does the production full-seed GenInfer path restrict candidate search to a
frame, or does each query scan all eligible `ShapeSignature` parts in the
shared codebook? How does one shared closure cost change as frame-tagged parts
and observations grow together?

## Task development and scope

The implementation's `eval_gen_infer` loads all parts of the requested
codebook type, then iterates over each part with two `coord:*` dimensions;
there is no frame identifier in this search. A one-run exploratory full-seed
pilot with K=1,2,4,8 frame-tagged parts and observations acquired all target
generators. Closure times were approximately 11, 37, 86, and 289 ms. This
pilot selected the repeated map family and sample sizes and is not scored.
Frame identifiers below are caller-supplied audit labels; this code path does
not use them to scope the search. The evaluation therefore measures shared
codebook exposure and a present scoping gap, not the performance of an
implemented hierarchical frame partitioner.

## Locked design

Fifteen fresh-process workers cross K in `{1,2,4,8,16}` with three repeats.
Each worker boots one production core, adds K distinct four-relation base
signatures and K corresponding observations, tags each pair with a separate
`frame_id`, then runs one full native closure. Four preregistered linear
matrices cycle across frames; all have data-derived coefficient bound B=3.
Predicates are unique to each frame to make the correct base identifiable.

Before the production closure, a pure direct-Term diagnostic asks GenInfer
for its `checked` field on every observation against the full shared codebook.
It must leave graph node and edge counts unchanged. With K eligible parts,
one query should check `K*((2B+1)^4-1) = K*2,400` candidates; the sum over K
queries is `K²*2,400`. This is a direct diagnostic of full candidate volume,
not a claim that production closure invokes GenInfer K times: generator mint
and re-decode may cause later observations to reuse earlier results. The
production closure is separately timed and scored for exact recognition,
generator acquisition, CPU, wall time, peak-RSS delta, and graph size.

## Gates

1. Exactly 15 unique workers run in distinct processes, with three repeats at
   every K and stable locked sources/native engine.
2. The direct-Term checked count for each query is exactly K×2,400 and the
   aggregate is K²×2,400; graph node/edge counts remain unchanged during the
   diagnostic.
3. Every observation settles as `recognized_transformed`, uses a receipt
   naming its own frame's base, and matches its preregistered matrix exactly.
4. Every intended linear generator exists after closure, and all timing,
   memory, work, and graph-size readings are present.

The measured timing relationship is descriptive; no post-hoc scaling-law
threshold is imposed. Results cannot be presented as frame-local or
hierarchical inference. A later frame-scoped implementation must receive its
own preregistered paired comparison against this shared-codebook baseline.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_multipart_codebook_scaling_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_geninfer_multipart_codebook_scaling_v1.py`
- Source lock: `evaluation/substrate_capability/substrate_geninfer_multipart_codebook_scaling_v1_lock_20261003.json`
- Raw capture: `evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_20261003.json`
- Analysis: `evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_analysis_20261003.json`
