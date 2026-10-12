# Offline GenMint candidate efficacy with reusable CoW snapshot v1.1 results

Date: 2026-10-01

## Result

All **30 source-locked workers** completed without errors; the independent analyzer passes **15/15 gates**. The existing efficacy outcomes replicate: 25/30 workers acquire the intended authored linear generator; acquired candidates route to it and predict exactly on 400/400 held-out positive cases, while frozen and equal-exposure/no-consolidation controls score 0/480. Negative tasks produce no false acceptance and no new linear generator mint; nonlinear novelty signals remain unadjudicated.

The new application path captures a reusable immutable shared-graph-pages snapshot after GenMint candidate acquisition, then evaluates a child through `snapshot.fork()`. Across all 30 workers, reusable-fork positive and negative semantic outputs match both direct shared-page and eager-copy controls; the snapshot's backend/revision identity is valid, the source digest is unchanged after evaluation, and existing primary/candidate isolation gates pass. Median reusable branch fork time is 0.294 ms (direct shared pages 0.365 ms; eager 0.641 ms). Median whole branch-validation time is 183.6 ms for reusable snapshots, 181.7 ms direct shared pages, and 176.9 ms eager. The small fork-time difference does not produce an end-to-end speedup in this task family.

## Interpretation and limits

This adds a second application consumer for the reusable snapshot/fork lifecycle: a learned candidate-validation path, in addition to the Thoughtexperiment correction harness. It also confirms use of the same immutable base after candidate-training mutations and later isolated evaluation branches. It is not a solver/planner integration, concurrent lifecycle test, reclamation bound, revision-conflict adoption test, natural-task result, formal P3-E1 result, broad transfer claim, or vLLM/KV-cache integration. The vLLM-style path still requires its own adapter and ownership/cancellation/reclamation workload.

See [preregistration](SUBSTRATE_OFFLINE_CANDIDATE_SNAPSHOT_EFFICACY_V1_1_PREREG_20261001.md), [runner](../../../scripts/genmint_candidate_snapshot_efficacy_v1_1.py), [analyzer](../../../scripts/analyze_genmint_candidate_snapshot_efficacy_v1_1.py), [lock](../../../evaluation/substrate_capability/genmint_candidate_snapshot_efficacy_v1_1_lock_20261001.json), [capture](../../../evaluation/reports/genmint_candidate_snapshot_efficacy_v1_1_20261001.json), and [analysis](../../../evaluation/reports/genmint_candidate_snapshot_efficacy_v1_1_analysis_20261001.json).
