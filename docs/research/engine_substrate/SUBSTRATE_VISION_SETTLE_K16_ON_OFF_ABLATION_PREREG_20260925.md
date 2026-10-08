# K=16 settling on/off ablation preregistration

Date: 2026-09-25. Single-seed acute ablation; no production seed or engine change.

## Question
After matched retinal development and theta adaptation, does enabling `st_settle` change orientation responses relative to the same substrate and stimuli with settling disabled?

## Paired design
Use two independent `settle_lib.build_sheet` worlds with seed 20260928, n_side=4, lateral channels, connectivity=8, settle initially enabled, bubble=0. Deep-copy and tag all executable rules from the five vision manifests `hard_realtime` for default DualProcess tick. Both arms undergo identical 3,000-step retinal development and 2,000 random grating theta-adaptation presentations. Then pin theta and freeze all learning. The only arm difference is `SettleParams.settle`: 1.0 (on) versus 0.0 (off), set immediately before the orientation readout. Use `cell_stats(key="rate", period=4, K=16)` with its 12-orientation stimulus grid. Use cycle-aware default tick and retain the exact integer return from every adaptation and probe presentation; do not label the return as a termination reason.

## Outcomes
Record full tuning matrices, per-unit and mean OSI, alive counts, weight hashes/drift, and per-presentation progress values. Independently recompute OSI and tuning deltas. An acute settling effect is present if the max absolute tuning difference exceeds 1e-10; report OSI delta and response direction without a post-hoc equivalence threshold. Zero difference is evidence for this one seed/protocol only. Report any zero-progress or cap-sized tick returns. Timing is descriptive, not a speed comparison.
