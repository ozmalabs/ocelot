# VISION — PAINT-FROM-SAMPLE: appearance as an order-k code painted over a region, and the residual where the paint was wrong (PRE-REGISTRATION)

*Written and COMMITTED before any measurement (PROTOCOL §3). Branch
`gamma-substrate/paint-from-sample`, worktree
`.claude/worktrees/agent-a21abdeb1c5fde2cc`. Seed block **66000–66999** (verified free
before launch; appended to the ledger below). Base `main` HEAD **a67afe4f**.*

**Engine `b31b5911dcee`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` — **shared
build, Rust source byte-identical** to canonical (`provenance_line()` reads *"shared build
from … — Rust source identical"*). **This rung adds NO Rust**, so the shared build is
legitimate (§10.1 rule 4), and a gate pinned to this rung's own commit range will assert it
(§12.3: BOTH endpoints pinned, never `HEAD`).

`data/` symlinked to canonical (§10.2). The §9 bench baseline is quoted **with its
condition** (`200 passed / 0 failed WITH data/`).

---

## 0. The proposal, stated so it can be wrong

Colour/appearance is not computed densely. Instead:

1. **SAMPLE** the appearance of a contour-bounded region;
2. **PAINT** the whole region with that sample as a cheap pass;
3. **SUBTRACT** — take the residual where the paint was wrong;
4. **ESCALATE** the order of the appearance code only where the residual demands it.

The sample is an **order-k appearance code**, not a single colour. `k=1` is the degenerate
flat fill; `k=2` is a vague pattern (a linear gradient over the region). **`k` MUST FALL
OUT of the residual (§13), never be set.**

This is the sd loop's own decode → grow → re-decode ladder applied to surface appearance,
and it is built as that, not as a parallel mechanism.

## 0.1 What this rung does NOT do (§8, stated in advance)

- **Real frames are OUT OF SCOPE.** Proto-objects produce nothing on real frames (0 protos
  on 7/7), so real-frame painting is blocked on a seam this rung is not fixing. The battery
  is **synthetic, with contours that exist in the stimulus**.
- **No claim about which biological mechanism is correct.** An illusion falling out of this
  mechanism does not license "this is how the brain does it".
- **No claim about segmentation.** The boundary criterion below is the cheapest
  threshold-free one available; if it fragments, that is reported, not fixed.
- **The ladder stops at k=2.** A periodic / texture-statistic order is NOT built. Ladder
  EXHAUSTION is therefore one of the three pre-registered outcomes, not a gap discovered
  later.

---

## 1. THE CRUX — baseline first, and an already-present illusion is UNINFORMATIVE

**An illusion the current system already produces by some other mechanism would "appear"
under paint-from-sample too, and prove nothing.** For every item in the battery, the
system's behaviour is measured **with paint absent** before paint exists. The rule, fixed
now:

> **Only an illusion that is ABSENT at baseline and PRESENT with paint is evidence. An
> illusion present at baseline is UNINFORMATIVE and is reported as such — never as
> support.**

Two items are declared **UNINFORMATIVE IN ADVANCE**, from reading the code rather than from
the data:

| item | why it is uninformative before it is measured |
|---|---|
| **Blind-spot filling (flat)** | `seeds/vision_ground.json`'s `gr_fill` **already** fills the optic disc with *"surface (mean of filled surface neighbours)"* — that IS paint-from-sample at k=1, already landed and already gated (`test_illusion_render_migrated.py`). Re-observing it proves nothing. |
| **Crowding as summary statistics** | `seeds/vision_crowding.json`'s `cr_pool` **already** replaces a peripheral target's identity with a pooled summary statistic (`pooled_ident`), already gated (`test_crowding_migrated.py`). Already present ⇒ uninformative. |

What remains informative in each of those two areas is the **strictly stronger** claim the
order-k extension makes and the flat version does **not**:

- **blind-spot filling carries TEXTURE, not just a hue** — `gr_fill`'s mean-of-neighbours is
  flat by construction, so a textured surround must produce a flat fill at baseline. A
  non-flat fill is new.

---

## 2. THE MECHANISM — every decision is a rule; nothing is chosen

Seed `seeds/vision_paint.json` (emitted by `tools/build_vision_paint.py`), adapter
`domains/paint_world.py` (mechanical I/O only, source-grep gated). **NO new Rust. NO edit
to any existing seed.** Ships `PaintParams{paint: 0.0}` — **OFF by default (§9)**.

The field is a `PaintField` hub with `PaintCell`s at integer `(prow, pcol)`, wired
4-connected by `neighbour` edges. Two channels, following this tree's own split
(*luminance is structure, colour is a sign*):

- **`plum`** — luminance. **Defines the regions.**
- **`papp`** — appearance. **Is sampled and painted.** (`plum` is painted too, so the
  brightness illusions are readable on the same machinery.)

### 2.1 The boundary — a strict local maximum of |Δ|, with NO threshold

`pt_delta`: per cell, the forward luminance difference to the east / south neighbour.

`pt_block`: the link east of cell `c` is **BLOCKED** iff its `|Δ|` is **strictly greater
than** the `|Δ|` of the link on either side of it, along the same axis. Same for south.

This is non-maximum suppression stated as an exact comparison. **There is no threshold and
no scale**, which is the point (§13): a magnitude threshold would be a number chosen against
the answer. Its consequences are entailed and are stated here in advance, including the ones
that hurt:

| stimulus | Δ profile | boundary? | consequence |
|---|---|---|---|
| uniform | all 0 | **no** (no strict max) | one region ✓ |
| linear ramp | all equal | **no** (no strict max) | one region ✓ |
| step edge in a flat field | 0,0,K,0,0 | **yes**, at the step | region splits ✓ |
| Cornsweet cusp | ramps to a peak at the cusp | **yes**, at the cusp only — the shoulders are not maxima | the ramp stays INSIDE the flat region ✓ |
| texture | maxima scattered | **yes, everywhere** | **fragments into micro-regions — the predicted failure mode, see §5.2** |

### 2.2 The region — a flood that cannot cross a blocked link

`pt_seed` / `pt_flood`: `pregion = MinOver` of `pidx` over self and every neighbour reachable
across an unblocked link, to the `run_rules` fixpoint. **The region's representative ("hub")
is the unique cell whose `pidx == pregion`** — it falls out of the flood; no node is minted
and no region id is assigned by Python.

### 2.3 The sample and the paint — one uniform rule, no stimulus special-casing

`pt_fit1` (on the hub, pooling over the field-anchored set of cells sharing its `pregion`):
the **order-1 code** is the region mean of `plum` and of `papp`.

`pt_fit2`: the **order-2 code** is the region's least-squares plane (mean + `dr` + `dc`),
computed from the region's own first and second moments about its centroid.

`pt_paint`: every cell in the region is painted with the region's code at the region's
current order `korder` → `ppaint_lum`, `ppaint_app`.

**There is exactly ONE sampling rule and it is applied to every stimulus identically. If a
stimulus needs its own rule, this rung has failed and the failure is what gets reported
(§7).**

### 2.4 The residual, and how k FALLS OUT

`pt_resid`: per cell, `presid = |observed − painted|` on each channel.

`pt_escalate`: the region's order increments iff **any** cell in it is **REFUTED**, where

> a cell is REFUTED iff `|observed − painted| >= pquant / 2`

— i.e. the paint is closer to a *different representable value* than to the observed one.

**`pquant` is the field's own alphabet step, not a tolerance.** The stimuli are integer-
valued because that is what grounding IS (CLAUDE.md's frame/continuum invariant: *in-frame is
INTEGER; non-integer math is CROSS-FRAME*). The paint is a cross-frame rendering and may be
real-valued; the comparison against an in-frame observation is therefore made at the frame's
own resolution. **Nothing is tuned.** This is gated by a **scale-invariance arm** (§4, arm
K3) in the manner of `test_b_invariance_...`: present the same stimuli with the alphabet
scaled ×4 and `pquant=4`, and every qualitative verdict must be unchanged. If a verdict
moves, `pquant` is a magic number wearing a quantum's clothes and the rung says so.

`korder` starts at 1 and is capped at 2 (the built ladder). **Three outcomes, and which one a
region reaches is decided by the residual alone:**

| outcome | reached when | meaning |
|---|---|---|
| `korder=1`, `prefuted=0` | the flat code reproduces every cell at the field's resolution | flat surface |
| `korder=2`, `prefuted=0` | the flat code was refuted; the plane is not | vague pattern (gradient) |
| `korder=2`, `prefuted=1` | **the ladder EXHAUSTED and the paint is still wrong** | the mechanism knows it is wrong |

**Nothing in the seed, the adapter or the tests sets `korder`.** A gate asserts that the
string `korder` appears in no assignment outside the seed's own rules.

---

## 3. THE GATE IS A CONJUNCTION — both arms, or nothing

A paint mechanism that fills everything indiscriminately would produce spreading illusions
AND be useless. **The rung passes only if BOTH hold:**

- **ARM I — the illusions appear** where they should, ABSENT at baseline and PRESENT with
  paint; AND
- **ARM R — the residual is LARGE on textured and gradient regions the low-order paint
  should fail on**, i.e. the mechanism knows when it is wrong.

**Either alone is worthless and is reported as a FAIL of the rung, not as a partial
success.** A uniform region with a small residual is what a working mechanism and a no-op
both produce, so the contrast arm is built deliberately and its stimuli are fixed here.

---

## 4. The arms, fixed in advance. Exactly these. No sweeps.

All battery stimuli are deterministic; the two floor arms are the only ones with n, and their
n is fixed here.

### ARM I — the illusion battery (deterministic; baseline vs paint, per item)

| id | stimulus | statistic | baseline expectation | paint = evidence iff |
|---|---|---|---|---|
| **I1 — neon spreading** | a uniform achromatic field, a contour-bounded region, chromatic inducer segments on a *sub-part* of the region's cells | `ppaint_app` at a FAR cell of the region whose observed `papp == 0` | `0.0` (nothing spreads appearance today) | `> 0` |
| **I2 — watercolour** | an enclosed region with a STRONG dark outer contour and an ADJACENT weak chromatic inner contour; interior achromatic | `ppaint_app` at the region interior; and its SIGN vs the inner contour's chroma | `0.0` | `> 0` **and** matching the INNER contour, not the outer |
| **I3 — Cornsweet / Craik-O'Brien** | two large flat regions of IDENTICAL physical mean, joined by a cusp edge profile | `ppaint_lum` at a far-field cell of the left region minus the same in the right | `0.0` exactly (the two flats are physically equal) | `!= 0`, and in the direction of the cusp polarity |
| **I4 — blind-spot texture** | a textured surround with an unsensed hole | the variance of the painted value across the hole's cells | `~0` (`gr_fill` = mean of neighbours ⇒ flat BY CONSTRUCTION) | `> 0`, i.e. the fill is not flat |
| **U1 — crowding** | the existing crowding battery | `pooled_ident` | **already present** | **DECLARED UNINFORMATIVE IN ADVANCE — reported, never counted** |
| **U2 — blind-spot flat fill** | the existing `gr_fill` battery | `gbel` in the hole | **already present** | **DECLARED UNINFORMATIVE IN ADVANCE — reported, never counted** |

**ARM I passes iff I1–I4 each move from absent to present.** Any item that does not is a
reported negative and ARM I fails. **No item may be rescued by adding machinery: an illusion
that has to be built is not a prediction (§7).**

### ARM R — the residual contrast arm (deterministic)

| id | region content | pre-registered verdict |
|---|---|---|
| **R1** | uniform | `korder=1`, `prefuted=0`, mean `presid` `< pquant/2` |
| **R2** | linear gradient | `korder` escalates 1→2, `prefuted=0`, mean `presid` `< pquant/2` at k=2 |
| **R3** | texture | `korder=2`, **`prefuted=1`**, mean `presid` **`>= pquant/2`** — the ladder exhausts and the residual STAYS large |
| **R4** | the R1/R3 CONTRAST | mean `presid`(texture) **strictly greater than** mean `presid`(uniform), and `prefuted` 1 vs 0 |

**ARM R passes iff R1–R4 all hold.** R3 is the arm that can kill the rung (§5.2).

### ARM K — k falls out (deterministic)

- **K1** — the three outcomes of §2.4 are each REACHED by some stimulus, and `korder` is
  never assigned outside the seed's rules (source-grep gate).
- **K2** — **§13.2 VACUITY**: toggle `paint` 0→1 and measure `max|on − off|` on every
  attribute this rung claims to affect. **`D == 0.0` exactly on all of them ⇒ decorative ⇒
  the rung STOPS and reports that**, before any illusion is claimed. Run FIRST.
- **K3** — **scale invariance of `pquant`**: alphabet ×4 with `pquant=4` reproduces every
  qualitative verdict of ARM I and ARM R. A verdict that moves means `pquant` is a magic
  number and §13 kills it.

### ARM F — floors and §9 (the only arms with n)

- **F1 — noise floor, n=100, seeds 66000–66099 (CONFIRMATORY, never used for anything
  else).** 100 iid random integer fields with **zero chroma anywhere**. Verdict:
  **0/100 invent painted appearance** (`max ppaint_app == 0.0`). A mechanism that paints
  chroma from no chroma is a confabulator, not a percept.
- **F2 — texture-residual floor, n=100, seeds 66100–66199 (CONFIRMATORY).** 100 iid random
  textures. Verdict: the fraction reaching `prefuted=1` is reported; pre-registered as
  **> 0.9**. This is R3 at power rather than on one hand-made texture.
- **F3 — §9 OFF-DAY.** `paint=0.0` (the shipped default) ⇒ every paint attribute reads
  exactly `0.0`; the fresh-boot default is asserted to be `0.0`; and
  `scripts/rung7_vision_bench.sh` reads **200 passed / 0 failed with `data/`**, unmoved. The
  **sd orbit law `{2:1,3:2,4:2,6:2,12:4}`** must be unmoved.

---

## 5. My predictions, in advance, with their provisos (§3.7)

Being right in advance is the only evidence I understand the model; a proviso that breaks
tells me what I did not understand.

### 5.1 What I expect to fall out

- **I1 neon spreading — WILL fall out.** High confidence. The region's appearance sample is
  a mean over the region's cells, so a sub-part carrying chroma tints the whole region. The
  magnitude will be **weak** (it is diluted by the achromatic majority), and I predict that
  is the *right* answer: neon spreading in humans is a weak tint, not a saturated fill. If it
  comes out saturated, my sampling rule is wrong even though the sign is right.
- **I2 watercolour — WILL fall out, and this is the RISKED prediction of the rung.** The
  strong outer contour IS a strict-|Δ| maximum, so it is a boundary and is EXCLUDED from the
  region. The weak inner chromatic contour is nearly iso-luminant with the interior, so it is
  NOT a maximum, so it is INSIDE the region and its chroma enters the sample. **The tint
  therefore takes the colour of the INNER contour and not the outer** — the actual asymmetry
  of the illusion — and it falls out of which contour is strong enough to be a boundary,
  with nothing about watercolour written anywhere. **If the tint comes out the colour of the
  outer contour, or the inner contour is a boundary, the account is wrong here.**
- **I3 Cornsweet — WILL fall out, WEAKLY, and the brief's guess that it needs k=2 is one I
  expect to be WRONG.** The cusp is the only strict-|Δ| maximum, so each flat region KEEPS
  its ramp shoulder; the k=1 region mean is therefore pulled toward the shoulder's polarity
  and the two physically-equal flats are painted DIFFERENTLY. That is the illusion, at
  **k=1**. **Proviso — the magnitude will be much smaller than the human effect**, because
  a region mean is area-weighted and the human match is near-complete regardless of cusp
  width. A weak, correctly-signed effect is what I expect; a full-strength one would surprise
  me and I would distrust it.
- **ARM R R1/R2/R4 — will pass.** These follow from the ladder's construction.

### 5.2 What I expect to break — pre-registered as the likely failure

- **R3 / F2 texture — THE ARM MOST LIKELY TO KILL THE RUNG, and I am registering that
  now.** The boundary criterion is threshold-free, and a texture is strict-|Δ| maxima
  everywhere, so a textured region should **FRAGMENT into micro-regions**. Each micro-region
  is then painted perfectly by its own k=1 mean and **`presid` collapses to ~0 with
  `prefuted=0`**. If that happens, **the mechanism does NOT know it is wrong on texture,
  ARM R fails, and the conjunction gate fails** — even if all four illusions land. **That
  outcome is a full result and will be reported as loudly as a success.** The diagnosis is
  already named: threshold-free non-maximum suppression over-segments, and the missing
  ingredient is a code-length cost on region count (MDL), which this rung does not build
  because its constant does not fall out of anything yet.
- **I4 blind-spot texture — UNCERTAIN, and for the same reason.** If the textured surround
  fragments, the hole joins whichever micro-region abuts it and the fill is locally plausible
  but is not a texture. I give this arm the lowest confidence of the four.

### 5.3 The outcome table — what each result MEANS, fixed now

| ARM I | ARM R | verdict |
|---|---|---|
| pass | pass | **the account is supported** — paint-from-sample predicts a family of illusions nobody added, AND knows when it is wrong |
| pass | **fail** | **THE RUNG FAILS.** A mechanism that fills indiscriminately produces spreading illusions and is useless. Reported as an indiscriminate filler, NOT as an illusion result. |
| **fail** | pass | the residual ladder works; the illusion predictions are **wrong**. The account, as a theory of these illusions, is refuted. |
| fail | fail | the account is wrong and the mechanism is inert. |

---

## 6. Analysis discipline binding on this rung

- **§5 — no metric surgery.** The statistics above are final. A failure that suggests the
  readout is wrong is a NEW pre-registration, never a reinterpretation.
- **§7 — negatives reported as loudly as positives**, and no machinery is added to make an
  illusion appear.
- **§13.1 — could this model have produced the OPPOSITE result?** Stated per item: I1 could
  fail if the sample excluded the inducers; I2 could fail if the inner contour were a
  boundary (a threshold criterion would make it one); I3 could fail if the shoulders were
  boundaries; R3 could fail (and I predict it will) by fragmentation. **None of the four is
  forced by the architecture** — each turns on a boundary/sampling fact that could have gone
  the other way, and §5.2 registers the one I expect to go against me.
- **§12.3 — provenance gates pinned to BOTH endpoints** of this rung's own commit range,
  never to `HEAD`.
- **§9 — OFF by default, byte-identity verified** before commit.

## 7. Burned-seed ledger — append

| range | used for |
|---|---|
| 66000–66099 | ARM F1 — noise floor (chroma confabulation), CONFIRMATORY |
| 66100–66199 | ARM F2 — texture-residual floor, CONFIRMATORY |
| 66200–66999 | reserved to this rung, UNBURNED |
