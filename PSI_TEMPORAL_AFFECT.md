# PSI temporal and affect contract

The PSI layer uses graph epochs as event latches. Hosts may stamp an epoch as
mechanical I/O, but they must not carry cognitive state between epochs.

- `Drive.now_epoch > Drive.last_tend` admits one decay update. The same rule
  advances `last_tend`, so repeated settlement in one epoch is idempotent.
- `ModulatorState.epoch > competence_epoch` admits one learning-progress update.
  The graph advances `competence_epoch`; Python never copies competence into a
  base accumulator.
- `ModulatorState.epoch > emotion_epoch` clears all region hits and read-off
  cells before the stable appraisal is classified. The graph advances
  `emotion_epoch`; Python never clears emotion cells.
- Leading drive is the graph `Argmax(weight * urgency)`. An incumbent persists
  until the best challenger exceeds it by `drive_switch_threshold`.

`affective_state_core` defines the canonical downstream state:

```text
Agent              -has_affective_state-> AffectiveState
EmotionHub          -has_affective_state-> AffectiveState
ModulatorState      -projects_affect_to->  AffectiveState
DualProcessContext  -uses_affective_state-> AffectiveState
```

The required attributes are `valence`, `arousal`, `resolution`,
`selection_threshold`, `securing`, `competence`, and `epoch`. The seed installs
one neutral state on the agent root. PSI projection is inert unless a
`ModulatorState -projects_affect_to-> AffectiveState` edge is explicitly wired.
This lets non-PSI cognition use the neutral contract without loading drives or
modulators.

The falsifiable gates are in
`tests/test_psi_temporal_affect_migrated.py`, including the exact half-life case
`1024 -> 512 -> 512` across two settlements in one epoch.
