# VISION — STALENESS DECAY: the shared integer-half-life decay primitive; the held surface DECOUPLES density from latency (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Branch `worktree-agent-a57d2f54374965fd8`, isolated worktree off
`main` HEAD **`4d97f51903`** (LEDGER 195000 — SHIP THE LINEAR EYE). Engine
canonical **`793ce09ed498a749abb79aeaea44b92e`** (`libsubstrate_rs.so`, shared
build, Rust source byte-identical to this worktree — this rung adds **NO Rust**,
`term.rs` diff EMPTY). Seed block **196000–196999**.*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 196000 196999
SEED CLAIM 196000-196999: CLEAN -- no collision DETECTED.
  Scope: 895 files with seed sinks; 609 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. The idea — decouple the eye's two timescales

The held surface (block 180000) accumulates a per-cell denoised super-resolution
belief `value` via a FIXED-rate EMA (`held_surface_accumulate`, `lr` constant).
A fixed rate FORCES A TRADE: low `lr` denoises a static region deeply but SMEARS
a moving edge (adopts new content over ~`1/lr` ticks); high `lr` adopts motion
fast but never denoises. Density (accumulated detail) and latency (time to adopt
change) are COUPLED through the one rate. This rung DECOUPLES them:

- **The held surface that has not decayed IS the accumulated super-resolution =
  the PREDICTION.**
- **The new frame is read at ORDER-0 as the RESIDUAL against that prediction** —
  the cheap, low-latency reflex read. The residual (surprise) does THREE jobs
  with one computation: it is the fast response, it marks where the held
  super-res went stale, and it gates the refresh.
- **`decay ∝ surprise`, per cell**, is the arbiter: a static cell (low residual)
  keeps a LONG half-life → its freshness persists → its blend gain stays low →
  it keeps denoising (density accrues). A moving cell (high residual) gets a
  SHORT half-life → its freshness collapses in a few ticks → its gain rises →
  it ADOPTS the new content (refreshed, not smeared). One cell can denoise while
  its neighbour refreshes, over ONE held belief.

## 1. THE DECAY LAW — pinned, integer-native, and SHARED (the re-scope)

Integer half-life is **not** this rung's bespoke law — it is the substrate's
UNIVERSAL decay, forced by the integer ontology. `2^(-k)` is the only decay that
is BOTH memoryless (loss depends on the current amount, not history) AND
integer-exact (halving an integer is exact; `e^(-λ)` is not). Non-exponential
forgetting (power-law) is a SUPERPOSITION of these atoms at different half-lives
(the Wixted/Anderson resolution). So this rung builds **ONE shared, generic
decay primitive that any decaying quantity uses**; the held surface is the FIRST
consumer, not the owner.

**The primitive — one representation, keyed on any epoch axis:**

- `last_refresh_epoch` — integer, the epoch this quantity was last confirmed
  fresh (an innovation clock).
- `half_life` — integer epochs, set INVERSELY by surprise.
- `freshness` — integer, DERIVED and first-class:
  ```
  Δepoch   = now_epoch − last_refresh_epoch                 (Minus; integer, unbounded frame index)
  k        = IDiv(Δepoch, half_life)                        (integer floor; both ≥ 0)
  freshness = Ashr(C0, k)                                   (integer-EXACT ×2^−k; C0 = 1024 = 2^10)
  ```
  `Ashr` (arithmetic shift-right = integer `÷2^k`) IS the substrate's
  integer-exact `scale2` read on the epoch axis — the halving atom the
  shape-decode `scale2` generator (block on "a base IS a dimension") is the
  multiplicative twin of. Freshness is a bounded integer in `[0, C0]` that halves
  every `half_life` epochs and floors at 0 (`Ashr(1024, k≥10) = 0`).

**`now_epoch` is the per-sensor epoch (block 188000)** — the eye's
`column.input_epoch` (the same axis `held_surface_accumulate` fresh-guards on).
The primitive is agnostic to WHICH epoch axis; that is what makes it shared.

**`half_life ← Max(hl_min, IDiv(hl_scale, residual + 1))`** (integer; a true
reciprocal of surprise). With `hl_scale = 256`, `hl_min = 1`: residual 0 → 256
(effectively never decays), residual ~4 (shot noise) → ~51 (long — static
denoises), residual ~180 (a block arrives/leaves) → 1 (short — refreshes). This
is `decay ∝ surprise`, integer.

**Refresh = Kalman innovation.** `last_refresh_epoch` is reset to `now_epoch`
when the surprise is LOW (`residual < refresh_thresh` — the estimate is
CONFIRMED, mark it fresh now, Δepoch→0, freshness→C0). When surprise stays HIGH,
`last_refresh_epoch` is NOT reset → Δepoch grows → freshness decays at the (short)
half-life → the blend weights the observation more → the cell adopts. Sustained
innovation erodes the held precision; confirmation restores it. That is the
precision-weighted (Kalman) gate.

**The held-vs-new blend is PRECISION-WEIGHTED by freshness (the cross-frame map
— float admissible here, integer ontology honoured):**
```
staleness = C0 − freshness                                 (integer)
gain      = lr_min + (1 − lr_min)·Div(staleness, C0)        (FLOAT, cross-frame blend weight ∈ [lr_min, 1])
value'    = value + gain·(caught_quanta − value)            (FLOAT — the denoised super-res estimate is a refinement/cross-frame quantity)
```
Fresh cell (staleness 0) → `gain = lr_min` (deep denoise). Fully stale cell
(staleness C0) → `gain → 1` (snap/adopt). `value` and `gain` are the ONLY floats,
and they are cross-frame by construction; ALL decay bookkeeping is integer (§Gate 5).

**Integer ontology, stated as the decision rule:** the decay bookkeeping
(`last_refresh_epoch`, `half_life`, `freshness`, `residual`, `Δepoch`, `k`) is
BETWEEN a frame and its successor via the integer frame index — but is itself a
count and MUST be integer. The blend value/gain is a cross-frame map (temporal
denoising / precision weighting) — MAY be real. `residual` is kept integer by
comparing this epoch's integer photon catch to the PREVIOUS epoch's stored
integer catch: `residual = Abs(caught_quanta − obs_prev)` — the order-0 temporal
surprise (the change-detect quantity of block 185000), integer by construction.
The float innovation `caught − value` appears ONLY inside the blend.

## 2. THE MECHANISM — one seed, four rules, gated OFF by default (NO Rust)

New seed `seeds/staleness_decay.json` (`self_load_only`, in NO default eye seed
list). It reuses the block-180000 `HeldSurfaceCell` node + `has_held_surface_cell`
edge, driven by a NEW params node `HeldDecayParams{enabled, lr_min, hl_scale,
hl_min, c0, refresh_thresh, attn_thresh}` and NEW integer cell attributes
(`residual`, `last_refresh_epoch`, `half_life`, `freshness`, `needs_attention`),
all written only by the measure adapter on opt-in. Four rules, area `retina`, each
guarded on `HeldDecayParams.enabled == 1` AND the same
`column.input_epoch > hs.epoch` / `rod.input_epoch == column.input_epoch`
fresh-guard as the base rule:

- **`sd_residual` (order 0 — the reflex read):**
  `hs.residual ← Abs(Minus(rod.caught_quanta, hs.obs))` — the order-0 integer
  temporal surprise against the held prediction. O(cells), independent of dwell.
- **`sd_gate` (order 1 — surprise sets half-life, gates refresh):**
  `hs.half_life ← Max(hl_min, IDiv(hl_scale, Plus(residual, 1)))`;
  `hs.last_refresh_epoch ← IfThenElse(Lt(residual, refresh_thresh), column.input_epoch, hs.last_refresh_epoch)`.
- **`sd_freshness` (order 2 — the decay law):**
  `hs.freshness ← Ashr(c0, IDiv(Minus(column.input_epoch, hs.last_refresh_epoch), hs.half_life))`.
- **`sd_blend` (order 3 — precision-weighted Kalman update; the FIRST consumer):**
  `hs.value ← value + [lr_min + (1−lr_min)·Div(Minus(c0, freshness), c0)]·(caught_quanta − value)`;
  then `hs.obs ← caught_quanta`; `hs.epoch ← column.input_epoch`.
- **`sd_flag_stale` (order 3 — a SECOND consumer, foveation):**
  `hs.needs_attention ← IfThenElse(Lt(hs.freshness, attn_thresh), 1, 0)`.

The base `held_surface_accumulate` cannot fire (no `HeldSurfaceParams` node is
created); only these rules drive the cell. `seeds/held_surface.json` is UNTOUCHED.

**Terms used, ALL pre-existing** (`term.rs` diff EMPTY): `Abs, Minus, Plus,
Times, Div, IDiv, Ashr, Max, Min, IfThenElse, Gt, Lt, Eq, And, Attr, Lit, Var`.
No new Term enum variant.

## 3. GATES — pre-registered; each outcome's meaning fixed here

### GATE 1 — HEADLINE: the DECOUPLING (density climbs on static WHILE latency stays flat on moving)

Scene (deterministic, seeded `196000`): a persistent fine-texture STATIC patch
(top rows, L in {40,80,120,160} needing denoise) held for the whole run, PLUS a
bright block (L_hi=200 on L_bg=20) that JUMPS to a new disjoint column set every
`P=15` ticks, `T=90` ticks (6 move epochs). Photon catch carries Poisson shot
noise each tick.

- **Static density** `D(t) = 1 / E_static(t)`, `E_static` = normalized error of
  held `value` vs the noiseless true static patch at tick `t`.
- **Moving latency** `L(m)` at move `m` = ticks after the jump for `E_moving`
  (held vs true on the block's NEW cells) to fall below 0.15.

Pinned pass (all):
- **G1a DENSITY CLIMBS:** `E_static(T) < 0.5 · E_static(t0)` (t0 = first static
  tick) — accumulation, monotone-ish (≤3 up-ticks by >0.03).
- **G1b LATENCY FLAT:** `std(L)/mean(L) < 0.5` across the 6 moves AND the OLS
  slope of `L` vs move index is within `±0.5` tick/move (does not grow with
  dwell — order-0).
- **G1c THE DECOUPLING (dominates the fixed-lr trade):** against two fixed-lr
  controls on the IDENTICAL scene — `lr_low = 0.15` (best denoiser) and
  `lr_high = 0.9` (best adopter): the gated eye achieves
  `E_static(gated) ≤ 1.5 · E_static(lr_low)` (matches the best denoiser's density)
  AND `mean L(gated) ≤ mean L(lr_high) + 2` (matches the best adopter's latency),
  while NEITHER fixed-lr control achieves both (each fails the axis it trades away:
  `E_static(lr_high) > 2·E_static(lr_low)` and `mean L(lr_low) > 2·mean L(lr_high)`).
  **Report BOTH curves and the (density, latency) point for all three eyes.**

### GATE 2 — FIRST-CLASSNESS: a consumer keys off the EXPOSED `freshness` attribute

- **G2a CONSUMER READS FRESHNESS:** ablate freshness (patch `freshness ≡ c0`,
  i.e. never stale) → `sd_blend`'s gain collapses to `lr_min` everywhere → the
  moving region SMEARS: `mean L(freshness-pinned) > 2 · mean L(gated)`. The blend
  demonstrably keys off the freshness graph attribute.
- **G2b SECOND CONSUMER (foveation):** `sd_flag_stale` sets `needs_attention`
  from `freshness`. The flagged cell set == the moving region (freshness
  collapsed) and is EMPTY on the settled static patch: at a post-move tick,
  `≥ 80%` of flagged cells are in the moving block and `≤ 5%` of settled static
  cells are flagged.
- **G2c SOURCE AUDIT:** `freshness` is a `HeldSurfaceCell` graph attribute
  written ONLY by rule `sd_freshness` (Attr reads) and read ONLY via `Attr` by
  the two consumer rules — NOT an engine internal, NOT computed in Python. The
  measure adapter's only writes are node/edge creation + config; a grep gate
  asserts no Python assigns `freshness`/`half_life`/`last_refresh_epoch`.

### GATE 3 — FALSIFIER (non-vacuity): kill surprise-gating → an observable breaks BOTH ways

Uniform (surprise-decoupled) `half_life` on the SAME scene:
- **G3a UNIFORM-LONG (half_life ≡ 256):** freshness never collapses → moving
  content SMEARS: `mean L(uniform-long) > 2 · mean L(gated)`.
- **G3b UNIFORM-SHORT (half_life ≡ 1):** freshness always collapses → static
  cells force-refresh every tick → density STOPS accumulating:
  `E_static(uniform-short) > 2 · E_static(gated)`.
- **PASS = BOTH diverge from gated** (the coupling `surprise→half_life` is
  load-bearing; a uniform decay cannot get both). A `D ≡ 0` (gated ≡ uniform on
  every measured channel) ⇒ decorative; STOP, burn no seed.

### GATE 4 — GENERICITY (re-scope): the SAME primitive, a SECOND quantity

A synthetic SECOND decaying quantity `DecayTrace{magnitude, last_refresh_epoch,
half_life, freshness}` (a "salience trace" that spikes on an event then decays),
in the SAME seed, decayed by a rule `sd_freshness_generic` whose freshness Term
tree is **STRUCTURALLY IDENTICAL** to `sd_freshness` (only the node type, edge,
and var names differ). Pinned:
- **G4a:** the two freshness rules' Term JSON are structurally identical (same
  op tree `Ashr(c0, IDiv(Minus(now, last_refresh), half_life))`) — asserted by a
  canonicalising comparison in the gate.
- **G4b:** the `DecayTrace` freshness curve halves on schedule at its half-life
  (integer-exact), driven by the identical machinery. One primitive, two
  consumers (held-surface value; salience trace) — proves it is shared, not
  perception-local.

### GATE 5 — INTEGER-NATIVE audit

- **G5a:** across the full run, EVERY value of `{residual, last_refresh_epoch,
  half_life, freshness}` on every cell (and `DecayTrace`) is integer-valued
  (`float(x).is_integer()`).
- **G5b:** `sd_residual`/`sd_gate`/`sd_freshness`/`sd_freshness_generic` use ONLY
  integer Terms (`Abs, Minus, Plus, IDiv, Ashr, Max, Min, IfThenElse, Lt, Gt`) —
  no `Div/Times/Exp/Log` — asserted by scanning the seed JSON. The ONLY
  float-producing rule is `sd_blend` (the cross-frame precision blend: `Div/Times`
  on `value/gain`), which is admissible by the integer ontology.

### GATE 6 — EMERGENT POWER-LAW (secondary; honest null accepted)

Heterogeneous half-lives across a surface, all refreshed at epoch 0 then FROZEN
(input withheld so `last_refresh_epoch` never resets). Half-lives log-spread
`{1,2,3,4,6,8,12,16,24,32,48,64}` over 12 cell-cohorts. Aggregate
`S(Δ) = Σ_cohorts freshness(Δ) = Σ_h C0·2^(−⌊Δ/h⌋)`, Δ = 1..128.
- **Report:** log-log slope of `S(Δ)`; R² of a power-law fit `S ∝ Δ^(−α)` vs a
  single-exponential fit over the window. Prediction: superposition of integer
  halvings is approximately power-law (log-log more linear than semilog) over the
  decade spanned by the half-lives, even though each cohort halves exponentially.
  **A null (exponential fits as well or better) is a valid honest result and is
  reported either way.**

### GATE 7 — EXISTING-DECAY AUDIT (re-scope): enumerate the substrate's decays

Enumerate every temporal decay / leaky integrator already in the eye/substrate
and classify each as (a) already integer-half-life (`Ashr`/`scale2` on an epoch
axis) or (b) an AD-HOC FLOAT. Known candidates to enumerate and classify:
photoreceptor/rod **adaptation** (`adaptation += adapt_rate·(caught − adaptation)`,
`adapt_rate` float, fused in `cognitive_tasks.rs`); the held-surface **`lr`** EMA;
**residual-salience** decay (`seeds/residual_salience.json`); **onset refractory**
(`onset_refractory_epochs`); any net-internal leaky integrator
(`effort_dial`/`net_forward`). For EACH, report integer-vs-float and, if float,
flag it as a migration candidate to the shared primitive. **Do NOT migrate them
all here.** If one is a trivially-clean byte-observable swap, do it and gate it;
otherwise LIST it as a named follow-on. Deliverable: after this rung the
substrate has ONE decay primitive with a KNOWN set of not-yet-migrated consumers
— not a zoo.

## 4. PREDICTIONS, STATED IN ADVANCE (being wrong here is the informative outcome)

| # | prediction | value |
|---|---|---|
| P1 | G1a static density climbs | `E_static` falls from shot-noise floor (~0.10) to denoised (~0.03) over the run |
| P2 | G1b moving latency flat | `L ≈ 3–4` ticks at every move, `std/mean < 0.3`, slope ≈ 0 |
| P3 | G1c decoupling: gated (low E_static, low L); lr_low (low E_static, HIGH L≈12); lr_high (HIGH E_static, low L≈1–2) | gated dominates the fixed-lr Pareto frontier |
| P4 | G2a freshness-pinned smears | `mean L` rises to ≈ `lr_low` (~12) |
| P5 | G3 both uniforms break | uniform-long L ≈ 12 (smear); uniform-short E_static ≈ shot-noise floor (no denoise) |
| P6 | G4 identical machinery | freshness rule Term trees byte-structurally equal; DecayTrace halves at its half-life exactly |
| P7 | G6 power-law | log-log slope ≈ −0.7…−1.1; power-law R² > single-exp R² over the window (or honest null) |

## 5. DISCIPLINE COMMITMENTS

- **This file committed ALONE, BEFORE any measurement** (§3).
- **DEFAULT-OFF / C1 BYTE-IDENTITY:** the seed is additive + `self_load_only`,
  in no default eye seed list; with it absent every existing path is
  byte-identical. Oracle `bash scripts/rung7_vision_bench.sh` = **214 passed /
  10 skipped / 0 failed, exit 0** (data-less worktree), BEFORE == AFTER.
  `tests/test_held_surface_migrated.py` stays 3/3 (`held_surface.json` untouched).
- **NO Rust; `term.rs` diff EMPTY.** Canonical engine
  `793ce09ed498a749abb79aeaea44b92e` reported UNTOUCHED before and after; no build
  performed. `source_match ∈ {own, shared}`, never a pinned hash.
- **NEW FILES ONLY:** `seeds/staleness_decay.json`,
  `scripts/staleness_decay_measure.py`, `tests/test_staleness_decay_migrated.py`,
  this prereg, `VISION_STALENESS_DECAY_RESULTS.md`, `results/staleness_decay*`.
- Measure module IMPORT-INERT (no shared-flag mutation at import; opt-in only
  inside the adapter). No agent decisions in Python — every decision is a rule.
- Engine-semantics gate set run for confirmation (unchanged, since no engine
  edit): `test_incremental_match`, `test_empty_match_proof`, `test_dirty_precision`,
  `test_per_sensor_epoch`, `test_per_area_settlement`, `test_predicate_retraction`,
  `test_eye_binding_projection`, plus the eye suite.
- Gate `tests/test_staleness_decay_migrated.py` pins the decoupling (G1), the
  first-classness consumer (G2), the falsifier divergence (G3), genericity (G4),
  and the integer-native audit (G5), reading measured values (able to fail on a
  flat static curve, a growing latency, a non-diverging falsifier, or a float
  in the decay bookkeeping).
- Raw numbers → `VISION_STALENESS_DECAY_RESULTS.md` + `results/staleness_decay.json`;
  decoupling + power-law renders under `results/staleness_decay/`.
- **Do NOT merge to main or edit VISION_PROTOCOL.md — the supervisor merges the
  ledger row.**
