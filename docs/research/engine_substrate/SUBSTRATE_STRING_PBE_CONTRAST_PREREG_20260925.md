# Contrastive string PBE confirmatory pilot preregistration

**Status:** lock inputs before running the benchmark. This is a small confirmatory pilot for one generated workload family; it does not estimate natural task prevalence.

## Question

Do P4's held-out string successes depend on the shared exemplar-retrieval ladder, and does a declared increase in enumerator candidates recover any retrieval-disabled gaps? Can the retrieval ladder be made to accept a near exemplar that fits revealed examples but fails deliberately discriminating held-out examples?

## Frozen suite

Eighteen deterministic tasks form six strata, with three task variants/stratum and four revealed plus three held-out examples/task:

- `replace_first`: adversarial retrieval pair; all revealed inputs contain one target character, while each holdout contains it at least twice, distinguishing first-only replacement from the held exemplar's replace-all operation.
- `reverse_split`: adversarial retrieval pair; revealed inputs split into two identical tokens, while heldouts contain distinct tokens in non-palindromic order, distinguishing reversed parts from ordinary split.
- `replace_all` and `reverse_string`: supported-operation controls with discriminating revealed/held-out examples.
- `fold_suffix` and `fold_replace`: two-operation composition strata.

The generator is `tests/fixtures/substrate_string_pbe_contrast/build_tasks.py`; the frozen fixture is `tests/fixtures/substrate_string_pbe_contrast/tasks.json`.

## Arms

1. **Main:** standard P4 retrieval → codebook/descent/exact/enumeration route; default native candidate policy.
2. **No retrieval:** after native rules mint a goal at `retrieve_pending`, the harness records an ablation fact, routes that goal to `pending`, and runs the unchanged downstream P4 pump. It bypasses only the exemplar-retrieval ladder; the held exemplar store remains installed but is not consulted for this goal.
3. **No retrieval + escalation:** the same bypass, with `ps_enum_candidate_budget=500000` for that goal. The enumerator reads this explicit ceiling; no ordinary request receives the override. All other budgets/rules are unchanged.
4. **Main replay:** independent fresh-substrate rerun of main for deterministic route/read-back checks.

Arm order is balanced by task ordinal: even tasks main/no-retrieval/escalated/replay; odd tasks no-retrieval/main/replay/escalated. Each arm uses a fresh substrate per task.

## Outcomes and analysis

Primary outcome: exact correctness on all three held-out rows under the existing P4 scorer. Report accepted-but-wrong, gaps, route/construction, retrieval selections, enumerator candidate counts and requested ceilings, boot/route time, whole-run time and peak RSS. The main-vs-no-retrieval pass-rate difference is paired by task; report a family-stratified bootstrap interval but do not interpret a null result as equivalence. Separately report no-retrieval escalation gain over default. Require exact task-by-task main replay fingerprints and an independent recomputation of all 126 fixture outputs. Preserve every miss and false accept.

## Claim boundary

All operators are within the current string DSL, except that the first-only transformation may not be representable within the current bounded grammar. The two adversarial strata intentionally include revealed examples that are nondiscriminating between a near retrieval and the true function; these are a declared false-accept challenge, not representative sampling. Results do not establish natural distribution rates, open-ended induction, general string understanding, or transfer beyond this task family. No task, split, operation, scoring rule, arm, or candidate ceiling will be changed after locking. Any such change requires a separate amended benchmark.
