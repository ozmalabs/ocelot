# NaturalProofs reading-path rung-entry panel v1 results

Date: 2026-09-27  
Status: confirmatory entry-incidence panel passed its locked integrity gates.

## Result

Two fresh full-runtime workers processed the same outcome-blind, ID-hash-selected 64 statement bodies in order. Both workers completed all rows, produced replies for all 64, had no task errors, matched schedules, and remained source-stable under the locked runtime. Independent analysis passed all 15 checks, including independent reconstruction of the selected frame and verification of statement hashes.

The primary post-cold-start measure is **0/63 tasks with a new concern receipt in each worker**. Across all 64 tasks, each worker has one receipt, on the first request only. That first request lazily initializes `conceptualizer_live`; it creates one Observation with status `minted` and one graph-native minted-axis edge. Treat this as runtime setup, not induction prompted by a theorem statement. No later Observation-linked mint, transform, or new ShapeSignature was recorded. All tasks returned replies, but answer correctness and proof quality were not assessed.

Each worker added 1,216 nodes of the overloaded `CapabilityAxis` type. Attribute-level accounting separates these into 1,215 `understand_word` lexical frontiers and one first-use axis whose `kind` is missing. The 1,215 lexical frontiers cover 910 distinct token hashes. They are not counted as dimension induction: the only rung mint counted here requires a new Observation's native `minted` edge, corroborated by its `induced` marker.

Runtime envelope per worker: boot 12.68–12.76 s; peak RSS 1.899–1.900 GB; median request wall time 298–304 ms; nearest-rank p95 631–637 ms; median CPU time 467–478 ms. These are full-runtime measurements for this repository state and selected statement stream, not general latency estimates.

## Interpretation and limits

This is evidence that the audited reading route does not enter the reflective dimension-decode/mint path for these 126 post-startup worker-task observations. It is not evidence that mathematical statements generally do not trigger residuals, that the system understands or proves the statements, or that rung 3/4 entry is rare in natural use. The 64 tasks are one title-disjoint NaturalProofs test-shard sample, run with `shadow_read=False`; proofs are not supplied to the runner and no proof-generation evaluation was performed. The runtime indexes all corpus shards, so this is not a clean proof-generation holdout.

The result refines the tractability report's economic hypothesis: this route incurred continuous reading and lexical-frontier work, but no post-startup higher-rung induction in the measured sample. It does not establish an economic advantage or validate cheap-cut/frame locality. The large type-node delta also shows why rung accounting must follow typed graph relations and outcomes rather than count node classes alone.

## Reproduction artifacts

- Frozen protocol: [preregistration](SUBSTRATE_NATURALPROOFS_RUNG_ENTRY_PANEL_V1_PREREG_20260927.md)
- Runner: [panel runner](../../../scripts/substrate_naturalproofs_rung_entry_panel_v1.py)
- Independent analyzer: [analyzer](../../../scripts/analyze_substrate_naturalproofs_rung_entry_panel_v1.py)
- Source lock: [lock](../../../evaluation/substrate_capability/naturalproofs_rung_entry_panel_v1_lock_20260927.json)
- Raw capture: [worker results](../../../evaluation/reports/naturalproofs_rung_entry_panel_v1_20260927.json)
- Analysis: [independent analysis](../../../evaluation/reports/naturalproofs_rung_entry_panel_v1_analysis_20260927.json)
- Outcome-blind frame: [selected frame](../../../evaluation/reports/naturalproofs_rung_stream_frame_v1_20260927.json)

## Next measurement

The direct Think Python code-reading counterpart is now measured separately. The next family gap is visual-text reading with an independent task oracle. Keep the no-proof-access boundary for any theorem input; for every family, report ordinary lexical frontier volume, post-startup concern entry, minted-edge outcomes, transforms, and per-request CPU/RSS. Then perturb controlled frame boundary width and test whether learned partitions improve exact inference. Do not treat this panel's zero-entry estimate as evidence that residual-driven acquisition is rare generally.
