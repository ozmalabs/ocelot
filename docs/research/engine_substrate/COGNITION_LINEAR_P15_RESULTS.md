# P15 frozen evaluation results

**Protocol:** `linear-p15-v1`
**Held-out run:** 2026-10-22, one run after the preregistration commit `e0483bc2`.
**Disposition:** integrity PASS; registered positive generation trend NOT_ESTABLISHED (the criterion fails because the model is not estimable).

## Result

The fixed draw completed all 1,800 task rows (200 worlds × 3 generations × 3 arms), giving 600 paired task worlds. Full system solved 600/600 (100%). Unchanged operator solved 196/600 (32.67%); adaptive curriculum also solved 196/600 (32.67%). The full-minus-unchanged difference is 67.33 percentage points. The curriculum arm matched the unchanged arm exactly, so this run shows no independent task-success benefit from the tested curriculum fixture.

| Generation | Unchanged operator | Adaptive curriculum | Full system | Paired exact McNemar p, full vs unchanged |
|---:|---:|---:|---:|---:|
| 1 | 0/200 (0%; 95% Wilson [0, 1.88%]) | 0/200 (0%; 95% Wilson [0, 1.88%]) | 200/200 (100%; 95% Wilson [98.12%, 100%]) | 1.2446×10⁻⁶⁰ |
| 2 | 56/200 (28%; 95% Wilson [22.24%, 34.59%]) | 56/200 (28%; 95% Wilson [22.24%, 34.59%]) | 200/200 (100%; 95% Wilson [98.12%, 100%]) | 8.9683×10⁻⁴⁴ |
| 3 | 140/200 (70%; 95% Wilson [63.32%, 75.93%]) | 140/200 (70%; 95% Wilson [63.32%, 75.93%]) | 200/200 (100%; 95% Wilson [98.12%, 100%]) | 1.7347×10⁻¹⁸ |

Full-system scores stayed at 100%, while the unchanged operator increasingly matched the generation-specific target: the paired outcome gap narrowed from 100 to 72 to 30 percentage points. The preregistered seed-stratified conditional-logistic arm-by-generation model returned `complete_or_near_complete_separation`; its slope, corrected lower bound and p-value are therefore not estimable. The primary registered criterion requires an estimable positive trend, so it is **not met**. The per-generation McNemar tests are descriptive paired contrasts and do not replace the failed trend criterion. The reported bootstrap work difference is +2.0 units per task (95% interval 1.9367–2.0650); full-system latency was slightly lower in this run, but the measured interval is only about 1–13 microseconds and is not treated as a meaningful latency result. More work did not establish greater efficiency.

## Candidate qualification and controls

Before the held-out draw, candidate development outcomes were 2/2 versus 0/2 parent outcomes for each of `commutator_square_v1`, `commutator_cube_v2`, and `commutator_fourth_v3`. Each preserved eight invariant checks, with declared development work of 8, 12 and 16 units. The user separately approved each candidate under `pmb-v1-frozen-criteria`, and the raw run records the corresponding three graph approval events. No later candidate is approved.

All 100 preregistered analyzer-integrity controls detected their single-field mutation (20 each for world hash, primitive-access hash, input audit, invariant receipt and action receipt). The scored rows had zero pairing, world/access, input, invariant, action, work, graph-limit, status or family failures. No external actions occurred, all three approved generations were active with valid ancestry before their tasks, and all configured budget ceilings were respected.

## Scope and limits

This is one finite S4 process-macro family with a generated task goal that becomes the next commutator power at each checkpoint. It establishes that the three approved macros solve this declared one-call permutation task, not that the system autonomously discovers general strategies, improves across domains, learns mechanisms or exceeds human performance. The unchanged control improved on later-generation targets without operator changes, accounting for the shrinking gap. No protocol-matched human comparison exists. The run does not close L1–L7 or authorize a broader capability claim.

The supported next work is a separately preregistered evaluation with independently generated goals and task structure that can estimate improvement across generations. This result does not authorize an unregistered follow-on or imply that the current trend criterion passed.

## Provenance and raw artifacts

The held-out runner/analyzer hashes and dependency closure are frozen in [`COGNITION_LINEAR_P15_PREREG.md`](COGNITION_LINEAR_P15_PREREG.md). The raw scorecard and analyzer output remain outside git:

- `/tmp/p15-heldout.json` — SHA-256 `2805a9c041624583dfbcca6e1e05f1783113dab3b0ee10f584b5210559d12438`
- `/tmp/p15-analysis.json` — SHA-256 `e5fabd74ec3933d85f85aa2966234a6a531cca581cde4ae35b7c38751f31b407`

Human comparison is `UNAVAILABLE_PROTOCOL_NOT_MATCHED`; no capability level is closed.

## Post-run review qualification (2026-10-22)

The [source/artifact review](COGNITION_P15_REVIEW_AND_REMAINING_GAPS_20261022.md) verified that the archived raw and analyzer hashes match this ledger. It also found two limits not detected by the frozen integrity checks: `engine_binary_sha256` hashes the Python package wrapper rather than the loaded native extension, so execution-time native artifact identity remains `NOT_ESTABLISHED`; and the scored `_run_task` selects/composes the arm's process in Python before native application rather than executing the active graph-selected operator expression. The outcome counts and original NOT_ESTABLISHED trend are preserved, with their claim scope restricted to this adapter's native macro application and separately exercised lifecycle. No historical frozen hash or result was changed and no hold-out draw was repeated. Follow-up Phases 16–22 in the canonical plan address these limits and the earlier behavioral learning gaps.
