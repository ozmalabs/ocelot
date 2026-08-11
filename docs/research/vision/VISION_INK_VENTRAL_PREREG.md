# INK × VENTRAL — DOES THE VENTRAL MACHINERY RETROACTIVELY IMPROVE THE HANDWRITING ARC? — PRE-REGISTRATION

*Written and **COMMITTED BEFORE THE RUN** (§3). Base `main` HEAD **328065b6**
(`git merge-base --is-ancestor 328065b6 HEAD` verified, §11). Branch
`gamma-substrate/vision-ink-ventral`, worktree
`.claude/worktrees/agent-aa9def1a0f13b03bb`. Seeds **54000–54999** — the block is
**CLEAN**, verified against the burned-seed ledger below. New Rust Term
`EnclosedCount` is **PURELY ADDITIVE** and constructed by **NO** existing seed, rule
or adapter (§9 by construction — byte-identity to be proven, not assumed).*

---

## 0. THE CLAIM UNDER TEST

`VISION_VENTRAL_GROUNDING.md` (2026-07-18) grounded the ventral "what" phase and made
three build-implication claims. This rung asks whether any of them **retroactively
improve this project's own handwriting arc** — the one benchmark in this tree where a
strong, powered, CI-gated one-shot number already stands.

**This is a RETRODICTION test, and it is the honest kind: the benchmark, the protocol,
the controls and the standing numbers were all fixed BEFORE the ventral grounding
existed.** Nothing here can be tuned to make the grounding look good.

---

## 1. THE STANDING NUMBERS THIS RUNG MUST NOT MISQUOTE

Quoted with their scope (§8), from the sources named:

| number | what it is | source |
|---|---|---|
| **26.8% [22.6, 31.3]**, n=400 | the powered honest ceiling of the EARNED-QUANTA pipeline, one-shot 20-way, 10 alphabets | RUN 15, `results/omniglot_gate_run15_power_b.log`, CLAUDE.md "RUN 15 CORRECTION" |
| **22.0% [16.8, 28.2]**, n=200 | RUN 16's own re-measurement of that same `adopted` arm (CI-overlapping ⇒ consistent) | `results/omniglot_gate_run16_reconcile.log` |
| **73.5% [67.0, 79.1]**, n=200 | SC+TPS FULL DWELL — a **BORROWED** continuous verdict grafted on, not earned by the substrate | RUN 16, same log |
| **48.0% [41.2, 54.9]**, n=200 | SC+TPS on the earned shortlist ("bins propose, continuous decides" in its literal form) | RUN 16, same log |
| **+21pp** | COMPOSITION over multiset — the ONE CI-separated effect the earned-quanta side ever produced | CLAUDE.md "RUN 15 CORRECTION" |
| **coverage@shortlist 53.0%** | proposal recall; mean shortlist size 4.33 | RUN 16, same log |
| **80.5% [76.3, 84.1]** | the LATER terminal verdict bound after the runs 17–46 proposal campaign — **a different, larger pipeline** | `OMNIGLOT_ARC.md` Addendum |

**SCOPE NOTE, DECLARED IN ADVANCE.** This rung deliberately builds on the **RUN 16
harness** (`scripts/jabberwock_omniglot_run16_reconcile.py`), i.e. the
`ADOPTED` / `SC+TPS FULL DWELL` pair, **NOT** the runs-17–46 80.5% pipeline. Reason:
the RUN 16 pair is the **minimal honest contrast** between the earned layer and the
borrowed verdict, which is exactly what the three ventral claims speak to; the 80.5%
pipeline adds twelve further mechanisms whose interaction would confound every arm.
**Consequence, stated up front: a positive here would be a positive against a 73.5%
baseline, NOT against the arc's best 80.5%, and must never be reported as the latter.**

---

## 2. THE THREE HYPOTHESES

### H1 — TOPOLOGY (counters / enclosed regions) AS A FIRST-CLASS PROTO-OBJECT FEATURE

*Ventral grounding: border-ownership → figure-ground → enclosure; "proto-objects are
BEFORE the wall". Topology (how many holes, how they nest) is claimed to be one of the
most writer-INVARIANT features that exists — an 'A' has one counter whoever writes it.*

**The ink pipeline currently has NO topological feature of any kind** — verified by
inspection: `domains/ink_decode.py`, `domains/stroke_codebook.py`,
`domains/character_compose.py` and `domains/abs_read.py` carry only turn/length quanta,
pose bins, relative-pose arrangement relations, and continuous point-set metrics. No
enclosure, no genus, no Euler number.

**H1:** adding the query's own enclosed-region count as a HARD ADMISSIBILITY GATE on the
verdict's candidate set raises one-shot 20-way accuracy above the SC+TPS full-dwell
baseline.

### H2 — CONTOUR / FIGURE-GROUND **COMPLEMENTS** DUCTUS (both, not either)

*This project's standing position ("YOU DON'T HAVE TO CHOOSE — the answer is BOTH").
The existing arc reads strokes as CONSTRUCTION (ductus: earned stroke quanta +
arrangement). The continuous point-set read (SC+TPS on raw normalized ink) is a
different, co-present source of evidence.*

**H2:** the two reads are genuinely COMPLEMENTARY — i.e. on the episodes where the
contour read (`SC+TPS`) is WRONG, the ductus read (`ADOPTED`) is right MORE OFTEN THAN
CHANCE. This is a claim about information, **not** about a fusion mechanism, and it is
measured on the same episodes with no new arm.

### H3 — IDENTITY-UNTANGLING AS THE PRINCIPLED REPLACEMENT FOR THE SC+TPS GRAFT

*Ventral grounding's headline crossing: "untangling ≡ generator discovery. Identity =
the generator-invariant residual; nuisance = the generator parameter." The 26.8% → 73.5%
gap is currently closed by a bolt-on. If untangling is the real mechanism, quotienting
out the discovered transform group should close some of that gap in a way the substrate
EARNS.*

**The transplant must import the group the wall crossing ACTUALLY EARNED, not a
convenient one.** That group is DISCRETE: `shape_decode.rs`'s `DimensionGenerator`
codebook is `rotation90` + reflections — the **dihedral group D4** (8 elements:
rotations by 0/90/180/270 × {identity, reflection}). Scale and translation are ALREADY
quotiented out upstream by `abs_read.whole_figure_point_set` (centre + abs-max
normalize; orientation deliberately KEPT). So the untangling transplant is exactly:
**identity := min over g ∈ D4 of d(g·query, candidate)**.

**H3:** that generator-invariant residual, as the verdict, beats the raw SC+TPS verdict.

---

## 3. THE HONEST RISK, STATED BEFORE THE RUN (this is the pre-registered warning)

**The wall crossing is bounded to a DISCRETE SIMILARITY group. Handwriting variation is
CONTINUOUS and DEFORMABLE — and this project's own deformation rung was a clean
diagnosed NEGATIVE** (identity-preserving and identity-changing deformation bands
overlap, so no threshold separates them; `VISION_*` deformation record + the run-44
"learned deformation metric" null at 79.5%). **There is therefore a real, pre-registered
possibility that H3 does not transfer at all.**

Worse, and stated now rather than discovered later: **D4 rotation is, for handwriting,
frequently an identity-CHANGING transform, not a nuisance one.** Many scripts contain
character pairs that differ ONLY by rotation or reflection. Quotienting D4 out therefore
DESTROYS discriminative information at the same time as it removes nuisance. **A
CI-separated DECREASE is a fully expected outcome and will be reported as the result,
not as a bug.**

---

## 4. THE INSTRUMENT — `EnclosedCount`, and its magic-number derivation (§13)

New Rust Term (`runners/dsl/src/term.rs` + `vision_primitives.rs`), purely additive:

```
EnclosedCount { a }   -- a : list of strokes, each a list of [x, y]
                      -> Dict{ holes, grid_w, grid_h, cell, n_samples, clamped }
```

Mechanism: rasterize each stroke's polyline (Bresenham, 8-connected foreground), flood
the background 4-connected from the raster border, count the remaining background
components. 8-connected foreground / 4-connected background is the **standard consistent
digital-topology pairing** — declared, not tuned.

**THE ONE NUMBER THAT COULD BE MAGIC IS THE RASTER RESOLUTION, AND IT FALLS OUT (§13).**
It is NOT chosen. It is the ink's **own mean inter-sample arc step**:

```
cell = (total within-stroke arc length) / (total number of inter-sample steps)
grid_w = ceil(bbox_width / cell) + 2,   grid_h = ceil(bbox_height / cell) + 2
```

This is the resolution at which the pen was actually recorded. It is the frame/continuum
invariant's own identifiability guard applied verbatim — *"never encode precision the
steps cannot support"*. A gap narrower than one sample step is **below the datum's own
resolution** and is therefore closed; a gap wider than one is open. **No threshold, no
dilation radius, no tuned grid size.**

**One honest guard, declared:** grid dimensions are clamped to 4096 per side purely to
bound memory. The `clamped` field reports whether the clamp bound; **the run must report
the clamp rate, and a clamp rate > 0 on the confirmatory set invalidates the §13
derivation claim for those figures.** Expected: 0.

---

## 5. GATE 0 — CALIBRATE THE MEASURE BEFORE THE AGENT (§1). NO CONFIRMATORY SEED CONSUMED.

**§1 requires the measure be gated first. If GATE 0 fails, H1 is refuted AT THE
INSTRUMENT and no amount of downstream accuracy can rescue it.** All three gates run on
DETERMINISTIC sweeps (no seeded draws) except G0b's null.

**G0a — POSITIVE AND NEGATIVE CONTROL (synthetic, exact).** `EnclosedCount` must return
exactly:

| figure | required |
|---|---|
| closed unit circle (one stroke) | **1** |
| open 270° arc | **0** |
| figure-of-eight | **2** |
| two nested circles (two strokes) | **2** |
| straight line | **0** |
| three scattered points | **0** |

**PASS iff all 6 exact.** A single miss = the instrument is not measuring enclosure and
the rung stops (§1: a gate whose measure passes noise is not a gate; and the arm must be
alive in BOTH directions).

**G0b — WRITER-INVARIANCE ON REAL INK (the claim's own load-bearing assertion).** Over
the 10 confirmatory alphabets × 20 characters × all available drawers, compute the hole
count of every drawing. Statistic: **modal-agreement rate** = mean over the 200 classes
of (number of that class's drawings whose hole count equals the class's modal hole
count) / (number of that class's drawings). Null: the SAME statistic under a
**class-shuffled** reassignment of drawings to classes (seed 54001), which is the honest
chance level GIVEN the marginal hole-count distribution.

**PASS iff observed modal-agreement is CI-separated ABOVE the shuffled null.**

**G0c — INFORMATIVENESS (declared in advance, and it can refute at the premise).** Report
the distribution of per-class modal hole count over the 200 classes, its entropy, and
`f0` = the fraction of classes whose modal hole count is 0.

> **DECLARED BEFORE THE RUN: if `f0` > 0.90, the feature is near-constant on this
> corpus. A near-constant feature cannot carry 20-way discrimination REGARDLESS of how
> writer-invariant it is, and H1 is recorded as REFUTED AT THE PREMISE.** The
> confirmatory arm A3 is still run and reported (a near-constant hard gate should then be
> a near-no-op, and measuring that is the honest confirmation of the diagnosis) — but the
> verdict is written from G0c, not from A3's delta.

This clause exists because the two failure modes — *"the feature is unreliable across
writers"* (G0b) and *"the feature barely varies across classes"* (G0c) — are DIFFERENT
diagnoses with different consequences, and a single accuracy delta cannot tell them
apart. **Naming both before the run is what stops a null being reported as one vague
shrug.**

---

## 6. THE CONFIRMATORY RUN — arms, n, statistic, decision rule

**PROTOCOL (fixed, matching RUN 15/16 exactly — §8 eval-subset coverage is part of the
claim):** Omniglot `strokes_evaluation`, one-shot **20-way**, **WITHIN-alphabet**,
**CROSS-drawer**. Alphabets: the RUN 15/16 ten — `Angelic, Atemayar_Qelisayer, Atlantean,
Aurek-Besh, Avesta, Ge_ez, Glagolitic, Gurmukhi, Kannada, Keble`. **R=2** seeded repeats
× 20 episodes × 10 alphabets = **n = 400** episodes. Master seed **54000**.

LEARN is unchanged from RUN 16 (5 background alphabets, drawers 01–14, 1500 pen-down
stroke cap, saturation re-checked).

**n IS FIXED IN ADVANCE AT 400 AND IS NOT NEGOTIABLE (§3.3, and the arc's own POWER THE
GATE rule).** RUN 16 ran at n=200 under a 480s budget; RUN 15's own powered gate was
n=400. Per-episode step at n=400 is 0.25pp, so the standing rule *"deltas within ~3× the
per-episode step are not results"* sets a ~0.75pp noise band; every arm carries a Wilson
95% CI and no delta is claimed without CI separation.

### Arms (every winner a HELD `Argmin`/`Argmax` evaluate — never a Python min/max/sort)

| arm | what | role |
|---|---|---|
| **A0 ADOPTED** | `ar.abs_rerank_targeted(delta=0, use_appearance=True)` — the earned-quanta pipeline, BYTE-IDENTICAL to RUN 15/16's own arm | **CONTROL.** Must reproduce CI-overlapping with 22.0% [16.8, 28.2] / 26.8% [22.6, 31.3] |
| **A1 SC+TPS FULL DWELL** | `ar.sctps_rerank` over `range(20)` | **CONTROL.** Must reproduce CI-overlapping with 73.5% [67.0, 79.1] |
| **A2 TOPOLOGY ALONE** | held `Argmin` over `(abs(holes_q − holes_c), ci)` | **FLOOR ARM.** What the feature alone buys. Ties resolve to the lowest candidate index — declared, and the tie rate is reported |
| **A3 SC+TPS + TOPOLOGY GATE** | **H1 CONFIRMATORY.** A1's verdict restricted to candidates whose hole count EQUALS the query's; if that set is empty, fall back to all 20 (an honest non-crash, and the fallback rate is reported) | a HARD gate — **zero free parameters**, no penalty weight to choose |
| **A4 D4-UNTANGLED SC+TPS** | **H3 CONFIRMATORY.** held `Argmin` over candidates of `min over g ∈ D4 of SC+TPS(g·query, candidate)` | the wall crossing's OWN earned group, transplanted verbatim |

Plus, from the SAME per-episode records, with no extra compute:

- **H2 COMPLEMENTARITY:** A0's accuracy RESTRICTED to the episodes where A1 is wrong,
  with a Wilson CI, against the 5% chance floor; plus the ORACLE-UNION ceiling
  (either A0 or A1 correct) and the per-arm error overlap.
- Shuffled-label controls on every arm (breaks the query↔exemplar correspondence).
- Per-arm and per-compare wall-clock cost.

### DECISION RULES (fixed now; §5 forbids touching any of them after seeing a number)

- **H1 CROSSES** iff **A3's CI is separated ABOVE A1's**. **NULL** if the CIs overlap.
  **HARM** if separated below. If G0c refutes at the premise, the verdict is written from
  G0c and A3 is reported as the confirmation of that diagnosis.
- **H2 COMPLEMENTARY** iff A0's accuracy on A1's error episodes has a Wilson CI whose
  lower bound EXCEEDS 5% (chance). **NULL** otherwise.
- **H3 CROSSES** iff **A4's CI is separated ABOVE A1's**. **NULL** if overlapping. **HARM**
  if separated below.
- **THE RUNG'S OVERALL VERDICT is CROSSING only if at least one of H1/H3 crosses.**
  Otherwise it is a **DIAGNOSED NEGATIVE**, and the deliverable is the diagnosis: WHICH of
  (instrument unreliable / feature near-constant / group wrong / information genuinely
  absent) each null is, decided by G0a–G0c and the arm-level diagnostics, never by
  hand-waving.

**EXACTLY THE ARMS LISTED. NO SWEEPS. NO RE-RUNS. NO POST-HOC ARM.** A further attempt
needs a NEW pre-registration with a NEW mechanism-level hypothesis (§3.6).

---

## 7. MY PREDICTIONS, IN ADVANCE, WITH PROVISOS (§3.7)

**H1 — I predict NULL, most likely via G0c (refutation at the premise).** Reasons: (a)
Omniglot is dominated by simple few-stroke glyphs and I expect the great majority of
classes to have modal hole count 0; (b) hand-drawn counters frequently fail to CLOSE — a
hand-drawn apex leaves a gap — so even where a counter exists, the trajectory may not
enclose it. **Proviso that would break my prediction:** if G0b shows high cross-drawer
agreement AND G0c shows a non-degenerate hole distribution, the hard gate should give a
small positive, and my reasoning about pen-trajectory closure was wrong.

**H2 — I predict COMPLEMENTARY, but small.** The two reads use genuinely different
information (quantized construction vs continuous contour geometry), so A0 should beat
5% on A1's errors. But A0's absolute accuracy is only ~22%, so the headroom is small and
the oracle-union ceiling should sit only modestly above A1. **Proviso that would break
it:** if A0 is at chance on A1's errors, then the earned layer contributes NO independent
information at the verdict grain, and this project's "the answer is BOTH" position does
not hold at this seam — which would be the most interesting negative in the rung.

**H3 — I predict NULL or CI-separated HARM.** Reason: §3 above. The earned group is
discrete similarity; the actual nuisance is continuous deformation; and D4 is
identity-CHANGING for many scripts. **Proviso that would break it:** if A4 ≥ A1, then
Omniglot's within-class variation contains substantial D4-like nuisance that the raw
verdict was paying for, and my reading of the deformation negative was too pessimistic.

**Being right in advance is the only evidence I understand the model. If a proviso
breaks, that is what I did not understand, and it will be recorded as such.**

---

## 8. WHAT THIS RUNG DOES NOT CLAIM (§8, written before the numbers exist)

- Nothing about the arc's **80.5%** pipeline. The baseline here is RUN 16's 73.5%.
- Nothing about **images**. Topology is computed from PEN TRAJECTORIES; an image-derived
  contour (true border-ownership on a raster) is a DIFFERENT instrument and is out of
  scope. A null here does not refute topology-from-images.
- Nothing about **border-ownership itself** — no border-ownership rung exists in this
  tree; `EnclosedCount` is enclosure only, which is the CONSEQUENCE the grounding names,
  not the mechanism.
- Nothing about **untangling in general**. H3 tests exactly one group — the discrete D4
  the crossing earned. A null bounds THAT transplant, not the untangling idea.
- Nothing about **one-shot learning beyond Omniglot**, and nothing beyond the 10 named
  alphabets, 20-way within-alphabet cross-drawer, n=400.
- **Synthetic-proven mechanism ≠ benchmark value.** If G0a passes and the benchmark does
  not move, BOTH facts are reported, clearly separated (the arc's own standing rule).

---

## 9. §9, §10, §11, §12 COMPLIANCE

- **§9:** `EnclosedCount` is a NEW Term constructed by NO existing seed/rule/adapter. To
  be PROVEN, not assumed: `pytest tests/ -k migrated` at the pre-rung baseline and after;
  the sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` measured before AND after; `scripts/
  rung7_vision_bench.sh` at 200/0 with `data/` present.
- **§10/§10.1:** this rung **ADDS RUST**, so `scripts/engine_build.sh` MUST be run in this
  worktree and `tests/test_engine_provenance_migrated.py` must report `own`. Every result
  file carries `provenance_line()`. **A shared engine would be a DIVERGED source here and
  the gate must refuse it** — this is the first vision rung in a while to actually
  exercise §10.1 rule 4.
- **§10.2:** `data/` is symlinked (gitignored, cannot enter a commit). The reader is
  positive-controlled by G0a before any real-ink number is read.
- **§11:** own worktree, own branch, named-path staging only, no `git add -A`.
- **§12.3:** the provenance self-audit pins **BOTH** endpoints (`git diff BASE_SHA
  RUNG_SHA`, tracked files only). **Never against `HEAD`. Never against the working
  tree.** This defect has occurred three times in this arc.
- **§13:** the only derived constant is the raster resolution (§4), which falls out of
  the ink's own sampling. The D4 group is IMPORTED from the crossing, not chosen. The
  topology gate is HARD (equality), so it has no weight to tune.

## 10. SEED LEDGER ENTRY (claimed at pre-registration)

**54000–54999 — CLEAN at claim time**, verified against the ledger: consumed blocks run
0–28k, 30–37k, 39k, 41k, 43–53k; 16k/29k/38k/40k/42k and everything ≥ 54000 are free.
This rung takes **54000–54999** and will record ACTUAL consumption in the results:

- **54000** — the confirmatory powered run's master rng.
- **54001** — G0b's class-shuffled null.
- **54002** — the powered run's shuffled-label controls.
- 54003–54999 expected to remain CLEAN.
