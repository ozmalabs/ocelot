# Gap grounder operation-key comparison v1 preregistration

## Question and scope

Does adding the observed operation multiset to the gap faculty key prevent cross-operation coalescence while preserving duplicate recognition when only argument names change? This is a bounded follow-up to the faculty-key collision result. It tests one candidate identity policy in the real `extend_for_gap` path; it does not test general key design or authorize a production change.

## Arms

- **Faculty key (current):** use the unmodified `gap_<faculty>` hint.
- **Faculty plus operation key (candidate):** pass `gap_<faculty>__ops_<sorted predicate multiset>` to the existing `name_hint` parameter. The candidate is a harness-side intervention; production source remains unchanged.

The operation key intentionally ignores relation arguments and retains repeated predicate heads. It distinguishes the frozen A/B operation families and should coalesce B with B-value, whose operation heads are the same while argument labels differ. It does not encode topology or role wiring; no broader structural-identity claim will be made.

## Fixtures and order controls

- A: the three-operation classify/route/mark-handled gap from v1.
- B: `spectral_value` followed by `log_scale`, with signal/magnitude/value arguments.
- B-value: the same two operation heads with sensor/amplitude/result argument labels.

Run each arm in a fresh `WorldAdapter(seeds=())` for seven sequences: isolated A, isolated B, isolated B-value, B→B, B→B-value, A→B, and B→A. Total: 14 fresh graphs and 22 calls. Call `extend_for_gap(..., verify=True)` for each event. Capture observation signatures/status, concern keys, outcome/path, verification, axis/request/held-primitive deltas, codebook epoch, native steps, and source hashes before/after.

## Outcomes and gates

Primary comparisons: (1) exact-repeat B second call against isolated B; (2) B-value second call against isolated B and the candidate-key B repeat; (3) A/B cross-order second calls against the corresponding isolated outcome. Report recognition status separately from grounder route and verification. Count a composite-key result as improved only if it suppresses B-value duplication, separates A/B identity under both orders, and does not change isolated outcomes. Verification failure remains a failure even when routing matches.

Gate: all 22 calls complete; the pre/post lock is identical; A/B operation multisets differ; B/B-value operation multisets match while observation signatures differ; all four cross-order/control comparisons are emitted. This fixed synthetic panel cannot estimate natural frequencies, downstream task success, or general tractability. Do not adopt a global key change from this result alone.

## Execution

```sh
python3 evaluation/substrate_capability/gap_grounder_operation_key_v1.py --lock
python3 evaluation/substrate_capability/gap_grounder_operation_key_v1.py
python3 evaluation/substrate_capability/analyze_gap_grounder_operation_key_v1.py
```
