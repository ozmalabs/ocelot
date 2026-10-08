# Thoughtexperiment mixed-receipt oracle v1 — results

**Date:** 2026-10-01  
**Status:** source-locked mechanism probe; all 50 positive and 50 conflict trials pass.

Five fresh workers each execute ten seeded trials on independent 64-node sparse directed graphs. Each positive receipt contains six operation kinds: node attribute change, node addition, edge addition targeting the new node, edge attribute change (including key replacement), edge removal, and node removal with incident-edge cascade. Every explicitly approved batch commits, and its complete semantic node/edge projection exactly equals an independently applied Python full-graph delta oracle after mapping the added-node identity from the write receipt.

For each seed, a paired conflict arm regrounds the same receipt shape, changes the target edge after reground, then calls commit. All 50 conflict arms are rejected as stale before writeback; the concurrent edge mutation is preserved and no intended node/edge operation is applied. Five worker PIDs are distinct, all six operation kinds appear in every positive receipt, and all source/binary hashes match the capture.

The probe constructs `ImaginedConclusion` records directly rather than generating these mixed outcomes through learned/native imagination rules. Its graphs and attribute edits are synthetic and small. It verifies the authorization/writeback mechanism and transaction/oracle parity, not proposal quality, large-graph adoption throughput, arbitrary effect semantics, production hook parity, or natural-task frequency. Next combine this oracle with generated residuals from multiple rule families, vary graph size/degree and receipts, then evaluate naturally produced proposals on held-out tasks.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_MIXED_RECEIPT_ORACLE_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_mixed_receipt_oracle_v1.py)
- [Raw five-worker capture](../../../evaluation/reports/thoughtexperiment_mixed_receipt_oracle_v1.json)
