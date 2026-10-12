# Rung 3 ambiguity and counterexample response v1 preregistration

## Question

When sparse training supports a simple but wrong threshold shortcut, does the integrated synthesizer accept it? Does one exact counterexample eliminate that false candidate, and can a narrowly supplied operator grammar recover the intended program within the same default candidate cap? This directly measures the ambiguity, false-acceptance, and query-cost boundary exposed by the prior hinge false generalization.

This is an authored integer-pair task with a known oracle, not a test of autonomous query selection. The evaluator chooses the distinguishing example in advance. The constrained grammar is an oracle-information upper bound, not a learned selector.

## Pilot disclosure

Before locking the confirmatory panel, one worker per arm was run to validate branch semantics and estimate feasibility. Sparse/default accepted a 6/6 training fit and scored 0/6 held-out; counterexample/default gapped at 200,000 candidates; counterexample/oracle-grammar accepted a 7/7 training fit and scored 6/6 held-out after 58,824 candidates. These pilot rows are excluded. The 15 confirmatory workers will run from fresh processes under the source lock below; outcomes are already known directionally, so this replication tests repeatability and source-locked branch behavior rather than an undisclosed hypothesis.

## Target, examples, and arms

The target is `f(r,c) = (r + max(c - 1, 0), c)`. All arms share the exact six held-out pairs: `(1,3),(2,3),(1,4),(4,4),(2,5),(5,5)`. The ambiguous training set is `r ∈ {0,1}` at each `c ∈ {0,1,2}`. The corrective example is `(r,c)=(0,3)` with target `(2,3)`; it distinguishes the known shortcut `r + (c > 1)` from the target.

Run five fresh-process workers per arm (15 total), with one randomized fixed schedule and equal 200,000 candidate caps:

1. **Ambiguous/default:** six sparse examples, default broad operator path.
2. **Counterexample/default:** the same six examples plus the one distinguishing counterexample, default broad operator path.
3. **Counterexample/oracle grammar:** the seven examples plus explicit `ps_enum_ops = ['Plus','Minus','Max','TupleOf']`.

Each worker learns only inside an isolated shared-graph-page branch. If an accepted Program exists, evaluate its reflected IR on every training point and every common held-out point from both eager-copy and shared-graph-page child branches. Record the primary and candidate snapshot digests before/after evaluation. No candidate is adopted.

## Measures and decision criteria

Report accepted/gapped rate, exact training fit, exact held-out transfer, false acceptance (accepted program with any oracle-held-out mismatch), candidate work/cap, pump wall and CPU time, peak RSS, selected grammar, and branch validation cost. Retain all misses and errors.

Primary ambiguity signature: the sparse/default arm accepts a candidate that fits all six training examples but fails at least one oracle-held-out point. Counterexample efficacy: the corrected/default arm must either find a candidate with exact held-out transfer or gap without accepting a false candidate; report which outcome occurs. Oracle-grammar diagnostic: if it accepts, require exact training and held-out outputs. The oracle arm cannot be described as autonomous disambiguation.

Integrity gates: exact 15-cell randomized schedule and source/native lock, unique fresh worker PIDs, exact independent reconstruction of training/holdout labels, candidate training fit readback, complete held-out readback for every accepted IR, primary and candidate snapshot isolation, eager/shared semantic and final-state digest parity, complete cost/status fields, and no unreported worker failure. A failed gate blocks the corresponding claim.

## Claim boundary

The panel measures one ambiguity construction and one known distinguishing query. It can show that the current Occam/search route accepts, rejects, or gaps under these fixed conditions. It does not estimate ambiguity prevalence, discover a query policy, prove general program learning, or establish broad tractability. Results apply only to the locked substrate revision and task.
