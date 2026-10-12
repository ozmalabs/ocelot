# Two-sheet current-source vision scale extension v2.4 preregistration

## Question
As each sheet grows from 256 to 4,096 SUnits, how do total Term evaluations, counter-off closure time, and process memory scale under global and root-scoped versions of the same settle rule?

## Design
Repeat the v2.3 controlled two-sheet fixture at side lengths 32 and 64 (2,048 and 8,192 total SUnits), with the same three RNG seeds, two B-sheet states, global/root-scoped folds, and isolated counter-off/on workers. The 96 new cells make 144 cells total across the v2.3 and v2.4 size grids. Keep the same deterministic afferents, root membership, closure work cap, independent equation oracle, and exact audit-on/off parity checks. Capture both the operation-specific `term_unit:NodesOfType` counter and total Term evaluation counts; do not treat the former as a total-work measure, because it omits `Neighbours` result cardinality in the scoped source. Report the aggregate input scope per target separately (all 2N units globally versus N units within one sheet for side length N).

## Integrity and analysis
Use fresh isolated workers for every size/scope/state/audit cell. Lock the v2.4 runner and protocol, current engine/native inputs, and the prior v2.3 report, analyzer, lock, and runner. Require exact output and progress parity between counter-off/on for every cell, exact root membership, equation residual ≤1e-12, no cap exits, per-rule counter conservation, the measured `NodesOfType` expressions, and stable source hashes. Report median and range for closure wall/CPU time, total Term evaluations, process peak RSS, and audit overhead by size and scope.

## Claim boundary
This extends one controlled arithmetic factor through 8,192 SUnits. It tests one explicit source of cross-frame coupling and the cost of the audit counters. It does not measure natural task distributions, general rule sets, learned hierarchy, or the 10⁷–10⁸ node regime. The global and root-scoped aggregate input scopes are measured; they are not exact graph treewidth bounds because an implementation could factor the aggregate with auxiliary nodes.
