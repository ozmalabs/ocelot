# GenInfer scope index trace v2.1 amendment

Date: 2026-10-05

The v2 capture preserved exact outputs and candidate work, but failed its
pre-registered count gate: the protocol expected two index queries and two
result members per worker. The fresh traces showed four GenInfer invocations,
four index queries, and four scoped result members in every worker. Production
closure evaluates the relevant GenInfer Term more than once per observation;
the earlier query count assumed one call per frame and was wrong.

The original v2 lock, capture, and failed analysis remain unchanged. V2.1
repeats all four conditions in 12 new fresh processes and corrects that gate
to four queries/members. This is a confirmatory rerun of the same authored
fixture, not an independent prior prediction: the corrected count is motivated
by the v2 trace. No engine or measurement logic changed between v2 and v2.1.
All sources, including this amendment and the v2.1 analyzer, are locked anew.

Reproduction uses the current provenance-checked extension:

```sh
python3 evaluation/substrate_capability/substrate_geninfer_scope_index_trace_v2_1.py --lock
python3 evaluation/substrate_capability/substrate_geninfer_scope_index_trace_v2_1.py --run
python3 evaluation/substrate_capability/analyze_geninfer_scope_index_trace_v2_1.py
```
