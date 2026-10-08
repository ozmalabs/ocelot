# Shared-substrate SUnit rate-threshold audit v1.6 preregistration

## Question
Does the v1.5 coexistence of positive SUnit `act` and zero `rate` follow directly from the stored `theta` threshold, and are both fields evaluated at the captured Retina step?

## Protocol
Repeat the v1.5 source-locked root-scoped fixture, same seed, 3,000 development steps per Retina, 2,000 paired adaptation presentations, exact fixed A/B gratings, common prepared-state restores, and four blank/A/B/both conditions. Add per-unit `theta`, `act_step`, and `rate_step` to each SUnit endpoint record. Do not change stimuli, settling rules, or parameters.

## Analysis
For every unit in B-only and both-grating conditions, independently compute `max(act - theta, 0)` and compare with the captured `rate` within 1e-9. Also require `act_step == rate_step == Retina.step` at capture. Report per-unit values and exact mismatch counts. A pass establishes consistency of the thresholded-rate rule on these endpoints, not biological validity or task capability. If fields are stale or inconsistent, stop further scope/task interpretation and trace closure ordering before expanding the benchmark.
