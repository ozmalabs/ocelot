# Area-settlement fixed-seed repeatability v1

Date: 2026-10-06  
Status: preregistered uninstrumented repeatability check.

## Question

Does the original, uninstrumented v1.1 settlement-parity worker become repeatable when every worker starts with the same `PYTHONHASHSEED=0`? This checks whether the earlier graph-fingerprint variation is explained by process hash randomization or persists in the ordinary workload path.

## Design

Run three fresh global-arm workers using the exact v1.1 parity runner, source lock, seeds, teaching sequence, and seven prompts. Set `PYTHONHASHSEED=0` before each interpreter starts. Do not install diagnostic wrappers or modify production behavior. Retain per-turn ID-independent fingerprints, raw hashes, graph counts, replies, and the final compressed graph snapshots returned by the runner.

## Gates

- Three distinct PIDs; all report stable v1.1 source inputs.
- Compare per-turn fingerprints, replies, and counts across workers.
- Compare final retained node/edge records with the ID-independent fingerprint; do not claim exact graph isomorphism from WL equality alone.
- The result only diagnoses this fixed workload and seed. If it passes, a subsequent all-arm fixed-seed scheduling replay is required. If it fails, identify the non-hash source of baseline variation before scheduler attribution.
