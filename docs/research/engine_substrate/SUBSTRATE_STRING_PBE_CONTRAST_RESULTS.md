# String PBE contrast benchmark results (2026-09-25)

## Result

The locked 18-task synthetic contrast suite compared the normal P4 route (`main`), retrieval bypass (`no_retrieval`), retrieval bypass with an explicit 500,000 candidate ceiling (`no_retrieval_escalated`), and an independent normal-route replay (`main_replay`). Each arm used fresh substrate state per task. The independent audit checked all 126 fixture input/output pairs.

| Arm | Exact held-out pass | Accepted, held-out failure | Gap |
|---|---:|---:|---:|
| Main | 5/18 | 6/18 | 7/18 |
| No retrieval | 5/18 | 6/18 | 7/18 |
| No retrieval, 500k ceiling | 5/18 | 6/18 | 7/18 |
| Main replay | 5/18 | 6/18 | 7/18 |

The main outcomes reproduce exactly in the replay. The independent audit found no fixture errors and no replay outcome mismatches. `replace_first` and `reverse_split` were accepted from revealed examples but failed all their discriminating holdouts in every arm. `reverse_string` passed all three tasks. `fold_suffix` passed two and gapped on one. `replace_all` and `fold_replace` gapped on all six tasks.

The retrieval bypass was effective: it forced all 18 tasks into enumeration. Default enumeration tested 1,974,447 candidates in aggregate; the escalated arm tested 4,074,447. The regular route enumerated 7 tasks per run and tested 1,400,000 candidates. Enumeration found held-out-valid programs for the reverse-string and two fold-suffix tasks, but did not change aggregate outcomes: retrieval already handled reverse-string and suffix-fold successes in the main arm, while the no-retrieval arm independently found equivalent task-level outcomes. The escalated ceiling did not improve any outcome. Its additional search cost therefore bought no measured capability on this suite.

Aggregate route time was 3.40 s main, 1.76 s no-retrieval, and 4.01 s escalated; boot time was about 0.48–0.50 s per arm. These are small local synthetic-run measurements, not scaling estimates. All arms had 11 acceptances, including six false accepts under the held-out criterion. The benchmark exposes a validation/generalisation gap as well as search gaps.

## Interpretation and limits

This experiment rejects the narrow claim that the earlier string-transfer successes depended exclusively on exemplar retrieval: bounded enumeration can recover some supported string transformations after retrieval is bypassed. It does not show a benefit from the 500k escalation, nor broad string induction. Main and replay are deterministic on these tasks. The deliberately adversarial strata show that training-example acceptance is not a reliable substitute for held-out validation.

The suite is generated, small, and restricted to supported operators. Retrieval was bypassed at the pending-goal route while the exemplar store remained present; the arm did not remove or ablate the store itself. The 500k ceiling is per goal and does not imply that every task consumed the full allowance. No natural-task prevalence, learned-frame locality, rung-three dimension induction, minting/adoption, or general capability is established. Continue with fresh task families and measure false acceptance, candidate economics, transfer, and acquisition cost.

## Reproduction artifacts

- Preregistration: [`SUBSTRATE_STRING_PBE_CONTRAST_PREREG_20260925.md`](SUBSTRATE_STRING_PBE_CONTRAST_PREREG_20260925.md)
- Raw run: [`substrate_string_pbe_contrast_20260925.json`](../../../evaluation/reports/substrate_string_pbe_contrast_20260925.json)
- Independent output audit: [`substrate_string_pbe_contrast_analysis_20260925.json`](../../../evaluation/reports/substrate_string_pbe_contrast_analysis_20260925.json)
- Lock: [`string_pbe_contrast_lock_20260925.json`](../../../evaluation/substrate_capability/string_pbe_contrast_lock_20260925.json)
