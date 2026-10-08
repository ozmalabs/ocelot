# Thoughtexperiment A8 proposal bridge v1.1 — multi-rule seed loader amendment

**Date:** 2026-10-02  
**Reason:** The v1 source-attribution gate failed before held-out scoring. The frozen order output showed `served_by: python` in all four workers. Runtime tracing found `_ensure_graph_composer_seed` assumes every composer seed contains exactly one Rule; the current `composer_experiment_graph` manifest contains three independent Rules, so the caught loader error causes a silent Python fallback.

The implementation now loads every uniquely named Rule in the requested seed, skipping an already-active same-name rule only when its `match`, `where`, and `effects` match the manifest. Duplicate names and stale conflicting active rules fail closed. This permits multi-rule seeds while preserving source parity and prevents the previous silent mismatch. The v1 capture and its lock remain immutable.

Repeat the same four-worker prompted/unprompted protocol with the same held-out directions, using a new source lock that includes the changed `reflective_faculty.py`, runner, analyzer, all task and seed sources, and native binary. The order-stage scoring gate is explicit: do not run held-out scoring unless all prompted proposals report `served_by: graph`, target-rule preservation passes, and all unprompted proposals abstain through the graph path. If the gate fails, preserve only the order capture and report the failure. If it passes, score every host reference candidate plus the graph proposal under the v1 protocol and keep the source/fault controls and complete cost ledger.

This amendment does not widen A8 beyond chosen-action rules or change the supplied cue. A pass measures one prompted graph-composed proposal bridge, not autonomous diagnosis, general candidate generation, or self-improvement.
