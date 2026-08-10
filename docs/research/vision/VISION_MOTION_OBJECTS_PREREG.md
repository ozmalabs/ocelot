# COMMON MOTION AS THE OBJECT CRITERION — pre-registration

*Written and committed BEFORE any real-frame number (PROTOCOL §3).*
Seeds **84000–84999**. Engine **25fa11652e83**. Provenance gate run as its own
step before this file was written: **640 passed**. Oracle
`scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped** (no `data/` — the
documented no-corpus case; the 10 skips are `BSDS300 corpus absent`).

---

## 0 — WHY THIS RUNG EXISTS

The figadj-replacement rung produced 10–17 multi-cell proto-objects per frame,
persisting at 0.813 against an arbitrary partition at 0.069, and that was read
as success. **It is not sufficient.**

- **10–17 per frame is a FRAGMENT count, not an object count.**
- **Persistence proves STABILITY, not OBJECTHOOD. A stable patch of wall
  persists beautifully.**
- Enclosure and border ownership are **STATIC FORM** criteria. They fragment a
  scene into however many enclosed regions it happens to contain. Hence
  seventeen.

**The developmental primitive is COMMON MOTION, not static form.** Infants
segment by common fate before boundary or appearance (Spelke: cohesion,
continuity, contact). **A thing is what moves together.** A walking person is
ONE object regardless of how many enclosed colour regions they contain. Static
form yields many and small; common fate should yield **FEW and LARGE**.

**And the corpus inverts.** Evolution built no machinery for understanding
photographs. A still strips motion, depth and temporal continuity — precisely
the signals that define objecthood. **VIDEO is the corpus; STILLS are the NULL
ARM. A mechanism that groups by common motion SHOULD decline on a still, and
declining there is CORRECT BEHAVIOUR, not failure.**

---

## 1 — THE REPRESENTATION: MOTION IS A VECTOR MATRIX

**Motion is not a per-pixel comparison aggregated into a coherence statistic.**
It is a matrix of vectors, and every question this rung asks is a **direct read
of that matrix**, not a statistic rebuilt from pairwise cell comparisons.

- **Cohesion is a direct vector read** — dispersion of the vectors in a
  candidate group, against dispersion across groups. Not an aggregate over
  pairwise cell scalars.
- **The grouping tolerance FALLS OUT of the field's own dispersion** (§4).

### 1.1 The codec-native path is UNAVAILABLE HERE, and this is MEASURED

For compressed video the vector matrix is **transmitted, not computed** — H.264
hands over motion vectors plus a residual in hardware, and computing flow from
decoded pixels discards that representation to rebuild a worse copy.

**Measured, not assumed:** this corpus is **HEVC/H.265 at 1920×1080**. PyAV
17.0.1 exposes `sidedata.Type.MOTION_VECTORS` and accepts
`flags2=+export_mvs`, but **ffmpeg's HEVC decoder does not implement MV export**
— probed on C1 over 8 consecutive frames spanning I, P and B pictures
(`pict_type` 1/2/3): **`MOTION_VECTORS` side data absent on every one.**

**Therefore this rung computes the vector field, and states the bound: every
cost number below is for COMPUTED flow. A codec-native path would not pay it.**
This is a named-not-built residual, with a measured reason.

### 1.2 `seeds/vision_motion.json` does NOT hold the field — checked, not assumed

Its five "rules" have `match_type: null` and `match: null`. They are prose
propositions (`aperture_problem_requires_global_pooling`, …) with **no
mechanism behind them**. `seeds/vision_change.json` IS executable but its
frame-to-frame terms are **scalar per-cell magnitude only** (`ch_transient_on/off`
compare `lum_raw` to `lum_prev`); there is no displacement, no direction, no
`dx`/`dy`. The Rust `TemporalDiff` Term is elementwise `b−a` — magnitude, not a
vector. `feature_identity`'s `vel_row`/`vel_col` is the only 2-D velocity in any
executable rule, and it *assumes* correspondence rather than solving it.

**There is no existing vector field to reuse. This rung builds one.** Recorded
here so the claim cannot later be laundered as reuse.

---

## 2 — THE MECHANISM

New seed **`seeds/vision_motion_group.json`**, master-OFF by default (§9).
Every decision is a rule; the adapter supplies the vector matrix and a clock.

**Adapter (mechanical I/O only):** decode CONSECUTIVE frames (`every=1`) at
72×72 grey; for each cell of an 18×18 block lattice (block extent `B`), write
the integer displacement `(vy, vx)` as **cell attributes**. This is the
observation — the same status as `quantize()`'s value matrix, and the substitute
for the transmitted MVs of §1.1.

**Aperture, and what falls out of what.** The search radius is **`R = B`, and
this falls out of overlap**: beyond a displacement of its own extent a block
shares no pixels with its source, so the match is unconstrained rather than
merely coarse. **`B` itself is an inherited sensor aperture and is declared a
magic-number residual (§13), exactly as `k` is** — it is NOT claimed to fall
out. **The §13 claim this rung makes is scoped precisely to the GROUPING
CRITERION**, which is where the brief places it.

**Rules (all decisions):**

| rule | reads | writes |
|---|---|---|
| `mo_pair_diff` | own `(vy,vx)`, neighbours' | `pd` = max L1 vector difference to a 4-neighbour |
| `mo_tol_otsu` | the observed `pd` distribution | `mtol` — Otsu's split, **candidates are the observed `pd` values themselves** |
| `mo_flood` | `(vy,vx)`, `mlabel`, `mtol` | `mlabel = Argmin` over neighbours within `mtol` — common-fate connected components |
| `mo_ring` | group members' and non-members' vectors | the bounding ring's mean vector, a **direct vector read** |
| `mo_mint` | group vector vs ring vector | `MotionObject` iff they differ by more than `mtol` |
| `mo_cohere` | members' vectors | within-group vector dispersion |

**Ablation flags are graph DATA** (`MotionParams`), never a Python code path:
`marm` (master), `mo_contrast` (the ring test), `mtol_mode`.

---

## 3 — HYPOTHESIS, TWO-SIDED

**H1.** Grouping by common motion yields **FEWER and LARGER** proto-objects than
grouping by static form, on the same frames.

**Two-sided alternative, and it is the outcome to guard against: it yields the
same fragmentation (≈10–17, small).** Then **the criterion did not help**, and
that is this rung's primary honest outcome, to be stated plainly.

**Prediction, in advance, with its provisos.** I predict C1 (cartoon: large flat
regions, clean synthetic motion) yields **2–6 objects per frame** with mean size
several times the incumbent's, and that **C2 (live-action) does markedly worse**
because a moving camera makes the whole field move, and computed block-match
flow on 72×72 downsampled frames is noisy.

**The proviso I expect to break, stated now:** the dominant risk is that the
computed vector field is mostly noise, Otsu splits noise, and the result is
**many small groups — fragmentation by a different route**. If that happens the
finding is "motion is the right criterion, computed flow at this grain is the
wrong instrument", and it is NOT to be rescued by tuning `B`, `R` or the
tolerance (§5, §13).

---

## 4 — §13: THE TOLERANCE FALLS OUT

**The motion-agreement tolerance is not a number in any file.** It is **Otsu's
split of the field's OWN adjacent-pair vector-difference distribution**, with
the candidate splits being **the observed `pd` values themselves** — so the
threshold is the `pd` of a cell the graph picked.

**Precedent in this tree:** `ca_otsu` (`seeds/vision_cut_abstention.json`) does
exactly this and records its own honest limit, which is inherited here and
stated in advance: **Otsu has no null hypothesis — it returns a split on any
distribution, including one with no structure in it.** The stills and noise arms
exist to measure precisely that.

**A median split is REFUSED** — it is 50%-by-construction, the defect
`ch_drive_median` already carries in this tree.

**Registered secondary arm:** `mtol_mode = "exact"` sets the tolerance to exact
integer vector equality — **zero constants at all**, mirroring the value flood's
halt at exact equality. Reported alongside, not swept over.

**M6 verifies by AST WALK, never a substring selector:** no literal appears in
any comparison against `vy`, `vx`, `pd`, `mtol`, `members` or a dispersion
attribute, in any rule of the new seed.

---

## 5 — THE ARMS. THE COUNT IS REPORTED FIRST.

**n fixed in advance:** 40 consecutive frame pairs per corpus (matching the
incumbent's `N_CONSECUTIVE`), 7 sampled frames for per-frame counts.

### M1 — COUNT (the headline)
Objects per frame and their **size distribution**, C1 and C2, against:
- (a) the incumbent's published **10–17** multi-cell protos/frame at G72;
- (b) **the incumbent RE-RUN on this rung's own 18×18 whole-frame lattice** —
  the exactly-matched control. **Every floor is re-earned at this
  configuration; none is inherited.** (Floors have moved 3.6× and in opposite
  directions between configs in this arc, and an inherited floor produced a
  phantom 3× gain in the previous rung.)

### M2 — COHESION
Within-object vector dispersion vs between-object dispersion. A **direct vector
read**. PASS = within markedly below between, CI-separated.

### M3 — CONTINUITY
IoU persistence of motion-defined groups across consecutive frames, against a
**temporal-shuffle floor** and an **arbitrary size-matched partition floor**,
both re-earned here. PASS = paired CI lower bound clear of zero.

### M4 — A STABLE BACKGROUND PATCH IS NOT AN OBJECT
**This is the arm a persistence test alone will happily certify.** Static
background regions are included explicitly; measure the share of minted objects
whose support is static background (vector equal to its ring's).
**PASS = ≈0. Prediction: 0, by the ring contrast rule.**

### M5 — STILLS DECLINE (near-zero objects is the PASS condition)
- **BSDS300 is ABSENT from this tree** (`data/` does not exist). Declared, not
  worked around.
- **Frozen frame** (a frame paired with itself, `V ≡ 0`): PASS = 0 objects.
  **Declared WEAK in advance** — it is arithmetically forced, not empirically
  interesting.
- **Global pan** (one still frame translated by a constant vector): the
  stronger arm — the field is non-zero and uniform, nothing moves differently
  from its surround. **PASS = ≈0 objects.** This doubles as the moving-camera
  control.

### M0 — CONTROLS, WHICH MUST ACTUALLY FIRE
**This thread has produced a vacuous mint reading as success THREE times.**

- **D1 positive:** synthetic 18×18, a 6×4 rectangle translating by (0,+1)
  against static background → exactly **1** object, **24** members. Run aborts
  if not.
- **D2 dead-instrument, registered to FIRE:** whole field translating by one
  constant vector, **`mo_contrast` DISARMED** → **1 object with 324 "members" on
  a field containing no figure** (the known-good shape: *uniform field,
  unseeded, 1 proto with 144 members*). With `mo_contrast` **ARMED** → **0**.
  **The run aborts if D2 does not fire.** Separated from every live run by the
  disarmed flag.
- **NOISE:** iid random vector field → must mint no multi-cell object.

---

## 6 — DECISION RULE, INCLUDING WHAT A NULL MEANS

Three outcomes, **all publishable, and whichever occurs is what gets reported**:

1. **The developmental case** — few large motion-coherent objects that cohere
   (M2) and persist (M3), refusing background (M4), declining on stills (M5).
2. **The criterion did not help** — the same fragmentation as static form
   (≈10–17, small). **Stated plainly; this is the outcome to guard against.**
3. **Motion-driven but wrongly grouped** — objects on video with a correct
   decline on stills, but poor cohesion. Grouping is motion-driven; the
   grouping RULE is wrong.

**A null on M1 does not license tuning `B`, `R` or the tolerance.** A further
attempt requires a NEW pre-registration with a NEW mechanism-level hypothesis
(§3.6), never a parameter search (§5).

---

## 7 — SEEDS, AND THEY WILL BE MEASURED NOT ASSERTED

Declared **84000–84999**, allocated in advance:

| range | use |
|---|---|
| 84100 / 84101 | C1 / C2 corpus RNG |
| 84200 | iid noise vector-field control |
| 84300 | arbitrary-partition floor (M3) |
| 84400 | temporal-shuffle floor (M3) |
| 84900 | synthetic controls D1 / D2 |

`scripts/seed_audit.py` will be run **on this rung's own scripts**, and the
report will state resolved seeds AND unknown sinks. **A `--check` that passes
while leaving sinks UNKNOWN has verified nothing** — every seed must be
statically resolvable, so seeds are drawn from explicit literal tuples, never
from a dict subscript.

## 8 — WHAT IS NOT SHOWN (§8)

- No claim about codec-native motion vectors — **unavailable on this corpus,
  measured** (§1.1).
- No claim that the block-match flow is a good flow estimator. It is the
  sensor; its quality bounds every result and is not separately validated.
- `B` is a declared magic-number residual; `k` remains one, inherited.
- The motion lattice (18×18 whole-frame) is **coarser in cell count** than the
  incumbent's G72 (16 tiles × 324). M1(b) exists precisely so one comparison is
  exactly matched; the published-10–17 comparison is across grains and is
  labelled as such wherever it appears.
- BSDS300 absent, so the stills arm is frozen-frame + global-pan, not a
  photograph corpus.
