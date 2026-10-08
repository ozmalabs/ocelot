# Bigville authored-cut mutation follow-up — sensitivity inconclusive

**Date:** 2026-09-26. This is a locked Bigville-only follow-up to the authored
cut comparison. It is not a positive partitioned-execution result and does
not close the dialogue mutation cell.

## Capture and validation

Six fresh worker processes ran insertion, retraction, and reweight branches
with runtime tracing off/on. The independent analyzer passes all fingerprints,
branch, ownership, full-closure, residual, graph-reconstruction, cut-metric,
and trace-parity checks. Traced and untraced final graph digests match in all
five paired checkpoints (one insertion, two retraction, two reweight).

The post-operation full graph contains two directed cross-frame
`causal_influence` edges on insertion and reweight, and none after retraction.
The same pair of edge identities remains present through reweighting, with
weight changed from 0.2 to 0.35. Authored, balanced-ID, and dependency-min-fill
partitions report the same structural metrics at each checkpoint; induced
width upper bound is 2. Candidate execution refuses before any scoped call
because the active CAN rule declares `reads_any=true`.

## Semantic sensitivity result

All monolithic calls return fixed point with zero progress; the independent CAN
residual is zero before and after every tested mutation. The mutation does
change the graph topology/attributes, but the selected single edge does not
activate a rule or change closure state in this fixture. Runtime tracing
therefore records zero read events. This is explicitly classified as a
semantically insensitive mutation cell: it cannot validate omitted-boundary
sensitivity or partition parity. The endpoint was frozen by the follow-up
protocol and was not retuned after capture.

The measured Python cut reconstruction takes roughly 174–191 ms median wall
and CPU time per checkpoint for 500 task nodes; substrate construction and
closure are excluded. This number includes complete graph export, typed-edge
projection, access-row processing, three partition assignments, and naive
min-fill ordering. It is an implementation-cost diagnostic, not a substrate
scaling result. Closure calls take roughly 0.13–0.17 ms in this insensitive
case and are not a meaningful operating-cost comparison.

The dialogue mutation cell is recorded as unsupported because no
oracle-preserving authored boundary-link harness exists. The existing complete
dialogue graph has 40 incidences from task nodes to global state, so the
current frame definition is refused for scoped execution absent an explicit
global-state delivery contract.

## Consequence and next gate

This capture closes the mechanical question for Bigville graph mutation,
cut rebuilding, wildcard refusal, and trace-on/off parity. It does not satisfy
the parent protocol's omission-divergence requirement. A new sensitivity study
must be separately preregistered using a boundary mutation known to affect a
rule outcome, with matched full and omitted-notification controls and a
task-state oracle. The existing dynamic-link study establishes a sensitive
multi-link/evidence seam, but uses caller-supplied endpoint frames and does not
compare balanced-ID or dependency-derived partitions. The next confirmatory
work should adapt that known-sensitive seam without changing its frozen
topology after inspection, then retain dialogue as an explicit refusal until
its shared-state contract is represented.

## Artifacts

- Follow-up protocol: [`SUBSTRATE_AUTHORED_BIGVILLE_CUT_MUTATION_V1_PREREG_20260926.md`](SUBSTRATE_AUTHORED_BIGVILLE_CUT_MUTATION_V1_PREREG_20260926.md)
- Runner: [`substrate_authored_bigville_cut_mutation_v1.py`](../../../scripts/substrate_authored_bigville_cut_mutation_v1.py)
- Independent analyzer: [`analyze_substrate_authored_bigville_cut_mutation_v1.py`](../../../scripts/analyze_substrate_authored_bigville_cut_mutation_v1.py)
- Lock: [`authored_bigville_cut_mutation_v1_lock_20260926.json`](../../../evaluation/substrate_capability/authored_bigville_cut_mutation_v1_lock_20260926.json)
- Raw six-worker capture: [`substrate_authored_bigville_cut_mutation_v1_20260926.json`](../../../evaluation/reports/substrate_authored_bigville_cut_mutation_v1_20260926.json)
- Accepted independent analysis: [`substrate_authored_bigville_cut_mutation_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_authored_bigville_cut_mutation_v1_analysis_20260926.json)
- Preserved failed analyzer attempts: [pre-runner hash refresh](../../../evaluation/reports/substrate_authored_bigville_cut_mutation_v1_analysis_attempt_20260926.json), [lock shape correction](../../../evaluation/reports/substrate_authored_bigville_cut_mutation_v1_analysis_attempt_lock_shape_20260926.json)
