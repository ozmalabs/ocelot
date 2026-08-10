# VISION — STALENESS DECAY: RESULTS (seed block 196000)

*Prereg `VISION_STALENESS_DECAY_PREREG.md` (committed ALONE at `ae385b1847`,
before any measurement). Branch `worktree-agent-a57d2f54374965fd8` off `main`
HEAD `4d97f51903`. Engine canonical `793ce09ed498a749abb79aeaea44b92e`
(UNTOUCHED — this rung adds NO Rust; `term.rs` diff EMPTY). Raw numbers in
`results/staleness_decay.json`; renders in `results/staleness_decay/`.*

## Headline

A **shared, generic integer-half-life decay primitive** landed
(`seeds/staleness_decay.json`), of which the held surface is the FIRST consumer.
`freshness = Ashr(C0, IDiv(now_epoch − last_refresh_epoch, half_life))` — the
integer-exact `×2^−k` (`scale2`) atom read on the per-sensor epoch axis. Surprise
(the order-0 residual against the held prediction) sets `half_life` inversely, so
over ONE held belief a **static cell denoises (density accrues) while a moving
cell refreshes (adopts, not smears)** — density and latency DECOUPLE. **13 of 14
pre-registered gates pass; G6 (power-law) is the honest partial/null the prereg
registered as acceptable.** NO Rust, default-OFF byte-identity held, canonical
`.so` untouched.

## The loop, as built (held → predict → order-0 residual → refresh → decay)

Four rules in `seeds/staleness_decay.json`, area `retina`, gated on
`HeldDecayParams.enabled`, driving the block-180000 `HeldSurfaceCell`:

1. `sd_residual` (order 0) — the reflex read: `residual = Abs(IDiv(caught,1) −
   IDiv(value,1))`, the order-0 INTEGER surprise against the held prediction
   (both operands floored to i64, so integer-native AND sustained until adopted).
2. `sd_gate` (order 1) — `half_life = Max(hl_min, IDiv(hl_scale, residual+1))`
   (reciprocal of surprise); the innovation clock resets `last_refresh_epoch` to
   `now` only when CONFIRMED (`residual < refresh_thresh`).
3. `sd_freshness` (order 2) — THE DECAY LAW:
   `freshness = Ashr(C0, IDiv(now − last_refresh_epoch, half_life))`.
4. `sd_blend` (order 4) — precision-weighted Kalman update:
   `gain = lr_min + (1−lr_min)·(C0−freshness)/C0`, `value += gain·(caught−value)`.
   `sd_flag_stale` (order 3) — SECOND consumer: `needs_attention = [freshness <
   attn_thresh]`.

Constants: `C0=1024 (2^10)`, `lr_min=0.15`, `hl_scale=hl_min-clamped, hl_min=1`,
`refresh_thresh=32`, `attn_thresh=768`. Scene: 16×16, a persistent fine-texture
STATIC patch (rows 0–7) + a bright block (L 200 on 20) that JUMPS every P=15
ticks across the moving band (rows 8–15), T=90 ticks, Poisson shot noise, seeded
196000.

## Gate results

| gate | claim | result | numbers |
|---|---|---|---|
| **G1a** | static density climbs with dwell | **PASS** | `E_static` gated 0.282 → **0.026** (~11× denoise) |
| **G1b** | moving latency FLAT | **PASS** | latency `[1,1,1,1,1]`, slope **0.0**, cv 0.0 |
| **G1c** | DECOUPLING dominates the fixed-lr trade | **PASS** | gated (E=0.026, L=1) matches best denoiser lr=0.15 (E=0.022) AND best adopter lr=0.9 (L=1); neither control gets both (lr=0.9 E=0.075 > 2·0.022; lr=0.15 L=13 > 2·1) |
| **G2a** | blend keys off `freshness` | **PASS** | pin freshness≡C0 → L=**13** (smears; > 2·1) |
| **G2b** | foveation keys off `freshness` | **PASS** | at jump tick: **98.5%** of flagged cells in moving band, **0.8%** of static flagged |
| **G2c** | decay is graph-resident (source audit) | **PASS** | no Python `set_attr` of any decay-bookkeeping key; rule `sd_freshness` owns the `freshness` write |
| **G3a** | uniform-LONG half_life SMEARS | **PASS** | L=**13** (> 2·1) |
| **G3b** | uniform-SHORT half_life kills density | **PASS** | `E_static`=**0.083** (> 2·0.026) |
| **G3** | falsifier: BOTH horns diverge | **PASS** | uniform decay cannot get both — the surprise→half_life coupling is load-bearing |
| **G4a** | identical machinery, 2nd quantity | **PASS** | both freshness rules' op tree = `Ashr(Attr,IDiv(Minus(Attr,Attr),Attr))` |
| **G4b** | DecayTrace halves integer-exact | **PASS** | freshness `[1024,1024,1024,1024,512,…,256,…]` == `C0>>(Δ//4)` exactly |
| **G5a** | decay bookkeeping is INTEGER | **PASS** | **0** non-integer cells across the whole run (residual/half_life/freshness/last_refresh) |
| **G5b** | only the cross-frame blend is float | **PASS** | `sd_freshness/gate/residual` use only `Ashr/IDiv/Minus/Max/IfThenElse` (integer); `sd_blend` alone uses `Div/Times` (cross-frame) |
| **G6** | emergent power-law (secondary) | **NULL (honest)** | log-log slope **−0.74** (in predicted −0.7…−1.1) but R²_power **0.88** < R²_exp **0.955** over the discrete 12-cohort window — approximately power-law, not CI-separated from exponential here |

## First-classness (the Hyrum's-Law point)

`freshness` (and `last_refresh_epoch`, `half_life`, `residual`) are EXPLICIT typed
`HeldSurfaceCell` attributes, written ONLY by the seed rules and read ONLY via
`Attr` by two independent downstream consumers: the precision-weighted blend
(`sd_blend`) and the foveation flag (`sd_flag_stale`). Ablating the exposed
freshness (pin ≡ C0) demonstrably breaks the blend (moving content smears, L
1→13). The decay is graph data governed by the admissibility grammar and visible
to the agent's own self-improvement loop — not a hidden engine internal.

## The falsifier (non-vacuity)

Killing the surprise→half_life coupling (uniform decay) breaks an observable BOTH
ways: uniform-LONG never lets freshness collapse → moving content smears (L=13);
uniform-SHORT always collapses freshness → static never denoises (E=0.083). A
uniform decay CANNOT get both; the coupling is load-bearing. (The fixed-lr
controls are the same lesson from the incumbent's side: lr=0.15 denoises but
smears, lr=0.9 adopts but never denoises.)

## Genericity + the existing-decay audit (the re-scope)

**One primitive, two consumers.** The identical `Ashr(C0, IDiv(now −
last_refresh, half_life))` op tree decays both the held-surface value and a
synthetic `DecayTrace` (a salience-like quantity) — same representation, same
machinery, proven byte-structurally identical (G4a) and integer-exact (G4b).

**Existing-decay audit** (`results/staleness_decay.json → existing_decay_audit`):

| decay | form | classification | disposition |
|---|---|---|---|
| rod light adaptation (`photon_retina`) | `adaptation += adapt_rate·(caught−adaptation)` EMA | **AD-HOC FLOAT** | FOLLOW-ON (fused Naka-Rushton hot path in `cognitive_tasks.rs`; not a rule; not a byte-clean swap) |
| held-surface value EMA (`held_surface_accumulate`) | `value += lr·(caught−value)` EMA | **AD-HOC FLOAT** | SUPERSEDED-IN-VARIANT (this rung's precision blend reads integer freshness; base rule retained as the control) |
| residual salience (`residual_salience`) | recomputed per pass | not a temporal decay | N/A (stateless recompute) |
| onset refractory (`onset_refractory_epochs`) | integer-epoch window | already integer-epoch | OK |
| **shared staleness freshness (THIS RUNG)** | `Ashr(C0, IDiv(Δepoch, half_life))` | **INTEGER-HALF-LIFE (scale2 on epoch)** | THE PRIMITIVE |

After this rung the substrate has ONE decay primitive with a KNOWN set of
not-yet-migrated float consumers (rod adaptation; the base held-surface EMA) — a
named follow-on list, not a zoo. Neither float decay is a byte-clean swap (both
change behaviour), so neither is migrated here (that would need its own rung).

## Integer-native audit (G5)

Every value of `{residual, last_refresh_epoch, half_life, freshness}` across the
full 90-tick run is integer-valued (`0` violations). The freshness/gate/residual
rules use ONLY integer Terms (`Ashr, IDiv, Abs, Minus, Plus, Max, IfThenElse,
Lt, Eq`); `Ashr` (arithmetic shift-right = integer `÷2^k`) IS the substrate's
integer-exact `scale2` on the epoch axis. The ONLY float-producing rule is
`sd_blend` — the precision-weighted held-vs-new blend — which is a cross-frame map
(temporal denoising / precision weighting) and float there is admissible by the
integer ontology ("in-frame is integer; the continuum lives in the map").

## Power-law (G6) — honest partial

The aggregate forgetting of a heterogeneous-half-life surface (12 cohorts,
half-lives 1…64, all refreshed then frozen) has log-log slope **−0.74** (squarely
in the pre-registered −0.7…−1.1 band) and a high power-law fit (R²=0.88), but a
single exponential fits marginally better (R²=0.955) over this DISCRETE 12-cohort
Δ=1…128 window. Registered as a valid null. The Wixted/Anderson superposition→
power-law result is for a CONTINUOUS log-uniform mixture; a denser continuous
mixture is expected to sharpen it — a named follow-on, NOT run here (tuning the
cohort set post-hoc to flip a secondary gate would be p-hacking).

## Discipline

- **Prereg committed ALONE** (`ae385b1847`) before any number.
- **NO Rust; `term.rs` diff EMPTY** — `Ashr/IDiv/Abs/IfThenElse/Max` all
  pre-existed. Canonical engine `793ce09ed498a749abb79aeaea44b92e` verified
  UNTOUCHED before and after; no build performed. `source_match` = own
  (worktree native, Rust source byte-identical to canonical).
- **DEFAULT-OFF byte-identity (C1):** the seed is additive + `self_load_only`,
  in no default eye seed list. Oracle `bash scripts/rung7_vision_bench.sh`
  BEFORE = **214 passed / 10 skipped / 0 failed, exit 0** (data-less worktree);
  AFTER = **214 passed / 10 skipped / 0 failed, exit 0** — BEFORE == AFTER.
  `held_surface.json` UNTOUCHED (`test_held_surface_migrated.py` 3/3).
- **Engine-semantics gate set** (unchanged — no engine edit): held_surface +
  `incremental_match, empty_match_proof, dirty_precision, per_sensor_epoch,
  per_area_settlement, predicate_retraction, eye_binding_projection` =
  **71 passed / 0 failed**.
- Gate `tests/test_staleness_decay_migrated.py` **7/7** (runs the measure; able
  to fail on a flat static curve, a growing latency, a non-diverging falsifier,
  a float in the decay bookkeeping, or non-identical machinery).
- NEW FILES ONLY: `seeds/staleness_decay.json`, `scripts/staleness_decay_measure.py`,
  `tests/test_staleness_decay_migrated.py`, `tools/build_staleness_decay.py`,
  the prereg, this doc, `results/staleness_decay*`.

## Implementation note (honest deviation from the prereg's rule-order sketch)

The prereg sketched `sd_blend` at order 3 and `sd_flag_stale` at order 3. In
practice `sd_blend` advances `hs.epoch` (closing the shared fresh-guard), and the
engine's within-fixpoint order handling let that race the flag rule. Fixed with
NO threshold change: `sd_blend` moved to order 4, and `sd_flag_stale` — a pure
READER of `freshness` — is guarded on `enabled` only (not the epoch fresh-guard),
so it recomputes idempotently and cannot race the epoch advance. This is a
mechanism-hygiene refinement, not a gate change.
