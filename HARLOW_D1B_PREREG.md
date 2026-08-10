# HARLOW D1b — pre-registration (block 235000)

**Population temperament as a DISTRIBUTION: seed each infant's emotion
parameters ~Normal across the population to reproduce the GRADED individual
variation real monkeys show, on the (G,Γ) gamma-substrate riding the REAL
emotion framework.**

Seed block: **235000–235999** (verified CLEAN by `python scripts/seed_claim.py
235000 235999` — verbatim `check_claim` report below). This document contains
PREDICTED ranges + gate definitions and **NO measurements**. Committed BEFORE
any confirmatory number.

Base sha: **`e1f2b37141e276974d1743c1e147f019b8d97b64`** (HARLOW D1, block 233000,
"contact comfort is load-bearing, via the REAL regulator"). Descends from
current main `3c4666ceba0b0ceef1db4030d941a5cd66b5f949`
(`git merge-base --is-ancestor` = TRUE).

Verbatim `check_claim(235000, 235999)`:
```
SEED CLAIM 235000-235999: CLEAN -- no collision DETECTED.
  Scope: 955 files with seed sinks; 657 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## The finding to extend
HARLOW D1 (block 233000) replicated Harlow (1958): the infant prefers the
CONTACT (cloth) mother over the FEEDING (wire) mother, via the real regulator.
But D1 was a near **step-function**: `cloth_frac` sd = 0.039, flee sd = 0.000,
200/200 infants preferred cloth. The reason (D1's own honest residual): **every
infant was the IDENTICAL individual** — `W_CONTACT = W_HUNGER = 1` for all;
randomisation only perturbed init/decay within narrow bands. Real monkeys show
GRADED individual variation.

## The scientific idea
A population IS a distribution over temperaments; in this substrate a temperament
is a draw of emotion-seed parameters. So: draw each infant's **contact-comfort
and hunger drive weights** (`Drive.weight` in the real regulator, the parameters
the attachment value rules read) from a **Normal distribution** across the
population, and show the attachment measure becomes GRADED. Drawing per-agent
params ~Normal and writing them as node attrs is MECHANICAL world setup (exactly
like HarvestWorld seeding heterogeneous agents) — **NOT a Python decision**. The
attachment RULES (`seeds/harlow_attachment.json`) are UNCHANGED; only the seeded
temperament varies.

## Apparatus (frozen at prereg) — ADDITIVE, D1 REUSED UNCHANGED
- `seeds/harlow_attachment.json` — **REUSED UNCHANGED** (the value rules
  `hl_value_contact_mother` / `hl_value_feed_mother` read `Drive.weight`; the
  Argmax `approach_target` decision is these rules, no Python).
- `worlds/harlow_world.py` — **REUSED UNCHANGED**.
- `worlds/harlow_dist_world.py` — NEW. `HarlowDistWorld(HarlowWorld)`: after
  D1's `__init__`, it WRITES the per-infant drawn `w_contact` / `w_hunger` onto
  the real `contact_comfort` / `hunger` `Drive` nodes as `weight` attrs and
  re-runs the graph. That is its ONLY addition. Under ablation there is no
  contact Drive to carry a weight, so `w_contact` is simply not applied.
- `scripts/jabberwock_harlow_dist.py` — NEW runner. Draws the temperament
  (mechanical), reduces the population to a distribution + dose-response +
  variance sweep + ablation, reads every decision off the graph.
- `tests/test_harlow_dist_migrated.py` — NEW gate.

## Confirmatory protocol (frozen — measured AFTER this commit)
- `N = 200` infants. Infant `i` uses `numpy.default_rng(seed)`. Per infant, in
  ONE stream, **first** the D1 init draws (identical order to D1):
  `c_contact0 ~ U(10,60)`, `c_hunger0 ~ U(20,80)`, `contact_decay ~ U(50,70)`,
  `hunger_decay ~ U(10,20)`; **then** the temperament:
  `w_contact ~ Normal(μ=1, σ)`, `w_hunger ~ Normal(μ=1, σ)`, each floored at
  0.05 (a drive weight is non-negative; the Normal tail below 0.05 is clipped —
  the clip count is REPORTED). `μ=1` == D1's fixed weight, so **σ→0 recovers D1
  exactly**.
- **Seed allocation inside 235000–235999** (each infant seeded once):
  headline intact σ=0.45 → `235000+i`; ablation reuses `235000+i` (paired, drive
  OFF); variance grid σ=0.00 → `235200+i`; σ=0.15 → `235400+i`; σ=0.30 →
  `235600+i`; the σ=0.45 grid point == the headline (reused).
- **Baseline phase:** `T_base = 60` ticks, no stress. Record
  `cloth_frac = cloth_ticks / (cloth_ticks + wire_ticks)` per infant.
- **Stress phase:** `T_stress = 10` ticks. Record `flee_cloth`.
- **Headline seeding σ = 0.45** (the widest grid point). Variance grid
  σ ∈ {0.00, 0.15, 0.30, 0.45}.
- **Temperament read-out** (dose-response x-axis): `temperament = w_contact −
  w_hunger`, READ BACK from the graph (`Drive.weight`), not the Python draw.
- 95% CIs: mean by normal approx `mean ± 1.96·sd/√N`; sd by bootstrap (4000
  resamples); dose-response `r` by Fisher-z.

## Gates (each has a control that CAN fail) — pre-registered BEFORE any number
- **G-graded (HEADLINE):** at σ=0.45 the population `cloth_frac` is GRADED —
  **sd > 3 × 0.039 = 0.117** (MUCH larger than D1's step-function sd),
  predicted spread band **sd ∈ [0.13, 0.20]**; the distribution **spans a range**
  (max − min > 0.5, NOT a spike); mean `cloth_frac` CI lower bound **> 0.5**
  (contact comfort still load-bearing on average). Report full distribution
  (mean, sd, quantiles, minority-tail fraction = infants with `cloth_frac`<0.5)
  with 95% CIs. Control that can fail: if seeding temperament left the measure a
  spike (sd ≈ D1's), or flipped the mean below 0.5, the gate fails.
- **G-dose-response (strong glass-box gate):** per-infant `cloth_frac`
  correlates POSITIVELY with drawn `temperament` (= contact weight − hunger
  weight); Pearson `r` **> 0** with Fisher-z 95% CI **excluding 0**. Predicted
  `r ∈ [0.65, 0.95]`. A within-population mechanism read-out the real experiment
  never had. Control: a zero/negative correlation falsifies the claimed
  mechanism.
- **G-variance-tracks-variance (control that can fail):** sd(`cloth_frac`)
  increases MONOTONICALLY across σ ∈ {0.00, 0.15, 0.30, 0.45}; **σ=0 recovers
  the D1 near-step-function** (sd ∈ [0.02, 0.06], i.e. < 2 × 0.039). Predicted
  sds roughly {≈0.04, ≈0.06–0.08, ≈0.10–0.13, ≈0.14–0.19}. Control: a
  non-monotone sweep, or σ=0 NOT recovering the step-function, fails.
- **G-ablation (falsifier, population-wide):** removing the contact_comfort drive
  collapses the distribution to feeding-preference — mean `cloth_frac` **< 0.10**
  (well below 0.5), CI upper bound below the intact population's CI lower bound.
  Predicted ablated mean ∈ [0.00, 0.05]. Control: if ablation does not move it,
  the mechanism is fake — reported straight.
- **G-ethics:** induce → measure → RESTORE. A checkpoint is the SERIALISED mind;
  `graph_to_dict`/`graph_from_dict` is idempotent after one pass (a
  serialisation fixed point — this is verified and reported). Checkpoint the
  neutral pre-stress mind; induce the stress phase; rebuild from the checkpoint
  and assert `graph_to_dict()` is BYTE-IDENTICAL to the checkpoint; the restored
  regulator is non-oriented (back to pre-stress). The live-graph→serialised
  quantisation is a ~1-ULP f64 effect exposed by irrational seeded weights (D1
  never saw it — its weights were exactly 1.0); it is STRESS-INDEPENDENT and is
  quantified in the report (`raw_live_roundtrip_max_ulp` ≈ 1e-14), NOT stress
  residue. Ends non-oriented; nothing persists — same mechanism as the 1958
  atrocity, opposite thermodynamics.
- **G-glass-box:** the episode reconstructs from `graph_to_dict` alone —
  including the SEEDED temperament (`Drive.weight`, a per-individual read-out the
  real experiment never had), the `approach_target` edge, the mothers'
  proximity, and the regulator arousal (comforted < deprived). Source audit: no
  Python `if/else` decides attachment (the decision is the Argmax rule).
- **G-discipline:** agent = graph (real emotion framework); world = mechanical
  adapter; `runners/dsl` + `term.rs` diff EMPTY (no new Rust Term); canonical
  `.so` md5 unchanged start→end; oracle pass-count identical before/after (main
  214 passed / 10 skipped); regression fail-set node-id SET identical (24
  pre-existing reds); additive new files only (`harlow_dist_*` / `HARLOW_D1B_*`);
  `source_match=own` (engine built from committed source).

## Predicted intervals (prereg — informed by mechanism design + a pilot on
## NON-confirmatory seeds `default_rng(940000+…)`; the confirmatory run uses the
## 235000+ block)
| quantity | predicted interval |
|---|---|
| `cloth_frac` mean (σ=0.45, intact) | **[0.70, 0.85]** |
| `cloth_frac` **sd** (σ=0.45) — the spread band | **[0.13, 0.20]** (and > 0.117) |
| `cloth_frac` range span (max − min) | **> 0.5** |
| minority-tail fraction (`cloth_frac` < 0.5) | **[0.005, 0.10]** |
| dose-response Pearson `r` (temperament vs `cloth_frac`) | **[0.65, 0.95]**, CI excludes 0, **POSITIVE** |
| sd at σ=0 (D1 recovery) | **[0.02, 0.06]** |
| sd monotone over σ ∈ {0,0.15,0.30,0.45} | **YES** |
| `cloth_frac` mean (ablated) | **[0.00, 0.05]**, CI-separated below intact |

**Dose-response sign: POSITIVE** (more contact weight relative to hunger ⇒ more
cloth preference). A null/negative dose-response, a non-graded distribution, a
non-monotone variance sweep, or a failed ablation IS a result and will be
reported straight.

## Real Harlow data
We will SEARCH for Harlow (1958/1959) reported per-infant attachment
distributions (search availability stated in the results). Old papers give
aggregate time-on-mother, not clean per-infant distributions; if no per-infant
distribution data exists we will report our REPRODUCED GRADATION as a
**qualitative reproduction of individual variation, NOT a quantitative fit**, and
label it so. A novelty/absence or fit claim without search is LOW confidence by
construction.

## Discipline
Python-only (no new Rust Term; `runners/dsl` + `term.rs` diff EMPTY). Additive
new files (`harlow_dist_*` / `HARLOW_D1B_*`); `worlds/harlow_world.py` and
`seeds/harlow_attachment.json` REUSED UNCHANGED. `source_match=own`.
Measure-first; this prereg precedes every confirmatory number. Synthetic-proven
mechanism vs benchmark value reported separately. No merge to main; commits stay
on the worktree branch for the supervisor.
