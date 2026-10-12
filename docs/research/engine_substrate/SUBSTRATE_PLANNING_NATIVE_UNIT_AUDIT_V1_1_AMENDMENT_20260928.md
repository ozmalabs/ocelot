# Bounded planner native unit audit v1.1 amendment

## Reason

The first execution did not reach any test. Cargo compiled the library test target, then the linker failed with unresolved CPython symbols because this crate enables PyO3's `extension-module` feature. The runner then raised `ModuleNotFoundError: domains` while assembling provenance because it had added `scripts/` but not the repository root to `sys.path`. The compiler output is retained at [`run 1 stderr`](../../../evaluation/run_logs/substrate_planning_native_unit_audit_20260928_1.stderr.log). The parent-side `ModuleNotFoundError` surfaced in the terminal tool output but was not captured to the empty parent log; this custody gap is disclosed. This attempt is harness/setup failure evidence, not a failed planner test.

## Amendment

V1.1 preserves the same five exact test names and one-test-per-command gate. Before invoking Cargo, it obtains `LIBDIR` and `LDLIBRARY` from the active Python interpreter and supplies Rust linker arguments for that host Python library, so a `cargo test` executable can resolve PyO3 symbols. It also places the repository root on the runner's import path. No Rust implementation or test source changes. V1.1 writes separate logs and report files; it does not overwrite v1 artifacts.

## Claim boundary

The outcome can support only those five unit fixtures. The initial link failure remains in the record and is not counted as a test result.
