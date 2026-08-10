# ls20 LIVE BENCHMARK — pre-registration (rung 219000)

**Posture:** the FIRST LIVE measurement of the ls20 stack against the REAL
ARC-AGI-3 game (`https://three.arcprize.org`, game `ls20-9607627b`) via the
public-preview API. 216000 (pixel eye), 217000 (transform bridge) and 218000
(salience/investigation/curiosity-first planner) proved the MECHANISM on OFFLINE
and SYNTHETIC ls20-SHAPED scenarios. This rung measures the stack on the REAL
game — EXPECTING A PARTIAL RESULT and reporting it STRAIGHT.

**This is a MEASUREMENT rung. Canonical UNCHANGED.** No Rust build, no new seed,
no adapter decision logic. The runner + world adapter that already exist
(`scripts/arc_run.py`, `worlds/arc.py`, `scripts/arc3_live_env.py`) are run live;
a new measurement harness (`scripts/arc_ls20_live_measure.py`) pulls real frames
and grades perception. All DECISIONS stay graph-native (218000 rules); the adapter
does live API I/O + mechanical perception only.

**Seed block:** `SEED CLAIM 219000-219999: CLEAN -- no collision DETECTED.`
(`python3 scripts/seed_claim.py 219000 219999`, exit 0.)

**Engine:** NO Rust build. Canonical `.so` md5 **`793ce09ed498a749abb79aeaea44b92e`**,
`term.rs` + whole `runners/dsl` diff EMPTY, `source_match` reported in RESULTS.

**Key/auth (worktree gotcha handled):** `ARC_API_KEY` read via
`scripts/_arc3_load_key.py` from the ABSOLUTE `/home/matt/ozma/internal/.env`
(the loader already uses the absolute path — no relative-parent miss). A
connectivity/auth check (open scorecard + RESET ls20) is run BEFORE any
measurement; if the API is unreachable / key rejected / rate-limited, STOP and
report that straight — NEVER fabricate a number.

## The two measurements (registered)

### G-perceive-real (the load-bearing headline)

Does the 216000 pixel eye segment the REAL live ls20 64×64 frame? The 216000
envelope was measured on OFFLINE + SYNTHETIC ls20-shaped grids; this measures it
on REAL live frames pulled from the API.

- **Corpus:** N real live ls20 frames (a bounded live episode: RESET + a cycle of
  the server-legal directional actions). The API returns the SYMBOLIC 64×64
  integer grid — this is the SCORING ORACLE ONLY; it is NEVER fed to the pixel
  perception path.
- **Pipeline (unchanged from 216000):** for each real frame,
  `_render_screen(grid)` → RGB pixels → `recover_grid_from_render` (palette-
  quantize + lattice-register, PIXELS ONLY) → cv2 4-conn carve on the RECOVERED
  grid. ORACLE carve = the same cv2 carve on the symbolic grid.
- **Metric:** per-Region position-set IoU (best match) + matched-Region fraction
  (best IoU ≥ 0.5) + exact-grid-recovery frames, pooled over the real frames,
  Wilson/normal CIs. PLUS the Gaussian-noise degradation sweep (σ = 2,4,8,16,24,
  32,48) on the REAL frames — locating where perception breaks on real content,
  vs the 216000 synthetic envelope (parity held to σ=16, fell by σ=32).
- **HONEST CAVEAT (pre-stated):** `_render_screen` is a LOSSLESS block render
  (cell_px=3 at 64×64, solid palette blocks, no anti-aliasing), so a correct
  pixel→grid recovery reproduces the oracle grid EXACTLY → clean-render parity is
  near-1.0 BY CONSTRUCTION, even on real frames. The VALUE of the clean number is
  (a) the source-audit (perception reads ONLY pixels), (b) that it now holds on
  REAL frame CONTENT (dense, real palette usage — far richer than the synthetic
  corpus), (c) the degradation envelope on real frames. The real anti-aliased
  BROWSER render is genuinely unavailable through the API (the API returns
  symbolic grids, not pixels); the Gaussian sweep stands in for render
  degradation. If perception breaks, report WHERE (palette quantization / lattice
  registration / sub-cell bleed) and NAME the fix as a perception follow-on rung.

### G-benchmark (the real number)

Run the EXISTING `arc_run` stack (218000 planner, oracle-grid perception) live on
a BOUNDED number of ls20 actions/episodes; report the ACTUAL score
(`levels_completed`) / win state from the live frames + the server scorecard.

- **What is wired:** `arc_run.py`'s live loop — the 218000 salience/investigation/
  curiosity-first planner over the ORACLE grid perception path (`sub.arc3_grid` →
  `_perceive_regions` cv2 carve). This is the canonical live runner.
- **What is NOT wired (named-next, honest):** the pixel_eye (216000) is NOT in
  arc_run's live loop — it reads the oracle grid; wiring `recover_grid_from_render`
  into the live perceive path is a named follow-on. The 217000 transform bridge
  (`cells_to_signature` / ShapeDecode) is available as a decode primitive but its
  integration into the live ls20 action loop (multi-step transform composition)
  is NOT the driver of arc_run's action choice — arc_run drives navigation, not
  transform-composition. State exactly what solved and which NAMED gap each
  unsolved episode hit (multi-step transform composition / wall routing / fog
  exploration / an unmodelled mechanic).
- **Bounded:** ≤ ~2 episodes, ≤ ~60 actions each, to respect API quota — enough
  for a first number, not a marathon.

## HONESTY (the whole point)

This is the FIRST live number. The current stack handles ONE mechanic on simple
scenarios; real ls20 is likely harder (multi-step, walls, fog, more mechanics).
EXPECT A PARTIAL RESULT. Do NOT claim "solved ls20." The honest deliverable is
"the first real ls20 measurement + where the frontier is." A low-but-honest number
that names the frontier is the valid landing; a fabricated or cherry-picked number
is a firing offence.

## Pre-registered reporting (BEFORE the run)

RESULTS.md will report, unconditionally: prereg SHA; key-loaded + API-reachable
confirmation; the perceive-on-real-render number (mean per-Region IoU + matched
fraction + exact-grid frames on real frames) AND the degradation envelope (+ where
it breaks); the live solve rate / score breakdown per episode (which solved, which
gap); what is wired vs named-next; canonical md5; term.rs + runners/dsl diff-empty;
`source_match`; honest residuals. No number is quoted without its condition.
