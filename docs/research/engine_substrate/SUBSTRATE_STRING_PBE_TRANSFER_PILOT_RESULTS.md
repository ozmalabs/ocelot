# String PBE transfer pilot results

**Run date:** 2026-09-25 local. **Evidence grade:** pre-locked pilot, one generated suite. The fixture and raw report use the identifier suffix `20260926`; that suffix was assigned one day ahead in error before execution and is retained as the fixed suite/run identifier. It does not represent the execution date. The pre-run input lock verifies the exact measured files.

## Protocol

The preregistered [`24-task suite`](../../../tests/fixtures/substrate_string_pbe/tasks.json) has six strata: replacement, split, substring count, append, prefix and casefold-then-suffix. Every task has four revealed and three held-out examples. The paired arms are current P4 main, the frozen learned-layer setting with exemplar retrieval retained, and an independent fresh-substrate replay of main. Held-out correctness is exact across all three rows. This measures applying already supported string operations to generated fresh instances and constants; it does not test discovery of an unknown operator or natural task prevalence.

The protocol is in [`SUBSTRATE_STRING_PBE_TRANSFER_PILOT_PREREG_20260926.md`](SUBSTRATE_STRING_PBE_TRANSFER_PILOT_PREREG_20260926.md). Source, fixture, seed, engine and build hashes were locked before execution in [`string_pbe_transfer_lock_20260926.json`](../../../evaluation/substrate_capability/string_pbe_transfer_lock_20260926.json). The raw records, route readbacks, environment and provenance are in [`substrate_string_pbe_transfer_pilot_20260926.json`](../../../evaluation/reports/substrate_string_pbe_transfer_pilot_20260926.json).

A separate post-run analyzer independently recomputed the expected output for all 168 generated revealed and held-out input/output pairs and compared the three arms' task outcomes. It found zero fixture mismatches and zero paired-arm outcome mismatches; see [`analyze_substrate_string_pbe_transfer.py`](../../../scripts/analyze_substrate_string_pbe_transfer.py) and its [analysis record](../../../evaluation/reports/substrate_string_pbe_transfer_analysis_20260926.json). This validates the fixture and report consistency; it does not turn the pilot into a confirmatory or population estimate.

## Results

| Arm | Exact held-out pass | Accepted, including false accepts | Accepted but held-out wrong | Gaps | Enumerator candidate evaluations |
|---|---:|---:|---:|---:|---:|
| Main | 12/24 (50%) | 14 | 2 | 10 | 1.60 million |
| Frozen | 12/24 (50%) | 14 | 2 | 10 | 1.60 million |
| Main replay | 12/24 (50%) | 14 | 2 | 10 | 1.60 million |

Main and frozen matched task-by-task: 12 pass in both, 12 pass in neither. The descriptive family-stratified paired bootstrap interval for the difference is [0, 0] because every paired task outcome is identical; with 24 generated tasks this is not evidence of population equivalence. Main and replay outcome/readback fingerprints match exactly.

| Stratum | Exact pass | Accepted wrong | Gaps | Main route observation |
|---|---:|---:|---:|---|
| Split | 4/4 | 0 | 0 | All four accepted through exemplar retrieval. |
| Append | 3/4 | 0 | 1 | Three retrieval passes; one enumeration budget gap. |
| Casefold then suffix | 3/4 | 0 | 1 | Three retrieval passes; one enumeration budget gap. |
| Prefix | 2/4 | 0 | 2 | Two retrieval passes; two enumeration budget gaps. |
| Replace | 0/4 | 0 | 4 | All four exhausted the 200,000-candidate cap. |
| Substring count | 0/4 | 2 | 2 | Four exemplar retrievals; two false accepts and two structural-verdict gaps. |

Sixteen tasks selected retrieved exemplars; eight reached enumeration, all at the 200,000-candidate limit. Summed route time was 3.66 seconds for main and 3.64 seconds for frozen, excluding each task's reported boot time; the whole 72-run benchmark took 13.23 seconds with 352,004 KiB parent peak RSS. These are measurements of this harness and machine only.

## Interpretation and next gate

The route can transfer retrieved templates to fresh string values and constants, especially for split and simple concatenation patterns. The result also identifies concrete failures: replacement is expressible in the shipped native string grammar but all four requests gap at the current search cap; substring-count retrieval produces two accepted programs that fail all-row validation. The unchanged main/frozen result shows no measured benefit from the ablated learned layer on this suite. Retrieval availability is shared by both arms, so this is not a test of general acquisition.

Before claiming string generalization, run a separately generated confirmatory family with less reliance on near-verbatim operator wording, adversarial examples that distinguish close retrievals, a frozen/no-retrieval baseline, and a budget escalation arm declared in advance. Retain the current pilot and false accepts as fixed evidence; do not tune this suite and then reuse it as held out.
