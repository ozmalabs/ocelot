# BIGVILLE R10e — SCALE TO 50 — PRE-REGISTRATION

**Block 276000. Pre-registered BEFORE the real number** (the only prior run is a 40-tick
smoke to prove the world boots; the measurement is the 1800-tick run below). Base = main
HEAD after the coin-cache perf commit. Seed-claim `python scripts/seed_claim.py 276 276`
→ CLEAN (tool caveats: "no collision detected", not "none exists"). Additive-only
(`bigville_integ5_*` + the additive `bigville_townspeople_50` register); edits NO landed
seed/world; **NO Rust** (`runners/dsl` diff EMPTY); own engine.

## What R10e changes (nothing but scale)

`BigvilleInteg5World(BigvilleInteg4World)` inherits EVERY mechanic unchanged (shopping
loop, social rungs, conservation, the perf batching). The ONLY change: **cast=50** with
a **50-resident register** — the 30-register plus 20 ordinary townsfolk drawn from the
SAME generative model at archetype offset 0 (grand-mean residents + individual noise;
`param_sd` non-zero → not clones). This exists to MEASURE at a population where dynamics
are genuine rather than anecdotal.

## The pre-registered measurements (1800 ticks / 50 days, cast=50, seed=276000)

1. **GENUINE DYNAMICS — cast-16 vs cast-50.** Classify both with R10's UNCHANGED
   `classify_regime`. Report the verdict, `heavy_tail_ratio`, `cascade_max`, activity
   head/tail for EACH. The question (falsifiable): does 50 cross into qualitatively
   different / richer macro behaviour than 16 — bigger cascades, a mobilisable minority
   that is MORE than one person (the 3.5% quorum stops rounding to 1), coalition
   structure — or is it the SAME regime, just bigger? WHATEVER emerges is the result.
2. **COST vs HEADCOUNT (the SCALE × TIMING frontier).** Report ms/tick at cast=50 and
   the elapsed run. Pre-run probe (60-tick): cast 16 → 212, cast 30 → 343, cast 50 →
   588 ms/tick — i.e. **sub-linear-to-linear** in population after the phase-batching
   (which made the economy/violence phases scale with the GRAPH not the POPULATION; the
   residual per-buyer WALK is the linear component). The full-run ms/tick is the datum.
3. **CONSERVATION holds at scale:** Σcoin invariant (Δ=0).
4. **The town is coherent at 50:** circulation > 0, social rungs fire, named cast.

## Anti-tuning (binding)

Nothing is dialled. cast/register are the only changes; the regime, the cascade
statistics, and the cost are MEASURED and reported as-is — a regime that stays
CLEAN_PERIODIC, or moves, or a cost that scales badly, are all valid findings. The
40-tick smoke is NOT a result (too short for the weekly social cadences to fire).

## Honest scope (pre-declared)

- The map is the R10d 30×18 grid; 50 residents make the housing district CRAMPED
  (multiple residents per home cell) — a cosmetic/coherence residual, not a dynamics
  one; a bigger map is a follow-on. Reported, not hidden.
- The 20 new residents are ORDINARY townsfolk (offset 0), so the special-role structure
  (mayor/pastor/council/press) is the 30-register's; scale adds citizens, not new
  institutions.

## Discipline

`runners/dsl` diff EMPTY; no `.so` committed; gate `test_bigville_integ5_migrated`
(boots at 50, register has 50 distinct names, conservation holds on a short run) +
`test_failure_baseline_migrated` 11/11. Pre-existing provenance red (`ada5f2ae`)
persists. Two commits: (1) this prereg + register + world + run; (2) results. Supervisor
merges `--no-ff`.
