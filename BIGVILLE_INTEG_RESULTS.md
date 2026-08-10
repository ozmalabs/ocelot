# BIGVILLE R10 — DYNAMICS: the PUNCTUATED-EQUILIBRIUM validity gate — RESULTS

**Block 258000. The CAPSTONE rung — it ASSEMBLES the town and measures whether it
LIVES.** Pre-registration: `BIGVILLE_INTEG_PREREG.md` (committed BEFORE this number).
Seed-claim `python scripts/seed_claim.py 258 258` = **CLEAN**. Own engine, canonical
`.so` md5 `fd82dc2978dbb055496dd82390ac2ebe`, START==END. No Rust
(`git diff <base> -- runners/dsl` empty). Additive-only, prefix `bigville_integ_`.

## The measured verdict (headline)

Over a LONG run of the fully-assembled town (cast=16, seed=258000, **400 ticks**,
247.6 s, no crash), the macro time-series is:

> **DEAD_FIXPOINT** in the discrete-event series **+ a slow SMOOTH monetary drift
> (a coin-non-conservation misbalance).** **Punctuated equilibrium is NOT observed.**

This is a **FINDING**, reported as pre-registered — a dead-fixpoint result is the
proof that, *under this balance*, circulation is insufficient to sustain the political
economy; it is not a failure to hide. The town **did NOT explode** (the node-count /
load runaway guard never tripped; `first_decile_load 41.3 → last_decile_load 24.2`, so
load FELL, the opposite of a runaway), and it **is genuinely coupled** — it produced
endogenous structural events — but the dynamics **relax to a fixpoint** rather than
sustaining self-organized criticality.

## What actually happened (glass-box)

- **A one-shot demographic + housing PUNCTUATION, ticks 138–187.** 6 endogenous
  **deaths** (the founding-elderly cohort aging out — cause 1, chronic aging, NO
  scheduled shock) + 3 endogenous **evictions** (poor tenants falling behind on rent →
  `bf_evict`). Living 16 → 10; homeless 0 → 3; land-Gini 0.59 → 0.65 (concentration
  ticks up as the dead vacate). The SHAPE of these 187 ticks *is* stability → change →
  stability — but it is a **transient, not sustained**.
- **Then a DEAD FIXPOINT in structural events, ticks ~188–400.** Activity = 0 for the
  entire last third (132 ticks). `activity_total = 19` events over the whole run;
  `cascade_max = 5`; `heavy_tail_ratio = 3.0 < 5.0` (NOT heavy-tailed → **SOC / the
  G-heavy-tailed-cascades sub-gate FAILS**). No violence EVER ignited (grief from the
  deaths/evictions never crossed the `trigger_threshold = 8` in `bv_trigger`).
- **A SMOOTH monetary MISBALANCE runs underneath the whole time.** `total_coin`
  inflates monotonically **529 → 18 662 (~35×)** while bank `reserves` fall only
  ~700 (1516 → 804). The coin injected therefore comes NOT from a conserved transfer
  but is **created** — diagnosed to the affect work-outcome income (`af_outcome_work`
  adds coin as a SOURCE with no conserving sink) once composed with the R4 economy.
  This is a slow **coin-non-conservation leak across the R4/R17 seam**, a *misbalance*
  distinct from a structural explosion: it never trips the node/activity guard, but it
  is a real imbalance the ASSEMBLED town reveals that neither rung showed in isolation.
- **Cost does NOT punctuate.** `cost_mean 31.1`, range 23–51, `cost_transition_
  coincidence = 0.0` — the rare events are CHEAP (a death/eviction is a few rule-fires)
  relative to the routine ~31/tick economic re-settling, so the independent cost
  measurable does NOT spike at the transitions → **the G-cost-punctuates-with-it
  triangulation FAILS**. (During the event window cost peaks to 48–51, but not
  separably enough for the 90th-percentile coincidence test.)

### Full evidence (from `results/bigville_integ/macro.json`)

| metric | value | reading |
|---|---|---|
| verdict | DEAD_FIXPOINT | discrete-event series dies after tick 187 |
| activity_total / max | 19 / 3 | tiny; a handful of events, none large |
| head vs tail activity | 19 (first 268) / **0** (last 132) | ground to a halt and STAYED |
| stable_fraction / dwell_max | 0.968 / 213 | one enormous dead stretch |
| cascade_max / heavy_tail_ratio | 5 / **3.0** | NOT heavy-tailed (SOC fails, <5) |
| cost_mean / min / max | 31.1 / 23 / 51 | flat; economy churns, events cheap |
| cost_transition_coincidence | **0.0** | cost does NOT punctuate (triangulation fails) |
| first→last decile load | 41.3 → 24.2 | load FALLS ⇒ NOT an explosion |
| total_coin 529 → 18 662 | ~35× | smooth monetary inflation (misbalance) |
| deaths / evictions / violence | 6 / 3 / **0** | endogenous, transient; no violent cascade |

## Diagnosis — WHICH couplings (the prereg abandon/narrow deliverable)

The dead fixpoint is not a bug in any one rung; it is an emergent property of the
BALANCE, and it names three weak/mis-set couplings:

1. **No sustained STRESS GENERATOR.** The only stressors are (a) chronic aging (a
   ONE-TIME cohort — the founding elderly die once; no new generation ages in within
   400 ticks because the fertility/birth path is loaded-but-dormant) and (b) rent/
   mortgage service (which stabilises once the vulnerable few are evicted). With no
   ongoing stress injection AND no scheduled shocks (G-endogenous, correctly held),
   the discrete dynamics **must** relax to a fixpoint. R14's own gate is prophetic:
   "death ON → the concentrating fixpoint is PUNCTUATED; death OFF → the DEAD
   attractor" — here death fires SIX times then RUNS OUT, so the punctuation is a
   one-shot, not a cycle.
2. **The negative-spiral cascade never ignites.** `af_outcome_work` income keeps most
   agents solvent (and, worse, INFLATES the money supply), so foreclosure→grief→
   withdraw/drink→further-default→snap→violence never gets going: 0 foreclosures of
   mortgagors, 0 violent acts. The grief from 6 deaths + 3 evictions is real but below
   the violence trigger. The chain the spec designed (economy → affect → society) is
   PRESENT but under this balance stays sub-threshold.
3. **A coin-conservation LEAK across the R4/R17 seam.** `af_outcome_work` mints coin;
   composed with the R4 exchange economy it makes `Σcoin` unbounded (the ~35× drift).
   In isolation R17 measured wellbeing, not the town's money supply, so the leak was
   invisible; ASSEMBLING is what surfaced it — exactly R10's job.

**None of these is fixed here** (fixing the balance would be tuning-to-a-result, which
the prereg forbids). They are the pre-registered diagnosis: the assembled political
economy, as balanced, LIVES enough to transition once but then dies to a fixpoint, and
carries a slow monetary misbalance. Punctuated equilibrium — the signature of a genuine
complex adaptive system — is **not** present. The gate's own words: *a DEAD-fixpoint
result is a FINDING — circulation/redistribution is insufficient, the money model is
DYING; punctuated equilibrium is the proof the political economy LIVES* — and it does
not, yet, at this operating point.

## Assembly — what composed cleanly vs what is dormant

- **31 CORE rungs on the R15 MRO chain** (assembled by construction, each proven in its
  own rung): movement/energy, needs (drives + choice), time (sleep/concern/co-reg),
  economy (production/exchange/supply/debt/expectation), skill (learn/teach), finance
  (bank/tenure), land (market/tenure), life (rearing/health/inheritance), affect
  (grief/decide/spiral/coreg/propagate), violence (act/evidence/prosecute/kill).
- **21 SIBLING-branch seeds loaded CLEANLY into the SAME engine, 0 conflicts** (doctor,
  fisc-state, fisc-church, school×3, goal×2, coll×2, build×2, news×2, council×2, loop,
  fert, infant, loud×2). The seed loader raised no rule-name collision — the rungs are
  distinctly prefixed and compose. **However**: their FULL ingest lives on separate
  Python adapter chains this harness does not subclass, so they are **LOADED-but-
  DORMANT** (their rules are present but few of their trigger node-types are populated
  — e.g. the fertility/birth path, the collective-action coalition read-off, the
  construction builder). This is documented honestly, not forced: populating them fully
  is a follow-on. The measured dynamics are driven by the 31 populated core rungs.

**No hard CONFLICT was encountered** (`conflicts = []`). The one interaction worth
noting is the SEMANTIC one above (the R4/R17 coin-conservation seam) — not a load-time
collision but a runtime misbalance, surfaced only by assembly.

## The three deliverables (all landed)

1. **The integration harness** — `worlds/bigville_integ_world.py` (assembles + drives)
   + `scripts/bigville_integ_run.py` (boot → long run → dump). Mechanical I/O only; no
   agent decision (source-audit gate green); no scheduled shocks (G-endogenous).
2. **The macro measurement + instrument** — `scripts/bigville_integ_measure.py`. The
   7-regime classifier's thresholds are PRE-REGISTERED; the instrument is proven on
   SYNTHETIC series to distinguish EXPLODED / FROZEN / DEAD_FIXPOINT / CLEAN_PERIODIC /
   PUNCTUATED_EQUILIBRIUM / WHITE_NOISE / SMOOTH (so its call on the real town — an
   explosion is an explosion, a dead fixpoint a dead fixpoint — is trustworthy).
3. **THE TOWN-STATE EXPORT CONTRACT** — `worlds/bigville_integ_state.py`, a pure reader
   emitting the exact UI data contract. A mock-real snapshot is at
   `results/bigville_integ/townstate.json` (all 10 top keys, 6 institutions, 17
   villagers with class/coin/health/held/rel, 400 macro entries) so the parallel UI
   track can build against it NOW.

## Gates

- `python -m pytest tests/test_bigville_integ_migrated.py -q` — **13 passed** (assembly,
  population, macro-series shape, no-scheduled-shocks source audit, regime-of-the-run,
  the 7 instrument tests on synthetic series, the exact-contract-shape assertion, the
  snapshot emit).
- `python -m pytest tests/test_failure_baseline_migrated.py -q` — 11/11 (R10 loads MANY
  seeds; the baseline is unbroken).
- `python -m pytest tests/test_engine_provenance_migrated.py -q` — 7/7 (own-engine).
- `runners/dsl` diff EMPTY; canonical `.so` md5 unchanged START==END; no `.so`
  committed.
- The ~43-min `per_area` / `rung7` oracles: see the commit message for whether time
  permitted; R10 is additive + `self_load`-heavy but not purely `self_load_only`, so
  the baseline gate + additive discipline are the primary guard.

## Honest residuals

- **The verdict is balance-conditional** (cast=16, seed=258000, the pre-registered
  cadence FIN_PERIOD=LIFE_PERIOD=6). A different balance could ignite the spiral or the
  monetary leak faster; that would be a DIFFERENT operating point on the SCALE×TIMING
  frontier (§4), not a correction — and finding it would require tuning, which the
  prereg forbids for this measurement. The claim is exactly: *this assembled town, at
  this operating point, dead-fixpoints and mildly inflates.*
- **The coin-conservation leak is diagnosed, not fixed** (fixing = tuning).
- **21 sibling rungs are loaded-but-dormant** — their rules compose but their world
  entities are minimally populated; a fuller assembly (populating fertility, coalition,
  construction, fisc treasury flows) is the natural follow-on and might supply the
  missing sustained stress generator.
- **`circulation` reads 0 in the contract** (the `bought` per-mover counter is not
  accumulated by the exchange path as read here) — a cosmetic read-off gap, not a
  dynamics issue; the real exchange is visible in the coin/hunger flow.
- **Scale**: N=16 in real-ish time (247 s / 400 ticks ≈ 0.6 s/tick). A batch town of
  thousands (for statistical power on the 3.5% / SOC questions) is the other operating
  point on the frontier; not run here.
