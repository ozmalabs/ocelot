# ARC-AGI-3 ls20 with the perception eye — scoping (understand-before-build)

> **Status: SCOPING DOC, not a rung.** No seed, no gate, no pre-registration is
> filed here — this scopes the pivot and *proposes* the first pre-registerable
> gate. `VISION_PROTOCOL.md` is untouched. Everything below is either (a) cited
> from a source, (b) read from the code with a path, or (c) flagged as a guess.

## 0. Headline (lead honestly)

**The pivot in one sentence:** ls20 is already played *graph-native* today, but the
eye reads the **symbolic integer grid** (the oracle) — not the rendered pixels.
`WorldAdapter._perceive_regions` runs `cv2.connectedComponentsWithStats` on the
raw `arc3_grid` integer values, per exact colour index. That is perfect,
oracle-*given* segmentation: each object is a set of cells that share an exact
integer, handed to the agent for free. The owner's commitment — **the eye SEES
the game (its rendered pixels), the symbolic grid is scoring-oracle only** (the
VizDoom depth/labels discipline) — is **not yet honoured on the primary
perception path.** The RGB render exists (`worlds/arc.py::_render_screen`, palette
verified against a live ls20 frame) and is fed to `GraphEye`, but only opt-in
(`render=False` by default) and the code marks it "redundant" for
region/agency perception.

**The deciding number that does not yet exist:** seeing only the RGB render, does
the eye carve the ls20 frame into the **same object/Region set** the oracle grid
produces? (mean per-Region IoU + matched-Region fraction vs the golden trace).
Everything downstream — agency, meter, goal derivation, navigation, transform —
already runs off `Region` nodes, so **if the pixel eye reproduces the oracle
Regions, the entire existing stack runs on SEEING with no other change.** That IoU
is the first rung.

**How far the ShapeDecode core already goes:** most of the way on *understanding*,
none of the way on *perception*. `ShapeDecode`'s transform rung (rotate / reflect
/ recolour / translate as a per-dimension quantum delta) and dimension-inference
rung (latent dims: rotation90 / reflection / scale2 / modular / translate / general
integer-linear) express exactly the shape-relations ls20's **symbol-transformation
mechanic** needs — but they are not yet wired to ls20 perception, and they consume a
*signature*, which nothing yet extracts from a *perceived* region. **Two gaps, not
one:** (1) *perception* — pixels → regions → signatures (the headline); and (2)
higher-order *object reasoning* — the carve is 4-connected equal-value only (a
two-colour avatar shatters) with no counting / containment / symmetry-detection /
relational scene graph. Honest caution: on real ink the substrate's own discrete
featureset plateaued at ~33–41% (the ~80% came from continuous comparators outside
the Term path), so the native core must be *measured* on ls20, not assumed strong.

---

## PART A — ls20 understood (with sources)

### A.1 What ARC-AGI-3 is

ARC-AGI-3 is an **interactive reasoning benchmark**: agents must explore novel
environments, acquire goals on the fly, build adaptable world models, and learn
continuously — a shift from static input→output puzzles to video-game-like
environments where an agent must *perceive, plan, and act across many steps*.

- **Games:** 6 environments — 3 **public** for development (`ft09`, **`ls20`**,
  `vc33`) and 3 **private** for the leaderboard (`sp80`, `lp85`, `as66`).
- **Preview competition:** ran 30 days, **18 Jul – 19 Aug 2025**; 1,200+ human
  players, 3,900+ games generated the human baselines.
- **Level structure:** each game has **8–10 levels**; each subsequent level
  introduces a new mechanic. Score = number of levels completed; tiebreaker =
  total actions taken.
- **"Intelligence is efficiency":** agents are scored on action efficiency vs a
  human baseline (100% = beats every game as efficiently as humans). The winning
  preview agent reached **12.58%** action efficiency; frontier LLMs (GPT-5,
  Claude, Gemini) scored **below 1%**.

Sources: [ARC-AGI-3 Preview: 30-Day Learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings),
[ARC-AGI-3](https://arcprize.org/arc-agi/3),
[ARC-AGI-3 Technical Report (PDF)](https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf),
[GPT-5/Claude/Gemini below 1%](https://dev.to/codepawl/gpt-5-claude-gemini-all-score-below-1-arc-agi-3-just-broke-every-frontier-model-5dbj).

### A.2 The ls20 game specifically

ls20 is described as **"Agentic, map based"**:

> "Navigate a map while bringing a matching symbol to another object. The symbol
> must go through various transformations in order for it to reach the goal."
> — [ARC-AGI-3 30-Day Learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings)

So ls20 fuses two demands:
1. **Navigation** — move an avatar through a map (rooms / corridors / walls) to a
   goal (the "NAVIGATION/MOVEMENT mechanic … what a game like ls20 instantiates —
   an avatar moved through a space to reach a goal-cell", `seeds/game_mechanics.json`).
2. **Symbol transformation** — carry a symbol that must undergo *transformations*
   (rotate / recolour / reshape) to *match* a target object at the goal. **This is
   the shape-understanding crux the owner named.**

**Concrete ls20 structure the repo has already read from live frames** (`worlds/arc.py`
lines 33–56, "Verified against a live ls20 frame"; `seeds/projection.json`,
`seeds/meter.json`):
- Grid **64×64**, integer cell values **0–15** (`scripts/arc3_live_env.py:6,33`).
- Palette is the ARC-AGI-3 render (NOT canonical ARC order): a **grey ramp for
  0–5** (white→black) then hues 6–15. In ls20: **value 4 = dark-grey walls/field**,
  **value 3 = mid-grey rooms**, **value 9 = blue** + **value 11 = yellow** = the
  player, **value 11 yellow = the countdown meter bar**.
- ls20 has a **countdown meter** (a value-11 bar that *resizes* while staying put —
  `seeds/meter.json` recognises it as a monotone-depleting COUNTDOWN sub-kind).
- ls20 has **enclosure / room structure** (`seeds/projection.json` extrude prior:
  `wall → full column {0,1,2}`, `floor → single locus {0}`; the floor is the
  largest Region = structural ground).

### A.3 Observation / action / scoring (the interaction contract)

From the published protocol, re-implemented faithfully offline in
`scripts/arc3_env.py:16–36` and driven live by `scripts/arc3_live_env.py`:

- **Observation (frame):** a list of 1..N grids, each up to **64×64**, integer
  cells **0..15** (colour/state indices), origin top-left, `(x, y)` addressing.
  The live JSON is `{game_id, guid, state, score, frame:[64×64 grid],
  levels_completed}`. **The API returns integers; a human sees the rendered
  coloured squares.**
- **Action space:** `RESET`, `ACTION1` (up), `ACTION2` (down), `ACTION3` (left),
  `ACTION4` (right), `ACTION5` (interact/select/execute), `ACTION6(x,y)`
  (coordinate click, x,y ∈ 0..63), `ACTION7` (undo).
- **State:** `NOT_PLAYED | NOT_FINISHED | WIN | GAME_OVER`.
- **Scoring:** levels completed (score) + action count (efficiency / tiebreaker).

### A.4 How ls20 differs from ARC-1/2

ARC-1/2 are **static** input→output grid puzzles solved by pattern-recognition
over fixed example pairs. ARC-AGI-3 / ls20 is **interactive**: no NL instructions,
the agent must **infer the rules and the goal by acting**, build a world model,
and plan a long-horizon route — measured by *efficiency across time*, not a single
output grid. "Solving" ls20 = discover which cell is the avatar, what each action
does, the transformation law of the symbol, and the goal — purely from observed
transitions.

### A.5 Seeing-vs-oracle for ls20 (the discipline)

The API *literally returns the integer grid.* Honouring "the eye sees the game"
means: the eye perceives the **RGB render** (16-palette coloured squares, the same
image a human sees), and the **integer grid is used ONLY for scoring/verification**
(the oracle) — exactly as VizDoom's per-pixel depth/labels are scoring-oracle only
while the eye must SEE walls. Today the ls20 eye violates this: it reads the
integers as its percept.

### A.6 What already exists in the repo (vs what's missing)

**Live, graph-native line (current, post-migration — the thing to build on):**
- `scripts/arc_run.py` — the canonical seed-booted runner. Agent derives its own
  goals; host loop is perceive → stamp score/budget → tick → read `chosen_action`.
- `worlds/arc.py` — the `ArcWorld` adapter: Frame→Substrate ingest, the affordance
  set (Up/Down/Left/Right/Select/Reset + per-cell Click), **`_render_screen` + the
  verified 16-colour palette** (the pixel render, currently opt-in), and an
  order-4 self-authoring seam (`author_faculty` → a retaining visual cortex).
- `substrate/world_adapter.py::perceive_frame` / `_perceive_regions` — the eye
  (segment + cross-frame track → persistent `Region` nodes). **Reads the oracle
  grid.**
- `scripts/arc3_live_env.py` — the network connection (needs `ARC_API_KEY`, absent
  in this env; the offline `arc3_env.py` is the faithful stand-in).
- **Seeds already modelling ls20 structure:** `goal_derivation`, `agency`,
  `meter` (the ls20 countdown bar + a full meter taxonomy: extent/fill/gauge/
  icons), `projection` (ls20 floor/wall extrude priors, top-down + map viewpoints,
  parallax depth-from-motion), `grid_navigation`, `quanta_navigation`,
  `spatial_sense`, `game_mechanics` (navigation mechanic = ls20).

**Legacy (pre-migration CuriousAgent era — mostly deletable, do NOT build on):**
`domains/arc3_world.py`, `domains/arc3_seed.py`, `domains/arc3_full_seed.py`,
`domains/arc3_thin.py`, and the many one-off `scripts/arc_*.py` capture/diagnose
scripts. `arc3_world.py` explicitly ingests each grid cell as a `CellC<v>` node
(oracle read) and references the deleted `CuriousAgent`.

**Missing / degenerate for the pivot:**
- **Pixel perception** — the eye sees the grid, not pixels (the headline gap).
- **Foveated map discovery** — `quanta_navigation`'s "whole-map-on-load is the
  degenerate case" (CLAUDE.md): ls20's map is currently handed whole, not
  discovered foveally by an eye that only sees what's on screen.
- **The symbol-transformation mechanic** — the ls20 crux is not yet modelled as a
  `TransformDecode`/`DimInfer` shape step wired to perception.
- **A signature extractor** — nothing turns a *perceived* Region into a
  `ShapeDecode` signature (the bridge from the eye to the shape core).

---

## PART B — the substrate's SHAPE machinery (inventory + measured state)

### B.1 ShapeDecode — the dequantization primitive (`runners/dsl/src/shape_decode.rs`)

The core of "deep understanding of shape." A Rust port of the beam-search shape
composer (`reflective_faculty.py::compose_design_for_goal`), field-for-field
parity-tested. An `Observation` carries a **signature** (a relation-system) that is
decoded against a held **`ShapeSignature` codebook**. Three rungs, Occam-ordered:

1. **Literal decode / recognize** — exact match of a held shape (parts compete, the
   assignment emerges, the residual is the unmatched span).
2. **`TransformDecode`** — checks whether a residual is the SAME held shape stepping
   by **one per-dimension quantum delta**: **rotate / reflect / recolour / translate**
   (kinds `rotation90`, `reflection`, `translate`, plus symbolic recolour as a global
   rename). "Transformation is quantum change in a specific dimension." A
   `Transform{dim,delta}` is minted as graph data; the predicate slot is never
   transformable; identity is flagged.
3. **`DimInfer` / `DimensionGenerator`** — infers a **latent dimension** when a
   residual is coupled across observed dims (e.g. a flat 2D shape rotated in Z). It
   decodes against a held generator codebook; **generator kinds:** `rotation90`,
   `reflection_r`/`reflection_c`, **`scale2`** (multiplicative ×2^k log-scale base),
   **`modular`** (cyclic Z_n step with wrap), **`translate`** (affine offset), and
   **`linear`** (a general integer `GL(n,ℤ)` matrix carried as *graph data* —
   rotation/reflection/shear/scale, so minted generators participate with no new
   dispatch arm). Tries every ordered **pair** of generators (composition length ≤ 2).
   Mints a `LatentDimension` — "quanta OF dimensions." Two siblings extend it:
   **`GenInfer`** *mints a new integer-linear generator from an orbit* when the
   codebook is exhausted (guarded unimodular `|det|=1` / similarity-subgroup, so the
   "universal container" over-merge can't leak); **`TimeInfer`** infers whether a
   frame *sequence* is an orbit under one transition generator whose exponent is a
   minted `latent:time` axis.

**Key invariant (`coord_ints`, lines ~550):** in-frame coordinates are the **integer
lattice** — `coord_ints` returns `None` on a float slot *by design* (in-frame is
integer; all real-valued structure — rotation by a real angle, scale ratios,
verdict metrics — lives in the cross-frame MAP, never in a frame's coordinates).

**What it expresses for ARC:** exact shape match; **symmetry / rotation / reflection**
recognition; **discrete recolour** as a transform delta; translation; **periodic /
modular** structure; **scale families**; latent-dimension minting. This is directly
the vocabulary ls20's symbol-transformation mechanic needs.

**What it does NOT do (the ARC gaps):**
- No **object segmentation from pixels** — it consumes a signature, not an image.
- No **signature extraction from a perceived region** (the missing bridge).
- **Integer-lattice + exact-match + count-preserving only** (`coord_ints`): no
  approximate/float shapes, no odd-ratio scaling (only 2^k), no continuous rotation
  (only 90°); a transform requires **matching relation counts**, so add/remove-object
  and partial-occlusion transforms fall *outside a single decode*.
- No first-class **counting**, **containment / topology** (holes, inside/outside), or
  **symmetry / repetition detection** as an operator (a symmetry is expressible only
  if it is one of the named generators applied to a *held* part). Composition exists
  as *arrangement* (see B.5) but count/containment are not modelled.

### B.2 The sd_* dynamic-quantization loop (`seeds/shape_decode_loop.json`)

The decode → grow → re-decode fixpoint as tick-driven graph rules — "shape matching
IS dequantization; order-N growth IS dynamic quantization; the SAME op both ways;
boundaries EMERGE from the decode, not pre-cut." The rules
(`sd_decode` / `sd_recognize` / `sd_transform_decode` / `sd_recognize_transformed` /
`sd_infer_dimension` / `sd_recognize_dim` / `sd_mint_quantum` / `sd_redecode`) run in
one `run_rules` fixpoint: full coverage → recognize (no growth); residual → try a
transform in the existing basis → try inferring a dimension → only if BOTH fail,
mint a new `CapabilityAxis` quantum; codebook growth (`codebook_epoch`) re-arms
prior observations so an exact match beats a transform reading. **No Python
iteration — the fixpoint IS the loop.**

### B.3 Quanta navigation (`runners/dsl/src/space_quantize.rs`, `seeds/quanta_navigation.json`)

The MAP/ROUTE half of ls20. `space_quantize` decodes a persistent map *belief*
(unknown = absence, first-class) into **N-dim `SpaceQuantum` boxes**, **per body
shape** (config-space erosion via `body_key` — a 1×1 vs 2×2 avatar route
differently over ONE belief), **foveated** (decode only in focus, incremental
reuse), with per-dimension resolution + per-dimension residual splits. The seed
rules (14 `qf_*`) do an epoch-gated Bellman flood over portals, N-dim hops, and
multi-source frontier-seek exploration, with stale/retire lifecycles as rules.
**Adapters opt in via `nav_repr="quanta"`.** CLAUDE.md notes ls20's "whole-map-on-load
is the degenerate case" — i.e. the foveated-discovery machinery exists but ls20
currently loads the whole map; a SEEING eye (on-screen only) would exercise the
non-degenerate foveated path.

### B.4 The pattern-recognition eye (`domains/doom_pattern_eye.py`, ledger 209000–214000)

The closest existing thing to a *pixel* shape reader — RGB pixels only, single-frame,
integer descriptors (no depth/labels oracle, audited). Two channels:
- **Texture** (pattern-as-arrangement + colour-sign): vertical-gradient luma energy
  (`col_texture_level`); **colour-as-a-sign** = chroma contrast from the ambient wall
  chroma (`col_colour_level`); and pattern-as-arrangement = the **horizontal-gradient
  share** (fraction of edge energy forming vertical contours), which normalises out
  total energy. **Measured: faint-door door-vs-wall AUC 0.94** (vs the energy scalar's
  0.69).
- **Geometry** (occluding-contour): seen horizontal luma gradient minus the ambient
  median, so only a local structural edge survives. **Measured AUC 0.78** vs a
  depth-edge oracle over ~169k real columns (supersedes depth-from-motion = chance).

**Critical limit for ARC:** it emits **per-column 1-D descriptors**, not 2-D object
masks — a texture/edge feature extractor feeding nearest-prototype recognition. It has
**colour-as-sign but not colour-mapping**, and does no object segmentation. Built for
Doom, it is not yet the ls20 eye — but it is the proven precedent for *seeing from
pixels* rather than reading the oracle.

### B.5 Omniglot / character composition (`scripts/jabberwock_omniglot*.py`, `runners/dsl/src/strokes.rs`)

The substrate's most developed shape-recognition line — one-shot character
recognition from ink. `StrokeQuantize` produces rotation/translation/scale-**invariant**
relative-pose signatures (pose carried as separate single-slot relations so every
similarity transform is a rung-1 quantum delta read by the *unchanged*
`TransformDecode`). Character composition = the SAME sd loop one level up
(strokes → characters via relative-pose relations). **Analysis-by-synthesis (AbS):**
`StrokeRender` is `StrokeQuantize`'s exact inverse, so reading = propose-by-index →
RENDER → compare.

**Measured ceilings (one-shot 20-way, held-out-alphabet, cross-drawer; powered
n=200–400, Wilson CIs). There is a decisive TWO-TRACK split:**
- **Continuous track (SC+TPS / AbS comparators, float — *outside* the integer-lattice
  Term path):** **80.5% [76.3, 84.1]** parse-marginal (`run17b_completion.py`, n=200);
  **73.5% [67.0, 79.1]** (RUN 16); 78–81.5% at matched protocol.
- **Discrete graph-native strokeq relation track (the substrate's OWN integer-lattice
  featureset):** plateaus at **~33.8%** (strict whole-relation coverage) → **41.2%**
  with sub-stroke composition (RUN 14). **52.8% of misses** are decided by a tie at
  the strict metric.
- **Weak render-verdict powered floor:** **26.8% [22.6, 31.3]** (the honest floor once
  the easy 4-alphabet eval was corrected).
- **Composition = +21pp** over a multiset baseline (CI-separated) — **arrangement is
  real and large.** **coverage@5 ≈ 54%** — proposal recall is the binding lever.
- **The synthesis:** "**bins propose, continuous decides**" — earned quanta are the
  LEARNING/PROPOSAL layer; strong continuous geometry is the VERDICT layer.

**The honest caution this raises for ls20:** the ~80% numbers come from **continuous
(float) SC+TPS/AbS comparators that live OUTSIDE the integer-lattice Term path**; the
substrate's *own* discrete symbolic featureset is materially weaker on real ink
(~33–41%). For ARC this cuts the RIGHT way — ARC shapes are **discrete cell
arrangements on an integer lattice**, so the "in-frame is integer / continuum is
cross-frame" invariant fits: the verdict layer for ARC is **exact set equality**, not
TPS (cf. memory "a comparison can be false, a selection cannot" — refusers decide by
exact equality vs a reconstruction). ARC does not need the continuous comparator that
carried Omniglot — but the ~33–41% discrete plateau is the measured warning that the
native featureset alone is not obviously strong, and must be **measured on ls20
shapes, not assumed** from the Omniglot arc. **What transfers:** composition-as-
arrangement (+21pp), the transform rung, the propose/verdict split, AbS render-and-
compare (`StrokeRender`/`StrokeQuantize` exact inverse — the ARC analogue is
`_render_screen` vs the pixel eye).

### B.6 Scene carving / held surface / allocentric reconstruction

The scene carve is a **native Rust primitive**, `substrate.rs::segment_and_track`
(line 3630, exposed to Python as `native.segment`; the `cv2` path in
`_perceive_regions`, `world_adapter.py:7619`, is the fallback + spec). It runs
**union-find over 4-connected equal-value cells** → `Comp`s (value, cell set, count,
centroid, bbox); the **largest component = the structural ground** (the floor,
`seeds/projection.json:661`); `track_comps` gives cross-frame identity (cell-overlap →
nearest-same-value centroid → velocity-predicted), conserving ground and re-pointing
figures' `within` membership; birth/death of `Region` nodes in place; motion =
centroid delta. A **motion-common-fate** twin (`segment_motion_and_track`, :3921)
floods by shared motion. `agency` / occlusion / `meter` / `goal_derivation` are graph
rules **over these `Region` nodes**; the `projection` seed holds an allocentric
reconstruction (Loci on Axes, top-down + map viewpoints, project/lift, parallax
depth-from-motion). **Every bit of this carving starts from the oracle integer grid.**

**Two ARC gaps here, independent of the pixel pivot:**
- The value carve is **4-connected, equal-value only** — no 8-connectivity, **no
  multi-colour objects**: a striped or multi-hue object *shatters into per-value
  fragments* (substrate.rs:3917 explicitly: "has no object notion and shatters by grey
  value"). An ls20 avatar rendered in *two* colours (value 9 blue + value 11 yellow)
  is already two Regions today.
- **No containment/topology, no counting, no relational scene graph** binding carved
  objects to each other (copy-of / contains / aligned-with). Those must be composed on
  top from Terms/rules.

### B.7 Synthesis — what the substrate HAS vs what ARC object-reasoning still needs

The substrate has strong, tested machinery for: (a) **transform-as-quantum-delta**
recognition (translate / rotate90 / reflect / scale2 / modular / general-linear +
discrete recolour as a `subst` function); (b) **compositional shape decode + dynamic
quantization** (mint axes/generators from residuals, re-decode on growth); (c)
**connected-component object carving** (4-connected equal-value) + cross-frame
tracking; (d) **N-dim spatial / config-space navigation**; (e) **pixel texture / edge
/ occluding-contour feature extraction**.

The gaps an ls20/ARC solver still needs to build: **8-connected / multi-colour object
segmentation**, **symmetry & repetition detection** as first-class operators,
**counting**, **containment / topology (holes, inside/outside)**, and a **relational
scene graph** binding carved objects (copy-of / contains / aligned-with). The
transform machinery is **integer-lattice + exact-match + count-preserving only**, so
add/remove-object and partial-occlusion transforms fall outside a single decode.

**The consistent finding across every read: the shape CORE is strong on
transform/dimension/composition and consumes a *signature*; the missing pieces are (1)
the pixels → regions → signature *perception* bridge (the pivot), and (2) the
higher-order object-reasoning operators (count / containment / symmetry / relational
scene graph) — neither is the shape algebra, which is well-built.**

---

## PART C — gap analysis + ordered rung plan (measure-first)

### C.1 The gap, precisely

To do ls20 **by SEEING (pixels → shapes → action)**, the eye must recover from the
RGB render everything it currently gets free from the oracle integers, and the shape
core must be wired to the ls20 mechanic. Two shape-understanding demands ls20 makes:

1. **Segmentation from pixels.** Recover the cell lattice + per-cell colour (quantize
   RGB back to the 16-palette) + connected Regions **without** the integer grid.
   Trivial from the oracle (exact integers); from pixels it needs colour quantization
   + grid registration + robustness to the render's block edges. *This is the first
   blocker.*
2. **The symbol-transformation mechanic (the crux).** "The symbol must go through
   various transformations to reach the goal." This is exactly `TransformDecode` /
   `DimInfer` territory — a symbol stepping by a per-dimension quantum delta — but it
   is **not yet wired** to ls20 perception, and it needs a *signature extractor* to
   turn a perceived symbol Region into a `ShapeDecode` signature.

**A second, independent gap (do not conflate with the pixel pivot):** even from the
oracle grid, the carve is **4-connected equal-value only** and there is **no counting
/ containment / symmetry-detection / relational scene graph** (B.6, B.7). A
two-colour ls20 avatar already shatters into two Regions today. These are
object-reasoning operators to build regardless of pixels — but they are *downstream*
of, and gated by, getting a correct object set, which is why the pixel-parity rung
comes first.

**Where the first measurable blocker is (the Doom-line lesson — name the deciding
number that does not exist):** whether the **pixel eye** carves the ls20 frame into
the **same object set** the oracle grid gives. Everything downstream already runs off
`Region` nodes; if the pixel eye reproduces the oracle Regions, the whole existing
stack (agency, meter, goal, navigation) runs on SEEING. If it does not, that IoU gap
is the first thing to close, and it is measurable *today* against a golden trace whose
methodology already exists (`docs/incremental_perception_design.md:72`).

### C.2 The ordered rung plan

**Rung 0 — baseline capture (the oracle golden trace).** Run **today's** oracle-grid
`_perceive_regions` over a real (or offline `arc3_env` `ls20`-shaped) episode and
snapshot, per frame, the set of `Region`s as **canonical member-position sets**
(identity-independent) + each Region's `count / cy / cx`. This is the oracle.
*Methodology already specified in `docs/incremental_perception_design.md:72`.*
Honest baseline: oracle-vs-oracle agreement = **1.0 by construction**; the pixel eye
starts **unmeasured** (no number exists yet — that is the point).

**Rung 1 — THE FIRST REAL NUMBER: pixel-segmentation parity.** Feed the eye **only**
the 192×192 RGB render (`worlds/arc.py::_render_screen`; cell_px = 192//64 = 3px).
The eye must (a) **quantize** pixels to the 16-palette, (b) **register** the cell
grid, (c) **connected-component** into `Region`s, and match the Rung-0 golden trace.
- **Pre-registerable gate (to be filed as its own rung, not here):** on N frames of
  one real ls20 episode, **mean per-Region IoU ≥ T** AND **matched-Region fraction
  ≥ F** (pixel-eye Regions vs oracle-grid golden-trace Regions). *T and F are chosen
  at pre-registration time from a first honest measurement — this doc does not
  pre-set them.*
- **Honest baseline:** none exists; this is the first measurement. A trivial
  reference point to beat: "render then argmax-nearest-palette per 3×3 block" should
  be near-perfect on a clean synthetic render — so the gate must be measured on a
  **real** ls20 render (anti-aliasing / scaling artefacts) to be meaningful, and the
  claim must state the episode + frame count (per the standing rule: eval-subset
  coverage is part of every claim).
- **Seeing-vs-oracle:** the RGB render is the **PERCEPT**; the integer grid is the
  **SCORING ORACLE** (used only to build the golden trace and to score IoU). This is
  the rung that converts the ls20 eye from oracle-reading to seeing.

**Rung 2 — shape-vocabulary recognition.** Does `ShapeDecode` recognise the ls20 shape
vocabulary (wall / room / avatar / symbol / meter-bar) **from the pixel-eye Regions**
at accuracy Y? Requires the **signature extractor** (Region → `ShapeDecode`
signature). Gate: per-class recognition accuracy on the labelled ls20 vocabulary.

**Rung 3 — the symbol transform (the ls20 crux).** Model the carried symbol → goal
symbol as a `TransformDecode` / `DimInfer` step; measure whether the agent recognises
the **required transformation** (rotate / recolour / reshape) that makes the symbol
match its goal. Gate: fraction of symbol-goal pairs whose transform is correctly
identified (synthetic ls20-shaped set first; the standing rule — synthetic-proven ≠
benchmark value, report both).

**Rung 4 — end-to-end on real ls20.** Levels-completed / action-efficiency on the live
ls20 game (needs `ARC_API_KEY`), reported **alongside** the synthetic mechanism number.

### C.3 What is SEEING-vs-ORACLE-sensitive

| Signal | Must be **perceived** (eye) | May be **oracle** (scoring) |
|---|---|---|
| Cell colours / Region boundaries | ✔ (from the RGB render) | integer grid — verification only |
| Avatar identity, its motion | ✔ (which Region moves under an action) | — |
| Meter extent (countdown bar) | ✔ (bbox resize from pixels) | — |
| Symbol shape + its transform | ✔ (signature from pixels) | — |
| Score, WIN/GAME_OVER, levels_completed | — | ✔ (given by the API) |
| Action repertoire, RESET | given affordance (not perception) | — |

The rule of thumb: **anything a human reads off the screen must be perceived; anything
the game *tells* you (score, win, level count) may be oracle.** The integer grid is
the single biggest oracle temptation — it must be demoted to golden-trace/verification.

---

## What "deep understanding of shape" concretely means for ls20

1. **Carve the scene into objects from pixels** (segmentation — the eye).
2. **Recognise each object's shape** invariant to position / rotation / reflection /
   recolour / scale (`ShapeDecode` literal + transform rungs).
3. **Recognise that two objects are related by a transformation** — the symbol the
   avatar carries vs the target at the goal (`TransformDecode` / `DimInfer`). *This is
   the ls20 crux.*
4. **Compose multi-object arrangements** (a room + its contents) and reason over
   **containment / adjacency** for routing (composition-as-arrangement + quanta-nav).

**How far the ShapeDecode core already goes:** (2) and (3) are its core strength —
transform-as-quantum-delta + latent-dimension inference cover rotation / reflection /
recolour / translate / scale / modular / general-integer-linear **exactly**, in one
Occam-ordered fixpoint (with `GenInfer`/`TimeInfer` minting new generators/time axes);
composition-as-arrangement is proven (+21pp on Omniglot). What it does **not** yet do:
(1) segment from pixels (today oracle-fed); the **signature extractor** that turns a
perceived Region into a `ShapeDecode` signature; **counting / containment / symmetry-
detection** as first-class predicates; and a **relational scene graph**. And two honest
cautions: the transform machinery is **integer-lattice + exact-match + count-preserving
only** (add/remove-object and partial-occlusion fall outside a single decode), and on
real ink the substrate's *own* discrete featureset plateaued at **~33–41%** while the
~80% came from continuous comparators outside the Term path — so the native shape core
must be **measured on ls20, not assumed strong** from Omniglot.

**So the ShapeDecode core is most of the *understanding* (transform / dimension /
composition), and it fits ARC's integer lattice; the missing halves are *perception*
(pixels → regions → signatures — the pivot) and the higher-order object-reasoning
operators (count / containment / symmetry / relational scene graph).**

---

## Sources

- [ARC-AGI-3 Preview: 30-Day Learnings](https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings) — ls20 = "Agentic, map based … bring a matching symbol … the symbol must go through various transformations"; games list; efficiency framing; 12.58% winner.
- [ARC-AGI-3](https://arcprize.org/arc-agi/3) — benchmark definition; interactive vs static.
- [ARC-AGI-3 Technical Report (PDF)](https://arcprize.org/media/ARC_AGI_3_Technical_Report.pdf).
- [GPT-5 / Claude / Gemini all below 1%](https://dev.to/codepawl/gpt-5-claude-gemini-all-score-below-1-arc-agi-3-just-broke-every-frontier-model-5dbj).
- [Graph-Based Exploration for ARC-AGI-3 (arXiv 2512.24156)](https://arxiv.org/pdf/2512.24156).
- Repo: `scripts/arc3_env.py`, `scripts/arc3_live_env.py`, `worlds/arc.py`, `scripts/arc_run.py`, `substrate/world_adapter.py` (`_perceive_regions`), `runners/dsl/src/shape_decode.rs`, `seeds/shape_decode_loop.json`, `runners/dsl/src/space_quantize.rs`, `seeds/quanta_navigation.json`, `seeds/{projection,meter,goal_derivation,agency,game_mechanics}.json`, `docs/incremental_perception_design.md`, project `CLAUDE.md` (Omniglot ceilings, quanta-nav degenerate-case note).
