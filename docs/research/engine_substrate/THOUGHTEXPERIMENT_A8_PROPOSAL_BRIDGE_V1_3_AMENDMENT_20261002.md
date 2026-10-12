# Thoughtexperiment A8 proposal bridge v1.3 — score-worker source-control binding

**Date:** 2026-10-02  
**Reason:** v1.2 passed its source-attribution, canonical parity, target-preservation, and graph-path abstention gates. The first held-out score worker failed before writing a score capture because it unpacked `task.build_agent()` incorrectly: the third return is the `reflective_faculty` module, not the native engine. The worker had started isolated candidate scoring before reaching this error; no score JSON was persisted, and that failed execution is not analyzed as a result.

Correct the score worker to derive the native engine from the task's returned agent wrapper (or substrate) and add an explicit preflight assertion that it is the native engine object expected by `task.active_rule`. Add a locked control proving the source-control setup can extract the original rule before candidate scoring begins. Freeze this amendment and a new runner/analyzer lock, capture a fresh four-worker order file, inspect all order gates again, then run held-out scoring. Preserve v1.2 lock and orders unchanged. The held-out navigation fixture is the same preregistered task/case set; all candidate proposals are still generated from training contexts, with no held-out results passed to the order stage.

This amendment only repairs scoring capture and its control. A valid v1.3 score file and all analyzer gates are still required before making any utility claim.
