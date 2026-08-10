# BIGVILLE R10b — THE BALANCE FIX: repair R10's two diagnosed defects + RE-MEASURE — PRE-REGISTRATION

**Block 273000. Pre-registered BEFORE any recorded number.** Base = current
`origin/main` HEAD `a900de98bc` (the whole ladder incl. R10 the integration capstone,
`bigville_integ_*`). Seed-claim: `python scripts/seed_claim.py 273 273` → **CLEAN — no
collision DETECTED** (with the tool's standing caveats: the unit is the seed integer;
CLEAN means "no collision detected", never "no collision exists").

R10 (`BIGVILLE_INTEG_RESULTS.md`) assembled the town and MEASURED it: **DEAD_FIXPOINT +
a coin-non-conservation misbalance** (`total_coin` inflated ~35×), and, per its own
prereg, did NOT fix the defects (fixing = this follow-on). R10b fixes exactly those
defects — CORRECTNESS work, NOT tuning — and RE-MEASURES the macro regime with R10's
SAME classifier. This is additive-only, prefix `bigville_integ2_`, edits no tracked
R10/rung file (imports them read-only), NO Rust, own engine.

## What R10b fixes (pre-registered as CORRECTNESS, not tuning)

**DEFECT 1 — the coin-conservation LEAK.** `af_outcome_work` (R17 `bigville_affect_
spiral`) credits a worker +5 coin as a SOURCE with no conserving sink → Σcoin grew
unbounded once composed with the R4 economy. FIX (integration layer, edits no landed
seed): a `WagePool` employer/output account + a new seed `bigville_integ2_conserve`
whose `bi2_*` rules give every affect-outcome coin move a MATCHING counter-move against
the pool (work: pool pays 5; a withdraw/drink/snap loss returns to the pool). The rules
fire on an INDEPENDENT `wsink_armed` flag armed in parallel with `outcome_armed`, so
they never race the landed `af_outcome_*` rules. **GATE: Σcoin (every `coin` attr +
bank `reserves` + the pool) is INVARIANT across the whole run** (measured start→end;
|Δ| < 1e-6). The pool is a pure double-entry ledger account — no rule gates on it — so
conservation holds EXACTLY regardless of magnitude.

**PRIORITY 2 — the DEMOGRAPHIC TIMESCALE (a TICK/DAY/LIFE hierarchy, on PRINCIPLE).**
R10 ran ~12 ticks/day and aged every 6 ticks with elderly acceleration, killing 6/16 in
~15 game-days from routine "chronic aging" — a ~37% cull in two weeks. That is
unrealistic: a HEALTHY, normal-age, fed adult's base death rate over weeks must be ~0.
FIX (world-setup on parameters, edits no seed): calibrate the whole hierarchy —
`TICK` = the finest action grain; `DAY` = `TICKS_PER_DAY` = 36 ticks (a real day's
activity budget); chronic AGING keyed to the DAY cadence at a SLOW, UNIFORM per-day rate
(~1 health/day; frailty lives in the age→health starting value, not a rate multiplier),
so a `LIFE` = many DAYS. Plus a realistic age pyramid: a small genuine-ELDER cohort at
end-of-life (R10 drew ages 18–72 uniform, under-representing elders). **ACCEPTANCE BAR:
over the run the ONLY deaths are CAUSED — genuine old age at the end of a long life
(many days of accrued aging), violence (health→0 from an attack), or severe UNTREATED
illness. A healthy normal-age adult must NOT die.** Deaths are RARE, CAUSED punctuations
that trigger renewal, never a background toll.

**PRIORITY 3 — the dormant RENEWAL.** In R10 deaths fire ~6× then RUN OUT (the founding
elderly age out once); the R23 fertility / R14 birth path is loaded-but-DORMANT. FIX:
wire the birth path — every fertile adult holds a `FertilityState` (the R23 `bf_*` rules
DECIDE the fertility number), and each NEW death triggers a REPLACEMENT birth from a
fertile couple whose graph-decided fertility ≥ 1 (new agents born to replace the dead,
fully endowed). The COUNT/willingness is the graph's decision; the mint is the honest
R14 birth boundary. **GATE: living-count does not monotonically decay to a halt; births
> 0; a birth is counted as a structural event, exactly as a death is.**

## The RE-MEASURE (pre-registered criteria)

RUN LONG (target 1800 ticks = 50 days; ≥ the demographic window so the genuine-elder
deaths + renewal occur) with cast=16, seed=273000, and classify with R10's UNCHANGED
`scripts/bigville_integ_measure.classify_regime` (the 7-regime classifier, pre-registered
thresholds). Report the NEW verdict — DEAD_FIXPOINT / PUNCTUATED_EQUILIBRIUM / EXPLODED /
SMOOTH / WHITE_NOISE / CLEAN_PERIODIC / FROZEN — with its evidence (heavy_tail_ratio,
cost_transition_coincidence, dwell/cascade, first→last decile load). RE-EXPORT the
town-state contract `results/bigville_integ2/townstate.json`.

## ANTI-TUNING COMMITMENT (absolute, binding on the verdict)

I fix the four items above as CORRECTNESS (conservation bug; unrealistic demographic
timescale; dormant renewal; presentation). I do **NOT** tune coefficients/thresholds to
manufacture self-organized criticality / punctuated equilibrium or to make the town
"live". The demographic-timescale and aging calibrations are scale-on-PRINCIPLE (a life
should be many days; a healthy adult should not die in weeks), NOT death rates dialled to
a regime. **Whatever regime emerges after the honest fixes is REPORTED** — a still-dead,
still-frozen, or newly-noisy result is a valid finding. Predicted honest risk: with a
realistic demographic timescale, deaths become RARE, so the demographic engine ALONE may
not sustain activity, and the run may still relax toward a fixpoint unless the (dormant)
social/economic rungs are activated (a separate follow-on) — if so, that is the finding.

## Acceptance evidence to report

- **DEFECT 1:** Σcoin start→end (invariant?), pool trajectory, AND the post-fix TOP-3
  coin-holders (name, coin, class) — showing the distribution re-saned (class roughly
  tracks coin; no minted pile-up). Any residual incoherence is DUG and root-caused, not
  tuned away.
- **PRIORITY 2:** ticks-per-day, days elapsed, a resident's lifespan in DAYS (before vs
  after), and for EACH death its cause + decedent age + days-lived — showing every death
  is old-age / murder / severe-illness, never a routine-aging cull of the healthy.
- **PRIORITY 3:** births fired, living-count trajectory, activity in the final third.
- **REGIME:** the new verdict vs R10's DEAD_FIXPOINT, with the classifier's evidence.

## Presentation additions (world-setup + read-only; never fabricated)

Layered on the SAME assembled town, all faithful (never authored prose): a NAMED cast
(real Pratchett-register names + real seeded params, deterministically assigned; zero
generic `v00`), a DEEP held-state export (real affect/decision graph reads; the R10
`"held":"bank"` hardcode removed), a REAL journal (or `null` when the nightly-journal
faculty is dormant — no fake summary), and a COHERENT map (institutions around a central
square + a resource `features` base + meaningful resident positions). These are
admissible world-setup (placing/naming) + a read-only export; they may shift movement/
perception (a more-correct town, reported), never agent logic. **Priority: the DYNAMICS
core (conservation / timescale / renewal) comes FIRST; presentation defers if it would
rush the dynamics, with any deferral reported.**

## Discipline

Own engine, canonical `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe`, START==END. NO Rust
(`git diff a900de98bc -- runners/dsl` empty). Additive-only; NEW files prefixed
`bigville_integ2_`. Gates: `tests/test_bigville_integ2_migrated.py`;
`tests/test_failure_baseline_migrated.py` (11/11). Two commits: (1) this prereg, (2) the
build + results. DO NOT merge (the supervisor merges).
