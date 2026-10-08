# Thoughtexperiment node-identity CoW integration v1 preregistration

## Question

Can the generated node-identity candidate path execute on isolated reusable
snapshot branches, preserve the primary rule/graph through candidate search,
and return the selected training-evidence receipt through the revision-checked
graph-delta API?

## Design

Reuse the locked v1.1 actor-recipient candidate generator and its eight
edge/attribute identity guards. Four worker processes freeze candidate order,
then score every candidate on the v1.1 training sequence under both native
full-copy and shared-graph-page snapshots. Each candidate runs on its own
branch from a fresh faulted primary. Inputs are added and closed sequentially,
with one shared `RecipientVerb` node per verb. The native graph-Term selector
receives opaque candidate IDs and training outcomes only. Held-out candidate
scores are captured in a separate stage after selection and cover all
candidates on both backends.

The selected candidate is replayed on a branch using the training sequence.
The branch changes a preexisting `ThoughtExperimentProposal` receipt to
`selected_from_training`; it does not patch the primary active rule. Capture
that receipt change with the native mutation journal and return it through
`apply_experiment_graph_delta`. Require exact receipt parity, primary
rule-store preservation, isolation before return, and atomic rejection of a
stale retry. This measures evidence handoff, not activation of a new production
rule; production-rule adoption is outside this gate.

## Gates

- Lock runner, analyzer, protocol, shared candidate generator, actor task
  source, native binary, and build manifest before capture.
- Require semantic parity between full-copy and shared-page branches for all
  candidate outcomes; require one actor+verb training winner per worker.
- Require selected repair and unmodified source-rule control to pass every
  held-out event, and score all alternatives.
- Verify unchanged parent graph/rules before return; returned receipt must
  match the selected branch exactly; stale retries must leave primary state
  unchanged.
- Report candidate generation, branch setup, input materialization, closure,
  selector, journal extraction, adoption, and held-out costs separately.

This remains one authored task family with supplied task semantics, fault,
examples, and oracle. It tests CoW integration and residual return for generated
candidate evidence, not autonomous diagnosis, rule activation, or general
self-improvement.
