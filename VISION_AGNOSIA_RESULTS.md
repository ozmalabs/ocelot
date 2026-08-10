# VISION — APPERCEPTIVE / ASSOCIATIVE AGNOSIA (FRONTIER T9): the FORM↔RECOGNITION seam (RESULTS)

*Confirmatory run of `VISION_AGNOSIA_PREREG.md` (committed BEFORE the run at
**`30704d58`**, §3). Runner `scripts/agnosia_measure.py`; adapter
`domains/agnosia_world.py`; seed `seeds/vision_agnosia.json` (the two lesion flags);
gate `tests/test_agnosia_migrated.py`; raw `results/agnosia_measure.json`. Failure-mode
gate **#1** of `VISION_VENTRAL_GROUNDING.md` — "the sharpest architectural tell".*

## Engine / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()` reads
  *"shared build from … — Rust source identical"*). This rung adds **NO Rust**, so the
  shared build is legitimate (§10.1 rule 4).
- Worktree `.claude/worktrees/agent-a65a0ebcc1313b14b`; base `main` HEAD **`b1c736a0`**,
  `git merge-base --is-ancestor b1c736a0 HEAD` = **true** (§11). `data/` symlinked to
  canonical (§10.2).
- **NO new Rust. ONE new seed** (`vision_agnosia` — the `AgnosiaParams` node and
  nothing else) **and TWO guard-clause edits**: `shape_decode_loop` 1.7.0 → **1.8.0**,
  `vision_ground` 1.0.0 → **1.1.0**. Both flags default 0 (= INTACT), so §9
  byte-identity holds by construction and is verified below.

## STEP 1 AUDIT — can these be clean FLAGS, and are COPY and NAME independently readable? (§12.4, file:line)

**VERDICT: YES for both — and the audit's real finding is that the two stages already
live in TWO SEPARATE SEEDS WITH NO CROSS-READ, which is the structural precondition
the dissociation then tests behaviourally.**

- **RENDER (percept formation) — `seeds/vision_ground.json`.** `gr_label` (rule 1)
  labels a SENSED cell's contour axis by exact equality (no magic number); `gr_fill`
  (rule 2) CONTINUES a contour across a no-data span; `gr_interp` (rule 3) is the
  pre-existing blur control. Gated on `GroundParams.{ground,interp}`. Adapter
  `domains/ground_world.py` is decision-free by construction (`add_grounded_field:39`
  anatomy, `present:83` observe+tick, `belief_field:130` pure query). **The percept
  `gbel` is produced entirely by rules.**
- **RECOGNITION (identity) — `seeds/shape_decode_loop.json`.** `sd_recognize`
  (`:1465`), `sd_recognize_transformed` (`:1570`), `sd_recognize_dim` (`:1722`) are the
  **sole writers of `covered_by`** — the entire identity assignment. `sd_decode`,
  `TransformDecode`/`DimInfer`, and `sd_mint_quantum` are separate rules and are NOT
  touched by the lesion.
- **No cross-read.** No `vision_ground` rule mentions `Observation`/`ShapeSignature`/
  `covered_by`; no `sd_*` rule mentions `RetinaCell`/`gbel`/`GroundParams`. The
  percept→concept handoff is the adapter minting ONE `Observation` whose `signature`
  is the percept's cell set (`agnosia_world.name_percept`) — the same mechanical idiom
  `identity_untangling_measure.py:96` uses.
- **Both ablations are clean FLAGS** (achromatopsia template, §9 OFF by default):
  `AgnosiaParams.associative` guards ONLY the three `sd_recognize*` rules;
  `AgnosiaParams.apperceptive` guards ONLY `gr_fill`. Each is an
  **absence-tolerant** `Count(Filter(NodesOfType(AgnosiaParams), ap, ap.<flag> > 0.5)) < 1`
  — a graph with no `AgnosiaParams` node counts 0 and is INTACT. **Deliberately NOT the
  `PickUnique` idiom**, which returns `None` on an absent node and would silently kill
  recognition in every graph that does not load this seed (§12.3).
- **What each readout measures.** COPY = the rendered percept cell set
  (`|gbel − 1| ≤ 1e−6`, the exact-value read of `illusion_measure.py:156–197`, not a
  tuned threshold) vs the TRUE form. The 3 occluded on-form cells per object carry **no
  sensor data in any arm**, so a passing copy is a genuine RECONSTRUCTION, not a
  pass-through. NAME = `covered_by` when the loop reached a recognition state.

## Verdict — ALL 10 pre-registered arms PASS; a CLEAN DOUBLE DISSOCIATION

| arm | flags | copy | name | result |
|---|---|---|---|---|
| **A INTACT** (§1.1 control validity) | — | **6/6** | **6/6**, each its OWN object | **PASS** |
| **B ASSOCIATIVE** (headline) | `associative=1` | **6/6** (symdiff `[0,0,0,0,0,0]`) | **0/6** | **PASS** |
| **C APPERCEPTIVE** (headline) | `apperceptive=1` | **0/6** (symdiff `[3,3,3,3,3,3]`) | **0/6** | **PASS** |
| **C2 APPERCEPTIVE-B** (2nd render corruption) | `interp=1` | **0/6** (symdiff `[3]×6`) | **0/6** | **PASS** |
| **D DOUBLE DISSOCIATION** | — | copy survives B, fails C | naming fails BOTH | **PASS** |
| **E COPY-ALIVE** (§1.1) | `associative=1` | percepts **set-identical to A**, **3/3 occluded cells rendered** per object | — | **PASS** |
| **F LESION-ALIVE** (§1.1) | `apperceptive=1` | percept **non-empty 6/6** | identity layer still ran (`status=minted`) | **PASS** |
| **G FLOOR** (seeds 48000–48099) | all three arms | — | **0/100** false names in EVERY arm | **PASS** |
| **H FLAG LOAD-BEARING** (§13.2) | — | `associative` moves copy by **0** | `associative` moves name by **6**; `apperceptive` moves copy by **6** | **PASS** |
| **X OFF-DAY** (§9) | defaults | percepts identical to A | 6/6 | **PASS** |

## The headline — the seam is REAL: form and identity are SEPARABLE stages

**Two ablations, two different stages, and the COPY test discriminates them:**

- **ASSOCIATIVE (`associative=1`, the identity layer lesioned).** Every one of the six
  forms is still **FORMED EXACTLY** — `symdiff = 0` for all six, and the percept is
  **set-identical, object by object, to the intact arm's** — while **nothing is named**
  (`covered_by = None` 6/6, `n_named_anything = 0`). Recognition dies **downstream of an
  intact percept**. This is the clinical associative picture: the patient copies the
  drawing and cannot say what it is.
- **APPERCEPTIVE (`apperceptive=1`, percept completion lesioned).** The form **cannot be
  built** — `symdiff = 3` for all six, exactly the three occluded on-form cells — and
  naming fails **with** it (`0/6`). The failure is **upstream**: there is no percept to
  recognise.
- **The dissociation is the pair.** Copy: **6/6 under the identity lesion, 0/6 under the
  render lesion.** Name: **0/6 under both.** One blob could not do this — an
  identity lesion that also degraded the percept would break `copy_B == copy_A`, and a
  render lesion that left naming intact would break the downstream claim. Neither
  happens.

**The surviving copy is genuinely ALIVE, not a trivial pass (§1.1).** The three occluded
cells per object carry **no sensor data at all** (`raw_sensor` has no observation there);
in the associative arm the render puts **3 of 3 into the percept, for every object**. So
the copy that survives the identity lesion is a real reconstruction ACROSS A HOLE, not a
pass-through of the stimulus. And it is byte-identical to the intact arm's — the identity
guard does not leak into `gbel`.

**Neither lesion is a dead instrument (§1.1).** Under the apperceptive lesion the percept
is **non-empty** (6/6) and the identity layer **still runs on it**, terminating at
`minted` — the sd loop processed the broken form and minted novelty rather than
falling silent. Under the associative lesion the percept is non-empty and the decode
machinery runs to completion (see the characterisation below).

**Noise is not a confound.** 100 random binary stimuli (seeds 48000–48099) produce
**0 false names in every arm** — intact, associative, and apperceptive alike — with
**0 empty percepts**, so the floor is a refusal, not a silence.

## What I predicted, and what I got (§3.7 / §7)

I predicted **all arms PASS**; they did, and **every one of the six provisos held**:

1. **Arm B's copy BYTE-IDENTICAL to arm A's — HELD** (set-identical per object, not
   merely also-correct). The two seeds share no attribute; the guard cannot leak.
2. **Arm A reads `recognized_transformed`, not `recognized` — HELD** (flagged in
   advance precisely so it could not be read as a post-hoc reinterpretation). Both are
   `covered_by`-bearing recognition states.
3. **Arms C and C2 fail copy by exactly the 3 occluded on-form cells — HELD**
   (`symdiff = 3` uniformly, both arms). The flag did not leak beyond `gr_fill`.
4. **Arm C fails naming by falling through to `minted` — HELD.** The identity layer is
   intact in C and processes the corrupted percept; it is a FORM failure, not a second
   identity lesion.
5. **Floor 0/100 in every arm — HELD.**
6. **`apperceptive=1` is NOT the same as `ground=0` in the graph — HELD, and measured
   for it:** under `apperceptive=1` `gr_label` is still live (**58** contour-labelled
   cells, vs **61** intact — the 3 missing are exactly the never-filled occluded cells),
   whereas `ground=0` gives **0**. The percepts coincide (21 cells) but the graphs do
   not: the lesion is on **running machinery**, and the "live machinery" claim is
   measured rather than asserted.

## The one instrument I got wrong, and how it was handled (§5 / §7)

The first execution reported **`F_lesions_alive = False`**, and it was **my instrument,
not the model**. Arm F **as pre-registered** concerns arm C only (non-empty percept +
the recognition layer still running) and **passed on that first execution**. What failed
was an **extra conjunct I added to the runner after the pre-registration was committed**
— `associative_decode_ran_residual_empty`, reading `Observation.residual`.

**`residual` is a DEAD INSTRUMENT here (§1.1's disease, in a new costume):** it is the
value the adapter seeds at mint time and the sd loop **never rewrites it**. It reads
**identically — `[24,24,14,37,37,41]` — in the INTACT and ASSOCIATIVE arms**, so it
could not have distinguished anything, and it would have "failed" the intact arm too.

**What I did:** restored arm F to **exactly its pre-registered definition** (which
passes, and passed on the first run), and reported the concept-layer liveness question
as **F2 — an explicitly NON-PRE-REGISTERED characterisation that no decision rule
depends on**, with the dead `residual` values printed in the results JSON alongside it
(`F2.residual_lens_dead_instrument`). This is **not** metric surgery under §5: no failed
pre-registered gate was rescued by changing a measure — the pre-registered gate passed,
and a non-gating readout was diagnosed and replaced.

**F2 (characterisation, not a gate) — and it is the sharpest mechanism-level statement
of the seam.** Read off the sd loop's own bookkeeping:

| arm | `transform_checked` | `dim_checked` | `dim_explained` |
|---|---|---|---|
| INTACT | 6/6 | 6/6 | **6/6** |
| ASSOCIATIVE | 6/6 | 6/6 | **6/6** |
| APPERCEPTIVE | 6/6 | 6/6 | **0/6** |

Under the associative lesion the concept layer **runs AND still explains the percept —
exactly as in the intact arm** — and only the identity ASSIGNMENT is suppressed. Under
the apperceptive lesion the same machinery runs and **cannot explain** the broken form.
The two failures are at different depths of the same intact ladder.

**No metric was changed to rescue a failed gate (§5); no arm was re-run to flip a
verdict (§3.6).** The second execution differs from the first only in that arm F is
computed as pre-registered; every other number is unchanged.

## §9 / bench / siblings

- **Named vision bench** (`scripts/rung7_vision_bench.sh`, `data/` symlinked per
  §10.2): **200 passed / 0 failed** (130.8s) — the committed baseline, **UNMOVED**. The
  no-Python-thresholds scan is clean ("every knob is graph data").
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED** — `test_sdloop_vision_migrated.py`
  `test_orbit_law_arithmetic_matches_the_measured_mint_counts` passes after the
  `shape_decode_loop` 1.8.0 edit.
- **Siblings green in one process (73 passed):** sdloop-vision · identity-untangling ·
  dimension-inference · face-inversion · category · illusion-render · vision-ground ·
  engine-provenance.
- **New gate `tests/test_agnosia_migrated.py` 12/12**, including a source-grep gate that
  the ablations are FLAGS and never Python branches (it tokenises, so it scans CODE, not
  prose about the code) — **verified to FAIL on a real `if associative:` branch**, since
  a gate that has never failed is not a gate.
- **The diff is exactly the guards:** `shape_decode_loop.json` +101/−2 (three 33-line
  guard clauses + version + description), `vision_ground.json` +35/−2, plus the new
  seed/adapter/runner/gate. Nothing else moved.

## Scope — what is NOT shown (§8), and the named frontier

- A **VALIDATION gate for the form↔recognition seam**, nothing more. It does NOT show
  object recognition at natural-image scale, that the render is the ONLY percept stage,
  or that the sd loop is the ONLY identity stage.
- **It licenses nothing about which cortical locus realises either agnosia.** The
  clinical double dissociation is the behavioural target, not a circuit claim.
- **Bounded to the discrete/integer, in-frame, binary luminance-contour class** the
  render is already bounded to (`VISION_ILLUSION_RESULTS.md` §8) and to the **held
  invertible discrete-similarity nuisance class** the identity layer is already bounded
  to (`VISION_IDENTITY_UNTANGLING_RESULTS.md` REGIME A). Six stroke-composed forms on a
  20×20 retina with a 5-cell occluder is a small, deterministic stimulus set; n=6 per
  arm is exact, not powered — the arms are all-or-none geometry, and the only sampled
  arm is the 100-seed floor.
- The apperceptive lesion destroys **completion**; it does not model every way a percept
  can be degraded (the pre-registered second corruption, `interp` blur, agrees with it,
  which is evidence but not exhaustiveness).
- **NAMED FRONTIER:** the generator-track extensions — **lighting, deformation, style**.

## Is the form↔recognition seam real in this build? — the plain answer

**Yes.** One flag (`associative`, OFF by default) suppresses ONLY the identity
assignment and naming vanishes (6/6 → 0/6) while the percept is **formed exactly and
identically to intact** — including three cells per object that carry no sensor data
and exist only because the render reconstructed them. A second flag (`apperceptive`,
OFF by default) suppresses ONLY percept completion and the copy fails by exactly those
three cells, taking naming down with it. Copy survives one lesion and fails the other;
naming fails under both; noise names nothing in any arm; each flag moves its own target
and only its own target. The render and the recognition layer are **separable stages,
not one blob** — with ZERO new Rust, ZERO metric surgery, and the one instrument I got
wrong diagnosed in place rather than quietly retired.
