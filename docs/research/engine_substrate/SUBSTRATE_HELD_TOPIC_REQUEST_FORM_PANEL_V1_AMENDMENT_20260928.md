# Held-topic request-form panel v1 amendment

Date: 2026-09-28  
Applies to: [v1 preregistration](SUBSTRATE_HELD_TOPIC_REQUEST_FORM_PANEL_V1_PREREG_20260928.md)

## Lock setup correction before any task execution

The initial lock-generation call recorded the caller's inherited `PYTHONPATH`. The runner prepends the repository and selected native package paths for child workers, so worker 0 rejected the lock before booting or executing any benchmark task. No scored observations were produced by that attempt.

The driver now records the effective child import path deterministically and recognizes it when validating a child. It continues to record the separately selected environment variables and native-package path. The corrected driver is re-locked before execution; no prompt, expected answer, scoring rule, or analysis decision changed. The failed attempt is retained in this amendment for a complete run history.

A second launch also stopped before boot/task execution: worker validation compared its two-field runtime snapshot to the entire lock object, which additionally contains the task and fact manifests. The comparison now checks the intended `inputs` and `runtime_data` fields explicitly. No benchmark cases ran in either rejected launch. The driver hash and amendment hash were refreshed in the lock after this correction.

The next attempt passed pre-run validation and executed the workload, but post-run validation found input drift. That driver version raised before returning the worker object, so the completed prompt data was not preserved as raw evidence; this attempt is an invalid, incomplete capture and is not scored. The current driver retains worker output and names changed fingerprint paths even when the stability gate fails. The protocol and oracle remain unchanged; the lock is regenerated for the corrected driver/amendment pair before the next attempt.
