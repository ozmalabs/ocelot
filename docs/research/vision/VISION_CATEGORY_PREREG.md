# VISION — CATEGORY-LEVEL RECOGNITION (FRONTIER T2): a category as an MDL-minted AXIS-CODEBOOK region (pre-registration)

*Written and COMMITTED before the confirmatory run (PROTOCOL §3). Seeds
**44000–44999** (declared below; 12000–43999 burned/untouched by this rung). Builds
DIRECTLY on the wall-crossing rungs — INSTANCE recognition
(`VISION_IDENTITY_UNTANGLING_RESULTS.md`: generator-orbit identity, the invariant
"what"; `VISION_SIMILARITY_RESULTS.md`: the right nuisance group) — and on the MDL
category-minting pattern of `VISION_COLOUR_IDENTITY_RESULTS.md` (a category as a
quantum minted over a VALUE space, MDL-gated). It generalizes that MDL minting from
COLOUR value space to an OBJECT AXIS space, and it adds the ONE thing colour
identity lacked: a category with EXTENT (a region), so that an UNSEEN instance is
recognized by PROJECTION-CONTAINMENT — generalization, not memorization.*

## 0. The claim, and the audit that precedes it

**Instance recognition** (the crossed wall) recognizes a SPECIFIC shape invariant
under a nuisance transform: `t(O_i) → O_i`, one held identity per object, the
generator being the nuisance. **Category recognition** (this rung) is
generalization to a KIND: a NEW instance never seen before is recognized as a
member of a known category (a chair you have never seen, known as a chair).

The grounding (`VISION_VENTRAL_GROUNDING.md` BUILD-IMPL #5, the Chang–Tsao face
code): a high-level category IS a learned low-D AXIS basis with linear readout —
"shape (landmark-integer) + appearance (texture)" axes, a face = its projection.
The design this implies: **a category is a SUBSPACE / REGION in a learned
axis-codebook of the identity space** — mint the region where instances of a kind
VARY, and recognize a new instance by its PROJECTION falling into the held region.
This is the SAME MDL category-minting colour identity did over colour value space,
now over the OBJECT axis space, plus the region's EXTENT.

### THE CRUX (§1.1) — the likely failure point, stated in advance

**A system that only recognizes the exact instances it was shown has MEMORIZED, not
learned a category.** The decisive test is a HELD-OUT instance: a category member
the codebook never saw, whose axis coordinates are provably absent from the training
set, recognized as the category. If the substrate can only recognize seen instances
(no generalization) this is a CLEAN DIAGNOSED NEGATIVE — reported with the mechanism,
never forced to a pass by testing only on seen instances or by metric surgery (§5).

### AUDIT (in-code, §12.4) — is category-level expressible by composition, or does it need a mechanism the substrate lacks?

The three sub-questions the task poses, answered against the source:

**(1) The object AXIS-codebook — can an instance be encoded as a projection onto
axes?** YES, mechanically, EXACTLY as colour identity encoded a region by its
opponent coordinate. An instance is a node carrying an INTEGER coordinate over K
axes (the in-frame integer lattice — the frame/continuum invariant: in-frame is
integer, `shape_decode.rs::coord_ints` refuses floats by design). This is the
Chang–Tsao "landmark-integer shape" projection at the abstract-coordinate grain.
**BOUND (honest):** the axes are GIVEN by the representation (the adapter presents
the coordinate, mechanical ingest — like `colour_world` supplying `cL,cM,cS`), NOT
DISCOVERED from raw pixels. Learning the axis-codebook itself from natural images
(the full ~50-axis face code at scale) is the NAMED FRONTIER, out of scope, and is
the honest reason this crossing — if it crosses — is bounded.

**(2) MDL category-minting over that axis space — does the colour
`ci_mint_category` pattern generalize?** YES, with NO new Rust. The colour rung
minted a category where a VALUE clusters (`Count(same exact value) >= m_min`,
`Argmin` nearest assignment, `Not(Exists ...)` recognize-not-remint, all in
`seeds/vision_colour_identity.json`). The DSL already evaluates every primitive
needed for a REGION over axes: `Count`/`Filter`/`NodesOfType` (member count),
**`MinOver`/`MaxOver`** (`runners/dsl/src/term.rs:4543-4548`, used in
`seeds/principal_axes.json`, `continuous_pose.json` — per-axis box bounds over a
member set), `Gte`/`Lte`/`And` (containment), `Argmin`/`Sqrt`/`Minus`/`Times`/`Plus`
(nearest / distance), `Exists`/`Not` (guards). So the category REGION is expressible
by composition.

**(3) GENERALIZATION — does a new instance's projection land in the held category
subspace?** This is the thing to MEASURE, and where a negative would live. Colour
identity generalized to unseen VALUES only by `Argmin` NEAREST assignment, which
FORCE-ASSIGNS everything and so has NO floor (a novel category would be swallowed by
its nearest neighbour). Category recognition needs CONTAINMENT (a region with
extent), which gives BOTH generalization (interior interpolation) AND a floor
(refuse outside). `MinOver`/`MaxOver` + `Gte`/`Lte` express containment. The open
empirical question the run answers: does containment of a never-seen interior
coordinate constitute genuine generalization, or does the construction collapse to
memorization?

**VERDICT: IN-CLASS by composition — NO new Rust, NO seed edit to a committed rung.**
Category-level recognition composes from the axis-coordinate encoding (colour's
ingest pattern), the MDL mint (colour's `ci_mint_category`, generalized from a POINT
to a REGION via `MinOver`/`MaxOver`), and projection-containment
(`Gte`/`Lte`/`And`). What is NOT claimed and is the honest bound: the axes are given,
not learned from pixels; the region is an axis-aligned BOX, not an arbitrary
manifold; generalization is INTERPOLATION within the learned box (extrapolation is
refused, correctly). If the substrate could only mint POINT categories (no
`MinOver`/`MaxOver`), category-level would be a NEGATIVE — but those aggregators
exist and evaluate, so the region is buildable.

### The mechanism this rung contributes

ONE seed (`seeds/vision_category.json`, flag `CategoryParams.identity` OFF by
default, §9). An instance is an `ObjItem` with an integer coordinate split into:

- a **DISCRETE part-signature** `(d0, d1)` — d_disc = 2 axes shared EXACTLY by all
  members of a kind (the topology / parts: "a chair has a seat and a back"). This
  is the GROUPING key — it clusters WITHOUT a magic radius (colour's exact-`Count`
  mechanism, applied to the signature sub-coordinate);
- **CONTINUOUS proportion axes** `(v0, v1)` — d_var = 2 axes each member varies on
  (the metric proportions). These carry the within-category VARIATION and the
  generalization EXTENT.

Rules:

- `cat_mint` — DYNAMIC QUANTIZATION (colour's `ci_mint_category`, generalized).
  Group `ObjItem`s by exact discrete signature; where `Count(same (d0,d1)) >= m_min`
  and MDL compresses, MINT an `ObjCategory` quantum carrying the signature `(d0,d1)`,
  the member count, the canonical-member EXEMPLAR `(ex_v0, ex_v1)` (for the
  memorization control), and the REGION box `MinOver`/`MaxOver` of the members'
  `(v0, v1)` — `v0lo, v0hi, v1lo, v1hi`. Guarded by the same canonical-representative
  (lexicographic top-left member mints) and `Not(Exists ObjCategory@signature)`
  guards colour used, so batch `s.tick()` mints exactly one category per kind.
- `cat_recognize` — an `ObjItem` is RECOGNIZED as an `ObjCategory` iff its discrete
  signature matches AND its `(v0,v1)` is CONTAINED in the box
  (`v0lo <= v0 <= v0hi AND v1lo <= v1 <= v1hi`). Writes `cat_sig0/cat_sig1`
  (the recognized kind's signature) and `cat_recognized = 1`; leaves `cat_recognized
  = 0` (refused) when no held region contains it. This is the projection into the
  held subspace — the generalization readout AND the floor.
- `cat_memorize` — the MEMORIZATION CONTROL (colour's exact-match, in-seed). Writes
  `mem_recognized = 1` iff the `ObjItem`'s `(v0,v1)` EXACTLY equals some
  `ObjCategory`'s stored EXEMPLAR `(ex_v0,ex_v1)` (with matching signature); else 0.
  A memorizer recognizes ONLY exact stored exemplars; a held-out interior instance
  (coords never trained) gets `mem_recognized = 0`. The DiCarlo-style control:
  containment GENERALIZES what exact-match MEMORIZES.

The in-frame coordinate is INTEGER; the continuous lives ONLY in the cross-frame
containment/distance comparison (the frame/continuum invariant). NO new Rust.
`m_min = 3` FALLS OUT of d_disc = 2 (a category pays iff `m > d_disc/(d_disc-1) = 2`
⟺ `m >= 3`; the shared discrete signature is stored once per category instead of
once per member — §13, NOT tuned; identical derivation to colour's).

## 1. Hypotheses (two-sided)

- **H_gen (headline):** with the flag ON, a HELD-OUT instance of a trained kind —
  continuous coordinates provably ABSENT from the training set, interior to the
  learned box — is RECOGNIZED as that kind (`cat_recognized = 1`, correct
  signature). Null: held-out instances are NOT recognized (`cat_recognized = 0`) ⇒
  the axis-region cannot generalize ⇒ CLEAN NEGATIVE.
- **H_disc:** a held-out instance of a DIFFERENT trained kind is NOT recognized as
  this kind (cross-kind false-recognition count = 0, exact-0).
- **H_crux (memorization vs generalization):** on the SAME held-out instances,
  `mem_recognized = 0` for ALL (exact-match refuses the never-seen coords) while
  `cat_recognized = 1` for all (region recognizes). If both are equal, the region
  is not doing generalization work ⇒ NEGATIVE.
- **H_mdl:** k categories mint from N training instances, k << N, and MDL compresses
  (`d_disc*k + N < d_disc*N`); m_min=3 falls out of d_disc=2.
- **H_floor:** with the flag ON, (a) n=100 iid-noise fields (no shared signature)
  mint ZERO categories; (b) a held-out with a NOVEL discrete signature (never
  trained) is REFUSED (`cat_recognized = 0`, not force-assigned); (c) a held-out
  with a matching signature but continuous coords OUTSIDE the box (EXTRAPOLATION) is
  REFUSED — proving the box is LOAD-BEARING (§13.2) and the model CAN say no (§13.1).
- **H_down (load-bearing, §1 clause 5):** flag ON vs OFF, `max|on - off|` > 0 on the
  minted categories and recognitions (the mechanism moves something downstream).
- **H_offday (§9):** flag OFF (default) ⇒ seed inert; `ObjCategory` count 0, all
  recognition attrs at their neutral init; vision bench 200/0; sd orbit law
  `{2:1,3:2,4:2,6:2,12:4}` unmoved; sibling gates green.

## 2. The statistics, exactly

- **A_generalization:** count of held-out instances (one per trained kind, K=3)
  recognized with the correct signature via containment; `cat_recognized` and the
  assertion that each held-out `(v0,v1)` is not equal to any training member's
  `(v0,v1)`. Statistic: `gen_correct / K`.
- **B_discrimination:** over all (held-out instance, non-matching kind) pairs, the
  count recognized as the wrong kind. Statistic: `cross_false` (target 0, exact-0).
- **C_crux:** `mem_recognized` vs `cat_recognized` for every held-out instance.
  Statistic: `(sum mem_recognized, sum cat_recognized)` — target `(0, K)`.
- **D_mdl:** `k = |ObjCategory|`, `N = |training ObjItem|`, `mdl_raw = d_disc*N`,
  `mdl_categorized = d_disc*k + N`. Statistic: `mdl_categorized < mdl_raw`, ratio.
- **E_floor:** (a) false-mint fields over 100 noise seeds; (b) `cat_recognized` of a
  novel-signature held-out (target 0); (c) `cat_recognized` of an
  extrapolation held-out (target 0).
- **F_downstream:** `d_categories`, `d_recognized_max` between flag ON and OFF.
- **G_offday:** category count, max recognition attr with flag OFF (default).

## 3. n, fixed in advance

- **A/B/C/D/F/G** are DETERMINISTIC constructions (fixed integer fields), n=1 each —
  a deterministic mechanism check, exactly as colour identity's E/A/G/D/X arms.
- **E(a) noise floor: n=100, seeds 44000–44099** (the confirmatory floor block, the
  only randomized arm; power/precision matches colour identity's 100-seed floor).
  Seeds 44100–44999 remain CLEAN. A single false mint FAILS the floor.

## 4. Confirmatory seeds

Noise floor draws **44000–44099** (fresh, never used — verified against the ledger).
No other seed block is consumed. 12000–43999 untouched.

## 5. Decision rule

- **CROSSING (bounded)** iff ALL of: A_gen = K (all held-out recognized), B_disc = 0
  (exact-0 cross-kind), C_crux = (0, K) (memorization refuses, region recognizes),
  D_mdl compresses, E_floor all pass (noise 0/100, novel refused, extrapolation
  refused), F_down > 0, G_offday inert. Report as a BOUNDED crossing with the bounds
  of §7 stated on the claim.
- **CLEAN DIAGNOSED NEGATIVE** iff H_gen or H_crux nulls — held-out not recognized,
  or region ≡ memorization. Report the mechanism: what the axis-codebook region can
  and cannot generalize, and WHY (no forcing, no metric surgery, no seen-only test).
- A partial outcome (e.g. generalizes but no floor) is reported AS a partial, per
  the arm that failed — never rescued.

## 6. Exactly the listed tests. No sweeps. No re-runs.

The six arms above, once. A further attempt needs a NEW pre-registration with a NEW
mechanism-level hypothesis (§3.6).

## 7. Scope — what is NOT shown (stated in advance, §8)

- **The axes are GIVEN, not learned from pixels.** This is category recognition over
  a SUPPLIED axis-codebook (integer coordinates), not the discovery of the codebook
  from natural images. The full learned axis-codebook at natural-image scale is the
  NAMED FRONTIER.
- **The axis PARTITION (which axes are discrete-defining vs continuous-varying) is
  GIVEN by the representation** — the substrate discovers the category (grouping +
  region + recognition, unsupervised, no label read) but not the partition. Colour
  identity likewise hardcoded "group on the opponent axes."
- **The region is an axis-aligned BOX** (the simplest MDL region). Non-box category
  manifolds are a frontier.
- **Generalization is INTERPOLATION within the learned box.** Extrapolation beyond
  is REFUSED (a bound — and arguably the correct conservative behaviour).
- **Bounded to the discrete-similarity regime already crossed** (integer-lattice
  in-frame coordinates). NOT lighting, deformation, style — each the named frontier.
- Category minting is UNSUPERVISED (clustering, no label); the ground-truth `label`
  attr is used ONLY by the runner to build the train/test split and to score, NEVER
  read by any seed rule.

## 8. My PREDICTION, stated in advance (§3.7)

**I predict a BOUNDED CROSSING.** Reasoning: the axis-region genuinely generalizes
by containment — a never-seen INTERIOR lattice coordinate (strictly between the
training corners on each varying axis, inside the learned box) is recognized by
`v0lo <= v0 <= v0hi AND v1lo <= v1 <= v1hi`, and a memorizer (exact-exemplar match)
provably refuses that same coordinate. `MinOver`/`MaxOver` make the box's extent
fall out of the members' own spread (no magic radius, §13), and `Gte`/`Lte`
containment gives the floor colour's nearest-assignment lacked, so I expect
A_gen = 3, B_disc = 0, C_crux = (0, 3), the floors to hold, and G_offday inert.

**The provisos that would break it (and what each would teach):**

- If I cannot construct a held-out that is SIMULTANEOUSLY (a) absent from training,
  (b) interior to the box, and (c) refused by the memorization control, then
  generalization has collapsed to memorization ⇒ NEGATIVE. (I believe interior
  lattice points not equal to the training corners satisfy all three; if the box is
  degenerate — training members share a v-coordinate — it would fail, so the
  construction spaces training members apart.)
- If containment recognizes a matching-signature EXTRAPOLATION instance (H_floor c
  fails), the box is decorative and recognition is really signature-only ⇒ the
  region is not load-bearing (§13.2) — a partial, not a crossing.
- If a novel discrete signature is force-recognized (H_floor b fails), there is no
  floor ⇒ the mechanism is the nearest-assignment defect colour identity had, not
  containment.

Being wrong in any of these directions is the diagnosed result; I will report it as
such.
