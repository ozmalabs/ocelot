# Endogenous nonholonomic control

`embodied_adaptation/1.6.0` removes the fixed 24-action heading-escape
horizon from the graph-native controller. It also removes the associated
progress fraction and heading-weight parameters.

The controller now derives recruitment, action choice, and termination from
its own learned sensorimotor graph:

- The weakest learned translation consequence supplies the body's empirical
  rest scale. Goal progress below that scale recruits orientation.
- The strongest learned turn consequence supplies one empirical turn quantum.
  Orientation stops when the remaining egocentric bearing error fits inside
  that quantum.
- Candidate actions are compared by estimated remaining motor work:
  translation distance in learned translation-action quanta plus bearing error
  in learned turn-action quanta. This prevents angle reduction from ignoring
  displacement without introducing a cross-unit weight.
- Every `MotorTrial` records its pre-action goal bearing. A heading bout remains
  viable only when the receipt-backed post-action bearing is smaller. An
  ordinary goal-directed action starts a fresh bout.

All of those quantities are graph attributes or graph terms evaluated by the
Rust substrate. Python continues to provide raw simulator observations and to
record the resulting decisions; it does not decide when to orient or which
actuator to use.

## Development regression

After implementation, both previously completed nonholonomic protocols were
replayed as development matrices. Historical protocol and result artifacts
were not changed.

| Matrix | Racecar enhanced median progress | Legacy median | Median paired advantage | Wins | Original gates |
|---|---:|---:|---:|---:|---:|
| v1 | 0.8220 | 0.1365 | +0.3569 | 6/6 | pass |
| v2 | 0.7731 | 0.6075 | +0.2409 | 4/6 | pass |

The same controller also passed the other-body regression floors. On v2,
median paired advantage was +0.1127 for R2D2 and +0.0265 for Husky. These are
post-hoc development results, not a new preregistered confirmatory claim.
