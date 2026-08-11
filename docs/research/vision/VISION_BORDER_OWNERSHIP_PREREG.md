# BORDER-OWNERSHIP / PROTO-OBJECT — a directed boundary that OWNS its figure (PRE-REGISTRATION)

*Written and committed BEFORE any measurement (PROTOCOL §3). Seeds 36000–36999,
declared here, ledgered. The block 12000–35999 is untouched (burned by rungs up to
COLOUR IDENTITY). Grounded in `VISION_VENTRAL_GROUNDING.md` — "Mid-level form (V2→V4)",
build-implications #3 (proto-objects/border-ownership) and #4 (recurrence = the
run_rules fixpoint).*

## The claim under test

**A local edge becomes a DIRECTED boundary that OWNS its figure, and a bounded,
owned, PRE-IDENTITY region is minted as a `ProtoObject`.** The biology (grounding doc,
SETTLED-(A)):

- **Zhou, Friedman & von der Heydt 2000** (*J.Neurosci.* 20:6594): for an IDENTICAL
  local edge, V2/V4 cells fire differently depending on WHICH SIDE OWNS the border.
  Ownership is CONTEXT-dependent, not a local property. **THE HEADLINE.**
- Grouping cells integrate ownership over a region, test Gestalt "objectness"
  (closure / surroundedness / size), and FEED BACK to make ownership consistent
  around the whole contour (Craft/Niebur/von der Heydt).
- Correct figure-ground REQUIRES RECURRENCE, not one feedforward sweep. The
  substrate's `run_rules` fixpoint IS that recurrence — where the substrate is
  architecturally AHEAD of the feedforward DNN account (grounding doc #4).
- A **proto-object** is the PRE-IDENTITY stage: bounded, border-owned, NO category.
  It is the NEAR side of the objecthood "what" wall.

## The mechanism (SEED RULES, `seeds/vision_border_ownership.json`; NO new Rust)

**AUDIT (PROTOCOL §12.4, in-code): IN-CLASS by composition, NO new Rust.** Confirmed by
reading the DSL term inventory (`runners/dsl/src/*.rs`): `IfThenElse`, `Argmin`,
`Exists`, `Not`, `Neighbours`, `Filter`, `Count`, `Abs`, `Minus`, `Plus`, `Gt/Lt/Gte/Eq`,
`And/Or`, `NodesOfType`, `PickUnique` all exist and evaluate; effects `set_attr` /
`add_node` / `add_edge` exist. **Surroundedness = discrete REACHABILITY computed by a
same-value flood iterated by `run_rules` to a fixpoint** — the exact `vision_ground` /
`vision_lateral` cell-neighbour-fold idiom, already proven O(N) per sweep under the
`run_rules` drive (NOT the O(N²) `apply_rule_once` drive). No `space_quantize` Rust
flood is needed: the Bellman machinery is for navigable free-space over portals; here
the flood is a 1-bit reachability over a same-value cell field, which the DSL expresses
directly. Figure assignment is an `IfThenElse` precedence ladder over graph-read cues;
minting is `add_node` with a canonical-representative guard; ownership is a directed
`add_edge`. Nothing here needs a primitive the DSL lacks.

The adapter supplies ONLY mechanical geometry (PROTOCOL §0): a grid of `Cell`
{crow, ccol, val, frame, cid} + 4-`neighbour` edges (like `vision_ground`'s field).
`val` is the observed luminance; `frame`=1 iff the cell is on the grid border; `cid` =
crow·W+ccol is a stable integer id. Every DECISION is a rule, gated on
`BorderOwnParams.bown > 0.5` (ships OFF, §9):

1. `bo_bgflood` — **SURROUNDEDNESS as reachability (the recurrence).** `bg`=1 iff the
   cell is a frame cell, OR it has a same-`val` 4-neighbour with `bg`=1. Iterated by
   `run_rules` to a fixpoint, `bg`=1 ⟺ the cell's same-value region is REACHABLE FROM
   THE FRAME without crossing a contour (a value change) ⟺ it is GROUND/background;
   `bg`=0 ⟺ ENCLOSED (figure candidate). The flood never crosses a contour because it
   only propagates along equal-`val` adjacency.
2. `bo_label` — **COMPONENT LABEL** (grouping substrate): `glabel` = min over same-`val`
   4-neighbours' `glabel` (init `cid`), iterated to a fixpoint. Each same-value
   connected component shares its root's `cid` (= its minimum). A cell is a component
   ROOT iff `glabel == cid`.
3. `bo_mint_enclosed` — **PROTO-OBJECT from a CLOSED, SINGLY-SURROUNDED figure.** A
   component ROOT that is enclosed (`bg`=0) mints ONE `ProtoObject{root, members,
   minted:1}` (NO identity/category) iff it is bordered by a SINGLE ground component —
   `Not Exists` two ground-side (`bg`=1) neighbours of the figure with different
   `glabel`. This CLOSURE test is what makes a proto-object an OBJECT (a hole in ONE
   surface), and it is what refuses iid speckle (an interior noise cell is bordered by
   many distinct singleton components → not singly surrounded → no proto). No size
   threshold — the closure constraint FALLS OUT of "a figure is enclosed by one ground"
   (§13). Canonical-representative (root) guard ⇒ batch-safe, exactly one proto per
   enclosed component.
4. `bo_own_enclosed` — **DIRECTED OWNERSHIP.** A figure boundary cell (`bg`=0, adjacent
   across a contour to a `bg`=1 ground cell) sets `owns`=1 and adds a directed
   `owns_figure` edge → its component's `ProtoObject`. The border OWNS the figure side;
   the ground side is not owned. This is the grounded directed contour relation.
5. `bo_mint_gestalt` / `bo_own_gestalt` — **GESTALT figure-ground on an AMBIGUOUS
   bipartition (surroundedness silent).** When NO component is enclosed and the display
   is a bipartition (`Count(components)==2`), figure = the SMALLER component (`Argmin`
   over the two by size); ownership → the smaller; a `ProtoObject` is minted for it.
   A size TIE (`Exists` the other component with equal size) is HELD OPEN — no figure,
   no proto (anti-confabulation; the symmetric Rubin bistable case). Size = `Count`
   (integer, no magic number). The `Count==2` gate is the DEFINITION of a single
   contour splitting the field into figure+ground, not a tuned number — an open/partial
   contour makes ≥3 components and this rule never fires.

`run_rules` runs ALL of 1–5 to a joint fixpoint: flood ⇄ label ⇄ mint ⇄ own iterated
to convergence. That joint fixpoint IS the grouping⇄ownership recurrence (grounding #4);
a single feedforward sweep does not resolve a deep interior (measured, arm RECURRENCE).

## The pre-registered arms — two-sided, exact pass/fail, n fixed

Every deterministic arm consumes NO confirmatory seed (fixed stimuli, no RNG), like
SHAPE-SELFSEE / vision-ground. The ONLY randomness is the NOISE floor.

- **HEADLINE — the ZHOU SIGNATURE (context-dependence).** Two 12×12 configs sharing a
  BYTE-IDENTICAL local window (rows 4–6, cols 4–7, straddling the test edge between
  cell (5,5)=val 1 and (5,6)=val 0), differing only in the FAR global arrangement:
  * Config A: the val-1 region is a bounded interior bar (rows 3–8, cols 3–5, enclosed),
    val-0 is the frame-touching surround → the val-1 side (left) is figure.
  * Config B: the val-0 region is a bounded interior block (rows 3–8, cols 6–8,
    enclosed), val-1 is the frame-touching surround → the val-0 side (right) is figure.
  Statistic: `(owns(5,5), owns(5,6))` in each config. **PASS iff the identical local
  edge FLIPS ownership: A=(1,0) and B=(0,1)**, and each owning border cell's
  `owns_figure` points at the enclosed proto on its own side. Pre-registered check: the
  local window is asserted byte-identical (else the test is invalid). **Two-sided:** if
  ownership is the SAME in A and B (e.g. always the val-1 side, or always the left),
  it is edge-detection (local), not border-ownership (contextual) → NEGATIVE.

- **FIGURE-GROUND on a CLOSED figure.** One enclosed rectangle (val 1, rows 3–8,
  cols 4–7) on a val-0 frame-touching surround. **PASS: exactly ONE `ProtoObject`;
  `members` == 24; every figure boundary cell carries `owns_figure` → that one proto
  (`owns`=1); the surround is ground (`bg`=1, `owns`=0, no proto).** Two-sided: 0 or
  >1 protos, or a surround cell owning, → NEGATIVE.

- **RECURRENCE / global consistency (the FIXPOINT).** A PLUS-shaped enclosed figure
  (concave corners) on a surround. A purely-LOCAL convexity heuristic would assign
  different owners at the concavities; the closed-contour flood keeps ownership globally
  consistent. Statistics: sweeps-to-fixpoint `S`; the number of DISTINCT proto ids owned
  by the figure boundary `K`; and a 1-sweep-truncated resolved-count vs the fixpoint
  resolved-count. **PASS: S > 1 (recurrence is used); K == 1 (all segments own the ONE
  figure — global consistency); and the 1-sweep truncation resolves strictly fewer
  figure cells than the fixpoint (recurrence is LOAD-BEARING, not decorative — §13.2).**
  Two-sided: K > 1 (inconsistent ownership around the contour) → NEGATIVE; S == 1 (no
  recurrence needed) → the recurrence claim is unsupported and reported as such.

- **GESTALT — SIZE (load-bearing, ambiguous bipartition).** A 12×12 split into two
  non-enclosed regions by one vertical contour: left cols 0–3 (val 1, 48 cells) vs right
  cols 4–11 (val 0, 96 cells). **PASS: figure = the SMALLER (left); a `ProtoObject` is
  minted for it; `owns_figure` at the contour points at the smaller region.** Load-bearing
  check (SWAP): make the RIGHT region smaller (left cols 0–7 val 1 = 96, right cols 8–11
  val 0 = 48) → the figure must FOLLOW the size to the right, not stay put. Two-sided: if
  the figure does not track the smaller region across the swap → size is not load-bearing
  → NEGATIVE.

- **GESTALT — CONVEXITY (EXPLORATORY, reported, not a confirmatory claim).** Two
  non-enclosed equal-size regions, one convex (rectangle), one concave (U/L). Predicted:
  figure = the convex one. **Reported as an exploratory measurement**, NOT a pass/fail I
  claim, because a discrete convexity measure on a 4-connected raster is fragile
  (needs diagonal corner logic) and the arc's discipline is to scope a fragile measure
  (§8) rather than overclaim it. If it reproduces cleanly it is reported as a bonus; if
  not, an honest negative (§7). Surroundedness + size are the confirmatory Gestalt cues.

- **ANTI-OVERFIT floor.**
  * **OPEN contour** (deterministic): a val-1 horizontal bar (rows 5–6, cols 0–11)
    touches the frame → NOT enclosed, and splits the field into ≥3 components (not a
    bipartition). **PASS: NO `ProtoObject` minted; NO confident ownership (`owns`=0
    everywhere, no `owns_figure` edge).** An open contour owns nothing.
  * **iid NOISE** (RNG, n=100 fixed, seeds 36000–36099): a 12×12 field of iid `val` in
    [0,99]. **PASS: 0/100 fields mint a `ProtoObject`** — the single-ground closure test
    refuses speckle (an interior noise cell is bordered by many distinct components).
  * **AMBIGUOUS / bistable** (deterministic): a SYMMETRIC bipartition (cols 0–5 val 1 =
    72, cols 6–11 val 0 = 72), equal size, neither enclosed. **PASS: HELD OPEN — 0
    protos, no confident figure** (the size tie is refused, not confabulated). Two-sided:
    if it force-picks one side → confabulation → NEGATIVE.

- **§9 OFF-DAY.** `BorderOwnParams.bown` ships 0.0 (INERT). With the flag OFF: no proto
  minted, no `owns`/`bg`/`glabel`/`owns_figure` written, the seed is not boot-loaded.
  Committed results reproduce byte-identically: sd orbit law {2:1,3:2,4:2,6:2,12:4}
  unmoved; sibling gates green (colour-identity · colour · stream · illusion · blink ·
  ground · time · depth · stereo · dim · gen_infer · provenance · sdloop · cycle-detect);
  vision bench with `data/`.

## Scaling (part of the spec, PROTOCOL "LOCAL / O(N)")

The floods (`bo_bgflood`, `bo_label`) fold each cell's own 4-neighbourhood and are driven
by `run_rules` (`s.tick`, all bindings per pass), NEVER `apply_rule_once` per binding.
Statistic: fit wall-clock border-ownership cost vs grid N (sweep 12²…36²) to `N^p`;
REPORTED (not gated) with the expectation p ≤ ~1.3 (a flood is O(N·diameter); diameter
grows as √N, so a mild super-linear exponent is honest and is NOT the O(N²) drive's ~2).

## Decision rules, seeds, n

- Every H except NOISE is DETERMINISTIC (fixed stimuli) — no confirmatory seed consumed.
- NOISE floor: seeds **36000–36099**, n=100 fixed in advance; PASS = 0/100 mint a proto.
  Confirmatory block **36100–36999** reserved and unburned.
- §9: `seeds/vision_border_ownership.json` ships `bown=0` (INERT). Not boot-loaded.
- Exactly the listed tests. A further attempt needs a NEW pre-registration (§3.6).

## PREDICTION (stated in advance, with provisos)

I predict **the Zhou flip reproduces, figure-ground/recurrence/size all PASS, and every
floor holds at exact-0**, because surroundedness is computed GLOBALLY by the flood (a
region's figure/ground status is a property of its reachability from the frame, not of
the local edge), so the identical local edge MUST flip when the global enclosure flips —
that is the mechanism, not a fit.

- **Proviso on the Zhou flip:** the local window must be provably byte-identical; if it
  is not (a construction error), the arm is invalid, not a result. I assert the window
  and check it in the runner.
- **Proviso on RECURRENCE:** if the plus-shape flood happens to settle in one sweep
  (small grid, short diameter), S==1 and the recurrence claim is unsupported — I will
  size the figure so the interior is ≥2 cells from the ground and REPORT S honestly; a
  forced S>1 by padding would be a magic construction and is disallowed.
- **Proviso on the NOISE floor:** the single-ground closure test is what delivers
  exact-0; if a rare noise field DOES contain a genuinely singly-surrounded enclosed
  region, that is a real (if tiny) proto-object and a HONEST non-zero I will report and
  diagnose, NOT patch away (§5/§7).
- **Proviso on CONVEXITY:** exploratory only (above); a fragile measure is scoped, not
  claimed.

## BOUNDS (PROTOCOL §8 — stated, not overclaimed)

- This is the **PROTO-OBJECT / figure-ground / border-ownership** stage — **PRE-IDENTITY**.
  A `ProtoObject` has NO category, NO recognition. It is the NEAR side of the objecthood
  "what" wall.
- **In-frame integer coords; ownership is a RELATION; surroundedness is discrete
  reachability** (a same-value flood) — no continuous coordinate lives in a frame (the
  frame/continuum invariant).
- Component membership is a same-value connected-component labelling computed IN-GRAPH by
  the flood (`bo_label`), not supplied by the adapter — the adapter supplies only
  `val`/`frame`/`cid` and `neighbour` edges (mechanical geometry, like `vision_ground`).
- **NAMED FRONTIER, NOT this rung:** object IDENTITY / recognition (the "what" wall); the
  identity-untangling-via-generator-discovery crossing (grounding #1); full Gestalt /
  amodal-completion beyond figure-ground (the ILLUSION rung did amodal contour
  completion; this rung's CORE is figure-ground OWNERSHIP, not recognition); convexity as
  a confirmed cue; multi-illuminant/constancy. Texture-statistic quantization (V2) and
  V4 curvature-part coding are separate mid-level rungs, not attempted here.

**Either answer is a result (§7).** "The identical local edge flips ownership with the
global figure; a closed contour mints one owned proto-object; the fixpoint makes
ownership globally consistent; open/noise/ambiguous displays own nothing — O(N)" proves
border-ownership is contextual and proto-objects are the near side of the wall. "Ownership
does not flip / needs Rust / the fixpoint does not converge" is a clean negative reported
in place.
