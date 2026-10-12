# Omniglot contrastive-verdict current-source replay v1 preregistration

**Date:** 2026-09-28  
**Question:** Does the current checked-out implementation reproduce the completed historical run-37A global baseline and its paired top-two contrastive result on the same frozen 400-episode Omniglot panel?  
**Scope:** current-source replication of the historical host-side contrastive classifier; not an evaluation of the generated experiment-judge rule.

## Fixed benchmark

Use the existing run-37A protocol and `scripts/jabberwock_omniglot_run37a_contrastive.py`, which stages each query and candidate set once and scores both the unchanged global SC+TPS parse-marginal verdict and the top-two contrastive verdict against the same character label. The schedule is 10 named alphabets × 2 blocks × 20 queries (n=400), using the original fixed `POWER_SEED`, way, episodes, target rank, and sorted alphabet selection. The first guard block must exactly reproduce the current run-26 baseline predictions and the helper's top-two/global consistency check; otherwise stop before the full panel. The preregistered stop condition remains `broken >= fixed`: report harm/wash without tuning the contrast formula.

## Source and input lock

Before the guard, record a content hash for every Python source under `domains/` and `scripts/`, all Rust source and Cargo manifests under `runners/dsl/src`, Python facade sources and the native extension/build manifest, the complete `data/omniglot/` tree, `seeds/stroke_shapes.json`, and `results/run26_checkpoints/eval_baseline.json`. Also record the Git HEAD, Python/platform, NumPy/SciPy versions, and native extension build identity. Compare the full lock before and after every invocation and again at completion. Run with a new isolated checkpoint directory; never reuse or modify historical run-37A or run-26 checkpoints.

## Outcomes and analysis

Capture all 400 paired predictions. Independently calculate global and contrastive accuracy with Wilson 95% intervals, paired fixed/broken counts and exact two-sided McNemar p-value, per-alphabet counts, true-rank ceiling, and contrastive decision counts. The full-run global arm must equal the independent current baseline on all 400 exact episode keys and match the historical 322/400 result before any contrastive claim is accepted. Report source-lock equality and all preregistered stop gates.

## Integrity, resume, and failure handling

Use `PYTHONPATH=.:runners/dsl/python /usr/bin/python3 scripts/substrate_omniglot_contrastive_current_v1.py --lock` before evaluation, followed by `PYTHONPATH=.:runners/dsl/python /usr/bin/python3 scripts/substrate_omniglot_contrastive_current_v1.py` for each invocation. Use the runner's block checkpoints only under the new capture directory. A partial evaluation may resume only if the entire source/input lock remains byte-identical. Any lock drift censors the partial run; preserve it and do not pool its outcomes. The final raw capture is written only when all 20 blocks complete under a stable lock. The independent analyzer must recompute the result without calling the benchmark's reporting function.

## Claim boundary

This measures a selected 20-way Omniglot one-shot task. It estimates neither natural image-task prevalence nor general perception. Even a successful replay does not support a general tractability claim; it supplies a source-current capability datapoint and a paired cost/quality comparison for this workload.
