# SURFACE ASSIGNMENT — put a mirror or a screen in real video and ask what the system does

*Binding: `VISION_PROTOCOL.md`. Adjudication context: `VISION_CALIBRATION_SCIENCE.md`
(committed `2f107486`, amended `e8bf3987`). This is a NEW pre-registration with a NEW
mechanism-level hypothesis. It adds no Rust, no seed rule and no default. Written and
committed BEFORE any confirmatory number.*

**SEED BLOCK: 87000–87999.** Draws are reported measured, via
`scripts/seed_audit.py --check 87000 87999`, not asserted.

**ENGINE PROVENANCE (PROTOCOL §10).** Every number in this document:
`engine 68860d0b0f78 @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`,
an **own** build produced by `scripts/engine_build.sh` in this worktree.
Branch `worktree-agent-a79dbc7b6eb9ca724`, base commit `e8bf3987`.

> **A PROVENANCE INCIDENT HAPPENED DURING SETUP AND IS PART OF THE RECORD (§0.4).**
> The first pilot ran on engine `ed399ddae26d` — the CANONICAL tree's engine, rebuilt
> from **different Rust source** by a concurrent rung while this worktree had none of its
> own. Those pilot numbers are **VOID and discarded**. Worse, and this is the reusable
> part: `pytest tests/test_engine_provenance_migrated.py` reported **7 passed** in the
> same minute that `provenance_line()` in a plain script reported
> **`** WRONG ENGINE — built from DIFFERENT Rust source than this tree **`**. See §0.4.

---

## 0. WHAT IS BEING CLAIMED, AND HOW SMALL IT IS

### 0.1 The gap

`VISION_CALIBRATION_SCIENCE.md` §6h and its SUMMARY item 6 establish the claim's true
size. Per-surface calibration is **not novel**: it is `local slant compensation`
(Vishwanath, Girshick & Banks 2005) in perception, and in graphics it is a shipped,
enumerated, costed taxonomy (portal cameras with oblique clip planes, render-to-texture,
Fresnel-blended reflection+refraction on one pixel, since ~2005).

> **What nobody does is THE ASSIGNMENT PROBLEM: inferring FROM AN IMAGE which
> calibration a surface carries.** Graphics is *told* by an artist. Perception science
> studies compensation *given an already-identified surface*.

This rung does not solve the assignment problem. It asks the prior question: **put a
mirror or a screen in real video and measure what this system actually does with it.**

### 0.2 The three outcomes, from the brief, verbatim in substance

- **WRONG** — mints the reflected/displayed content as objects **in the scene**. They are
  not there. This is walking into the mirror.
- **RIGHT** — mints the surface as **one object carrying its own internal calibration**.
- **ACCEPTABLE** — **refuses**; declines to place content it cannot assign.

### 0.3 RIGHT IS UNREACHABLE BY CONSTRUCTION — DECLARED BEFORE THE RUN (PROTOCOL §13.1)

**§13.1 forbids reporting a signature the architecture forces, and it applies here in the
negative direction, so it is stated in advance rather than discovered afterwards.**

An audit of every file in `seeds/` finds:

- **no `Surface`, `Mirror`, `Screen` or `Reflection` node type anywhere**;
- **no calibration, projection or internal-frame attribute on any visual node**;
- **no `contains` / `part_of` / `internal` edge between `ProtoObject`s** — the
  `has_part`/`contains` edges in the tree are all in non-visual seeds
  (`figure_grounding.json`, `figurative_language.json`, `composer_grouping_graph.json`,
  `browser_affordance_reach.json`);
- the `ProtoObject` node carries **exactly four attributes** — `root`, `members`,
  `minted`, `gestalt` (`seeds/vision_border_ownership.json` v1.1.0). No extent, no
  bbox, no motion, no coherence, and nothing nestable.

The nearest thing in the whole tree to "a region carrying its own internal frame" is
`seeds/nested_frame.json`, which is a **conceptual world-model** frame (basis change on a
locus), not a visual region, and is not wired to the vision path.

**Therefore RIGHT cannot be produced by this substrate.** Not "was not produced" —
**cannot be**. A `SURFACE` verdict in §4 below means only *"the surface region was minted
as one object"*; it does **not** mean *"carrying its own internal calibration"*, because
there is no representation in which that could be written down. Reporting the absence of
RIGHT is therefore a **tautology, not a finding**, and it is recorded here so that it
cannot later be presented as one.

**The informative contrast is consequently WRONG vs REFUSE**, plus the strictly weaker
question of whether the surface region is minted as one object at all.

### 0.4 THE PROVENANCE INCIDENT — the gate passed while the script loaded the wrong engine

This worktree, like every worktree, ships `runners/dsl/python/substrate_rs/*.py`
(tracked) **without** `_native.abi3.so` (gitignored), and resolves the engine through
`engine_provenance`. At the start of this rung that resolved to the CANONICAL tree's
build, `shared`, Rust source identical — legitimate under §10.1.

**Mid-pilot, a concurrent rung rebuilt the canonical engine from changed Rust source.**
The next pilot process printed
`engine ed399ddae26d ... ** WRONG ENGINE — built from DIFFERENT Rust source than this tree **`.
Those pilot numbers are void and are not used anywhere.

**The reusable defect:** `pytest tests/test_engine_provenance_migrated.py` returned
**7 passed** while a plain script in the same tree, in the same minute, resolved the wrong
artifact. The gate certifies the *tree's* configuration under its own preamble; **it does
not certify that the process you are about to measure in loaded the engine you think it
did.** A bare `python -c` with `sys.path.insert(0, '.')` picks up the canonical `.pth`
first and the gate has nothing to say about it.

**Rule adopted for this rung, and offered upward:** *print `provenance_line()` from
inside the measuring process, into the results artifact, on every run.* A green gate in a
different process is not provenance. Resolved here by running `scripts/engine_build.sh`
(§10.3-safe) so this tree owns engine `68860d0b0f78`, and by calling
`ep.engine_preamble()` + emitting `ep.provenance_line()` inside the measurement script
itself.

---

## 1. THE STIMULUS SET, AND ITS PROVENANCE

**Real video, streamed from the same pinned Jellyfin episodes the G72 proto rungs used**
(`scripts/video_probe_measure.py::jellyfin_frames`; deterministic positional episode
pick, not a content choice):

| corpus | what | `episode_index` | pin | 
|---|---|---|---|
| C1 | cartoon | 0 | `08630d4b` |
| C2 | live-action | 3 | `119eca43` |

**A pin mismatch voids the run**, exactly as in `figadj_replacement_measure.py`.

**Fresh material:** `start_s=900` (the committed G72 rungs used `start_s=300`), `every=2`,
`size=72`, `N=100` frames per corpus. Decode configuration otherwise identical to G72.

**Configuration: G72**, unchanged — one 72×72 greyscale decode tiled row-major into 16
tiles of 18×18 (`VISION_RESOLUTION_SCALE_RESULTS.md` §10). The surface is placed inside
**tile 5** of the 16 (a fixed ordinal position declared in advance, not a content choice),
and only that tile is run.

> **THE TILING IS A HARD STRUCTURAL CONSTRAINT AND IT IS DECLARED, NOT DISCOVERED.**
> G72 mints per 18×18 tile. **A surface larger than one tile cannot be minted as one
> object at all**, whatever the mechanism does. So this design places the surface
> *strictly inside a single tile* — the most favourable geometry that exists for a
> SURFACE outcome. A negative here is therefore a negative under the best available
> conditions; it is not evidence about surfaces that span tiles, and nothing is claimed
> about those.

### 1.1 The surface region

`R` = a centred square of side `s ∈ {8, 14}` inside the 18×18 tile. Both sizes are run and
both are reported. `R` is **ground truth held by the stimulus builder** and is never
written into the graph.

### 1.2 The five content arms — what fills `R`

| arm | fill | role |
|---|---|---|
| `plain` | nothing; the base frame unmodified | **the paired control** — the base rate of protos falling in `R` with no surface present |
| `flat` | the base tile's own median value | a surface with NO internal content — the pure "one object" case, in a real surround |
| `screen` | the OTHER corpus's frame at the same index, area-resampled to `s×s`, rescaled into the base tile's own `[min,max]` | **a screen: real video displayed on a surface.** The rescale is so the region is not separable by brightness alone |
| `mirror` | a horizontally-flipped copy of the base frame's cells immediately left of `R` | **a mirror: the scene reflected** |
| `scramble` | a random permutation of `screen`'s own pixels (seeds 87000–87999) | **dead-instrument control** — identical marginal histogram, structure destroyed. If `screen` ≡ `scramble`, the system is responding to the histogram, not to the content |

### 1.3 Honest scope on the stimulus (PROTOCOL §8)

**These are COMPOSITES, not photographed mirrors and screens.** That is a deliberate
trade and it is the reason the rung can say anything at all: a composite is the only way
to hold `R` as exact ground truth, and the assignment problem is precisely *"which region
carries a different calibration"*, which requires knowing which region does. The cost:
a composite has a hard pixel boundary and no perspective foreshortening, specularity,
frame/bezel, or partial transparency. **A real mirror is strictly harder than this
stimulus in every one of those respects**, so a failure here is a failure on the easy
case, and a success here would NOT transfer without a photographed-surface replication.
Nothing is claimed about photographed surfaces.

---

## 2. PREDICATE ARMS

Both mint predicates of `seeds/vision_border_ownership.json` v1.1.0, via the seed's own
`bown_own` flag (graph DATA, PROTOCOL §0 — never a Python code path):

- `incumbent` (`bo_mint_enclosed`, `bown_own=0.0`) — the committed baseline. `G_figadj`:
  **any** contact with another enclosed component refuses.
- `replacement` (`bo_mint_owned`, `bown_own=1.0`) — the ladder's current best. `G_own_lost`:
  a region `R` must strictly win `perim(R) < perim(Q)` against **every** abutting `Q`; a
  tie is held open and also refuses.

`replacement` is the **primary** arm; `incumbent` is reported alongside.

---

## 3. THE DISCRIMINATOR, AND WHY IT IS NOT THE MINTING QUANTITY

**The trap, from the brief:** the proto layer mints 10–17 multi-cell objects per frame at
G72. **A mirror region will produce objects whether or not the surface was identified**,
so "objects appeared in the mirror" is evidence of nothing.

**The discriminator is the SET RELATION between a proto's support `S` and the
ground-truth rectangle `R`, and it is threshold-free.** For each proto minted in the
target tile:

- `n_overlap` = #{p : S ∩ R ≠ ∅}
- `n_inside`  = #{p : S ⊆ R and S ≠ R} — content minted as free-standing objects inside the surface
- `n_surface` = #{p : R ⊆ S} — the surface minted as one object (the strict case is `S = R`; `|S|/|R|` is reported so a reader can see whether it is the surface or the whole tile)
- `n_spill`   = #{p : S ∩ R ≠ ∅, S ⊄ R, R ⊄ S}

**No thresholds, no tuned fractions — subset, superset and disjointness only.** This is
the strongest §13 outcome available: not a number that falls out, but **no number**.

### 3.1 Independence (the brief's requirement)

`R` is **external ground truth**, known only to the stimulus builder. It is never written
into the graph and no rule can read it. The minting reads exactly four quantities —
`val` (per-tile quantized intensity), `bg` (surroundedness flood from the tile frame),
`glabel` (min-flood component id) and `rim` (materialised perimeter). **None of them is
`R`, and none is derived from `R`.** The discriminator therefore cannot be the quantity
the minting uses, by construction rather than by argument.

### 3.2 The paired control defeats the trap directly

**Nothing is claimed from `n_inside` alone.** Every claim is the paired difference

    Δ = n_inside(content arm) − n_inside(plain)

on the **same frame, same tile, same rectangle `R`**. `plain` measures how many protos
fall inside that rectangle when there is no surface there at all. That is the base rate
the brief warns about, measured rather than assumed.

### 3.3 The instrument positive control (PROTOCOL §1 clause 4 — MUST FIRE)

A synthetic uniform 18×18 tile containing one square of side `s`. The discriminator must
report `S = R` **exactly**. Measured on burned material before this document was written:
**`S == R` exactly at s=8 (64/64) and s=14 (196/196), under BOTH predicate arms.**
The SURFACE verdict is reachable by the instrument. **If this control ever fails, the
run is void** — a discriminator that cannot report SURFACE would make "no SURFACE" a
§1.1 dead-arm floor.

---

## 4. THE THREE-WAY OUTCOME, PER FRAME

Read off the primary (`replacement`) arm, reported for both:

| verdict | condition |
|---|---|
| **REFUSE** (ACCEPTABLE) | `n_overlap == 0` |
| **SURFACE** | `n_surface ≥ 1` |
| **CONTENT-IN-SCENE** (WRONG) | `n_surface == 0` and `n_inside ≥ 1` |
| SPILL-only (residual) | `n_overlap > 0`, `n_inside == 0`, `n_surface == 0` |

Reported as **counts over frames**, per corpus × side × content arm × predicate arm.
Every cell of the design is reported; none is dropped.

---

## 5. HYPOTHESES AND THE PREDICTION, STATED IN ADVANCE (PROTOCOL §3.1, §3.7)

**H1 (two-sided).** The verdict distribution over frames differs between `screen`/`mirror`
and `plain`. Null: it does not — the surface changes nothing, and the objects in the
mirror region are the base rate.

**H2 (two-sided).** `Δ = n_inside(screen) − n_inside(plain) ≠ 0`.

**MY PREDICTION, WITH ITS MECHANISM AND ITS PROVISOS.**

Under `replacement`, `G_own_lost` awards figure status to the **smaller perimeter**
(`perim(R) < perim(Q)`). A side-14 square has a contour of 52 cells; the content blobs
abutting it in real video have far smaller perimeters. **So the surface loses the
competition to essentially anything that touches it, and the content wins.** I predict:

1. **`screen` and `mirror` → CONTENT-IN-SCENE dominates** under `replacement`, with
   `n_surface ≈ 0` wherever content abuts the boundary. **This is the WRONG outcome, and
   I expect it.**
2. **`Δ > 0`** — a screen puts *more* free-standing objects in the scene than the same
   rectangle without a screen.
3. **`flat` raises `n_surface`** relative to `screen` (nothing inside to abut it), but may
   still lose to blobs abutting from **outside**, so I do not predict `n_surface` is high
   in absolute terms.
4. **Under `incumbent`, REFUSE dominates everywhere** — `G_figadj` refuses on any contact
   at all, and the committed refusal rates at G72 are 96.1% (C1) / 92.1% (C2).
5. **`scramble ≈ screen`** on the proto statistics. The mechanism reads a quantized
   intensity field; it has no access to the content's structure. If these differ, my
   account of what the mechanism reads is wrong.

**What would falsify the prediction:** `n_surface` high on `screen` under `replacement`
(the perimeter reading is wrong); or `Δ ≈ 0` (the surface is inert and the base rate
explains everything); or `scramble ≠ screen` (the mechanism sees more than I claim).

**The proviso most likely to break:** that content reliably *abuts* the surface boundary.
If the composite's hard edge makes `R` a clean closed contour with a background gap around
it, the surface may win more often than I expect, and the result would be an artifact of
the composite rather than a fact about surfaces.

---

## 6. THE ASSIGNMENT CUE — NAMED, AND MEASURED FOR PRESENCE ONLY

**The brief requires the cue be FOUND, not inherited: disparity is the dominant
uncorruptable cue in the human case and a monocular system does not have it.**

**This rung builds no assignment mechanism.** There is nowhere to put one (§0.3). What it
does is name a candidate cue and **measure whether the information for it is present in
the stimulus**, so that a future rung is not starting from a hope.

**THE CUE: the temporal DECOUPLING of interior change from exterior change across a
persistent boundary.** A screen's edge stays where it is in the scene while what it
displays changes on its own schedule. Formally, over consecutive frames,

    Δ_in(t)  = mean |I(t+1) − I(t)| over R
    Δ_out(t) = mean |I(t+1) − I(t)| over (tile \ R)
    cue      = Pearson r(Δ_in, Δ_out) over t

**Why content cannot corrupt it.** It is a **coupling** statistic between two aggregate
change magnitudes, not a statistic of what the surface shows. The displayed content sets
the *values* of `Δ_in`; it does not set their *correlation with the surround*. A screen
may display anything at all — and the single thing that defeats the cue is a screen
displaying **the surrounding scene**, which is exactly the `mirror` arm, which is
predicted to fail. **Naming the case that defeats it is what makes this a cue rather than
a hope**, and it is the honest boundary: this cue separates screens, not mirrors.

**Prediction (two-sided):** `r` high for `plain` and `mirror` (interior *is* the same
scene), low for `screen`. Measured on frame data only — it never touches the proto layer,
so it is independent of §3 and §4 in the strong sense.

---

## 7. n, SEEDS, AND THE ANALYSIS

**n = 100 frames per corpus, FIXED IN ADVANCE.** n is not power-limited here: the burned
pilot measured **~0.075 s per (frame × tile × arm)**, so the full design is minutes, and
the binding constraint is the pre-registration, not the compute. Unit of analysis is the
**frame** (PROTOCOL §4); frames within a corpus are not independent, so corpora are
reported separately and never pooled, and paired comparisons are within-frame.

**Seeds 87000–87999**, drawn only for the `scramble` control's permutation RNG. Draws are
reported **measured** by `scripts/seed_audit.py --check 87000 87999`, with the analyser's
own caveat quoted: a `--check` that passes with UNKNOWN sinks has verified nothing, so the
run also reports the sink audit.

**Exactly the tests listed above. No sweeps, no re-runs, no parameter search.** The two
surface sizes and five content arms are a declared factorial stimulus design with every
cell reported — not a search over model parameters, of which this rung changes none.

**Defaults (PROTOCOL §9):** this rung adds no Rust, no seed, no rule and no default. The
`bown_own` flag it sets is the seed's own existing, committed ablation flag.

---

## 8. OUTCOME

*Written after the run, in `VISION_SURFACE_ASSIGNMENT_RESULTS.md`. Nothing above is
edited after the first confirmatory number.*
