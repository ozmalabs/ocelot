# Code-composition safety and refusal panel v1 results

Date: 2026-09-28  
Status: complete; all 10 independent analysis gates pass.

## Outcome

Two fresh workers each completed the preregistered 12-check schedule. Both returned the two supported positive cases exactly (`True`/`True`) and raised `EmitError` on all ten out-of-fragment cases: duplicate and dynamic globals, wildcard-import scope, recursive helper, depth overflow, keyword helper call, effectful helper, and bool/string/out-of-i64 bitwise operands. No wrong output or alternate exception occurred. The file-write sentinel remained absent in both workers, and predictions matched case by case.

| Measure | Worker 0 | Worker 1 |
|---|---:|---:|
| Schedule | 12/12 complete | 12/12 complete |
| Supported positives exact | 2/2 | 2/2 |
| Typed `EmitError` refusals | 10/10 | 10/10 |
| Wrong returns / other exceptions | 0 / 0 | 0 / 0 |
| Effect sentinel created | No | No |
| Boot | 731/742; 11 failures | 731/742; 11 failures |
| Boot wall time | 12.64 s | 12.63 s |
| Peak RSS | 1.803 GB | 1.803 GB |
| Call median / p95 wall | 3.20 / 36.36 ms | 3.14 / 31.48 ms |

The recursive-helper refusal is the latency outlier (about 32–35 ms). Full boot dominates end-to-end process cost and is not included in per-call summaries.

## Integrity and rerun history

The final execution passed the parent lock, both worker locks, complete schedules, worker return codes, exact parity, and shared console-capture checks. Independent analysis rechecked the frozen frame, expected result class/value for every case, absence of the sentinel, and raw run integrity. Two earlier attempts completed schedules but failed the preregistered source-stability gate: first a seed changed, then `domains/comprehend_text.py` changed between parent lock and worker start. Both were excluded; their changes and hashes are documented in the [amendment](SUBSTRATE_CODE_COMPOSITION_REFUSAL_PANEL_V1_AMENDMENT_20260928.md). The final run uses the new stable source snapshot.

- Raw report SHA-256: `dfc8e372cffa6c660233d3b8a49ce83bd7a4a767a4b44bdfec5a30783856665e`
- Independent analysis SHA-256: `c6401c5d0fed30606d6c6a27620ae35e91704a9803b107c59836f016ab883a62`
- Source lock SHA-256: `8989739639c763c0a906ae3cbfdf7978b4dec71123ce45ba938473b10d7e7d95`
- Frozen case frame SHA-256: `ac7d322187ca24885efeeeafa3bc55e6c787ac50e7b68677af1eff35cc9b660f`

## Claim boundary

This supports the bounded emitter’s refusal behavior on the named module-binding, helper-expansion, and bitwise-domain cases, plus non-execution of one authored file-write helper through this prediction path. It is not a general proof that arbitrary source or native tools are contained, nor does it establish Python transfer accuracy. The next code gate is a construction family selected without inspecting function bodies, with held-out scoring and coverage/conditional accuracy/wrong-return rate separated.

## Artifacts

- [Preregistration](SUBSTRATE_CODE_COMPOSITION_REFUSAL_PANEL_V1_PREREG_20260928.md)
- [Amendment](SUBSTRATE_CODE_COMPOSITION_REFUSAL_PANEL_V1_AMENDMENT_20260928.md)
- [Runner](../../../scripts/substrate_code_composition_refusal_panel_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_code_composition_refusal_panel_v1.py)
- [Frozen case frame](../../../evaluation/substrate_capability/code_composition_refusal_panel_v1_frame_20260928.json)
- [Raw report](../../../evaluation/reports/code_composition_refusal_panel_v1_20260928.json)
- [Analysis report](../../../evaluation/reports/code_composition_refusal_panel_v1_analysis_20260928.json)
- [Source lock](../../../evaluation/substrate_capability/code_composition_refusal_panel_v1_lock_20260928.json)
