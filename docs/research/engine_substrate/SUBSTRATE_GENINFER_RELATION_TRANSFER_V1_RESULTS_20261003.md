# GenInfer relation transfer v1 results (2026-10-03)

## Question

Can the full-seed GenInfer path acquire a 2-D integer relation from a training
signature, retain it, and apply that acquired generator to a distinct held-out
signature without access to the held-out answer during training?

The preregistered capture contains 30 fresh-core cases: three repeats for each
of three maps with GenInfer enabled and disabled, three identity controls, and
nine corrupted-heldout controls. The held-out signature was inserted after the
training closure. Runner, analyzer, inputs, code, seed manifests, and native
engine were source locked. See [protocol](SUBSTRATE_GENINFER_RELATION_TRANSFER_V1_PREREG_20261003.md),
[runner](../../../evaluation/substrate_capability/substrate_geninfer_relation_transfer_v1.py),
[analysis](../../../evaluation/reports/substrate_geninfer_relation_transfer_v1_analysis_20261003.json),
and [raw capture](../../../evaluation/reports/substrate_geninfer_relation_transfer_v1_20261003.json).

## Result

The strict general transfer gate **fails**. Only the `[2,1,1,1]` map was
acquired during the training stage and then used on its held-out signature in
all three repeats (3/3). Across all enabled clean cases, this gives 3/9
train-acquire-and-transfer successes. The `[1,0,1,1]` map was absent after
training and appeared only after the held-out input was introduced; its exact
held-out match is therefore not evidence of transfer. The `[1,1,0,1]` map
used the pre-existing `cycle4` route in enabled and disabled conditions, so
its exact answers likewise do not demonstrate learning. The three identity
controls added no generator and routed through a pre-existing reflection.

All three corrupted-heldout cases for the genuinely acquired `[2,1,1,1]`
generator named that generator, but none matched the corrupted target exactly.
Across the nine corrupted controls, exact matches were 0/9. Disabled controls
acquired no target generators. Median training closure was 0.61 ms and median
held-out closure 0.86 ms in this small fixture; these are closure times, not a
general runtime estimate. The full-seed route therefore demonstrates bounded
relation acquisition and genuine held-out reuse for one map, while existing
routes and late acquisition confound the other maps. It does not establish
open-ended relation learning or general self-improvement.

## Interpretation and next measurement

The analyzer's failed gates are retained; no criteria were relaxed after
capture. The next study should select a preregistered family whose members are
not explained by existing seed transformations, verify each candidate is
absent before training, and separately require (a) acquisition before held-out
insertion, (b) held-out route attribution to that exact acquired generator,
and (c) disabled, identity, and corrupted controls. Candidate selection and
route aliases must be audited before locking the next capture. The present
result is a bounded positive for one transform and a useful negative result
for the stronger three-family claim.
