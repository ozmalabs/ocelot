# Linear P11 results

**Status:** mechanism and safety gates pass; transfer benefit is
`NOT_ESTABLISHED`. The source-exposed adapter transfers the registered
processes, but the fresh arm never solves the target and yields no matched
target outcome for the registered efficacy comparison.

## Frozen heldout draw

The separately committed preregistration is
[`COGNITION_LINEAR_P11_PREREG.md`](COGNITION_LINEAR_P11_PREREG.md), frozen at
`0215137f`. The heldout runner used the registered 6,000,000 seed block and
completed all 2,600 records: 800 each for fresh, source-exposed and
mismatched-source arms, plus 100 wrong-frame and 100 nonconjugate controls.
The run used the frozen code, engine and limits. Raw records and analysis are
archived outside git at `/tmp/linear-p11-heldout.json` and
`/tmp/linear-p11-heldout-analysis.json`.

| Measure | Heldout result | Registered interpretation |
|---|---:|---|
| Completed records | 2,600/2,600 | PASS |
| Missing paired arms | 0 | PASS |
| Paired world-hash failures | 0 | PASS |
| Input-audit failures | 0 | PASS |
| Source-exposed proposals selected | 800/800 | Mechanism observed |
| Source-exposed representations adopted | 800/800 | Mechanism observed |
| Source-exposed target effects verified | 800/800 | Mechanism observed |
| Source-exposed transferred processes adopted | 800/800 | Mechanism observed |
| Fresh target effects verified | 0/800 | Fresh arm has no source map; no solved outcome |
| Mismatched-source transfers adopted | 0/800 | Safe abstention |
| Wrong-frame control adoptions | 0/100 | PASS |
| Nonconjugate control adoptions | 0/100 | PASS |
| Matched solved exact-check comparisons | 0 | `NOT_ESTABLISHED` |
| Mean relative exact-check saving | unavailable | `NOT_ESTABLISHED`, not zero/pass |
| Solve-loss bound ≤2 pp and ≥25% savings | not evaluable | `NOT_ESTABLISHED` |
| ARC/LS20 external panel | unsupported | No registered ingestion adapter |
| Human comparison | unavailable | No protocol-matched reference |

Source-exposed records executed 21,600 exact native target checks (27 per
record across training, heldout and transfer verification); mismatched-source
records executed 20,400 (25 per record) and abstained. Fresh records executed
no target checks. Every arm received 8 training-state opportunities per record
(6,400 per arm); source-exposed and mismatched-source each had 6,400 source
evidence exposures, while fresh had zero. Mean graph sizes were 770 nodes
(fresh), 782 (source-exposed) and 778 (mismatched-source). Mean elapsed time,
including agent construction/boot, was 0.0613s, 0.1012s and 0.0646s per record,
respectively; separate boot time and process RSS were not measured. Mean
remaining shared budget was 8.0 after source transfer and 9.0 after
mismatched-source abstention. These costs are descriptive, not a compute-matched
efficacy comparison. Average complete package costs were 3,306 bits for the
source-exposed arm and 3,298 bits for mismatched-source; the frozen heldout
candidate description gate was evaluated within each representation trial.

The exact-check primary is inconclusive for a structural reason: the current
fresh adapter receives no acquired source map and has no native target-learning
route, so it cannot provide the solved target outcome required by the frozen
paired comparator. The result does not establish a ≥25% intervention/check
saving or a solve-loss bound. Do not interpret source-arm transfer correctness
as faster target learning, and do not infer L4 transfer or L5 invention.
Closing this capability gap requires a separately specified fresh target
learning adapter with equal primitive/model access and a new preregistration;
the completed heldout allocation must not be tuned or reused.

## Reproduction and validation

Preregistration commands and frozen hashes are in the preregistration. The
heldout raw scorecard SHA-256 is
`765c12a364b9b2fa051081bc8011083996fcd1b9cb5498e4d704a971f80bdd30`; analysis SHA-256 is
`f53f077cb445aa36e831f9fa29d10aae8440fb20aa347b518433f30cfffcf9dd`.

The P11 acceptance bundle passed: 60 tests across representation search,
process transfer, PMB grid transfer and cognition profile integration.
Runner and analyzer self-checks passed. P10's registered zero-gain result,
P4 C5 failure and P3 inherited `NOT_ESTABLISHED` status remain unchanged.

## Next supported entry

Phase 12 may proceed using verified native ProcessSchema effects, the exact
source/target frame and epoch contracts, bounded shared-budget requests,
heldout validation and the experience-grounded episode interfaces from P7.
Treat transfer as unavailable for learning-curve claims; Phase 12 must not
assume that a fresh observer can infer these process maps. External ARC/LS20
and human comparisons remain unsupported/unavailable until separately
registered adapters exist.
