# INK × VENTRAL — DOES THE VENTRAL MACHINERY RETROACTIVELY IMPROVE THE HANDWRITING ARC? — RESULTS

*Pre-registered in `VISION_INK_VENTRAL_PREREG.md`, committed **BEFORE** this run at
**`91793bcf`** (§3). Runner `scripts/ink_ventral_measure.py`; primitive
`runners/dsl/src/ink_topology.rs` (new Rust Term `EnclosedCount`); gate
`tests/test_ink_ventral_migrated.py`; pinned raw `results/ink_ventral_measure.json`;
log `results/ink_ventral_measure.log`. Base `main` HEAD **`328065b6`**. Seeds
**54000–54999** claimed; **54000 / 54001 / 54002 consumed, 54003–54999 CLEAN.***

**Provenance (§10.1):** `engine d2f31f7e5a95 @ …/runners/dsl/python/substrate_rs/_native.abi3.so`.
**This rung ADDS RUST**, so the shared-engine route is illegitimate here and
`scripts/engine_build.sh` was run in this worktree — the provenance verdict is **`own`**,
not `shared`. This is the first vision rung in a while to actually exercise §10.1 rule 4.

---

## HEADLINE

**A DIAGNOSED NEGATIVE, and the diagnosis is not the one I pre-registered.**

**None of the three ventral claims improves the handwriting benchmark. Two of them
actively HARM it, both CI-separated at n=400.** But the interesting part is *why*: the
mechanism the ventral grounding names is **real, measurable, and above chance on this
corpus** — and it still costs 18.5 points, because **being above the null is not the same
property as being reliable enough to gate on.** That distinction is this rung's actual
result.

| | measured (n=400) | verdict |
|---|---|---|
| **A0 ADOPTED** (earned quanta) | **24.8%** [20.8, 29.2] | CONTROL — reproduces RUN 15's 26.8% [22.6, 31.3] |
| **A1 SC+TPS FULL DWELL** | **73.2%** [68.7, 77.4] | CONTROL — reproduces RUN 16's 73.5% [67.0, 79.1] |
| **A2 TOPOLOGY ALONE** | **7.0%** [4.9, 9.9] | floor (barely above 5% chance) |
| **A3 SC+TPS + TOPOLOGY GATE** | **54.8%** [49.9, 59.6] | **H1 — HARM, −18.5pp, CI-SEPARATED** |
| **A4 D4-UNTANGLED SC+TPS** | **62.0%** [57.2, 66.6] | **H3 — HARM, −11.3pp, CI-SEPARATED** |
| **H2 complementarity** | A0 on A1's 107 errors = **16.8%** [10.9, 25.0] vs 5% chance | **COMPLEMENTARY** |

Both controls reproduce, every arm beats its own shuffled-label control, the instrument
passes all six exact synthetic cases, and the memory-guard clamp never bound (0/4000
drawings, 0/400 queries) — so the §13 resolution derivation holds for **every** figure
measured. **The negative is earned, not an artefact of a dead harness.**

---

## 1. THE INSTRUMENT IS ALIVE AND EXACT (GATE 0a, §1)

`EnclosedCount` — the new Rust primitive — is exact on all six pre-registered cases, in
BOTH directions (§1 clause 4: a hole-counter that returned 0 everywhere would have
"explained" this whole rung's null and passed a positive-only check):

| figure | want | got | derived grid | derived cell |
|---|---|---|---|---|
| closed circle | 1 | **1** | 42×42 | 0.5235 |
| open 270° arc | 0 | **0** | 54×54 | 0.3927 |
| figure-of-eight | 2 | **2** | 46×46 | 0.4714 |
| two nested circles | 2 | **2** | 44×44 | 0.4886 |
| straight line | 0 | **0** | 5×3 | 10.0000 |
| three scattered points | 0 | **0** | 13×12 | 1.0000 |

**The §13 derivation holds in code and is gated:** the raster resolution is the ink's own
mean inter-sample arc step, so the same circle sampled at n ∈ {40, 120, 400} and at radius
r ∈ {1, 10, 1000} returns **1** every time. Nobody picked a grid size; had anyone, those
would diverge.

---

## 2. GATE 0b/0c — THE PREMISE HELD, AND MY PREDICTION DIED HERE

This is where the rung stopped being the one I expected.

**G0b — WRITER-INVARIANCE: PASS, CI-SEPARATED.** Over 200 classes × 20 drawers = **4000
real drawings**:

- observed modal-agreement **71.5%** [68.4, 74.7]
- class-shuffled null (seed 54001) **56.6%** [55.2, 58.0]

**Topology IS writer-invariant above the marginal null on real Omniglot pen data.** The
ventral grounding's claim survives its own test. I had predicted the opposite (that
hand-drawn counters fail to close often enough to destroy the signal) — **that prediction
was wrong.**

**G0c — INFORMATIVENESS: did NOT refute at the premise.** Per-class modal hole count
`{0: 126, 1: 50, 2: 17, 3: 6, 4: 1}`; entropy **1.4122 bits** over 200 classes; **f0 =
63.0%**, comfortably under the pre-declared 90% refutation line. **The feature is not
near-constant.** I had predicted f0 > 90% and named it as the likely refutation route —
**that prediction was also wrong.**

**Diagnostic (entered NO verdict, §5):** 2900 holes over 4000 drawings (0.72/drawing);
**13.2%** are one-cell micro-loops (pen self-intersections — identified with no threshold,
since one cell is the minimum representable enclosure); the largest hole covers **5.80%**
of the raster (median). So micro-loop contamination is real but is a minority, and it is
**not** the explanation for what follows.

---

## 3. H1 — THE TOPOLOGY GATE HARMS BY 18.5pp, AND THE DIAGNOSIS CLOSES QUANTITATIVELY

**A3 54.8% [49.9, 59.6] vs A1 73.2% [68.7, 77.4] — CI-SEPARATED, −18.5pp.**

Both of my pre-registered escape routes are closed. The feature is *not* unreliable
(G0b passed). The feature is *not* near-constant (G0c passed). **My proviso said in
advance that if both of those held, "the hard gate should give a small positive, and my
reasoning about pen-trajectory closure was wrong." Both held. The gate gave a large
NEGATIVE. So the proviso broke too — and what it exposes is the thing I did not
understand.**

**THE DIAGNOSIS, AND IT CLOSES TO THE POINT:**

> **71.5% modal agreement means 28.5% of drawings DISAGREE with their own class's modal
> hole count. The gate changed A1's winner on 118/400 = 29.5% of episodes.**
> **28.5% ≈ 29.5%.** The fraction of episodes the gate disturbs is the fraction of
> drawings whose topology disagrees with its own class — measured independently, on
> different data, and they land on top of each other.

A **hard** admissibility gate converts a per-item 28.5% disagreement rate into an outright
exclusion of the correct answer on ~28% of episodes. There is no recovery path: once the
true exemplar is excluded, the strong verdict cannot reach it. The gate admitted a mean
**12.05/20** candidates and fell back to all-20 only **7** times, so it was not
pathologically strict on average — **the damage is concentrated exactly where the feature
is wrong**, which is the failure mode a hard gate is built to have.

**THE GENERALIZABLE FINDING — and it is the one worth carrying forward:**

> **ABOVE-THE-NULL IS NOT GATE-GRADE. A feature can be CI-separated from its own chance
> baseline and still be catastrophic as a hard admissibility constraint, because a gate
> pays the feature's ERROR RATE, not its EFFECT SIZE.** 71.5% invariance sounds strong and
> is genuinely non-trivial; as a hard gate it is a 28.5% chance of destroying the answer.

**A2 (topology alone) at 7.0% [4.9, 9.9]** is the corroborating floor: barely above 5%
chance, with a mean **12.13/20** candidates tied at the winning |Δholes|. Topology's
information content is real (1.41 bits) but is nowhere near sufficient to discriminate 20
classes on its own — consistent with everything above.

---

## 4. H2 — CONTOUR AND DUCTUS *ARE* COMPLEMENTARY (the one claim that survives)

**A0's accuracy on the 107 episodes where A1 is WRONG: 16.8% [10.9, 25.0], CI lower bound
10.9% > 5.0% chance ⇒ COMPLEMENTARY.**

The earned-quanta (ductus/construction) read recovers **18 of the 107** episodes the
continuous contour verdict misses — more than three times chance. **The two reads carry
genuinely independent information**, which is direct measured support for this project's
standing "the answer is BOTH" position at this specific seam.

**And the honest bound, which I also predicted in advance:** the headroom is small. The
oracle-union ceiling (either arm correct) is **77.8% [73.4, 81.6]** against A1's **73.2%
[68.7, 77.4]** — **+4.6pp, and the CIs OVERLAP.** Both arms are correct together on
81/400. So:

> **H2 is a CI-separated fact about INFORMATION and a NON-CI-separated fact about
> ATTAINABLE ACCURACY.** The complementarity is real; the ceiling it opens is not yet
> distinguishable from A1 at n=400. **No fusion mechanism was built or tested here, and
> none is claimed.** A rung that wants the 4.6pp must pre-register a fusion and power it —
> and should note that a perfect oracle is required to get all of it.

**A POST-HOC OBSERVATION, LABELLED AS SUCH (it changed no decision rule, §5).** The
pre-registered test was against the 5% chance floor and it passed. But there is a second,
stricter reading worth recording because it sharpens what "complementary" means here: under
**independence** of the two arms' errors, A0's accuracy on A1's error set would equal A0's
*unconditional* accuracy, **24.8%**. Measured: **16.8% [10.9, 25.0]** — the interval
**contains 24.8%**, so independence cannot be rejected either. So the honest statement is:

> **A0's errors are measurably NOT the same as A1's (well above chance), and are not
> distinguishable from INDEPENDENT of A1's.** That is exactly the regime in which the
> oracle-union headroom is small and real — and it is why +4.6pp, not something larger, is
> the expected ceiling. Two independent sources at 24.8% and 73.2% simply do not stack to
> much.

This is the prediction I got right, including its size.

---

## 5. H3 — D4 UNTANGLING HARMS BY 11.3pp, EXACTLY AS THE PRE-REGISTERED RISK SAID

**A4 62.0% [57.2, 66.6] vs A1 73.2% [68.7, 77.4] — CI-SEPARATED, −11.3pp.**

The pre-registration named this outcome and its mechanism before the run:

> *"D4 rotation is, for handwriting, frequently an identity-CHANGING transform, not a
> nuisance one. Many scripts contain character pairs that differ ONLY by rotation or
> reflection. Quotienting D4 out therefore DESTROYS discriminative information at the same
> time as it removes nuisance. A CI-separated DECREASE is a fully expected outcome and
> will be reported as the result, not as a bug."*

**That is what happened.** Minimizing over the earned group lets a foil that is a rotation
or reflection of the query win, and on scripts built from rotated/reflected strokes that is
a large class of foils.

**AND IT IS NOT A CHEAP LOSS: A4 cost 153.7s over 64 000 compares against A1's 19.2s over
8 000 — 8× the compute for −11.3pp.**

**THE BOUND THIS PUTS ON THE CROSSING — and it is the honest reading of a result this tree
already owns.** `VISION_IDENTITY_UNTANGLING_RESULTS.md` (seeds 37000–37999) established
generator-orbit identity as a **bounded CROSSING** on synthetic objects under held
invertible discrete-similarity generators. That result stands and is not disturbed here.
What this rung adds is the transfer measurement:

> **The discrete-similarity untangling crossing does NOT transfer to real handwriting, and
> the reason is not that the mechanism fails — it is that on this domain the group is
> WRONG.** Handwriting's nuisance is continuous deformation; D4 is not a subgroup of it in
> any useful sense, and D4 *is* a subgroup of the identity distinctions the task requires.
> **Untangling the wrong group is worse than not untangling.**

This is the arc's own standing rule in a new instance: **synthetic-proven mechanism ≠
benchmark value.** Both facts are reported, clearly separated: the mechanism works (37k
rung, 8/8); the transplant costs 11.3 points (this rung, n=400).

---

## 6. MY PREDICTIONS, SCORED (§3.7)

Being right in advance is the only evidence I understood the model; a broken proviso is
what I did not understand.

| hypothesis | predicted | measured | verdict on the prediction |
|---|---|---|---|
| **H1** | NULL, most likely via G0c refuting at the premise (f0 > 90%) | **HARM −18.5pp**; f0 = 63.0%; G0b and G0c BOTH passed | **WRONG, twice over — and the PROVISO broke too** |
| **H2** | COMPLEMENTARY but small | COMPLEMENTARY (16.8% [10.9, 25.0]); oracle union +4.6pp, CIs overlap | **RIGHT, including the size** |
| **H3** | NULL or CI-separated HARM, because D4 is identity-changing for real scripts | **HARM −11.3pp**, CI-separated | **RIGHT, including the mechanism** |

**WHAT I DID NOT UNDERSTAND (the H1 proviso, stated plainly):** I treated
"writer-invariant above the null" and "reliable enough to be a hard constraint" as the same
property. They are not. A gate is priced by its error rate; a feature is scored by its
effect size. I pre-registered a premise check (is the feature informative?) and an
invariance check (is it above chance?) and **neither of those is the check a hard gate
actually needs**, which is: *what fraction of the time does this feature exclude the truth?*
That check did not exist in my design and had to be reconstructed after the fact from
G0b's own number. **A future rung proposing any hard admissibility gate should pre-register
that quantity directly.**

---

## 7. A CORRECTION TO THE PRE-REGISTRATION (§7 — retract when the evidence turns)

**`VISION_INK_VENTRAL_PREREG.md` §8 states: *"no border-ownership rung exists in this
tree."* THAT IS FALSE, and I am recording the correction rather than quietly editing it.**

`VISION_BORDER_OWNERSHIP_PREREG.md` / `_RESULTS.md`, `seeds/vision_border_ownership.json`
and `tests/test_border_ownership_migrated.py` exist and pass **8/8** confirmatory arms,
including the Zhou context-dependence signature (a byte-identical local edge FLIPS
ownership with the global figure) and figure-ground on a closed figure.

**The accurate statement is the more useful one, and it strengthens this rung's negative
rather than weakening it:** border-ownership and proto-objects ARE built here — on
**synthetic raster grids**, where enclosure is exact. This rung is the first to take the
enclosure consequence to **real ink**, and it needed a new ink-side primitive because the
handwriting pipeline never rasterizes. **So the mechanism was already proven before this
rung ran, which means the 18.5pp loss is a fact about ink and about hard gating — not
about whether enclosure computation works.**

---

## 8. BOUNDS — what is NOT shown (§8)

- **The baseline is RUN 16's 73.2/73.5%, NOT the arc's 80.5%** [76.3, 84.1] terminal bound
  from the runs-17–46 proposal campaign. Declared in the pre-registration before the run
  and repeated here. **Nothing in this rung may be quoted against 80.5%.**
- **Eval-subset coverage:** Omniglot `strokes_evaluation`, the RUN 15/16 ten alphabets
  (Angelic, Atemayar_Qelisayer, Atlantean, Aurek-Besh, Avesta, Ge_ez, Glagolitic, Gurmukhi,
  Kannada, Keble), one-shot **20-way, within-alphabet, cross-drawer**, R=2, **n = 400**.
  LEARN on 5 background alphabets, 1500-stroke cap, codebook saturating at **7** quanta
  (identical to RUN 15/16).
- **H1 bounds a HARD gate ONLY.** A soft/weighted topology term, a topology-as-tie-break,
  or topology as a PROPOSAL feature were **not tested** and are not refuted. The
  measurement says a hard equality gate on this feature costs 18.5pp; it says nothing
  about a calibrated soft one. *(A weight would also have needed a §13 derivation, which is
  precisely why the hard gate was chosen — it has no free parameter.)*
- **H3 bounds ONE group — D4** (`rotation90` + reflections), the group the wall crossing
  actually earned. It does not bound untangling in general, and it does not disturb the
  37k rung's synthetic crossing.
- **Topology here is computed from PEN TRAJECTORIES**, not from images. An image-derived
  contour with true border-ownership is a different instrument; this null does not refute
  topology-from-images.
- **H2 shows INFORMATION complementarity, not an achieved gain.** No fusion was built.
- Nothing about one-shot learning beyond Omniglot; nothing about other scripts, other
  ways, or n beyond 400.
- **The per-compare timings are UPPER BOUNDS**: two other CPU-bound processes shared this
  machine during the run. Accuracies are deterministic under the fixed seed and are
  unaffected.
- **`cargo test` cannot link in this crate** (pyo3 `extension-module` leaves libpython
  symbols undefined) — **verified PRE-EXISTING on unmodified source** (20 undefined
  symbols at base). The Rust unit tests in `ink_topology.rs` therefore do not execute in
  CI; **the instrument is gated through the Python engine instead**, which is the stronger
  test anyway since it exercises the real Term dispatch. Reported, not worked around.

---

## 9. §9 — DEFAULTS PRESERVE COMMITTED RESULTS

- **`EnclosedCount` is constructed by NO seed, rule or adapter** — gated by
  `test_EnclosedCount_is_constructed_by_NO_seed` (a scan of every `seeds/*.json`). It is
  purely additive: nothing that ran before this rung can reach it.
- **The Rust surface is exactly six files**, all mechanical Term registration plus the new
  module: `ink_topology.rs` (new), `term.rs`, `shape.rs`, `jsonio.rs`, `reflect.rs`,
  `lib.rs`. Pinned and gated as an exact set.
- **No seed, no adapter, no earlier rung's script was edited** — gated
  (`test_this_rung_edits_NO_earlier_rungs_seed_or_measurement`).
- **sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` re-measured UNMOVED** on this rung's own
  engine, both via `tests/test_sdloop_vision_migrated.py` and directly in this rung's gate.
  *Stated precisely rather than over-claimed:* `predicted_orbits` is Python and is
  **byte-untouched** by this rung's diff, so "unmoved" is also true by inspection — the
  re-measurement is the check that the ENGINE did not move it underneath.
- **THE STRONGEST §9 FORM AVAILABLE TO A RUNG THAT ADDS RUST, and it is gated:** the whole
  engine diff `328065b6..73efd7d0` is **404 insertions and exactly 2 deletions**, and both
  deletions are `shape.rs` match arms rewritten *solely* to append `| EnclosedCount`. **No
  pre-existing code path was altered at all**, which is why no committed result can move.
  `test_the_RUST_DIFF_IS_PURELY_ADDITIVE` asserts this against the fixed commit range and
  checks each deleted line has an additive twin.
- **`scripts/rung7_vision_bench.sh`: 200 passed / 0 failed WITH `data/` symlinked** (§10.2 —
  a bench number without its condition is 5% vacuous), measured on **this rung's own engine
  `d2f31f7e5a95`**. Identical to the committed baseline.
- **Sibling gates, 112 passed in ONE process:** sdloop-vision · border-ownership ·
  identity-untangling · dimension-inference · transform-decode · ink-decode ·
  engine-provenance · this rung's gate.
- **This rung's gate: 23/23**, positive-controlled in both directions (§7 below).

### `pytest tests/ -k migrated`: 25 failed / 3351 passed / 73 skipped / 5 errors (48:48)

The 5 errors are the standing missing-`chess` optional-dep collection errors. **Of the 25
failures, 23 are PRE-EXISTING — MEASURED, NOT ASSUMED — and 2 ARE MINE.**

**THE 23: measured pre-existing by an engine swap.** My first PRE-change baseline attempt
was cut off by my own 3000s `timeout` at 96% (exit 124), so a name-level pre/post diff from
that run was unavailable. Rather than argue from the additive diff alone, I **built a
BASE-SOURCE engine** (base `.rs` restored from `328065b6`, `ink_topology.rs` removed,
`engine_build.sh` → engine `4ccfea943ac8`) and re-ran the exact failing subset:

| engine | the 12 affected files |
|---|---|
| this rung's `d2f31f7e5a95` | **23 failed, 53 passed** |
| base-source `4ccfea943ac8` | **23 failed, 53 passed** |

**Identical.** The 23 (document-memory, run67, run82, varcomp, theorems-as-terms,
speech-act-parity, reading-parity, topic-span, temporal-pattern, live-loop,
previsual-vacuity, comprehension-self-optimisation) are unaffected by this rung. The engine
was then restored to `d2f31f7e5a95` and the rung gate re-verified 23/23.

### THE 2 THAT ARE MINE — and they are the §12.3 defect firing for the FOURTH time

**I caused these, they are false accusations, and I am reporting them rather than fixing
them (§11 rule 4: do not edit another rung's tests).**

| test | what it does | why it fired |
|---|---|---|
| `test_lighting_l3b_migrated.py::test_the_tail_after_the_pin_adds_no_Rust_and_no_seed` | diffs `rung_commit_sha..HEAD`, asserts no `.rs` | assumes *"the only commits after the pinned rung commit are... doc-only"* — false the moment any later rung adds Rust |
| `test_margin_migrated.py::test_this_rung_adds_NO_Rust` | diffs `07eeda24..HEAD`, asserts no `.rs` | its docstring says *"pinned to THIS RUNG'S OWN DIFF (§12.3), base..HEAD"* — **self-contradictory: `base..HEAD` is NOT the rung's own diff, because HEAD moves** |

**Neither claim is actually false. L3b still adds no Rust; the margin rung still adds no
Rust. This rung does — legitimately, gated, §9-verified, provenance `own`.** This is
verbatim the pattern §12.3 records:

> *"The two-eyes rung then added `PickUnique` (a legitimate, gated, §9-verified Rust Term)…
> and both gates fired. Rung 8B still added no Rust. The gates were making a false
> accusation."*

**§12.3 says this defect has occurred three times. This is the fourth and fifth instance,
and the margin one is the sharper finding: it CITES §12.3 in its own docstring while
violating it.** The reason both lay dormant is that **no rung had added Rust since they
were written** — the vision arc's Rust source was byte-identical across 51 commits. This
rung is the first to add Rust in a long while, which is exactly why it is the one that
exposed them.

**RECOMMENDED FIX (named, NOT built — not my files):** pin both to their own commit range,
as `test_this_rung_ADDS_RUST_and_says_so` in this rung's gate does. The margin test needs
a `rung_commit_sha`; L3b's already has one in its pin file and simply needs to use it for
the tail assertion too, or drop the tail assertion (its own docstring already concedes the
PRIMARY claim is the fixed range).

**The §9 conclusion is unchanged and now rests on measurement rather than inference:** no
pre-existing behaviour moved. The two red gates are provenance bookkeeping about *other*
rungs' commit ranges, not a regression in anything this rung touched.

---

## 9b. THE GATE IS POSITIVE-CONTROLLED IN BOTH DIRECTIONS (§12.3)

*A gate you have only ever seen pass is not a gate you have tested — and a gate over a
NEGATIVE has a specific way of being worthless: it passes on a build where nothing works,
because a dead instrument would "explain" the null.* Both injections were run, and the
result is the important part:

| injection | what went RED | what stayed GREEN |
|---|---|---|
| **DEAD INSTRUMENT** — `EnclosedCount` returns 0 always, engine rebuilt | `test_G0a_the_six_synthetic_controls_are_EXACT`, `test_the_resolution_is_SAMPLING_DERIVED_not_chosen` (**2 red**) | **every pinned verdict** — H1, H2, H3, overall, G0b/G0c |
| **FALSE VERDICT** — pins say `CROSSES` / `CROSSING` / a3 = 0.9 | `test_H1_verdict_is_pinned`, `test_the_overall_verdict_is_pinned` (**2 red**) | **the whole instrument battery** |

**Each injection reddens exactly what the other passes. Neither half is a gate; the
CONJUNCTION is.** Both were reverted and the suite returned to green (23/23), verified.

## 10. SEEDS CONSUMED

**54000** powered run master rng · **54001** G0b class-shuffled null · **54002**
shuffled-label controls. **54003–54999 remain CLEAN.** 12000–53999 untouched by this rung.
