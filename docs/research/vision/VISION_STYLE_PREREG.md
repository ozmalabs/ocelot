# VISION — STYLE AS A DISCOVERED DIMENSION (FRONTIER T5): pre-registration

*Written and COMMITTED BEFORE the confirmatory run (PROTOCOL §3). Seeds **47000–47999**
(noise floor 47000–47099; coherence-crux random sources 47100–47199). Base `main` HEAD
**543b552b** (`git merge-base --is-ancestor 543b552b HEAD` verified). The LAST rung of
the frontier program.*

---

## 0. The rung

Category (T2) captures the **KIND** — the DISCRETE part-signature, and a region box over
the CONTINUOUS proportion axes that is the *within-category variation*
(`VISION_CATEGORY_RESULTS.md`). T2 explicitly names **style** as a frontier and leaves
the within-category variation UNEXPLAINED: the box is a blob, and nothing says *why* a
given instance sits where it sits inside it.

**STYLE is the claim that the blob has structure: the within-category variation is not
noise, it is partly a COHERENT per-SOURCE offset.** One writer/renderer's instances sit
consistently displaced in the same way across the category's continuous axes; a
different source sits displaced differently. Style is what is SHARED by everything one
source makes and DIFFERS across sources — orthogonally to the kind.

**And the "DISCOVERED DIMENSION" half is the sharp part: the mechanism is NOT told which
axis carries the style.** A source is coherent on *some* subset of the continuous axes
and free on the rest. The rung mints a style ONLY where a source's projected offsets
actually agree, and the minted style RECORDS THE AXIS IT FOUND. Style is a latent
dimension the substrate discovers, in the exact sense the Omniglot writer-dimension arc
established: *"the writer's physical limits become IMPLIED dimensions"* — per-instance a
delta is noise; POOLED across one hand's output it is a coherent quantum coordinate.

---

## 1. AUDIT (§12.4) — can style compose? **YES. NO new Rust.**

Every piece exists and is cited by `file:line`.

### 1.1 The category's CONTINUOUS proportion axes — the substrate style varies over

| piece | where |
|---|---|
| the REGION BOX over the continuous axes (`v0lo/v0hi/v1lo/v1hi` = `MinOver`/`MaxOver` of the members' `v0,v1`) | `tools/build_vision_category.py:132–135` |
| containment recognition (`Lte` both bounds both axes) — an item's membership of the region | `tools/build_vision_category.py:167–170` |
| the DISCRETE/CONTINUOUS split (`d0,d1` grouping key vs `v0,v1` within-category variation) | `tools/build_vision_category.py:79` (`sig_eq`), `:110–115` (the mint comment) |
| `ObjCategory` carries the box + exemplar, minted once per signature | `tools/build_vision_category.py:126–139` |

**So T2 already hands style exactly the substrate it needs:** a per-category ORIGIN
(`v0lo`,`v1lo` — derived by `MinOver` from the members' own spread, no magic radius) that
turns a raw coordinate into a **within-category coordinate**. That within-category
coordinate is the thing a style can be coherent in — and it is what makes style
comparable ACROSS categories (a raw coordinate is not: kind A and kind B live in
different parts of the axis space).

### 1.2 The per-source coherence-minting pattern — the writer dimension

| piece | where |
|---|---|
| `wd_infer_writer` — per-source pose deltas pooled over one hand's whole output; per-stroke a delta is noise, POOLED it is a coherent quantum coordinate | `seeds/writer_dimensions.json:15` |
| `wd_infer_writer_family` — pool per (writer, recognized-family), require **`Count(agreeing) >= 3`**, mint a `WriterStyle{writer, family, orient_delta}` | `seeds/writer_dimensions.json:228` |
| the mint effect: `add_node_if_absent WriterStyle` + `has_family_style` edge + an idempotency flag | same rule, `effects` |
| the pooling hop: `Neighbours(w, "wrote_transform")` filtered by exact-equality agreement | same rule, `where` |
| *"a real hand is a FAMILY of implied dimensions, not one slant"* — two hands mint DISTINCT styles, no cross-writer pollution | `seeds/writer_dimensions.json:228` (comment), `tests/test_ink_decode_migrated.py` |

**That is precisely the mechanism this rung needs**, one level up: replace *(writer,
stroke-family) → orient_delta* with *(source, continuous axis) → within-category offset*.

### 1.3 The DSL Terms — all present, NO new Rust

| Term | where | used for |
|---|---|---|
| `Minus {a, b}` | `runners/dsl/src/jsonio.rs:1270`, `term.rs:493` | the within-category offset `v − anchor` |
| `MinOver {source, var_name, value, default}` | `jsonio.rs:1174`, `term.rs:79`, `:4543` | extracting the (unique) owning category's anchor in EFFECT position |
| `Neighbours {node, edge_type, any_type}` | `jsonio.rs:1121` | the per-source pool (`produced`), exactly the writer rule's hop |
| `Count` / `Filter` / `NodesOfType` / `Exists` / `Not` / `Eq` / `And` / `Or` / `Gt` / `Gte` / `Lt` / `Lte` / `Attr` / `Lit` | as T2 | gates, guards, agreement test |

**AUDIT VERDICT: IN-CLASS BY COMPOSITION — T2's continuous axes + the writer rung's
per-source coherence mint, joined by `Minus` and `Neighbours`. NO new Rust, NO edit to
any committed rung's seed/adapter/tests.**

### 1.4 The §13 number, and where it FALLS OUT

`m_min = 3`, and the accounting is stated because it is **not** T2's:

- A style is described by an **(axis, delta) PAIR** ⇒ `d_style = 2` units of description
  (WHICH axis it lives on + WHAT the offset is).
- Membership is **FREE**: the source is OBSERVED (the `produced` edge), so a member pays
  nothing to record which style it belongs to — unlike T2, where a member pays 1 for its
  category label.
- Without the style, the `m` members each store their own value on that axis: cost `m`.
  With it: cost `d_style = 2`.
- **Pays iff `m > d_style = 2` ⟺ `m >= 3`.**

Same number as T2 and as the writer precedent (`>= 3`), from its own honest ledger. **It
is not tuned, and no radius/tolerance exists anywhere in the mechanism** — agreement is
EXACT equality, the colour/T2/writer discipline.

---

## 2. The mechanism to be built (`seeds/vision_style.json`, flag OFF by default)

Five rules. Nothing decides anything in Python (CLAUDE.md); the adapter
(`domains/style_world.py`) only builds `ObjSource -produced-> ObjItem` + `Scene
-has_obj-> ObjItem` and reads attributes back.

1. **`sty_project`** — projects a recognized `ObjItem` into ITS category's own frame:
   `dv0 = v0 − c.v0lo`, `dv1 = v1 − c.v1lo`, `dv_set = 1`. Gated on the item being
   CONTAINED in the category box (it inherits T2's floor: an unrecognized / out-of-box
   item is never projected). The anchor is fetched in effect position by `MinOver` over
   the singleton filtered set of owning categories.
2. **`sty_mint_a0`** / 3. **`sty_mint_a1`** — one rule PER AXIS (the DSL has static
   rules; `ndim<=3` is unrolled the same way in `seeds/quanta_navigation.json`). Fires
   where `>= 3` of a source's projected items agree EXACTLY on that axis's offset. Mints
   `ObjStyle{src, axis, delta, members, ex_v0, ex_v1}` + a `has_style` edge.
   Canonical-representative (`min oidx`) + `Not Exists` guards make it batch-safe and
   mint-once. **The axis is DISCOVERED: a source coherent only on axis 0 mints exactly
   one style, on axis 0.**
4. **`sty_recognize_a0`** / 5. **`sty_recognize_a1`** — recognizes an item as being in a
   held style iff its offset equals a held style's delta on that axis. **SOURCE-BLIND: no
   recognition rule reads the `produced` edge or any source attribute.** Writes
   `sty_recognized_a{0,1}` and `sty_src_a{0,1}` (separate attributes per axis, so the two
   rules can never race). This is what makes DISCRIMINATION a genuinely risked test.
6. **`sty_memorize`** — the MEMORIZATION CONTROL (T2's `cat_memorize`, in-seed): fires
   iff the item's RAW `(v0,v1)` exactly equals a style's stored exemplar coordinate.

Flag `StyleParams.style`, default `0.0`. Every rule's ENABLED guard is
**ABSENCE-TOLERANT** — `Count(Filter(NodesOfType("StyleParams"), p, p.style > 0.5)) >= 1`,
deliberately **NOT** `PickUnique` (which returns `None` on an absent params node and would
silently change behaviour), per the agnosia rung's lesson.

**`Times` is NOT used anywhere in this seed** (T3's caught defect: `Times` takes an
`items` LIST, `jsonio.rs:1274`, and an `a`/`b` form parses to an EMPTY PRODUCT = 1,
silently making an invariant `Eq(1,1)` true for everything). The one list-form Term family
is avoided outright; the gate is nonetheless positive-controlled (§6).

---

## 3. The corpus (fixed in advance, and its arithmetic checked here)

Three kinds, reusing T2's signatures, each with an axis-space base:
`A sig(1,1) base(10,30)` · `B sig(2,1) base(50,30)` · `C sig(1,2) base(10,70)`.

Three STYLED sources, 6 training instances each (2 per kind), given as offsets `(r0,r1)`
added to the kind's base:

| source | styled axis | its constant offset | its FREE axis (all distinct — no accidental agreement) |
|---|---|---|---|
| **S1** | axis 0 | `r0 = 0` | `r1 = 5,10,15,20,25,30` |
| **S2** | axis 0 | `r0 = 6` | `r1 = 5,10,15,20,25,30` |
| **S3** | axis 1 | `r1 = 0` | `r0 = 3,9,12,15,18,21` |

**The anchor arithmetic, verified in advance:** every kind's members give `min r0 = 0`
(S1) and `min r1 = 0` (S3), so `dv == r` in EVERY kind ⇒ the offsets are comparable
across kinds. The free axes never collide with a held delta (`{0,6}` on axis 0, `{0}` on
axis 1): S3's `r0 ∈ {3,9,12,15,18,21}` avoids `0` and `6`; S1/S2's `r1 ∈ {5..30}` avoids
`0`.

Three HELD-OUT instances, added AFTER minting (boxes fixed), each with a raw coordinate
**provably absent from training** (the runner asserts it):
`S1 → kind A (0, 7)` · `S2 → kind B (6, 17)` · `S3 → kind C (13, 0)`.

---

## 4. Arms, statistics, and decision rules

Structural arms are all-or-none over a deterministic scene (n = 1 scene, as T2);
sampled arms are n = 100 seeds.

| arm | statistic | PASS |
|---|---|---|
| **H — STYLE DISCOVERED (headline)** | `n_styles`; per source `(n_styles_src, axis, delta)` | exactly **3** styles, **one per source**, each on the **correct DISCOVERED axis** (S1→0, S2→0, S3→1) with the correct delta, and NO source mints on its free axis |
| **G — GENERALIZATION** | per held-out: `sty_recognized`, `sty_src`, `cat_recognized`, `cat_sig`, `coord_unseen` | **3/3** held-out recognized as their OWN source's style AND as the correct KIND, every `coord_unseen = true` |
| **B — DISCRIMINATION** | `cross_false` = # items whose recognized `sty_src` ≠ its true source | **exact 0**, and each source's style is distinct |
| **X1 — THE COHERENCE CRUX (§1.1, RISKED)** | over seeds 47100–47199: `false_mint_frac` = fraction of scenes where the INCOHERENT source S4 (both axes iid `Uniform{1..40}`, 6 instances) mints ANY style; paired in the SAME scene: `styled_mint_ok` (S1–S3 still mint 3/3) and `alive` (all 6 of S4's items have `dv_set=1`) | `false_mints <= k95` (the exact binomial 95% critical value at the ANALYTIC chance rate `p_chance` of ≥3 of 6 draws from 40 being equal on either axis — computed exactly, in-runner, no seeds burned) **AND** `styled_mint_ok = 100/100` **AND** `alive = 100/100`. **DISQUALIFYING: a false-mint rate near 1.0 ⇒ universal container.** |
| **C — MEMORIZATION CONTROL** | `sum_mem` over held-outs | **0** (declared ENTAILED, §5) |
| **E — FLOOR / noise** | 100 iid-noise fields, seeds 47000–47099 | **0** categories and **0** styles (declared ENTAILED via T2's floor, §5) |
| **L — BOUND PROBE / anchor coverage** | train with S1 producing kinds A,B ONLY; test S1 in kind C | **PREDICTED REFUSAL** — see §5 |
| **D — MDL** | `k` styles from `N` items; `mdl_raw` vs `mdl_styled`; `m_min` derivation | `mdl_styled < mdl_raw` and `m_min = 3` falls out of `d_style = 2` |
| **F — DOWNSTREAM / load-bearing (§1 clause 5)** | flag ON vs OFF: `d_styles`, `d_recognized_max` | both `> 0` (`D == 0.0` ⇒ decorative ⇒ STOP) |
| **X — OFF-DAY (§9)** | flag at default | `0` styles, `0` recognitions, `0` projections; plus vision bench **200/0** with `data/`, sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved, sibling gates green |

**What a null means:** if H fails — no source mints, or every source mints on both axes,
or the offsets do not cohere across kinds — **style is not separable from within-category
noise by this mechanism, and that is the honest negative and a first-class result**
(§7). It would be reported with the diagnosis (which of: the anchor is not
source-coherent; exact agreement is too strict; the axis is not identifiable), NOT
rescued by adding a tolerance (§5).

---

## 5. §13.1 — ENTAILED vs RISKED, declared IN ADVANCE

**ENTAILED by the construction (reported as consistency, NOT banked as evidence):**

- **C — the memorization control refuses.** The held-outs have raw coordinates that are
  not any style's stored exemplar, so an exact-match control MUST return 0. This is a
  consistency check that the two channels are distinct, not a discovery.
- **E — the noise floor.** No shared signature ⇒ T2 mints no category ⇒ `sty_project`
  cannot fire ⇒ no style. Inherited from T2's already-committed floor.
- **The styled sources' offsets are constant BY CONSTRUCTION.** The corpus supplies
  sources with a constant offset on one axis — that IS the definition of a styled source.
  **The mechanism is not credited with discovering that a constant exists.**
- **F, X** — flag plumbing.

**GENUINELY RISKED (the mechanism could have produced the opposite):**

- **H — that the offsets COHERE ACROSS KINDS AT ALL.** This is the real risk and it is
  not obvious: the anchor is each category's `MinOver` box origin, minted from the pooled
  training data of ALL sources. Whether `v − anchor` is source-constant across DIFFERENT
  kinds depends on every kind's anchor being set by the same source — a property of the
  data, not of the rule. A shifted anchor in one kind destroys coherence and mints
  nothing (or two spurious styles). **Arm L is the pre-registered demonstration that this
  can fail.**
- **H — that the AXIS is DISCOVERED, not assigned.** Both axis rules run on every source.
  A source could mint on its FREE axis by accident, or on both, or on neither. Nothing
  tells the mechanism which axis is the styled one.
- **B — DISCRIMINATION.** The recognition rules are **SOURCE-BLIND** — they never read
  the `produced` edge. Pollution is mechanically possible and is refuted (or not) by the
  deltas alone.
- **X1 — THE COHERENCE CRUX.** An incoherent source is given the SAME instance count, the
  SAME categories and a comparable value spread, and its items are alive. A mechanism
  that mints a "style" for any source is a universal container and is disqualified here.
  The observed false-mint rate is compared against the EXACT analytic chance rate — the
  mechanism is NOT claimed to have infinite selectivity, and its chance-level
  false-positive rate is reported as a BOUND.

---

## 6. Positive control on the gate (§12.3 / §1 clause 4)

A gate that has only ever been seen to pass is not a gate. Before reporting, the T3
lighting defect will be INJECTED into this seed's own agreement test (rewriting the exact
`Eq` agreement into a vacuously-true form) and the gate re-run; it MUST go RED, and
reverting MUST restore green. The result of that injection is reported.

---

## 7. PREDICTION, stated in advance (§3.7)

**I predict a BOUNDED CROSSING.**

- **H passes**: 3 styles, one per source, each on the correct discovered axis. The
  arithmetic in §3 is checked, so the anchors line up; the axis discovery follows from
  exact agreement being satisfiable only on the constant axis.
- **G passes 3/3**; **B gives exact 0**; **C gives 0**; **E gives 0/100**.
- **X1: S4 mints a style in ROUGHLY 2–3 of 100 scenes** — the analytic chance of ≥3 of 6
  draws from 40 coinciding on either axis (`≈ 2.5%`), NOT 0 and NOT 100. I predict
  chance-level, and I predict the paired positive control holds (S1–S3 mint 3/3 in all
  100 scenes with S4 present, and S4's items are all alive).
- **L: I predict REFUSAL** — S1's held-out in kind C is NOT recognized as S1's style,
  because removing S1 from kind C's training moves that kind's anchor by +6 and the
  offset becomes `−6` instead of `0`. This is the mechanism's real limit and I expect the
  probe to expose it.

**Provisos that would tell me what I did not understand:** (i) if `MinOver` in effect
position over a singleton misbehaves, `sty_project` will write wrong offsets and H will
fail for a plumbing reason, not a scientific one — I will say so; (ii) if two same-type
incoming edges on `ObjItem` trip the known engine gotcha, the pool will silently
under-count — `has_obj` and `produced` are deliberately different types, and item
liveness (`dv_set`) is reported to catch it; (iii) if the free axes accidentally agree,
a source will mint two styles — the §3 corpus is chosen so they do not, and the arm
reports per-axis mints so this is visible.

---

## 8. BOUNDS declared in advance (§8) — what this rung will NOT show

- Style over the **discrete-similarity category axes** — the axes are GIVEN, not learned
  from pixels. **The learned axis-codebook at natural-image scale remains the NAMED
  FRONTIER**, as does whatever the deformation rung leaves open.
- **A style is a CONSTANT offset on an axis.** A style that is a *scaling*, a *rotation*
  of the axis pair, or a non-constant function of the instance is out of class.
- **Two sources with an IDENTICAL delta on the same axis are the SAME style** — the
  mechanism has no way to tell them apart and should not pretend to.
- **The anchor is the category's box origin**, so style is only cross-kind coherent when
  every kind's anchor is set consistently (arm L is exactly this bound).
- Style is discovered **per axis independently**; a style spread across a correlated pair
  of axes is not represented.
- **Chance-level false positives exist** (arm X1) — exact agreement over a finite value
  pool is not infinitely selective.

---

## 9. Seed ledger

**47000–47999** allocated to this rung. **47000–47099** = the noise floor (arm E).
**47100–47199** = the incoherent-source draws (arm X1). **47200–47999 remain CLEAN.** No
seed outside this block is touched.

## 10. Provenance (§10)

Engine hash + source verdict from `domains/engine_provenance.provenance_line()` is
recorded in `results/style_measure.json` and quoted in `VISION_STYLE_RESULTS.md`. Base
`main` HEAD `543b552b`, ancestor-verified. **NO new Rust is expected**; if the DSL turns
out not to express the mechanism, the gap will be justified in-code, the addition flagged
OFF, `scripts/engine_build.sh` run in THIS worktree, and the NEW engine hash recorded.
