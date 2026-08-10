# DOES THE SUBSTRATE SEE PHI? — PRE-REGISTRATION

**Committed BEFORE any phi number.** Branch `worktree-agent-af6f51636362ac138`
(reporting the name I actually see; no `gamma-substrate/phi` name was created).
Engine **`68860d0b0f78`**, provenance gate run as its **own step before this
file was written**: `tests/test_engine_provenance_migrated.py` **7 passed**.
**No Rust change is planned in this rung** — `scripts/engine_build.sh` was run
so the worktree holds its own build rather than shadow-importing the canonical
one (§10.1).

Seed block **86000–86999**. Four other rungs run concurrently on other blocks.

---

## 0 — THE CLAIM UNDER TEST

**Motion is not the INPUT; it is the PREFERRED INFERENCE over change.** Given a
thing at A at t1 and a thing at B at t2, the human system resolves the
correspondence toward *"one thing moved"* rather than *"one vanished, another
appeared"*, and this is cognitively impenetrable. That prior **is object
permanence** expressed temporally.

The operational cut, and it is the whole rung: **`matched` versus
`births` + `deaths`.**

## 0.1 — WHAT I FOUND BEFORE REGISTERING, RECORDED BECAUSE IT CHANGED THE DESIGN

An audit of the tree for *any* cross-time correspondence mechanism (not merely
the motion sensor) found **three**, at three different apertures. **The rung
therefore tests three levels, not one**, because "does THE SUBSTRATE see phi"
is a different question from "does the motion sensor see phi", and the motion
rung consumed only the first:

| level | mechanism | aperture | where the aperture comes from |
|---|---|---|---|
| **L1** | `motion_group_world.vector_field` — SAD block match | `radius = block = 4 px` | falls out of block overlap; `BLOCK` itself is a declared §13 residual |
| **L2** | `Substrate::segment_and_track` (`substrate.rs:2329`) | `span + 2.0`, **L1/Manhattan** | `span` falls out of the object's own extent; **the `+ 2.0` is PUT IN** |
| **L3** | `Substrate::track_identity` (`py.rs:3113`) | **`radius`, a caller argument** | **supplied — nothing derives it** |

L3 is a fully-built, unit-tested, **orphaned** primitive: zero callers in
`seeds/`, `domains/` or `tests/` as a Term. Its Rust unit test
(`term.rs:9747`) is already literally a phi stimulus.

**This is registered as a §13 observation in advance, not discovered after a
number:** a correspondence range that is a caller argument is a magic number,
and *"the substrate does phi if you tell it how far to look"* is not the
substrate doing phi. **Which level answers, and whether its aperture FELL OUT,
is part of the verdict — not a footnote to it.**

`TimeInfer` (unbounded offset, `seeds/time_axis.json`, off by default) is
**excluded in advance and the reason is recorded**: `VISION_TIME_RESULTS.md`
establishes that translation is group-closed, so on TWO frames "is this pair
explainable by a translation" is **vacuously yes for any pair**. A vacuous yes
is exactly the failure mode this thread has produced three times. It is not run.

---

## 1 — THE STIMULUS

72×72 greyscale, `BLOCK = 4`, an 18×18 motion lattice — **the motion rung's own
configuration, inherited unchanged** so the C1 re-reading is like-for-like.

A **dot** of side `BLOCK` px (one lattice cell — the smallest thing the sensor
can represent; inherited from `BLOCK`, not a new constant) at row 36.
Frame 1: dot at column 16. Frame 2: dot at column `16 + S`.

Two background arms, both run:
- **UNIFORM** — a constant field. Clean: a textureless block SADs to a tie at
  every offset, and the tie-break returns `(0,0)`, so any non-zero vector is
  attributable to the dot.
- **TEXTURED** — iid background (seed **86000**). Realistic and harder: the
  background is matchable, so background blocks report the background's true
  motion and the dot's cell must compete.

**ISI** is implemented the only way a frame-sequential system admits it: `k`
intervening frames of **background alone** (the dot is present in neither).
`k = 0` means frames 1 and 2 are consecutive.

---

## 2 — MEASUREMENTS AND STATISTICS, EXACTLY

### M1 — WHAT THE SENSOR REPORTS (raw, reported first)

For `S = 8`, `k = 0`, both backgrounds: the **raw** field —
count of non-zero cells, the vector at the source cell, the vector at the
target cell, and every distinct non-zero vector with its multiplicity.
Reported as output, not as interpretation.

**Verdict, pre-registered, exact — no threshold, no partial credit:**
- **PHI** ⟺ `v[source cell] == (0, S)` exactly.
- **TWO EVENTS** ⟺ `v[source cell] == (0, 0)`.
- **OTHER** ⟹ report the raw vector and classify nothing.

### M2 — SEPARATION DEPENDENCE

`S ∈ {1, 2, …, 20}` px, `k = 0`, both backgrounds, all three levels.
Statistic: the M1 verdict at each `S`; for L2/L3 the `matched` / `births` +
`deaths` verdict. Reported as a curve.

### M3 — ISI DEPENDENCE (the classic parameter; the discriminating measurement)

`k ∈ {0, 1, 2, 3, 4}` at `S ∈ {2, 4, 8}`, both backgrounds, all three levels.

**Response is defined over the whole sequence**, so a system that bridged the
gap would be credited: `R(S, k) = 1` iff **any** consecutive pair in the
sequence yields a correspondence linking the source location to the target
location. Otherwise `0`.

**This definition is deliberately generous to the substrate** and is fixed
here, before any run.

### M4 — THE OTHER TWO MECHANISMS

- **L3** `track_identity(prev, cur, "feat", "identity", radius)` on two
  `Entity` nodes at the two dot centroids, `radius ∈ {1, 2, 4, 8, 16, 32, 64}`
  × `S ∈ {2, 4, 8, 16}`. Statistic: the `radius` at which the verdict flips
  from `births + deaths` to `matched`, per `S`.
- **L2** `segment(...)` on the real 72×72 pixel frames, quantized, `S` swept as
  in M2. Statistic: the largest `S` at which the prior Region **survives** with
  non-zero `drow`/`dcol` (correspondence) rather than being removed and a fresh
  Region minted (two events).

### M5 — CONTROLS

| id | stimulus | required |
|---|---|---|
| **C-POS** | dot, `S = 4` (one block), `k = 0`, TEXTURED | **`v[source] == (0,4)`. If not, the instrument is DEAD and the RUN IS VOID.** |
| **C-NULL** | frame 1 ≡ frame 2 | field identically zero |
| **C-RIGID** | the **same total** displacement `S` delivered as CONTINUOUS motion — the dot at intermediate positions in intermediate frames, per-frame step ≤ `BLOCK` | the sensor must track it at every `S` |
| **NOISE** | dot at an independent random position in each frame (seed **86200**) | reported raw |

**C-RIGID is the interpretive control and the reason a null here is
diagnosable.** If the sensor tracks the same total displacement when it is
delivered continuously but fails when it is delivered as a jump, **the failure
is specifically about correspondence across a gap and not about general
blindness.** Human vision sees both as motion. Without this arm a null is
uninterpretable.

**C-POS is the dead-instrument arm and it must ACTUALLY FIRE, not merely be
capable of firing** — the run raises `SystemExit` on it.

### M6 — THE C1 RE-READING, QUANTIFIED

`n = 40` consecutive C1 pairs (**the motion rung's own n and corpus**, pin
`08630d4b`), C2 (`119eca43`) as the contrast. Per pair, per lattice cell:

- share of frame pairs that are **literally pixel-identical**;
- the four-way cell classification, split at **exactly zero** (a constant-free
  split, §13), where `Δ = max |a − b|` over the block's own pixels:

| | `v == 0` | `v ≠ 0` |
|---|---|---|
| **`Δ == 0`** | still — correctly zero | spurious |
| **`Δ > 0`** | **CHANGE WITHOUT MOTION** ← the candidate phi-blind population | motion reported — the 0.8% |

- of the **change-without-motion** cells: the share that acquire a non-zero
  vector when the block match is re-run at `radius ∈ {4, 8, 16, 32}`.

**This radius enlargement is a DIAGNOSTIC OF THE APERTURE, registered in
advance as the instrument for M6, and it licenses NOTHING** — no motion-grouping
arm may be re-run at a wider radius on the strength of it (§3.6, §5). It answers
one question only: *is the discarded change a correspondence the aperture could
not reach, or is it non-correspondent?*

---

## 3 — n, AND WHY IT IS NOT A POWER ANALYSIS

M1–M5 are **deterministic**: the block matcher, `segment_and_track` and
`track_identity` are exact functions of their input. There is no sampling
distribution, so a CI would be a decoration. Every synthetic arm is run once
per cell of its grid and the **exact** verdict is reported.

**This is stated in advance precisely so it cannot be used as a rescue.**
Where a number IS a sample — M6, over 40 real frame pairs per corpus — the mean
is reported with a **95% CI**, and `n = 40` is the motion rung's own registered
n, inherited so the re-reading is like-for-like rather than re-powered to taste.

---

## 4 — PREDICTIONS, STATED IN ADVANCE, WITH PROVISOS

**P1 (L1, separation).** The sensor reports the true displacement for
`S ≤ 4` and `(0,0)` for `S > 4`. **The cutoff is the aperture exactly**, because
beyond its own extent a block shares no pixels with its source and SAD has
nothing to minimise against.

**P2 (L1, the shape of the dependence).** There IS therefore a non-zero motion
response, but its separation dependence is a **hard geometric cutoff at the
aperture** — not the graded, wide-range function of human beta movement. *A
response with the wrong parameter dependence is a different mechanism wearing
phi's clothes*, and I expect this to be the finding at L1.

**P3 (ISI — the strongest prediction, and the one I most expect to be right).**
`k ≥ 1` gives **zero** response at **every** separation and **every** level,
because each consecutive pair then contains at most one dot and there is
nothing to correspond. **Human phi REQUIRES an ISI** — Wertheimer's optimum is
an interior one, at a real temporal gap; `k = 0` is simultaneity, which humans
see *worst*. So the predicted substrate curve is **maximal at `k = 0` and
monotonically dead thereafter: the human curve inverted, not merely different.**

**P4 (L3).** `track_identity` flips to `matched` at exactly `radius ≥ S` —
i.e. it has no intrinsic aperture and returns whatever was asked for. **This
would be a §13 negative, not a phi positive.**

**P5 (L2).** `segment_and_track` corresponds up to Manhattan `span + 2 = 6` px
for a 4 px dot — wider than L1 and **scaling with object size**, which is the
most nearly-emergent aperture in the tree. I expect it to fail beyond that.

**P6 (M6, the C1 re-reading).** I predict the 0.8% is **partly, but NOT
wholly**, the sensor. Specifically: (a) a substantial share of C1 pairs are
literally identical — that share is genuine stillness and the "de-facto stills"
reading is correct for it; but (b) among cells that DO change, I predict
**change-without-motion outnumbers motion-reported**, i.e. the sensor discards
more change than it converts. I do **not** predict that widening the radius
rescues most of it, because a cartoon animated on twos changes by *redraw*
(appearance/disappearance of drawn regions) rather than by translation, and a
redraw has no correspondence to find at any radius.

**Proviso that could break P1/P2:** with a TEXTURED background the dot's cell
may report a **spurious** non-zero vector — the background under the dot is
matchable and SAD may prefer some background offset. That would be neither PHI
nor TWO EVENTS but the OTHER bucket, and it is why M1 reports the raw field and
why the uniform arm exists alongside the textured one.

**Proviso that could break P3:** if a level integrated over more than two
frames it could bridge a blank. None of L1/L2/L3 does — L1 is a two-frame
operator by construction; L2/L3 compare "previous" to "current" only — so if
`k ≥ 1` produced a response I would suspect an instrument fault before a
discovery, and would say so.

---

## 5 — DECISION RULE, INCLUDING WHAT EACH NULL MEANS

**All four outcomes are publishable and are named here so none can be
back-fitted.**

1. **THE SUBSTRATE SEES PHI.** Some level corresponds across a gap it could not
   pixel-match, **AND** shows the human ISI dependence (an interior optimum),
   **AND** its aperture fell out rather than being supplied. Motion would then
   already be inferential in this tree.
2. **IT DOES NOT.** Correspondence is bounded by a pixel aperture at every
   level and dies at `k ≥ 1`. Then **the motion layer is at the wrong level of
   description**, and everything built on it consumes the wrong quantity.
3. **A MOTION RESPONSE WITH THE WRONG PARAMETER DEPENDENCE.** Non-zero, but
   cut off geometrically and destroyed rather than helped by ISI. *A different
   mechanism wearing phi's clothes.* **This is what I expect (P2 + P3).**
4. **CORRESPONDENCE-IF-TOLD** (the L3 case). A mechanism that matches at
   whatever radius it is handed. **Registered in advance as a §13 NEGATIVE, not
   a positive** — the aperture is the claim, and a supplied aperture makes none.

### What a null implies for the motion-grouping rung — registered now

If outcome 2 or 3 obtains, then `VISION_MOTION_OBJECTS_RESULTS.md` grouped
vectors from a sensor answering *"what pixels moved less than 4 px"*, not
*"what moved"*. **Grouping a bad signal well is indistinguishable from grouping
a good signal badly**, so its FLOOR-B failure (0.187 vs 0.803) would become
**uninterpretable as a verdict on the grouping RULE** — it cannot be attributed
to the criterion until the sensor is re-founded. **That is a scope reduction on
a committed result, not a rescue of it**, and it is written here before the
measurement so it cannot be produced afterwards to taste.

**It does NOT retract that rung's positives**: cohesion (within 0.404 vs
between 3.950) and the tolerance's 3.8× fragmentation cut are statements about
whatever the vectors are, and hold regardless of what they mean.

### What CANNOT be concluded

- Nothing about biological mechanism. Human phi data enters as the **parameter
  dependence to compare against**, never as something measured here.
- The ~11% per-block sensor error (`VISION_MOTION_OBJECTS_RESULTS.md` §0.2) is
  **inherited, not re-derived**, and bounds every claim; no claim here may
  exceed it.
- A null licenses **no** tuning of `BLOCK`, `radius` or any threshold (§3.6).
  A further attempt needs a new pre-registration with a new mechanism-level
  hypothesis.
- M6's radius diagnostic is an instrument, not an arm.

---

## 6 — §13: WHERE THE NUMBERS COME FROM

**No threshold is introduced by this rung.** Every verdict is **exact
equality** — `v == (0,S)`, `v == (0,0)`, `matched` vs `births`, `Δ == 0` — which
is the McCollough-gate shape: unambiguous discrimination, no metric to argue
about.

Declared residuals, inherited and named rather than hidden: `BLOCK = 4`
(the motion rung's own declared residual), `GRID = 72`, `K_LUM = 16`. The dot
side is `BLOCK`. The swept ranges (`S`, `k`, `radius`) are **independent
variables**, not constants.

**The §13 finding this rung expects to make is about L2's `+ 2.0` and L3's
`radius`** — see §0.1. Both are aperture constants that were put IN, and the
rung's headline may well be that **the substrate's correspondence range is a
supplied number rather than one that falls out.**

---

## 7 — SEEDS

Declared **86000–86999**. Explicit literal draws so every sink is statically
resolvable (a `--check` that passes with UNKNOWN sinks has verified nothing):

| seed | use |
|---|---|
| 86000 | textured background, phi stimuli |
| 86100 | textured background, C-RIGID |
| 86200 | NOISE control dot positions |

Measured with `scripts/seed_audit.py` on the runner and reported in the
results, not asserted.
