# Live self-report route regression v1 (locked source snapshot)

Date: 2026-09-27

## Result

On the source snapshot locked by this probe (`boot_all.py` SHA `0e2139b24c23603df15a48995dd696c6b69a4592c706f62ad26907ff6f9ec5f7`), the previously successful full-seed request `report your organisation` does not reach the self-report faculty. Three fresh processes reproduce the same outcome, and the independent analyzer passes all 6 integrity/behavior gates. Each run loads 731 seed manifests, records the same 11 seed failures, and ends with the same 24,976-node/11,428-edge graph digest. The inbound Message has no communication route, no comprehending Goal, and returns:

> I understood that as an instruction to report 'organisation', but I hold no faculty for it yet -- I've filed it as a gap to work on.

This is a current capability regression relative to the source-locked v1.1 self-report scale result, where the same request reached `self_report` and resolved its Goal. The old scale result remains valid for its captured source; it does not describe the current tree.

## Proximal interpretation evidence

A separate read-only probe of the same source snapshot captured the selected comprehension record. The inbound Message is marked as an instruction with predicate `report`, but the comprehender returns a statement interpretation whose dispatch path is `wordplay`, with intent `wordplay:organisation`. Native instruction outcome is `unhandled`; the Python action faculty does not receive the self-organisation target. This is direct evidence that the current route-selection path fails before reflective self-report execution. It does not identify which source edit caused the change or prove a single root cause.

The full boot also consistently reports these 11 seed failures:

- `acoustic_cue_vocab`, `character_tom`, `reading_constructions`, `conceptual_categories`, `cue_investigator`, `named_compound_heads`, `reading_skeleton`, and `vision_change`: `ValueError: seed node missing local_id`.
- `qwen3_reaped_isa_full`, `qwen3_reaped_knowledge`, and `qwen3_reaped_knowledge_scaled`: `ValueError: seed ref must be an object`.

Conversation/discourse seeds including `conversation_self_reply` load successfully. The failures are therefore a boot-integrity issue that co-occurs with the route shortfall; this measurement does not establish that those particular failed seeds caused the self-report route loss.

## Interpretation

This is one instruction family on that locked full boot, not a rate estimate for conversation generally. The source was copied into an isolated snapshot before the three confirmatory workers, preventing concurrent worktree edits from changing their inputs. The exact source lock and runner/protocol hashes are preserved. Subsequent source snapshots produce different route behavior; this result must not be generalized to the later or live worktree. The earlier frame-cost measurements remain evidence for their own captured source only.

Next compare the current wordplay/self-report arbitration against the previously successful source and isolate the smallest source change that altered the selected interpretation. Separately repair and gate all 11 malformed seed manifests before making full-seed performance claims. Re-run the route panel after any repair; do not attribute causality to the boot failures without an intervention.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_SELF_REPORT_ROUTE_REGRESSION_V1_PREREG_20260927.md)
- [Probe runner](../../../scripts/probe_live_self_report_route_regression_v1.py)
- [Independent analyzer](../../../scripts/analyze_live_self_report_route_regression_v1.py)
- [Single-worker comprehension diagnostic runner](../../../scripts/diagnose_live_self_report_route_regression_v1.py)
- [Source lock](../../../evaluation/substrate_capability/live_self_report_route_regression_v1_lock_20260927.json)
- [Three-worker report and raw records](../../../evaluation/reports/live_self_report_route_regression_v1_20260927.json)
- [Analysis](../../../evaluation/reports/live_self_report_route_regression_v1_analysis_20260927.json)
- [Comprehension diagnostic](../../../evaluation/reports/live_self_report_route_regression_v1_comprehension_diagnostic_20260927.json)
- [Prior successful source-state scale result](SUBSTRATE_LIVE_SELF_REPORT_LIVE_SCALE_V1_RESULTS_20260927.md)
