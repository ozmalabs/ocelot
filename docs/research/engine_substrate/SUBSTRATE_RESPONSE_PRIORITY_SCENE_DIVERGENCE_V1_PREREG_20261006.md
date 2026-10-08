# Response-priority scene-route divergence diagnostic

Date: 2026-10-06  
Status: preregistered two-worker forensic replay of the deterministic scene-description graph mismatch.

## Question

Which typed records and attributes cause the global and priority scene-description graphs to diverge before continuation, despite equal reply and node/edge counts?

## Design

Replay only the source-linked `scene_description` condition, one fresh global worker followed by one fresh priority worker, under the same full-seed build and four-rule ambient partition as cross-family v1. Preserve host hooks. Capture the complete graph immediately before continuation and after unbounded continuation, along with turn firing-history records, replies, utility oracle result, selected call traces, and source inputs. This is a forensic diagnosis, not a new task-utility or performance estimate. The original cross-family capture remains authoritative for the two-replicate result.

## Analysis

Compare both arms' node and edge records by stable IDs where possible, then compare normalized typed/attribute signatures. Report node/edge type differences, attribute fields and values, firing-history ledger contents, and whether the mismatch exists before continuation. If graph IDs differ, do not treat raw-ID set differences as semantic differences; use normalized references and the stored semantic fingerprint.

## Artifacts

Runner: `scripts/substrate_response_priority_scene_divergence_v1_20261006.py`  
Capture: `evaluation/reports/response_priority_scene_divergence_v1_20261006/capture.json.gz`  
Lock: `evaluation/substrate_capability/response_priority_scene_divergence_v1_20261006_lock.json`
