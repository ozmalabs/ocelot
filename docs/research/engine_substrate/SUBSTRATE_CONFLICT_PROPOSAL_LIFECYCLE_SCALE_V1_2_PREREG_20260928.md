# Conflict proposal lifecycle and ambiguity-aware resolution scale v1.2

## Question

Can existing graph-native Terms express a correct, stable resolver that selects a unique maximum and explicitly marks tied maxima ambiguous? What operation counts does this construction incur as proposal count grows?

## Change from v1.1

v1.1 established that the basic `MaxOver` selector silently picks one of two tied maxima. This version retains proposal generation and the same sizes/distributions, but uses `Count(Filter(Neighbours(...), score == MaxOver(...)))` to count maxima. A trigger rule marks `ambiguous=true` when that count exceeds one. A selection rule writes `selected` only when the count is exactly one and the candidate score equals the maximum. This is a graph-rule construction using existing Terms, not an engine modification.

## Protocol

Run three fresh worker processes for N = 2, 4, 8, 16, 32, 64 and distributions `unique_max` and `tied_max`. Each cell generates N proposals, runs a second closure to measure idempotence, then installs and executes the ambiguity-aware resolver. Capture native scale-audit counters, elapsed time, reports, labels, selected value, ambiguity flag, graph sizes, and source/native fingerprints. Do not use elapsed-time or `_ns` counters as deterministic work counts.

## Gates

Each worker must complete all 12 cells under the locked source and native extension. Generation must produce exactly N proposals and proposal edges and reach fixed point; repeat closure must be fixed point with zero progress and zero graph writes. Unique-max cases must select the unique top proposal and leave ambiguity unset. Tied-max cases must set ambiguity and leave selection unset. Integer operation counters must replicate across workers after excluding timing counters (keys ending `_ns`). Record every gate, including failures.

## Interpretation limits

This measures one authored resolver over one proposal family through N=64. It does not establish a general complexity bound, natural tie frequency, semantic score quality, learned proposal acquisition, or cost of general rung-3 induction. Results are conditional on this exact graph-native expression and current locked engine build. The v1.1 tie failure remains part of the evidence and is not overwritten.
