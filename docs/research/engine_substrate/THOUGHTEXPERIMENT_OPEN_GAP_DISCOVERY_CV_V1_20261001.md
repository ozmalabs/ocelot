# Thoughtexperiment computer-vision open-gap discovery v1

**Purpose:** produce a reproducible exploratory candidate list for a later, separately preregistered utility experiment. This scan does not test utility, novelty, or learning improvement.

## Frozen discovery procedure

- Start a fresh `WorldAdapter` and load the complete seed corpus.
- Select every held postulate returned by `harvest_postulates(..., mt_name="computer_vision")`.
- Compute the live covered-keyword set once and resolve the exact default harvested shape library once. Pass both unchanged to each postulate evaluation while the substrate graph remains fixed.
- Call `synthesize_gaps` for each selected postulate with `max_order=1`, `prune=True`, and `record=False`.
- Capture every postulate and all retained gap payloads. Fingerprint the runner, protocol, relevant implementation sources, native extension, and all seed JSON files before and after the run.

The precomputed `covered_keywords` argument is valid only while the underlying substrate and implementation surface used to construct it remain unchanged. Ordinary synthesis callers omit it and keep the safe recompute behavior. Sharing it here avoids repeating a whole-corpus coverage scan for every postulate; it does not change selector semantics.

## Interpretation limits

This is one full-boot discovery run on one host. Candidate selection is exploratory and is therefore not confirmatory evidence. A retained gap means only that the current selector did not match its capability keys to its implementation/coverage index. Before any capability-gain claim, independently audit the source surface for semantic equivalents, nominate a task with a frozen external outcome oracle, and preregister a fresh derivation/utility panel. A manually supplied implementation can test the task oracle but cannot be credited as substrate learning.

## Result

See [raw capture](../../../evaluation/reports/thoughtexperiment_open_gap_discovery_cv_v1_raw_20261001.json) and the corresponding overall measurement plan entry.
