# BIGVILLE R10e — SCALE TO 50 — RESULTS

**Block 276000.** Prereg: `BIGVILLE_INTEG5_PREREG.md` (committed before this number).
Additive-only; **NO Rust**; own engine. 1800 ticks / 50 days, cast=50, seed=276000.

## Headline — 50 gives GENUINELY richer dynamics (the creator's call, confirmed)

Same mechanics as R10d, only the population changed (16 → 50, via the 50-register). The
macro dynamics are not "the same, bigger" — they are QUALITATIVELY heavier:

| statistic | cast-16 (R10d) | cast-50 (R10e) | change |
|---|---|---|---|
| heavy_tail_ratio | 5.33 | **17.33** | 3.3× heavier-tailed |
| cascade_max | 43 | **194** | a 194-event avalanche |
| cascade_sizes (top) | — | [194, 83, 55, 48, 45, 36, 30, 29, 24, 24] | a real power-law tail |
| activity_total | (small) | **1070** | |
| violence events | ~46 | **171** | 3.7× |
| evictions / deaths / foreclosures | 13 / 8 / 2 | **24 / 22 / 16** | |

At 50 the town produces **genuine avalanches** — a shock (a death, an eviction) now
propagates through a big enough web of kin/rivalry/tenancy to cascade to ~194 coupled
state-changes, where at 16 the biggest cascade was 43. This is the population where the
dynamics stop being anecdotal: the mobilisable minority is a group, and conflict/grief
cascades have room to run. The "3.5%" quorum no longer rounds to 1.

## Regime — still `CLEAN_PERIODIC` (honest)

Verdict unchanged from R10c/R10d: `CLEAN_PERIODIC`, `dominant autocorr peak 0.81 @ lag
36` — one game-DAY. The clock-scheduled institutions (daily finance/aging, weekly paper/
council) still impose the dominant rhythm; scale AMPLIFIED the cascades WITHIN that
periodic frame but did not break the periodicity. `cost_transition_coincidence 0.0`.
Breaking to true punctuated equilibrium remains the ENDOGENOUS-TRIGGER lever (events fire
on stress-crossings, not a calendar), not tuning — unchanged by scale.

## Cost vs headcount (the SCALE × TIMING datum)

| cast | ms/tick (60-tick probe, solo) | 1800-tick run |
|---|---|---|
| 16 | 212 | ~6 min |
| 30 | 343 | ~10 min |
| 50 | 588 | **~18 min** |

**Sub-linear-to-linear in population** — the phase-batching moved the economy/violence
phases off population-scaling (cost ∝ graph), leaving the per-buyer walk as the linear
term. cast-16 → cast-50 is ~2.8× cost for 3.1× population. (This run's wall-clock —
2498 s / 1388 ms-per-tick — is INFLATED ~2.4× by concurrent CPU load during the run; the
solo probe figures above are the datum. Reported honestly.)

## Coherent at 50

- **Conservation holds:** Σcoin **2663 → 2663, Δ=0, invariant** at scale.
- **Renewal at scale:** 73 residents lived over the run, **51 alive** at the end (deaths
  replaced by births); circulation **1584** (639 buys); gini_wealth **0.972** (inequality
  SHARPENS at scale — a working market + rent stratification over more people).
- **Named cast:** 50 distinct register residents (30 + 20 ordinary townsfolk).

## Honest residuals

- The map is the R10d 30×18 grid; 50 residents crowd the housing district (multiple per
  home cell) — cosmetic, a bigger map is a follow-on.
- gini 0.97 is extreme — the inequality spine at scale; a real read, and the redistribution/
  land-tax levers are the designed structural responses to measure next.
- Verdict CLEAN_PERIODIC (scale did not break it — endogenous triggers are the lever).

## Discipline
`runners/dsl` diff EMPTY; no `.so` committed; gate `test_bigville_integ5_migrated`
(boots at 50, register 50-distinct-not-cloned, conserves) + `test_failure_baseline_migrated`
11/11. Pre-existing provenance red (`ada5f2ae`) persists. Raw:
`results/bigville_integ5/{macro,townstate,shopping}.json`.
