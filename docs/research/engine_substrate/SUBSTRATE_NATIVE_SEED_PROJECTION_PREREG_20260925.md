# Native seed manifest projection experiment preregistration

Date: 2026-09-25  
Status: preregistered follow-up to the nested prefix scale measurement

## Question

Does serializing irrelevant top-level manifest payload at the PyO3 boundary materially contribute to full seed boot cost, while preserving the observed substrate and Python-side load result?

## Hypothesis and intervention

The native function `PySubstrate::load_seed_manifest` converts the entire Python object through `pyobj_to_json`, then reads only `nodes`, `edges`, `productions`, `rules`, `reflexes`, `id`, `self_modification_patchable_rules`, `area`, `order`, and `latency_class`. The treatment projects to those keys immediately before the original native method call; the original Python manifest remains unchanged and is still used by the rest of `load_all_seeds`. The control passes the original object unchanged. This tests boundary conversion cost only; it does not change persisted manifests, seed indexing, or the Python materialization path.

The projection is a temporary measurement intervention, not an approved production behavior. It must be rejected if any result/report or downstream self-model consumer changes. The key allowlist is source-derived and must be rechecked against the locked Rust function before each run.

## Design

- Corpus: frozen `problem_shape_eventized_rule_order_seed_corpus_lock_v1_7` snapshot, canonical topological prefixes N=512 and N=737. At N=737 preserve all 833 physical files, including non-indexed `self_load_only` and non-dict files.
- Arms: control and projection, each with three independent fresh processes at both sizes (12 workers total), in an interleaved order fixed in the runner.
- Environment: identical interpreter, native build, source snapshot, seed directory and environment variables; no in-place writes to the corpus. Record per-process wall time, CPU time, RSS high-water mark, native-call count, total input JSON bytes, and total projected JSON bytes. The wrapper retains manifest references and computes byte totals after the timed boot and RSS snapshot so diagnostic JSON dumps do not inflate those measurements. Retaining these references may affect boot peak memory; report this instrumentation limitation and use identical wrappers in both arms.
- State oracle: compare each arm at a given N on the complete boot report (including per-seed failures), node/edge counts, graph snapshot, grammar, exported rule store, rule access sets/order, and relevant self-model summary counts. Require all three repetitions within each arm to match exactly and treatment state to match control exactly.
- Runtime: separately time wrapper work around the native call and total boot. Report medians and all observations. Do not remove outliers. The sample is exploratory; it estimates this intervention on this corpus, not general startup or asymptotic complexity.

## Pass and interpretation gates

1. Lock check: corpus digest, manifest hashes, Python source hashes, Rust source hash, built-extension provenance, protocol hash, and runner hash match before and after execution.
2. State parity: every listed fingerprint and boot report is exactly equal across arms and repetitions.
3. Intervention integrity: the projected JSON omits only keys outside the reviewed native read set, while the Python source manifest is byte/value-identical before and after loading.
4. Cost evidence: report actual byte reduction, wrapper conversion time, total boot wall/CPU, and RSS. A lower projected wall median alone is not causal proof if native-call/wrapper timing does not account for it or sample spread overlaps substantially.

Failure of a parity or integrity gate means the projection is not safe under the present contract and no performance benefit may be claimed. Passing parity with negligible runtime change means the large nested payload is not a material boot bottleneck under this implementation. A consistent improvement localizes avoidable work to boundary serialization, but any permanent change still requires review of all direct callers and the Python/native API contract.

## Limits

This experiment measures only startup for two points in one frozen authored corpus. It does not establish cheap-cut prevalence, frame locality, task capability, learning cost, scaling to arbitrary graphs, or commodity-hardware feasibility. The source is a shared worktree with unrelated edits; the lock must therefore capture the exact checked-in and working-tree artifacts actually executed, without reverting or rewriting unrelated files.

## Harness execution note

Two initial harness attempts are excluded and retained as raw diagnostics. Attempt 1 completed one N=512 control worker, then the driver failed while trying to read a PID from `subprocess.CompletedProcess`; that worker was not checkpointed. Attempt 2 completed the planned 12-process schedule but patched the Python facade class instead of the underlying PyO3 class; its interception counter was zero in every worker, so it tested parity only and did not apply the intervention. The harness now patches `substrate_rs._native.Substrate`, and the complete schedule is rerun. Both attempts are reported as protocol deviations and excluded from cost estimates.
