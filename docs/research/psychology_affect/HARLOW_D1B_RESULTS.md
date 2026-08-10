# HARLOW D1b — results (block 235000)

Pre-registration: `HARLOW_D1B_PREREG.md` (commit `4a682aadfe07…`, before any
confirmatory number). Base sha **`e1f2b37141…`** (HARLOW D1, block 233000);
descends from current main `3c4666ceba…` (`git merge-base --is-ancestor` = TRUE).
Full data: `results/harlow_d1b.json`. N=200 infants, seeds `default_rng(235000+…)`.

## What was built — population temperament as a DISTRIBUTION
D1 was a near **step-function** (`cloth_frac` sd 0.039, flee sd 0.000, 200/200
preferred cloth) because every infant was the IDENTICAL individual
(`W_CONTACT = W_HUNGER = 1` for all). D1b draws each infant's TEMPERAMENT — its
`contact_comfort` and `hunger` **`Drive.weight`** in the real regulator, the
parameters the attachment value rules read — from a **Normal(μ=1, σ)**
distribution across the population. `worlds/harlow_dist_world.py`
(`HarlowDistWorld(HarlowWorld)`) only WRITES the drawn weights onto the real
`Drive` nodes as attrs and re-runs the graph; **`seeds/harlow_attachment.json`
and `worlds/harlow_world.py` are REUSED UNCHANGED.** The attachment DECISION is
still the Argmax `approach_target` rule riding the real drive+regulator
machinery — no Python decides an infant's attachment. Drawing the weights is
mechanical world setup (like HarvestWorld seeding heterogeneous agents). Because
μ=1 == D1's fixed weight, **σ→0 recovers D1 exactly.**

## Real Harlow data — searched; no per-infant distribution exists
Search availability: WebSearch + WebFetch both WORKED. Searched Harlow (1958)
"The Nature of Love" (read the original PDF end-to-end off disk) and Harlow &
Zimmermann (1959). **Finding: the original papers report only GROUP-MEAN
time-course curves** (Fig 5/6/25: mean hours/day on cloth ≈ 15–18 h vs wire
< 1.5 h; Fig 15 fear test ≈ 80–90% cloth) over a **tiny N (8 dual-mother
infants)** — there are **NO per-infant distributions, no individual-variation
statistics, no between-subject variance or ranges**. So there is **no clean
per-infant distribution to quantitatively fit against.** We therefore report our
reproduced gradation as a **QUALITATIVE reproduction of individual variation, NOT
a quantitative fit** — and label any fit claim LOW confidence by construction.
What we reproduce qualitatively: a graded, **cloth-skewed** distribution (mean
well above 0.5, matching Harlow's overwhelming group cloth preference) with a
**small minority tail** of feeding-preferring individuals.

## Gate outcomes (N=200, headline σ=0.45)
| gate | quantity | D1b result | D1 (step-function) | verdict |
|---|---|---|---|---|
| **G-graded (HEADLINE)** | `cloth_frac` sd | **0.2115** [0.179, 0.242] | 0.039 | **5.4× larger** — GRADED |
| | `cloth_frac` mean | **0.765** [0.736, 0.795] | 0.797 | CI_lo 0.736 **> 0.5** |
| | range (max−min) | **0.933** (min 0.067 → max 1.0) | ~0.17 | spans a range, not a spike |
| | minority-tail (`<0.5`) | **5.0%** (10/200) | 0% | real feeding-preferring minority |
| **G-dose-response** | Pearson `r`(temperament, `cloth_frac`) | **0.856** [0.813, 0.889] | n/a | **POSITIVE, CI excludes 0** |
| **G-variance-tracks-variance** | sd over σ∈{0,.15,.30,.45} | **[0.037, 0.071, 0.119, 0.212]** | — | **monotone**; σ=0 sd 0.037 ≈ D1 |
| **G-ablation (FALSIFIER)** | ablated `cloth_frac` mean | **0.000** [0,0] | 0.000 | collapses to feeding; CI-separated |
| **G-ethics** | restore byte-identical | **True** (idempotent checkpoint) | True | non-oriented; stress fully reversed |
| **G-glass-box** | reconstruct from `graph_to_dict` | **True** (incl. seeded weights) | True | — |
| **G-discipline** | `.so` md5 / dsl diff / oracle / regression | all clean | — | — |

### G-graded PASSES (with one honest prediction-band miss)
Seeding temperament ~Normal turns D1's step-function into a **graded**
distribution: sd **0.2115** (bootstrap 95% CI [0.179, 0.242]) — **5.4× D1's
0.039**, decisively above the pre-registered gate threshold (> 3×0.039 = 0.117).
The distribution spans **0.067 → 1.0** (quantiles: p05 0.498, p10 0.533, p25
0.683, median 0.80, p75 0.883, p90/p95 1.0). Mean **0.765** [0.736, 0.795], CI
lower bound **> 0.5** — contact comfort remains load-bearing on average
(matching Harlow's overwhelming group cloth preference). Minority tail: **10/200
(5%)** infants prefer the feeding mother.
**HONEST MISS:** the pre-registered spread BAND was sd ∈ [0.13, 0.20]; the
confirmatory sd 0.2115 is **just above** the upper bound (the pilot on
non-confirmatory seeds gave 0.162). The miss is on the "MORE spread than
predicted" side (strengthens, not weakens, the graded claim), and the predicted
upper bound 0.20 falls inside the observed sd's own 95% CI [0.179, 0.242] — so
the miss is within the sd's sampling uncertainty. The gate PASS condition
(sd MUCH larger than D1) holds decisively. 7 of 8 pre-registered intervals were
hit; this is the one exceedance, reported straight.

### G-dose-response PASSES (the strong glass-box gate)
Per-infant `cloth_frac` correlates with the infant's DRAWN temperament
(`w_contact − w_hunger`, read back from the graph): **r = 0.856**, Fisher-z 95%
CI **[0.813, 0.889]**, excluding 0. A high-contact-weight infant prefers cloth; a
low-contact-weight infant prefers feeding — a **within-population mechanism
read-out the real experiment never had** (you can read each individual's
temperament AND its outcome).

### G-variance-tracks-variance PASSES
sd(`cloth_frac`) rises **monotonically** with the seeding σ:
`0.037 (σ=0) < 0.071 (σ=.15) < 0.119 (σ=.30) < 0.212 (σ=.45)`. **σ=0 recovers the
D1 near-step-function** (sd 0.037 ≈ D1's 0.039; mean 0.796 ≈ D1's 0.797). The
gradation is CAUSED by the seeding spread, not an artifact.

### G-ablation PASSES (falsifier bites, population-wide)
Removing the `contact_comfort` drive collapses the whole distribution to
feeding-preference: **0/200** infants prefer cloth, mean `cloth_frac` **0.000**
[0,0] — well below 0.5 and CI-separated below the intact population's 0.736 lower
bound. The contact drive CAUSES the attachment; the world is not scripted.

### G-ethics PASSES (induce → measure → RESTORE)
On the confirmatory infant (seed 235000): stress moves the real regulator's
arousal **147 → 347**; restoring the pre-stress **serialised checkpoint** into a
fresh substrate is **byte-identical** and returns the regulator exactly to
pre-stress (arousal 147, non-oriented). The checkpoint is a **serialisation
fixed point** (`graph_to_dict`/`graph_from_dict` idempotent after one pass —
verified). Disclosure: irrational seeded weights expose a **~1-ULP f64
live-graph→serialised quantisation** (`raw_live_roundtrip_max_ulp = 1.42e-14`)
that D1 never saw (its weights were exactly 1.0); it is **STRESS-INDEPENDENT**
(present on a stress-free round-trip too), NOT stress residue. Same mechanism as
the 1958 atrocity, opposite thermodynamics — the induced distress is fully
reversed; nothing persists.

### G-glass-box PASSES
The episode reconstructs from `graph_to_dict` alone, **including the seeded
temperament**: seed-235000 infant has `Drive.weight` contact **1.414** / hunger
**0.726** (temperament +0.688 → prefers cloth: `cloth.proximity 61` vs
`wire.proximity 0`); the real regulator's arousal is **147 comforted** vs **312
on the contact-deprived first tick** (the regulator stabilises with the bond).
Source audit: no Python rule-engine call; the decision is read from the
`approach_target` edge.

### G-discipline PASSES
`runners/dsl` + `term.rs` diff **EMPTY** (no new Rust Term). Canonical `.so` md5
**`10f65be659e0d9a9290aff39f7f5b92a`** unchanged start→end (a real file, not a
symlink; engine built from committed source → `source_match=own`). Oracle
`rung7_vision_bench` **214 passed / 10 skipped** BEFORE == AFTER.
`per_area_settlement_regression` fail-set node-id **SET identical** BEFORE==AFTER
(24 pre-existing conversation/composer/elaboration/gap/topic-route/cortices reds,
none Harlow). Additive new files only (`harlow_dist_*` / `HARLOW_D1B_*`);
`worlds/harlow_world.py` and `seeds/harlow_attachment.json` REUSED UNCHANGED.

## Synthetic-proven mechanism vs benchmark value
This is a **synthetic-proven mechanism**, not a benchmark number. The scientific
claim it supports is architectural: on the (G,Γ) substrate, a POPULATION is a
distribution over temperaments (draws of emotion-seed parameters), and seeding
the real regulator's drive weights ~Normal turns Harlow's step-function into the
GRADED individual variation real monkeys show — cloth-skewed, mean > 0.5, with a
feeding-preferring minority tail — WHILE the attachment rules stay unchanged. The
dose-response (drawn contact weight ⇒ outcome, r=0.856) is a per-individual
mechanism read-out the real experiment could not perform. It is NOT a quantitative
fit to held-out per-infant data (none exists).

## Honest residuals
- **Predicted sd band exceeded** (0.2115 vs [0.13, 0.20]) — reported above; the
  effect is larger than predicted, within the sd's 95% CI, gate passes.
- **The minority tail is enriched for CLIPPED draws.** A drive weight is
  non-negative, so the Normal is floored at 0.05; **12/200 (6%)** infants had a
  weight clipped, and **9 of the 10** tail (wire-preferring) infants sit at the
  `w_contact = 0.05` floor. The Normal's lower tail piles at the floor, so the
  feeding-preferring minority is slightly more concentrated at extreme-low contact
  weight than an unclipped Normal would give. The dose-response spans the full
  temperament range regardless (r=0.856). A truncated/log-normal weight prior
  would remove the pile-up — a documented extension, not done here.
- **Only the two drive weights were drawn ~Normal** (the temperament the
  dose-response reads). Distress/threat sensitivity and regulator gains/thresholds
  were held fixed to keep the baseline dose-response identifiable (the threat
  channel is ≈0 in baseline); drawing those too (a richer temperament, affecting
  the flee phase) is a documented extension.
- **No per-infant real data → qualitative reproduction only**, explicitly not a
  quantitative fit (LOW confidence on any fit claim, by construction).
- **Inherited D1 residuals:** no developmental time-course (per-tick Argmax); the
  `securing` axis is uninformative here (dominated by the competence gap); need-
  decay is a mechanical body process (documented, same status as HarvestWorld
  pool regrowth). Every urge / regulator axis / decision remains in-graph.

## Files
- `HARLOW_D1B_PREREG.md` — pre-registration (commit `4a682aadfe07…`).
- `worlds/harlow_dist_world.py` — NEW adapter (subclass; writes drawn weights).
- `scripts/jabberwock_harlow_dist.py` — NEW runner.
- `tests/test_harlow_dist_migrated.py` — NEW gate (7/7 green).
- `results/harlow_d1b.json` — full N=200 data + headline per-infant table.
- REUSED UNCHANGED: `seeds/harlow_attachment.json`, `worlds/harlow_world.py`.
