# Where-aware prefix-cost selector v2 preregistration

Date: 2026-10-01

## Rationale and question

V1 estimated structural joins but ignored the production `where` guard. The retinal matcher can evaluate the epoch comparison as soon as the `column` and `percept` variables bind, pruning guard-failing columns before expanding their receptor edges. V2 includes supported guard atoms at the earliest prefix where all their variables are bound. Does this correct the held-out order choice on a new support profile while preserving manageable selection cost?

## Frozen selector

Keep v1's beam width 8, sample cap 128, smallest-global-relation first clause, estimated-prefix scaling, lexicographic tie-breaking, and Python adjacency indexes. Add partial evaluation for `And`, `Eq`, `Gt`, `Var`, `Lit`, and `Attr`. Evaluate each top-level conjunction atom as soon as all of its referenced variables are bound; reject a sampled partial binding immediately when any known atom is false. Unknown or unsupported term kinds remain undecided and do not prune. Costs still include relation candidates scanned before the guard rejection. No parameter is tuned on v2 outcomes.

## Held-out fixture

Use the production `photon_column_synthesizes_retinal_percept` rule, its real epoch guard and productive effects, and N=20 columns. The new deterministic receptor-count profile is `count[r,i] = 1 + ((7i + 5r + floor(i/5)·r + 3) mod 4)` for relation index r∈{0,1,2,3} and column i∈{0,…,19}. As in v1, every relation edge exists at every column, only the final percept has epoch 0, and all other percepts are guard-rejected. Three fresh workers each compare the selector against all 120 native clause orders and the automatic install order. Record selector choice and timing, estimated/actual candidate work, exact minimum, productive attributes, graph parity, and terminal closure. Repeat selector timing 21 times, and rerun the selector choice without instrumentation.

## Gates

- Three source/native-locked fresh workers on the same generated profile.
- Exactly all 120 unique orders measured per worker; deterministic selector decision across repeats and workers.
- Correct guard rejection and one productive percept update in default, selector, and every exact order.
- Canonical semantic parity, fixed-point, instrumentation parity, and exhaustive minimum reconciliation.
- Report selector regret and timing whether favorable or not; no success threshold is imposed on the ranking hypothesis.

## Limits

This tests one supported guard shape and one new synthetic N=20 retinal profile. Unknown terms are conservatively ignored, so it does not establish correctness for arbitrary guard languages. The implementation is a Python measurement prototype, not a Rust matcher integration or natural-image benchmark.
