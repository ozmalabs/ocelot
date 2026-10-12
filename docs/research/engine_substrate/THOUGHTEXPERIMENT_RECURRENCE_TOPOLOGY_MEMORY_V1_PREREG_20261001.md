# Recurrence-ledger repair memory across graph topologies v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does graph adjacency topology change the memory cost of a real recurrence-ledger rule-repair rehearsal when node and edge counts are held constant?

## Design

Reuse the single-guard fault and authored repair from `thoughtexperiment_recurrence_offer_idempotence_v1.py`. Construct 100k- and 200k-node noise graphs with identical node attributes and exactly N−1 `te_noise_next` edges. Compare a path, a star, and a balanced binary tree. Cross topology and size with native eager full-copy and shared-graph-page forks; run three fresh processes per cell (36 processes total), no warmups, and sample Linux `smaps_rollup` every 10 ms during fork, rule replacement, five native closure sweeps, exact task-oracle checks, and branch release.

Topology edge targets: path connects i−1→i; star connects 0→i for i>0; balanced tree connects parent `(i−1)//2`→i for i>0. Each graph has N nodes and N−1 edges, so topology is varied without changing graph cardinality or noise payload.

## Gates

- Six topology/size cells × two backends × three fresh processes complete (36 unique PIDs); locked sources and native binary remain unchanged.
- Every branch restores the authored `where` clause, emits exactly one offer, and reaches zero-progress fixed point.
- The primary graph/rule revision, counts, and rules remain unchanged.
- Backend outcomes match for each topology/size/repeat.
- Report median baseline, sampled peak ΔPSS/RSS/private-dirty, and operation duration; preserve raw per-process rows.

## Interpretation limits

This compares three synthetic equal-edge-count topologies, on one Linux host, for one authored recurrence task. It does not establish natural topology prevalence, concurrent branch scaling, autonomous correction, end-to-end throughput, or unsampled kernel peak memory. The 10 ms sampler may miss short-lived peaks.
