# Bounded planner native unit audit v1.2 amendment

## Reason

V1.1 linked the Rust test binary successfully, but execution stopped before the Rust test harness loaded: the dynamic loader could not find `libpython3.13.so.1.0`. The v1.1 command, linker arguments, exit status, and full warning/error output are preserved in its [manifested report](../../../evaluation/reports/substrate_planning_native_unit_audit_v1_1_20260928.json) and [stderr log](../../../evaluation/run_logs/substrate_planning_native_unit_audit_v1_1_20260928_1.stderr.log). This was a runtime-loader setup failure, not a test assertion result.

## Amendment

V1.2 keeps the same five test names and gates. It adds the active interpreter's `LIBDIR` to `LD_LIBRARY_PATH` for Cargo test child processes, retaining any existing value. V1.2 writes separate artifacts and leaves v1/v1.1 untouched.
