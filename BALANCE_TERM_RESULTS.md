# THE BALANCE TERM WAS SWITCHED OFF — results

Measured 2026-08-09. One protocol line changed:
`locomotion.support_geometry_preview_authority: 0.0 -> 1.0` in
`protocols/humanoid_walking_v1.json`. Nothing else.

## What it is

`motor_compose.rs::support_preview` is the composer's support-polygon term: it
projects a capture point one `sqrt(height/gravity)` ahead and penalises it
leaving the foot polygon, in both axes.

```rust
let authority = self.po("support_geometry_preview_authority");
if authority == 0.0 || !(grounded) { return 0.0; }
```

The authority is read from the protocol's `locomotion` block, defaults to 0.0,
and is validated as 0.0-or-1.0. **It is a declared operator switch that had
never been declared for this protocol**, so the term returned zero on every
call. It is not a defect in the term; it is a switch nobody flipped.

Found by applying the F-16 thread's own diagnostic (`7099c47402`, *"before
changing a decision, find the code that makes it"*) after establishing that the
humanoid walk composes in Rust via `MotorCompose`, exactly as the F-16 does.

## Safety check before enabling

`support_preview` divides by `prior * support_count` and by `prior^2`, so a
coalesced zero would have produced inf/NaN and poisoned every candidate's cost.
Measured live on the episode/policy before flipping the switch:

```
support_phase_prior_strength  9.0   (policy; = (sensor_count+1)^2, derived not hand-picked)
support_sensor_count          2.0   (episode)
prior*count = 18.0   prior^2 = 81.0        -> no divide-by-zero
state_x/y/vx/vy, state_support_{0,1}_{x,y}  all present, real   ABSENT: none
```

Worth recording: a literal grep found ZERO writers for `state_x`, `state_y`,
`state_vx`, `state_vy` and the support positions, and the runtime probe found
all of them present with real values. The static audit lied, as this tree's own
dark-channel note says it does. Enabling on the strength of the grep would have
been enabling blind.

## Measured effect, single variable, 600 actions

| metric | authority 0.0 | authority 1.0 |
|---|---|---|
| `bounded_lateral_drift` | **False** | **True** |
| `directed_progress` flag | True | **False** (matches the gate's expectation) |
| `upright` | False | False |
| `bounded_aerial_occupancy` | False | False |
| `support_alternation` | True | True |
| lateral_offset | −0.693 m | **2.7e-05 m** |
| directed_progress | 0.742 m | 0.095 m |
| first_fall_action | 282 | 201 |
| aerial samples / cycle | 7.81 | 9.0 |

Against the full assertion set of
`test_graph_walks_with_alternating_support_and_bounded_aerial_phases`:

```
                                    before   after
  adaptation_first_fall is None      False    True   <- FIXED
  upright_at_end == 1.0              False    True   <- FIXED
  directed_progress < 0.3            False    True   <- FIXED
  |lateral_offset| < 0.2             False    True   <- FIXED
  evaluation dict                    False    False
  first_fall_action is None          False    False
  minimum_height > height_floor      False    False
  0 < support_alternations < 20      False    False
  aerial/cycle <= 1.0                False    False
  TOTAL PASSING                        4/13     8/13
```

**Four fixed, none broken.** The lateral axis is fixed decisively — drift falls
by a factor of ~25,000 — which is exactly the axis `support_preview` governs.

## Confirmed by the gate itself

`pytest tests/test_humanoid_walking_migrated.py` before and after, same tree,
same invocation:

```
baseline  1 failed, 22 passed   differing: upright, bounded_lateral_drift, bounded_aerial_occupancy
after     1 failed, 22 passed   differing: upright, bounded_aerial_occupancy      (956.64s)
```

`bounded_lateral_drift` moves into pytest's "identical items" set — three
differing flags become two. The same 22 tests pass either way, so nothing else
in the file moved. `test_humanoid_lifelong_migrated` (which uses this protocol
as its `base_protocol`) is 5 passed before and after.

## HONEST SCOPE — what this does NOT do

* **The test still fails.** `upright` is still False: the body falls at action
  201, earlier than the 282 of the baseline. Enabling the balance term changed
  the FAILURE MODE (no lateral drift, much less forward travel, still airborne,
  still falls) rather than preventing failure. It is an improvement on 4 of 13
  assertions, not a repair.
* **`directed_progress` flipping to the expected value is hollow.** The gate
  wants "does not walk"; the body now walks less. That is not progress toward
  walking, and it should not be counted as such.
* **The remaining failure is not a balance problem.** Aerial occupancy is 9.0
  per cycle against a limit of 1.0, and `support_preview` correctly returns 0
  when no foot is loaded — a support polygon does not exist in flight. The term
  cannot address the phase that produces the fall.
* **Run-to-run variance is large and unquantified.** Two 600-action runs of the
  same protocol produced 164 and 24 aerial actions. Every number above is n=1.
  A single before/after pair cannot attribute a change with that spread, and no
  seed sweep was run.
* **The declared value is 1.0 because the switch is validated as 0.0-or-1.0.**
  It is not a tuned weight and was not selected against alternatives.

## The standing residual this does not touch

Consequence models are selected inside a hard bucket
(`peer.support_phase == model.support_phase`), and `_support_code` returns 0 for
BOTH "both feet loaded" and "neither foot loaded". Measured: `current_support_phase`
is written correctly on **600/600** actions — the tracker is flawless — and 24
flight actions were filed alongside 468 double-support actions under phase 0.

The continuous metric that would not need the bucket already exists
(`context_distance`, over attitude, angular rate, velocity and lateral offset)
and carries **no contact term at all**, so the one quantity varying continuously
from standing through single support to flight is expressed only as the enum
that discards it. Measured load spans a continuum (15 of 20 bins occupied,
0 to 3.26 x body weight), and the labels overlap almost completely: `support_0`
ranges from 0.022 to 2.172 body weights.

Adding a fourth code would preserve the defect. The direction the code points at
is to add load to `context_distance` as another nondimensionalised error term
and drop the bucket filter. NOT done here, and it would change which models are
active on every action, grounded included.
