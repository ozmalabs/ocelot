# ls20 LIVE BENCHMARK — RESULTS (rung 219000)

**The first live number.** The ls20 stack (216000 eye + 217000 transform + 218000
planning) run against the REAL ARC-AGI-3 game `ls20-9607627b` via the public API.
PARTIAL result, reported straight: **perception on real frames survives to the
palette half-step (clean IoU 1.0, cliff at σ=24); live solve rate 0/7 levels in
2 bounded episodes.** Do NOT read this as "solved ls20" — it is "the first real
ls20 measurement + where the frontier is."

- **Prereg:** `LS20_LIVE_PREREG.md`, committed SHA **`f5cdcbd8d705a8cbafd09b8d307c5f9257127973`**
  (blob `925aaf409184cd8aed07e0a10971ca263f841ccc`).
- **Seed block:** `SEED CLAIM 219000-219999: CLEAN -- no collision DETECTED.` (exit 0).
- **Canonical `.so` md5:** `793ce09ed498a749abb79aeaea44b92e` — UNCHANGED (loaded
  native is byte-identical; `import substrate_rs` resolves the worktree copy).
- **Engine:** `term.rs` diff EMPTY, whole `runners/dsl` diff EMPTY (vs main),
  NO Rust build. `source_match = own` (engine `04c9d28e316d`).

## Key / auth / connectivity (verified BEFORE any measurement)

- `ARC_API_KEY` loaded via `scripts/_arc3_load_key.py` from the ABSOLUTE
  `/home/matt/ozma/internal/.env` (the loader already uses the absolute path — the
  worktree relative-parent miss does not apply). Key present, 36-char UUID.
- **API reachable, auth accepted:** `POST /api/scorecard/open` + `POST
  /api/cmd/RESET` on `ls20-9607627b` returned a live 64×64 frame,
  `state=NOT_FINISHED score=0`, `available_actions=[ACTION1..4]`, guid set. No
  number below is fabricated — every figure is from a live response.

## G-perceive-real (the load-bearing headline) — REPLICATES on real frames

The 216000 pixel eye (`_render_screen` → `recover_grid_from_render`, PIXELS ONLY;
the symbolic grid is scoring-oracle only, never fed to perception) run on **32 REAL
LIVE ls20 frames** (`scripts/arc_ls20_live_measure.py`, `results/arc_ls20_live_live.json`).

**Real frame content (much richer than the 216000 synthetic corpus):** every
frame **4093 / 4096** cells non-empty; palette values seen `{0,1,3,4,5,8,9,11,12}`
— dominated by value 4 (`#333`, 2609 cells) and value 3 (`#666`, 892 cells), two
ADJACENT grey-ramp entries. 671 oracle Regions across the 32 frames.

| condition (real live frames) | mean per-Region IoU | matched-Region fraction | exact-grid frames |
|---|---|---|---|
| **CLEAN render (headline)** | **1.0000 [1.0000, 1.0000]** | **1.0000 [0.9943, 1.0000]** | **32 / 32** |
| + Gaussian σ=2  | 1.0000 | 1.0000 | 32/32 |
| + Gaussian σ=8  | 1.0000 | 1.0000 | 32/32 |
| + Gaussian **σ=16** | **1.0000** | **1.0000** | **32/32** |
| + Gaussian σ=24 | **0.0002** | **0.0000** | **0/32** |
| + Gaussian σ=32 | 0.0002 | 0.0000 | 0/32 |

Round-trip exact inverse on the live frames: **True**.

**What this establishes, honestly:**

1. **Clean-render parity is near-1.0 BY CONSTRUCTION** (`_render_screen` is a
   LOSSLESS block render, cell_px=3 at 64×64, no anti-aliasing). This is stated,
   not hidden. Its VALUE is that it now holds on **REAL, dense live content** (671
   regions, 4093/4096 cells) — not just the synthetic ls20-shaped corpus — while
   reading **only pixels** (source-audit below), and that it locates the frontier.
2. **The 216000 σ-envelope REPLICATES: parity holds to σ=16, breaks by σ=24.** The
   pre-registered 216000 claim (parity to σ=16) is confirmed on real frames.
3. **On real frames the break is a CLIFF (σ=24 → ~0), sharper than the synthetic
   envelope** (216000 synthetic σ=24 → 0.59). **WHERE it breaks and WHY:** the real
   ls20 field/rooms pack the two ADJACENT grey-ramp entries `#333`(51) and
   `#666`(102) — a palette step of only **51 grey levels**. Once Gaussian σ crosses
   ~half that step (~25), pixels flip `#333↔#666` across the WHOLE dense field at
   once, so every region shatters simultaneously — a cliff, not a slope. The
   synthetic corpus degrades gently because its regions are more separable in
   palette space. **The robustness margin on real ls20 content is exactly the
   palette half-step, no more, because the content is dense adjacent-greys.**

**NAMED perception follow-on (not this rung):** the real anti-aliased BROWSER
render is genuinely unavailable through the API (it returns symbolic grids, not
pixels), so the Gaussian sweep stands in for render degradation. The frontier the
cliff locates is **adjacent-grey disambiguation**: anti-aliasing that blends
`#333`/`#666` at wall/room boundaries lands right at this σ≈24 margin. The fix is a
palette-step-aware / edge-context-primed recovery (majority-vote already carries
the clean case; adjacent-grey boundary bleed needs a context prior) — a perception
rung, not this measurement.

**Source-audit (seeing-not-oracle):** the pixel path derives the value grid ONLY
from render pixels (`recover_grid_from_render` reads `screen`, never `arc3_grid`);
the symbolic grid is read ONLY by the grader (`carve` on the oracle). This rung
adds no adapter perception switch — it is a pure measurement harness over the
existing 216000 `_render_screen`/`recover_grid_from_render` pair.

## G-benchmark (the real number) — 0 / 7 levels, honest gap named

The EXISTING `arc_run.py` stack (218000 salience/investigation/curiosity-first
planner, **ORACLE-grid** perception) run live on ls20, two bounded episodes:

| episode | actions | levels_completed | win | over | scorecard score |
|---|---|---|---|---|---|
| A | 60 | **0 / 7** | no | no | 0.0 |
| B | 45 | **0 / 7** | no | no | 0.0 |

Server scorecard (episode B): `level_actions=[45,0,0,0,0,0,0]`,
`level_baseline_actions=[22,123,73,84,96,192,186]`, `level_scores=[0,…]`,
`levels_completed=0`, `state=NOT_FINISHED`. **Level 1's baseline is 22 actions; the
agent spent 45–60 and completed 0.**

**The agent is NOT blind — it perceives and navigates.** It self-reports (via its
own language faculty) a coherent world model: 19–23 Features (kinds
`{static:16-17, meter:2-4, mover:1-2}`), latches a blue "control" token as the
avatar (slides 5 cells/press), reads a yellow "counter" (the depleting meter), and
names a red goal square, mid/dark-grey rooms/walls. It cycles nav modes
(`frontier_seek` / `mover_avoid` / `pocket_escape`) and the avatar does move
between rooms.

**Why it does not solve — NAMED gaps (each unsolved for a specific reason):**

1. **Win-condition binding is missing (primary gap).** The planner pursues
   *unexplored cells* (curiosity/frontier-first: "Heading to unexplored cell
   @(50,29)") rather than routing to the *goal object it already perceives* ("Red
   square stays"). 218000 validated goal-PURSUIT on SHAPED scenarios where the goal
   station was the explicit target; on the real game nothing grounds the red
   square / meter-completion as THE objective, so the agent explores instead of
   solving. This is the top lever.
2. **Coarse nav quantization + sticking.** The nav map reads `explored 3 / 100`
   (a 10×10 coarse flood) and the avatar repeatedly registers `slideNone` (pressed,
   didn't move — walls) and drops into `pocket_escape`. Map coverage never grows
   past ~3 %, so even frontier exploration barely progresses.
3. **The ls20 mechanic itself is unmodelled.** 7 levels with rising baselines
   (22→192 actions) imply a multi-step lock/route mechanic; the stack has the
   NAVIGATION mechanic (216000/218000) but not ls20's specific win rule (multi-step
   transform composition / switch sequence / fog), so it cannot compose the solve.

**What is wired vs named-next (honest):**

- **WIRED, live, driving actions:** the 218000 planner over the ORACLE-grid
  perception path (`sub.arc3_grid` → `_perceive_regions` cv2 carve) — the canonical
  `arc_run` runner. Perception, avatar-latch, nav-mode selection, self-report are
  all live and graph-native.
- **NOT wired (named-next):** (a) the **pixel_eye** (216000) is measured OFF-loop
  here — `arc_run` reads the oracle grid, not `recover_grid_from_render`; wiring the
  pixel path into the live perceive loop is a follow-on. (b) The **217000 transform
  bridge** (`cells_to_signature` / ShapeDecode) exists as a decode primitive but is
  NOT the driver of `arc_run`'s action choice — arc_run drives navigation, not
  transform-composition; binding transform-composition to the ls20 win condition is
  the multi-step-mechanic follow-on. (c) **Goal-grounding of the perceived red
  square / meter** as the objective (gap 1) is the single highest-value next rung.

## Engine / provenance / regression

- Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` — UNCHANGED.
- `term.rs` diff EMPTY; whole `runners/dsl` diff EMPTY (`git diff main -- …`).
- `source_match = own`, engine `04c9d28e316d`, loaded native path is the worktree
  copy (byte-identical to canonical).
- No seed added, no rule changed, no adapter decision added. Two NEW files only:
  `LS20_LIVE_PREREG.md` and `scripts/arc_ls20_live_measure.py` (a measurement
  harness reusing the 216000 grader); `results/arc_ls20_live_live.json` written.

## Honest residuals

- **Clean-render parity is by construction** (lossless block render) — NOT a novel
  mechanism; the novelty is the live-content replication + the real-content cliff
  + the source-audit. Stated plainly, not headlined as a perception advance.
- **The real anti-aliased render is unavailable** via the API; the Gaussian sweep
  is a stand-in. The σ≈24 cliff LOCATES the frontier but does not measure the
  browser's actual AA directly.
- **Benchmark is 2 episodes, ≤60 actions each** — CI-grade, deliberately bounded
  for quota; it is a floor, not a saturated estimate. The agent is deterministic
  enough that both episodes read 0/7 identically.
- **Solve rate 0/7 is real** — the stack navigates but does not close ls20's win
  condition. The valid landing is naming that frontier (win-condition grounding >
  nav quantization > mechanic model), not a solve number.
