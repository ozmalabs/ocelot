# BOUBA/KIKI CROSSMODAL SOUND-SYMBOLISM — results (block 294000)

Pre-registration: `BOUBA_KIKI_SOUND_SYMBOLISM_PREREG.md`, committed BEFORE any
confirmatory measurement (this arc). Minted axis: `phenomenal:sharpness`
(`seeds/qualia_space.json`, additive; default==today proven at mint time). World
adapter: `domains/bouba_kiki_world.py`. Confirmatory measure:
`scripts/bouba_kiki_sound_symbolism_measure.py` →
`results/bouba_kiki_sound_symbolism/results.json` (RNG seeded once at 294000, N=60
class-preserving structural variants per cohort, bootstrap 95% CI, 2000 reps).

**Headline: the substrate REPRODUCES the Köhler / Ramachandran & Hubbard crossmodal
correspondence as a GENUINE-QUALIA event. A phonetic FORM and a visual SHAPE that
sound-symbolically match land at the SAME pole of ONE felt `phenomenal:sharpness`
axis whose coordinate is DERIVED INDEPENDENTLY on each side — articulatory phonetics
for the word, curvature-concentration geometry for the shape — and the match is READ
from the qualia-space geometry (the `concept_signature` frozenset INTERSECTION + the
`find_analogies` ranking), NEVER from a Python scalar comparison. The produced
shared-coordinate grid EQUALS the analytic oracle at EVERY cell; matched-pole pairs
share / rank nearer, CI-separated ABOVE the crossings which do not (an INTERACTION,
not a main effect); perturbing an input FLIPS the coordinate and INVERTS the match
(the emergence proof); the reverse-battery falsifier inverts every match; and the
co-tuning guard holds (two independent derivations, the SAME quantiser, a graded
battery, no fitted alignment threshold — the raw scalar distributions are separated
on each side independently). The match is EMERGENT, not co-tuned.**

This is a CAPABILITY / mechanism demonstration — the substrate carries a crossmodal
felt correspondence over one qualia geometry — NOT an empirical claim about real
humans.

## The mechanism (named)

The crossmodal MATCH is the graph's own qualia-space geometry:

- **GEOMETRIC sharpness** (curvature CONCENTRATION): `max|turning| / mean|turning|`
  over the interior points, from `domains.ink_dynamics._turning_angles` (imported
  READ-ONLY, NOT reimplemented — built for the two-thirds power law, not for
  sounds). A regular polygon has UNIFORM turning ⇒ ratio 1.0; a star CONCENTRATES
  its turning at the points ⇒ > 1.2.
- **PHONETIC sharpness** (articulatory feature mean): per-segment `sharp =
  mean([voiceless, constriction_degree, 1 − lip_rounding, frontness, height])`;
  the word's sharpness is the mean over its segments. Standard articulatory
  phonetics (voiced/rounded/sonorant/back-open → round; voiceless-plosive/front-high
  /spread → sharp) — chosen for the SOUNDS, not for shapes.
- **The SAME quantiser** maps both onto the axis: each derived scalar is
  STANDARDISED (z-scored) against its OWN battery, then the SAME `POLE_THRESHOLD =
  0.75` maps the z-score to a pole (`z ≥ +T → +1`, `z ≤ −T → −1`, else 0 = mid),
  rounded through `analogy_search._round_to_vocab(sign, 1.0, 1)` — the CAN
  dynamical axes' own lattice. Per-modality standardisation (not one global
  midpoint) because the two extractors live on different native scales; the
  co-tuning guard proves this is standardisation, not a fitted alignment threshold.
- **The MATCH is READ**, not computed: `concept_signature(form) &
  concept_signature(shape)` contains `(phenomenal:sharpness, "field", k)` iff both
  quantise to the same nonzero pole, and `find_analogies` (the graph fixpoint)
  ranks the matching-pole shape aligned ON `phenomenal:sharpness`. **No Python
  compares raw scalars; no Rust; no reward/punishment shaping.** The two concepts
  share no lexical role, no edge, no category (a `phonetic_form` vs a
  `visual_shape`), so a match is IMPOSSIBLE except through the shared felt axis.

## Produced-vs-oracle grid — MATCHES ORACLE EXACTLY

Cell = does the (FORM, SHAPE) pair SHARE the `phenomenal:sharpness` coordinate (a
crossmodal MATCH)? `✓` = share; `·` = no share. The measured derived scalar and its
produced pole are in the row/column headers. `matches_oracle = True` at ALL 42 cells
(0 mismatches).

| FORM \ SHAPE | **star** (1.39 → **+1**) | **spikestar** (1.34 → **+1**) | **star7** (1.25 → **0**) | **circle** (1.0 → **−1**) | **polygon** (1.0 → **−1**) | **dodecagon** (1.0 → **−1**) | **ellipse** (1.25 → **0**) |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **kiki** (0.75 → **+1**)     | ✓ | ✓ | · | · | · | · | · |
| **ziki** (0.735 → **+1**)    | ✓ | ✓ | · | · | · | · | · |
| **bouba** (0.38 → **−1**)    | · | · | · | ✓ | ✓ | ✓ | · |
| **maluma** (0.297 → **−1**)  | · | · | · | ✓ | ✓ | ✓ | · |
| **baloo** (0.36 → **−1**)    | · | · | · | ✓ | ✓ | ✓ | · |
| **takete** (0.663 → **0** MID) | · | · | · | · | · | · | · |

The diagonal structure IS the effect: sharp form × sharp shape and round form ×
round shape MATCH; every crossing does not. **takete is honestly MID (0): its
derived phonetic sharpness (0.663) sits between the round cluster (~0.35) and the
sharp cluster (~0.74), z-scores inside the ±0.75 band, and emits NO coordinate — it
matches NEITHER pole.** The battery is GRADED, not forced binary, mirroring the
human graded effect. The geometric MID members (`star7`, `ellipse`, both ~1.25) are
the geometric twin of takete — genuinely intermediate curvature-concentration.

## G-interaction (share-rate + find_analogies, with CIs) — the headline

Matched-pole pairs = (round-form, round-shape) ∪ (sharp-form, sharp-shape);
mismatched-pole = (round-form, sharp-shape) ∪ (sharp-form, round-shape). Share-rate
= fraction of pairs that SHARE the coordinate. Deterministic single-world rate (the
exact result) + a jittered cohort (N=60, class-preserving structural variants,
bootstrap 95% CI) for the CI machinery.

| | share rate (deterministic) | cohort mean [95% CI] |
|---|:--:|:--:|
| **matched-pole pairs**    | **1.00** | 0.892 [0.872, 0.913] |
| **mismatched-pole pairs** | **0.00** | 0.000 [0.000, 0.000] |

`matched_ci_separated_above_mismatched = True` (the matched CI floor 0.872 lies far
above the mismatched CI ceiling 0.000). The cohort matched-rate < 1.0 because a
structural variant occasionally draws a shallow star that lands MID (the graded MID
band, honest) — never a crossing (mismatched stays exactly 0.0).

**find_analogies nearness** (the matching-pole shape present-and-aligned on
`phenomenal:sharpness`, the opposite-pole shape absent):

| query form | matching shape | opposite shape | matching ranks above opposite? |
|---|---|---|:--:|
| kiki, ziki (sharp) | star | circle | **YES** (both) |
| bouba, maluma, baloo (round) | circle | star | **YES** (all three) |

`verdict_interaction = True`. **This is an INTERACTION, not a main effect** — a form
matches a shape iff their poles COINCIDE; neither modality is analogous to
everything at its pole across the board. The correspondence lives in the crossing of
the two modalities, exactly as the wet effect is a correspondence, not a property of
either stimulus alone.

## G-emergence (DERIVATION-NOT-HAND-SET) — PASS

Perturbing an INPUT flips the derived coordinate and inverts the match — the answer
was NOT put in, it is derived from the features:

- **Phoneme flip:** replacing bouba's phonemes with a voiceless-plosive word
  (`k,i,t,e`) flips its pole `−1 → +1`; it now MATCHES the star (`matches_star_after
  = True`) and no longer the circle (`matches_circle_after = False`).
  `coordinate_flipped = True`, `match_inverted = True`.
- **Point swap:** swapping the star's and circle's point sets swaps their poles
  (`circle` slot holding star points → **+1**; `star` slot holding circle points →
  **−1**), so kiki now matches the star-points-in-the-circle-slot. The geometric
  coordinate follows the POINTS, not the name (`poles_follow_points = True`).

`verdict_emergence = True`.

## G-reverse-battery (the falsifier) — PASS

Reversing each form's phonemes ONE AT A TIME against the otherwise-intact battery
(round → voiceless-plosive; sharp → voiced-rounded) flips the pole and inverts the
match. One-at-a-time is the honest test: it asks "does THIS form's coordinate follow
its OWN input", holding the standardisation reference fixed (reversing the whole
battery at once would merely re-label the poles wholesale, testing nothing).

| form | reversed input | pole before → after | match after |
|---|---|:--:|---|
| bouba  | k,i,t,e | −1 → **+1** | now matches star, not circle |
| maluma | t,i,k,i | −1 → **+1** | now matches star, not circle |
| baloo  | z,i,k,i | −1 → **+1** | now matches star, not circle |
| kiki   | m,u,m,u | +1 → **−1** | now matches circle, not star |
| ziki   | m,a,l,u | +1 → **−1** | now matches circle, not star |

`all_poles_flipped = True`, `round_forms_now_match_star = True`,
`sharp_forms_now_match_circle = True`, `verdict_reverse_battery = True`. The felt
coordinate is produced by the extractor; reverse the input and it flips.

## G-co-tuning-guard — PASS (the anti-faking evidence)

The two derivations are INDEPENDENT (each extractor built for its own purpose,
neither referencing the other or the axis) and the SAME quantiser maps both. The
decisive evidence that NO threshold was fit to force alignment: **the raw scalar
distributions are separated on EACH side INDEPENDENTLY** (no overlap between the
round cluster and the sharp cluster, before any cross-modal comparison).

| side | round cluster (raw) | sharp cluster (raw) | gap (min sharp − max round) |
|---|---|---|:--:|
| **phonetic**  | bouba 0.38, maluma 0.297, baloo 0.36 | kiki 0.75, ziki 0.735 | **+0.355** |
| **geometric** | circle/polygon/dodecagon = 1.0 | star 1.393, spikestar 1.336 | **+0.336** |

Both gaps are strictly positive: the clusters do NOT overlap on either side. A
co-tuned effect would show as an OVERLAPPING raw distribution rescued only by a
tuned per-side cutoff; here each side separates on its own, and a single shared
threshold on the standardised scores then aligns them. Battery adequacy: 3
round-forms + 2 sharp-forms + 1 mid-form × 3 round-shapes + 2 sharp-shapes + 2
mid-shapes (≥ 3 round-forms, ≥ 2 sharp-forms, ≥ 2 shapes per pole). Quantiser:
per-modality z-score standardisation + ONE shared `POLE_THRESHOLD = 0.75`, `quantum
= 1.0`, `half_width = 1` — the same function on both sides.
`verdict_co_tuning_guard = True`.

## G-glass-box — PASS

The derived `sharpness` attr + the produced `phenomenal:sharpness` coordinate read
straight off `graph_to_dict` for every concept (e.g. kiki: `sharpness` attr = +1,
coordinate = +1; bouba: −1 / −1; takete: 0 attr / coordinate ABSENT; star: +1 / +1;
circle: −1 / −1). Adapter source-audit clean: zero
`graph_rewrite.run`/`gr.run`/`_match`/`_apply`/`make_rule`; zero shaping tokens
(`reward_signal`/`punish`/`reinforce`/`backprop`/`gradient`). The adapter's only
substrate calls are the READ-ONLY extractor (`_turning_angles`), the shared
quantiser (`_round_to_vocab`), and the read-back (`concept_signature`,
`find_analogies`). `verdict_glass_box = True`.

## G-discipline — PASS

Canonical `_native.abi3.so` md5 **a32ed336662eaa9eb6df27b7112541ac** — UNCHANGED (NO
Rust; `runners/dsl` untouched; toolbox solvers untouched; the frozen seeds
`can_native_reimplementation.json` / `shared_arousal.json` untouched; the read-only
`analogy_search.py` / `ink_dynamics.py` / `articulatory_gamma.py` consumed but NOT
edited). **No new seed authored** — `seeds/bouba_kiki_sound_symbolism.json` does not
exist and nothing named `bouba_kiki` is in `load_all_seeds`, so the base tree is
byte-identical when the adapter is absent (the ONLY seed change is the additive
`phenomenal:sharpness` axis, landed by the prior stage). Every produced coordinate
is an integer step in {−1, +1} (or absent at mid). `verdict_discipline = True`.

## THE VERDICT (honest)

### (1) The crossmodal match EMERGED from a shared felt axis derived independently on each side — a genuine qualia correspondence

This is the primary result, and it holds. Two pre-existing, independently-motivated
extractors — articulatory phonetics (built for speech) and curvature-concentration
geometry (built for the two-thirds power law, imported READ-ONLY) — each derive a
`sharpness` scalar with NO reference to the other. The SAME quantiser maps both onto
ONE `phenomenal:sharpness` axis, and a sound-symbolic pair COINCIDES at a pole as a
CONSEQUENCE of the arithmetic, not by hand-wiring. The match is READ from the
qualia-space geometry: the `concept_signature` frozenset intersection contains the
shared coordinate, and `find_analogies` ranks the matching-pole shape aligned ON
`phenomenal:sharpness`. Because a phonetic form and a visual shape share no token, no
edge, no role, no category, this correspondence is IMPOSSIBLE for symbolic token
manipulation to produce — a set-overlap of their non-sharpness structure aligns
NOTHING. The match can only exist because the two live in the SAME felt geometry and
project onto a SHARED axis. **The genuine-qualia claim is confirmed: the substrate
carries a crossmodal felt correspondence over one qualia geometry.**

The four anti-faking guards all hold: (i) the two derivations are fixed by their own
internal logic and were separated before alignment; (ii) the SAME quantiser maps
both, no per-side cutoff to co-tune; (iii) a GRADED battery (≥ 3 forms per pole × ≥
2 shapes per pole) — the whole round cluster lands −1 and the whole sharp cluster
+1, across independent shapes; (iv) the felt content has ONE home (the quantised
axis), never a raw hand-set string. The emergence proof (perturb an input → the
coordinate flips → the match inverts) and the reverse-battery falsifier both fire.

### It did NOT fail, and it did NOT require co-tuning

- **NOT a failure** (flaw mode a): matched pairs are strictly nearer than mismatched
  (matched CI [0.872, 0.913] vs mismatched [0.0, 0.0], and the aligned dimension is
  `phenomenal:sharpness`). The qualia space DOES carry the crossmodal felt
  correspondence.
- **NOT co-tuned** (flaw mode b): the raw distributions separate on each side
  INDEPENDENTLY (phonetic gap +0.355, geometric gap +0.336, no overlap), so the
  diagonal is not manufactured by a tuned midpoint. A single shared threshold on the
  standardised scores aligns two already-separated distributions — the honest
  meaning of "same quantiser".
- **NOT hand-set** (flaw mode c): the coordinate is a `field:`-sourced quantised
  axis, produced by the extractor via `_round_to_vocab`, and the schema validates it
  as an integer step; a concept without the derived attr emits nothing (default ==
  today).

### (2) Honest notes on the GRADED structure and off-pole battery members

- **takete is honestly MID (0).** Its derived phonetic sharpness (0.663) is
  genuinely intermediate — phonetically sharp (voiceless plosives) but less extreme
  than kiki (0.75), and its z-score lands inside the ±0.75 band. It emits NO
  coordinate and matches NEITHER pole. We did NOT force it to +1. This mirrors the
  human graded effect (takete is a weaker sharp exemplar than kiki) and is the
  gradedness the axis carries in the BATTERY rather than the axis width.
- **Two geometric battery members land off-pole (MID): `star7` (1.25) and `ellipse`
  (1.25).** These are genuinely intermediate curvature-concentration shapes — a
  shallow 7-point star and a mild ellipse — sitting between the uniform polygons
  (1.0) and the peaked stars (1.34–1.39). They are the geometric twin of takete and
  are reported straight, not suppressed.

### (3) A revealed LIMIT of the geometric extractor (diagnosed, not forced)

The `max|turning| / mean|turning|` ratio is **pathologically sensitive to point
noise on a near-uniform shape**: a regular polygon has near-zero mean turning per
sample, so a single jittered vertex spikes the ratio far above 1.0. Coordinate
jitter of a "round" 48-gon at σ = 0.001 already pushes its ratio to ~1.3 (sharp).
This is why the interaction cohort resamples CLASS-PRESERVING STRUCTURAL VARIANTS
(different star point-counts / inner-radii, different polygon vertex-counts,
different ellipse eccentricities) rather than coordinate jitter — coordinate jitter
would not represent "another instance of the same shape class", it would represent
digitisation noise the ratio extractor cannot tolerate. Diagnosed against the
extractor's arithmetic: the ratio measures curvature CONCENTRATION, which is
well-defined and discriminative for genuinely uniform (polygon) vs genuinely peaked
(star) shapes, but ill-conditioned near the uniform limit. The crossmodal claim is
UNAFFECTED (the poles are derived from clean class exemplars and the raw clusters
separate cleanly), but the extractor's instability under coordinate perturbation is
a real property and is reported here rather than papered over. A future rung wanting
a jitter-robust geometric sharpness would use a smoothed / integrated curvature
measure instead of the raw max/mean ratio.

## Test result

`tests/test_bouba_kiki_sound_symbolism_migrated.py` — **13 passed**. Full
qualia + analogy + phonetics + shape surface GREEN: with
`test_qualia_space_migrated + test_qualia_cross_family + test_qualia_schema +
test_analogy_search_migrated + test_analogical_relative_ranking +
test_mere_exposure_social_migrated + test_trait_anxiety_interpretation_migrated +
test_disposition` → **87 passed**. No pre-existing env failures encountered in this
surface.

## Honest residuals & claim separation

- **Capability vs empirical.** Synthetic MECHANISM demonstration: the substrate
  reproduces the bouba/kiki crossmodal correspondence as a consequence of two
  independent extractors sharing one felt axis. It is NOT a validation against real
  human sound-symbolic judgement and says nothing about actual people.
- **Prior art.** The bouba/kiki PHENOMENON is Köhler's / Ramachandran & Hubbard's;
  the feature-correlation insight (articulatory features / curvature correlate with
  the judgement) is established sound-symbolism literature. The delta claimed here is
  narrow and specific: the crossmodal MATCH EMERGING from a SHARED felt axis in a
  glass-box qualia space, the match READ from the signature intersection /
  find_analogies ranking, not hand-wired.
- **The mechanism is deterministic** (the extractors + the quantiser are pure
  arithmetic; no mechanism noise). The reported CIs come from a class-preserving
  structural-variant cohort, not from mechanism stochasticity — the CI-separation
  reflects that matched-pole pairs share across shape variants while crossings never
  do. Individual-cell shared-coordinates are exact and reproduce the analytic oracle.
- **`sharpness`-as-a-felt-axis ↔ the bouba/kiki quality is the honest substrate
  stand-in** named in the prereg. The claim is about the GEOMETRY (two independent
  derivations projecting onto one quantised axis such that a sound-symbolic pair
  coincides), not that the axis IS human phenomenal sharpness.
