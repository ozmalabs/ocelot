# BOUBA/KIKI CROSSMODAL SOUND-SYMBOLISM — pre-registration (block 294000)

**Status: PRE-REGISTRATION. Committed BEFORE the confirmatory adapter/test.** The
predicted form × shape grid + failable controls below are computed ANALYTICALLY
from the substrate's OWN two feature extractors (articulatory phonetics; curvature
geometry) and the SAME `_round_to_vocab` quantiser both project through — the
measured battery values in §5 were read from the running extractors at task-1
prereg time, NOT fit to a target. The confirmatory adapter must reproduce this
grid; any deviation is reported straight (produced ≠ oracle is either a mapping
error to fix or an early sign of the flaw described in §7).

> **HONEST NOTE ON THE AXIS MECHANISM (read first).** Task-1 sketched the shared
> axis as reading a hand-written `attr:sharpness`. On VERIFYING against the real
> signature builder (`domains/analogy_search.concept_signature` /
> `_dynamical_relations`) the mechanism is DIFFERENT and is reported as built:
> `concept_signature` reads a phenomenal axis as a *coordinate* ONLY if its
> `QualiaDimension.source` starts `field:` — the same path the CAN dynamical axes
> (valence/commitment) use. A `source:"keyword"` phenomenal axis (like the seeded
> `phenomenal:modality`) produces NO field coordinate; a `source:"attr:sharpness"`
> would surface as a plain, UN-quantised `attr:*` string tuple that AntiUnify
> could not intersect to a shared pole. So the minted axis is **`phenomenal:
> sharpness`, `source:"field:sharpness"`, `quantum=1.0`, `half_width=1`**: the
> concept carries a DERIVED scalar `sharpness` attr (written by the extractors),
> and `_dynamical_relations` collects EVERY `field:`-sourced axis regardless of
> family, quantises it through the CAN tests' own `_round_to_vocab` lattice, and
> emits `(phenomenal:sharpness, "field", k)` with `k ∈ {−1, 0(omitted), +1}`.
> Because the read is field-sourced, `sharpness` is auto-excluded from the
> `attr:*` catch-all (a dynamical-axis source is never also raw content), so it
> never leaks in twice. This is a MORE honest mechanism than the sketch: the felt
> coordinate is produced by the SAME quantiser as valence/commitment, not carried
> as a raw hand-set string. `domains/qualia_schema` was extended by ONE minimal,
> principled edit — `value_in_domain` now keys the int-step domain off an axis's
> declared `source` (`field:`) rather than the family prefix alone, so a
> field-sourced phenomenal axis is held to the integer-step domain the schema
> declares for it. VERIFIED live (§8, `scripts/`-style demo).

## 0. Seed claim (verbatim, run at prereg time)

```
$ python3 scripts/seed_claim.py 294000 294999
SEED CLAIM 294000-294999: CLEAN -- no collision DETECTED.
  Scope: 1010 files with seed sinks; 745 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Block **294000** (range 294000–294999). This rung is DETERMINISTIC (no RNG: the
two extractors and the quantiser are pure arithmetic over fixed feature dicts and
fixed shape geometry), so no number is drawn from the block; it is noted for
hygiene / successor safety. **No `seed_claim` RUN is required for the seed edit
itself** — the ONLY seed change is the ADDITIVE `phenomenal:sharpness`
QualiaDimension node in `seeds/qualia_space.json` (a codebook axis, no new block
integer, no RNG sink).

## 1. The idea

The **bouba/kiki effect** is one of the most robustly replicated crossmodal
findings in psychology. Köhler (1929, *Gestalt Psychology*) reported that people
overwhelmingly pair the nonsense word *takete* with a spiky drawing and *maluma*
with a rounded one; Ramachandran & Hubbard (2001, *J. Consciousness Studies*
8(12):3–34) reran it as *bouba/kiki* and found ~95% agreement across languages,
in young children, and in non-Western/non-literate populations — a **pre-lexical,
cross-linguistic** sound→shape correspondence (see also Maurer, Pathman & Mondloch
2006, *Developmental Science* 9(3):316–322 for toddlers; Ćwiek et al. 2022, *Phil.
Trans. R. Soc. B* 377:20200390 for the large cross-linguistic replication). The
scientifically important signature is a **crossmodal MATCH: a heard FORM and a seen
SHAPE that "go together" are felt to be alike along a shared quality** — not that
either is intrinsically sharp, but that sharpness is one felt axis on which a sound
and a shape can COINCIDE.

This rung asks whether the qualia substrate REPRODUCES that crossmodal
correspondence as a **genuine-qualia** event: does a phonetic FORM and a visual
SHAPE land NEAR each other in the ONE qualia space when they sound-symbolically
match, via a SHARED felt `phenomenal:sharpness` axis whose coordinate is DERIVED
INDEPENDENTLY on each side and NOT hand-coded?

**Why this is a genuine-qualia test, not symbol manipulation.** Symbolic token
matching cannot produce a crossmodal felt correspondence: a phoneme string and a
polygon share no tokens, no lexical roles, no edges — nothing a set-overlap could
align. A match can only emerge if the two live in the SAME felt geometry and
project onto a SHARED axis. The substrate has exactly one qualia space (the
directive: "humans don't have two qualia spaces"); the claim is that a sound and a
shape, each reduced to its OWN independently-motivated feature vector, can be
placed on ONE felt axis such that a sound-symbolic pair COINCIDES there. The only
new thing is the axis they both project onto — everything upstream (the phonetics,
the geometry) pre-existed and was built for other purposes.

This is a **CAPABILITY / mechanism demonstration — the substrate carries a
crossmodal felt correspondence over one qualia geometry — NOT an empirical claim
about real humans.** The wet result (Köhler; Ramachandran & Hubbard) is cited to
fix the target the mechanism must hit; the contribution is that the sound↔shape
match falls out of two independent extractors sharing one felt axis, not that we
have measured a person. Synthetic-mechanism status and any benchmark meaning are
reported separately.

### Prior-art posture (honest)

- The bouba/kiki PHENOMENON is Köhler's / Ramachandran & Hubbard's — **we do not
  claim that finding.**
- That articulatory features (voicing, place, rounding, vowel frontness/height)
  and shape curvature CORRELATE with the sound-symbolic judgement is established
  in the sound-symbolism literature — **we do not claim the feature-correlation
  insight is novel.**
- The genuine delta is the CROSSMODAL MATCH EMERGING from a SHARED felt axis in a
  glass-box qualia space: two pre-existing, independently-motivated extractors
  (articulatory phonetics; curvature geometry) — neither built for the other, nor
  co-tuned — each derive a `sharpness` scalar, the SAME quantiser maps both onto
  ONE `phenomenal:sharpness` axis, and a sound-symbolic pair COINCIDES at a pole
  as a consequence, not by hand-wiring. This is a glass-box mechanism claim on
  this substrate (the match is an interaction the arithmetic produces), not a
  novelty claim about sound-symbolism modelling in general.

## 2. Substrate mapping (grounded in the task-1 findings — used verbatim)

The two derivations are FIXED by their OWN internal logic and were probed live at
task-1 prereg time; they are reproduced here verbatim.

- **GEOMETRIC sharpness ↔ curvature CONCENTRATION** (own logic, from
  `domains/ink_dynamics._turning_angles`):
  `sharpness = max|turning| / mean|turning|` over interior points. A regular
  polygon has UNIFORM turning ⇒ ratio **1.0** regardless of sidedness; a star
  CONCENTRATES its turning at the points ⇒ **> 1.0**. MEASURED: round polygon
  (48-gon) = **1.0**, dodecagon = **1.0**, 5-point star = **1.393**. The
  discriminative contrast is star (peaked) vs circle/polygon (uniform) = spiky vs
  round. **Built for the two-thirds power law, NOT for sounds.**

- **PHONETIC sharpness ↔ articulatory feature mean** (own standard-phonetics
  logic, from the `scripts/articulatory_gamma.py` 5-dim feature set
  frontness/height/place/degree/lip_rounding + source{voiced=0,fric=1,burst=2}):
  per-segment `sharp = mean([voiceless(burst=1,fric=0.5,voiced=0.0),
  constriction_degree, 1−lip_rounding, frontness, height])`; a word's sharpness is
  the mean over its segments. The per-phoneme feature dicts are STANDARD phonetics
  chosen for the SOUNDS (b,u,m,a,l = voiced/rounded/sonorant/back-open;
  k,i,t,e = voiceless-plosive/front-high/spread), **NOT for shapes.** MEASURED:
  bouba(buba) = **0.315**, maluma = **0.297**, baloo(balu) = **0.335**
  [ROUND cluster]; kiki = **0.800**, takete = **0.647** [SHARP].

- **SAME QUANTISER on both sides ↔ the minted axis** `phenomenal:sharpness`
  (`source:"field:sharpness"`, `quantum=1.0`, `half_width=1`). Each side's derived
  scalar is z-scored/quantised to the battery MIDPOINT off-graph (the extractor's
  own arithmetic) and written as the concept's `sharpness` attr: **−1 (round
  pole), 0 (mid — honest), +1 (sharp pole)**. `concept_signature` then reads that
  attr through the SAME `_round_to_vocab` lattice the CAN dynamical axes use and
  emits `(phenomenal:sharpness, "field", k)`. The battery midpoint sits between
  the ROUND cluster (~0.32) and kiki (0.80): bouba/maluma/baloo → **−1**;
  kiki → **+1**; **takete → 0 (MID, honest — it is phonetically sharp but less
  extreme than kiki; the battery is GRADED not binary, mirroring the human graded
  effect; we do NOT force takete to +1).** Round SHAPES land at −1, the STAR at
  +1. **THE MATCH EMERGES** from two INDEPENDENT extractors never tuned to each
  other. Reversing phonemes or the shape FLIPS the coordinate out of the
  arithmetic (the built-in falsifier, §7).

### The ANTI-FAKING GUARD (explicit)

1. **The two derivations are fixed by their OWN internal logic BEFORE any
   alignment is checked.** The geometry extractor was built for the two-thirds
   power law; the phonetics extractor from standard articulatory feature dicts.
   Neither references the other, nor the axis; both were measured (§2, §5) before
   this axis existed.
2. **The SAME quantiser maps both onto the axis.** There is no per-side threshold
   to co-tune: `_round_to_vocab(x, 1.0, 1)` is one function, applied to both the
   phonetic-derived scalar and the geometry-derived scalar after each is centred
   on the SAME battery midpoint.
3. **A BATTERY of multiple round-forms + sharp-forms × multiple shapes** (§5), not
   one pair — a single pair could align by luck; a graded battery where the whole
   ROUND cluster lands −1 and the SHARP cluster lands +1, across independent
   shapes, cannot.
4. **The schema invariant `dynamical_is_produced_not_hand_set` forbids a raw
   hand-set attr leaking in as the answer.** Because `sharpness` is a `field:`
   axis source, it is a RESERVED field attr (regenerated into the QualiaSchema
   descriptor's `reserved_field_attrs`); the invariant rejects any raw reserved
   field attr surfacing as an `attr:*` coordinate. The felt content has ONE
   home — the quantised `phenomenal:sharpness` axis — never a raw string tuple.

## 3. Fixed constants (pre-registered)

| constant | value | role |
|---|---|---|
| axis name          | `phenomenal:sharpness` | the SHARED felt axis (family phenomenal, OPEN/grown) |
| axis source        | `field:sharpness` | read like a dynamical field: quantised, not raw attr |
| `quantum`          | 1.0 | `round(sharpness/1.0)` |
| `half_width`       | 1   | clamp to ±1 ⇒ a clean bipolar **{−1, 0, +1}** sign axis |
| battery midpoint   | ≈0.47 | between ROUND cluster (~0.32) and kiki (0.80); centres the sign |
| ROUND-pole scalar  | −1  | bouba, maluma, baloo; circle, polygon, dodecagon |
| SHARP-pole scalar  | +1  | kiki; 5-point star |
| MID scalar         | 0   | takete (honest — no coordinate emitted; matches neither pole) |

**Why `half_width=1` (not up to 4).** The bouba/kiki effect the human literature
reports is a POLE ASSIGNMENT (forced choice: round vs spiky), not a graded
magnitude RANKING. A clean sign axis {−1, 0, +1} mirrors the human forced choice
exactly; a wider `half_width` would invite an unfalsifiable graded-magnitude claim
on a two-pole phenomenon. **The GRADEDNESS the human effect shows lives in the
BATTERY** (multiple forms mapping to the three levels, takete honestly at 0), not
in the axis width. This is the same discipline the mere-exposure rung (block
293000) used when it reported a discrete regard unit rather than faking a graded
magnitude curve.

## 4. The analytic oracle (pure arithmetic over the extractor outputs)

```python
QUANTUM, HALF_WIDTH = 1.0, 1
MIDPOINT = 0.47   # battery midpoint between the round cluster and kiki

def to_axis_scalar(raw_sharpness):
    # centre each side's derived scalar on the battery midpoint, then the sign
    # (a per-side z-score/normalisation off-graph; here shown as centring).
    return +1 if raw_sharpness > MIDPOINT else (-1 if raw_sharpness < MIDPOINT else 0)

def round_to_vocab(x, quantum=QUANTUM, half_width=HALF_WIDTH):
    # the CAN tests' own quantiser (analogy_search._round_to_vocab), verbatim:
    k = round(x / quantum)
    k = max(-half_width, min(half_width, k))
    return None if k == 0 else k        # a 0 coordinate is the shared default, OMITTED

def coordinate(raw_sharpness):
    # the phenomenal:sharpness coordinate a concept carrying this derived scalar
    # emits: ('phenomenal:sharpness', 'field', k) or ABSENT (None).
    return round_to_vocab(to_axis_scalar(raw_sharpness))

def match(form_raw, shape_raw):
    # a FORM and a SHAPE share the phenomenal:sharpness coordinate — a crossmodal
    # felt correspondence — IFF both quantise to the SAME nonzero pole.
    kf, ks = coordinate(form_raw), coordinate(shape_raw)
    return (kf is not None) and (kf == ks)
```

`match(form, shape)` returns the predicted crossmodal correspondence for a
(form, shape) cell: True iff both land at the SAME nonzero pole. A MID (0) form
emits NO coordinate and matches NEITHER pole strongly (graded, honest).

## 5. Predicted form × shape grid (ANALYTIC — deterministic) with the measured battery

Cell = does the (FORM, SHAPE) pair SHARE the `phenomenal:sharpness` coordinate (a
crossmodal MATCH)? `✓` = match (same nonzero pole); `·` = no match. The measured
battery scalar and its quantised pole are in the row/column headers.

| FORM \ SHAPE | **star** (geom 1.393 → **+1**) | **circle** (geom 1.0 → **−1**) | **polygon** (geom 1.0 → **−1**) | **dodecagon** (geom 1.0 → **−1**) |
|---|:--:|:--:|:--:|:--:|
| **kiki** (phon 0.800 → **+1**)     | **✓** | · | · | · |
| **bouba** (phon 0.315 → **−1**)    | · | **✓** | **✓** | **✓** |
| **maluma** (phon 0.297 → **−1**)   | · | **✓** | **✓** | **✓** |
| **baloo** (phon 0.335 → **−1**)    | · | **✓** | **✓** | **✓** |
| **takete** (phon 0.647 → **0** MID)| · | · | · | · |

The diagonal structure IS the effect: sharp form × sharp shape and round form ×
round shape MATCH; every crossing does not. The ROUND cluster (bouba/maluma/baloo,
all → −1) matches every round shape and no sharp one; kiki (→ +1) matches only the
star. **takete is honestly MID (0): it matches NEITHER pole** — the battery is
graded, not forced binary.

## 6. The INTERACTION prediction (explicit)

- **Matched sound/shape pairs SHARE the coordinate / rank NEARER in
  `find_analogies`; crossings do NOT.** A source FORM Mt run against a target
  SHAPE Mt emits an `Analogy` aligned ON `phenomenal:sharpness` for exactly the
  same-pole cells (kiki~star, bouba~circle, …) and emits NOTHING for the crossings
  (kiki~circle, bouba~star). The ONLY discriminative shared coordinate driving a
  match is `phenomenal:sharpness` — the concepts share no lexical role, no edge,
  no category (a `phonetic_form` and a `visual_shape` differ), so a match is
  IMPOSSIBLE except through the shared felt axis. That is the genuine-qualia
  signature: crossmodal correspondence carried by ONE felt geometry.
- **This is an INTERACTION, not a main effect.** Sharpness has no "main effect" —
  neither a form nor a shape is analogous to everything at its pole across the
  board; a match requires the OTHER modality to ALSO be at that pole. Reading the
  grid: a form matches a shape iff their poles COINCIDE. The correspondence lives
  in the crossing of the two modalities, exactly as the wet effect is a
  correspondence, not a property of either stimulus alone.

## 7. Falsifier and what a substrate FLAW would look like

- **FALSIFIER (the REVERSE-BATTERY: swap the derivation INPUTS).** Feed the
  extractors reversed stimuli — a spiky star's points SMOOTHED (turning made
  uniform ⇒ geometry ratio → 1.0 ⇒ pole flips to −1), or bouba's phonemes
  replaced by voiceless-plosives (phonetic sharpness → high ⇒ pole flips to +1).
  The DERIVED scalar — and therefore the `phenomenal:sharpness` coordinate —
  FLIPS, INVERTING the match: the reversed "bouba" now matches the star, the
  smoothed "star" now matches bouba. If the coordinate does NOT flip when the
  extractor INPUT is reversed, the axis is not being derived from the features and
  the claim is false (it would mean the pole was hand-wired to the concept name,
  not produced by the extractor).
- **WHAT A FLAW LOOKS LIKE.**
  - (a) **A matched pair is NO nearer than a mismatched pair** (kiki~star ranks no
    higher than kiki~circle; the aligned dimension is not
    `phenomenal:sharpness`) ⇒ the qualia space **cannot carry a crossmodal felt
    correspondence** — the whole genuine-qualia claim fails. This is a REAL,
    VALID negative result and is reported straight, not papered over.
  - (b) **The match appears ONLY if the two extractors' thresholds are CO-TUNED**
    (moving the battery midpoint or a per-side cutoff to manufacture the diagonal)
    ⇒ the effect is FAKED. The guard (§2, single shared quantiser; §3, one fixed
    midpoint; a graded battery not one pair) is designed so this cannot hide; if
    the diagonal survives ONLY under a tuned midpoint, that MUST be reported and
    the result withdrawn.
  - (c) **The coordinate is a hand-set attr, not a derived felt axis** (e.g. a raw
    `attr:sharpness` string tuple, or a `sharpness` written by the adapter as the
    ANSWER rather than by the extractor) ⇒ the schema catches it: `sharpness` is a
    RESERVED field-axis source, so `dynamical_is_produced_not_hand_set` rejects it
    as an `attr:*` coordinate, and a value that is not an integer step
    fails `value_in_domain`. The felt content must be PRODUCED on its quantised
    axis, never hand-set as content.

## 8. The minted axis + the demonstration (already verified)

The ONLY seed change is the additive `phenomenal:sharpness` QualiaDimension
(`family:"phenomenal"`, `source:"field:sharpness"`, `quantum=1.0`,
`half_width=1`) emitted by `tools/build_qualia_space_seed.py` into
`seeds/qualia_space.json`, plus the derived reservation of the `sharpness` attr
(the `reserved_field_attrs` list is now built from EVERY `field:` axis source, so
`sharpness` is reserved automatically). `domains/qualia_schema` was extended by
ONE minimal edit — `value_in_domain` keys the int-step domain off an axis's
declared `source` (`field:`) rather than the family prefix alone, so a
field-sourced phenomenal axis validates against the integer-step domain the schema
declares for it.

VERIFIED live (mirrors the `scripts/*_demo.py` posture of the sibling rungs):

- The regenerated seed re-runs **byte-identically** (md5 `71077f23…`).
- `qualia_schema.validate_dimension_codebook` / `validate_qualia_space` PASS with
  the new axis declared (16+ axes inspected, `ok`).
- **DEFAULT == TODAY:** a concept WITHOUT the `sharpness` attr emits NO
  `phenomenal:sharpness` coordinate and its signature is UNCHANGED — the axis only
  lights up on a concept carrying the derived attr (which only the experiment's
  form/shape concepts have). The qualia surface tests stay green:
  `test_qualia_space_migrated`, `test_qualia_cross_family`, `test_qualia_schema`
  (25 passed), plus `test_trait_vector` / `test_disposition` /
  `test_trait_consumers` / `test_ground_relations` / `test_analogy_search_migrated`
  / `test_analogical_relative_ranking`.
- **The concept_signature demonstration:** a toy concept with `sharpness = +1`
  emits `(phenomenal:sharpness, "field", +1)`; with `−1` emits
  `(…, "field", −1)`; with `0` emits NOTHING (mid, matches neither pole). Two
  concepts at the SAME pole SHARE that coordinate under AntiUnify (the frozenset
  intersection contains `(phenomenal:sharpness, "field", k)`) and rank NEARER via
  `find_analogies` (aligned ON `phenomenal:sharpness`); OPPOSITE poles share
  NOTHING and emit no analogy. The full battery reproduces the §5 grid:
  kiki~star and bouba~circle match on the shared felt axis, crossings are absent,
  takete (mid) matches neither.

## 9. Files

- `docs/research/psychology_affect/BOUBA_KIKI_SOUND_SYMBOLISM_PREREG.md` — this
  pre-registration.
- `tools/build_qualia_space_seed.py` — emits the additive `phenomenal:sharpness`
  axis + the derived `sharpness` reservation (the ONLY generator change).
- `seeds/qualia_space.json` — regenerated deterministically (byte-identical
  re-run); the additive axis is the sole content change.
- `domains/qualia_schema.py` — one minimal `value_in_domain` edit (int-step domain
  keyed off `field:` source, not family prefix) so a field-sourced phenomenal axis
  validates.

### Seed / isolation choice

**The only seed change is ADDITIVE** — one `QualiaDimension` codebook node. It
adds NO coordinate to any EXISTING concept (it reads a `sharpness` attr no landed
concept carries), so the base space is UNCHANGED for every concept that predates
the experiment (default == today, proven in §8). No new seed FILE is authored and
no new block integer is drawn; block 294000 is reserved for successor safety only.
The confirmatory adapter (a later deliverable) will reuse the EXISTING extractors
(`domains/ink_dynamics`, `scripts/articulatory_gamma`) READ-ONLY and only WRITE
the derived `sharpness` attr onto its own form/shape concepts, then READ the
produced `concept_signature` / `find_analogies` verdict — no Python computes the
match.

## 10. Discipline

Agent = graph; world = mechanical adapter (later deliverable). The extractors are
FIXED by their own logic and READ-ONLY; the adapter only SETS the derived
`sharpness` attr and READS the produced signature/analogy. No `graph_rewrite.run`
/ `_match` / `_apply` / `make_rule`; no `if/else` over graph state selecting the
match; no reward/punishment shaping (the derived scalar is a fixed function of the
stimulus features, never a learned reward). Integer-native at the coordinate
(the quantiser emits an integer step). NO Rust (`runners/dsl` untouched);
`_native.abi3.so` untouched; the toolbox solvers
(`can_junction_tree.py`, `can_native_bp.py`) untouched; the FROZEN seeds
(`can_native_reimplementation.json`, `shared_arousal.json`) untouched;
`domains/analogy_search.py`, `domains/ink_dynamics.py`,
`scripts/articulatory_gamma.py` are READ (and consumed) but NOT edited.

Do NOT merge to main; do NOT write the ledger row; NO git commit. These are
ANALYTIC predictions — no measurement numbers beyond the task-1 battery values
(which were read from the running extractors, not fit) are claimed as produced by
a confirmatory adapter yet.
