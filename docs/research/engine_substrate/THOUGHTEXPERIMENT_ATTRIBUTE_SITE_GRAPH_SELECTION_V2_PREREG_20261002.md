# Thoughtexperiment graph-resident proposal selection v2 — preregistration

## Question

Can the substrate itself score a finite set of proposals from graph-resident prediction/oracle evidence and return only a unique positive-evidence winner, including abstention on ties and all-wrong evidence?

## Procedure

Repeat the fresh `classify_meter_delta` cue-free active-choice panel with four workers, two branch backends, and four alias rates. The ordinary composer should abstain. Host `_default_candidates` supplies the unmodified fault and both ordered swaps. The existing selector freezes a probe before the oracle, and isolated native rule branches produce one predicted label per hypothesis. After the oracle is released, the runner stores candidate identities and per-probe predicted/expected labels as `CandidateProposal` and `CandidateEvidence` nodes in the scoring substrate. `select_candidate_from_graph_evidence` runs a native Term that aggregates matching labels and returns a winner only for a positive, unique maximum. A separate host comparison is retained as a reviewer oracle for the Term's result.

Each worker also exercises tied-positive, all-zero-match, incomplete-coverage, and duplicate-namespace cases. Tied and zero-match evidence must abstain; incomplete evidence and reused experiment IDs must be rejected before graph mutation. The primary rule set and rule revision must remain unchanged. The test reports graph materialization and native Term selection costs separately from candidate enumeration, branch execution, and query selection.

## Pass conditions and scope

Pass requires 32/32 valid query conditions to yield the forward candidate as the unique graph-Term winner after oracle scoring; all held-out and branch isolation checks must pass. The unique-winner control must select; tie/all-wrong controls must abstain; malformed coverage and namespace reuse must fail closed without adding nodes. This demonstrates substrate-owned scoring/selection over host-supplied hypotheses and labels. It does not demonstrate candidate invention, oracle trust, distribution coverage, or general structural transfer.

## Reproduction

Run the v2 runner with `--lock`, `--orders`, `--score`, then run its independent analyzer. Oracle scoring must only run after the frozen-order artifact exists. Preserve the v1 study as the prior stage; this capture adds graph-resident candidate evidence and native-Term winner selection.
