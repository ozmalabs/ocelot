# ADVANCED LIGHTING — RUNG L2: SPATIALLY-VARYING ILLUMINANT (RETINEX) — RESULTS

*Confirmatory run of `VISION_LIGHTING_L2_PREREG.md`, authored and **committed BEFORE
the run** at **`f0417465`**, with **AMENDMENT 1** (a build-phase mechanism correction,
stating the rejected design's score in advance) **also committed BEFORE the run** at
**`97eda7f5`** (§3). Runner `scripts/lighting_l2_measure.py`; seed
`seeds/vision_lighting_l2.json` (builder `tools/build_vision_lighting_l2.py`); adapter
`domains/lighting_l2_world.py`; gate `tests/test_lighting_l2_migrated.py`; pinned raw
`results/lighting_l2_measure.json`. Seeds **45440–45539** (noise floor) + **45540–45559**
(out-of-class fast-varying). Base `main` HEAD **afc195b9**
(`git merge-base --is-ancestor afc195b9 HEAD` verified). Branch
`gamma-substrate/vision-lighting-l2-retinex`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `…/runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()` reads
  *"shared build from … — Rust source identical"*). **This rung adds NO Rust**, so the
  shared build is a legitimate build of this tree's source (§10.1 rule 4). **No new
  engine hash — there is truly no `.rs` change.**
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE
  any file was added: 200 passed / 0 failed.** After the rung: **200/0**, unchanged.
- **NO new Rust, NO new constant, ONE new seed** (`vision_lighting_l2`, NOT boot-loaded;
  ships `LightingL2Params{lighting_l2:0.0}` **OFF by default**). **NO committed seed file
  is edited** — `git status` on `seeds/`, `tools/build_vision_lighting.py`,
  `tools/build_vision_lighting_l1.py` and `domains/lighting_world.py` is **clean**.

---

## VERDICT — **BOUNDED CROSSING, WITH A FLOOR THAT FAILS ITS OWN PRE-REGISTERED RULE**

**The rung crosses: a spatially-varying illuminant field is recognized 60/60 with exact-0
discrimination, where T3 and L1 — read off the SAME graph in the SAME tick — score 0/60.**
That is genuine reflectance recovery beginning to REPLACE T3's blanket refusal.

**But the honest headline is two findings, and the second is a failure I caused by
strengthening my own floor after the run:**

> **The pre-registered NOISE FLOOR is a DEAD ARM. As written it scores 0/1300 — because
> 13 random cone triples are all distinct, `li_mint` mints NOTHING, and every surface is
> refused against an EMPTY CODEBOOK. Re-run with a LIVE codebook it measures 13/1300
> (1.0%), which FAILS the pre-registered "exactly 0". 12 of those 13 are surfaces that
> ARE their own locale's MAXIMUM, matched at residual EXACTLY 0.0 — the WHITE-PATCH
> ASSUMPTION, localized, with a price tag on it for the first time.**

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A SPATIALLY-VARYING INVARIANCE** *(headline; RISKED)* | correct id / 60 under the 5 pre-registered fields | **60/60, 0 false** | ≥57/60 ✓ |
| **A′ WHERE T3/L1 REFUSED** *(ENTAILED — direction only)* | T3 and L1 correct, SAME graph, SAME rows | **T3 0/60, L1 0/60** | ✓ |
| **B DISCRIMINATION exact-0** *(RISKED — the §1.1 crux)* | cross-material false identities | **0** | ==0 ✓ |
| **C RATIOS ARE LOAD-BEARING** (§13.2, RISKED) | global-anchor ablation under the fields | **10/60** | ≤15 ✓ |
| **C-alive** *(§1.1 cl. 4 — DEAD-ARM FLOOR)* | the ablation arm at UNIFORM gains | **96/96 — ALIVE** | ≥11/12 ✓ |
| **D NO REGRESSION — THE CONJUNCTION** *(RISKED, process rule 5)* | L2 ON, 8 uniform gains × 12 | **96/96, 0 false**; T3 12/12 and L1 12/12 unmoved | ✓ |
| **E1 NOISE FLOOR as pre-registered** | noise surfaces claiming | **0/1300 — but codebook = 0** | ✓ **and WORTHLESS** |
| **E2 NOISE FLOOR, LIVE codebook** *(strengthened after the run)* | noise surfaces claiming, codebook = 6 | **13/1300 (1.0%)** | **✗ FAILS "exactly 0"** |
| **F OUT-OF-CLASS FLOOR** *(RISKED, n=20, 45540–45559)* | fast-varying fields: recognized / false | **5/240 (2.1%), 0 false** | ≤25%, 0 false ✓ |
| **G NOVEL-MATERIAL FLOOR** *(RISKED)* | never-minted material force-matched | **0**, all `l2_refused` | 0 ✓ |
| **H CANDIDATES INSIDE THE BOUND** *(process rule 7)* | `l2_ncand` over admitted rows | **min 1 / median 1 / max 1** | reported |
| **S SLOWVAR DISCOVERY** *(reported)* | locales the graph judges slowly-varying | 13 / 11 / 5 / 3 / 10 of 13 | reported |
| **X OFF-DAY** (§9; ENTAILED) | flag at default 0 | **no `l2_*` attribute written anywhere**; T3/L1 unmoved | ✓ |

---

## THE CROSSING — what T3 and L1 refuse, L2 recognizes

All three arms are read **from one graph in one tick**, so this is a measurement, not
three experiments:

| field (ρ per channel) | total range | T3 `lit_*` | L1 `l1_*` | **L2 `l2_*`** | ablation `l2g_*` | max residual | `l2_ncand` |
|---|---|---|---|---|---|---|---|
| (1.006, 1.006, 1.006) | ×1.074 | 0/12 | 0/12 | **12/12** | 2/12 | 1.000 | 1 |
| (1.008, 1.008, 1.008) | ×1.100 | 0/12 | 0/12 | **12/12** | 2/12 | 1.000 | 1 |
| (1.010, 1.010, 1.010) | ×1.127 | 0/12 | 0/12 | **12/12** | 2/12 | 1.000 | 1 |
| (1.012, 1.012, 1.012) | ×1.154 | 0/12 | 0/12 | **12/12** | 2/12 | 1.000 | 1 |
| (1.006, 1.008, 1.010) | per-channel | 0/12 | 0/12 | **12/12** | 2/12 | 1.000 | 1 |

**The mechanism is T3's, with ONE thing changed: WHERE THE ANCHOR COMES FROM.**

- `l2_locale_stats` reads a per-channel `MaxOver`/`MinOver` over the **LOCALE's** own
  membership (`Neighbours(loc,"in_locale")`, hub-scoped — never a global grab, §12.1).
  T3 and L1 read ONE anchor for the WHOLE FRAME, so a field makes that single anchor
  wrong everywhere except where it was measured.
- `l2_pair` makes the test↔reference locale pairing **the GRAPH's decision** — an
  `Eq(pos,pos)` join across `compares_to`. **The adapter draws no cross-frame edge.**
- `l2_recognize` renders the held prototype at the **LOCAL** illuminant estimate
  `ĝ_loc = a_loc / pa_loc` and admits within **ONE LATTICE STEP**. The illuminant field
  **cancels locally** — no global estimate, no path integration, which is exactly why
  this is L2 and not L3.
- The codebook is **T3's integer `li_mint` population, reused UNMODIFIED**.

### The bound is INHERITED, and "slowly varying" FALLS OUT (§13)

**No new constant exists in this seed** — its entire numeric literal set is
`{0.0, 0.5, 1.0, 1.0e9}` (the flag comparison, the half-step, L1's lattice step, and the
empty-codebook sentinel), gated by `test_this_rung_adds_NO_new_constant`.

L1's `½ + ½·(r/a)` derivation needs `r/a ≤ 1`, which held because the anchor was the
frame's maximum. **It holds verbatim at locale grain because the locale CONTAINS ITS OWN
CENTRE.** And the rung's own admissibility condition falls out too:

```
c_max · (ρ − 1)  ≲  1 lattice step      ⇒   ρ − 1  ≲  1 / c_max
```

**"Slowly varying" is the lattice step over the frame's own measured dynamic range** —
§13's *"a fraction of a dynamic range the system measures for itself"*. The **total**
admissible field variation is `ρ^(N−1)` and therefore **grows with scene extent** while
each adjacency stays sub-step. With `c_max ≈ 120` the prediction is `ρ−1 ≲ 0.008`;
**measured, the mechanism holds to ρ=1.012 and breaks at ρ=1.014.**

### The bound is HUGGED, not comfortable — pre-registered proviso 3, CONFIRMED

L1's true residuals ran **0.500–0.568** against a bound of 1.0. **L2's reach EXACTLY
1.000 at every one of the five headline conditions.** There is no slack: the admissible
slope is precisely the falls-out quantity above. Pinned by
`test_BOUND_the_bound_is_HUGGED_not_comfortable`.

### THE BOUND IS DISCRIMINATIVE — L1b's hazard does NOT reproduce (process rule 7)

Rung L1b found a landed rung (T1) whose bound **never bound** — ≥2 candidates inside it
in **63/63** of its headline regime — invisible because only the winner's residual had
ever been reported. **L2 reports the COUNT: `l2_ncand` is 1 for EVERY admitted row, at
every condition, including throughout the failure regime.** The bound is doing the
discriminating and the silent-`Argmin` hazard is absent here. Pinned by
`test_h_exactly_one_candidate_lies_inside_the_bound`.

---

## THE NEGATIVE — my floor was dead, and the live version FAILS

### E1 was a DEAD ARM (§1.1 clause 4)

The pre-registered noise floor builds **both** frames from noise. 13 random cone triples
are all distinct, so no material reaches `m_min`=2, **`li_mint` mints NOTHING**, and
every surface is refused **against an empty codebook**. `codebook_size = 0`.

**0/1300 is a perfect score bought by an absent population.** This is precisely rung 8B's
disease — *"a dead arm scores a perfect floor"* — in my own instrument, and I did not see
it until I recorded the codebook size. Pinned, as a dead arm, by
`test_e1_noise_against_an_EMPTY_codebook_is_a_DEAD_ARM_and_is_discounted`.

### E2 — the live-codebook version measures 13/1300, and that FAILS the rule

Keeping the **reference** frame as the six real materials (codebook LIVE, 6 identities,
the same recognizer scoring 60/60 elsewhere) and making only the **test** frame noise:

**13 of 1300 noise surfaces CLAIM a held identity.** The pre-registered decision rule for
arm E was **"exactly 0"**. **It fails, and it is pinned at its measured value** rather
than reported at the convenient one (`test_BOUND_e2_the_noise_floor_is_NOT_exact_zero…`).

**This is a measure made STRICTER AGAINST MYSELF after the run, which §1.1 explicitly
permits and §5 explicitly does not forbid** (§5 forbids changing a measure to *rescue* a
failure; this one *creates* one).

### THE DIAGNOSIS — it is the WHITE-PATCH ASSUMPTION, localized, with a price

**12 of the 13 are surfaces that ARE their own locale's MAXIMUM on all three channels,
matched at residual EXACTLY 0.0.** The reason is structural, not statistical:

> If a surface is its locale's maximum, then `c = a_loc`, so the prototype that is the
> **reference** locale's maximum renders to `p·(a_loc/pa_loc) = a_loc = c` — **exactly**.
> A local maximum is therefore *always* recognized as whatever material is the reference
> locale's maximum, whether or not it is that material.

Chance alone predicts ≈0.1 hits in 1300 (six prototypes × 27 in-bound lattice points over
121³). **We measured 13 — two orders of magnitude more, because the mode is
architectural.** This is T3's and L1's declared **white-patch (anchor) assumption**,
localized — and L2 is the first rung to put a **measured cost** on it: **~1% on random
input**. It does not affect the headline, because there the test scene's local maxima
*are* the reference scene's local maxima (the registration assumption holding). Pinned by
`test_BOUND_the_noise_false_positives_ARE_the_localized_white_patch_assumption`.

**NAMED, NOT BUILT (§5):** the fix would be to require the local anchor's *identity* to be
corroborated rather than assumed — which is a global/pooled statement about the scene, and
therefore **L3's job, not this rung's**. Bolting it on after seeing this failure is exactly
what §5 forbids.

---

## AMENDMENT 1, AND WHY IT IS NOT §5 SURGERY

**The build phase found that the mechanism I pre-registered was wrong, and the graph is
what said so.** §2.4's `l2_inclass` — L1's MIN clause "localized" — asks *"is this change
ONE UNIFORM GAIN?"*. **L2's entire premise is that it is not.** A radius-1 locale still
spans two adjacencies of field variation, so the clause picks up a term proportional to
the field's own slope, which is not a rounding and which its envelope cannot cover.
**Measured: it admitted 6 of 13 locales at ρ=1.008.** Not a tight bound — the wrong test.

Its principled replacement, `l2_slowvar`, tests L2's own premise (a locale's illuminant
estimate must agree with **every** adjacent locale's) and its envelope falls out with no
new constant. **But it is REPORTED, NOT A GATE, and the reason is measured:** its envelope
is **worst-case over the locale** (`p ≤ ra`) while `l2_recognize`'s is **exact for the
actual surface**. A necessary-condition pre-filter that is *tighter* than the exact test
it precedes does not filter — it discards rows the exact test correctly accepts.

| condition | `slowvar` locales | arm A **if slowvar GATED** | arm A **as shipped** |
|---|---|---|---|
| ρ=1.006 | 13/13 | 12/12 | 12/12 |
| ρ=1.008 | 11/13 | 10/12 | 12/12 |
| ρ=1.010 | 5/13 | 4/12 | 12/12 |
| ρ=1.012 | 3/13 | 2/12 | 12/12 |
| per-channel | 10/13 | 9/12 | 12/12 |
| **TOTAL** | — | **37/60** | **60/60** |

**Every number in that table was written into the pre-registration BEFORE the confirmatory
run** (AMENDMENT 1, `97eda7f5`), precisely so this choice could not later be read as
convenience. If a reader rejects the reasoning, **the gated number is 37/60 and it is
right there.** §4's arms, statistics and decision rules were not touched.

**`l2_slowvar` earns its keep as a DISCOVERY:** on the fast-varying floor it collapses to
**≤1/13 locales** — the mechanism detecting, non-circularly and without any surface
correspondence, that the field is too fast for local ratios. Gated both ways
(`test_slowvar_DISCOVERS_a_fast_field_non_circularly`,
`test_BOUND_slowvar_is_STRICTLY_MORE_CONSERVATIVE_than_the_verdict`,
`test_slowvar_gates_NOTHING_in_the_seed`).

---

## THE SHADOW EDGE — the brief's expectation was WRONG, and I said so before the run

**The brief anticipated that a shadow EDGE (a discontinuous field) would STILL be
REFUSED.** Pre-registered proviso 2 predicted the opposite, and the run confirms it:

| jump | correct | false | refused | which rows refused |
|---|---|---|---|---|
| ×1.5 | **10/12** | **0** | 2 | exactly the two whose locale STRADDLES the discontinuity (residuals 12.0, 9.0) |
| ×2.0 | **10/12** | **0** | 2 | same two (residuals 24.0, 18.0) |
| ×3.0 | **10/12** | **0** | 2 | same two (residuals 48.0, 36.0) |

**A discontinuous field is out-of-class for a GLOBAL mechanism and NOT for a LOCAL one.**
A step function is piecewise constant, so every locale except those straddling the step
sees a single gain and is discounted correctly. The refusal is **local because the
mechanism is**.

**THIS DOES NOT SOLVE L4.** L2 recovers identities on both sides of the edge **without
ever knowing an edge was there, let alone that it was a shadow**. Shadow-vs-reflectance
**attribution** is untouched. Pinned by
`test_BOUND_a_shadow_EDGE_is_NOT_refused_only_the_edge_locales_are`.

---

## THE FAILURE BOUNDARY — arm A COULD have failed (§13.1, process rule 6)

The headline's steepest condition (ρ=1.012) sits **one step below** the boundary:

| ρ | range | correct | **false** | refused | ablation |
|---|---|---|---|---|---|
| 1.010 | ×1.127 | 12 | 0 | 0 | 2 |
| **1.012** | ×1.154 | **12** | 0 | 0 | 2 |
| 1.014 | ×1.182 | **11** | 0 | 1 | 1 |
| 1.015 | ×1.196 | **7** | 0 | 5 | 1 |
| 1.020 | ×1.268 | **6** | 0 | 6 | 1 |
| 1.050 | ×1.796 | **1** | 0 | 11 | 0 |

**The failing input was stated in advance and is in range.** And the degradation is
**CONSERVATIVE everywhere — `false = 0` in every row**: the mechanism refuses, it never
claims a wrong identity. Pinned by `test_BOUND_a_steeper_field_DEGRADES…`.

**Locale-radius probe (reported):** radius 1 dominates (12/12/6 at ρ=1.006/1.010/1.020)
over radius 2 (12/11/3) and radius 3 (9/7/1). **The smallest neighbourhood is the best
one**, which is what the algebra says (a wider locale spans more field variation) — the
radius was pre-registered at 1 as *the minimum*, not tuned to this result.

---

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run, honoured here

**ENTAILED — reported as consistency, NOT banked:**

- **A′.** T3 and L1 were already measured to refuse spatially-varying scenes 20/20. Only
  the magnitude of the contrast is informative.
- **X.** The seed is not boot-loaded and every rule is flag-gated at 0, so inertness is
  entailed by construction.
- **The algebra for a locale-constant field.** A field constant *within* each locale is
  discounted exactly, by construction. **That is not what was tested** — the confirmatory
  fields vary *inside* every locale, so recovery is approximate and both the admission and
  the correctness were genuinely at risk.

**RISKED — this is the result:** **A** (fails at ρ=1.014, one step away — demonstrated),
**B**, **C** (both halves: collapse AND aliveness), **D** (demonstrated red under an
injected refuse-everything build), **E** (**failed**), **F**, **G**.

---

## THE POSITIVE CONTROLS (§12.3, process rules 4 and 5) — measured, not asserted

**Control 1 — the `Times` EMPTY-PRODUCT trap.** Injected the a/b form (empty product = 1):
**30 of 46 tests go RED.** Reverting restores **46/46** with the seed **byte-equal** to the
committed one (verified by file compare).

**AND §1.1 REPEATED ITSELF FOR THE THIRD TIME IN THIS ARC.**
`test_b_discrimination_is_exact_zero` **stayed GREEN** under the universal-container
defect — exactly as L1's own control found. **The arm that caught it was the
NO-REGRESSION arm (8 red).** The discrimination floor is passed by a broken build, again.

**Control 2 — the REFUSE-EVERYTHING build** (`LATTICE_STEP = −1.0`): **29 of 46 go RED,
including all 8 `test_d_no_regression_*`** — the arm that exists for exactly this, and
**`test_b_discrimination_is_exact_zero` stayed GREEN once more**. Reverting restores
**46/46**, seed byte-equal.

**Neither floor alone is a gate. The CONJUNCTION is** — demonstrated twice, on two
independently injected defects, in this rung alone.

---

## TWO PROCESS DEFECTS FOUND IN MY OWN INSTRUMENTS — recorded, not smoothed

1. **The pre-registered mechanism was a category error** (AMENDMENT 1, above), caught by
   the graph refusing 7 of 13 locales during the build phase.
2. **The runner's arm F shuffled the scene and NEVER PASSED IT.** All 20 out-of-class
   seeds ran the **identical** layout — the seed block did nothing, an arm that **cannot
   vary** (§1). It read `0/240`; corrected, it reads **5/240**. **It was caught by the
   GATE disagreeing with the RUNNER**, which is the entire argument for writing the gate
   independently of the runner rather than as an assertion over its output.

---

## AUDIT (§12.4) — composition, with file:line

**VERDICT: COMPOSE. NO new Rust. ONE new seed. NO new constant.**

| reused | where |
|---|---|
| the local neighbourhood / hub-scoped population | `Neighbours` (`runners/dsl/src/jsonio.rs:437`) — the SAME term `cc_contrast` and `li_frame_stats` use, pointed at a `Locale` hub instead of a frame |
| the locale's own order statistics | `MaxOver`/`MinOver` (`jsonio.rs:1180`/`:1174`) |
| the continuous cross-frame gain | `Div` (`jsonio.rs:1275`) — L1's, localized |
| the render at a continuous parameter | `Times` (`:1274`) — **`items` LIST, never a/b** |
| the continuous L∞ verdict | `Abs`(`:1267`) / `Minus`(`:1270`) / `Max`(`:1403`) — extracted from `l1_recognize`'s `_render_residual` shape |
| bins-propose-continuous-decides | `Lte`(`:1094`) + `MinOver`(`:1174`) + `Argmin`(`:1194`) — `cp_recognize`'s shape, via `l1_recognize` |
| the candidate counter (process rule 7) | `Count`(`:1148`) + `Filter`(`:1149`) — **`uq_admit`'s construction** (`tools/build_vision_uniqueness.py`), reused as a REPORTER rather than a gate |
| the "for all neighbours" quantifier | `Not` + `Exists` — T3's `li_mint` guard construction (`tools/build_vision_lighting.py:232`) |
| the discrete codebook that proposes | T3's `li_mint` (`tools/build_vision_lighting.py:232`) — **reused UNMODIFIED** |
| the bound `1.0` | **L1's own falls-out ONE LATTICE STEP** (`tools/build_vision_lighting_l1.py`, `LATTICE_STEP`) — inherited, not re-derived, not re-tuned |
| absence-tolerant config read | `MaxOver(…, default 0.0)` — **never `PickUnique`** (process rule 3), gated by `test_the_flag_is_absence_tolerant_and_never_PickUnique` |

**Not reused, because it does not exist:** any pooling of ratios along a path, any global
illuminant estimate, any edge attribution. Named below as the frontier.

**§0 / CLAUDE.md compliance:** every decision — the local anchor, the pairing, the
field-slowness discovery, the verdict, the refusal, the candidate count, the ablation —
is a seed **RULE**. The adapter (`domains/lighting_l2_world.py`) builds world scaffolding
and reads attrs; it is source-audited **on the AST** (`test_no_python_decision_in_the_adapter`:
no `If`/`IfExp` node anywhere, and no comparison mentioning a recognition attribute).

---

## §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**. Its
  no-Python-thresholds scan reports *"(none — every knob is graph data)"*.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED** (2 passed).
- **Sibling gates: 159 passed in one process** — T3 lighting · L1 lighting · L1b
  uniqueness · continuous-pose · category · colour-identity · similarity · sdloop-vision ·
  engine-provenance + the new gate.
- **New gate `tests/test_lighting_l2_migrated.py`: 46 passed**, and **verified to fail on
  two independently injected defects** (30 red and 29 red).
- The seed is **not boot-loaded** and ships its flag at **0**; **no committed seed file is
  edited at all**, so §9 holds on the files as well as at the flag.

---

## BOUNDS (§8) — what this rung does NOT do

**L2 is a SLOWLY-VARYING SINGLE illuminant field discounted by LOCAL ratios, and nothing
more.** Specifically NOT shown:

- **L3 — global illuminant inference.** L2 performs **no pooling of ratios along paths**
  and forms **no global estimate**. This is the named next rung, and the E2 failure's
  principled fix lives there.
- **L4 — shadow-vs-reflectance edge ATTRIBUTION.** L2 recovers identities on both sides of
  a discontinuity **without knowing an edge exists**. Untouched.
- **MULTI-ILLUMINANT scenes** — unsolved even computationally.
- **THE LOCALIZED WHITE-PATCH ASSUMPTION IS LOAD-BEARING AND NOW HAS A MEASURED PRICE:**
  a surface that is its own locale's maximum is recognized as the reference locale's
  maximum *by construction*, costing **13/1300 (1.0%) false claims on random input**.
- **SPATIAL REGISTRATION AT LOCALE GRAIN IS GIVEN** — strictly stronger than T3/L1's
  frame-level `compares_to`. The adapter supplies `pos`; the **pairing** is a rule's
  decision. **IDENTITY correspondence is NOT given** — that is what recognition decides.
- **ADJACENCY IS GIVEN, NOT GROWN.** L2 does not learn a retinotopy.
- **The admissible field is narrow and quantified:** per-adjacency `ρ−1 ≲ 1/c_max`
  (measured: holds to 1.012, breaks at 1.014), total range ×1.15 over 13 surfaces —
  growing with scene extent, but never fast.
- **A 1-D chain of 13 surfaces, radius-1 locales, six hand-chosen materials.** The
  boundary ρ≈1.013 is a property of THESE materials and THIS dynamic range, **not a
  universal constant**.
- **Inherited from T3/L1:** abstract cone-triple grain, **reflectance GIVEN**, the
  intrinsic global-scale ambiguity, deformation, style, and the learned axis-codebook at
  natural-image scale.

---

## Why this is believed

Because **it fails where it must, and it failed somewhere I did not predict.** The
ablation collapses (10/60) while being demonstrably ALIVE (96/96); a steeper field
degrades by refusing, never by claiming; a fast-varying field is refused with 0 false ids
and the graph *discovers* it is too fast; a never-minted material is refused everywhere;
the flag off makes it inert. Two independently injected defects turn 30 and 29 tests red,
**and both times the discrimination floor stayed green** — the third demonstration in this
arc that neither floor alone is a gate.

And the two things that would have been easiest to leave alone are the two most useful
outputs: **a pre-registered mechanism that the graph proved was the wrong test**, corrected
with the rejected design's 37/60 recorded in advance; and **a noise floor that scored a
perfect 0/1300 while measuring nothing at all**, which — once made honest — failed its own
rule at 13/1300 and handed back a diagnosed, architectural bound.
