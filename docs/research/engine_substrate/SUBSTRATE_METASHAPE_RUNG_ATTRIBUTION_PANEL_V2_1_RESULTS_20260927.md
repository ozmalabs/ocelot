# MetaShape rung-attribution panel v2.1 source-stable replication results

## Integrity

The eight-worker schedule ran on an isolated snapshot of the post-edit worktree. The source/runtime lock covers 311,885 Python/seed/runtime asset files and explicit protocol, amendment, runner, analyzer, measurement helper, native extension, Rust source/build manifest, and Cargo manifests. The snapshot source directories were read-only. Full pre/post batch locks agree, all workers use the registered immutable snapshot, two workers ran per family, and the dependency closure loaded without seed errors. The independent analyzer passes all eight integrity checks.

The preceding v2 capture is separately retained as censored because `substrate/boot_all.py` changed during it. This is a source-stable replication after the outcomes were inspected, not an independent confirmatory sample.

## Outcomes

Each worker trained on two examples, then received one positive and four registered control probes. Values below pool only the two replicates within the named authored schema; they are not population estimates.

| Schema family | Mint after training | Exact positive transfer | Fixed/missing/type controls attributed by any rung | Added-field probe | Median teach-call time |
|---|---:|---:|---:|---|---:|
| FrameBindingProbe | 2/2 | 2/2 | 0/6 | 2/2 `recognized` by the new MetaShape | 1.981 ms |
| ResourceTransferProbe | 2/2 | 2/2 | 0/6 | 2/2 `recognized` by the new MetaShape | 2.014 ms |
| GoalTraceProbe | 2/2 | 2/2 | 0/6 | 2/2 `recognized` by the new MetaShape | 2.218 ms |
| MotionRuleProbe | 0/2 | 0/2 | 6/6 `recognized_prior` | 2/2 `recognized_prior` by preexisting `spatial_dynamics` | 1.858 ms |

For the three families that minted a new shape, every fixed-value change, omitted fixed field, and fixed-field type change remained residual and uncovered. Their novel positive values transferred to the newly minted shape. The repeated MotionRule examples were absorbed by the preexisting `spatial_dynamics` keyword prior: no family-specific shape was minted, the positive was not exact structural transfer, and every registered control was also prior-attributed. This reproduces the specific failure mechanism identified in the earlier multi-schema panel.

The original protocol registered the added-field case as a negative. It was recognized by the new shape in all six replicated cases where a new shape was acquired. A new field can be a harmless open-world extension, so recognition alone does not establish a semantic false positive. We preserve the preregistered status and the analyzer's any-rung counts, but interpret this probe separately as extension tolerance; it is excluded from the fixed-relation discrimination count above. This interpretation is post-capture and must be frozen in any future confirmatory protocol.

Median per-teach call times range from 1.858 to 2.218 ms across these workers. These exclude the full seed-index/boot cost, are two-replicate descriptive values, and are not a scaling curve. Peak process RSS and each call duration are available in the raw record.

## Interpretation

On three of four hand-designed schema families, the induced structural MetaShape transfers to a novel positive and rejects the three fixed-relation controls in this panel. The weaker prior path remains a decisive boundary: one preexisting prior prevents acquisition and attributes all tested perturbations. New fields are tolerated by the structural shape in this fixture, which may be useful open-world behavior but was not originally specified as an acceptance contract.

These outcomes do not establish semantic correctness, downstream task benefit, natural false-positive rates, or open-ended concept invention. They do improve the tractability/capability map by showing that the measured induction mechanism has a distinct cheap-use vs acquisition boundary: structural acquisition requires a two-example recurrence, while prior attribution can be immediate and broad. The experiment does not measure the prevalence or economic frequency of either route.

## Next gate

Freeze the extra-field case as a nuisance/extension probe rather than a negative. Expand to independently authored schemas with explicit relation-level ground truth; include multiple fixed relations, same-keyword adversarial controls, exact structural positives, prior collisions, and downstream task utility. Report precision and recall separately by rung. Add a held-out behavior oracle so structural key coverage is not mistaken for semantic equivalence. Then measure acquisition frequency and cost under a representative residual stream.

## Artifacts

- [v2 preregistration](SUBSTRATE_METASHAPE_RUNG_ATTRIBUTION_PANEL_V2_PREREG_20260927.md)
- [v2.1 source-snapshot amendment](SUBSTRATE_METASHAPE_RUNG_ATTRIBUTION_PANEL_V2_1_AMENDMENT_20260927.md)
- [v2 censored result](SUBSTRATE_METASHAPE_RUNG_ATTRIBUTION_PANEL_V2_CENSORED_RESULTS_20260927.md)
- [runner](../../../scripts/substrate_metashape_rung_attribution_panel_v2_1.py)
- [independent analyzer](../../../scripts/analyze_substrate_metashape_rung_attribution_panel_v2_1.py)
- [source/runtime lock](../../../evaluation/substrate_capability/metashape_rung_attribution_panel_v2_1_lock_20260927.json)
- [raw replication](../../../evaluation/reports/metashape_rung_attribution_panel_v2_1_20260927.json)
- [independent analysis](../../../evaluation/reports/metashape_rung_attribution_panel_v2_1_analysis_20260927.json)
