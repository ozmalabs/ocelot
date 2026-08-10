# PREREG — CLOSING THE 2-D LOOP: 2-D MOTION + 2-D SALIENCE kernels

Committed ALONE, before any confirmatory number, per the discipline in the
task brief and PROTOCOL §0/§8.

## What this rung does

The 2-D expansion (block 166000) made the RETINA, the ONSET events, and the
CARVE 2-D (az×el), but left the MOTION and SALIENCE kernels 1-D — they read
azimuth (`column_index`) only. This rung closes the loop: the whole
event-native pipeline (onset → motion → carve → salience) becomes 2-D.

- **2-D motion** — a NEW Rust `CognitiveTask` kind `retinal_event_motion_2d`
  (NO new DSL Term enum variant; the 1-D `retinal_event_motion` kind is left
  byte-untouched, exactly as 166000 added `retinal_common_fate_carve_2d`
  beside the 1-D carve). It recovers a 2-D velocity `(v_az, v_el)` as the
  least-squares slope of BOTH `col`-on-epoch and `row`-on-epoch from the
  `(col, row, epoch)` onset-event cloud. Payload
  `[n, c_0, r_0, e_0, …, c_{n-1}, r_{n-1}, e_{n-1}]`. Output tuple
  `(v_az, v_el, dir_az, dir_el, speed, residual, coherence, n)` where
  `speed = |(v_az, v_el)|`, `coherence` = the combined multiple-correlation
  `sqrt((s_ec² + s_er²) / (s_ee·(s_cc + s_rr)))` (reduces EXACTLY to the 1-D
  `|Pearson r|` when `s_rr = 0`), `residual` = the unexplained 2-D spatial SSE.

- **2-D salience** — a NEW Rust kind `retinal_residual_salience_2d` (1-D
  `retinal_residual_salience` byte-untouched). Payload identical header to the
  2-D carve: `[n_az, n_el, max_gap, vel_tol, k, c, r, e, …]`. It reduces events
  to one mean epoch per firing CELL, groups cells into 8-connected components
  (the SAME grouping the 2-D carve uses), fits each component's 2-D velocity,
  picks the DOMINANT component (most cells; ties → most events) as the coherent
  background `v_dom`, and per firing cell emits stride-3
  `[fired, raw_salience = |v_comp|, residual_salience = |v_comp − v_dom|]`
  (the 2-D VECTOR-difference norm — the event-native re-expression of the
  157000 egomotion-cancelled residual, now on the az×el field).

- **Graph rules** — `seeds/retinal_motion_2d.json`
  (`retinal_mint_motion_2d`) and `seeds/retinal_salience_2d.json`
  (`retinal_mint_salience_2d`), the 2-D twins of `retinal_motion` /
  `retinal_salience`. Gated by `RetinaMotionParams2d` / `RetinaSalienceParams2d`
  DATA nodes. Python (`domains/photon_eye.py`) is mechanical I/O only:
  `settle_motion_2d` / `settle_salience_2d` pack the event stream,
  `motion_percepts_2d` / `salience_percepts_2d` read percepts back. No decision.

## THE HEADLINE (falsifiable — same shape as the 2-D carve's same-az/diff-el)

**PURE-ELEVATION motion is INVISIBLE to the 1-D motion kernel but the 2-D
kernel RECOVERS it.** A purely vertical mover fires onset events at ONE azimuth
column, rows sweeping over successive epochs. Fed the SAME event set:

- **1-D `retinal_event_motion`** (events collapsed to `(col, epoch)`): all
  events share one column ⇒ zero azimuth spatial spread ⇒ it reports
  **`speed ≈ 0`, `coherence = 0`** — BLIND to the vertical motion.
- **2-D `retinal_event_motion_2d`** on `(col, row, epoch)`: recovers
  **`v_el` with the CORRECT SIGN and MAGNITUDE, `v_az ≈ 0`, `coherence ≈ 1.0`**
  — SEES it.

And a DIAGONAL mover (col AND row both stepping with epoch) → the 2-D kernel
recovers BOTH components (`v_az`, `v_el` both non-zero, correct signs,
`coherence ≈ 1.0`).

For SALIENCE: a scene with a dominant azimuth-sweeping BACKGROUND plus a small,
spatially-separated PURE-ELEVATION mover. The 1-D residual salience (elevation
collapsed) ranks the mover's column at the BACKGROUND level (its vertical
motion contributes nothing to the azimuth-only velocity) — MISSES it. The 2-D
residual salience gives the mover's cells a residual
`|(0, v_el) − (v_az, 0)| = |(v_az, v_el)|` ≫ the background's residual `0` —
RANKS it far above the background. **1-D blind, 2-D sees.**

### Pre-registered QUANTITIES (exact predictions, measured behind controls)

Scene grid `n_az=16 × n_el=12`; noiseless synthetic sweeps (unit step per
epoch); coherence gate `MIN_COHERENCE = 0.5`, event gate `MIN_EVENTS = 2.5`.

| condition | 1-D motion | 2-D motion | predicted |
|---|---|---|---|
| **PURE-ELEVATION** mover (col fixed, rows step +1/epoch) | `speed=0`, `coh=0` | `v_el=+1` (sign +, \|v_el\|≈1), `v_az≈0`, `coh≈1.0` | **1-D BLIND / 2-D SEES** |
| **PURE-AZIMUTH** mover (row fixed, cols step +1/epoch) | `speed≈1`, `coh≈1.0` | `v_az=+1`, `v_el≈0`, `coh≈1.0` | **BOTH SEE** (2-D keeps 1-D case) |
| **DIAGONAL** mover (cols & rows both +1/epoch) | (azimuth only) | `v_az≈1`, `v_el≈1`, both sign +, `coh≈1.0` | **2-D recovers BOTH** |
| **STATIC** (no events) | `0` | `0` | 0 / 0 |
| **SCRAMBLED** epochs | low coh | low coh, no percept | incoherent |

| condition | 1-D residual salience of mover | 2-D residual salience of mover | predicted |
|---|---|---|---|
| **PURE-ELEVATION mover vs azimuth background** | ≈ background level (≈ 0 departure) | ≫ background (≈ `|(v_az,v_el)|`, large) | **1-D MISSES / 2-D RANKS** |

Directional signs are the falsifiable core: a mover stepping rows in the
`+` direction MUST read `v_el > 0`; reverse the sweep and it MUST read
`v_el < 0`. A kernel that reported a magnitude but not the sign would fail.

## Able-to-fail controls (read MEASURED values, not asserted)

1. **PURE-AZIMUTH** → BOTH 1-D and 2-D recover it (2-D does not LOSE the 1-D
   case; `v_el ≈ 0`).
2. **PURE-ELEVATION** → 1-D blind (`coh = 0`) / 2-D sees (`coh ≈ 1`).
3. **STATIC** (no events) → 0 for both.
4. **SCRAMBLED** epochs → coherence collapses; the 2-D motion mint gate
   (coherence > 0.5) suppresses the percept.
5. **SIGN control** → reversing a sweep flips the recovered velocity sign in
   BOTH axes.

## Default OFF / byte-identity (§9)

- The two new kinds are ADDITIVE. The 2-D motion/salience SEEDS + their
  `RetinaMotionParams2d` / `RetinaSalienceParams2d` nodes load ONLY when
  `context["visual_motion"]` / `context["visual_salience"]` is set AND
  `retina_2d` is on. Absent the flags, the 2-D build is byte-identical to the
  166000 2-D-carve build; `settle_motion_2d` / `settle_salience_2d` are no-ops.
- The 1-D `retinal_event_motion` / `retinal_residual_salience` kinds and their
  seeds are byte-untouched — the 1-D motion/salience paths and the 2-D-carve
  path are all byte-unchanged. Proven by the gate + the oracle.

## Oracle (§9) and provenance (§10)

- `bash scripts/rung7_vision_bench.sh` = **0 failed, BEFORE == AFTER** (flag
  off, both sides). BEFORE (this worktree's baseline engine) already measured:
  **214 passed, 10 skipped, 0 failed.** AFTER (this rung's engine, flags off)
  must equal it.
- The gate asserts `engine_provenance()["source_match"] in ("own", "shared")`
  — never a pinned hash. This worktree builds its OWN `_native.abi3.so` via
  `scripts/engine_build.sh` (symlink-safe `cp --remove-destination`); the
  canonical artifact's md5/size/mtime are verified UNCHANGED across every build.

## NO TIMING CLAIM. Seed block: 170000–170999 (FREE).

`python3 scripts/seed_claim.py 170000 170999`:

```
SEED CLAIM 170000-170999: CLEAN -- no collision DETECTED.
  Scope: 868 files with seed sinks; 584 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Not 135000/136000/163000/164000/166000, and not in `VISION_PROTOCOL.md`.

## Gate

`tests/test_2d_motion_salience_migrated.py` — kernel-direct headline (1-D blind
/ 2-D sees, motion + salience), the pure-azimuth and sign controls, static +
scrambled, end-to-end through the REAL 2-D mint rules, default-OFF byte-identity
of the 2-D-carve path, merge-block source audit (settle reads ONLY the event
stream), and §10 provenance.
