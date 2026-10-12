# Native rule-closure pilot — post-fix recheck

**Run ID:** `closure-pilot-20260924T090058Z`  
**State:** exploratory pilot; not preregistered or confirmatory.  
**Raw artifact:** [`substrate_closure_pilot_20260924_recheck.json`](../../../evaluation/reports/substrate_closure_pilot_20260924_recheck.json)  
**Harness:** [`substrate_capability_closure_pilot.py`](../../../scripts/substrate_capability_closure_pilot.py)  
**Prior failed run:** [`SUBSTRATE_CLOSURE_PILOT_RESULTS.md`](SUBSTRATE_CLOSURE_PILOT_RESULTS.md)

## Diagnosis and correction

The first pilot’s rules expressed the intended finite transitive closure. The trace showed the failure in `Substrate::attempt_one_rule`: after a cold full rematch, the engine recorded each matched edge-type cursor at the post-effect edge count. A recursive rule writing an edge type it also reads was then re-dirtied, but its incremental visit saw zero new edges because its own newly minted edges had been included in that advanced cursor.

The cold-rematch path now records the matched-edge frontier before applying bindings and restores the cursor to that frontier. Newly created same-type edges remain visible to the next incremental visit. The focused regression test is [`test_recursive_rule_closure_migrated.py`](../../../tests/test_recursive_rule_closure_migrated.py). It checks exact closure on a six-vertex path and a zero-work follow-up.

## Measurement

The post-fix pilot used path sizes 6, 10, and 14; two graph-authored rules; a 100,000 progress-step cap; and the independent path-closure formula. The native build fingerprint was `25a2b504890f`; the harness refused to run if source provenance was stale.

| Path vertices | Initial edges | Expected/observed total edges | Progress steps | Candidate pairs enumerated | Leaf visits | Wall time (ms) | One-step follow-up |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 5 | 15 / 15 | 4 | 19 | 10 | 0.045 | 0 |
| 10 | 9 | 45 / 45 | 8 | 53 | 36 | 0.034 | 0 |
| 14 | 13 | 91 / 91 | 12 | 103 | 78 | 0.054 | 0 |

All three outputs match the expected transitive closure, and each follow-up returns zero. Candidate-pair counts increase with size, but these three tiny cases and one structural family do not establish an asymptotic envelope. The wall times are below a useful benchmarking scale and remain sensitive to process/runtime noise. Peak RSS is a shared process high-water mark, not a per-size measure.

## Verification performed

- `scripts/engine_build.sh` completed and wrote build fingerprint `25a2b504890f`.
- `PYTHONPATH=runners/dsl/python:. python3 -m pytest tests/test_recursive_rule_closure_migrated.py -q --tb=short` — **1 passed**.
- `PYTHONPATH=runners/dsl/python:. python3 -m pytest tests/test_incremental_match_migrated.py -q --tb=short` — **6 passed** in 277.99 s.
- The post-fix pilot emitted exact expected edge counts for all three sizes; raw records contain provenance, output counts, counters, costs, and the terminal probe.

These checks support this recursive two-edge rule pattern and the existing incremental-match regression cases. They do not establish that all rule effects terminate or that all rule patterns are polynomial.

## Current conclusion and next gate

The original mismatch was an engine cursor bug, not an incorrect closure oracle. The fix restores closure for this tested workload. Keep the first failed artifact as counterevidence about the pre-fix engine, and use this recheck as post-fix pilot evidence only.

Before a confirmatory closure envelope:

1. expand controlled families to vary path length, branching, rule count, join arity, duplicate effects, and fresh-node minting;
2. record per-instance peak RSS in isolated worker processes and reconcile candidate counters with hand-countable small cases;
3. compare a known-good reference implementation and retain adversarial/high-candidate inputs;
4. define the restricted rule class for any termination statement and separately test resource-capped nontermination;
5. preregister sizes, thresholds, timeout behavior, analysis, and raw-record expectations.

The result does not validate cheap cuts or frame locality. The path has small treewidth, but this experiment measured recursive rule closure, not frame discovery or inference factorisation.
