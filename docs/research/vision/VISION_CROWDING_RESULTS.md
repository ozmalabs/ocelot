# VISION — CROWDING (T8) — RESULTS

*Confirmatory run of `VISION_CROWDING_PREREG.md` (pre-registered and committed at
**8703131e** BEFORE this run, §3). Runner `scripts/crowding_measure.py`; gate
`tests/test_crowding_migrated.py`; results JSON `results/crowding_measure.json`.*

**Provenance (§10):** `engine 7d5f50c18673 @
runners/dsl/python/substrate_rs/_native.abi3.so — shared build, Rust source identical`
(this rung adds **NO Rust**; the shared canonical engine is a legitimate source-identical
build, §10.1). Base commit **d8955f47** (`git merge-base --is-ancestor d8955f47 HEAD`
holds). Seeds **43000–43999**; confirmatory noise **43100–43199**.

## OUTCOME — ALL SIX CONFIRMATORY ARMS PASS; every prediction held

| arm | result | verdict |
|---|---|---|
| **A CROWDING** | flanked (ecc=10, sF=3): `recognized=0`, `pool_n=2`, `pooled_ident=7≠5`; isolated: `recognized=1`, `pool_n=1`, `pooled_ident=5` | **PASS** |
| **B FOVEAL SPARING** | SAME spacing sF=3: foveal (ecc=2) `recognized=1`, peripheral (ecc=10) `recognized=0` | **PASS** (risked) |
| **C ECC-SCALING (Bouma)** | crit spacing `s* = {4:2, 8:4, 12:7}` = `floor(0.6·ecc)`, strictly monotone; `s*/ecc ≈ {0.5,0.5,0.58}` | **PASS** (entailed) |
| **D FLOOR / §1.1** | isolated peripheral & foveal both `recognized=1`; both recognized states {0,1} reached (alive) | **PASS** |
| **E NOISE FLOOR** | 100 random isolated items (seeds 43100–43199): **0/100** false-crowded | **PASS** |
| **F §9 OFF-DAY** | flag OFF: all readout attrs `0.0` (inert); default `crowd=0.0` | **PASS** |

`ALL_CONFIRMATORY_PASS: True`. Gate `tests/test_crowding_migrated.py` **8/8**.

## The headline, in one line

**Eccentricity-scaled pooling reproduces crowding: recognition reads a pooled summary
over `R = bouma·ecc` from the fixation, so a peripheral target flanked within `R` loses
its identity to the mixed summary (`pooled_ident` 5→7), survives in isolation, and is
SPARED at the fovea by the identical flankers.** The mechanism is two seed rules
(`cr_ecc` computes ecc² and `pool_radius2 = bouma²·ecc²`; `cr_pool` reads the local
`co_item` pool and sets `recognized = (pool contains only the target)`) driven by the
`run_rules` fixpoint — NO new Rust, NO Python decision.

## What is EVIDENCE vs what is CALIBRATION (§13.1, declared in the prereg)

This is a VALIDATION gate, and the prereg split the arms honestly BEFORE the run:

- **RISKED / load-bearing (the model could have produced the opposite):**
  - **B — foveal sparing at MATCHED spacing.** Foveal `recognized=1` while peripheral
    `recognized=0` at the *same* sF=3. A model whose pool radius did NOT scale with
    eccentricity (constant `R`) would crowd the foveal target too and FAIL B. B passing is
    the evidence that the pooling is genuinely eccentricity-scaled.
  - **A2 / D / E — clutter-dependence.** Isolated targets (foveal AND peripheral, and 100
    random ones) are all `recognized=1`. A model that jumbled everything peripheral would
    FAIL these. Identity loss requires a flanker actually inside the pool.
- **ENTAILED / calibration (NO discovery credit claimed):**
  - **C — Bouma's growth law.** `s* = floor(b·ecc)` is monotone in ecc *by construction*
    of `R = b·ecc`. Reported as a consistency check, not as a risked prediction (the
    Troxler-arm-B / Engbert-crossover discipline). `s*/ecc ≈ b` (the constant-fraction
    law) is likewise entailed.
  - **The magnitude `b`.** A **free scale** set as graph data (`CrowdParams.bouma`), NOT a
    biological constant — deliberately **0.6, not Bouma's 0.5** (§13: it does not "fall
    out" of the system; only the numeric crit-spacing values depend on it). The non-gated
    **b-invariance sweep** confirms every qualitative arm holds for `b ∈ {0.4, 0.6, 0.8}`
    — crit spacing scales (`{1,3,4} / {2,4,7} / {3,6,9}`) but crowding, foveal sparing and
    monotonicity are invariant to the constant.

## AUDIT verdict (STEP 1, restated with the outcome)

The eccentricity STRUCTURE (`Foveate`'s center + eccentricity-dependent resolution,
`vision_primitives.rs:113`, `vision_floor.json:16/142`) and the summary-stat CONCEPT
(`vf_summary_stat`) already existed; the LOCAL `Neighbours`→`Filter`→`Count`/`Sum` pooling
fold was proven by the blind-spot rung. What did NOT compose and was ADDED: a pooling READ
whose radius scales with eccentricity and returns the mixed summary (the existing
`Foveate` DECIMATES, it does not pool-and-mix). That composition is `cr_ecc` + `cr_pool`.

## SCOPE — what is NOT shown (§8)

- **Crowding is here a GEOMETRIC critical-spacing model at an abstract item grain**
  (points with an `ident`), not pixel/glyph ink. It validates that eccentricity-scaled
  pooling *entails* the crowding phenomenology; it does not claim a mechanism for WHICH
  features get pooled, nor reproduce the feature-specific similarity effects (target/flanker
  similarity, radial-tangential anisotropy, inner/outer asymmetry) — a NAMED FRONTIER.
- **The pooling summary is a MEAN of a scalar `ident`.** A richer texture statistic
  (higher-order, à la V2 / Freeman-Simoncelli) is not built; the mean is the minimal
  summary that makes "identity lost to the pool" literal.
- **`R = b·ecc` is a MONOTONE radius the rung supplies.** The eye's *current* `Foveate`
  geometry is a STEP (sharp fovea + constant periphery stride), from which foveal-sparing +
  peripheral-crowding fall out but the GRADED Bouma-linear growth does NOT — so the graded
  law is an added assumption of this rung, honestly flagged, not something the existing
  step foveation already contained.
- Licenses nothing about which biological pooling mechanism is correct.

## Believed for the reason the dimensional / blind-spot rungs were

**It FAILS where it must:** isolated targets survive, foveal targets are spared, noise
never false-crowds — and it JUMBLES only a peripheral target with a flanker actually inside
its eccentricity-scaled pool. The two risked arms (B, and the clutter-dependence controls)
could each have failed and did not; the one entailed arm (C) is reported as consistency,
not banked as a discovery.

## §9 — DEFAULTS PRESERVE COMMITTED RESULTS

- Flag `crowd` **OFF by default** (`seeds/vision_crowding.json` ships `crowd=0.0`); Arm F
  inert (all readouts `0.0`).
- **Vision bench** (`scripts/rung7_vision_bench.sh`): **190 passed / 10 skipped** — same as
  the pre-build baseline (10 skipped = `data/`-gitignored corpus, §10.2). *(re-verified
  after the build; see commit.)*
- **sd orbit law** `{2:1,3:2,4:2,6:2,12:4}` unmoved (`test_sdloop_vision_migrated.py -k
  orbit` 2/2).
- **Provenance gate** 7/7; **sibling** `test_border_ownership_migrated.py` 9/9.
- No existing seed, adapter, test or Rust touched — the rung is purely additive
  (`seeds/vision_crowding.json`, `domains/crowding_world.py`, `scripts/crowding_measure.py`,
  `tests/test_crowding_migrated.py`, `tools/build_crowding_seed.py`, one `seed_registry.py`
  registration).

## FILES

- `VISION_CROWDING_PREREG.md` — pre-registration (committed 8703131e, before the run).
- `seeds/vision_crowding.json` — the seed (2 rules, flag OFF); source `tools/build_crowding_seed.py`.
- `domains/crowding_world.py` — world adapter (mechanical I/O only).
- `scripts/crowding_measure.py` — confirmatory runner → `results/crowding_measure.json`.
- `tests/test_crowding_migrated.py` — the gate (8/8).
