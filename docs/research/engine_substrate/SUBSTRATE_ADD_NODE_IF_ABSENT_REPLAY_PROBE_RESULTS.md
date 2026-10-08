# `AddNodeIfAbsent` effect-only attribute replay probe

**Run date:** 2026-09-25  
**Evidence grade:** exploratory mechanism probe  
**Status:** both controlled cases reached their declared graph oracle and a zero-work terminal probe. The dedup identity policy determines whether replay duplicates or refreshes the output.

## Method

The runner [`substrate_add_node_if_absent_replay_probe_v1.py`](../../../scripts/substrate_add_node_if_absent_replay_probe_v1.py) constructs two native one-binding readers whose output value depends on `Attr(x, watched)`. The reader is first settled against value 0. Only then is a writer installed to change the source to 7, which isolates the stale-output condition from cold-start scheduling. After the writer settles, the runner records the suppressed output, invokes `force_all_dirty()` as a full-rescan diagnostic, and compares the resulting graph with a declared oracle. Stage A compare mode is enabled, but neither case produces an admitted compare drain; the result therefore supplies no undo/commit comparison evidence.

## Results

| Identity/effect policy | Before rescan | After full rescan | Interpretation |
|---|---|---|---|
| `AddNodeIfAbsent` key contains computed `value=Attr(x, watched)` | one node with value 0 | two nodes with values `[0, 7]` | Changed value changes the dedup key. Rescan creates a second node and retains the stale result. |
| `AddNodeIfAbsent` key is stable `identity="root-1"`, then `SetAttr(born, value, Attr(x, watched))` | one node with value 0 | one node with value 7 | Stable key reuses the witness; the following attribute write refreshes it in place. |

Both cases report one progressing writer step, one progressing rescan step, and zero terminal-probe progress. All declared checks pass. Two fresh-process runs produced byte-identical JSON (SHA-256 `ef2c5ef25b7e3500c4f6bb965a20c23124dded04ab844a7ac8b06a9634a5aa99`). Raw output and exact source/build identities are in [`substrate_add_node_if_absent_replay_probe_v1_20260925.json`](../../../evaluation/reports/substrate_add_node_if_absent_replay_probe_v1_20260925.json); the pre-repeat raw snapshot is also retained at [`precheck`](../../../evaluation/reports/substrate_add_node_if_absent_replay_probe_v1_precheck_20260925.json).

The first harness attempt is retained at [`attempt1`](../../../evaluation/reports/substrate_add_node_if_absent_replay_probe_v1_attempt1_20260925.json). It allowed the reader and writer into the same initial closure. Because `AddNodeIfAbsent` reads the candidate node type while writing that type, cold closure had already created both value variants before the intended rescan comparison. That fixture did not test the stated question; the amended runner settles the reader before installing the writer. The corrected probe also asserts that both outputs are stale at the mutation boundary before full rescan, and explicitly records that Stage A admitted zero drains.

## Interpretation and limits

This narrows the replay-safety classification: `AddNodeIfAbsent` is not categorically idempotent with respect to changed computed attrs. A value-dependent dedup key turns the new value into a new identity and leaves the old node in place. A stable dedup key plus an explicit idempotent update effect can refresh the existing node in this case. The latter is not a general update contract: missing identities, collisions, multiple candidate nodes, rule-order interactions, effect failures, and multi-binding cases remain unmeasured.

This is an exploratory two-case diagnostic, not a confirmatory estimate or runtime-trace result. It does not establish that general full replay is safe, that `AddNodeIfAbsent` outputs are truth-maintained, or that frame locality holds. The earlier 46-case [`effect-only replay safety report`](SUBSTRATE_EFFECT_ONLY_ATTR_REPLAY_SAFETY_RESULTS.md) remains the broader selected-mechanism evidence and documents why fresh `AddNode` is unsafe under unconditional replay.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_add_node_if_absent_replay_probe_v1.py
```
