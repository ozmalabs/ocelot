# BORDER-OWNERSHIP / PROTO-OBJECT — RESULTS

*Confirmatory run of `VISION_BORDER_OWNERSHIP_PREREG.md` (committed at `60be4769`,
BEFORE this run, §3). Nothing below was measured before the pre-registration was
committed.*

## Provenance (§10)

- **Engine:** `engine 7d5f50c18673 @ …/runners/dsl/python/substrate_rs/_native.abi3.so
  [shared build, Rust source identical]` — **NO new Rust** (§10.1 rule 4: a shared build
  is legitimate exactly because the Rust source is byte-identical; `git diff
  1479bdfa..HEAD -- runners/dsl/src runners/dsl/Cargo.toml` is EMPTY).
- **Base:** branch `gamma-substrate/vision-border-ownership` off `main` HEAD
  **`1479bdfa`** (verified ancestor). Prereg commit `60be4769`.
- **Runner:** `scripts/border_ownership_measure.py` → `results/border_ownership_measure.json`.
- **Gate:** `tests/test_border_ownership_migrated.py` (9/9). **Seed:**
  `seeds/vision_border_ownership.json` (built by `tools/build_vision_border_ownership.py`).
  **Adapter:** `domains/border_ownership_world.py`. **Seeds:** 36000–36099 (noise floor)
  consumed; **36100–36999 CLEAN; 12000–35999 untouched.**

## AUDIT (§12.4, in-code) — IN-CLASS by composition, NO new Rust

Border-ownership / figure-ground is expressible entirely by DSL composition. Verified by
reading the term inventory in `runners/dsl/src/*.rs`: `IfThenElse`, `Argmin`, `Exists`,
`Not`, `Neighbours`, `Filter`, `Count`, `Abs`, `Minus`, `Plus`, `Gt/Lt/Gte/Eq`,
`And/Or`, `NodesOfType`, `PickUnique` all present and evaluating; effects `set_attr` /
`add_node` / `add_edge` present (`add_edge` binds src/tgt from the match, so ownership
binds its `ProtoObject` via a `has_proto` match edge — `graph_rules.rs:214`).

**Surroundedness = discrete REACHABILITY computed by a same-value flood iterated by
`run_rules` to a fixpoint** — the exact `vision_ground` / `vision_lateral`
cell-neighbour-fold idiom, already proven O(N) per sweep under the `run_rules` drive
(NOT the O(N²) `apply_rule_once` drive). **No `space_quantize` Rust flood is needed:** the
Bellman machinery (`space_quantize.rs`, `seeds/quanta_navigation.json`) floods navigable
FREE-SPACE over portals with per-body erosion; here the flood is a 1-bit reachability over
a same-value cell field, which the DSL expresses directly (`bo_bgflood`). Figure
assignment is a cue ladder over graph-read attrs (enclosure → size), minting is
`add_node` + a canonical-representative (component-root) guard, ownership is a directed
`add_edge`, and the grouping⇄ownership recurrence is the `run_rules` fixpoint. **Nothing
here needs a primitive the DSL lacks.**

## Per-arm verdict (`H` = `W` = 12; engine `7d5f50c18673`)

| arm | verdict | key numbers |
|---|---|---|
| **HEADLINE — ZHOU context-dependence** | **PASS** | local window BYTE-IDENTICAL `[[1,1,0,0]×3]`; A `owns(5,5),(5,6)=(1,0)` (figure LEFT), B `=(0,1)` (figure RIGHT) — the **identical local edge FLIPS ownership** with the global figure; each side's `owns_figure` → its enclosed proto (A→root 39, B→root 42) |
| **FIGURE-GROUND on a closed figure** | **PASS** | exactly **1** `ProtoObject` (root 40, members **24**, gestalt 0); **all 16 perimeter cells own** it; **0 interior cells own**; surround `bg=1`, unowned |
| **RECURRENCE / global consistency** | **PASS** | **13 sweeps**; **K=1** distinct owned proto around the whole plus-shaped contour (globally consistent despite concavities); flood grows monotone `44→80→104→129`; truncated feedforward passes mint **0** protos → the fixpoint is **LOAD-BEARING** |
| **GESTALT SIZE (load-bearing)** | **PASS** | left-smaller → figure=LEFT (root 0, members 48); SWAP right-smaller → figure=RIGHT (root 8, members 48) — **the figure TRACKS SIZE across the swap**, not position |
| **FLOOR — open contour** | **PASS** | open bar (≥3 components, not a bipartition) → **0 protos, owns nothing** |
| **FLOOR — ambiguous** | **PASS** | symmetric 72/72 split → **HELD OPEN (0 protos)** — the size tie is refused, not confabulated |
| **FLOOR — iid noise (n=100, seeds 36000–36099)** | **PASS** | **0/100** fields mint a proto |
| **§9 OFF-DAY** | **PASS** | flag OFF (default) → 0 protos, `max_bg=0.0`, `max_owns=0.0`; seed not boot-loaded |
| GESTALT CONVEXITY (exploratory) | reported | equal-size ambiguity **held open**; convexity-as-tiebreaker **NOT wired** — named FRONTIER |
| SCALING (reported, not gated) | reported | fitted exponent **1.453** over N∈{144…784} (0.002s→0.023s); a reachability flood is O(N·diameter), diameter ~√N ⇒ ~1.5 is honest — **NOT the O(N²) drive's ~2** |

**8 / 8 confirmatory arms PASS. Every pre-registered prediction held.**

## HEADLINE — the Zhou signature reproduces

For a **byte-identical** local edge (the 3×4 window rows 4–6 cols 4–7 = `[[1,1,0,0],
[1,1,0,0],[1,1,0,0]]` in BOTH configs, verified in the runner), ownership is OPPOSITE:
in config A the val-1 side is a bounded interior bar → the left cell (5,5) owns; in
config B the val-0 side is the bounded interior block → the right cell (5,6) owns. **The
same local edge owns opposite sides because the GLOBAL enclosure differs** — this is
border-OWNERSHIP (contextual), not edge-detection (local), exactly Zhou/Friedman/von der
Heydt 2000. The context-dependence FALLS OUT of the mechanism: figure/ground is a
property of a region's REACHABILITY from the frame (the `bo_bgflood` fixpoint), a global
computation, so the identical local edge MUST flip when the global enclosure flips. It
was not fitted.

## RECURRENCE is where the substrate is ahead (grounding doc #4)

The plus-shaped enclosed figure resolves only at the `run_rules` FIXPOINT (13 sweeps): a
truncated feedforward pass has an incomplete flood (`bg_set` 44 at 2 sweeps → 80 → 104 →
129 at the fixpoint) and mints **no** ProtoObject; ownership completes and becomes
globally consistent (K=1 proto owned around the entire concave contour) only when the
flood settles. **A single feedforward sweep cannot produce correct figure-ground here —
the recurrence is load-bearing (§13.2), not decorative.** This is the Craft/Niebur/von
der Heydt grouping⇄ownership loop realised as the substrate's native fixpoint.

## What I got WRONG (fixed BEFORE believing, §1)

**The first closure test passed VACUOUSLY on iid noise → 95 false protos per field.** The
initial `single_ground` guard (`Not Exists` two ground-border cells with different
`glabel`) was true VACUOUSLY when a figure had ZERO ground-border cells — and in iid
noise the reachability flood barely propagates, so almost every interior cell is `bg=0`
("enclosed") and surrounded by OTHER enclosed singletons, giving an empty ground-border
set → mint. The fix is the correct objecthood constraint, **caught by reading the noise
count (a field), not a single gate (§1):** a proto is a HOLE IN ONE SURFACE, so the
figure must be **SURROUNDED ENTIRELY BY GROUND** (`bo_mint_enclosed`'s
`_SURROUNDED_BY_GROUND`: no figure cell borders a different *enclosed* component) AND that
ground is one component. This refuses speckle with **NO size threshold** — the closure
constraint FALLS OUT of "enclosed by one ground" (§13). After the fix: noise 0/100, real
figures unaffected.

## Magic numbers (§13) — none

- **No size / count threshold for minting.** A proto-object is admitted by CLOSURE
  (surrounded by one ground), which falls out of "a hole in one surface", not by a tuned
  minimum size. A single-cell figure fully surrounded by one ground WOULD be a proto
  (correctly — border-ownership fires for small figures); it is the *absence* of a single
  surrounding ground that excludes noise, not a size cut.
- **`Count(components)==2`** in the Gestalt rule is the DEFINITION of a single contour
  splitting the field into figure+ground (a bipartition), not a tuned number — an
  open/partial contour makes ≥3 components and the rule never fires (verified: the open
  floor).
- **Size tie → held open** is a pure equality refusal (`Exists` the other root with equal
  size), not a threshold.
- Surroundedness is discrete reachability; ownership is a relation; every coordinate
  in-frame is integer (the frame/continuum invariant). No continuous quantity is read.

## §9 — committed results preserved

`seeds/vision_border_ownership.json` ships `BorderOwnParams.bown = 0.0` (INERT) and is
NOT in any boot set (verified: a bare `boot_core()` has 0 `BorderOwnParams` nodes). With
the flag OFF: 0 protos, no `bg`/`owns` written. The sd orbit law `{2:1,3:2,4:2,6:2,12:4}`
is unmoved (no seed touches the sd loop; its gate passes in the battery below).

**`SIBLING_GATES` (measured, engine `7d5f50c18673`): the full battery — colour-identity ·
colour · stream · illusion · blink · vision-ground · time · depth · stereo · dim ·
gen_infer · provenance · sdloop · cycle-detect + the new border-ownership gate — is
`126 passed, 0 failed` (573.5s; sdloop/cycle-detect are the slow ones). The new gate is
9/9. No committed result moves.**

## BOUNDS (§8) — stated, not overclaimed

- This is the **PROTO-OBJECT / figure-ground / border-ownership** stage — **PRE-IDENTITY**.
  A `ProtoObject` carries `{root, members, gestalt}` and NOTHING else: **no category, no
  recognition.** It is the NEAR side of the objecthood "what" wall.
- **In-frame integer coords; ownership is a RELATION (`owns_figure` edge); surroundedness
  is discrete reachability (a same-value flood).** No continuous coordinate lives in a
  frame (the frame/continuum invariant).
- Component membership (`glabel`) is a same-value connected-component labelling computed
  IN-GRAPH by `bo_label`, not supplied by the adapter — the adapter supplies only
  `val`/`frame`/`cid` and `neighbour` edges (mechanical geometry, like `vision_ground`).
- **CONVEXITY as a confirmed figure cue is NOT delivered** — it is reported exploratory
  and NAMED as a frontier (an equal-size ambiguity is held open; convexity-as-tiebreaker
  needs diagonal-corner logic this rung did not build). Reported honestly (§7), not
  claimed.
- **NAMED FRONTIER, NOT this rung:** object IDENTITY / recognition (the "what" wall); the
  identity-untangling-via-generator-discovery crossing (grounding #1); convexity as a
  cue; multi-illuminant surface colour / constancy; V2 texture-statistic quantization and
  V4 curvature-part coding (separate mid-level rungs); amodal completion beyond
  figure-ground (the ILLUSION rung did amodal contour completion; this rung's CORE is
  figure-ground OWNERSHIP — no scope-creep into recognition).

**The result:** an identical local edge flips ownership with the global figure (Zhou); a
closed contour mints exactly one owned proto-object; the `run_rules` fixpoint makes
ownership globally consistent (load-bearing recurrence); the smaller region of an
ambiguous bipartition is figure (load-bearing size); and open / noise / symmetric
displays own nothing — O(N·diameter), NO new Rust, zero magic numbers. Border-ownership
is contextual, and the proto-object is the near side of the objecthood wall.
