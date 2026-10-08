# Code-write contract coverage v1 — preregistration

## Question

Can the opt-in contract gate reject a wrong construction when the supplied examples are individually valid but fail to distinguish the candidate from the requested behavior?

## Arms

Four fresh full-seed workers, two repetitions per arm, randomized:

- **Aliasing narrow contract:** teach `def identity(value): return value` for a square request using only `0→0` and `1→1`. These labels are correct for both identity and square.
- **Discriminating contract:** same source/request, but add `2→4`, which distinguishes identity from square.

After teaching, attempt normal code composition/rendering and evaluate any emitted candidate on held-out inputs `-3, -2, 2, 3`. The substrate worker receives only contract rows; held-out expected outputs remain in the independent analyzer. Record exact source/native fingerprints, codebook deltas, acquisition result, selected shape, native Term outputs, Python outputs, and costs.

## Gates and scope

The narrow contract is expected to pass local validation and be admitted, but held-out square accuracy is the decisive capability outcome. The discriminating contract should refuse on the first differing observation and produce no new code-write ShapeSignature. Oracle expectations are `x*x`, independently computed by the analyzer. This panel measures coverage sensitivity on one deliberately aliased integer task; it does not estimate naturally occurring weak-contract prevalence or establish general probe selection. Keep all worker failures and report them.
