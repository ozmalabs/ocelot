# Native rule-closure pilot — initial result

**Run ID:** `closure-pilot-20260924T085224Z`  
**State:** exploratory pilot; not preregistered or confirmatory.  
**Raw artifact:** [`substrate_closure_pilot_20260924.json`](../../../evaluation/reports/substrate_closure_pilot_20260924.json)  
**Harness:** [`substrate_capability_closure_pilot.py`](../../../scripts/substrate_capability_closure_pilot.py)  
**Protocol:** [`SUBSTRATE_BENCHMARK_PROTOCOL.md`](SUBSTRATE_BENCHMARK_PROTOCOL.md)

**Follow-up:** the cursor bug diagnosed by this run was fixed and the same workload now passes at sizes 6, 10, and 14. See [`SUBSTRATE_CLOSURE_PILOT_RECHECK_RESULTS.md`](SUBSTRATE_CLOSURE_PILOT_RECHECK_RESULTS.md). This artifact remains the pre-fix failure record.

## Question

Can the current native `Substrate.run_rules` path compute finite transitive closure on a simple directed path, and does the harness capture enough evidence to support a larger closure/matching study?

The synthetic workload installs two graph-authored rules:

1. `pilot_link(x,y) ∧ pilot_link(y,z) → pilot_reach(x,z)`
2. `pilot_reach(x,y) ∧ pilot_link(y,z) → pilot_reach(x,z)`

For a directed path with (n) vertices, the expected total edge count after closure is (n(n-1)/2): the original (n-1) links plus all longer forward reach relations. A separate one-step runner call checks whether more rule work is available after the measured call returns. The check is outside the primary timing/counter window.

## Execution and provenance

The run used the checked-out native PyO3 extension after the sanctioned `scripts/engine_build.sh` completed. The build fingerprint was `2e02336c578f`; `domains.engine_provenance.build_is_stale(".")` returned no stale Rust files immediately before the run. The extension exposed `scale_audit_snapshot/reset/set_enabled` and the per-substrate `counters` API. The raw JSON records commit, native extension/build-record hashes, protocol/script hashes, environment details available to the harness, workload hash, and exact invocation.

The run is project-self-custodied and development-only. It has no task-split or independent evaluator. Two graph sizes are too few to support a scaling curve. Peak RSS is a process high-water mark shared across sizes, not an isolated per-size memory measurement. Wall times are tiny and are not a useful performance estimate. The raw artifact preserves these limits and all counter values.

## Results

| Path vertices | Initial edges | Observed total edges | Expected total edges | Progress steps | Candidate pairs | Terminal probe steps | Outcome |
|---:|---:|---:|---:|---:|---:|---:|---|
| 6 | 5 | 12 | 15 | 2 | 16 | 0 | Closure mismatch |
| 10 | 9 | 24 | 45 | 2 | 32 | 0 | Closure mismatch |

The runner returned after two progressing steps in both cases. Its one-step follow-up found no further dirty-rule progress, while the independent path-closure count showed missing reach edges. The scale-audit candidate-pair count increased from 16 to 32 over these two sizes; given the closure mismatch and only two tiny instances, this is a harness diagnostic, not a complexity result.

## Interpretation

**Pilot outcome: fail for expected closure; harness path viable enough to diagnose.** The experiment does not yet distinguish an error in the workload/rule specification from an issue in dirty-rule propagation, matching cursors, or the native runner’s closure semantics. The finding must not be reported as a general rule-engine failure until that distinction is resolved. It does demonstrate why fixpoint return/settlement status cannot substitute for checking the requested semantic result.

No tractability or performance conclusion follows. The pilot only covers the direct native PyO3 `Substrate.run_rules` path, two hand-authored rules, directed paths of sizes 6 and 10, and one exact expected-output check.

## Diagnosis record

1. **Rule/oracle check:** confirmed. The path closure oracle is (n(n-1)/2) total directed edges; the post-fix run matches at three sizes.
2. **Trace:** confirmed the recursive reader’s cursor was advanced past newly created same-type edges; the incremental visit reported zero new drivers.
3. **Corrective change:** the cold-rematch path now retains its pre-effect edge frontier; a focused regression pins same-type recursive closure.
4. **Regression:** the focused test and existing incremental-matching file pass after rebuilding the native engine.
5. **Retest:** preserved as [`SUBSTRATE_CLOSURE_PILOT_RECHECK_RESULTS.md`](SUBSTRATE_CLOSURE_PILOT_RECHECK_RESULTS.md). The first failed JSON is not overwritten.

The diagnosis gate is cleared for this specific workload; the next step is a broader controlled pilot across branching, arity, duplicates, and minting, with isolated per-size resource records. Confirmatory thresholds remain out of scope until that expanded pilot validates counters and resource capture.
