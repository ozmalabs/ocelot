# PREREG — MAKE A RECOGNISED DOOR ACTUALLY OPEN (block 210000)

Recognition (block 209000) is HELD: a generic integer pattern-recognition eye
recognises doors/switches on real E1M1 by texture (coarse family FAR, fine
door/switch NEAR) and mints an *operate* goal — but the door does **NOT** open:
**0 opens / 1800 USE-spammed tics** (209000's named residual). This block is the
**ACT half**: recognition → approach → USE at the right pose → the door OPENS.

A SIBLING rung (211000) concurrently owns the GEOMETRY channel
(`doom_pattern_eye.py::col_geometry_level` + a geometry seed). **This rung does
NOT touch the geometry feature** — it adds a new OPERATE seed/rule + the
run/adapter execution of the "use" action. No merge collision by construction.

Seed block claim: `python3 scripts/seed_claim.py 210000 210999` → **CLEAN**
(verbatim `check_claim` output pasted in the commit / results).

## The architecture (CLAUDE.md: the operate DECISION is a RULE)

The graph decides; the adapter is mechanical VizDoom I/O. A new seed
`seeds/doom_operate.json` (self_load_only, **default-OFF** on an `OperateParams`
gate) holds a graph-native orient→approach→USE state machine as rules over the
209000 recognition + the agent's own pose/proprioception:

- **Sensors the adapter writes each tic (mechanical, no decision):** for the
  target recognised region — its screen `col` (from the texture eye), `near`
  (set when in USE range, from proprioception), and `fwd_progress` (the integer
  displacement of the LAST forward action — a pure efference signal, ~0 when the
  body is blocked against the door). The 209000 recognition attrs
  (`recognised_family`, `recognised`, `recognised_as`) come from the held eye.
- **The operate rules DECIDE the motor command** (`operate_command` ∈
  {`turn_left`, `turn_right`, `forward`, `use`, `none`}) from those sensors:
  1. `op_mint` — a coarse-recognised operable region → mint one `OperateGoal{phase:orient}`.
  2. `op_orient` — phase orient, region off-centre (`|col-center| >= face_tol`) →
     turn toward it (sign of `col-center`).
  3. `op_orient_done` — faced (`|col-center| < face_tol`) → phase approach.
  4. `op_approach` — phase approach, still moving (`fwd_progress >= block`) → forward.
  5. `op_reorient` — drifted off-centre while approaching → phase orient.
  6. `op_use` — phase approach, **blocked** (`fwd_progress < block` = in range),
     **faced**, and the region is **fine-recognised** (`recognised==1`, i.e. a
     door/switch resolved up close, both carrying the `use` affordance) → command
     `use`, mark used, phase operated.
  7. `op_wait` — phase operated → command `none` (**USE ONCE, never spam** — in
     Doom a USE on an already-opening DR door toggles it back closed; the 209000
     0/1800 spam baseline is exactly this failure).

The adapter reads `operate_command` off the graph and presses the corresponding
VizDoom button. It never branches on graph state to pick the action.

## Measurement harness (world I/O; NOT the eye's input)

Real E1M1, `-nomonsters` for a clean motor setting. Four **real DR-door**
sectors located by parsing DOOM.WAD linedef specials (special=1), validated to
open with a single USE (ceiling rises 0→~72): sector 26 @ (1544,-2496), 83 @
(2928,-3840), 85 @ (3008,-4024), 69 @ (3008,-4640). An "approach episode" warps
the agent to a start pose a short distance from a door (world setup), then the
GRAPH loop does orient→approach→USE from the EYE's recognition. The door-open is
OBSERVED from VizDoom **sector ceiling_height** (a SCORING oracle for the metric
ONLY — it never enters the eye; the eye reads rendered RGB luma only, 209000
discipline, AST-audited).

## GATES (pre-registered)

- **G-open (headline):** a recognised door actually OPENS. Report **N opens / M
  approach episodes**, decisively beating the 209000 baseline **0/1800**. Open =
  the target door sector's `ceiling_height` rises > 32 from its pre-USE baseline
  (full open ≈ +68..72). At least a handful of clean opens on real E1M1 doors.
- **G-gated-use:** USE fires ONLY when a door is recognised AND in range AND
  faced. Report precision = **USE-presses-that-open / total-USE-presses**,
  decisively better than the 0/1800 spam baseline. No blind USE-spam.
- **G-switch (reach, honest):** a switch operated → its REMOTE sector changes
  (the non-local effect). If it does not fit cleanly, NAME it the follow-on with
  the real number — do not fake it.
- **G-discipline:**
  - integer-native where the substrate is (descriptors, tolerances, thresholds
    are integers; `col`, `col_err`, `fwd_progress` quantised to integers);
  - **default-OFF byte-identical:** every operate rule gates on
    `OperateParams{enabled}`; absent the node no rule fires and no path changes;
    the seed is `self_load_only` (skipped by `load_all_seeds`);
  - canonical `.so` md5 **`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED (seed +
    adapter + existing Terms only; NO Rust — if Rust seems needed, STOP + report);
  - `term.rs` + whole `runners/dsl` diff EMPTY; `source_match` reported;
  - vision oracle `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER;
  - 34-file `bash scripts/per_area_settlement_regression.sh` BEFORE == AFTER.

## Honesty pre-commitment

If the door will not open reliably (pose/facing/timing hard to hit), report the
real number straight — a partial ("opens 3/10, failures are facing-misalignment")
beats a faked full. Lead with: recognition (209000) is held; this rung is the ACT
half. Commit to the worktree branch only (no merge to main; do not touch
`VISION_PROTOCOL.md`).
