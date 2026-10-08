# Accepted string-program bounded exhaustive audit v1 results

Date: 2026-10-03

## Results

The source-locked audit scored all 12 accepted task-arm artifacts over complete finite domains: 10 casefold-count artifacts across 3,906 strings each, and 2 split-then-reverse-token artifacts across 1,365 strings each. This is 41,790 native ProgEval calls. The independent formulas matched the fixture task definitions; all evaluations halted without traps.

| Task family | Accepted artifacts | Domain size each | Exact on full domain | Mean row accuracy |
|---|---:|---:|---:|---:|
| Casefold then count | 10 | 3,906 | 0/10 | 28.1% |
| Split then reverse tokens | 2 | 1,365 | 2/2 | 100% |
| Overall, artifact-weighted | 12 | varies | 2/12 | 32.8% |

The two exact artifacts are both from the 500k escalation arm. Artifacts in the other arms repeat candidates for the same tasks, so the 12 rows do not represent 12 independent programs. All ten casefold-count artifacts fail at least one input in the finite domain; individual casefold accuracies range from 0% to 46.9%.

## Interpretation

This closes the finite-domain semantic question for the observed accepted programs: the two token-list programs are extensionally correct across their tested small domains, while the accepted casefold-count programs are not. The result also shows why a small number of random holdouts can mislead: a program with 47/50 stress accuracy still failed over half of its exhaustive casefold domain. The exhaustive alphabets and length bound were chosen to cover relevant case distinctions, separators, irrelevant symbols, and empty strings, but this is not proof over arbitrary Unicode strings or unbounded lengths.

This is not a measurement of candidate-generation coverage or a general estimate of P4. The enumerator still exposes aggregate counts and the returned candidate only; rejected-candidate stream attribution remains an engine instrumentation gap.

## Artifacts

- [Preregistration](STRING_COMPOSITION_BOUNDED_EXHAUSTIVE_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/audit_accepted_string_programs_bounded_v1.py)
- [Source lock](../../../evaluation/substrate_capability/accepted_string_bounded_v1_lock_20261003.json) and [capture](../../../evaluation/reports/accepted_string_bounded_v1_20261003.json)
- [Stress generalization results](STRING_COMPOSITION_ACCEPTED_PROGRAM_STRESS_V1_RESULTS_20261003.md)
