# VISION — COLOUR IDENTITY: categorical colour as a MINTED, MDL-GATED SIGN (pre-registration)

*Written and COMMITTED before the confirmatory run (PROTOCOL §3). Seeds
**35000–35999** (declared below; 12000–34999 burned/untouched by this rung). Builds
DIRECTLY on the colour-salience rung (`VISION_COLOUR_PREREG.md` /
`VISION_COLOUR_RESULTS.md`, seeds 34000–34999): salience answered WHERE to look
(surround-relative opponent CONTRAST); this rung answers WHAT COLOUR IT IS
(a categorical SIGN over the opponent-colour VALUE).*

## 0. The claim, and the audit that precedes it

**Colour salience** (the prior rung) computed a region's surround-relative
opponent CONTRAST — a pop-out magnitude, WHERE to look. **Colour identity** (this
rung) computes a region's colour CATEGORY — a categorical SIGN for its colour
VALUE, WHAT colour it is. The category is a QUANTUM minted from the opponent-colour
subspace by the sd loop's DYNAMIC QUANTIZATION, **MDL-gated**: mint a category
where colours CLUSTER and it COMPRESSES (N similar colours → 1 category), refuse
where they don't. A region's colour SIGN is its nearest minted colour-quantum. This
is the Witzel & Gegenfurtner picture — categories over an underlying continuous
representation, minted where they compress — NOT hand-set boundaries.

The driving variable is the **in-frame opponent COORDINATE** of a region — the L−M
(red–green) and S−(L+M) (blue–yellow) recombinations of the cone attrs `cL,cM,cS`
the `colour_world` adapter already supplies — **NOT** the surround-relative contrast
(that was salience). The in-frame colour coordinate is INTEGER (the frame invariant
the salience rung established: coord stays integer; only a cross-frame comparison
magnitude is continuous). A colour category is minted at an integer opponent
coordinate; the continuous lives ONLY in the cross-frame distance used to assign a
sign (`Sqrt` of opponent differences — the same continuous-in-comparison role
salience's contrast magnitude played).

### AUDIT (in-code, §12.4) — is colour categorization IN-CLASS via the sd loop, or does it hit the objecthood wall?

**VERDICT: IN-CLASS. Colour categorization is low-D colour-space quantization, NOT
objecthood. It reuses the sd loop's DYNAMIC-QUANTIZATION PATTERN
(decode → recognize → mint → re-decode-on-`codebook_epoch`-growth) realized as a
new colour-specific seed rule set, with NO new Rust.** The distinction the task
draws is decisive and confirmed in the source:

- **The sd loop's `ShapeDecode`/`sd_mint_quantum` decode a RELATION-SYSTEM
  signature**, not a low-D point. `runners/dsl/src/shape_decode.rs:1097`
  (`eval_shape_decode`) composes a goal `signature` (a `Vec<Value>` of relation
  tuples `[predicate, obj, …]`, `shape_decode.rs:69–149`) against a
  `ShapeSignature` codebook; `sd_mint_quantum`
  (`seeds/shape_decode_loop.json`) mints a `CapabilityAxis` from a residual RELATION
  set. A colour VALUE `(rg,by)` is a point in a 2-D integer subspace, not a
  relation-system — so `ShapeDecode` is not the natural decoder for it, and,
  critically, `sd_mint_quantum` mints on ANY residual (with only a `capability_keys`
  DEDUP guard, `shape_decode_loop.json` ~line 1881), so pointed at raw colour values
  it would mint one quantum per DISTINCT value — over-minting on a gradient. **The
  sd loop does NOT natively carry an MDL member-count gate.**
- **`space_quantize` (Rust, `space_quantize.rs:1`) decomposes NAVIGABLE SPACE
  geometrically** (config-space erosion of a Cell/pose belief into maximal
  axis-aligned boxes over the PASSABLE region), not a value distribution. A colour
  cluster is not a connected free-space region, so `space_quantize` is not the
  decoder either.
- **BUT the DSL expresses MDL-gated colour-space quantization with NO new Rust.**
  Every primitive the mint/assign decision needs already evaluates and is used in
  committed seeds: `Count(Filter(NodesOfType(...), var, pred))` (member count —
  `affordance_basis.json`), `Argmin(NodesOfType(...), var, value)` (nearest
  category — `conversation_steering.json`), `Exists`/`Not(Exists)` (the mint /
  re-mint guards — `shape_decode_loop.json`), `Sqrt`/`Minus`/`Times`/`Plus`
  (opponent distance — `vision_colour.json`), and `set_attr`/`add_node`/`add_edge`
  + a `codebook_epoch` bump (`sd_mint_generator`'s exact idiom). The engine's
  non-batch fixpoint applies ONE progressing binding per pass and re-derives guards
  between applications (`rewrite.rs:1886`), so a `Not(Exists ColourCategory@this
  colour)` mint guard prevents a duplicate category for one colour by construction.
- **This is NOT the objecthood wall.** Attaching colour to a BOUND OBJECT
  (object re-ID / colour constancy / the full recognition "what" layer) is the
  diagnosed cortex dead end (H1 null, `VISION_RUNG8E_RESULTS.md`). This rung is the
  FORMER only: quantize a 2-D colour VALUE space into category quanta. No object, no
  binding, no constancy.

**The rung's contribution:** ONE seed (`seeds/vision_colour_identity.json`, flag
OFF by default, §9). It instantiates the dynamic-quantization loop for the colour
subspace: `ci_opponent` computes the integer opponent coordinate; `ci_mint_category`
mints a `ColourCategory` quantum where a colour value CLUSTERS and MDL COMPRESSES;
`ci_assign` writes each region's categorical SIGN as its nearest minted quantum and
re-decodes on codebook growth. NO new Rust.

## 1. Mechanism — exact (all in graph data, no Python decision)

The runner (`scripts/colour_identity_measure.py`, adapter
`domains/colour_identity_world.py`) builds cone-cell fields **mechanically** and
reads the minted categories / per-cell signs back; it makes **no percept decision**
(§0 / CLAUDE.md). Supplying `cL,cM,cS` per cell is mechanical ingest, exactly like
`colour_world`. Graph:

- `ColourIdentityParams{identity: 0.0}` — ONE OFF-by-default flag (the
  `ColourParams`/`StreamParams` idiom); `identity` arms the whole loop.
- Cells are `Region` nodes (integer cone attrs `cL,cM,cS`; computed `crg,cby`;
  bookkeeping `op_done:0, assigned_epoch:-1, sign_rg:0, sign_by:0, sign_dist:-1`).
- A `Scene{epoch:0}` with `has_region` edges; `Scene.epoch` is the codebook epoch
  (bumped by each mint — the sd `codebook_epoch` re-arm, kept on the scene so the
  match variable can be written).
- Minted `ColourCategory{crg,cby,members,minted:1}` nodes (`has_category` edge from
  the scene) — the colour codebook, grown at runtime.

The opponent axes are integer linear recombinations of the cones (in-frame /
integer, the frame/continuum invariant): `rg = cL−cM`, `by = cS−(cL+cM)`. d = **2**
chromatic opponent dimensions.

**Rule `ci_opponent`** (`match [scene has_region R]`, where `identity>0.5` AND
`op_done<0.5`): set `crg = cL−cM`, `cby = cS−(cL+cM)`, `op_done=1`. Reads only raw
cones (self) — firing order irrelevant.

**Rule `ci_mint_category`** — DYNAMIC QUANTIZATION (mint), MDL count-gated. Where:
- `identity>0.5`;
- all opponent coords computed: `Not(Exists Region z with op_done<0.5)` (no
  transient undercount — mint only after the coordinate field is complete);
- **the MDL gate:** `Count(Filter(Region q, q.crg==R.crg AND q.cby==R.cby)) ≥ 3` —
  this exact colour value has ≥ m_min members;
- not already minted: `Not(Exists ColourCategory cat with cat.crg==R.crg AND
  cat.cby==R.cby)` (fixpoint safety + recognize-not-re-mint).
Effects: `add_node cat ColourCategory{crg:R.crg, cby:R.cby, members:<count>,
minted:1}`; `add_edge scene has_category cat`; `set scene.epoch = epoch+1`.

**m_min = 3 FALLS OUT of the coordinate dimensionality (§13), it is NOT tuned.** A
colour category costs a prototype of d integers; a member costs 1 label instead of
its d-integer raw coordinate. A category with m members pays for itself iff
`m·d > d + m` ⟺ `m > d/(d−1)`. For d = 2: `m > 2` ⟺ `m ≥ 3`. So the mint gate is
exactly "a category compresses a 2-D colour code iff it has ≥ 3 members" — the 3 is
determined by d=2, not by any answer we wanted. (At m=2: raw 4 vs categorized 2+2=4,
equal, no compression → refuse.)

**Rule `ci_assign`** — DEQUANTIZATION (decode/recognize), re-decode on growth.
Where: `identity>0.5`; all `op_done`; `Count(ColourCategory) > 0`;
`R.assigned_epoch != scene.epoch` (re-arm on codebook growth, the `sd_redecode`
idiom). Effects: `sign_rg = Attr(Argmin(ColourCategory c by dist(R,c)), crg)`,
`sign_by = Attr(Argmin…, cby)`, `sign_dist = dist(R, Argmin…)`,
`assigned_epoch = scene.epoch`, where `dist(R,c) = Sqrt((R.crg−c.crg)² +
(R.cby−c.cby)²)`. A region whose colour EXACTLY equals a prototype gets `sign_dist=0`
and that category's sign (recognize); an off-prototype region gets its NEAREST
minted quantum (the "nearest sign").

The runner ticks once (mechanical, no decision): arm the flag, `s.tick()` to
fixpoint, read categories + signs. Zero floats are tuned: cone values are STRUCTURAL
data; opponent axes are integer recombinations (in-frame integer); the MDL gate m=3
falls out of d=2; the distance is a pure `Sqrt` (the cross-frame comparison
magnitude, §13).

## 2. Statistics — exact, per arm

All arms DETERMINISTIC except the noise floor (n fixed in advance). "n_categories"
= `Count(NodesOfType("ColourCategory"))`; a cell's sign = `(sign_rg, sign_by)`.

### E — EMERGENCE / MDL (the headline)

A 6×6 = 36-cell field, THREE distinct colour clusters, each on 12 cells: A `(rg,by)`
= `(10, 0)` (`cL=15,cM=5,cS=20`), B `(−10, 0)` (`cL=5,cM=15,cS=20`), C `(0, 12)`
(`cL=10,cM=10,cS=32`). Every cell's colour is one of these three EXACT values.
- **PASS iff** exactly **3** `ColourCategory` are minted (one per clustered colour),
  each at the correct `(crg,cby)`, each with `members=12`; and MDL COMPRESSES:
  `MDL_categorized = k·d + N = 3·2 + 36 = 42` `<` `MDL_raw = N·d = 36·2 = 72` (ratio
  ≥ 1.5). *A few clusters mint that-many category quanta, k=3 ≪ N=36, MDL down.*

### A — ASSIGNMENT (correct sign + recognize-not-re-mint)

(a) On the E field, EVERY cell's sign `(sign_rg,sign_by)` equals its OWN colour, at
`sign_dist=0` (each cell recognized as its own minted category).
(b) NEAREST off-prototype: a 2-cluster field (A `(10,0)`×12, B `(−10,0)`×12) plus
ONE probe cell at `(6,0)` (`cL=13,cM=7,cS=20`, a singleton, count 1 < 3 so it mints
nothing) — the probe's sign is A `(10,0)` (nearest: dist 4 vs 16), NOT B.
(c) RECOGNIZE, not re-mint (the sd has-guard / epoch): a cluster of 5 A cells is
ticked → 1 category; a 6th A cell is then added and ticked again → still **1**
category (the `Not(Exists)` guard blocks a second mint) and the 6th cell is assigned
to the existing A category at `sign_dist=0`.
**PASS iff** (a) all 36 signs correct at dist 0; (b) probe sign == A; (c) n_categories
stays 1 across the re-presentation and the new cell is recognized.

### G — SMOOTH-GRADIENT FLOOR (anti-overfit, deterministic, exact 0)

A 6×6 field with a MONOTONE opponent ramp: cell `(r,c)` has `cL=10+3·(6r+c)`,
`cM=10`, `cS=10+cL+cM` (so `by=0` uniform, `rg = 3·(6r+c)` takes 36 DISTINCT values
0,3,6,…,105). No colour value recurs; every `Count(same colour) = 1 < 3`.
**PASS iff** n_categories == **0** EXACTLY and no cell receives a sign — *a smooth
gradient mints no false category per shade; a category is minted ONLY if it
compresses (§1.1: no minted category that fails to pay for itself).*

### N — COLOUR-NOISE FLOOR (anti-overfit, n = 100, seeds 35000–35099, exact 0)

100 fields of 6×6 iid-random cones (`cL,cM,cS ∈ [0,99]` per cell, per-seed RNG).
The opponent space is large (rg ∈ [−99,99], by ∈ [−198,99]; ≈ 200×298 ≈ 6×10⁴
values), so a coincidental 3-collision on one exact `(rg,by)` across 36 cells has
probability ≈ C(36,3)/V² ≈ 7140 / 3.6×10⁹ ≈ 2×10⁻⁶ per field (≈ 2×10⁻⁴ over 100).
**PASS iff `0/100`** fields mint any `ColourCategory` — scattered colour noise forms
no coherent cluster, so it mints no category. (Reported honestly per §7: a rare
coincidental exact 3-collision that DID mint would be the honest MDL answer — 3
identical cells genuinely compress — and would be reported, not hidden; the
prediction is that none occurs.)

### D — DOWNSTREAM / LOAD-BEARING (§1 clause 5 / §13.2)

The E field, run with `identity=1` vs `identity=0` (default). Measure
`D = max|on − off|` over the claimed downstream attrs (n_categories; each cell's
`sign_rg,sign_by,op_done`).
**PASS iff** `D > 0` on n_categories (3 vs 0) AND on the signs (a sign field vs an
empty one) — the mechanism moves something downstream; it is not decorative. (A NEW
cell of a seen colour is RECOGNIZED — assigned — ON and unassigned OFF, the
recognition the sign enables.)

### X — §9 OFF-DAY (defaults preserve committed results)

The E field, flag LEFT at default (`identity=0`), tick.
**PASS iff** n_categories == 0, no cell has `op_done=1`, no sign written — the seed
is inert by default, so every committed vision/colour result reproduces exactly.

**Bench / byte-identity (§9):** `vision_colour_identity` is loaded only by the
runner/gate (NOT boot-loaded), ships its flag OFF, and adds NO Rust ⇒ engine
byte-identical by construction. PASS iff: bench **200/0** with `data/`; the sd orbit
law `{2:1,3:2,4:2,6:2,12:4}` unmoved; sibling gates green — colour · stream ·
illusion · blink · vision-ground · time · depth · stereo · dim · gen_infer ·
provenance · sdloop · cycle-detect.

## 3. n, fixed in advance

Deterministic arms (E, A, G, D, X) need no n. The noise floor N: **n = 100**
(seeds 35000–35099), matching the colour/stream/illusion floors. No power analysis
is needed for a floor whose null is an EXACT 0 count (any single false category
fails it). No sweeps, no re-runs (§3.6).

## 4. Burned-seed ledger for this rung

- **35000–35099** — colour-noise floor (N), 100 seeds.
- **35100–35999** — CLEAN, reserved for any follow-up with its own prereg.

Confirmatory floor seeds consumed ONCE here, never reused. The deterministic arms
use hand-constructed stimuli only (no 35xxx seed touched).

## 5. Decision rule — what each answer means (§7: either answer is a result)

- **3 clusters mint 3 categories AND MDL compresses AND every sign is correct AND a
  seen colour is recognized-not-re-minted AND a gradient mints 0 AND noise mints
  0/100 AND the flag is load-bearing** ⇒ categorical colour is a minted, MDL-gated
  sign over the integer opponent subspace, reusing the dynamic-quantization pattern,
  with zero magic numbers (m=3 falls out of d=2). Bounded to the exact-value /
  integer-coordinate class.
- **Clusters do NOT mint that-many categories** (or a gradient over-mints) ⇒ colour
  categorization does not emerge/compress as claimed — a clean NEGATIVE, reported,
  NOT rescued (no metric surgery, §5).
- **A seen colour re-mints instead of recognizing** ⇒ the re-decode/has-guard is
  broken; reported.
- **Noise invents a category** ⇒ the MDL gate hallucinates structure; overfitting;
  reported.
- **Categorical colour turns out to need objecthood** (a bound object to attach a
  colour to) ⇒ this rung's IN-CLASS claim fails and the finding is the wall; a clean
  NEGATIVE, reported. *(Predicted NOT: the 2-D value-space quantization above is
  self-contained, object-free.)*

## 6. Prediction, stated in advance, with provisos (§3.7)

I predict **E mints exactly 3 categories with MDL 72→42 (1.71×), A holds all three
ways, G mints 0 exactly, N mints 0/100, D is load-bearing, X is inert** — because
colour categorization is a low-D clustering the DSL expresses directly (the sd-loop
mint/recognize/epoch pattern on `Count`/`Argmin`/`Sqrt`), and the MDL member-count
gate (m ≥ 3, falling out of d=2) mints exactly the recurring exact-colour values and
refuses lone shades.

Provisos that could break (and what each would teach):
1. **Fixpoint duplicate-mint.** I predict the non-batch one-binding-per-pass engine
   (`rewrite.rs:1886`) + the `Not(Exists ColourCategory@colour)` guard mint exactly
   ONE category per clustered colour. If two same-colour regions mint duplicates in
   one pass, the guard is not re-derived as expected — reported, and the fix is a
   representative-region guard, NOT a threshold.
2. **`Count(Filter(NodesOfType))` member count.** I predict the exact-colour member
   count evaluates (the `affordance_basis` idiom). If `Filter` over `NodesOfType`
   with an `Eq(crg,crg)∧Eq(cby,cby)` predicate returns 0/errors, the MDL gate is
   unreadable — a build detail, reported.
3. **Re-decode ordering.** I predict gating `ci_assign` on `assigned_epoch !=
   scene.epoch` makes every sign reflect the FINAL codebook (re-arm on each mint).
   If assignment latches an early (incomplete) codebook, some signs are wrong;
   reported, not patched with a threshold.

## 7. Scope — what is NOT shown (§8), the named frontier

- **This is CATEGORICAL COLOUR (the SIGN / "what colour"), at the EXACT-VALUE /
  INTEGER-COORDINATE grain.** A category is a quantum minted at an integer opponent
  coordinate where the value CLUSTERS (recurs ≥ 3, MDL-paying); a region's sign is
  its nearest minted quantum. The in-frame colour coordinate is INTEGER; the
  continuous lives ONLY in the cross-frame `Sqrt`-distance used to assign a sign
  (`coord_ints` refusing floats stays correct).
- **NAMED FRONTIER, NOT this rung — perceptual NEARNESS in MINTING.** Grouping
  SIMILAR-but-not-identical colours across a gap (jittered clusters → one category)
  is the CONTINUOUS CROSS-FRAME comparator ("bins propose, continuous decides") — the
  colour-metric twin of real-angle rotation and sub-integer disparity in the sibling
  rungs. Here MINTING is exact-value; only ASSIGNMENT is nearest. Deferred, not
  attempted. (The MDL join-vs-mint criterion that would license tolerance without a
  magic number is design-only.)
- **NAMED FRONTIER, NOT this rung — the OBJECTHOOD wall.** Object colour re-ID
  (attaching a colour to a BOUND object), colour CONSTANCY / illuminant-discounting,
  and the full recognition "what" layer need a bound object — the diagnosed cortex
  dead end (H1 null). Categories here are minted from colour AS PRESENTED; **no
  constancy is claimed**.
- **Do NOT claim this "solves colour identity" or crosses the objecthood wall.** It
  is the colour-categorization SIGN, one honest bounded step downstream of salience.

## 8. Engine / bench (filled at OUTCOME)

Engine hash + resolution path, bench condition, and the §9 byte-identity table are
recorded in `VISION_COLOUR_IDENTITY_RESULTS.md` at the confirmatory run. **This rung
adds NO Rust**; the shared canonical build is legitimate iff the Rust source is
byte-identical (§10.1 rule 4) — verified by `provenance_line()`. `data/` symlinked to
canonical (§10.2).
