# Cognition Linear P26 results — matched evidence selection v1

**Status:** complete, structurally valid negative efficacy result. The frozen heldout draw was executed once; it was not rescored or redrawn.

## Registered question and outcome

The preregistered primary compared residual-directed selection with the stronger of fixed and random selection on pooled paired-stream learning-curve AUC. The threshold was a gain of 0.10, with a positive 99% interval lower bound and both confirmatory contrasts meeting the registered Holm-adjusted test threshold.

| Arm | Mean AUC |
|---|---:|
| Residual | 0.008750 |
| Fixed | 0.002969 |
| Random | 0.024844 |

Against the stronger control (random), residual selection had mean gain **−0.016094**, 99% paired-bootstrap CI **[−0.025626, −0.007500]** (20,000 resamples; seed 26010271). Residual minus fixed was +0.005781 (99% CI [0.001563, 0.011250], Holm-adjusted one-sided p=0.000700); residual minus random was −0.016094 (99% CI [−0.025157, −0.007499], adjusted p=1.000000). The registered gate **failed**. This is evidence against a residual-selection advantage on this allocation, not evidence of no possible advantage on other tasks.

## Allocation, completeness, and stratified outcomes

The run retained all **800 paired streams** (200 in each family × load cell), **2,400 selector-arm rows**, **800 native-search comparator rows**, and **300 integrity controls**. The analyzer reported `VALID`, with zero structural failures; runtime attestation was `ATTESTED`. Missing heldout predictions were scored as failures and retained. There were no ceiling outcomes; floor rates were high.

| Family | Load | Residual AUC | Fixed AUC | Random AUC | Floor rate R/F/Rand | Missing predictions R/F/Rand |
|---|---|---:|---:|---:|---|---|
| Branching | High | 0.006250 | 0.001875 | 0.020625 | .975 / .985 / .935 | 771 / 777 / 741 |
| Branching | Low | 0.010000 | 0.001875 | 0.017500 | .970 / .985 / .945 | 766 / 778 / 751 |
| Cyclic | High | 0.013125 | 0.002500 | 0.021875 | .950 / .980 / .930 | 754 / 772 / 742 |
| Cyclic | Low | 0.005625 | 0.005625 | 0.039375 | .975 / .975 / .895 | 764 / 764 / 713 |

Each cell contains 200 paired streams. No stratum meets the preregistered pooled efficacy gate; the strata are descriptive and do not replace the primary. Performance is near floor in every arm, limiting interpretation of small absolute differences.

## Search comparator, controls, and resource accounting

Across the 800 native-search rows, the runner retained **25,600 attempts**: 22,737 residual and 2,863 verified. It logged 981 candidate proposals, all 981 unapproved; there were zero unique verified effects, adoption approvals, world receipts, or unseen-binding use. The comparator therefore establishes neither useful search nor capability improvement. Attempts/candidates remain proposals and did not execute in heldout worlds.

Per-cell native search accounting (attempts; proposals; maximum serialized graph bytes; maximum native-rule steps; unspent budget):

| Family | Load | Attempts | Proposals | Max graph bytes | Max rule steps | Unspent budget |
|---|---|---:|---:|---:|---:|---:|
| Branching | High | 6,400 | 174 | 734,453 | 11 | 3,200 |
| Branching | Low | 3,200 | 95 | 702,781 | 5 | 4,800 |
| Cyclic | High | 6,400 | 428 | 733,858 | 11 | 3,200 |
| Cyclic | Low | 3,200 | 284 | 702,880 | 5 | 4,800 |

The 300 controls comprised 100 heldout-selector guards, 100 receipt-replay controls, and 100 approval-boundary controls; all passed as required by the valid analyzer report. All selector arms used the common budget ceiling of 32, at most four decision rounds, and zero source exposure; native search was capped at 32 attempts per stream and four per task. The analyzer checked graph and native-work ceilings. No cost-efficiency claim follows from these score outcomes.

## Provenance and artifacts

- Preregistration-only freeze commit: `14b08988196810ab94311ab887bdd0638c52d4ce`.
- Raw heldout artifact: `evaluation/process_mastery/results/p26_linear_v1_heldout_20261025.json`; SHA-256 `c1abf9fff1f4d3d52f51a367defa1e235b2769fc30490b2c343f582f28fdf7cd`.
- Analyzer output: `evaluation/process_mastery/results/p26_linear_v1_heldout_20261025_analysis.json`; SHA-256 `a28c51d11300118bb43dc64aced08506bd6552d82bebd2e5209702255be234fb`.
- Runner SHA-256 `23308432d1a7598ae82119bd3b21074efb499a6dca38cd574dc719a758b35da0`; analyzer SHA-256 `a66cdb81f785470cfe0ac96b0a50cb4f3b79355b36e2a853bd95afad179a526d`.
- Frozen source bundle SHA-256 `fe0695783f9a5b8e9d2d48477fac8c129ed379cfd8b17e118c9125c72283fa89`; loaded extension SHA-256 `5b8c1b5d35e38d0c574b32f2089cc92b79ed9916c281e4670887f6542931ac07`; build receipt SHA-256 `661f708a7709a544d6606f3cab00a3540fa930c019849c25c84aebcf7047ad66`.

## Interpretation and next phase

P26 closes its evaluation/reporting cycle and validates the bounded integration, allocation, and accounting paths. It does **not** demonstrate a selection advantage, productive native search, or general process synthesis. P25 retention remains a narrow simulator-specific result; its unseen-task scores were at floor. P27 may proceed as a separately frozen scheduled-checkpoint evaluation using only demonstrated interfaces, but it must include no-change and failed-search intervals and cannot assume P26 efficacy. P22 remains a draft and its old allocation is not rescored. Capability levels are unchanged.
