# Vision settle root-scoped mean probe preregistration

Date: 2026-09-25. This is a benchmark-only semantic probe. It does not change `seeds/vision_settle.json` or engine code.

## Question
Can the existing rule DSL express the seed comment's per-sheet competition by replacing the `NodesOfType(SUnit)` source for the global activation mean with `Neighbours(r, has_sunit)`, and does this remove cross-World coupling while preserving the within-sheet predicted update on a minimal fixture?

## Arms
For each of two matched World-rooted SUnit pairs, load only `st_settle` from the authored seed. Global arm keeps the authored rule unchanged. Scoped arm deep-copies that rule and replaces both `NodesOfType(SUnit)` sources inside the global mean numerator/denominator with `Neighbours(r, has_sunit)`. The World owns both units through `has_sunit`; local pair adjacency is unchanged. A starts `[1,1]`, B starts `[0,0]` or `[1,1]`; afferents are zero; scratch buffers start at -1 to force a write. Only the scoped variant is renamed. The existing singleton `SettleParams` is set to settle=1.

## Predictions
The global arm reproduces the v1.2 outputs: A is `[0.5,0.5]` when B is zero and `[0,0]` when B is one. The root-scoped arm yields A `[0.5,0.5]` in both cases. Both arms must make native progress, remain below the application cap, and match the equations. This establishes DSL expressibility and this fixture's semantics only; it does not establish full-sheet quality, convergence, or cost.

## Provenance and reporting
Record seed, runner, protocol, engine source and native extension hashes, engine provenance, progress counts, and outputs. Preserve raw output. No timing claim is made. Any deviation or failure is reported without changing the prediction.
