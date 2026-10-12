# Thoughtexperiment graph-resident proposal selection v3 — preregistration

## Question

Can the substrate score a finite proposal set from graph-resident prediction/label evidence, return only a unique positive-evidence winner, and return a compact residual to the primary graph without leaking candidate/evidence nodes?

## Procedure

Repeat the fresh `classify_meter_delta` cue-free active-choice panel with four workers, two branch backends, and four alias rates. The ordinary composer should abstain. Host `_default_candidates` supplies the fault and two ordered swaps. The query and prediction orders are frozen before labels are released. After oracle release, a fresh snapshot branch receives `CandidateProposal` and `CandidateEvidence` nodes; `select_candidate_from_graph_evidence` uses a native Term to sum matching labels and selects only a unique positive maximum. The branch is discarded after selection. A compact `ExperimentResidual` containing the selected proposal ID and probe identity is returned to the primary graph. Verify candidate/evidence nodes do not leak into primary and active rule definitions remain identical.

Per worker, also test tied-positive and all-wrong labels (both must abstain), incomplete evidence (reject before graph mutation), and duplicate experiment namespace (reject). Record branch fork, graph-node materialization plus Term evaluation, residual return, proposal enumeration, native prediction/closure, and active-query times separately. A reviewer-side host comparison independently identifies the sole matching candidate.

## Pass conditions and scope

Pass requires all 32 active choices to return the forward proposal as unique graph-Term winner; five held-outs per worker must agree with the forward proposal and reject fault/reverse on nonzero cases. Tied and all-wrong evidence must abstain; malformed coverage and duplicate namespaces must fail closed. Every branch must reach a fixed point, receipts must validate, primary rule definitions must remain unchanged, exactly one compact residual must return per active choice, and no candidate/evidence nodes may enter primary. The candidates, input pools, predictions, and oracle labels remain host-supplied, so this is evidence selection over a bounded hypothesis set, not autonomous invention or oracle verification.

## Reproduction

Run the source-locked v3 runner with `--lock`, `--orders`, and `--score` in that order, then run the independent analyzer. Oracle labels are written only after orders freeze.
