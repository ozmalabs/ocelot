# RESULTS — A RECOGNISED DOOR ACTUALLY OPENS (block 210000)

Prereg: `DOOR_OPERATE_PREREG.md`, committed ALONE first at
**`3ae87fd5b850524eddaa57bb8b346f70851c2256`**. Off `main` HEAD **`6952055056`**.
Seed block **210000–210999** (`scripts/seed_claim.py 210000 210999` → `CLEAN`).

**Recognition (209000) is HELD; this rung is the ACT half:** recognition → orient
→ approach → USE at the right pose → the door OPENS. Block 209000 recognised
doors/switches by texture but the door did not open (**0 opens / 1800 USE-spammed
tics**). It does now.

## The build — and the mid-build owner steer

The operate DECISION lives entirely in a new seed `seeds/doom_operate.json`
(self_load_only, default-OFF on an `OperateParams` gate); the adapter
(`domains/doom_operate.py`) is mechanical VizDoom I/O.

**Owner steer, honoured:** *"no, it should set a movement goal."* The first draft
had the rules emit a per-tic `operate_command`; that was replaced. On recognising an
operable feature the graph now **SETS A MOVEMENT GOAL** — a first-class
`MovementGoal` that `moves_toward` the recognised region (the idiom of 205000's
`committed_goal`) — and rules PURSUE it. Four rules, one `run_rules` fixpoint:

1. `op_mint_move` — a coarse-recognised operable region → mint ONE
   `MovementGoal{kind:approach_operate, status:seeking}` `moves_toward` the region.
2. `op_steer` — pursuing a seeking goal, target off-centre (`|col−center| ≥ face_tol`)
   → turn toward it (sign of `col−center`).
3. `op_advance` — faced + still moving (`fwd_progress ≥ block`) → forward.
4. `op_use` — arrival (faced + **blocked** `fwd_progress < block` == in USE range +
   **recognised**) → USE, ONCE (marks the goal `operated`; the adapter clears the
   motor each tic so no rule re-fires → **no spam**).

The adapter writes the sensors (`col`, `near`, `fwd_progress`), clears the goal's
motor, runs the rules, and presses the button the graph named. It never branches on
graph state to choose an action. It does NOT touch the 211000-owned geometry channel
(region `geom_level` fixed 0, texture only) — no merge collision.

### The perceptual finding that shaped `op_use` (measured, load-bearing)

Texture is a **mid-distance** cue. Facing the door at d≈110 the eye reads its texture
strongly (central-band median level **6–8**); pressed FLAT against the door (d≈28)
the surface is uniform and the vertical-gradient energy → **0** (level 0–1). So the
door cannot be recognised at the contact pose. Recognition is therefore **latched
during approach** (object-permanent): `near` is set while texture is readable, the
fine door/switch recognition fires and `recognised` LATCHES, and `op_use` reads that
latched recognition at contact — not the (now-blank) current texture. This is exactly
209000's coarse-far/fine-near story, made to work through contact.

### The doors (world I/O, NOT the eye's input)

Real DR doors on E1M1 located by parsing `DOOM.WAD` linedef specials (special=1) →
door sectors, validated to open with a single USE (sector `ceiling_height` rises
0→~72). VizDoom sector index == WAD sector number. Each "approach episode" warps the
agent to a start point on an openable face and turns it to a JITTERED facing
(±25°/±12°/0 — orient must correct it); the graph loop then does the rest. The door
open is scored from the door sector's `ceiling_height` (a SCORING oracle for the
METRIC only — it never enters the eye; the eye reads rendered RGB luma, AST-audited
by 209000's `_assert_no_oracle_in_eye`).

## G-open (headline) — PASS

`results/doom_operate/gates.json`. 4 doors × 5 jitters = 20 approach episodes.

**GATED (the graph presses USE): 9 opens / 20 episodes** — vs the 209000 baseline
**0 / 1800**. Per door:

| door sector | eye texture on the openable face | opens / 5 |
|---|---|---|
| sec26 (1544,−2496) | strong (level 8) | **5 / 5** |
| sec69 (3008,−4640) | strong (level 8) | **4 / 5** |
| sec85 (3008,−4024) | faint (level ~2–4) | 0 / 5 |
| sec83 (2928,−3840) | faint (level ~2)   | 0 / 5 |

On the two doors the texture eye can actually SEE, **9 / 10 clean opens**, each from a
single USE at the right pose. The one sec69 miss is a start-pose where the body was
blocked at the warp point before reaching the door (USE from out of range). sec83 and
sec85 are texture-FAINT on their openable faces (the eye reads level ~2) — the eye
never recognises them and **never presses USE (n_use = 0): a clean negative, not a
mis-fire.** That is the 209000 texture-channel residual, exactly the surface the
sibling 211000 geometry channel is built to see.

## G-gated-use (precision) — PASS

USE fires ONLY when a door is recognised AND in range AND faced.

| arm | opens | total USE presses | USE precision (opens / presses) |
|---|---|---|---|
| **gated** (graph decides) | 9 | 10 | **0.90** |
| spam (USE every tic) | 0 | 1100 | **0.00** |

The gated arm presses USE **once** per episode, at the arrival pose, and 9/10 of those
presses open a door. The spam control (the 209000 failure mode) presses USE on every
tic while approaching the SAME doors and opens **nothing** in 1100 presses — in Doom a
USE on an opening DR door toggles it back closed, so mashing never lets a door reach
full open. **0.90 vs 0.00**, decisively better than the 0/1800 baseline.

## G-switch (reach) — NAMED FOLLOW-ON, honest number: 0 clean remote opens

E1M1's one remote-effect switch was located (WAD linedef **special=63**, SR remote
door-open, **tag=3** → remote target **sector 4**, at (288,−3072)). Two honest
blockers, both consistent with the door findings, meant it did NOT operate cleanly in
this rung: (a) its panel is texture-FAINT (level ~2–4, like sec83/85 — the eye does
not reliably recognise it); (b) its activation face sits in an alcove the straight
approach did not physically reach (the body stalls ~48 units short). **0 remote opens.**
The operate MECHANISM is identical to the door (USE a recognised operable feature →
its sector effect); the switch's *remote* demonstration is the named follow-on. Not
faked.

## G-discipline — PASS

- **Integer-native:** `OperateParams` (`center`, `face_tol`, `block_thresh`), the
  sensors (`col`, `tex_level`, `geom_level`, `fwd_progress`), and all rule arithmetic
  (`Abs`/`Minus`/`Gt`/`Gte`/`Lt`) are integers
  (`test_params_are_integer_native`). In-frame is integer.
- **Default-OFF byte-identical:** every rule gates on an enabled `OperateParams`; absent
  it, no movement goal is minted and no attr is written
  (`test_default_off_is_byte_identical`, `test_disabled_gate_is_inert`). The seed is
  `self_load_only` → `load_all_seeds` SKIPS it; the two new modules are imported by
  nothing existing.
- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED.**
- **`runners/dsl` diff EMPTY (incl. `term.rs`) — NO Rust.** Only existing DSL Terms
  (`test_seed_uses_only_existing_terms_no_rust`). `source_match = "shared"` (the loaded
  engine is the shared canonical `.so`, md5-identical; the worktree Rust source is
  byte-identical / empty diff). `stale_rust = []`.
- **Vision oracle `bash scripts/rung7_vision_bench.sh`:** BEFORE (at prereg commit)
  **214 passed / 10 skipped / 0 failed**; AFTER **214 / 10 / 0** — identical.
- **`bash scripts/per_area_settlement_regression.sh`:** BEFORE **23 failed / 277 passed
  / 5 skipped**; AFTER identical, SAME 23 failing node ids (enumerated in the run log;
  all pre-existing data-less-environment reds — conversation/topic/gap/cortices tests
  needing `data/` symlinked). NONE touch this block's modules; the seed is
  `self_load_only` (provably cannot affect them).
- **Operate migrated tests:** `tests/test_doom_operate_migrated.py` **7 passed**.

## Honest residuals (named, not patched)

- **Texture-faint doors are invisible to the eye** (sec83 level ~2, sec85 ~2–4): the
  eye correctly does NOT recognise them → n_use = 0 → 0/10 opens on those two. Texture
  alone cannot see every door; the 211000 geometry channel is the complement.
- **Facing/approach-geometry misses at the extremes:** 1/5 on sec69 (blocked at the
  warp point before reaching the door → USE out of range). No mis-fire on a wall.
- **The switch's remote effect is the named follow-on** (0 clean remote opens; faint
  texture + unreachable activation face), per prereg.
- **Fine door-vs-switch label is texture-dominated** (209000): a door surface at
  mid-distance resolves to the fine `switch` prototype (both carry the `use`
  affordance, so USE is unambiguous). Disambiguating door from switch is the
  211000-owned geometry residual.

## Reproduce

```
python3 scripts/build_doom_operate_seed.py            # emit seeds/doom_operate.json
pytest tests/test_doom_operate_migrated.py            # 7 passed (state machine + discipline)
PYTHONPATH=. python3 scripts/doom_operate_run.py      # real-E1M1 opens -> results/doom_operate/gates.json
```
