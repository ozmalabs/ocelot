# SD loop report reuse

The SD ladder used to recompute an entire report for every field a rule stored.
For example, `sd_decode` requests the full `ShapeDecode` report, its residual,
and its covered count as three effects. Those are one cognitive operation, but
the evaluator performed the beam search three times.

The evaluator now memoizes the full report for sibling projections from
`ShapeDecode`, `TransformDecode`, `DimInfer`, and `GenInfer`. Cache identity is
integer/symbolic: operator tag, integer parameters, symbols, input Values, and
an integer fingerprint of the graph-resident typed codebook. No floating-point
state or arithmetic was added to cognition. A codebook mutation between two
effects changes the fingerprint and forces a fresh report; unrelated graph
writes do not.

`scripts/profile_sd_report_cache.py` compares this against a cache-busted
same-binary control. In the recorded run, three field projections performed
one third of the interior work at every codebook size. Median latency improved
from 170,980 ns to 165,239 ns at K=1, from 267,065 ns to 196,419 ns at K=16,
and from 553,728 ns to 294,238 ns at K=64. The benefit therefore grows with
the amount of cognition each redundant report would have repeated.

Raw output is in `results/sd_report_cache_profile.json`. The static integer
boundary and sequential-invalidation regression are in
`tests/test_sd_cache_integer_guard_migrated.py`.
