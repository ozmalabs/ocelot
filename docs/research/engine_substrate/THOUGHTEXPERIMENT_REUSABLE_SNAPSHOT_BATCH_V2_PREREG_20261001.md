# Thoughtexperiment reusable snapshot batch v2 preregistration

Date: 2026-10-01

## Question

Does the reusable immutable snapshot lifecycle reduce total cost for the real six-candidate Thoughtexperiment harness at graph scales where direct shared-page copying has shown gains? How much of each branch result is represented by changed node/edge residuals, and what cost remains in prediction and residual readout?

## Frozen workload and controls

- Use the existing fixed-revision six-candidate benchmark and its deterministic authored fixture at +10,000 and +50,000 unrelated nodes.
- Compare `native_full_copy_scoped`, `native_shared_graph_pages_scoped`, and `native_reusable_snapshot`. The reusable snapshot is captured after one baseline prediction, revision-checked, and forked for each candidate. Direct shared pages create each scoped candidate branch independently. Eager full-copy is the control.
- For every backend and size, compare one-baseline/six-candidate batching with standalone evaluation that recomputes the baseline per candidate. Candidate set, candidate order, focus observations, rule semantics, residual readout, and trace suppression are held by the existing harness.
- Run one warmup and five measured randomized blocks per size/backend, with a fixed random seed. Each randomized block executes all six backend × evaluation-mode arms. This is a single-process paired benchmark; unlike the previous fresh-process scale panels, allocator and thermal history are shared across blocks. Preserve block order in the raw capture.
- Require exact candidate output, conclusions, derived-only residuals, nested forward-look residuals, convergence, and primary graph/rule revision parity. Cross-backend batch rows must match exactly.
- Capture all existing phase timings and branch residuals. Derive per-candidate counts of changed nodes and edges from the exact `conclusions` and `derived_only` journal readouts. These counts describe emitted semantic changes; they are not an instrumented count of all mutation attempts or touched memory pages.

## Gates and limits

Require all six candidates and every paired arm in both sizes, exact cross-backend parity, positive and negative controls, unchanged primary revision, and five measured blocks after the warmup. Report medians and paired comparisons; no speed threshold is imposed. The fixture is one authored correction family on one host. Cost attribution is descriptive, not a new asymptotic claim. The harness exercises sequential candidate branches; it does not measure concurrent serving, cancellations, branch reclamation, or vLLM KV-block integration.
