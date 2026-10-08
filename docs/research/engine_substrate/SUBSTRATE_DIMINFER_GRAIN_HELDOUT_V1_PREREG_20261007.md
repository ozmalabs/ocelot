# Held-generator grain ladder: held-out confirmation — preregistration (2026-10-07)

Confirms the exploratory tranche 2 gate 4 result: `diminfer_grain_omniglot_v1`, where 53/100 jittered cases were recognised versus 0/100, with 0/100 cross-character false recognitions. That run's grain range, [0,1,2], was chosen using the same 20 drawings. This run fixes everything in advance and uses drawings never used before.

## Frozen before capture

- **Mechanism:** the current tree. `shape_decode_loop` sets `agent.dim_grains=[0,1,2]` in the ladder arm and leaves it absent in the off arm.
- **Data:** `data/omniglot/strokes_evaluation`, a disjoint alphabet set never used in tranches 1–2. Take the first 20 alphabets by name, the first character of each, and drawers 1 and 2 (`*_01`, `*_02`).
- **Rendering:** identical to v1 (16×16, `raster()` from `geninfer_grain_ladder_omniglot_v1.py`). Jitter is ±0.35 cell, seed 20261008.
- **Held maps:** rot90, rot180, rot270, refl_r, refl_c.
- **Conditions per (character, map):**
  - exact: `M·A₁`
  - jitter: `M·A₁′`
  - drawer: `M·A₂`, a different person's drawing of the same character (new, harder; reported only)
  - cross: `M·B₁`, character i+7

Recognition means status `recognized_transformed` with `covered_by` equal to the base. The base is `A₁`.

## Gates

- **H1:** jitter recognition, ladder − off ≥ 25/100. The lower 95% Clopper–Pearson bound on the ladder rate must exceed the off rate.
- **H2:** cross-character false recognitions with the ladder: 0/100. The upper 95% bound is reported.
- **H3:** exact recognised 100/100 in both arms, all at grain 0.

Reported, not gated: drawer recognition, the grain distribution, and median closure time.
