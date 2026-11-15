# Research helper held-out evaluation preregistration

**Protocol ID:** `research-helper-heldout-v1`
**Status:** draft, not preregistered. The later four-case exploratory run has generated outputs and exposed its keys; those cases are burned and cannot be used for this confirmatory study. No 40-task confirmatory run has started.
**Scope:** compare the research helper with ordinary source access and a generic evidence ledger on source-grounded research questions. This tests answer quality under a controlled task set; it does not test scientific discovery or validate claims in either repository.

## 1. Prior work and separation

The three-case run in `evaluation/research_assistant/pilot_20261114/` was an exploratory feasibility shakedown. Its tasks are burned, its assignment was not randomized, and the prompts, outputs, and keys are available in the shared workspace. `evaluation/research_assistant/fixtures_v1.json` is likewise marked `pilot_only_burned_not_held_out`. None of those cases, prompts, variants, or answer-key facts may enter the confirmatory task set. The pilot's observed grader agreement is too small and selected to estimate reliability or effect size.

The existing harness validates the burned five-task fixture and produces descriptive means only. It does not accept a separate held-out fixture, randomize runs, calculate uncertainty, or perform confirmatory analysis. Before data collection, add an isolated confirmatory entry point that reuses the current score schema and rubric but reads a separately sealed held-out bundle after answer capture. Do not change the pilot fixture or call `harness score` on held-out data: it currently loads the pilot keys by default. The preregistration and the new entry point must be committed before generating any held-out answers. Record the commit IDs and hashes of the runner, helper, prompts, model configuration, source snapshots, and sealed task/key bundle in the study record.

## 2. Design and estimand

Three paired arms use the same model version, source snapshot, prompt, source access, allowed tools, context window, output limit, and per-task time/token budget:

1. **`source_only`:** source files and ordinary notes, without a prescribed claim/evidence ledger.
2. **`generic_ledger`:** the same sources plus a generic claim/evidence ledger with no GE-specific frame fields.
3. **`research_helper`:** the same sources plus the research helper's full frame and claim/evidence workflow.

The primary estimand is the mean within-task difference in the seven-dimension answer-quality score (`research_helper` minus `source_only`) over the frozen task population. The `generic_ledger` comparison is a prespecified secondary contrast that tests whether any difference is specific to the full helper rather than structured evidence tracking in general. Tasks, not rubric items or claims, are the independent units. Each task is run once per arm; all arms for a task share its source package and prompt. This is an evaluation of this model/configuration and task distribution, not a general claim about all models or research domains.

## 3. Tasks and sample size

Create **40 new held-out tasks**, none derived from the burned pilot prompts or their answer keys. Each task must have a question, frozen source package and revisions, key with acceptable answer and required points, explicit counterevidence/limitations where relevant, and a marked distinction between source statements and permissible inference. Use original source material plus clearly labelled synthetic fixtures where a planted contradiction is needed. Never insert synthetic facts into original research records.

Before answer generation, two reviewers who are not operating the arms independently verify each key against the pinned sources; disagreements are resolved and keys frozen before sealing. Cover these eight strata with five tasks each: finite versus universal mathematical claims; counterevidence to broad claims; Ocelot experimental controls or missing controls; stale sources or unavailable artifacts; inapplicable frame fields; GE repository material; Ocelot repository material; and non-GE examples. A task can satisfy multiple coverage labels, but the allocation must still total 40 unique tasks. Include both positive and null/ambiguous cases where the sources support them. Pilot cases and close paraphrases are excluded.

Forty paired tasks yield 40 independent paired differences for the primary contrast (120 generated answers total). A conventional paired-mean approximation gives about 80% power at two-sided 5% alpha for a standardized within-task effect near 0.46 (roughly 0.5); this is a planning approximation, not a pilot-derived effect estimate. The pilot is too small and uncontrolled to justify a more optimistic variance estimate. Forty is a feasible minimum chosen to detect a moderate average effect, not small effects or subgroup effects. If fewer than 40 valid task bundles are frozen, do not begin the confirmatory run; do not replace tasks after seeing arm outputs.

## 4. Run procedure and blinding

Use one locked model snapshot and fixed sampling settings (temperature 0 where supported; otherwise record the fixed seed and all sampling settings). Run each task in all arms in an independently reset workspace with no prior arm transcript, cached answer, hidden key, grader note, or pilot answer. The helper may read only the task prompt and its permitted source package. The sealed key bundle must be stored outside every arm's readable filesystem and tool scope. Log and audit file/tool access. If isolation cannot be demonstrated, do not describe the run as blinded to keys and do not treat it as confirmatory.

Randomize arm order separately within each task using a recorded seed, and randomize task order. Give each arm identical source/tool permissions and resource ceilings. Record exact prompts, source hashes, model/configuration IDs, tool calls, token usage, wall-clock latency, and failures. A run that times out, exceeds a ceiling, or fails source retrieval remains a failed row in that arm's denominator; do not rerun selectively. A documented infrastructure-wide interruption may restart the entire affected task triplet before any scores or keys are exposed, preserving both attempts.

Strip arm-specific metadata and assign random answer IDs before grading. Two independent graders, unaware of arm, score every answer against the frozen key using the rubric below. Preserve their individual scores and rationales. Resolve disagreements only after both score files are locked; the primary score is the mean of the two graders' values for each dimension. Report raw agreement and weighted kappa by dimension as descriptive reliability measures. Graders may reopen pinned source revisions but may not see arm identity, other graders' ratings, or pilot outputs during scoring.

## 5. Outcomes and scoring

Use the existing 0–2 rubric dimensions in `evaluation/research_assistant/README.md`: source claim accuracy, unsupported assertions (2 means none/materially immaterial), contradiction recall, limitation recall, citation reopenability, citation hash match, and completion. The **primary task score** is the unweighted mean of these seven dimensions, each already oriented so higher is better, and therefore ranges from 0 to 2. For a failed or missing run, assign primary score 0 and retain the failure reason; do not exclude it from the primary denominator. Graders score citation dimensions from observable citations and pinned snapshots, not from an arm's internal claims about having checked them.

Prespecified secondary outcomes are each rubric dimension separately, the `research_helper` versus `generic_ledger` primary-score contrast, task completion rate, and operational measures (tokens, latency, and tool cost). Operational measures remain separate from the quality score. Report all outcomes and all failures, regardless of direction.

## 6. Analysis plan and decision rule

For each task, calculate the mean grader primary score in each arm, including zero for failed/missing outputs. Calculate paired differences for the two prespecified contrasts. Report arm means, paired mean differences, 95% paired bootstrap confidence intervals resampling tasks (10,000 resamples, fixed analysis seed), and the full task-level paired data in the released record. Also report the paired median difference and the number of positive, zero, and negative task differences. The primary interval and estimate use all 40 tasks; no outlier removal, post hoc covariate adjustment, or per-claim pseudo-replication. Secondary rubric-dimension contrasts are descriptive with confidence intervals; no multiplicity-adjusted confirmatory claims will be made from them.

The practical improvement threshold is **+0.15 points on the 0–2 primary score** (7.5% of the scale). Call the result evidence of a practically meaningful improvement only if the primary paired 95% interval's lower bound is above 0 and the point estimate is at least +0.15. If the interval includes 0, report the primary result as inconclusive; if its upper bound is below 0, report evidence of degradation. A positive estimate smaller than +0.15 is not a practically meaningful improvement under this protocol. The generic-ledger contrast is secondary and cannot substitute for a failed primary contrast. No change to the helper or scoring rubric may be made after the first held-out answer; any such change requires a new, separately frozen task set and protocol.

## 7. Exclusions, deviations, and release

Exclude a task only before generation if its pinned source is unavailable, its key cannot be independently verified, or it fails the frozen coverage specification. Replace it before unsealing/generation and document the reason. After generation starts, retain all task-arm rows; mark failures and protocol deviations rather than excluding them. Report the planned and actual denominators, all deviations, missing outputs, grader reliability, and source/key/runner hashes. Release prompts, source snapshots where licensing permits, anonymized outputs, both grader sheets, analysis code, and the task-level results after the study is locked. Keep keys sealed until all outputs and grader sheets are locked; then publish them with the record unless a source or privacy constraint prevents it.

## 8. Execution gate

This document is not itself evidence that the held-out bundle or execution path exists. The study may start only after: (a) the 40-task bundle and keys are independently checked and sealed; (b) a confirmatory runner supports that bundle without loading pilot keys; (c) arm isolation, logging, randomization, and the fixed budgets are demonstrated on non-study dummy tasks; and (d) this protocol and all relevant code/configuration hashes are committed. No model outputs or hidden-key reads are authorized by drafting this protocol.
