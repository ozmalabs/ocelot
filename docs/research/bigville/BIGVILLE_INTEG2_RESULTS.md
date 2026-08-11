# BIGVILLE R10b — THE BALANCE FIX: R10's two defects repaired + the macro regime RE-MEASURED — RESULTS

**Block 273000.** Pre-registration: `BIGVILLE_INTEG2_PREREG.md` (committed BEFORE this
number, commit `300e00493e`). Seed-claim `python scripts/seed_claim.py 273 273` =
**CLEAN**. Own engine, canonical `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe`,
START==END. No Rust (`git diff a900de98bc -- runners/dsl` EMPTY). Additive-only, prefix
`bigville_integ2_`; edits no tracked R10/rung file (imports them read-only).

## Headline

R10 measured the assembled town as **DEAD_FIXPOINT + a ~35× coin-non-conservation
misbalance**. After repairing the diagnosed defects as CORRECTNESS (conservation +
realistic demographic timescale + renewal) and re-measuring with R10's **UNCHANGED**
classifier over a long run (1800 ticks = 50 days, cast=16, seed=273000, 622 s):

> **Σcoin is INVARIANT** (leak closed), **deaths are now RARE + CAUSED** (3 genuine
> old-age + 1 murder; ZERO healthy-adult aging deaths), **renewal sustains the
> population** (4 births replace 4 deaths), and the macro regime **MOVED from
> DEAD_FIXPOINT to `PUNCTUATED_WEAK`** — intermittent punctuations with activity
> sustained into the final third, but **NOT full self-organized criticality**
> (heavy_tail_ratio 3.0 < 5.0; cost/transition coincidence 0.0). Reported as it emerged;
> nothing was tuned to manufacture SOC.

## DEFECT 1 — the coin-conservation LEAK: CLOSED (Σcoin invariant)

A `WagePool` employer/output account + the new seed `bigville_integ2_conserve` (5
`bi2_*` rules) give every affect-outcome coin move a matching counter-move (work → pool
pays 5; a withdraw/drink/snap loss returns to the pool), armed on an independent
`wsink_armed` flag so they never race the landed `af_outcome_*` rules.

| | R10 | R10b |
|---|---|---|
| total_coin trajectory | **529 → 18 662 (~35×)** | — |
| Σcoin (all `coin` + `reserves` + pool) start → end | not conserved | **1953.0 → 1953.0, Δ = 0.0 (INVARIANT)** |
| WagePool end | (none) | −3568 (the aggregate employer's net wage deficit — the conserving sink R10 lacked) |

**Wealth distribution re-saned (the acceptance check).** In R10 a MINTED pile-up let a
*poor* worker hold 1750 while the banker held 396. After conservation **and** the
day-cadence wage fix below, the post-fix TOP holders are, in order:

| rank | name | coin | class |
|---|---|---|---|
| 1 | **John** (mayor / rich landlord) | 2399 | rich |
| 2 | **Scrooge** (banker) | 300 | rich (banker) |
| 3 | Councillor Ida Marrow | 132 | middle |
| 4 | Councillor Bettony Slade | 124 | middle |
| 5 | Marjorie Dough | 114 | middle |

Class now tracks coin (rich landlord ≫ banker > middle > poor) and **no poor resident
holds more than the banker** (Scrooge 300 > every poor holder). Scrooge's personal coin
(300) stays correctly separate from the bank's reserves (2163) — the R7/R9 split is
preserved.

**The dig-further finding behind the re-saning.** Conservation ALONE does not re-sane the
distribution — a conserved wage still accrues to workers. The root cause was a
TIMESCALE-SEAM scale bug: R10 ran the R17 affect life-cycle (the daily work/withdraw
decision that yields the +5 wage) **every tick**, so under the day-scaled clock each
worker earned a FULL DAY'S WAGE 36× per day (this, not the pool choice, is what would
have kept workers runaway-rich). Keying the affect life-decision to the DAY cadence
(once per `TICKS_PER_DAY`) — an affect outcome is a day-level event, not a per-tick one —
makes the +5 wage commensurate with finance (salary/rent are per-day), so the economy
stratifies coherently (poor renters run net-negative on rent → evictions; rich landlords
and the banker accrue). This is a correctness fix on the tick/day hierarchy, not a tuned
coefficient.

## PRIORITY 2 — the DEMOGRAPHIC TIMESCALE: realistic (deaths rare + CAUSED)

The tick/day/life hierarchy: `TICK` = finest action grain; `DAY` = 36 ticks; chronic
AGING keyed to the DAY cadence at a slow, UNIFORM ~1 health/day (frailty in the
age→health starting value, not a rate multiplier), so a `LIFE` = many DAYS; plus a
realistic age pyramid with a small genuine-elder cohort at end-of-life.

| lifespan (ticks) | min | median | max |
|---|---|---|---|
| **R10** (every-6-tick, elderly-accelerated aging) | 65 | 540 | 600 |
| **R10b** (per-day uniform aging) | 979 (**27 days**) | 3240 (**90 days**) | 3600 (**100 days**) |

**The acceptance bar is MET — every death over the run was CAUSED, none a routine-aging
cull of the healthy** (`healthy_normaladult_aging_deaths = 0`):

| day | resident | cause | age | genuine elder? |
|---|---|---|---|---|
| 28 | Marjorie Dough | old age (chronic aging) | very old | **yes** |
| 28 | Peony Fen | **violence (murdered)** | 50 | no |
| 33 | Wat Crane | old age (chronic aging) | very old | **yes** |
| 39 | Tobias Crane | old age (chronic aging) | very old | **yes** |

3 genuine old-age passings (the end-of-life elder cohort) + 1 **murder** (violence drove
health→0 — a caused death the acceptance bar explicitly allows). A healthy, normal-age,
fed adult did NOT die of routine aging over the 50-day run (their lifespans are 55–100
days). R10's absurd "6 of 16 culled by chronic aging in ~15 days" is gone.

## PRIORITY 3 — the dormant RENEWAL: WIRED

Every fertile adult holds a `FertilityState` (the R23 `bf_*` rules decide the fertility
number); each NEW death triggers a replacement birth from a fertile couple whose
graph-decided fertility ≥ 1. **4 deaths → 4 births**; the living count held at **16**
(never decayed to a halt); births are conserving (newborn coin 0) and fully endowed
(health/affect/attacker/rent/fertility/pays-edge/heir), so a newborn ages, works, and can
itself reproduce.

## THE RE-MEASURED REGIME — `PUNCTUATED_WEAK` (moved off the dead fixpoint)

R10's classifier, unchanged, on the R10b series:

| metric | R10 | R10b | reading |
|---|---|---|---|
| **verdict** | DEAD_FIXPOINT | **PUNCTUATED_WEAK** | moved OFF the dead fixpoint |
| activity_total / max | 19 / 3 | **32 / 3** | more endogenous events |
| head vs tail activity | 19 / **0** (dead tail) | 20 / **12** | **tail is NON-zero — not dead** |
| stable_fraction / dwell_max | 0.968 / 213 | 0.988 / 1007 | long stability between punctuations |
| cascade_max | 5 | **14** | a bigger burst (the day-28 double death + births) |
| heavy_tail_ratio | 3.0 | **3.0** (< 5.0) | still NOT heavy-tailed → not full SOC |
| cost_transition_coincidence | 0.0 | **0.0** | cost does NOT spike at transitions → not full SOC |
| first→last decile load | 41.3 → 24.2 | 9.58 → 5.71 | load FELL ⇒ **not exploding** |
| event kinds | death 6, evict 3, **viol 0** | death 4, **violence 8**, evict 3, foreclosure 1 | **violence IGNITED** (R10 had none) |

The verdict `PUNCTUATED_WEAK` means: **long dwells + real intermittent punctuations, but
light-tailed bursts** (`heavy_ratio 3.0 < 5.0`) — the classifier's own words: "intermittent,
not full SOC". Honestly: the fixes moved the town from a dead fixpoint TOWARD punctuated
equilibrium — activity is now sustained into the final third (tail = 12 vs R10's 0), the
negative spiral **ignited** (8 violent acts, 1 murder — R10 had zero violence ever), and
evictions/foreclosure fired — but it is **not** full self-organized criticality: the
cascades are not heavy-tailed and cost does not punctuate with the transitions. This is
the REAL regime, not a tuned one.

## Presentation additions (world-setup + read-only; all real, never fabricated)

Re-exported to `results/bigville_integ2/townstate.json` (21 villagers, day 50):

- **Named cast** — zero generic `v00`; e.g. `Marjorie Dough` (baker, 🍞), `Scrooge`
  (banker), `John` (mayor), the Cranes, councillors, etc. — real Pratchett-register names
  + real seeded params (`w_spite` drives the violence machinery).
- **Deep held (real graph reads)** — a resident: `doing=work; grief=2.0; wellbeing=100;
  spite=0.03; supergraph=1.84; hostility=0.48; mood=0.01`. The **banker**:
  `rate_bp=800; reserves=2163` (his real rate intent + reserves). The R10 hardcode
  `"held":"bank"` is GONE.
- **Real journal** — `journal: null` for every resident: the nightly-journal faculty is
  loaded-but-DORMANT in this assembly (no `Journal` node is minted), so the honest read
  is "no entry" — never a fabricated summary. (Activating the nightly-cadence + the
  dormant social rungs is the supervisor's separate follow-on.)
- **Coherent map** — 8 institutions around a central square (townhall, noticeboard, bank,
  church, school, surgery, inn, press) + a resource `features` base (crop, forest, rocks,
  orchard, water, well) + each resident at a meaningful home/workplace position.

## Gates

- `python -m pytest tests/test_bigville_integ2_migrated.py -q` — **12 passed**
  (conserving-seed load; Σcoin invariant over a run + pool absorbs the debit; healthy
  adult doesn't die in weeks; lifespans many-days & longer than R10; genuine-elder
  cohort; death→replacement-birth; birth conserves + is endowed; named cast no-`v0`; deep
  held is real graph state + journal null; contract shape incl. `features`/`births`;
  no-agent-decision source audit).
- `python -m pytest tests/test_failure_baseline_migrated.py -q` — **11/11** (baseline
  unbroken).
- `runners/dsl` diff vs `a900de98bc` EMPTY; canonical `.so` md5 unchanged START==END; no
  `.so` committed.

## Anti-tuning attestation

No coefficient or threshold was dialled to manufacture SOC. The day/aging/wage-cadence
calibrations are corrections on PRINCIPLE (a life is many days; a healthy adult does not
die in weeks; an affect life-decision is a day-level event). The emergent regime
`PUNCTUATED_WEAK` — better than R10's dead fixpoint, short of full SOC — is reported
exactly as measured. No landed R17 (or any) seed was edited (the conservation fix is a
pure integration-layer seed + a WagePool; the day-cadence is the adapter's tick loop).

## Honest residuals

- **Not full SOC.** `PUNCTUATED_WEAK`, not `PUNCTUATED_EQUILIBRIUM`: cascades are
  light-tailed (heavy_ratio 3.0 < 5.0) and cost does not punctuate with the transitions
  (coincidence 0.0). Reaching full heavy-tailed SOC would need the currently-DORMANT
  social/economic rungs (paper/council/sermon/market/gossip) activated — the supervisor's
  separate follow-on — NOT more coefficient tuning.
- **Elder displayed ages** read very high (the `age` attr accrues per aging call); the
  deaths are unambiguously genuine old age (the end-of-life elder cohort at low health),
  and `was_genuine_elder=True` is recorded for each.
- **Circulation stays weak** (buyers are not co-located with shops, exactly as R10 —
  `circulation` reads low); the distribution coherence came from the wage-scale (day
  cadence) fix + rent stratification, not from consumption.
- **Cast = 16 named movers** via the supervisor's permitted fallback (distinct real names
  + real params), NOT the full 30-person register boot (that boot is a documented
  follow-on; it did not gate the dynamics measurement).
- **`N_GENUINE_ELDERS = 3`** is a realistic-age-pyramid world-setup choice; the 3 elder
  deaths + the 1 emergent murder are the run's punctuations. A different pyramid/run
  length is a different point on the SCALE×TIMING frontier, not a correction.
- **Runtime** ~0.35 s/tick (10.4 min for 1800 ticks) — the SCALE×TIMING datum of a
  realistic day granularity; not shrunk to save cost.
