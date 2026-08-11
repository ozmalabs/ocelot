# PRE-REGISTRATION — does ownership respect CONTAINMENT, and what does it cost?

Written and **committed before any confirmatory number**. Seeds **92000–92999**.
Branch `worktree-agent-ac7efef13e76a8f7c`, base `ee0a1af25ef5dea0e9bc8919f85ebe7e8e19f463`.
Engine **`a1d350bbd23b`** (built in-tree by `scripts/engine_build.sh`; **no Rust
change in this rung** — the change is seed data).
Protocol §3.

**Seed claim (§ ledger), run before writing this file:**

```
SEED CLAIM 92000-92999: CLEAN -- no collision DETECTED.
  Scope: 798 files with seed sinks; 482 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0 — WHAT IS BEING FIXED

`VISION_SURFACE_ASSIGNMENT_RESULTS.md` (seeds 87000–87999) measured the mechanism on
the **settled graph**, not by inference:

> A **featureless** surface is SWALLOWED BY THE GROUND (60% of R marked `bg` by the
> equal-value flood). A **featured** surface SHATTERS INTO ITS CONTENT (82–92 enclosed
> components inside R), and `G_own_lost`'s `perim(R) < perim(Q)` awards figure to the
> **SMALLER** perimeter — **so the surface LOSES TO ITS OWN CONTENT BY CONSTRUCTION.
> THE PREDICATE DOES NOT MERELY LACK CONTAINMENT; IT INVERTS IT.**

This composes with the value-flood rung's verdict that the incumbent gate *"encodes
ISOLATION, NOT OBJECTHOOD, and was validated only on stimuli where those two
coincide"*.

**The claim under test: a component that ENCLOSES another should not lose figure status
to the thing it encloses.**

---

## 1 — THE DERIVATION (§13: what falls out, and from what)

### 1.1 The defect is a SCOPE error in the quantifier, not a missing parameter

`bo_mint_owned`'s conjunct `G_own_lost` refuses `R` if **there exists any** member cell
`f ∈ R` with an abutting enclosed cell `n ∉ R` such that `Not(R.rim < n.rim)` — i.e. R
fails to strictly win **any** border competition it is in.

Zhou/Friedman/von der Heydt 2000 — the basis this seed already cites and whose |B|
cancellation v1.2.0 re-derived — measure border ownership **of an EDGE, with a SIDE**.
It is not a property of a region. A region is a figure when it **owns its own OUTER
CONTOUR**: the border between it and what SURROUNDS it.

`G_own_lost` quantifies over **all** of R's borders. Where a rival `Q` is entirely
surrounded by `R`, the border between them is **not part of R's outer contour at all** —
it is the contour of R's own **hole**. Ownership going to Q there is the *correct*
reading, and it is the standard nested figure-ground case: **a figure is ground for a
smaller figure on it.** It says nothing about whether R owns its border with its
surround.

**So the fix is to restrict the competition to the borders that R's figurehood is
actually about.** Nothing is tuned; a quantifier's range is corrected.

### 1.2 The same statement in v1.2.0's own terms — and it composes rather than fights

v1.2.0 found the |B| cancellation is a **TWO-PARTY** statement, failing where one cell
is claimed in full by two competitions (fractions sum past one ⇒ `|B|` does not cancel).

Containment is the **other** degeneracy of the same cancellation. If `Q ⊂ R`, the shared
border **is the whole of Q's perimeter**: `|B| = perim(Q)`, so

```
|B| / perim(Q) = 1     identically, for every R whatsoever.
```

The fraction is pinned at its maximum **by the geometry**, not decided by the
competition. Q wins against every possible enclosing R, unconditionally — exactly the
degeneracy v1.2.0 identified at `rim = 1` ("a singleton wins every competition it enters,
unconditionally"), arriving one level up. `perim(R) < perim(Q)` is not reading a
competition here; it is reading a tautology.

**Where the two differ, and why the RESOLUTION differs — this is the point at which
tuning would hide, so it is stated explicitly.** v1.2.0 HELD OPEN because there was no
fact of the matter to read. Here there **is** a fact of the matter and Zhou supplies it:
the border of a hole belongs to the hole, R is ground *there*, and R's figurehood is
decided elsewhere — on its outer contour. So the contained rival is **removed from the
competition**, not held open. A hold-open here would be the third possible treatment and
would be chosen for its output, not derived; it is refused.

### 1.3 One definition of "rival", used by both conjuncts

The v1.2.0 well-posedness conjunct counts a competition ill-posed when a member cell
faces **two distinct enclosed rivals**. If a contained component is not a rival at all
(§1.1), it cannot make a competition ill-posed either. **The two conjuncts must range
over the same rival set or they disagree about what a rival is.** This is a consistency
requirement of the correction, not a second choice.

It is also load-bearing for the new arm: a screen's 82–92 contained components mean
almost every member cell of an enclosing region faces two of them, so under v1.2.0 the
enclosing region is held open regardless. Scoping only `G_own_lost` would have produced
a decorative change (§1 fifth clause / FM-0).

### 1.4 The conjunct, exactly

A rival `X` (an abutting enclosed cell of a different component) enters the competition
only if:

```
Exists q ∈ {Cell : q.glabel == X.glabel ∧ q.bg < 0.5}      (a member of X)
  Exists p ∈ Neighbours(q) : p.glabel ≠ X.glabel ∧ p.glabel ≠ R.glabel
```

— *"X has a neighbour that is neither X nor R"*, i.e. **X is not a hole in R**.

This is **structurally the third instance of a test the seed already contains**: the
single-ground-closure conjunct (*"the figure is a hole in ONE surface"*, `G_gnd2`)
present in all four mint rules, and v1.2.0's generalisation of it to the rival side.
Here it is applied to the rival's own surround.

**§13 compliance:** a positive `Exists` over the graph's own adjacency. **No `Count`.
No size. No magnitude literal.** Its only literals are the `0.5` discriminators over the
0/1 `bg` flag — the existing kind. It never mentions how big anything is: it excludes a
1-cell hole and a 200-cell hole identically, and it does **not** exclude a large abutting
neighbour that merely touches R.

Armed by a new `BorderOwnParams.bown_nest`, **default 0.0**, written as
`Or(bown_nest < 0.5, <rival-is-not-contained>)` inside each of the two rival predicates,
so v1.2.0 reproduces **byte-identically** (§9). Seed → **v1.3.0**.

---

## 2 — ARMS

| arm | `bown` | `bown_own` | `bown_wp` | `bown_nest` |
|---|---|---|---|---|
| **incumbent** (`bo_mint_enclosed`) | 1 | 0 | 0 | 0 |
| **replacement** (v1.1.0) | 1 | 1 | 0 | 0 |
| **wellposed** (v1.2.0, the standing arm) | 1 | 1 | 1 | 0 |
| **nested** (this rung) | 1 | 1 | 1 | 1 |

All four run through the substrate. A read-out calibrated to one predicate cannot score
another (the predecessors established this), so the read-out replicates the fourth
predicate explicitly and is reconciled against the rules' own minted output
(`G_pass == n_protos`) **separately under each arm**.

---

## 3 — MEASUREMENTS, STATISTICS, n FIXED IN ADVANCE

**M-E — VACUITY GATE, RUNS FIRST (§1 fifth clause / FM-0).** `max|nest=1 − nest=0|` on
proto count over 20 fields drawn at RNG **92800**, on material where containment is
expected (real-frame tiles, not iid speckle — speckle has few holes-in-holes and is the
wrong material for this gate; this is stated in advance, not chosen after). **If
`D == 0` exactly the conjunct is decorative — STOP, claim nothing, burn no further
seed.**

**M-A — THE REGISTERED SPECKLE CONTROL, re-earned.** 100 iid uniform fields, 18×18,
k=16, RNG **92900** (fresh; 89900 is not reused for the confirmatory number). Statistic:
**number of fields minting ≥1 proto**, and `max_false_proto_size`. All four arms on the
**same** fields. **Decision rule: the control PASSES for the `nested` arm iff it is
0/100.** Anything above 0 is a failure and is reported as one. n=100 fixed, not revisited.

**M-B — THE SYNTHETIC GATE, all arms.** `tests/test_border_ownership_migrated.py` (9) +
`..._owned_migrated.py` (9) + `..._wellposed_migrated.py` (9) + the same 9 re-run with
`bown_nest` armed. **Decision rule: 9/9 in the nested arm, or the correction has bought
its effect with false negatives and the trade is reported rather than a side picked.**

**M-B2 — THE GENUINE SINGLE-CELL FIGURE STILL MINTS**, all four arms (the predecessor's
hardest constraint: remove the false positive without buying a false negative). Plus the
noise singleton still refused. Both asserted, both directions.

**M-C — REAL-FRAME YIELD AND COST, AT G72.** Configuration **G72** (one 72×72 decode,
4×4 grid of 18×18 tiles), corpora **C1** `08630d4b…` / **C2** `119eca43…`, pinned and
asserted at run time, k=16, the predecessors' own 7 sampled frames. Statistics: **mean
protos/frame**, **mean MULTI-cell protos/frame**, reported against **BOTH** published
baselines — incumbent C1 3.3 / C2 10.7 and wellposed C1 7.1 / C2 14.4. Deterministic
decode; no seed drawn. **No direction is claimed as an improvement from M-C; it is a
cost statement.**

**M-F — THE SIZE DISTRIBUTION (the brief's actual target).** Every count in this arc has
come out as FRAGMENTS (median proto size 2 cells on a 324-cell field, identical to the
incumbent's median). Over the same M-C runs, per arm: **median / mean / p90 / max proto
size in cells**, and the **full size histogram**. **If containment moves the size
distribution that is the headline, not the count.** Statistic fixed here: **median proto
size**, with the histogram reported whole (no selective bins).

**M-G — THE NEW ARM: the screen/mirror composite.** `scripts/surface_assignment_measure.py`
stimuli **reused verbatim** so the comparison is exact — same tile ordinal 5, same sides
(8, 14), same content arms, same `start_s=900`, RNG ordinals in **92000+** (the 87000
block is burned). n = **100 frames per cell**, fixed here, matching the predecessor.
Primary statistic: the predecessor's own **`n_surface` / `n_surface_exact` / verdict
counts**, and **`n_inside`** as the paired difference against `plain` on the same
rectangle in the same frame.
**Decision rule: `n_surface > 0` in the nested arm is the positive outcome; `n_surface
== 0` is a null and is reported as one.**

**HONEST BOUND DECLARED BEFORE THE RUN, inherited from the predecessor and RESTATED
BECAUSE IT LIMITS THIS RUNG'S BEST CASE:** there is **no `Surface` type**, no calibration
attribute and no containment edge in `seeds/`, and `ProtoObject` has four attributes. A
featured screen **is not a single component** — it shatters, so there is no component
that *is* the surface for a proto to be minted from. **`n_surface = 0` therefore is NOT
evidence of failed identification, and this rung is not asked to identify a surface —
only to stop an enclosing region losing to its contents.** The measurable consequence
inside R is a change in the **size** of what mints there, not a SURFACE verdict.

**M-D — §13 / AST.** A term-tree AST walk (never a substring selector) over the new
conjunct: **zero `Count` nodes**; every `Lit` in a comparison is against a 0/1 flag
(`bown`, `bown_own`, `bown_wp`, `bown_nest`, `bg`, `frame`, `owns`); **no** literal
compared against `val`, `rim`, `glabel`, `cid`, `members`, `root`; every `glabel`
comparison is `Attr` vs `Attr`. Selector locates the conjunct **BY SHAPE**, never by
substring (§12 — four substring-selector failures are recorded in this arc).

**M-D2 — POSITIVE CONTROL BY INJECTION, and the injection must be verified to LAND.**
Plant a `Count`-bounded size test **into the SELECTED subtree**; confirm the AST gate
goes RED; revert; confirm GREEN. **The supervisor's own first injection at the previous
rung landed on a different `Not>Exists>Exists` in the same rule and PASSED — the gate was
right and the control was wrong.** So the injection is asserted to land: the harness
prints the path it mutated and re-reads it, and a *no-op* injection is itself a failure.

**Dead-instrument controls, which must ACTUALLY FIRE:** D1 (committed 12×12 figure
reproduces, all four arms), D2b (uniform field, frame stripped — the vacuous-mint trap).
Reused verbatim. The run aborts if D1 does not reproduce or D2b does not fire.

**PROVENANCE (§10, and the defect found at 87000):** `provenance_line()` is printed from
**inside every measuring process** into the results artifact, and the run aborts on
divergence. The migrated provenance gate is run as **its own step first** — it certifies
the tree's config under its own preamble, **not the process you measure in**.

**RE-EARN EVERY FLOOR ACROSS THE CONFIGURATION CHANGE.** The engine is newly built in
this tree. The oracle (`bash scripts/rung7_vision_bench.sh`) and all three predecessor
synthetic gates are run **in this tree, on this engine, before any arm number** — none
is inherited.

---

## 4 — PREDICTION, STATED IN ADVANCE (§3.7)

1. **M-E: D > 0.** Real-frame tiles at G72 average ~45 components per 324-cell tile, so
   holes-in-holes should be common. *Proviso that would break it:* if the equal-value
   flood makes nesting rare at k=16 (components are 2 cells at the median), the conjunct
   could be near-vacuous. That is a real possibility and D==0 stops the rung.
2. **M-A: 0/100 in the nested arm.** The correction only ever REMOVES rivals, which can
   only make `G_own_lost` easier to pass — so this is the direction of risk and I flag it
   as such. My reason for expecting 0 anyway: the v1.2.0 conjunct is what refuses speckle
   singletons, a 1-cell R can contain nothing, and its rivals therefore are not excluded.
   **But a LARGER speckle component that now passes `G_own_lost` and whose ill-posedness
   was carried by a contained rival could survive. If M-A is above 0 the rung has bought
   its effect with the registered negative control and I will report that as a failure,
   not reinterpret it.**
3. **M-B: 9/9**, all four arms. The synthetic stimuli are figure-on-blank, so no rival is
   contained and the conjunct is vacuously satisfied. **M-B2 mints.**
4. **M-C: the nested arm rises ABOVE the wellposed arm** (7.1 / 14.4), because
   components that were refused for losing to a hole now pass. **I do not predict which
   side of the incumbent's 3.3 / 10.7 it lands on.** A rise in count is a COST here, not
   a win — see 5.
5. **M-F: median proto size RISES above 2.** This is the prediction the rung is really
   making, and it is the one I am least sure of. **The proto that appears is the
   ENCLOSING one, which is by construction larger than the contents it was losing to.**
   *Proviso that would break it:* if enclosing components at k=16 are themselves 2–3
   cells (a thin ring around a 1-cell hole), the median moves by nothing and the count
   rises with no size gain — **which would be the same fragment result in new clothing
   and I will report it as that.**
6. **M-G: `n_surface` remains 0.** A featured screen is not one component; there is
   nothing for a SURFACE proto to be minted from. I predict `n_inside` **falls** (small
   content components lose their now-passing enclosers' competition… no — the correction
   never refuses anything, so `n_inside` can only stay level or rise) — **stated
   correctly: `n_inside` rises or stays level, and the composition shifts toward larger
   supports.** If `n_surface > 0` the prediction is wrong in the rung's favour and that
   is reported as a surprise, with the mechanism traced on the settled graph before it is
   claimed.

## 5 — THE OUTCOMES THIS RUNG CAN HAVE

1. **Containment is respected, the floors hold, and the size distribution moves** —
   ownership stops inverting, and "few and large" gets its first real evidence.
2. **Containment is respected and the size distribution does NOT move** — the count rises
   with the same fragments, reported as a null on the brief's actual target.
3. **A floor breaks** (M-A above 0, or M-B below 9/9, or M-B2 fails) — the correction is
   reported as a bad trade and **no side is picked**.
4. **The conjunct is decorative** (M-E `D == 0`) — stop, claim nothing.

## 6 — WHAT THIS RUNG DOES NOT TOUCH

`bo_mint_enclosed` (the incumbent path), `bo_mint_gestalt`, `bo_bgflood`, `bo_label`,
`bo_rim`, `bo_own`, the v1.2.0 well-posedness *predicate* (only the rival SET it ranges
over is scoped, under a flag), and **any Rust**. The flood is untouched, so component
structure must remain byte-identical across all four arms — checked (`n_components`
equal per row).

## 7 — WHAT IS INHERITED AND MUST BE EDITED, DISCLOSED IN ADVANCE

`tests/test_figadj_wellposed_ast_migrated.py::test_the_conjunct_is_a_NEGATED_EXISTENTIAL_not_a_bound`
asserts **exactly one** inner rival existential inside the v1.2.0 conjunct. Adding the
containment scope adds a second `Exists` there, so **that assertion must be amended** —
an inherited gate edited by the rung it constrains, which is the shape of an accident.
It is disclosed here **before** the edit, the amendment distinguishes the two
existentials **by shape** (the rival-distinctness branch is the one carrying the
rival-vs-rival `glabel` comparison), and **M-D2's injection is run against the AMENDED
test** so it is proven still able to fail.
