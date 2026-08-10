# ADVANCED LIGHTING — RUNG L3b: THE ANCHOR OF THE ANCHOR — RESULTS

*Confirmatory run of `VISION_LIGHTING_L3B_PREREG.md`, authored and **committed BEFORE the
run** at **`6842c2cd`** (§3). Runner `scripts/lighting_l3b_measure.py`; seed
`seeds/vision_lighting_l3b.json` (builder `tools/build_vision_lighting_l3b.py`); adapter
`domains/lighting_l3b_world.py`; gate `tests/test_lighting_l3b_migrated.py`; pinned raw
`results/lighting_l3b_measure.json`. Seeds **52000–52099** (noise) + **52100–52119**
(out-of-class) + **52200–52203** (the regress exhibition). Base `main` HEAD **`b7c3eaeb`**
(`git merge-base --is-ancestor b7c3eaeb HEAD` verified, §11). Branch
`gamma-substrate/vision-lighting-l3b`, worktree
`.claude/worktrees/agent-abaff99b9896a4b06`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` — **shared
  build, Rust source byte-identical** to canonical (`provenance_line()` reads *"shared
  build from … — Rust source identical"*). **This rung adds NO Rust**, so the shared build
  is a legitimate build of this tree's source (§10.1 rule 4), gated by
  `test_this_rung_adds_NO_Rust` **pinned to `b7c3eaeb..<this rung's own commit>`, tracked
  files only** — **BOTH ENDPOINTS FIXED**, never base→working-tree, never base→`HEAD`
  (HEAD moves the moment anything merges; that exact defect has now bitten three rungs),
  never a repo-wide untracked scan. The pinned commit is **`cc9c1a6f`**, recorded in
  `results/lighting_l3b_provenance.json` and asserted by the gate to be an ancestor of the
  branch. The only commit after it is the one adding that pin file, and a supplementary
  test verifies that tail adds no `.rs` and touches no earlier lighting seed.
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE any
  file was added: 200 passed / 0 failed.**
- **NO new Rust, NO new constant, ONE new seed** (`vision_lighting_l3b`, NOT boot-loaded;
  ships `LightingL3bParams{lighting_l3b: 0.0}` **OFF by default**). **NO committed seed
  file is edited** — T3's, L1's, L1b's, L2's and L3's seeds are byte-identical. The only
  edit to a committed file is the additive `domains/seed_registry.py` registration (the
  same mechanism L2 and L3 used), which installs nothing unless the seed is requested.

---

## VERDICT — **BOTH HALVES LANDED: THE MECHANISM SURVIVES AND THE REGRESS IS REAL**

**The audit found exactly one non-circular, non-external certifier — LEAVE-ONE-OUT — and
it closes the leak completely at zero cost to the crossing. And it still does not certify
the anchor, because it certifies each locale by the others and NOTHING certifies the set.**

> **THE LEAK CLOSES: 0/1300.** L3's self-including pool, read off the SAME graph in the
> SAME tick, leaks **6/1300** — and **all six sit at residual exactly 0.0 in scenes where
> L3 corroborated exactly ONE locale and L3b corroborated NONE.** The self-corroborating
> medoid was the entire remaining leak, and excluding a locale from its own pool removes it.
>
> **AND THE REGRESS IS REAL.** With every reflectance scaled by **κ = 2.0**, all **13/13**
> locales corroborate **unanimously** while the recovered illuminant estimate is **4.0
> against a true gain of 2.0** — **wrong by exactly κ, with zero false identities.**
> Mutual corroboration only ever compares locales to *each other*; it is blind by
> construction to an error every locale shares. **The anchor's anchor is not measured. It
> is CHOSEN.**

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A LEAVE-ONE-OUT** *(headline; RISKED)* | noise surfaces claiming, LIVE codebook, 52000–52099 | **0/1300 (0.000%)** | ≤1/1300 **and** < A′ — **✓ PASSES** |
| **A′ THE ABLATION** *(RISKED)* | same seeds, L3's self-including pool, SAME graph SAME tick | **6/1300 (0.462%) — the leak RETURNS**, all 6 at residual exactly 0.0 | > A ✓ |
| **B NO REGRESSION — THE CONJUNCTION** *(RISKED)* | L3b correct / 60 fields, / 96 uniform | **60/60 and 96/96, 0 false**; L3 **60/60**, L2 **60/60**, L1 **96/96**, T3 **36/96** — all UNMOVED | ≥57/60, ≥91/96, 0 false ✓ |
| **B′ DISAGREEMENT** *(RISKED, process rule 5)* | rows L3 admits and L3b refuses | **6 on noise, 0 on the headline** | non-empty / empty ✓ |
| **C DISCRIMINATION** *(RISKED but declared WEAK)* | cross-material false identities | **0** | ==0 ✓ |
| **R1 THE CIRCULARITY, EXHIBITED** *(ENTAILED)* | locales at `l3b_dev_cheb` **exactly 0.0** | **100/100 noise scenes**, and **exactly 1 on every headline field** | ≥95/100 ✓ |
| **R2 THE REGRESS — the SET is uncertified** *(RISKED)* | κ = 2.0 | **13/13 corroborated; `Ĝ` = 4.0 vs TRUE 2.0; 0 false** | ✓ **THE NEGATIVE HOLDS** |
| **R3 THE TWIN RESIDUAL** *(reported)* | corroborated locales at `l3b_dev_loo` exactly 0.0 | **12 of 1300 — real, and UNEXERCISED (none leaked)** | reported |
| **F OUT-OF-CLASS FLOOR** *(RISKED, 52100–52119)* | fast-varying fields | **3/240 (1.25%), 0 false** | ≤25%, 0 false ✓ |
| **G CANDIDATES INSIDE THE BOUND** *(process rule 7)* | `l3b_ncand` over admitted rows | **min 1 / median 1 / max 1** | reported |
| **X OFF-DAY** (§9; ENTAILED) | flag at default 0 | **no `l3b_*` attribute written anywhere**; T3/L1/L2/L3 unmoved | ✓ |

---

# PART A — THE AUDIT (§12.4): six candidate certifiers, each killed or kept BY MEASUREMENT

**This table is the rung's payload**, exactly as L1b's audit table was. A certifier is
**CIRCULAR** if its deviation is identically 0 by construction, **EXTERNAL** if it smuggles
in a new assumption (a white patch under another name), **GENUINE** if it breaks
self-membership without importing one.

| # | candidate certifier for `Ĝ` | the measurement that decided it | class |
|---|---|---|---|
| **C1** | **the Chebyshev centre — L3's own pool** | `\|ĝ_{L*} − ĝ_{L*}\| = 0` by construction. **Measured on the graph, not argued:** `l3b_dev_cheb` is **exactly 0.0 at some locale in 100/100 noise scenes** and at **exactly one locale on all 5 headline fields**. L3's 5 leaks and this run's 6 ablation leaks all sit there | **CIRCULAR** |
| **C2** | **a second pooling statistic — the per-channel MEDIAN** | **NO, it does not break self-membership.** The median vector coincides EXACTLY with locale 6's estimate on **5/5** headline fields. It loses its zero-deviation member only on *incoherent* scenes (**mean 0.04 zero-deviation locales/scene** on noise) — i.e. it breaks **precisely where there is no anchor to certify** and stays circular wherever the scene coheres. A different statistic, the same hole | **CIRCULAR** |
| **C3** | **LEAVE-ONE-OUT mutual corroboration** | **BREAKS SELF-MEMBERSHIP BY CONSTRUCTION** — the `Argmin` ranges over `{ĝ_j : j ≠ i}`, so `ĝ_i` is never its own certifier. **Measured: 13/13 on all 5 headline fields (max deviation 5.273 vs envelope 14.0), mean 0.14/13 on noise, leak 0/1300** | **GENUINE — individually. BUILT.** |
| **C4** | **cross-frame / temporal persistence** | **UNAVAILABLE AND EXTERNAL.** The world has ONE test frame per scene and no temporal axis — `domains/lighting_l2_world.py:43` builds a static 1-D chain and no adapter draws a cross-tick edge. Using it assumes **illuminant stationarity across ticks**, a new assumption of exactly the white-patch kind | **EXTERNAL** (assumes stationarity) |
| **C5** | **a physical invariant — the frame's dynamic-range ceiling** | **ALREADY KILLED BY MEASUREMENT, and for a reason that stands here.** `VISION_COLOUR_BOUND_K1_RESULTS.md:100`: same codebook, same observation, the verdict **FLIPS refused→admitted (bound 15.0 → 200.0) because of an unrelated patch elsewhere in the field** — **NON-LOCAL**. It also assumes a known sensor ceiling, which is *literally* "the brightest possible value is white" | **EXTERNAL + NON-LOCAL** |
| **C6** | **redundancy across the cone channels** (require `Ĝ` near-achromatic) | **UNSOUND AT THE SUBSTRATE'S OWN OPERATING POINT.** It assumes an **achromatic illuminant** (grey-world). T3/L1's landed chromatic uniform gain **(1.5, 2.5, 3.3)** yields `ĝ` chromaticity **2.169–2.314**, and **182 of 325 noise locales (56%) sit BELOW that** — so any threshold admitting the landed scene admits the **majority** of the noise. Choosing one after seeing both distributions is the magic number `VISION_MARGIN_RESULTS.md` rejected as **M6** | **EXTERNAL** (assumes achromatic illuminant) **+ unsound** |

**THE AUDIT'S VERDICT: exactly one candidate survives, and only in the INDIVIDUAL sense.**
Every other route is either the same circularity wearing a different statistic, or a new
assumption smuggled in as a physical fact.

---

# PART B — WHAT LEAVE-ONE-OUT ACTUALLY DID

## The leak closes, and the mechanism is verified rather than inferred

**All six ablation leaks are the SAME architectural mode**, and the readback shows it
locale-by-locale:

| noise scene | L3 (self-including) leaks | L3 corroborated locales | L3b corroborated locales | L3b leaks |
|---|---|---|---|---|
| 52007 | 1 | **1** | **0** | **0** |
| 52033 | 1 | **1** | **0** | **0** |
| 52038 | 1 | **1** | **0** | **0** |
| 52055 | 1 | **1** | **0** | **0** |
| 52061 | 1 | **1** | **0** | **0** |
| 52092 | 1 | **1** | **0** | **0** |

**In every leaking scene L3 corroborated exactly ONE locale — its own medoid — and L3b
corroborated NONE.** Mean corroborated locales on noise: **L3 1.07/13, L3b 0.14/13**.
All six L3 leaks are at **residual exactly 0.0**; L3b's count at residual 0.0 is **0**.

## It costs nothing, and it is not merely a stricter filter

- **On the 5 headline fields it refuses NOTHING** — 13/13 locales corroborate on every
  field, `l3b_ncand` is **1/1/1**, and the disagreement set on the headline is **empty**.
- **On the 8 uniform gains, 13/13 corroborate and L3b scores 96/96.**
- **On the fast-varying OUT-OF-CLASS field it also corroborates 13/13** — so this is *not*
  a mechanism that refuses anything unusual. Like L3's, it discriminates a scene whose
  local estimates cohere from one whose local estimates do not.

## The bound BINDS (process rule 7)

**`l3b_ncand` = 1 for EVERY admitted row on every headline field.** L1b's hazard — a
landed bound that never bound, invisible because only the winner's residual was reported —
**does not reproduce here.**

## R3 — leave-one-out's OWN residual, reported and not smoothed

**12 corroborated locales of 1300 still sit at `l3b_dev_loo` EXACTLY 0.0.** That is the
**TWIN** case: when two locales share an estimate, the leave-one-out pool can return `ĝ_i`
after all, and the exclusion buys nothing. **The hole is real. At n=100 it is
UNEXERCISED — none of the 12 produced a leak** — and it is pinned at its measured value so
it cannot drift unexamined. **Leave-one-out is not a proof; it is a mechanism whose
failure mode is now named and counted.**

---

# PART C — THE DERIVED NEGATIVE: the regress is real, and it is a SCALE

**This is the part that does not go away, and it was the predicted outcome.**

Leave-one-out removes every locale's *self*-certification. It does **not** certify the
**SET**. Exhibited by measurement rather than asserted: scale every reflectance in the test
frame by κ and leave the illuminant alone. That is a **different physical scene**
(reflectances κ×, illuminant `g`) which is **indistinguishable** from (reflectances 1×,
illuminant κ`g`). Every locale's anchor is wrong **in the same way**, so every locale
agrees:

| κ | locales corroborated | max deviation / envelope | recovered `Ĝ_L` | TRUE gain | false ids |
|---|---|---|---|---|---|
| 0.5 | **13/13** | 2.12 / 14.0 | **1.0** | 2.0 | 0 |
| **2.0** *(the pre-registered point)* | **13/13** | 7.75 / 14.0 | **4.0** | 2.0 | **0** |
| 3.0 | **13/13** | 9.33 / 14.0 | **6.0** | 2.0 | 0 |
| 4.0 | **13/13** | 13.18 / 14.0 | **8.1** | 2.0 | 0 |

**In every case the recovered illuminant is exactly κ times the true one, every locale
corroborates unanimously, and not one identity is false.** The graph cannot tell the two
worlds apart, and **no statistic that compares locales to each other ever will** — that is
not a limitation of *this* pool, it is a property of the whole family.

**THE ARM COULD HAVE FAILED AND THE FAILING INPUT WAS CONFIRMED IN RANGE BEFORE THE RUN**
(process rule 6): the deviation grows with κ and reaches **13.18 against an envelope of
14.0** at κ=4, so a mechanism that saw the shared scale would have refused here.

## WHAT CONSTANCY ON THIS SUBSTRATE THEREFORE IS (§8)

> **Constancy on this substrate is ANCHOR-RELATIVE. The illuminant estimate is determined
> only up to a global reflectance/illuminant scale; every corroboration statistic in this
> family is invariant to that scale; and the anchor is therefore an EXPLICIT DECLARED
> CHOICE, not a measurement.**

The regress terminates, but not by being closed — it terminates by **bottoming out in a
choice**. Each rung pushed the white-patch assumption up one level (T3/L1: every surface →
L2: every locale → L3: one locale per scene → **L3b: none — and instead one scene-level
scale that is fixed by declaration**). **L3b is where that ladder ends on this substrate**,
and the honest statement is that the last step is a convention, not an inference.

**What would be needed to do better is named and NOT built (§5):** a certifier outside the
comparison family altogether — a known reflectance, a known source, or a physical constraint
tying the scale to something the scene does not itself define. Every one of those is an
**EXTERNAL** anchor by the audit's own definition. **There is no internal escape**, and
inventing one after seeing this result is exactly what §5 forbids.

---

## THE POSITIVE CONTROLS (§12.3, process rules 4 and 5) — measured, not asserted

**Three independently injected defects, each pre-registered with the arm it should redden:**

| control | injected defect | tests RED | arms that reddened | arms that stayed GREEN |
|---|---|---|---|---|
| **1 REFUSE-EVERYTHING** | `LATTICE_STEP = −1.0` | **10 of 29** | **B** (0/60, 0/96) and **B′** (headline disagreement 60) — **exactly as pre-registered** | **A (0/1300 — a PERFECT FLOOR), C, and the leak rate** |
| **2 ADMIT-EVERYTHING** | corroboration envelope made vacuous (`1.0e9`) | **5 of 29** | **A** (leak returns to **10/1300**, worse than the ablation) and **B′** (noise disagreement → 0) — **exactly as pre-registered** | **B, C, F** |
| **3 `Times` EMPTY-PRODUCT** | the a/b form (empty product = 1) | **10 of 25** | the dedicated trap test, the composition tests, B, B′ | **A, C** |

**Reverting each restores 29/29 with the seed BYTE-EQUAL to the committed one (`cmp`
verified), and re-running the runner reproduces `results/lighting_l3b_measure.json`
**bit-identical in every measured value** (the only byte that moves is `elapsed_s`,
wall-clock).**

### AND §1.1 REPEATED ITSELF FOR THE **SEVENTH** TIME IN THIS ARC

**`test_C_discrimination_is_exact_zero` stayed GREEN under ALL THREE defects, and
`test_A_the_leak_CLOSES` stayed GREEN under the refuse-everything build.** A build that
recognizes nothing scores this rung's headline **perfectly**.

**The headline arm A is a FLOOR, and it is only a result because of the conjunction beside
it:** B's 60/60 + 96/96, B′'s two-directional disagreement, and the ablation A′ on the same
graph. **The gate pins every headline number at its MEASURED value** (`== 0`, `== 6`,
`== 60`, `== 12`, …) rather than at its pre-registered inequality, which is the only reason
controls 1 and 3 could redden it at all. **Neither floor alone is a gate; the CONJUNCTION
is.**

---

## AUDIT (§12.4) — composition, with file:line

**VERDICT: COMPOSE. NO new Rust. NO new constant.** Leave-one-out is fully expressible in
held Terms.

| reused | where |
|---|---|
| **the exclusion — THE RUNG ITSELF** | `Filter` (`runners/dsl/src/jsonio.rs:1149`) with `Not`(`:1266`) + `Eq`(`:1086`); **`Eq` compares `Value::Node` BY ID** (`runners/dsl/src/value.rs:225`) |
| the pool | `Argmin` (`jsonio.rs:1194`) over `MaxOver` (`:1180`) — L3's own nested fold, **only the SET it ranges over changed** |
| the disagreement metric | `Abs`/`Minus`/`Max` (`:1267`/`:1270`/`:1403`) — extracted VERBATIM from L3's `_disagreement` |
| the envelope | `Plus`/`Times` (`:1269`/`:1274`) over `l3_n_loc` — **L3's OWN, inherited unchanged**, gated by `test_the_envelope_is_L3s_OWN_inherited_unchanged` |
| the verdict, render, codebook, bound | **extracted VERBATIM from `l3_recognize`**, which extracted them from `l2_recognize` |
| the candidate counter | `Count` + `Filter` (`:1148`/`:1149`) — L1b's construction, as a REPORTER |
| the degenerate-frame guard | `Count(others) > 0.5` — a single-locale frame REFUSES rather than folding over an empty set (§1.1) |
| absence-tolerant config read | `MaxOver(…, default 0.0)` — **never `PickUnique`** (process rule 3) |

**The seed's entire numeric literal set is `{0.0, 0.5, 1.0, 1.0e9}` — IDENTICAL to L2's and
L3's** (gated by `test_this_rung_adds_NO_new_constant`). **§5 was not breached: the
envelope was NOT widened** to accommodate leave-one-out's necessarily larger deviations —
the build-phase probe confirmed the headline fields clear L3's own envelope with margin
(max 5.273 vs 14.0) **before the rule was written**.

**§0 / CLAUDE.md compliance:** every decision — the pool, the two deviations, the
corroboration, the verdict, the two refusals — is a seed **RULE**. The adapter
(`domains/lighting_l3b_world.py`) contains exactly ONE conditional, a `radius is None`
passthrough, and is source-audited on the **AST** (`test_no_python_decision_in_the_adapter`).

### THE ABLATION IS L3'S OWN ARM — a structural fact, gated

`l3b_recognize` is `l3_recognize` with the corroboration conjunct **SWAPPED** (`l3_corr` →
`l3b_corr`) and nothing else, asserted term-by-term by
`test_L3b_is_L3_with_EXACTLY_ONE_SWAPPED_conjunct`. So **L3's `l3_*` arm, read off the SAME
graph in the SAME tick, IS the leave-one-out ablation** — no duplicate rule ships — and
since the render clause is untouched, **L3b remains a SUBSET of L2's verdict and can never
widen an invariance class.**

---

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run, honoured here

**ENTAILED — reported as consistency, NOT banked:**

- **X.** The seed is not boot-loaded and every rule is flag-gated at 0, so inertness is
  entailed by construction.
- **R1.** The Chebyshev centre's deviation from itself is 0 by construction. **The
  measurement makes it VISIBLE on the graph; it does not make it surprising.**
- **The `L3b ⊆ L2` containment** — structural, one swapped conjunct on an untouched render.

**RISKED — this is the result:** **A** (PASSES, 0/1300), **A′**, **B**, **B′**, **C**,
**R2** (the derived negative), **F**.

---

## §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**. Its
  no-Python-thresholds scan reports *"(none — every knob is graph data)"*.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED.**
- **Sibling gates green:** T3 lighting **27/27** · L1 lighting **19/19** · L2 lighting
  **46/46** · L3 lighting **39/39** · L4 **74/74** · margin **21/21** · colour-bound-k1
  **25/25** — **276 passed in one process** together with this rung's own gate.
- **New gate `tests/test_lighting_l3b_migrated.py`: 29 passed**, and **verified to fail on
  three independently injected defects** (**10, 5 and 10 red**, each reddening exactly the
  arms pre-registered for it).
- The seed is **not boot-loaded** and ships its flag at **0**; **no committed seed file is
  edited**, so §9 holds on the files as well as at the flag.

---

## BOUNDS (§8) — what this rung does NOT do

**L3b is leave-one-out mutual corroboration and a derivation about what corroboration can
never reach. Nothing more.**

- **THE REGRESS IS REAL AND IS STATED PLAINLY.** Constancy here is **anchor-relative**; the
  scene's illuminant is recoverable only **up to a global scale**; **the anchor is a
  declared choice.** The κ-sweep is the measurement, not an argument.
- **THE RESIDUAL LEAK RATE IS 0/1300 — and a refuse-everything build scores that too.**
  It is a result only in conjunction with B (60/60, 96/96), B′ and the ablation A′.
- **THE TWIN RESIDUAL IS UNCLOSED.** 12 corroborated locales of 1300 still sit at
  deviation exactly 0. **NAMED, NOT BUILT (§5).**
- **CORROBORATION IS STILL NECESSARY, NOT SUFFICIENT** — inherited from L3 and now
  *demonstrated*: the κ scenes are exactly the case where the majority of anchors are wrong
  in the same way and corroborate anyway.
- **MULTI-ILLUMINANT scenes remain UNSOLVED — computationally, not just here.**
- **L4 — shadow-vs-reflectance edge ATTRIBUTION — is a separate rung and is not touched.**
- **SPATIAL REGISTRATION AT LOCALE GRAIN IS GIVEN** (inherited from L2). **ADJACENCY IS
  GIVEN, NOT GROWN. IDENTITY correspondence is NOT given.**
- **A 1-D chain of 13 surfaces, radius-1 locales, six hand-chosen materials.** Every number
  here is a property of THESE materials and THIS dynamic range, **not a universal
  constant.** In particular the κ-sweep's envelope headroom (13.18 vs 14.0 at κ=4) is a
  property of this scene size.
- **Inherited from T3/L1/L2/L3:** abstract cone-triple grain, **reflectance GIVEN**, the
  intrinsic global-scale ambiguity (**which this rung has now measured rather than merely
  declared**), the narrow admissible field (`ρ−1 ≲ 1/c_max`), deformation, style, and the
  learned axis-codebook at natural-image scale.

---

## Why this is believed

Because **the one candidate the audit kept was kept for a structural reason and then
behaved exactly as that reason predicts**, and because **the negative was exhibited by
measurement rather than argued.** The circularity L3 diagnosed is now read off the graph in
100/100 scenes as a literal 0.0. The six ablation leaks each sit in a scene where L3
corroborated its medoid and L3b corroborated nothing. The crossing is untouched at 60/60
and 96/96 with a bound that binds at one candidate. Three independently injected defects
turn **10, 5 and 10** tests red, and **all three times the discrimination floor stayed green** —
the seventh demonstration in this arc that neither floor alone is a gate.

And the most useful output is again the least triumphant one: **a mechanism that closes its
leak completely, together with a measurement showing that what it closed was never the real
problem.** The white-patch assumption has not been eliminated at any rung of this ladder —
it has been moved, four times, until what remains is a single global scale that the agent
must simply **declare**. **That is the terminus of the constancy track on this substrate,
and it is a choice, not a measurement.**
