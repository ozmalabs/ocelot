# Self-report route contrast panel v1.1 results

Date: 2026-09-27

## Result

**Superseded:** although v1.1 included the reference slabs, it omitted `scripts/collapse_engine.py`, a runtime dependency of the action path. Its “handled but no response” outcomes are therefore not evidence of provisioned action execution. See the [v1.2 amendment and full-environment results](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_2_RESULTS_20260927.md).

The corrected panel passed all 9 independent checks: 30 fresh PIDs; three replicates per stimulus; stable source and all 36 runtime slab hashes at driver/worker boundaries; exact protocol/runner identity; complete records; and within-stimulus behavior/graph repetition. The frozen snapshot includes the later `boot_all.py` (`43c5ef6a…`), `boot_profiles.py` (`d0e434d9…`), and the complete `data/slabs/` runtime reference directory. It is the authoritative evidence for this measurement. The source lock is the provenance boundary; it is not a claim about worktree files after the capture.

## Outcomes

| Stimulus | Repeatable outcome (3/3) |
|---|---|
| A `report your organisation` | Known noun; instruction comprehension; handled; **no communication route or reply** (`ERROR: no communicative response could be generated.`) |
| B `describe your organisation` | Same instruction/handled/no-response outcome |
| C `tell me about your organisation` | Same instruction/handled/no-response outcome |
| D `report your purpose` | Instruction/handled/no-response |
| E `describe yourself` | Instruction/handled; generic self-description reply |
| F `tell me about yourself` | Instruction/handled; same generic self-description reply |
| G `what do you do?` | Instruction-gap route; no faculty for parsed target `what 'you'` |
| H `what does florpification mean?` | Wordplay dispatch; no communicative response |
| I `florpification is a new word` | Wordplay dispatch; response defers with “I am checking whether this is an instruction before acting.” |
| J `what is organisation?` | Table dispatch; no communicative response |

The graph is stable within each stimulus. Every run loads 731 manifests and reproduces the same 11 seed failures. The probe directly verifies that `wiktionary_has_en("organisation")` is true with POS `noun` in the captured runtime: the OOV coinage classification seen in v1 was caused by omitting `data/slabs`, not evidence about the fully provisioned route.

## Interpretation

The demonstrated gap is downstream of lexical knownness and instruction comprehension. The account-request evidence is present for A–F, but most requests do not produce a communication route or response; two self-directed phrasings fall back to a generic self-description rather than the detailed held-structure report. Wordplay recognition still does not reliably yield a user-facing answer. This is an operational capability gap in the locked snapshot, not an inference-cost result.

The v1 panel and wordplay-suppression probes used snapshots without the runtime reference slabs. Their source-only locks were incomplete for this behavior and their coinage/arbitration conclusions are superseded. They remain useful as a record of a measurement protocol defect. The provider-scope hunk intervention also omitted the same assets and cannot establish route causality for the provisioned substrate.

## Next work

1. Trace A from comprehension evidence through the `WorldAdapter` self-account bridge, action faculty result, Goal/lifecycle evidence, and response materialization. Record each branch and exception; do not infer successful handling from `instruction_outcome="handled"`.
2. Contrast A with E/F under the same boot and runtime assets to identify the predicate/target branch that allows only the generic reply.
3. Diagnose the no-response wordplay cases separately from route selection.
4. Extend source-lock templates for capability probes to include runtime assets read by the path, at minimum `data/slabs` here.
5. After a concrete repair, rerun this 10-stimulus panel and its full-asset lock before resuming self-report scale claims.

## Artifacts

- [v1 preregistration](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_PREREG_20260927.md)
- [v1.1 runtime-asset amendment](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_1_AMENDMENT_20260927.md)
- [Runner](../../../scripts/probe_self_report_route_contrast_v1_1.py)
- [Independent analyzer](../../../scripts/analyze_self_report_route_contrast_v1_1.py)
- [Full code, seed, and slab lock](../../../evaluation/substrate_capability/self_report_route_contrast_v1_1_lock_20260927.json)
- [Raw 30-worker capture](../../../evaluation/reports/self_report_route_contrast_v1_1_20260927.json)
- [Analysis](../../../evaluation/reports/self_report_route_contrast_v1_1_analysis_20260927.json)
