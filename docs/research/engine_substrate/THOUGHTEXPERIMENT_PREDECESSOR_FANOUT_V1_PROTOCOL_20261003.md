# Protocol: predecessor-dependent candidate fanout in thought experiments

Date: 2026-10-03

Status: protocol prepared before the source-locked capture.

## Question

Can candidate branches use the substrate's correction-grounding result to
select one action-head hypothesis from a fanout, while preserving exact
monolithic state, primary isolation, and residual-return semantics as the
number/topology of discourse frames and unrelated host nodes grow?

## Workload and factors

The matched workload contains 1, 4, or 8 instruction/correction pairs, either
in one chained `DiscourseState` or in one independent state per pair. One
correction is unresolved; the remaining corrections carry the known
`open_calendar` head. The unresolved frame rotates with replicate. Candidate
fanout is 1, 4, or 16: exactly one branch receives the correct head and every
other branch receives a distinct decoy head. The correct branch's position
rotates, so selection cannot rely on candidate order. The graph includes 0 or
10,000 unrelated `ThoughtexperimentScaleNoise` nodes. Three replicates are
run in fresh processes for every cell and both full-copy/shared-graph-pages
backends (216 workers total).

Each worker builds an identical primary for a backend, captures an immutable
snapshot, and retains all K branches at once. Each branch changes only the
unresolved interpretation's candidate head, checkpoints that input, runs
scoped closure to a zero-progress terminal pass by exhaustively sweeping every
frame, and records a
derived-only residual. The evaluator selects by the substrate-produced
grounding status and exact evidence path; the hidden correct candidate index
is used only for scoring. It returns the selected branch's total delta so the
selected hypothesis input and derived evidence are both adopted. Nonselected
branches are discarded. A separate matched world runs monolithic closure on
the correct candidate for exact whole-graph parity.

## Gates

- All candidate orders contain exactly one correct hypothesis; exactly one
  candidate grounds the unresolved frame, with every decoy remaining
  unresolved.
- Both backends produce the same selected choice, expected evidence, and
  final canonical graph as the monolithic correct-candidate oracle.
- The primary graph, rule store, and revision remain unchanged until return;
  selected residual application at the captured revision reproduces the
  selected branch exactly.
- All frame sweeps reach a zero-progress terminal pass; nonselected branches do not mutate the
  primary; the full source lock remains stable through each worker/capture.
- Report candidate count, frame/node/edge count, phase timings, total useful
  selection lifecycle, PSS before/at fanout/after drop, and process peak RSS.

No speed threshold is preregistered. This is a controlled candidate-selection
experiment over an authored communication rule and authored candidate pool;
it does not demonstrate candidate generation, learned boundary discovery,
natural-task prevalence, or general self-improvement. The 10,000-node level is
an integration scale point; million-node CoW evidence remains in the separate
source-linked scale studies.
