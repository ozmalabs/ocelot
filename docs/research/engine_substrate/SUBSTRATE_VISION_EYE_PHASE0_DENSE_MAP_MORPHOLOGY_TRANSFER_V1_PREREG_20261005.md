# Phase-0 dense-map morphology transfer v1 preregistration

**Question.** Does nearest-site region prediction on a nine-site spatial map depend on training with a filled square patch, or does the same behavior appear with a sparse cross-shaped feature?

**Design.** Six fresh seeds (30–35) are crossed with two within-seed conditions: a 3×3 filled square (9 active retina cells) and a five-cell cross (center plus four orthogonal neighbours). Each condition uses nine WUnits, the same 16×16 retina, and the same 3×3 site grid `(3,8,13) × (3,8,13)`. Train each site for 4,000 contiguous presentations at `ph0_eta=0.005` (36,000 steps/worker), rotating site order by seed modulo nine. Square and cross workers share seeds, site order, per-site exposures, and probe sequence; only mask morphology changes.

**Frozen probes.** Freeze plasticity; probe all nine trained sites and sixteen held-out positions in `{5,6,10,11} × {5,6,10,11}` three times each (75 probes/worker, 900 total). Verify exact learned-weight preservation.

**Scoring.** Independently reconstruct receptive-field centers/spreads and native activations/winners from each condition's captured weights and actual input masks. Report field coverage and exact localization at trained sites, exact held-out coordinate localization, held-out nearest-trained-site-region accuracy, confusion matrices, and paired per-seed differences between morphologies. Nearest-region agreement is discrete spatial classification and does not establish continuous interpolation.

**Gates and limits.** Lock runner, analyzer, protocol, source/native/seed inputs, and the prior dense-map v1 source lock before capture. Require twelve workers, six paired seeds, exact training exposure/order/write counts, 75 probes with three per location in every worker, unique winners, positive runtime progress, stable source identity, activation/winner parity, and frozen weights. This compares two simple authored masks in one retinotopy learner; it is not shape recognition or natural-image vision.
