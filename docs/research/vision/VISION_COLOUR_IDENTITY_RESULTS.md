# VISION — COLOUR IDENTITY: categorical colour as a MINTED, MDL-GATED SIGN (RESULTS)

*Confirmatory run of `VISION_COLOUR_IDENTITY_PREREG.md` (authored and committed
BEFORE the run at **`bfdb449f`**, a separate commit ahead of this results commit,
§3). Runner `scripts/colour_identity_measure.py`; gate
`tests/test_colour_identity_migrated.py`; seed `seeds/vision_colour_identity.json`
(builder `tools/build_vision_colour_identity.py`); adapter
`domains/colour_identity_world.py`; raw `results/colour_identity_measure.json`.
Builds DIRECTLY on the colour-salience rung (`VISION_COLOUR_RESULTS.md`, seeds
34000–34999): salience answered WHERE to look (surround-relative opponent CONTRAST);
this rung answers WHAT COLOUR IT IS (a categorical SIGN over the opponent-colour
VALUE), downstream of salience.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`
  — **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*; this rung adds **NO
  Rust**, so the shared build is legitimate, §10.1 rule 4). `data/` symlinked to
  canonical (§10.2).
- **Bench 200 passed / 0 failed with `data/`** (`scripts/rung7_vision_bench.sh`).
- **Sibling gates green.** colour · stream · sdloop · dimension-inference ·
  engine-provenance + the new colour-identity gate = **49 passed** in one process;
  illusion · blink · vision-ground · time · depth · stereo · cycle-detect green
  (separate process). The **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is unmoved** (the
  sdloop gate `test_orbit_law_arithmetic_matches_the_measured_mint_counts` passed).
- **NO new Rust, ONE new seed** (`vision_colour_identity`, NOT boot-loaded; ships
  `ColourIdentityParams{identity:0.0}` OFF by default), so §9 byte-identity holds by
  construction and is verified above.

## Verdict — ALL 6 gated arms PASS (every prediction held; one build error was caught and fixed BEFORE believing, reported below)

| arm | result |
|---|---|
| **E_emergence** (headline) | **PASS** — a 36-cell field of 3 colour clusters (12 cells each) mints EXACTLY **3** `ColourCategory` quanta at the correct opponent coords `{(−10,0),(0,12),(10,0)}`, `members=12` each; MDL COMPRESSES **72 → 42 (1.71×)**; all 36 cells' signs are correct at `dist=0`. *A few clusters mint that-many category quanta, k=3 ≪ N=36, MDL down.* |
| **A_assignment** | **PASS** — (a) every cell recognized as its OWN category at `dist 0`; (b) an off-prototype probe at `(6,0)` gets its NEAREST quantum `(10,0)` at `dist 4` (vs B's 16), NOT B; (c) a NEW instance of a seen colour is RECOGNIZED, not re-minted (`n_cats` 1→1, new cell `dist 0`). |
| **G_gradient_floor** (anti-overfit) | **PASS** — a smooth monotone 36-shade opponent ramp (all shades distinct) mints **0** categories and assigns **0** signs. *No false category per shade.* |
| **N_noise_floor** (anti-overfit, n=100) | **PASS** — **0/100** iid colour-noise fields (seeds 35000–35099, cones [0,99]) mint any `ColourCategory`. |
| **D_downstream** (§1.5 / §13.2) | **PASS** — flag load-bearing: `n_categories` 3 (ON) vs 0 (OFF), `max|sign_on−sign_off|=10`, `max|op_done_on−op_done_off|=1`. The mechanism moves structure downstream; it is not decorative. |
| **X_offday** (§9) | **PASS** — flag OFF (default) ⇒ inert: `n_categories=0`, `max op_done=0.0`, `max sign_rg=0.0`. |

## The headline — categorical colour is a MINTED, MDL-GATED quantum over the opponent-colour VALUE

**ONE seed instantiates the sd loop's DYNAMIC-QUANTIZATION pattern
(decode → recognize → mint → re-decode on `codebook_epoch` growth) for the 2-D
integer opponent-colour subspace — with ZERO new Rust and ZERO magic numbers:**

- **`ci_opponent`** computes the in-frame INTEGER opponent coordinate of each cell
  from its raw cones: `crg = cL−cM`, `cby = cS−(cL+cM)` (the two chromatic axes the
  colour-salience rung used, but here the VALUE, not the surround-relative contrast).
- **`ci_mint_category`** MINTS a `ColourCategory` quantum at an exact opponent
  colour value where the value CLUSTERS and MDL COMPRESSES — gated on the **member
  count** `Count(Filter(Region, same exact crg&cby)) ≥ 3`. That `3` is `m_min`, and
  it **FALLS OUT of the coordinate dimensionality d=2**: a category costs a
  d-integer prototype and saves 1 label per member vs a d-integer raw coordinate, so
  it pays iff `m·d > d + m` ⟺ `m > d/(d−1)`; for d=2 that is `m > 2` ⟺ `m ≥ 3` (at
  m=2: raw 4 vs categorized 2+2=4, equal — refuse). No tuned threshold (§13).
- **`ci_assign`** writes each region's categorical SIGN as its NEAREST minted
  quantum — `Argmin` over `ColourCategory` by the cross-frame opponent distance
  `Sqrt((R.crg−c.crg)² + (R.cby−c.cby)²)` — and re-decodes on codebook growth
  (`assigned_epoch != Scene.epoch`, the `sd_redecode` re-arm).

**The emergence discriminator is the whole point, and it holds exactly:** a scene
with three distinct colour clusters mints exactly three category quanta (one per
cluster, at the correct opponent coordinate, each carrying its 12 members), and the
MDL cost drops from `N·d = 72` (raw) to `k·d + N = 42` (categorized), a 1.71×
compression — the categories PAY for themselves. *Categories EMERGE from the colour
distribution via MDL; they are NOT hand-set boundaries* (Witzel & Gegenfurtner).

**The anti-overfit crux holds — NOT a universal colour-hallucinator.** A smooth
monotone gradient of 36 distinct shades mints ZERO categories: no colour value
recurs, so `Count(same colour) = 1 < 3` for every cell and nothing pays for itself
— the MDL member-count gate does the anti-overfit work for free. Scattered iid
colour noise mints **0/100** (the opponent space is large enough — ≈ 6×10⁴ values —
that a coincidental exact 3-collision across 36 cells has probability ≈ 2×10⁻⁶ per
field). A category is minted ONLY if it compresses (§1.1: no minted category that
fails to pay).

**Assignment is a real decode, not a lookup.** Every cell is recognized as its own
minted category at distance 0; an off-prototype colour gets its NEAREST quantum (the
probe at `(6,0)` is assigned to A `(10,0)` at distance 4, not B `(−10,0)` at
distance 16); and a NEW instance of a seen colour is RECOGNIZED — assigned to the
existing category at distance 0 — WITHOUT re-minting (the `Not(Exists)` / epoch
guard), exactly the sd-loop recognize-not-re-mint behaviour.

## AUDIT — is colour categorization IN-CLASS via the sd loop, or the objecthood wall? (§12.4, in-code)

**VERDICT: IN-CLASS.** Colour categorization is low-D colour-space quantization,
NOT objecthood — it reuses the sd loop's DYNAMIC-QUANTIZATION PATTERN as a new
colour-specific seed with NO new Rust. Verified in the source before designing:

- **The sd loop's `ShapeDecode`/`sd_mint_quantum` decode a RELATION-SYSTEM
  signature, not a low-D point.** `shape_decode.rs:1097` (`eval_shape_decode`)
  composes a goal `signature` (`Vec<Value>` of relation tuples) against a
  `ShapeSignature` codebook; `sd_mint_quantum` (`shape_decode_loop.json`) mints a
  `CapabilityAxis` from a residual RELATION set, on ANY residual (only a
  `capability_keys` DEDUP guard — no member-count gate). Pointed at raw colour
  values it would mint one quantum per DISTINCT value — over-minting on a gradient.
  **The sd loop does NOT natively carry an MDL member-count gate.**
- **`space_quantize` (`space_quantize.rs:1`) decomposes NAVIGABLE space
  geometrically** (config-space erosion of a pose belief into maximal boxes over the
  passable region), not a value distribution. A colour cluster is not a connected
  free-space region.
- **BUT the DSL expresses MDL-gated colour-space quantization with NO new Rust.**
  Every primitive evaluates and is used in committed seeds:
  `Count(Filter(NodesOfType(...), var, pred))` (member count —
  `affordance_basis.json`), `Argmin(NodesOfType(...), var, value)` (nearest
  category — `conversation_steering.json`), `Not(Exists ...)` (guards —
  `shape_decode_loop.json`), `Sqrt`/`Minus`/`Times`/`Plus` (opponent distance —
  `vision_colour.json`), `add_node`/`add_edge` + a `Scene.epoch` bump.
- **This is NOT the objecthood wall.** Attaching colour to a BOUND object (object
  re-ID / colour constancy / the full recognition "what" layer) needs a bound object
  — the diagnosed cortex dead end (`VISION_RUNG8E_RESULTS.md`, H1 null). This rung
  quantizes a 2-D colour VALUE space only: no object, no binding, no constancy.

**The contribution:** ONE seed (`vision_colour_identity.json`, flag OFF by default)
whose three rules compute the integer opponent coordinate, mint an MDL-gated
`ColourCategory` quantum where a colour value clusters, and assign each region its
nearest quantum as a categorical sign. NO new Rust; the whole loop is the existing
DSL, the sd-loop mint/recognize/epoch pattern realized for the colour subspace.

## What I predicted, and what I got wrong (§3.7 / §7)

I predicted **E mints exactly 3 categories with MDL 72→42 (1.71×), A holds all
three ways, G mints 0 exactly, N mints 0/100, D is load-bearing, X is inert** —
confirmed on every arm. The three provisos all held: (1) the fixpoint mints exactly
one category per clustered colour; (2) `Count(Filter(NodesOfType))` evaluated the
exact-colour member count; (3) the `assigned_epoch != Scene.epoch` re-decode made
every sign reflect the final codebook.

**WHAT I GOT WRONG — the first cut minted one category PER REGION (36, not 3), and
the run exposed it before I believed anything.** `s.tick()` **batch-applies** rules:
it snapshots ALL matching bindings BEFORE any effect fires, so a `Not(Exists
ColourCategory@this colour)` guard alone reads the PRE-mint state for every
same-colour region and each mints its own category (36 categories, epoch 36, 3
sweeps). The fix — reported here, not silently patched — is a **canonical-
representative guard**: only the top-left (lexicographic `(rrow,rcol)`) region of a
colour may mint, so under batch application exactly ONE region per DISTINCT colour
passes and mints exactly ONE category per colour. This is picking a canonical member
(the blind-spot rung's "single unified rule" lesson), NOT a magic threshold; it was
caught by reading the CATEGORY LIST, not a gate (§1). The MDL member-count gate and
every arm's PASS condition are unchanged — only the intra-pass duplicate hazard was
closed. (No headline was rescued or re-run, §5/§3.6: the mechanism was fixed before
the first believed measurement.)

## Scope — what is NOT shown (§8), and the named frontier

- **This is CATEGORICAL COLOUR (the SIGN / "what colour"), at the EXACT-VALUE /
  INTEGER-COORDINATE grain.** A category is a quantum minted at an integer opponent
  coordinate where the value CLUSTERS (recurs ≥ 3, MDL-paying); a region's sign is
  its nearest minted quantum. The in-frame colour coordinate is INTEGER; the
  continuous lives ONLY in the cross-frame `Sqrt`-distance used to assign a sign
  (`coord_ints` refusing floats stays correct — the frame/continuum invariant).
- **NAMED FRONTIER, NOT this rung — perceptual NEARNESS in MINTING.** Grouping
  SIMILAR-but-not-identical colours across a gap (jittered clusters → one category)
  is the CONTINUOUS CROSS-FRAME comparator ("bins propose, continuous decides") —
  the colour-metric twin of real-angle rotation and sub-integer disparity in the
  sibling rungs. Here MINTING is exact-value; only ASSIGNMENT is nearest. Deferred,
  not attempted.
- **NAMED FRONTIER, NOT this rung — the OBJECTHOOD wall.** Object colour re-ID
  (attaching a colour to a BOUND object), colour CONSTANCY / illuminant-discounting,
  and the full recognition "what" layer need a bound object — the diagnosed cortex
  dead end. Categories here are minted from colour AS PRESENTED; **no constancy is
  claimed**.
- **Do NOT claim this "solves colour identity" or crosses the objecthood wall.** It
  is the colour-categorization SIGN, one honest bounded step downstream of salience.

## Is colour identity a minted, MDL-gated sign? — the plain answer

**Yes.** A colour category is a quantum minted from the 2-D integer opponent-colour
VALUE subspace by the sd loop's dynamic-quantization pattern, MDL-gated: mint a
category where a colour value recurs ≥ 3 times (the member count at which a category
pays for a 2-D colour code, a number that FALLS OUT of d=2), refuse where it doesn't.
A scene with three colour clusters mints exactly three category quanta (MDL 72→42),
every region is assigned its nearest minted quantum as a categorical sign, a seen
colour is recognized not re-minted, a smooth gradient mints zero, and iid noise mints
0/100 — with ZERO new Rust and ZERO magic numbers. **Bounded to** the
exact-value / integer-coordinate class; perceptual nearness in minting (the
continuous colour metric) and object colour re-ID / constancy / the "what" layer are
the named, unreached frontier — the objecthood wall this rung does NOT cross.
