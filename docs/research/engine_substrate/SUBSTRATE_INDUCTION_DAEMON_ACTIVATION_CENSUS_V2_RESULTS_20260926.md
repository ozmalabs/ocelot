# Daemon Rung 4 activation census v2 (2026-09-26)

## Question and scope

The v1 clean-boot capture compared `WorldAdapter()` core, the selected conversation evaluation profile, and an explicit growth profile. Source review showed that the daemon's fresh `full`, `chat`, and `embodied` modes follow different boot branches. This capture reproduces those three daemon branches with fresh adapters, then submits the same two authored `teach()` examples. Checkpoint resume is excluded because it depends on serialized prior state.

## Results

| Daemon fresh-boot arm | Seed selection / load | Shape loop | MetaShape growth | Teach statuses | New MetaShape |
|---|---|---|---|---|---|
| `full` | 740 selected; 729 loaded; 11 failed | loaded | loaded | residual → recognized | `ms_is_a_slot_a_slot_b` |
| `chat` | 17 core + 10 chat seeds, no captured failures | absent | absent | pending → pending | none |
| `embodied` | 7 selected seeds | absent | absent | pending → pending | none |

The full arm's failed manifests are recorded verbatim in the raw JSON (eight `seed node missing local_id`, three `seed ref must be an object`). The two target growth seeds are present in the selected/loaded closure. All four inspected learner flags (`gen_infer_enabled`, `time_infer_enabled`, `depth_infer_enabled`, `blink_bridge_enabled`) are absent in all three arms. Eight of eight analyzer gates pass.

## Interpretation

The daemon's ordinary **fresh full boot does activate** the symbolic MetaShape growth path; the earlier v1 inference that the ordinary production route lacked activation was too broad. V1 establishes that the separate conversation evaluation profile excludes `meta_shape_growth`, and that the small daemon `chat` and `embodied` boot modes also exclude it. The same teach helper writes observations in every arm, but only arms with growth rules can process them in this fixture.

This is boot-activation evidence, not evidence that real daemon conversations commonly call `teach()` with compatible recurring residuals, nor that the minted shape improves downstream performance. Full boot's unrelated 11 manifest failures remain a separate boot reliability issue. MetaShape is symbolic graph structure, not a newly executable operator.

## Production-route source trace

The daemon maps the graph-selected `teacher` host action to `_teacher_tick`, which delegates to `domains.teacher_dispatch.scan_and_teach`. That dispatcher selects explicitly linked `TeacherRequest` nodes, resolves local or remote evidence, writes `TeacherEvidence` and candidate graph nodes, then marks the request completed/unavailable. It does not call `domains.teach.teach`, `domains.meta_shape.observe`, or a learner-adoption function; the module docstring explicitly says it neither learns the payload through `learn_from_teacher` nor composes a reply. Separately, `domains.teach.teach` does call `meta_shape.observe` for items its callers explicitly submit. Therefore, daemon full boot makes the Rung 4 rules available, but the common graph-selected teacher-evidence route is not itself a path that feeds those rules. This source trace narrows the follow-up from boot activation to the missing evidence→adoption/teaching bridge; it does not establish that no other daemon subsystem invokes `teach()`.

Relevant source: [daemon action map](../../../scripts/jabberwock_daemon.py), [teacher evidence dispatcher](../../../domains/teacher_dispatch.py), [explicit teaching helper](../../../domains/teach.py), and [MetaShape observer](../../../domains/meta_shape.py).

## Reproduction and evidence

- Runner: [daemon activation census](../../../scripts/substrate_induction_runtime_activation_census_v2.py)
- Analyzer: [v2 gate analyzer](../../../scripts/analyze_substrate_induction_runtime_activation_census_v2.py)
- Raw capture: [JSON](../../../evaluation/reports/substrate_induction_runtime_activation_census_v2_20260926.json)
- Analysis: [gate summary](../../../evaluation/reports/substrate_induction_runtime_activation_census_v2_analysis_20260926.json)
- Boot source: [daemon boot](../../../scripts/jabberwock_daemon.py), [profile loader](../../../substrate/boot_profiles.py), [teaching path](../../../domains/teach.py), [growth rules](../../../seeds/meta_shape_growth.json)
