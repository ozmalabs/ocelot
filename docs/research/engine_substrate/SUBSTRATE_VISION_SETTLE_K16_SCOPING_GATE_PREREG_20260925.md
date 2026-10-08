# Settling and calibrated K=16 orientation gate preregistration

Date: 2026-09-25. One-seed gated workload evaluation. All latency tags and scope edits exist only in deep-copied in-process manifests.

## Question
After adding the metadata required by the enabled DualProcess plan, do global and Retina-root-scoped settling produce the same calibrated orientation response, and does tagged default tick reproduce unfiltered closure through the full probe?

## Four paired arms
Use `settle_lib.build_sheet`, seed 20260927, 4×4 SUnit lattice, lateral channels, connectivity 8, settle=1, bubble=0. Cross scope `{authored global, benchmark Retina-root scoped}` with execution `{default tick after hard_realtime tagging, unfiltered run_rules_report}`. All five executable vision seed families receive `latency_class="hard_realtime"` in benchmark copies in both execution arms; scoped clone additionally replaces the two SUnit-global mean sources with `Neighbours(r, has_sunit)`. No other rule/term differs.

Follow the committed preparation order: develop the lateral retina for 3,000 wave steps while cortical weights are frozen; adapt theta for 2,000 random orientation/phase grating presentations with weights frozen and theta active; pin theta and freeze all learning; measure `complex_cells.cell_stats(key="rate", period=4, K=16)`. Use PCG64 seeded stimuli and identical per-arm seeds. Wave development uses `WaveWorld.step` with cycle detection enabled; adaptation and measurement use either tagged default `tick(..., detect_cycles=True)` or unfiltered `run_rules_report(..., detect_cycles=True)`. Keep response statuses/progress counters.

## Outcomes and gate
Record mean and per-unit OSI, all tuning curves, alive counts, weight drift, root membership, per-presentation fixed-point/repeated-state/cap statuses, total/median rule applications, and phase timings. Compare arrays within 1e-10 and exact seed-paired outputs where deterministic. Any cap exit, silent output, or nonzero execution-mode discrepancy fails the tick-equivalence gate. Global versus root-scoped equality is assessed separately. This is a one-seed engineering/quality gate, not a population estimate or speed claim.
