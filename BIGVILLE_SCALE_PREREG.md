# BIGVILLE SCALE-VERIFICATION — PRE-REGISTRATION (block 248000)

**Pre-registered BEFORE any measurement number.** This commit contains only the
claim, the instrument spec, and the seed-claim verdict. No results.

Base SHA `611bf0464f` (current main; verified merge-base). Own engine built
in-worktree from committed Rust source (zero Rust added). This is a FIRST scale
probe over the proven small-cast scaffold (block 245000/247xxx `bigville_sim_world`);
it is **NOT** the north-star's 200-inhabitant real-time claim, and nothing here
extrapolates past the measured range (N ≤ 30).

---

## Seed claim (verbatim)

```
$ python3 scripts/seed_claim.py 248000 248999
SEED CLAIM 248000-248999: CLEAN -- no collision DETECTED.
  Scope: 969 files with seed sinks; 680 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
EXIT=0
```

Block seeded ONCE at base 248000 (numpy `default_rng`).

---

## What is being measured

The north-star's gating axis: **does the REALIZED interaction-operator count per
tick grow LINEARLY (sub-quadratically) in the number of inhabitants N?** The
thesis (memory `ozma_village_north_star`, `ozma_population_is_distribution_over_seeds`):
realized social interaction is SPARSE / LOCAL / bounded-degree → ~O(N·k) LINEAR;
a measured quadratic would be an accidental all-pairs sweep (a BUG to catch),
never a wall.

We count **ACTUAL** interaction-ops — realized perception pairs `(observer,
target)` that PASS the scaffold's sight/hearing gate — **NOT** possible pairs.

### The instrument (fixed here, before any run)

Inhabitants live on a constant-density village lattice. To isolate the
**N-scaling** of realized interaction from finite-size boundary artifacts, the
lattice uses **periodic boundaries (torus)** with **density held constant**
(`λ = N / L²` fixed ⇒ side `L(N) = round(sqrt(N/λ))` grows with N — a bigger
village for more people, the same local neighbourhood). The perception gate is
the scaffold's own gate, reused unchanged: **Chebyshev range + Bresenham
line-of-sight, occluded by trees/walls** (`bigville_sim_world._line`, `OCCLUDERS`,
`SIGHT_RANGE=7`, `HEAR_RANGE=11`). `perceive(o,t) = cheb_torus(o,t) ≤ 11 AND
LOS-clear`.

- **Target mean local degree** `k0 = 2.5` (bounded-degree village), so
  `λ = k0 / W` with perception window `W = (2·11+1)² − 1 = 528` ⇒ `λ = 0.004735…`.
  This keeps `L(N) > 2·11+1 = 23` for **every** N in the grid (even N=5:
  `L≈32`), so proximity genuinely gates (the perception window never covers the
  whole village) — the smallest-N point is NOT trivially all-pairs.
- **Occluder density** `ρ_occ = 0.08` (constant), scattered on the torus; LOS
  drawn in minimal-image space. Occlusion reduces realized degree by a roughly
  constant factor (does not change the exponent).

### Arms

- **sparse (HEADLINE):** realized ops per tick `= Σ_o #{t≠o : perceive(o,t)}`.
  Proximity/LOS-gated. Constant density ⇒ `E[ops] = N·k` ⇒ expected slope ≈ 1.
- **all_pairs (the falsifier that MUST be able to fail to ~2):** the SAME census
  code with the proximity/LOS gate REMOVED — every ordered pair counts, `ops =
  N·(N−1)`. This is exactly what an accidental all-pairs sweep (a broadcast
  world with no perception gate) would produce. Expected slope ≈ 2.

### Ramp / power

- `N ∈ {5, 10, 15, 20, 25, 30}` (6 points; deliverable is 30 townspeople).
- `R = 30` independent placements per (N, arm) — RNG seeds `248000 + …`.
  Positions are static within a placement, so the drama loop runs `T = 12` ticks
  but the realized-ops census is constant per placement; **placement is the unit
  of replication** and the slope CI is bootstrapped over placements.
- Each tick runs the FULL scaffold interaction loop: the seed-crystal drama
  (`run_rules()` — John's spite decision, Mary's ToM inference, villager +
  townsperson backing), the perception census, per-inhabitant nightly journals
  (three glass-box layers), and the reporter→newspaper channel. Townspeople are
  added as real `Villager` graph nodes (full agents processed by `run_rules`),
  NOT hollow NPCs.
- **Slope fit:** OLS of `log(mean_ops)` on `log(N)`.
- **CI:** 2000-sample bootstrap resampling placements; 95% percentile interval.

### Secondary read

Per-tick **wall-clock** (mean, ms) at each N — a secondary observable of what
would fall behind first at scale (includes `run_rules` over N Villager nodes +
the census + N journals). Reported, NOT gated (a first probe on commodity
hardware; N ≤ 30).

---

## PRE-REGISTERED CLAIMS (gates)

- **G-linear (HEADLINE).** The sparse-arm fitted log-log slope lies in the band
  **`slope_sparse < 1.5`** (target ≈ 1.0), because realized interaction is
  proximity-gated/local under constant density. FAIL if the sparse slope ≥ 1.5.

- **G-instrument-can-detect-quadratic (the falsifier that MUST be able to fail).**
  The all_pairs control slope lies in **`[1.8, 2.2]` (≈ 2.0)**, proving the
  instrument distinguishes linear from quadratic. AND the two arms are
  **CI-separated**: `sparse 95%-CI upper bound < all_pairs 95%-CI lower bound`.
  If the SPARSE arm ALSO comes out ≈ 2 (or the arms are not separated), that is a
  **real all-pairs BUG in the scaffold/census to REPORT — not to hide**.

- **G-population-not-cloned.** The 30 townspeople seeds have **non-zero variance**
  in their drawn emotion params (report per-param sd); a `σ→0` control recovers
  **identical agents (all param sd = 0)**. Params drawn `~Normal`, with
  **log-normal / truncated-Normal** for non-negative params (avoiding both
  zero-variance clones AND a clipped-Normal tail artifact).

- **G-discipline (hard).**
  - No Rust: `runners/dsl` (incl `term.rs`) diff EMPTY.
  - Own engine built in-worktree; md5 reported; `source_match = own`.
  - Canonical shared `.so`
    (`runners/dsl/python/substrate_rs/_native.abi3.so`) md5 **START == END**.
  - Oracles before == after: `bash scripts/rung7_vision_bench.sh` (match 245/246
    baseline) and `bash scripts/per_area_settlement_regression.sh` (fail-set
    IDENTICAL); `tests/test_failure_baseline_migrated.py` green.
  - Additive only: all-new files prefixed `bigville_pop_` / `bigville_scale_` /
    `bigville_town_` / `bigville_townspeople_`. No existing tracked file edited;
    the scaffold is subclassed/imported, never modified.

---

## Honest scope (load-bearing)

- **N ≤ 30 is a FIRST scale probe, NOT the 200-real-time claim.** The deliverable
  is the fitted exponent over 5→30 + the sparse-vs-all-pairs separation. No
  extrapolation to 200 is made or implied from ≤30.
- Torus + constant density is the correct **bounded-degree** model of a village
  (it is what "local interaction" MEANS); it is a modelling choice stated up
  front, not a result. A bounded-grid (walled town) adds perimeter/edge effects
  (a finite-size artifact); the torus isolates the N-scaling. A bounded-grid
  cross-check is reported as a secondary read.
- A synthetic MODEL of realized-interaction geometry; not a claim about real
  social networks and not new social science.
