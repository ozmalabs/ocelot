# VISION — STYLE AS A DISCOVERED DIMENSION (FRONTIER T5): results

*Pre-registration: `VISION_STYLE_PREREG.md`, committed BEFORE the run at **`a08b2a97`**
(PROTOCOL §3). Runner `scripts/style_measure.py`; pinned `results/style_measure.json`;
gate `tests/test_style_migrated.py`; seed builder `tools/build_vision_style.py` →
`seeds/vision_style.json`; adapter `domains/style_world.py`. Seeds **47000–47999**
(noise floor 47000–47099 consumed; coherence-crux draws 47100–47199 consumed;
**47200–47999 CLEAN**; 12000–46999 untouched). Engine **`7d5f50c18673`** (shared build,
Rust source byte-identical — **NO new Rust**, §10.1 rule 4). Base `main` HEAD
**`543b552b`** (`git merge-base --is-ancestor 543b552b HEAD` verified). The LAST rung of
the frontier program.*

## OUTCOME: BOUNDED CROSSING

**Style crosses as a DISCOVERED dimension, bounded.** Each source mints exactly ONE
style, **on the axis it is actually coherent on — and nothing tells the mechanism which
axis that is**: there is one mint rule per axis and both run on every source. A new
instance is recognized as its source's style and as its kind; distinct sources mint
distinct styles with exact-0 cross-source pollution, decided **source-blind**; and — the
crux (§1.1) — an **incoherent source mints at CHANCE level, not always**: 2 of 100
against an exact analytic chance of 2.347, so the mechanism is **not a universal
container**. All 10 pre-registered arms pass, and the pre-registered **BOUND probe
REFUSED exactly as predicted**.

## The mechanism (by composition, NO new Rust)

Style composes from two things already in the substrate, joined by `Minus` and
`Neighbours`:

1. **T2's CONTINUOUS proportion axes and its box ORIGIN.** `cat_mint` already stores
   `v0lo/v1lo` = `MinOver` of the members' own coordinates
   (`tools/build_vision_category.py:132–135`). **`sty_project` uses that origin as an
   ANCHOR**: `dv0 = v0 − c.v0lo`, `dv1 = v1 − c.v1lo` — the instance's **within-category
   coordinate**. This is the load-bearing idea: a RAW coordinate is not comparable
   across kinds (kind A and kind B occupy different parts of the axis space), a
   within-category offset is. Projection is gated on T2's own containment condition
   (`:167–170`), so **T2's floor is inherited** — an out-of-box or novel-signature item
   is never projected and can never contribute to a style.
2. **The Omniglot writer-dimension per-source coherence mint**
   (`seeds/writer_dimensions.json:15`, `:228` — *"the writer's physical limits become
   IMPLIED dimensions"*; per-instance a delta is noise, POOLED across one hand's output
   it is a coherent quantum coordinate). **`sty_mint_a0` / `sty_mint_a1` are that rule
   one level up**: pool a source's projected items over `Neighbours(W, "produced")`,
   require `>= 3` to agree **EXACTLY**, mint `ObjStyle{src, axis, delta, members}`.

**THE AXIS IS DISCOVERED because there is ONE RULE PER AXIS and BOTH run on EVERY
source.** Nothing marks an axis as "the style axis". A source coherent on axis 0 while
free on axis 1 satisfies the agreement test on axis 0 only, mints exactly one style, and
the minted node RECORDS the axis it found.

`sty_recognize_a0/a1` are **SOURCE-BLIND** — neither reads the `produced` edge or any
source attribute (gated structurally by `test_recognition_rules_are_source_blind`) —
which is what makes DISCRIMINATION a genuinely risked test rather than a label lookup.

The DSL evaluates every primitive needed (`Minus` `jsonio.rs:1270`, `MinOver` `:1174`,
`Neighbours` `:1121`, plus T2's `Count`/`Filter`/`NodesOfType`/`Exists`/`Not`/`Eq`/
`And`/`Gt`/`Gte`/`Lt`/`Lte`), so **NO new Rust and NO edit to any committed rung's seed,
adapter or tests.** Coordinates and offsets are INTEGER in-frame throughout — no
real-valued quantity is introduced anywhere, so the frame/continuum invariant is
untouched. **Agreement is EXACT equality: no radius, no tolerance exists in the
mechanism.**

`m_min = 3` **FALLS OUT** of `d_style = 2` (§13): a style is an **(axis, delta) PAIR** —
2 units of description, WHICH axis + WHAT offset — and **membership is FREE because the
source is OBSERVED**, so the style pays iff `m > d_style = 2` ⟺ `m >= 3`. The accounting
differs from T2's (there a member pays 1 for its category label) and is stated rather
than inherited; it lands on the same 3 the writer rung used.

## Per-arm results (`results/style_measure.json`)

| arm | result | verdict |
|---|---|---|
| **H — STYLE DISCOVERED (headline)** | **3 styles from 3 sources, one each, every one on the CORRECT DISCOVERED axis**: S1 `(axis 0, δ=0, 6 members)`, S2 `(axis 0, δ=6, 6)`, S3 `(axis 1, δ=0, 6)`. `n_on_free_axis = 0` for every source. Both axes are represented across sources, so the discovery is not a constant | **PASS** |
| **G — GENERALIZATION** | **3/3** held-out recognized as their OWN source's style, on the right axis, AND as the correct kind; every `coord_unseen = true` | **PASS** |
| **B — DISCRIMINATION** | `cross_false = **0**` over 21 recognized items, styles distinct, `items_matching_both_axes = 0`; decided SOURCE-BLIND | **PASS** |
| **X1 — THE COHERENCE CRUX (§1.1, RISKED)** | incoherent source mints in **2 / 100** scenes (47100–47199) vs **exact analytic chance 2.347**, binomial-95 critical value 6 ⇒ **within chance**; `universal_container = False`. **Paired positive controls in the SAME scenes: styled sources still mint 3/3 in 100/100, and 600/600 of the incoherent source's items are ALIVE (`dv_set=1`)** | **PASS** |
| **C — MEMORIZATION (ENTAILED)** | `(sum_mem, sum_sty) = (0, 3)` — exact-raw-coordinate matching refuses every held-out; the offset recognizes all | **PASS** (entailed) |
| **D — MDL** | `k = 3` styles over 18 members; `mdl_raw = 18 > mdl_styled = 6` (ratio **3.0**); `m_min = 3` falls out of `d_style = 2` | **PASS** |
| **E — FLOOR / noise (ENTAILED)** | **0/100** iid-noise fields (47000–47099) mint a style; 0 mint a category | **PASS** (entailed) |
| **L — BOUND PROBE / anchor coverage** | **REFUSED, exactly as predicted** — see below | **PASS** (as a BOUND) |
| **F — DOWNSTREAM (§1 cl. 5)** | ON: 3 styles; OFF: 0. `d_styles = 3`, `d_recognized_max = 1.0`, `d_projected_max = 1.0` | **PASS** |
| **X — OFF-DAY (§9)** | defaults: 0 styles, 0 recognitions, 0 projections — **and still 0 on a scene where T2's 3 categories are LIVE** (the style seed does not ride on the category flag) | **PASS** |

## The crux is the result (§1.1, §13.1)

The headline on its own would be weak: the corpus supplies sources whose offset is
constant on one axis, and **that constancy is ENTAILED — the mechanism is not credited
with discovering that a constant exists** (declared in advance, prereg §5). What is
RISKED, and what the crux measures, is whether the mechanism will mint a "style" for
**anything**.

An incoherent source is given the **same instance count, the same kinds, a comparable
value spread, and the same scene** as the three styled sources. It mints in **2 of 100**
scenes. The chance rate is not fitted — it is computed exactly, in-runner, by
enumeration (`_p_max_mult_ge3`: `1.2%` per axis that some value occurs ≥3 times among 6
draws from 40; `2.35%` over two axes), and both observed false mints have `members = 3`
exactly, the signature of a chance coincidence at the MDL floor. **A universal container
would have scored 100/100.** The paired controls in the *same* scenes rule out the
§1.1 death-scores-a-perfect-floor failure: the styled sources still mint 3/3 in every
scene, and every one of the incoherent source's 600 items is projected and alive.

**Chance-level false agreement is therefore a reported BOUND, not a defect claimed away:
exact agreement over a finite value pool is not infinitely selective.**

## The BOUND probe REFUSED, as predicted (§7, §13.1)

The pre-registration predicted this failure in advance and it happened. **Cross-kind
coherence is a property of the DATA, not of the rule.** The anchor is the category's
`MinOver` box origin, so an offset is source-constant across kinds only while every
kind's origin is set consistently. Train S1 in kinds A,B only and kind C's origin on
axis 0 moves from `10` (S1) to `16` (S2):

- S1 still mints its style (`axis 0, δ=0`, 4 members) from kinds A,B.
- S1's held-out in kind C at its own offset is **below the shifted box origin** — refused
  at T2's containment floor (`cat_recognized = 0`, never projected).
- The second, deliberately IN-box held-out **is** projected (`cat_recognized = 1`,
  `dv_set = 1`) but its offset has shifted to `2`, so it is **not S1's style**
  (`sty_recognized = 0`). The refusal is about the OFFSET, not merely about containment.

**No tolerance was added to widen this (§5).** The failure is CONSERVATIVE — refusal,
never a false style — and it is pinned in the gate as a bound.

## The gate is POSITIVE-CONTROLLED (§12.3, §1 clause 4)

A gate only ever seen to pass is not a gate. T3's caught defect was **injected** into
this seed's own agreement test — the exact `Eq` rewritten in `Times`'s `a`/`b` form,
which parses to an EMPTY PRODUCT (`=1`, `jsonio.rs:1274`) and makes the agreement
`Eq(1,1)`, true for everything:

- **10 of 16 tests went RED**, including the headline (`test_style_is_discovered...`),
  the crux, generalization, discrimination, MDL, the bound probe, and the structural
  `test_seed_uses_no_times_term`.
- Reverting restored **16/16** with the regenerated seed **byte-identical** to the
  pre-injection file (verified by sorted-key JSON diff).

`Times` and `Div` are absent from this seed by construction and the absence is gated.
The flag guard is **absence-tolerant** (`Count(Filter(NodesOfType("StyleParams"), …)) >= 1`)
and deliberately **not** `PickUnique`, which returns `None` on an absent params node and
would silently change behaviour elsewhere (the agnosia rung's lesson) — also gated.

## §13.1 — ENTAILED vs RISKED, as declared IN ADVANCE

| declared | arm | outcome |
|---|---|---|
| **ENTAILED** | C (memorization refuses), E (noise floor, inherited from T2), the constancy of the styled sources' offsets, F/X (flag plumbing) | reported as consistency, **NOT banked as evidence** |
| **RISKED** | **H** — that offsets cohere ACROSS KINDS at all (anchor-dependent; arm L shows it CAN fail), and that the AXIS is discovered rather than assigned | passed, with the failure mode demonstrated separately |
| **RISKED** | **B** — discrimination decided SOURCE-BLIND; pollution mechanically possible | exact-0 |
| **RISKED** | **X1** — the coherence crux; a universal container was the disqualifying outcome | chance-level, 2/100 |

**The prediction stated in advance (prereg §7) was correct on every point**, including
the quantitative one: *"S4 mints a style in ROUGHLY 2–3 of 100 scenes … NOT 0 and NOT
100"* → **2/100**, chance 2.347. And *"L: I predict REFUSAL"* → refused, by the exact
anchor-shift mechanism named in advance.

## BOUNDS (§8) — what is NOT shown

- **The axes are GIVEN, not learned from pixels.** Style here rides on T2's supplied
  axis-codebook. **The learned axis-codebook at natural-image scale remains the NAMED
  FRONTIER**, as does whatever the deformation rung leaves open.
- **A style is a CONSTANT offset on ONE axis.** A style that is a *scaling*, a *rotation*
  of the axis pair, or any non-constant function of the instance is out of class. Real
  style is a FAMILY (the Omniglot finding); this rung represents the family's coherent
  component on a single discovered axis, not the family.
- **Style is discovered PER AXIS independently.** A style spread across a correlated pair
  of axes is not represented.
- **Two sources with an IDENTICAL delta on the same axis ARE the same style** — the
  mechanism cannot tell them apart and does not pretend to.
- **Cross-kind coherence requires consistent per-kind coverage** (arm L) — the anchor is
  the box origin, so a kind whose training omits the anchor-defining source shifts.
- **Chance-level false agreement exists** (arm X1, 2/100 at an exact 2.35% chance rate).
- **The SOURCE is an observable, supplied by the adapter** (which hand produced an
  instance), exactly as the writer rung's `wrote_transform` edge is. It is not a
  category label and no rule reads any ground-truth kind or style — but the rung does
  not discover the partition of instances into sources.
- Bounded to the **discrete-similarity regime** already crossed; n is exact/all-or-none
  on the structural arms (deterministic geometry), with only the floors sampled.

## §9 — defaults preserve committed results

- **Flag OFF by default** (`StyleParams.style = 0.0`): the seed is inert (arm X),
  including on a scene where T2's categories are live, and `vision_style` is only ever
  loaded on explicit request, so no existing agent boots with it.
- **NO new Rust** — engine `7d5f50c18673`, shared build, Rust source byte-identical.
- **No committed rung's seed, adapter, runner or test was edited.** The only change to an
  existing file is the additive `REGISTRY.register(Seed(id="vision_style", …))` entry in
  `domains/seed_registry.py` (the §11 rule-1 expected conflict point — resolve by keeping
  both sides).
- Vision bench `scripts/rung7_vision_bench.sh`: **200 passed / 0 failed** (with `data/` symlinked, §10.2)
  = the recorded baseline.
- sd orbit law `{2:1,3:2,4:2,6:2,12:4}` **UNMOVED**.
- Sibling gates green: category · colour-identity · similarity · identity-untangling ·
  sdloop-vision · lighting · agnosia · engine-provenance + the new gate = **102 passed**
  (the new gate `test_style_migrated.py` **16/16**).

## Provenance (§10)

```
engine 7d5f50c18673 @ /home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so
  [shared build from /home/matt/ozma/internal/research/experiments/gamma-substrate — Rust source identical]
```

Base `main` HEAD `543b552b` (ancestor-verified). Pre-registration committed BEFORE the
run at `a08b2a97`. Results/build/gate committed on branch
`gamma-substrate/vision-style-t5`.
