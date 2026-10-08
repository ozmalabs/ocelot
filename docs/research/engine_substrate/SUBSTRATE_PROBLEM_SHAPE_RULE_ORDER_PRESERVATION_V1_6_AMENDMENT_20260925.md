# Amendment V1.6: normalize seed-index cache state

Date: 2026-09-25

V1.5 stopped at its first pair because a cold seed-index cache and a warm cache produce different seed traversal orders. A locked cold/warm probe confirmed the difference on byte-identical seed files: the five ProblemShape seed rule slots shifted from indices 1826–1830 to 1831–1835. The loader traverses seed-index dictionary insertion order, while cache JSON is written with sorted object keys.

Before any V1.6 treatment worker, the runner deletes only the derived index-cache files keyed to its two unique immutable snapshots, rebuilds both caches, and records their hashes. Every worker must use those warm caches; the cache bytes and immutable seed snapshot bytes are checked immediately before and after execution. The source lock now includes `substrate/boot_all.py`, `substrate/world_adapter.py`, and `substrate/seed_loader.py` in addition to both workers and the task/domain sources.

The three arms remain baseline, appended replacements, and original-slot replacements. Six randomized triads per workload mix use all arm permutations once. The exact seed-load and active-rule-order expectations are gated before interpreting per-rule counters. V1.6 is exploratory evidence for two authored N=32 workloads and does not establish substrate-wide tractability or natural frame locality.
