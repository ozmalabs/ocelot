# VISION — CATEGORY-LEVEL RECOGNITION (FRONTIER T2): results

*Pre-registration: `VISION_CATEGORY_PREREG.md`, committed BEFORE the run at
**`59ee91da`** (PROTOCOL §3). Runner `scripts/category_measure.py`; pinned
`results/category_measure.json`; gate `tests/test_category_migrated.py`; seed builder
`tools/build_vision_category.py` → `seeds/vision_category.json`; adapter
`domains/category_world.py`. Seeds **44000–44999** (noise floor 44000–44099
consumed; 44100–44999 CLEAN; 12000–43999 untouched). Engine **`7d5f50c18673`**
(shared build, Rust source byte-identical — **NO new Rust**, §10.1 rule 4). Base
`main` HEAD **`301ae161`** (`git merge-base --is-ancestor 301ae161 HEAD` verified).*

## OUTCOME: BOUNDED CROSSING

**Category-level recognition crosses, bounded.** A NEW instance never seen before is
recognized as a member of a known category by its PROJECTION falling into a held
category subspace — and, decisively (§1.1), this is GENERALIZATION, not
memorization: on the same held-out instances the exact-match memorization control
REFUSES all while the axis-region recognizes all. All 9 confirmatory arms pass, and
the crux and the floors are RISKED tests the mechanism could have failed (§13.1) —
each is answered by the opposite-mechanism control producing the opposite result.

## The mechanism (by composition, NO new Rust)

Category-level recognition composes from three pieces already in the substrate:

1. **The object AXIS-codebook** — an instance is an `ObjItem` carrying an INTEGER
   coordinate over axes (the Chang–Tsao "landmark-integer" projection at the
   abstract-coordinate grain; in-frame integer, the frame/continuum invariant),
   split into a DISCRETE part-signature `(d0,d1)` and CONTINUOUS proportion axes
   `(v0,v1)`. Mechanical ingest, exactly like `colour_world` supplies `(cL,cM,cS)`.
2. **MDL category-minting** — the colour-identity `ci_mint_category` pattern,
   generalized from a POINT (an exact colour value) to a REGION: `cat_mint` groups
   `ObjItem`s by exact discrete signature (the grouping key — colour's exact-`Count`
   mechanism, no magic radius), and where `Count(same signature) >= m_min = 3` mints
   an `ObjCategory` carrying the signature, the member count, the canonical-member
   EXEMPLAR, and the REGION BOX `MinOver`/`MaxOver` of the members' `(v0,v1)`.
3. **Projection-based generalization** — `cat_recognize` recognizes an `ObjItem` iff
   its signature matches AND its `(v0,v1)` is CONTAINED in the box
   (`v0lo<=v0<=v0hi AND v1lo<=v1<=v1hi`, `Lte`). Containment of a never-seen interior
   coordinate IS the generalization; the containment REFUSAL is the floor colour's
   `Argmin` nearest-assignment lacked.

The DSL evaluates every primitive needed (`Count`/`Filter`/`NodesOfType`,
**`MinOver`/`MaxOver`** — `term.rs:4543`, `Gte`/`Lte`/`And`, `Exists`/`Not`/`Eq`), so
the axis-region is expressible with NO new Rust and NO edit to a committed rung.
`m_min = 3` FALLS OUT of `d_disc = 2` (a category pays iff `m > d/(d-1) = 2` ⟺
`m >= 3`; the shared discrete signature is stored once per category instead of once
per member — §13, NOT tuned; identical derivation to colour's). Minting is
UNSUPERVISED — no label is read by any rule.

## Per-arm results (`results/category_measure.json`)

| arm | result | verdict |
|---|---|---|
| **G — GENERALIZATION (headline)** | 3/3 held-out recognized, every held-out `coord_unseen = true` (coords `∉` training set) and the correct kind's signature | **PASS** |
| **B — DISCRIMINATION exact-0** | `cross_false = 0` — no held-out recognized as a different kind | **PASS** |
| **C — THE CRUX (memorization vs region)** | `(sum_mem, sum_cat) = (0, 3)` — exact-match memorization REFUSES every held-out; the region RECOGNIZES every held-out | **PASS** |
| **D — MDL** | `k = 3` categories from `N = 12` training instances; `mdl_raw = 24 > mdl_categorized = 18` (ratio 1.33); `m_min = 3` falls out of `d_disc = 2` | **PASS** |
| **E(b) — FLOOR / novel signature** | a held-out with a signature never trained (`d0=9,d1=9`) → `cat_recognized = 0` (refused, not force-assigned) | **PASS** |
| **E(c) — FLOOR / extrapolation** | a held-out with a MATCHING signature but out-of-box proportions (`v0=100,v1=100`) → `cat_recognized = 0` (the box is LOAD-BEARING, §13.2) | **PASS** |
| **E(a) — FLOOR / noise** | 0/100 iid-noise fields (seeds 44000–44099) mint a category | **PASS** |
| **F — DOWNSTREAM / load-bearing** | flag ON: 3 categories, recognitions fire; flag OFF: 0 categories, no recognitions; `d_recognized_max = 1.0` | **PASS** |
| **X — OFF-DAY (§9)** | flag OFF (default): 0 categories, `max_cat_recognized = 0`, `max_mem_recognized = 0` — seed inert | **PASS** |

The categories minted (each a signature + box + exemplar): A `sig(1,1)` box
`[10,20]×[30,40]` ex `(10,30)`; B `sig(2,1)` box `[50,60]×[30,40]` ex `(50,30)`; C
`sig(1,2)` box `[10,20]×[70,80]` ex `(10,70)` — all 4 members each, boxes falling
out of the training corners' own spread.

## Why the crux is a real generalization result, not memorization (§1.1)

The held-out instances (A `(15,35)`, B `(55,35)`, C `(15,75)`) have continuous
coordinates that are **provably absent from the training set** (the runner asserts
`coord_unseen`) — they are INTERIOR points, strictly between the training corners on
each varying axis. A pure memorizer can only recognize a coordinate it stored: the
exact-exemplar control `cat_memorize` returns `mem_recognized = 0` for all three. The
ONLY way containment succeeds on a never-seen coordinate is genuine INTERPOLATION
within the learned box. This is the DiCarlo-style "the region separates what
exact-match memorizes" control — the object-axis twin of identity-untangling's
"orbit separates what raw tangles."

The floors make each half of the signature a RISKED test (§13.1 — "could this model
have produced the opposite?"): a nearest-assignment mechanism (colour's `ci_assign`)
would have FORCE-ASSIGNED the novel-signature and extrapolation instances to their
nearest category, FAILING E(b)/E(c); containment REFUSES them. And a memorization
mechanism would have refused the held-out interiors, FAILING G/C. Each control
produces the opposite result, so the crossing is not a tautology with error bars.

## BOUNDS (§8) — what is NOT shown

- **The axes are GIVEN, not learned from pixels.** This is category recognition over
  a SUPPLIED axis-codebook (integer coordinates ingested by the adapter), not the
  discovery of the codebook from natural images. **The full learned axis-codebook at
  natural-image scale (the ~50-axis face code from raw input) is the NAMED FRONTIER.**
- **The axis PARTITION (which axes are discrete-defining vs continuous-varying) is
  GIVEN by the representation.** The substrate discovers the category (grouping +
  region + recognition, unsupervised) but not the partition — exactly as colour
  identity hardcoded "group on the opponent axes."
- **A kind IS its discrete part-signature.** Two kinds with IDENTICAL part-signatures
  but different proportions are NOT separable — they merge into one category with a
  larger box. Category identity here rides on the shared discrete signature; richer
  category geometry (overlapping / non-box manifolds) is a frontier.
- **The region is an axis-aligned BOX** (the simplest MDL region).
- **Generalization is INTERPOLATION within the learned box.** Extrapolation beyond is
  REFUSED — a bound, and the conservative-correct behaviour (refuse rather than
  hallucinate a category for an out-of-distribution instance).
- **Bounded to the discrete-similarity regime already crossed** (integer-lattice
  in-frame coordinates; INSTANCE recognition = generator-orbit identity,
  `VISION_IDENTITY_UNTANGLING_RESULTS.md` / `VISION_SIMILARITY_RESULTS.md`). NOT
  lighting, deformation, style — each a named frontier.

## §9 — defaults preserve committed results

- **Flag OFF by default** (`CategoryParams.identity = 0.0`): the seed is inert (arm
  X), and `vision_category` is only ever loaded on explicit request
  (`load_seeds_into(..., ["vision_category"])`), so no existing agent boots with it.
- **NO new Rust** — engine `7d5f50c18673`, shared build, Rust source byte-identical
  (`provenance_line()` reads `shared … Rust source identical`).
- Vision bench `scripts/rung7_vision_bench.sh`: **200 passed / 0 failed** (with
  `data/` symlinked), = the pre-build baseline.
- sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED (`test_sdloop_vision_migrated.py`).
- Sibling gates green (colour-identity · similarity · identity-untangling ·
  sdloop-vision · engine-provenance) + the new gate `test_category_migrated.py` 9/9.

## Provenance (§10)

```
engine 7d5f50c18673 @ .../runners/dsl/python/substrate_rs/_native.abi3.so
  [shared build — Rust source identical]
```

Base `main` HEAD `301ae161` (ancestor-verified). Pre-reg committed BEFORE the run at
`59ee91da`. Results/build/gate committed on branch
`gamma-substrate/vision-category-t2`.
