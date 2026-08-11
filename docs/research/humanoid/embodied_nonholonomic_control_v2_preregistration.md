# Nonholonomic control v2 preregistration

V1 failed at heading weight `1.0` and is now development data. A fixed
three-point sweep on those cases selected weight `5.0`; no v2 case was
executed during that choice. All other controller parameters and gates remain
unchanged.

V2 freezes six new seeds, dynamics settings, damage/wear schedules, and
rearward or strongly lateral goal offsets. It repeats the exact enhanced
adaptive, legacy-controller adaptive, and healthy-reference arms on Racecar,
R2-D2, and Husky.

The primary claim and refusal gates are unchanged from v1: Racecar must win at
least four of six matched pairs, median paired advantage must be at least
`0.05`, and enhanced median progress must be positive. Both adaptive arms must
learn after damage, enhanced control must exercise heading escape, the legacy
ablation must not, median regression on either other morphology may not cross
`-0.10`, and every healthy morphology must retain positive median progress.
