# VISION — COLOUR SALIENCE: pop-out for the EQUILUMINANT target (RESULTS)

*Confirmatory run of `VISION_COLOUR_PREREG.md` (committed BEFORE the run at
`a1ee7d22`, §3). Runner `scripts/colour_measure.py`; gate
`tests/test_colour_salience_migrated.py`; seed `seeds/vision_colour.json` (builder
`tools/build_vision_colour.py`); adapter `domains/colour_world.py`; raw
`results/colour_measure.json`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`
  — **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*; this rung adds **NO
  Rust**, so the shared build is legitimate, §10.1 rule 4). `data/` symlinked to
  canonical (§10.2).
- **Bench 200 passed / 0 failed with `data/`** (`scripts/rung7_vision_bench.sh`,
  151.5s).
- **Sibling gates green.** colour · stream · sdloop · dimension-inference ·
  engine-provenance = **43 passed** in one process; illusion · blink · vision-ground
  · time · depth · stereo · gen_infer · cycle-detect = **68 passed** (553s, 1
  slow-marker warning). The **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is unmoved** (the
  sdloop gate `test_orbit_law_arithmetic_matches_the_measured_mint_counts`, which
  pins it, passed).
- **NO new Rust, ONE new seed** (`vision_colour`, NOT boot-loaded; ships
  `ColourParams{salience:0.0, colour:0.0}` both OFF by default), so §9 byte-identity
  holds by construction and is verified above.

## Verdict — ALL 6 gated arms PASS (every headline prediction held; one auxiliary stimulus was corrected mid-run and is reported below)

| arm | result |
|---|---|
| **H_equiluminant** (headline) | **PASS** — an equiluminant target (`lum=20`=surround, `target_lsal=0.0`) with high cone-opponent contrast (`target_csal=10.0`) is streamed in under COLOUR at `order=0` (`spent=1`), and MISSED under luminance-only (`order=−1`, `spent=0`). *Colour rescues the target luminance cannot see.* |
| **I_interactive** | **PASS** — a both-channel target: `lsal=10.0`, `csal=22.36`, `residual=255.97` ≫ trivial sum `32.36`; the interaction term `223.61` == `lsal·csal` exactly. The combine is `(1+lsal)(1+csal)−1`, NOT a sum. |
| **L_luminance_only_works** | **PASS** — a genuinely chroma-neutral luminance target (`target_csal=0.0`) is streamed at `order=0` under BOTH colour-on and luminance-only. *Colour is additive capability; it does not break the luminance path.* |
| **U_uniform_floor** (anti-overfit) | **PASS** — a uniform-colour field mints ZERO colour salience: `max_csal=0.0`, `n_positive_csal=0`, `spent=0`. |
| **N_noise_floor** (anti-overfit, n=100) | **PASS** — **0/100** iid colour-noise fields (seeds 34000–34099) invent a coherent pop (`tunnel` fires 0). |
| **X_offday** (§9) | **PASS** — both flags OFF (default) ⇒ inert: `spent=0`, `max_residual=0.0`, `max_cc_done=0.0` (`cc_contrast` never fired), all `order=−1`. |

## The headline — colour is the pop-out channel where luminance salience is ZERO

**Two seed rules generalise the eye's surround-relative difference
(`vision_lateral`'s centre-surround) to the two cone-opponent axes L−M and
S−(L+M), and feed the UNCHANGED `vision_stream` budget — with ZERO new Rust and
ZERO magic numbers:**

- **`cc_contrast`** computes, per cell, `csal` = the Euclidean opponent-space
  DISTANCE of `(L−M, S−(L+M))` from its surround mean (a CONTINUOUS contrast
  magnitude), and `lsal` = the SAME surround-relative difference on the achromatic
  axis L+M — via `Div(Fold(+neighbour-value), Max(Fold(+1),1))`, the `lat_pool`
  idiom, reading ONLY raw cone attrs so firing order is irrelevant.
- **`cc_salience`** combines them INTERACTIVELY into `Region.residual`
  (`lsal + csal + lsal·csal` when colour is armed; `lsal` alone when it is not),
  which the unchanged `stream_resolve_salient` rule then spends a bounded budget
  over.

**The equiluminant discriminator is the whole point, and it holds exactly:** a
target with `lum` identical to its surround (`lsal=0.0`, invisible to luminance
salience) but a distinct red–green coordinate (`csal=10.0`) becomes salient via
COLOUR and is streamed in at `order 0` under a budget of 1; the luminance-only arm
(same field, `colour=0`) computes `residual=0` everywhere, spends nothing, and
leaves the target at `order −1`. *This is the "ripe fruit against foliage" case —
colour provides detection salience precisely where luminance provides none.*

**The combination is INTERACTIVE, not a trivial sum.** A both-channel target has
`residual = 255.97`, far above `lsal+csal = 32.36`; the surplus (`223.61`) is
exactly `lsal·csal` — the parameter-free superadditive form `(1+lsal)(1+csal)−1`.
There is no tuned colour weight (§13); the interaction is a product.

**The anti-overfit crux holds — NOT a universal colour-hallucinator.** A
uniform-colour field mints exactly zero colour salience (`max_csal=0`, no cell has
positive contrast, budget spends 0); **0/100** iid colour-noise fields form a
coherent contiguous pop; and a purely luminance-salient target is found WITHOUT any
colour signal (`csal=0`), identically with colour on or off — colour is additive
capability that does not disturb the luminance path.

## What I predicted, and what I got wrong (§3.7 / §7)

I predicted **all deterministic arms hold, the uniform floor is exactly 0, and the
noise floor is 0/100** — confirmed on every arm. The three provisos:

1. **Fold-over-Neighbours surround mean (proviso 1)** — I predicted the inline
   neighbour-opponent `Fold` evaluates and edge-corrects the ring. **HELD:** the
   `lat_pool` idiom (`Div(Fold(+value), Max(Fold(+1),1))`) gives the true mean
   (target `csal=10.0` with a 0-mean surround; border cells `csal=2.5` from a
   4-neighbour ring holding the target once — exactly `10/4`). No adapter-recorded
   count was needed.
2. **Two-phase tick ordering (proviso 2)** — I predicted computing the residual
   field to fixpoint BEFORE turning the stream on avoids the stream picking a
   not-yet-computed cell. **HELD:** the two mechanical `s.tick()` phases serialise
   cleanly; the stream never fired on a zero-residual cell.
3. **Interaction term scale (proviso 3)** — I predicted `residual > lsal+csal`
   strictly whenever both channels are positive. **HELD:** `255.97 > 32.36`, and
   the surplus is `lsal·csal` to 1e-9.

**WHAT I GOT WRONG — the pre-registered "pure-luminance" stimulus was NOT
chroma-neutral, and the run exposed it.** The prereg's arm L stimulus (background
`cS=10`, target `cL=cM=20` at `cS=10`) was asserted to have `csal=0`. It does not:
**the blue–yellow opponent axis `by = S−(L+M)` is NOT luminance-invariant**, so
raising `L+M` at fixed `S` shifts `by` and injects real chromatic contrast (the run
measured `csal=20` on that target). The **headline PASS condition still held** (the
target was found under both arms), but the stimulus did not cleanly isolate
"luminance-only." The correction — reported here, not silently patched — is that a
genuinely chroma-neutral luminance change must **co-vary `S` with `L+M`** (base
`cL=cM=10, cS=30 ⇒ by=10`; target `cL=cM=20, cS=50 ⇒ by=10`, `rg=0` both), which
holds both opponent axes constant and yields `csal=0.0` exactly. This is a
STIMULUS-design correction (making the test STRICTER against itself, §1.1),
**not** metric surgery (§5): the measure — target found under both arms, `csal=0`
confirming chroma-purity — is unchanged; only the stimulus was corrected to match
its stated intent. It also records a genuine property of the opponent basis: the
chromatic axes as linear cone recombinations are chroma-pure only when the
luminance component is held via co-varying S.

**No headline proviso broke; the equiluminant discriminator was never rescued or
re-run (§5/§3.6).**

## Audit — what was already built vs the contribution (§12.4, in-code)

Verified in the source before designing (cited in the prereg §0):
- **Cone-opponent contrast IS expressible by composition — no new Rust.** The
  surround-relative difference is already a seed rule, not luminance-hardcoded Rust:
  `seeds/vision_lateral.json`'s `lat_pool` computes a surround MEAN by
  `Div(Fold(Neighbours(c,"neighbour"), acc, +…), count)` (lines 149–387) and
  `lat_residual` transmits `centre − g·surround` via `Minus`/`Times` (388–583).
  Generalising it to the cone attrs `cL,cM,cS` on three linear recombinations is the
  same idiom — pure graph data.
- **`stream_resolve_salient` reads salience as `Attr(cand,"residual")` under an
  `Argmax`** (`seeds/vision_stream.json:103–167`) and does not care HOW `residual`
  was produced. The colour rules WRITE `Region.residual`; the unchanged stream rule
  READS it — the colour channel feeds the SAME salience field with NO change to the
  stream rule.
- **`seeds/vision_color.json` is CONCEPTUAL, not machinery** — its rules
  (`opponent_processing_organizes_color`, …) are NL Concept claims (`match=None`, no
  `where`, no `effects`). No computational opponent-contrast rule existed anywhere;
  this rung builds the first.

**The contribution:** ONE seed (`vision_colour.json`, both flags OFF by default)
whose two rules compute the surround-relative cone-opponent contrast and combine it
interactively with luminance salience into `Region.residual`, which the unchanged
`vision_stream` rule spends a bounded budget over. NO new Rust; the whole channel is
the existing DSL (`Fold`/`Neighbours`/`Div`/`Minus`/`Sqrt`/`Abs`/`Times`), the
`vision_lateral`/`vision_stream` pattern.

## Scope — what is NOT shown (§8), and the named frontier

- **BOUNDED to the continuous-MAGNITUDE / integer-COORDINATE opponent class.** The
  in-frame colour coordinate (`cL,cM,cS` and the opponent recombinations) is
  DISCRETE/INTEGER; only the CONTRAST MAGNITUDE (the surround-relative
  opponent-space distance) is continuous — the continuous-in-the-comparison-role of
  the frame/continuum invariant. No continuous colour coordinate is placed IN a
  frame (`coord_ints` refusing floats stays correct).
- **Colour salience is SEPARABLE from luminance but combines INTERACTIVELY, not
  strictly additively** (the `lsal·csal` term). The DIRECTION of the interaction
  (superadditive facilitation here) is **not** claimed biological — only that it is
  non-additive (Bauer/Jolicoeur/Cowan reject naive additive-colour).
- **NOT claimed: luminance = structure / colour = NONE.** Colour carries WEAK
  COARSE structure (the achromatic/chromatic split is leaky — indeed the run showed
  `S−(L+M)` couples to luminance); this rung shows colour provides DETECTION
  SALIENCE for near-equiluminant targets, nothing about a colour "what" layer.
- **NOT claimed: trichromacy "evolved for fruit"** (a contested driver). Only that
  colour provides detection salience for near-equiluminant targets — the DETECTION
  case, not an evolutionary claim.
- **NAMED FRONTIER, NOT this rung:** categorical colour as the IDENTITY ("what")
  sign; the full recognition layer; colour constancy / reflectance inference. Out of
  scope, not attempted.

## Is colour the pop-out channel for the equiluminant target? — the plain answer

**Yes.** A cell's surround-relative cone-opponent contrast — the SAME
centre-surround difference the eye runs on luminance, computed on the L−M and
S−(L+M) axes — is a continuous salience magnitude that feeds the unchanged bounded
stream. A near-equiluminant target, invisible to luminance salience (`lsal=0`), has
high opponent contrast (`csal=10`) and is streamed in at `order 0`, where a
luminance-only salience spends nothing and misses it entirely. The channel is
additive capability: it does not fire on a uniform field (0 salience), invents no
pop from noise (0/100), leaves a purely luminance-salient target found without any
colour signal, and combines with luminance interactively (`lsal+csal+lsal·csal`,
not a sum) — with ZERO new Rust and ZERO magic numbers. **Bounded to** the
continuous-magnitude / integer-coordinate opponent class; categorical colour as the
identity sign and the "what" layer are the named, unreached frontier. The one
correction the run forced — the blue–yellow opponent axis is not luminance-invariant,
so a pure-luminance stimulus must co-vary S — is recorded above, not rescued.
