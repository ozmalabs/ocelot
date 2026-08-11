# Nonholonomic control v1 preregistration

The completed damage-navigation v4 matrix is development evidence only. It
exposed a controller failure independent of damage learning: in one Racecar
case, adaptive, frozen, and healthy graphs all selected the learned
near-zero-consequence action for every post-change step. The legacy scorer
imagined that the strongest translation action would follow the current
action, but replanned before enacting that imagined continuation.

Version 1.5.0 retains two-step distance descent as its default. When the last
goal-directed action produced less than 0.5 percent of the graph's learned
translation scale, a bounded orienting regime scores the next action by
one-step distance plus post-action egocentric heading error. It can run for at
most 24 actions per episode. Calibration, recalibration, and babble receipts
cannot trigger it. All state, thresholds, action models, regime selection, and
action choice are graph-held; the host only transduces raw simulator receipts.

The frozen protocol contains six previously unexecuted dynamics, damage/wear,
and rearward or strongly lateral goal combinations. Each is run on R2-D2,
Husky, and Racecar with:

1. adaptive plasticity and heading escape enabled;
2. identical adaptive plasticity with heading escape ablated; and
3. an undamaged heading-escape reference.

The primary claim is Racecar-specific but the mechanism is not. Enhanced and
legacy arms must have byte-exact matched pre-change trajectories. Both must
adapt after damage, the enhanced arm must exercise the new regime, and the
ablation must not. Racecar must win at least four of six pairs, have median
paired advantage of at least `0.05`, and retain positive median progress.
Median paired regression on R2-D2 or Husky may not be worse than `-0.10`, and
healthy median progress must remain positive in every morphology.
