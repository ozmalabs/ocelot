# Held-topic global versus per-area settlement parity v1

Date: 2026-10-05  
Status: preregistration; current-source semantic comparison, not a response-time deferral test.

## Question

Does the existing opt-in `run_rules_settle` API reach the same complete graph and conversation outputs as the production global `run_rules()` closure on the seven-turn held-topic workload when the traced population rules are assigned explicit areas?

## Arms

All arms boot the same full seed set, teach the same copper/basalt/hexagon facts, then run the same seven prompts in the same order in three fresh worker processes per arm.

1. **Global:** unchanged `WorldAdapter.comprehend()` and `run_rules()`.
2. **Barrier areas:** assign `slang_variant_bind_denotes` to `ambient_lexicon`, `curiosity_targets_ambivalent_nodes` to `ambient_curiosity`, `gr_condition_lapse` to `ambient_residual`, and `sd_decode`, `sd_transform_decode`, and `sd_infer_dimension` to `shape_decode`; call `run_rules_settle(budget_per_area=0, max_rounds=100000, drop_residual=false, snapshot_round=true)` from `comprehend()`.
3. **Live areas:** same assignments and unlimited settlement, with `snapshot_round=false`.

No rule is removed, disabled, or edited. All area assignments are scheduling metadata. The global arm remains the semantic oracle.

## Capture and gates

- Lock protocol, runner, base held-topic runner/protocol/amendment, Python/seed source closure, native extension, build manifest, and commit.
- Three fresh worker processes per arm; exactly seven turns each; source fingerprints unchanged at worker start/end and after capture.
- After each completed turn, record complete canonical graph digest, node/edge counts, reply, route, receipts, and task outcome fields. Compare graph digest and reply at every corresponding turn across arms and workers.
- Record settlement calls, rounds, residual count, per-area dirty/attempted/progressed/carried counts, and existing scale-audit work. Reject any arm that hits its round cap or returns with a residual at the purported fixed point.
- Report task utility separately. The known “Can you tell me about copper?” clarification is retained as a workload limitation and cannot be converted into a pass by scheduler parity.
- Timings are descriptive only: task frame projection and complete graph digest are capture overhead; the gate is exact semantic parity and scheduler behavior.

## Interpretation limits

Passing unlimited per-area settlement would validate a current API's full-settlement semantics on this workload. It would not establish that per-area execution is faster, that population rules can be moved off the response path, or that the scheduler generalizes. The API applies one shared budget to each area and `WorldAdapter.converse()` waits for its closure calls. A separate priority/residual continuation API would still need full graph/reply parity and mutation wake-up controls.
