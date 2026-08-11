# SURFACE ASSIGNMENT — RESULTS: it walks into the mirror, and the mechanism that makes it walk is named

*Pre-registration: `VISION_SURFACE_ASSIGNMENT_PREREG.md`, committed **`c3eb4b9a`** BEFORE
any confirmatory number. Nothing in it was edited after the first number.*

**ENGINE PROVENANCE (PROTOCOL §10)** — printed from **inside** the measuring process and
written into `results/surface_assignment.json`:

```
engine 68860d0b0f78 @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [own build, scripts/engine_build.sh; 1 other tree build shadowed]
```

Branch `worktree-agent-a79dbc7b6eb9ca724`, base `e8bf3987`, prereg `c3eb4b9a`.
**Seeds 87000–87999**; measured draws below (§7). Artifacts:
`results/surface_assignment.json`, `results/surface_assignment.log`.

---

## 1. THE HEADLINE

**Put a screen or a mirror in real video and the system WALKS INTO IT.**

Across **4000 frame-runs** — 2 corpora × 2 surface sizes × 5 content arms × 2 mint
predicates × 100 real frames — the surface was minted as one object **zero times**:

| | count |
|---|---|
| SURFACE verdicts (`R ⊆ S` for some proto) | **0 / 4000** |
| exact `S == R` | **0 / 4000** |
| runs reaching a settled fixpoint | **4000 / 4000** |

Under the ladder's current predicate (`replacement` / `bo_mint_owned`), a 14-cell screen
in live-action video mints **7.40** free-standing objects inside its own boundary against
a no-surface base rate of **4.55** on the same rectangle in the same frame —
**Δ = +2.85 [+2.06, +3.64]**. In the cartoon corpus, **7.34 vs 1.49, Δ = +5.85
[+5.21, +6.49]**. The displayed content becomes objects **in the scene**.

**This is the WRONG outcome of the brief, and it is the outcome I predicted.** The gap
identified in `VISION_CALIBRATION_SCIENCE.md` §6h is **real and unfilled**.

---

## 2. THE THREE-WAY OUTCOME, WITH COUNTS

n = 100 frames per cell. `REF` = REFUSE, `SURF` = SURFACE, `CONT` = CONTENT-IN-SCENE
(WRONG), `SPIL` = spill-only residual. `inside` = mean protos with `S ⊆ R, S ≠ R`.

### 2a. `replacement` (`bo_mint_owned`) — the ladder's current predicate, PRIMARY

| corpus | side | content | REF | **SURF** | **CONT** | SPIL | inside |
|---|---|---|---|---|---|---|---|
| C1 cartoon | 8 | plain *(control)* | 81 | **0** | 19 | 0 | 0.34 |
| C1 | 8 | flat | 100 | **0** | 0 | 0 | 0.00 |
| C1 | 8 | **screen** | 23 | **0** | **77** | 0 | 1.44 |
| C1 | 8 | **mirror** | 2 | **0** | **97** | 1 | 1.23 |
| C1 | 8 | scramble | 63 | **0** | 37 | 0 | 0.45 |
| C1 | 14 | plain *(control)* | 25 | **0** | 75 | 0 | 1.49 |
| C1 | 14 | flat | 100 | **0** | 0 | 0 | 0.00 |
| C1 | 14 | **screen** | 0 | **0** | **100** | 0 | **7.34** |
| C1 | 14 | **mirror** | 0 | **0** | **100** | 0 | **6.76** |
| C1 | 14 | scramble | 26 | **0** | 74 | 0 | 1.32 |
| C2 live | 8 | plain *(control)* | 28 | **0** | 72 | 0 | 1.45 |
| C2 | 8 | flat | 100 | **0** | 0 | 0 | 0.00 |
| C2 | 8 | **screen** | 31 | **0** | 69 | 0 | 1.67 |
| C2 | 8 | **mirror** | 16 | **0** | 80 | 4 | 1.74 |
| C2 | 8 | scramble | 74 | **0** | 26 | 0 | 0.33 |
| C2 | 14 | plain *(control)* | 1 | **0** | 99 | 0 | 4.55 |
| C2 | 14 | flat | 100 | **0** | 0 | 0 | 0.00 |
| C2 | 14 | **screen** | 0 | **0** | **100** | 0 | **7.40** |
| C2 | 14 | **mirror** | 0 | **0** | **100** | 0 | **5.28** |
| C2 | 14 | scramble | 47 | **0** | 52 | 1 | 0.91 |

### 2b. `incumbent` (`bo_mint_enclosed`) — the committed baseline

REFUSE dominates everywhere, as predicted: 91–100 of 100 on `screen` in both corpora at
both sizes, 100/100 on `flat` and `scramble` in most cells. **SURF = 0 in every cell.**
The two exceptions are `mirror` at C1 s=8 (REF 39) and C2 s=14 (REF 64), and the C1 s=14
`plain` control itself (REF 35) — i.e. the base rate, not the surface.

---

## 3. THE TRAP, DEFEATED BY THE PAIRED CONTROL

The brief's trap: *"a mirror region will produce objects whether or not the surface was
identified — so 'objects appeared in the mirror' is not evidence of anything by itself."*

**It is a real trap, and the data show exactly why.** The `plain` control — the SAME
rectangle in the SAME frame with no surface in it — already yields **4.55** inside-protos
on C2 at side 14, and 99/100 CONTENT verdicts. **Reading the raw count would have
"confirmed" that the system places mirror content in the scene using a stimulus with no
mirror in it.**

Every claim below is therefore the within-frame paired difference
`Δ = n_inside(content) − n_inside(plain)`, 95% CI, n = 100 frames:

| corpus | side | arm | screen | mirror | scramble | flat |
|---|---|---|---|---|---|---|
| C1 | 8 | replacement | **+1.100 [+0.83, +1.37]** | **+0.890 [+0.71, +1.08]** | +0.110 [−0.10, +0.32] | −0.340 [−0.50, −0.18] |
| C1 | 14 | replacement | **+5.850 [+5.21, +6.49]** | **+5.270 [+4.78, +5.76]** | −0.170 [−0.56, +0.22] | −1.490 [−1.84, −1.14] |
| C2 | 8 | replacement | +0.220 [−0.21, +0.65] | +0.290 [−0.12, +0.70] | −1.120 [−1.42, −0.83] | −1.450 [−1.72, −1.18] |
| C2 | 14 | replacement | **+2.850 [+2.06, +3.64]** | **+0.730 [+0.02, +1.44]** | −3.640 [−4.18, −3.10] | −4.550 [−5.08, −4.02] |
| C1 | 14 | incumbent | −0.710 [−0.90, −0.52] | −0.740 [−0.90, −0.58] | −0.790 [−0.97, −0.62] | −0.800 [−0.97, −0.63] |
| C2 | 14 | incumbent | −0.180 [−0.27, −0.09] | +0.260 [+0.09, +0.43] | −0.180 [−0.27, −0.09] | −0.180 [−0.27, −0.09] |

**Surviving the paired control (CI excludes 0, positive):** `screen` and `mirror` under
`replacement` at C1 s=8, C1 s=14 and C2 s=14. **NOT surviving: C2 at s=8**, where both
`screen` (+0.22 [−0.21, +0.65]) and `mirror` (+0.29 [−0.12, +0.70]) are indistinguishable
from the base rate. **The effect is size-dependent and corpus-dependent, and the small
surface on live-action is a null.** Reported, not buried.

---

## 4. THE MECHANISM — measured, not inferred

**Why the surface is never one object.** Diagnosed on the settled graph by reading `bg`
and `glabel` directly (5 frames, C1, side 14, `replacement`):

| content | fraction of `R` absorbed into **background** | distinct enclosed components inside `R` |
|---|---|---|
| `flat` | **0.60** | 1, 1, 0, 0, 0 |
| `screen` | 0.05 | **90, 92, 87, 82, 84** |

**There are two regimes and neither one is a surface:**

1. **A FEATURELESS surface is SWALLOWED BY THE GROUND.** `bo_bgflood` spreads
   surroundedness from the tile frame through **equal-valued** neighbours, so a uniform
   inset connects to the background and becomes ground. 60% of `R`'s cells are marked
   `bg`; in 3 of 5 frames `R` holds **zero** enclosed components. This is why `flat`
   refuses 100/100 in **every** cell of the design — the one case where "the surface is
   one object" is trivially true is the case where the surface stops existing.

2. **A FEATURED surface SHATTERS INTO ITS CONTENT.** A screen's interior fragments into
   **82–92 distinct enclosed components**, of which `G_own_lost` mints ~7 as
   free-standing protos. The mint predicate is
   `perim(R) < perim(Q)` against **every** abutting `Q` — **it awards figure status to
   the SMALLER perimeter**. A side-14 surface has a contour of 52 cells; the fragments
   inside it have contours of a few. **The surface loses to its own content, by
   construction.** The containment relation is not merely unrepresented — **the predicate
   actively inverts it.**

**This is the answer to "why", and it is a property of the predicate, not of the
stimulus:** the ownership competition is a size prior pointing the wrong way for a
surface, which is by definition the LARGER region enclosing the smaller ones.

---

## 5. WHAT I GOT WRONG — my own prediction 5 is FALSIFIED

The pre-registration predicted (§5.5): **`scramble ≈ screen`** on the proto statistics,
reasoning that the mechanism reads a quantized intensity field and has no access to the
content's structure. **Wrong, and not marginally:**

| | screen Δ | scramble Δ |
|---|---|---|
| C1 s=14 replacement | **+5.85 [+5.21, +6.49]** | −0.17 [−0.56, +0.22] |
| C2 s=14 replacement | **+2.85 [+2.06, +3.64]** | −3.64 [−4.18, −3.10] |

`scramble` holds the **identical marginal histogram** and destroys only spatial structure,
and it moves the statistic **in the opposite direction**. So the mechanism is strongly
sensitive to the content's spatial structure: a pixel-scrambled inset produces no coherent
components to mint (it is high-frequency noise, and the equal-value flood finds no
extended regions), whereas real displayed video produces ~85 of them.

**The correction this forces on the account:** "the layer reads an intensity field" is
true but useless; what it mints is a function of the field's **spatial autocorrelation**,
and my prediction ignored that. The dead-instrument control earned its place — it was
included to show the mechanism was NOT reading structure, and it demonstrated the
opposite.

**What was predicted correctly:** CONTENT-IN-SCENE dominance under `replacement` (§5.1);
Δ > 0 for `screen` (§5.2); REFUSE dominance under `incumbent` (§5.4); and the perimeter
mechanism that produces them (§5, and confirmed directly in §4). Prediction §5.3 (`flat`
raises `n_surface`) is also **wrong**, for a reason I did not anticipate: `flat` does not
lose a competition, it **stops being figure at all**.

---

## 6. THE ASSIGNMENT CUE — present, measured, and honest about what it cannot do

**The cue (pre-registered §6):** the temporal **decoupling** of interior change from
exterior change across a persistent boundary —
`r(Δ_in, Δ_out)` over consecutive frames, computed on **frame data only**, never touching
the proto layer.

| content | C1 s8 | C1 s14 | C2 s8 | C2 s14 |
|---|---|---|---|---|
| `plain` *(control)* | +0.914 | +0.869 | +0.927 | +0.944 |
| `flat` | +0.903 | +0.877 | +0.734 | +0.668 |
| **`screen`** | **+0.107** | **+0.126** | **+0.445** | **+0.449** |
| **`mirror`** | **+0.869** | **+0.851** | **+0.879** | **+0.878** |
| `scramble` | +0.192 | +0.133 | −0.189 | −0.204 |

**The cue works for screens and fails for mirrors, exactly as predicted.** A screen drops
the correlation from ~0.9 to 0.11–0.45; a mirror leaves it at 0.85–0.88, statistically
indistinguishable from no surface at all.

**Why content cannot corrupt it.** It is a **coupling** statistic between two aggregate
change magnitudes, not a statistic of what the surface shows. The displayed content sets
the *values* of `Δ_in`; it does not set their *correlation with the surround*. A screen
may display anything at all.

**And the one thing that defeats it is a screen displaying the surrounding scene — which
is precisely the `mirror` arm, and it is measured to fail.** Naming the case that defeats
a cue is what makes it a cue rather than a hope. **This cue separates screens from scene;
it does NOT separate mirrors from scene, and nothing here should be read as claiming it
does.** A mirror's interior *is* the scene, so no interior/exterior statistic can
separate it; that separation requires geometry (the reflected layout is a reflection of
the actual one), which is not measured here.

**Status: the information is PRESENT in the stimulus. No mechanism reads it.** This rung
built no assignment mechanism — §7 below says why there is nowhere to put one.

---

## 7. SCOPE — WHAT IS NOT SHOWN (PROTOCOL §8)

**7.1 RIGHT was declared unreachable BEFORE the run, and remains so (PREREG §0.3,
PROTOCOL §13.1).** There is no `Surface`, `Mirror`, `Screen` or `Reflection` node type in
`seeds/`; no calibration or internal-frame attribute on any visual node; no containment
edge between `ProtoObject`s; and `ProtoObject` carries exactly four attributes (`root`,
`members`, `minted`, `gestalt`). **`SURF = 0/4000` is therefore NOT evidence that the
system failed to identify a surface — the representation in which "surface carrying its
own internal calibration" could be written does not exist.** What §1–§4 do establish is
strictly weaker and strictly real: the surface region is not minted as **one object**, and
its content **is** minted as objects in the scene, against its own base rate.

**7.2 The gap is confirmed unfilled, not narrowed.** Nothing here infers from an image
which calibration a surface carries. `VISION_CALIBRATION_SCIENCE.md` SUMMARY item 6 stands
untouched.

**7.3 The stimuli are COMPOSITES, not photographed mirrors and screens.** Declared in
PREREG §1.3. No perspective foreshortening, specularity, bezel, or partial transparency; a
hard pixel boundary. **A real mirror is strictly harder in every one of those respects**,
so this is a failure on the easy case. A success would not have transferred without a
photographed-surface replication; the failure does not need one.

**7.4 Local patch, not global surface — and the literature agrees (PREREG §1, science
doc §1b).** G72 mints per 18×18 tile, so the surface was placed **strictly inside a single
tile** — the most favourable geometry that exists here. Nothing is claimed about surfaces
spanning tiles; those cannot be minted as one object under any predicate, for reasons of
tiling rather than of mechanism. Hertzmann (2024) explicitly denies global consistency and
this design does not assume it.

**7.5 The human compensation phenomenon is CONTESTED (Erkelens 2013 finds none) and was
never assumed.** This rung tested what *this* system does. No claim is made about humans.

**7.6 The cue does not separate mirrors** (§6), and no geometric cue was built or tested.

**7.7 Corpus- and size-dependence is real.** C2 at side 8 is a null on both `screen` and
`mirror` (§3). The headline effect is carried by side 14 and by C1.

**7.8 One predicate pair, one configuration.** `bo_mint_enclosed` / `bo_mint_owned` at
G72, k=16. Nothing is claimed about other quantizers, resolutions, or a predicate that
does not use perimeter.

---

## 8. INSTRUMENT DISCIPLINE — the controls that had to fire, and did

**8.1 The discriminator's positive control FIRED (PROTOCOL §1 clause 4).** A synthetic
uniform 18×18 tile with one square: the discriminator read **`S == R` exactly**, 1 proto,
at side 8 (64/64) and side 14 (196/196), under **both** predicate arms. **The SURFACE
verdict is reachable by the instrument** — so `SURF = 0` on real stimuli is a measurement,
not a §1.1 dead-arm floor. The run aborts if this control does not fire.

**8.2 The discriminator is not the minting quantity (PREREG §3.1).** `R` is external
ground truth held by the stimulus builder, never written into the graph. The minting reads
`val`, `bg`, `glabel`, `rim` — none of which is `R` or derived from `R`. The relation is
subset / superset / disjointness only: **no thresholds, no tuned fractions, no constant at
all** (PROTOCOL §13, the strongest form).

**8.3 The paired base-rate control (§3)** is what converts "objects appeared in the
mirror" from a non-observation into a measured difference, and it removed one cell of the
design (C2 s=8) from the claim.

**8.4 Settling.** 4000 / 4000 runs reached a settled fixpoint (`can_flood` and `can_label`
both false). No run was read off an unsettled graph.

**8.5 Seeds — MEASURED, not asserted.** `python3 scripts/seed_audit.py --check 87000 87999
scripts/surface_assignment_measure.py` → `{"ok": true, "outside": []}` with
**`unknown_sinks: 0`** and all 20 draws statically resolved:
`87000–87004, 87010–87014, 87100–87104, 87110–87114`.
The first version of the script had **1 unknown sink** (a `CONTENT_ARMS.index(content)`
the analyser could not resolve) and was rewritten to an explicit ordinal tuple sequence
before the run — *a check that passes with UNKNOWN sinks has verified nothing.*

**8.6 Pins.** C1 `08630d4b` (cartoon), C2 `119eca43` (live-action), verified in-run; a pin
mismatch voids the run. Fresh material: `start_s=900` (the committed G72 rungs used 300).

**8.7 §9 DEFAULTS PRESERVED — the oracle re-earned across the engine change.**
`scripts/rung7_vision_bench.sh` (the named selector, not `-k`) at engine `68860d0b0f78`
with `data/` symlinked: **222 passed / 0 failed / 0 skipped in 153s** — the stated oracle
for the with-`data/` condition, quoted with its condition per PROTOCOL §10.2. This rung
adds no Rust, no seed, no rule and no default; the only flag it sets (`bown_own`) is the
seed's own committed ablation flag, set as graph data.

---

## 9. THE PROVENANCE INCIDENT — and a gate that did not catch it

**Recorded in PREREG §0.4 before the run; here is the confirmed form.**

A concurrent rung rebuilt the **canonical** tree's engine from changed Rust source while
this worktree — like every worktree — had no engine of its own and resolved through the
shared build. The first pilot ran on `ed399ddae26d` and printed
`** WRONG ENGINE — built from DIFFERENT Rust source than this tree **`.
**Those pilot numbers are void and are used nowhere.**

**The defect worth propagating:** in the same minute,
`pytest tests/test_engine_provenance_migrated.py` reported **7 passed**, while a plain
script in the same tree resolved the wrong artifact. The gate certifies the tree's
configuration under its own preamble; **it does not certify that the process you are about
to measure in loaded the engine you think it did.** A bare `python -c` with
`sys.path.insert(0, '.')` picks up the canonical `.pth` first and the gate is silent about
it.

**The rule this rung adopted, offered upward for §10:** *print `provenance_line()` from
inside the measuring process, into the results artifact, on every run.* A green gate in a
different process is not provenance. `scripts/surface_assignment_measure.py` does this and
**aborts** on `WRONG ENGINE` / `DIVERGED`; the line is in
`results/surface_assignment.json` under `engine_provenance`.

Resolved by `scripts/engine_build.sh` — this tree now owns engine **`68860d0b0f78`**.
This rung adds **no Rust**; the build exists only to stop measuring someone else's.

---

## 10. WHAT THIS LEAVES FOR THE NEXT RUNG

Stated as findings, not as a plan; sequencing is the supervisor's.

1. **The perimeter predicate is a size prior pointing the wrong way for surfaces.** A
   surface is the LARGER region enclosing smaller ones; `perim(R) < perim(Q)` guarantees
   it loses. Any surface-capable mint must be able to hold a region as figure **while its
   interior is also figure** — which is the containment edge the tree does not have.
2. **A featureless region is absorbed into the ground** by the equal-value flood. "Surface
   with no content" and "not a surface at all" are currently the same state.
3. **The screen cue is present and measurable** (r drops 0.9 → 0.11–0.45) and nothing
   reads it. It is cheap: two means and a correlation over consecutive frames.
4. **Mirrors need geometry, not statistics.** No interior/exterior change statistic can
   separate a mirror, because a mirror's interior *is* the scene. Measured, §6.
5. **Nothing above requires the global surface** the science doc flags as the most likely
   over-reach (§1b). All of it is local-patch.
