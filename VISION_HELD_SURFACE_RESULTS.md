# VISION — HELD SURFACE: the SURFACE-level reconstruction BUILDS, graph-natively (RESULTS)

**Seed block: 180000–180999.** Branch: `worktree-agent-abe2bf48c1c0c0a16`
(isolated worktree off `main` HEAD `e7bb4c684901bb8331859607b27f5f49dffc6943`).
Prereg committed ALONE at `ef0af4eda1b944230309de03847295e5edf70b68` before any
number. Closes residual #1 of block 179000.

## Headline — CONFIRMED, all 9 pre-registered criteria PASS

The persistent held-surface node (`HeldSurfaceCell` per retina cell), updated by
the graph-native EMA rule `held_surface_accumulate` under `run_rules()`, BUILDS a
fixed scene toward an asymptote, sits a clear factor below the stateless
single-tick carve, and FORGETS when the scene moves (a frozen variant stays
stuck). The surface twin of the receptor adapting floor — **graph-data-only, NO
Rust, NO new Term.**

### HEADLINE 1 — the SURFACE builds (fixed scene A, 30 build ticks)

| quantity | value | threshold | pass |
|---|---|---|---|
| `E_acc_A(1)` (blank gist) | 0.849 | — | — |
| `asymptote` = mean E_acc_A(28..30) | **0.0274** | < 0.06 (H1b) | ✓ |
| build drop `asymptote / E_acc_A(1)` | 0.032 (31×) | < 0.15 (H1a) | ✓ |
| monotone violations (slack 0.03) | **0** | ≤ 3 (H1c) | ✓ |
| stateless `E_sl` mean (single-tick carve) | 0.0927 | — | — |
| stateless cv (flatness) | 0.051 | < 0.15 (H1d) | ✓ |
| `E_sl / asymptote` | 3.38 | `E_sl > 2·asymptote` (H1d) | ✓ |
| accumulation gap `asymptote / E_sl` | **0.295** | < 0.5 (H1e) | ✓ |

The held surface EMA-integrates the noisy per-tick observation and temporally
**denoises** it to 0.0274, a 3.4× improvement over the un-accumulated single-tick
carve (0.0927) — a real reconstruction benefit, not an artifact. The stateless
carve is flat (cv 0.051): re-deriving the surface each call never builds.

`E_acc_A` curve: 0.849, 0.722, 0.613, 0.520, 0.441, 0.378, 0.321, 0.273, 0.232,
0.198, 0.168, 0.141, 0.121, 0.103, 0.086, 0.073, 0.063, 0.055, 0.047, 0.043,
0.041, 0.038, 0.035, 0.033, 0.033, 0.030, 0.029, 0.029, 0.027, 0.027.

### HEADLINE 2 — DECAY is real (block MOVES at tick 31; 30 perturb ticks)

| quantity | value | threshold | pass |
|---|---|---|---|
| `E_acc_B(T1+1)` (held still ≈ A) | 1.072 | — | — |
| `tail(E_acc_B)` = mean E_acc_B(58..60) | **0.0306** | < 0.10 (H2a) | ✓ |
| `tail / first` | 0.029 | < 0.4 (H2b) | ✓ |
| `tail(E_frozen_B)` (lr=0 at perturb) | **1.2592** | > 0.5 (H2c) | ✓ |
| decay gap `tail_acc / tail_frozen` | **0.024** | < 0.2 (H2d) | ✓ |

After the bright block moves, the accumulating held surface fades the stale block
and adopts the new one, converging to 0.031 vs `true_B`. The FROZEN variant
(accumulation coefficient ablated to 0 at perturb onset) is stuck at **exactly**
1.2592 on every perturb tick — a flat, wrong line. Persistence is NOT freezing:
object-permanence-WITH-forgetting, at the surface grain, from one EMA rule.

`E_frozen_B` is constant 1.2592 across all 30 perturb ticks (stuck at scene A).

## The mechanism (graph-data-only)

- Seed `seeds/held_surface.json` (id `held_surface`, default-off): a
  `HeldSurfaceCell` node per retina cell + a `HeldSurfaceParams{enabled, lr}`
  config node, and ONE rule `held_surface_accumulate` (order 5).
- The rule matches `retina -has_held_surface_params-> params`,
  `retina -has_column-> column`, `column -rod_receptor-> rod`,
  `column -has_held_surface_cell-> hs`; guard
  `params.enabled==1 AND column.input_epoch > hs.epoch AND
  rod.input_epoch == column.input_epoch` (fresh-guard: fire only after this
  epoch's transduction wrote `caught_quanta`).
- Effect, standard DSL Terms only (`Plus`/`Times`/`Minus`/`Attr`):
  `hs.value ← value + lr·(rod.caught_quanta − value)`. The `run_rules()` fixpoint
  IS the accumulation loop. No Python decision, no Rust built, no new Term/kind.

## Deliverable — the surface splat render sequence

`results/held_surface/` — the SURFACE-level gist→reconstruction (distinct from
179000's floor-field render):
- `frame_t01..t30.png` — build A: blank gist → grounded surface (holes fade).
- `frame_t31..t60.png` — the block MOVES: old block fades, new block grounds.
- `contact_sheet.png` — the full sequence with per-frame E.
- `curves.png` — HEADLINE 1 (build vs stateless) + HEADLINE 2 (decay vs frozen).

## Discipline / provenance

- **Prereg committed ALONE** (`ef0af4ed`) before any number; thresholds analytic.
- **§9 byte-identity:** `git diff --stat e7bb4c6849..HEAD` = the prereg only; every
  other artifact is a NEW file (`seeds/held_surface.json`,
  `scripts/held_surface_measure.py`, `tests/test_held_surface_migrated.py`, this
  doc + prereg, `results/held_surface*`). No existing file touched; the seed is
  additive and default-off (the rule cannot fire without an enabled
  `HeldSurfaceParams`, created only on opt-in). All existing vision gates green.
- **Gate** `tests/test_held_surface_migrated.py` — 3/3, self-contained mechanism
  grain (8×8, 30+25 ticks), able to fail on a flat build or a frozen surface.
- **Oracle** `bash scripts/rung7_vision_bench.sh`: 214 passed / 10 skipped / 0
  failed BEFORE == AFTER (worktree-without-data profile).
- **Provenance (§10):** `source_match = "own"` (ambiguous=false, stale_rust=[]).
- **No Rust built.** Canonical `.so` md5 `417f667716d71ed7d98bae5df25fe9df`
  (mtime Jul 24 17:41:38) UNCHANGED before and after.
- **No timing claim** (deterministic; cost not reported as wall-clock).

## Honest residuals

- The held surface is at 1:1 receptor grain (one `HeldSurfaceCell` per cell). It
  is genuinely a distinct representation from the adapting floor — a persistent
  held BELIEF (object-permanence-with-forgetting, rendered as the reconstruction
  with holes) versus the floor's fast internal gain reference — but a COARSER
  pooled surface grain (a `HeldSurfaceCell` over a KxK receptor block) is deferred
  (the multi-receptor pool risks the known same-type-incoming-edge matcher gotcha
  and was kept out for robustness).
- The observed surface drive is the rod `caught_quanta`; numerically the held
  surface parallels the floor's `adaptation` when `lr == adapt_rate` (the "surface
  twin" by design). The genuine additions are the first-class PERSISTENT held
  surface (the stateless carve had none), its denoising gap over the single-tick
  carve, and the demonstrated decay/forgetting — none of which the re-derived
  surface carve provided.
- Perturb is a block MOVE (fade old + adopt new); a pure removal and a brightness
  ramp are equally handled by the same EMA but not separately gated.
