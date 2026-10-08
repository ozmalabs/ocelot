# LLM transport anonymous-separator solver v1.2 results

The source-locked capture and independent analyzer pass all gates across 60 anonymized cells. Every graph-only proposal independently reproduces the two minimum 8-variable separators in the connected K₈,₈ graph. Each candidate is solved and directly rescored from saved anonymous unary/pair factors; all candidate energies and target signs match monolithic JT exactly. Learned accuracy is 0.800 and shuffled accuracy 0.413.

The generic solver's precomputed-factor implementation improves candidate-solving time from the v1 pilot's median 1,220 ms for both candidates to 440 ms. However, the per-cell route still searches the graph anew and solves both candidates: median proposal time is 299 ms and proposal-plus-solve is 738 ms, against 539 ms for monolithic JT. Thus this direct, unamortized, all-candidate generic route is 1.37× slower than JT on this case. It establishes that anonymous graph-only proposals can feed exact generic inference, while exposing a real cost gap in exhaustive search and redundant solving.

Each minimum separator is independently sufficient for exact conditioning; there is no need to solve every candidate to compare utility. The next preregistered iteration should solve one deterministic valid candidate and cache it only while a graph-only topology signature is identical. This measures the practical benefit of reusing structure without exposing layer roles. The result remains confined to one fixed authored K₈,₈ model-derived topology and cannot establish natural cut prevalence or general frame learning.

## Reproducibility artifacts

- [Base protocol](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_PREREG_20261002.md), [factor-precompute amendment](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_1_AMENDMENT_20261002.md), and [component-set correction](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_2_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_anonymous_separator_solver_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1_2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/llm_transport_anonymous_separator_solver_v1_2_20261002.json)
- [Analysis](../../../evaluation/reports/llm_transport_anonymous_separator_solver_v1_2_analysis_20261002.json)
- [v1 diagnostic](../../../evaluation/reports/llm_transport_anonymous_separator_solver_v1_20261002.json) and [v1.1 failed adapter attempt](../../../evaluation/reports/llm_transport_anonymous_separator_solver_v1_1_20261002.json)
