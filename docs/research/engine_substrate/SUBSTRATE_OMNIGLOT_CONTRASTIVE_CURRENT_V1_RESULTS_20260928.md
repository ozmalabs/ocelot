# Omniglot contrastive-verdict current-source replay v1 results

**Status:** complete; source/input lock stable; preregistered harm/wash stop triggered.  
**Question:** Does the current checked-out implementation reproduce the run-37A global arm and what is the paired top-two contrastive result on its frozen 400-episode panel?

## Result

The block-0 guard passed: all 20 global predictions matched the locked run-26 baseline and top-two candidate selection agreed with the global winner on all 20 guard episodes. The completed panel contains 400 unique episode records across ten alphabets. An independent key join against the locked run-26 records found exact episode-key coverage and exact equality of every global prediction. The global arm reproduced 322/400 (80.5%, Wilson 95% CI 76.3–84.1%); the contrastive arm returned 256/400 (64.0%, Wilson 95% CI 59.2–68.6%).

Paired outcomes were 16 fixed and 82 broken (98 discordant episodes); the exact two-sided McNemar/binomial p-value is `7.380354309112728e-12`. This triggers the preregistered `broken >= fixed` stop. The contrastive procedure materially degrades this selected task, and no formula tuning or post-hoc rescue is included. The result does not imply that every contrastive method or focused perception operation is harmful.

An explicitly exploratory, post-hoc split finds degradation in both decision strata: the one-sided/unmatched branch scores 146/242 (60.3%) versus 194/242 (80.2%) globally, with 10 fixed and 58 broken; the two-sided/worst-matched branch scores 110/158 (69.6%) versus 128/158 (81.0%), with 6 fixed and 24 broken. The single-stroke subset scores 48/70 (68.6%) versus 59/70 (84.3%), with no fixed and 11 broken. These strata were inspected after the confirmatory outcome and are descriptive only; they do not establish a causal failure mechanism or justify a new threshold. Full counts are in the [independent analysis JSON](../../../evaluation/reports/omniglot_contrastive_current_v1_independent_analysis.json).

## Integrity and provenance

The source lock covers Python under `domains/` and `scripts/`, Rust sources and Cargo manifests, Python facade files, the native extension and build manifest, the complete Omniglot data tree, the stroke-shapes seed, the exact run-26 baseline file, protocol, runner, benchmark, Git HEAD, and runtime identity. The pre-run lock, captured pre/post lock, and a live recomputation after analysis are identical. The isolated run directory preserves `guard.json`, all 20 block checkpoints, `report.json`, and the final raw `capture.json`. The independent analyzer recalculates key parity, predictions, Wilson intervals, discordant counts, and the exact paired p-value without calling the benchmark's `stage_report` function.

The interpreter was `/usr/bin/python3` 3.12.3 with NumPy 1.26.4 and SciPy 1.17.1; `substrate_rs` loaded from this checkout through `PYTHONPATH=.:runners/dsl/python`. The repository `.venv` did not contain SciPy, so it was not used. The native extension hash and build manifest hash are included in the source lock. The historical source commit cited by run-37A comments is unavailable in this imported Git history; this is a source-current replay of the presently checked-out implementation and frozen workload, not recovery of the original historical build environment.

## Claim boundary and next measurement

This is a selected 20-way Omniglot one-shot benchmark of the host-side `domains/contrastive_verdict.py` path. It does not estimate natural-task prevalence, general perception, the generated experiment-judge rule, or substrate-wide tractability. The negative result makes the next useful step a failure-mechanism analysis with a separately locked diagnostic: stratify fixed/broken cases by decision kind, stroke count, true-class global rank, alphabet, and difference-region size; then compare the focused score to independent per-candidate evidence without changing the original confirmatory outcome. Any revised rule needs its own preregistration and held-out task panel.

Artifacts: [preregistration](SUBSTRATE_OMNIGLOT_CONTRASTIVE_CURRENT_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_omniglot_contrastive_current_v1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_omniglot_contrastive_current_v1.py), [source/input lock](../../../evaluation/substrate_capability/omniglot_contrastive_current_v1_lock_20260928.json), [raw capture](../../../evaluation/reports/omniglot_contrastive_current_v1_capture/capture.json), [independent analysis](../../../evaluation/reports/omniglot_contrastive_current_v1_independent_analysis.json).
