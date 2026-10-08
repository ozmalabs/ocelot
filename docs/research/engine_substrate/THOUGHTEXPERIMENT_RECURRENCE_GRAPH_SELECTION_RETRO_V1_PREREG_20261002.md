# Thoughtexperiment recurrence graph-selection retrospective v1

## Purpose and limitation

Check whether the new graph-resident proposal scorer transfers from a symbolic attribute-swap fixture to the recurrence-offer candidate family. This is a retrospective integration/transfer check on the already published source-locked recurrence candidate-admission capture, not a new blinded experiment: its train and held-out outcomes are visible in the worktree. The replay will provide only training-derived evidence to the graph Term, then inspect held-out outcomes after its winner has been fixed.

## Procedure

For each of the three frozen recurrence workers, load all eight generic candidate descriptors and their recorded training/held-out outcome rows. Recompute per-episode correctness from `offer_counts == 1` for the due key and `fixedpoint_progress == 0`; do not use the stored `pass` flag. Build graph evidence from the two disjoint training recurrence keys per worker only. In a fresh substrate snapshot branch, call `select_candidate_from_graph_evidence` on the eight candidates and all six training episodes. Return only the selected candidate digest and training-match count to primary. After recording the selection, score its digest against all six held-out episodes and report selection cost, evidence materialization cost, and primary isolation.

## Acceptance and interpretation

The transfer check passes if the graph Term uniquely selects the candidate with six correct training episodes, that digest is `dedup_identity_fix`, it passes all six held-out episodes, all seven other candidates have less than six training matches and fail at least one held-out episode, the primary graph gets one compact residual but no candidate/evidence nodes, and source/input hashes are stable. Because prior results were already inspected, success is evidence of cross-family data/API transfer only; it does not establish independent replication, online discovery, candidate generation, or blinded generalization.

## Reproduction

The runner source-locks itself, `domains/contract_query.py`, the original recurrence runner/lock/raw capture, and this protocol. Run `--lock`, `--replay`, then the independent analyzer. The replay never uses held-out fields to construct evidence or choose the candidate.
