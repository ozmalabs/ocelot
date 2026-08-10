# VISION — COLOUR SALIENCE: pop-out for the EQUILUMINANT target (pre-registration)

*Written and COMMITTED before the confirmatory run (PROTOCOL §3). Seeds
**34000–34999** (declared below). 12000–33999 burned/untouched by this rung.*

## 0. The claim, and the audit that precedes it

Colour is the pop-out channel exactly where luminance salience is **zero**. A
near-**equiluminant** target (same luminance as its surround, invisible to the
luminance conspicuity of the render/stream) has high **cone-opponent** contrast
against its surround, so it becomes salient via COLOUR and is streamed in by the
stream's budget `Argmax`; a luminance-only salience MISSES it. This is the "ripe
fruit against foliage" case — the reason a colour-salience channel exists.

The driving variable is **CONTINUOUS cone-opponent contrast, computed
SURROUND-RELATIVELY** on two opponent axes — L−M (red–green) and S−(L+M)
(blue–yellow), orthogonal to luminance L+M — i.e. the SAME surround-relative
difference the eye already runs on luminance (centre-surround / conspicuity), now
on the opponent-colour axes. NOT categorical colour, NOT discrete colour
categories: the salience of a region is the **magnitude of its opponent-space
distance from its surround** (the linear-separability geometry of colour search).
Categorical colour as the IDENTITY sign is the named frontier, OUT OF SCOPE.

### AUDIT (in-code, §12.4) — what already exists, verified in the source

- **Cone-opponent contrast IS EXPRESSIBLE BY COMPOSITION — no new Rust.** The
  eye's surround-relative difference is already a seed rule, not luminance-hardcoded
  Rust: `seeds/vision_lateral.json`'s `lat_pool` computes a surround MEAN by
  `Div(Fold(Neighbours(c,"neighbour"), acc, +…), count)` (lines 149–387) and
  `lat_residual` transmits `centre − g·surround` via `Minus`/`Times`
  (lines 388–583). That is exactly a surround-relative difference over per-cell
  attrs, built from `Neighbours`/`Fold`/`Div`/`Minus`. Generalising it to
  multi-channel cone attrs (`cL,cM,cS`) is the SAME idiom on three linear
  recombinations — pure graph data.
- **The arithmetic primitives all exist and evaluate.** `Fold`
  (`term.rs:387`), `Minus`/`Div`/`Sqrt`/`Abs`/`Times`/`Plus`/`Max`/`IfThenElse`
  (`term.rs:493,495,498,490,…`), each used across committed seeds
  (`ballistics.json` uses `Sqrt`+`Abs`; `vision_lateral` uses `Fold`+`Div`+`Times`;
  `physics_foundation` uses variadic `Times`). Opponent contrast composes from
  them with no engine change.
- **`stream_resolve_salient` reads salience as `Attr(cand,"residual")` under an
  `Argmax`** (`seeds/vision_stream.json:103–167`), and orders by it. It does not
  care HOW `residual` was produced — the stream rung set it mechanically; here a
  colour SEED RULE writes it. So a colour-contrast term feeds the SAME salience
  field with **NO new Rust and NO change to the stream rule**: the colour rules
  WRITE `Region.residual`, the unchanged stream rule READS it.
- **`seeds/vision_color.json` is CONCEPTUAL, not machinery.** Its rules
  (`opponent_processing_organizes_color`, …) are NL Concept claims with
  `match=None`, no `where`, no `effects` — verified in-code. There is **no
  computational opponent-contrast rule anywhere**; this rung builds the first one.

**The rung's contribution:** ONE seed (`seeds/vision_colour.json`, both flags OFF
by default, §9). Two rules compute, per cell, the surround-relative opponent
contrast (`cc_contrast`) and combine it INTERACTIVELY with luminance salience into
`Region.residual` (`cc_salience`), which the unchanged `vision_stream` rule then
spends a bounded budget over. NO new Rust.

## 1. Mechanism — exact (all in graph data, no Python decision)

The runner (`scripts/colour_measure.py`, adapter `domains/colour_world.py`) builds
a cone-cell grid **mechanically** and reads the stream back; it makes **no percept
decision** (§0 / CLAUDE.md). Supplying `cL,cM,cS` per cell is mechanical ingest,
exactly like supplying luminance. Graph:

- `ColourParams{salience: 0.0, colour: 0.0}` — TWO OFF-by-default flags (the
  `GroundParams`/`StreamParams` idiom). `salience` arms the surround-contrast
  computation at all; `colour` adds the chromatic channel (the ABLATION, graph
  data — luminance-only = `colour:0`, full = `colour:1`; §0 forbids a Python fork).
- Cells are `Region` nodes (so the unchanged stream rule matches them via
  `scene -has_region-> R`), integer cone attrs `cL,cM,cS`, grid attrs
  `rrow,rcol,scale`, stream attrs `resolved:0, order:-1, residual:0`, and computed
  `csal, lsal, cc_done:0, sal_done:0`.
- `neighbour` edges between 4-adjacent cells — grid geometry wired by the adapter
  with `add_edge_unchecked` (host bookkeeping, exactly as `vision_lateral` wires
  `neighbour`).

**Rule `cc_contrast`** (`match [["scene","has_region","R"]]`): where
`And`(flag `Gt(salience,0.5)`; once-guard `Lt(R.cc_done,0.5)`). Reads ONLY raw cone
attrs (self + neighbours — NO cross-node computed-attr dependency, so firing order
is irrelevant). Per cell, with `rg=cL−cM`, `by=cS−(cL+cM)`, `lum=cL+cM`, and the
surround means computed inline over `Neighbours(R,"neighbour")` by
`Div(Fold(+neighbour-value), Max(Fold(+1),1))` (the `lat_pool` idiom, a true MEAN
that handles edge cells):
- `csal = Sqrt( (rg−rg_s)² + (by−by_s)² )` — the continuous opponent-space
  **distance** from the surround (the continuous-in-comparison-role magnitude);
- `lsal = |lum − lum_s|` — the SAME surround-relative difference on the achromatic
  axis (luminance salience).
Effects: set `csal`, `lsal`, `cc_done=1`.

**Rule `cc_salience`** (same match): where `And`(flag `Gt(salience,0.5)`;
`Gt(R.cc_done,0.5)`; once-guard `Lt(R.sal_done,0.5)`). Effects:
- `residual = lsal + IfThenElse(Gt(colour,0.5), csal + lsal·csal, 0)` — the
  INTERACTIVE combine: luminance salience always, plus (when colour is on) the
  chromatic contrast AND an interaction term `lsal·csal`. This is the parameter-free
  superadditive/facilitation form `(1+lsal)(1+csal)−1` when colour is on — NOT
  strict addition (Bauer/Jolicoeur/Cowan reject naive additive-colour; §13: no
  magic weight, the interaction is a product, not a tuned coefficient). When colour
  is OFF, `residual=lsal` — the luminance path, unbroken;
- `sal_done=1`.

The runner ticks in **two mechanical phases** (no decision): (1) arm the flags,
`s.tick()` computes the residual field to fixpoint; (2) set `StreamParams.stream`,
`s.tick()` spends the budget. Then read `order` back. Zero floats are tuned: cone
values, positions and budget are STRUCTURAL data; opponent axes are integer linear
recombinations (in-frame/integer, the frame/continuum invariant); the contrast
MAGNITUDE and the combine are pure `Sqrt`/`Abs`/product (§13).

## 2. Statistics — exact, per arm

All arms DETERMINISTIC except the noise floor (n fixed in advance). The stream
`tunnel(regions, order, spent, budget)` readout (majority-mass contiguous, from
`scripts/stream_measure.py`) is REUSED unchanged as the false-pop detector.

### H — EQUILUMINANT POP-OUT (the headline discriminator)

A 5×5 field, uniform luminance (`cL=cM=10` ⇒ `lum=20, rg=0`), uniform `cS=10`
(⇒ `by` uniform), with ONE centre target `cL=15,cM=5` ⇒ `lum=20` (**equiluminant**),
`rg=10`. Budget `B=1`.
- **COLOUR** arm (`salience=1, colour=1`): target `residual = 0 + 10 + 0 = 10` is
  the unique max (border cells get csal≈2.5; the rest 0) ⇒ target streamed at
  `order=0`.
- **LUMINANCE-ONLY** arm (`salience=1, colour=0`), SAME field, same `B`:
  `residual=lsal=0` everywhere ⇒ `spent=0`, target `order=−1`.
**PASS iff** the target is streamed at `order=0` under COLOUR **AND** unresolved
(`order=−1`, `spent=0`) under LUMINANCE-ONLY. *Colour rescues the target luminance
cannot see; luminance-only misses it.*

### I — INTERACTIVE COMBINATION (not a trivial sum)

A 5×5 field, background `cL=cM=10`, ONE centre target `cL=25,cM=5` ⇒ `lum=30`
(Δlum vs 20), `rg=20`; `cS=10` uniform. So `lsal_target=10`, `csal_target=20`.
Budget `B=1`, COLOUR arm.
**PASS iff** (a) the target is found (`order=0`); (b) the combine is INTERACTIVE:
the target's `residual` **strictly exceeds** `lsal+csal` (measured
`residual − (lsal+csal) = lsal·csal = 200 > 0`), so a target salient in BOTH
channels is found but the combination is not a trivial sum.

### L — LUMINANCE-ONLY STILL WORKS (colour is additive capability)

A 5×5 field, uniform chroma (`cL=cM` everywhere ⇒ `rg=0`; `cS=10` uniform), ONE
centre target distinct in LUMINANCE only (`cL=cM=20` ⇒ `lum=40` vs background
`lum=20`). `csal=0` everywhere; `lsal_target=20`. Budget `B=1`.
**PASS iff** the target is streamed at `order=0` under BOTH the COLOUR arm
(`colour=1`) AND the LUMINANCE-ONLY arm (`colour=0`), with the SAME result — a
purely luminance-salient target is found WITHOUT any colour signal; colour does not
break the existing luminance path.

### U — UNIFORM-COLOUR FLOOR (anti-overfit, deterministic, exact 0)

A 10×10 uniform field (`cL=cM=cS=10`): no opponent contrast anywhere.
**PASS iff** `max csal over all cells == 0` EXACTLY **AND** the COLOUR arm
(`B=8`) spends `0` — a uniform-colour field mints ZERO colour salience (not a
universal colour-hallucinator).

### N — COLOUR-NOISE FLOOR (anti-overfit, n = 100, seeds 34000–34099, exact 0)

100 fields of 10×10 iid-random cones (`cL,cM,cS ∈ [0,20]` per cell, per-seed RNG),
COLOUR arm, budget `B=4`. `false_pop := tunnel(regions, order, spent, B)` — the
budget-many resolved cells form a majority-mass contiguous spear.
**PASS iff `0/100`** — scattered colour noise cannot form a coherent contiguous
majority-mass target, so it invents no pop. Mirrors the stream rung's 0/100.

### X — §9 OFF-DAY (defaults preserve committed results)

The equiluminant headline field, flags LEFT at default (`salience=0, colour=0`),
stream flag set, tick.
**PASS iff** `spent=0`, all `order=−1`, all `residual=0`, all `cc_done=0` — the
colour seed is inert by default, so the stream sees an empty salience field and
every committed stream/vision result reproduces exactly.

**Bench / byte-identity (§9):** `vision_colour` is loaded only by the runner/gate
(not boot-loaded) and ships both flags OFF, and adds NO Rust ⇒ engine
byte-identical by construction. PASS iff: bench **200/0** with `data/`; sd orbit
law `{2:1,3:2,4:2,6:2,12:4}` unmoved; sibling gates green — stream 6 · illusion 8 ·
blink · vision-ground · time · depth · stereo · dim · gen_infer/provenance ·
sdloop · cycle-detect.

## 3. n, fixed in advance

Deterministic arms (H, I, L, U, X) need no n. The noise floor N: **n = 100**
(seeds 34000–34099), matching the stream/illusion floors. No power analysis is
needed for a floor whose null is an EXACT 0 count (any single false pop fails it).
No sweeps, no re-runs (§3.6).

## 4. Burned-seed ledger for this rung

- **34000–34099** — colour-noise floor (N), 100 seeds.
- **34100–34999** — CLEAN, reserved for any follow-up with its own prereg.

Confirmatory floor seeds consumed ONCE here, never reused. The deterministic arms
use hand-constructed stimuli only (no 34xxx seed touched).

## 5. Decision rule — what each answer means (§7: either answer is a result)

- **The equiluminant target is streamed under colour AND missed under luminance-only
  AND the combine is interactive AND luminance-only still finds a luminance target
  AND uniform-colour mints 0 AND noise invents 0 pops** ⇒ colour is the pop-out
  channel for the equiluminant target, a surround-relative opponent-contrast salience
  feeding the same bounded stream, with zero magic numbers. Bounded to the
  continuous-magnitude / integer-coordinate opponent class.
- **The equiluminant target does NOT stream under colour** (or streams under
  luminance-only) ⇒ opponent contrast does not rescue the equiluminant target as
  claimed — a clean negative, reported, NOT rescued (no metric surgery, §5).
- **The combine is a trivial sum** (`residual == lsal+csal`) ⇒ the interaction term
  is inert; reported.
- **Uniform colour mints salience, or a noise field invents a pop** ⇒ the mechanism
  hallucinates colour salience; overfitting; reported.
- **Opponent contrast turns out to need Rust** ⇒ reported with the exact DSL gap
  justified in-code, §9 kept, hash recorded.

## 6. Prediction, stated in advance, with provisos (§3.7)

I predict **all deterministic arms hold, the uniform floor is exactly 0, and the
noise floor is 0/100** — because colour salience is a pure surround-relative
opponent-space distance (the `lat_pool`/`lat_residual` idiom on three channels)
feeding the proven stream `Argmax`, and the equiluminant target HAS opponent
contrast while HAVING zero luminance contrast by construction.

Provisos that could break (and what each would teach):
1. **Fold-over-Neighbours surround mean** — I predict the inline neighbour-opponent
   Fold evaluates and gives a true edge-corrected mean (the `lat_pool` precedent).
   If `Fold` over the wired `neighbour` edges returns 0 or errors, the surround
   contrast is unreadable and the mechanism needs the adapter to pre-record a
   neighbour count (as `lat_pool` in fact does) — a build detail, reported.
2. **Two-phase tick ordering** — I predict computing the residual field to fixpoint
   BEFORE turning the stream on avoids the stream picking a not-yet-computed cell.
   If the phases must instead be gated in-rule (stream waits on `sal_done`), C's
   ordering could be wrong; reported, not patched with a threshold.
3. **Interaction term scale** — I predict `residual > lsal+csal` strictly whenever
   both channels are positive. If `lsal·csal` underflows or the combine is read as a
   sum, arm I fails and the interactive claim is bounded; reported.

## 7. Scope — what is NOT shown (§8), the named frontier

- **BOUNDED to the continuous-MAGNITUDE / integer-COORDINATE opponent class.** The
  in-frame colour coordinate (`cL,cM,cS` and the opponent recombinations) is
  DISCRETE/INTEGER; only the CONTRAST MAGNITUDE (the surround-relative
  opponent-space distance) is continuous — the continuous-in-the-comparison-role of
  the frame/continuum invariant. No continuous colour coordinate is placed IN a
  frame (`coord_ints` refusing floats stays correct).
- **Colour salience is SEPARABLE from luminance but combines INTERACTIVELY, not
  strictly additively** (the `lsal·csal` term). The DIRECTION of the interaction
  (superadditive facilitation here) is NOT claimed biological — only that it is
  non-additive (Bauer/Jolicoeur/Cowan).
- **NOT claimed: luminance=structure / colour=NONE.** Colour carries WEAK COARSE
  structure (the achromatic/chromatic split is leaky); this rung shows colour
  provides DETECTION SALIENCE for near-equiluminant targets, nothing about a colour
  "what" layer.
- **NOT claimed: trichromacy "evolved for fruit"** (a contested driver). Only that
  colour provides detection salience for near-equiluminant targets — the
  "ripe fruit against foliage" DETECTION case, not an evolutionary claim.
- **NAMED FRONTIER, NOT this rung:** categorical colour as the IDENTITY ("what")
  sign; the full recognition layer; colour constancy / reflectance inference. Out of
  scope, not attempted.

## 8. Engine / bench (filled at OUTCOME)

Engine hash + resolution path, bench condition, and the §9 byte-identity table are
recorded in `VISION_COLOUR_RESULTS.md` at the confirmatory run. **This rung adds NO
Rust**; the shared canonical build is legitimate iff the Rust source is
byte-identical (§10.1 rule 4) — verified by `provenance_line()`. `data/` symlinked
to canonical (§10.2).
