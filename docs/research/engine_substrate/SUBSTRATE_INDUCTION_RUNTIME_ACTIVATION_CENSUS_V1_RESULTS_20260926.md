# Rung 3/4 runtime activation census v1 (2026-09-26)

## Question

Does the existing teaching observation route activate the serialized MetaShape growth mechanism under the default core, the selected conversation profile, or only when its seed dependency closure is selected explicitly?

## Method

One runner process created three fresh `WorldAdapter` instances. It recorded loaded seed counts and learner flags, called the same `teach()` route twice with the same authored relational-shape example, and recorded observation status and minted shapes. The conversation arm used `load_conversation_seed_profile`; the explicit arm used the seed loader with `meta_shape_growth` selected and dependencies enabled. Raw data include SHA-256 digests for relevant Python sources, seed manifests, build metadata, and the native extension. This is a controlled activation census, not a natural-task prevalence sample.

## Results

| Boot arm | Seeds | Shape decode loop | MetaShape growth | Two teach statuses | Mint |
|---|---:|---|---|---|---|
| `WorldAdapter()` core | 17 | absent | absent | pending → pending | none |
| Selected conversation profile | 70; no load failures | present | absent | pending → pending | none |
| Explicit growth dependency closure | 2 (`shape_vocabulary`, `meta_shape_growth`) | absent | present | residual → recognized | `ms_is_a_slot_a_slot_b` |

All four learner flags inspected by the runner (`gen_infer_enabled`, `time_infer_enabled`, `depth_infer_enabled`, `blink_bridge_enabled`) were absent in all three clean profiles. The analyzer admits all nine preregistered structural and behavioral gates. The explicit arm demonstrates that the growth rules can consume the same teaching observations when installed; it does not demonstrate automatic installation or autonomous concept discovery in conversation.

## Interpretation and limits

This locates an integration gap, not a defect in the rule mechanism: the default core does not load either shape seed; the selected conversation profile loads `shape_decode_loop` but not the `meta_shape_growth` seed; and the teaching path saves observations that remain pending without the growth rules. In this capture, the same path reaches residual recognition and one symbolic MetaShape mint only under explicit growth-seed selection. `MetaShape` is graph vocabulary/structure, not an executable learned operator.

The census is one process, one conversation-profile construction, and intentionally repeated authored examples. It does not cover alternate boot profiles or establish how frequently real production teaching produces compatible residuals. Source traces and runtime capture should be followed by a broader call-site/profile census before changing production activation policy.

## Follow-up correction

V1's mention of a "default" teaching route applies only to `WorldAdapter()`'s core-only constructor and the selected conversation evaluation profile. It does not describe the daemon's default fresh `full` boot. The daemon-specific v2 capture shows that `full` loads the growth path, while daemon `chat` and `embodied` boots do not. See [v2 results](SUBSTRATE_INDUCTION_DAEMON_ACTIVATION_CENSUS_V2_RESULTS_20260926.md).

## Reproduction and evidence

- Runner: [runtime activation census](../../../scripts/substrate_induction_runtime_activation_census_v1.py)
- Analyzer: [independent gate analyzer](../../../scripts/analyze_substrate_induction_runtime_activation_census_v1.py)
- Raw capture: [JSON](../../../evaluation/reports/substrate_induction_runtime_activation_census_v1_20260926.json)
- Gate summary: [analysis JSON](../../../evaluation/reports/substrate_induction_runtime_activation_census_v1_analysis_20260926.json)
- Related source: [`WorldAdapter`](../../../substrate/world_adapter.py), [`CORE_SEEDS`](../../../substrate/boot_core.py), [conversation profile loader](../../../substrate/boot_profiles.py), [teaching path](../../../domains/teach.py), [MetaShape observation helper](../../../domains/meta_shape.py), [`meta_shape_growth` seed](../../../seeds/meta_shape_growth.json)
