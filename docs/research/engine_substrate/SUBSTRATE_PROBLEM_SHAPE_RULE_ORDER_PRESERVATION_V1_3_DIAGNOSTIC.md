# ProblemShape rule-order preservation V1.3 diagnostic

Date: 2026-09-25  
Status: invalidated diagnostic checkpoint; no treatment conclusion

## What was attempted

V1.3 compared the ordinary ProblemShape eventization worker with a candidate whose five transformed rules were installed in their seed positions. It recorded active-rule fingerprints after seed load, before the observation stream, and at worker exit. The intended validity gates were semantic parity and matching rule order before observations; final rule order was retained as an outcome.

The first pair passed the observation-status and mint-count parity checks, but the pre-observation active-rule fingerprints differed. The baseline reported the five target rules at indices 1830–1834; the candidate reported indices 1825–1829. The pair and full per-rule counters are retained in [`V1.3 partial checkpoint`](../../../evaluation/reports/substrate_problem_shape_rule_order_preservation_v1_3_partial_20260925.json). V1/V1.1/V1.2 checkpoints remain separate and incomplete.

## Why this pair is not evidence

Two reproducibility defects were found during diagnosis:

1. The seed corpus changed while this experiment was being set up. Its digest changed from `46cc98e0…` to `f1b4a65f…`, with `communication_causal_retrieval.json` changing. The transformed corpus used symlinks to live seed files, so a corpus lock checked only once at startup did not freeze the data used by each worker.
2. A standalone boot diagnostic on the earlier transformed directory produced matching baseline and candidate fingerprints, while the preregistered worker invocation reproduced a mismatch. A later exact candidate-worker call against that earlier path again matched the baseline seed-load fingerprint. This inconsistency has not been explained; it prevents attributing the pair’s five-slot shift to the treatment.

The mismatch should therefore be treated as a harness/provenance failure, not as a runtime rule-order effect. The checkpoint is preserved and must not be pooled with the global attribution experiment.

## Required repair before another comparison

- Build a content-addressed, immutable copy of every seed file for both arms; do not use symlinks.
- Make the baseline worker accept that same frozen `seed_dir`, so the two arms load byte-identical corpora.
- Check the frozen manifest digest immediately before and after every worker. Record ordered seed names, loaded/failed IDs, and active rule names at each stage so an index delta can be explained directly.
- First run one baseline/candidate diagnostic pair and reconcile every differing rule name before scheduling repeated pairs. Only then freeze a new preregistration and lock.

The V1.3 worker and corpus locks are retained as provenance for the failed diagnostic. They do not certify the partial result as valid experimental evidence.
