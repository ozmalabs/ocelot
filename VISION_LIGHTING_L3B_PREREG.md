# ADVANCED LIGHTING — RUNG L3b: THE ANCHOR OF THE ANCHOR — PRE-REGISTRATION

*Written and **COMMITTED BEFORE THE RUN** (§3). Base `main` HEAD **b7c3eaeb**
(`git merge-base --is-ancestor b7c3eaeb HEAD` verified, §11). Branch
`gamma-substrate/vision-lighting-l3b`, worktree
`.claude/worktrees/agent-abaff99b9896a4b06`. Seeds **52000–52999** (the block is
CLEAN — verified against the burned-seed ledger). Flag `lighting_l3b` **OFF by
default** (§9).*

---

## THE PREMISE — what L3 measured and could not fix

L3 pooled the local illuminant estimates into one scene-level `Ĝ` and required each
locale's own `ĝ` to agree with it. The leak fell **13/1300 → 5/1300 (0.385%)** but did
not close, and the residual has a **verified self-referential mechanism**:

> **`Ĝ` IS some locale's own `ĝ`** (the pool is a Chebyshev centre, i.e. a MEDOID), so
> **that locale's deviation is EXACTLY 0 and it corroborates UNCONDITIONALLY.** On noise
> the corroborated set was measured to be exactly the Chebyshev-centre set in **10/10**
> inspected scenes, and **all 5 surviving leaks sat there at residual 0.0**.

**The white-patch assumption was PUSHED UP ONE LEVEL, not eliminated** — from 13 exposed
locales per scene to exactly 1. L3 also recorded the unflattering arithmetic: **per
exposed locale the rate WORSENED (0.92% → 5%)**; the entire gain was reducing exposures.

**THE QUESTION THIS RUNG ASKS:** *can the anchor's own anchor be corroborated, or is this
a genuine infinite regress?*

---

# STEP 1 — THE AUDIT (§12.4): candidate certifiers for `Ĝ`, classified

**A certifier is CIRCULAR if its deviation is identically 0 by construction** (it is
defined in terms of the estimate it certifies, so it cannot refuse its own centre);
**EXTERNAL if it smuggles in a new assumption** (a new white patch under another name);
**GENUINE if it breaks self-membership without importing an assumption.**

Every classification below is decided by a **MEASUREMENT**, following the standard set by
`VISION_COLOUR_BOUND_K1_RESULTS.md` and `VISION_MARGIN_RESULTS.md` — kill each rival by
measurement, then show the negative is structural rather than a failure of search.
Build-phase probe values are quoted; the confirmatory run re-measures every one of them
on the pre-registered seed block.

| # | candidate certifier for `Ĝ` | the deciding measurement | class |
|---|---|---|---|
| **C1** | **the Chebyshev centre — L3's own pool** | the centre's deviation from `Ĝ` is `\|ĝ_{L*} − ĝ_{L*}\| = 0` **by construction**; L3 measured the corroborated set == the centre set in **10/10** noise scenes, all 5 leaks at residual 0.0 | **CIRCULAR** |
| **C2** | **a second pooling statistic — the per-channel MEDIAN** (does a different statistic break self-membership?) | **NO.** The median vector coincides EXACTLY with locale 6's estimate in **5/5** headline fields (deviation identically 0 there). It loses its zero-deviation member only on *incoherent* (noise) scenes — **mean 0.04 zero-deviation locales/scene** — i.e. it breaks self-membership **precisely where the scene has no anchor to certify, and preserves it wherever the scene coheres** | **CIRCULAR** (measured; its breakage is incidental, not structural) |
| **C3** | **LEAVE-ONE-OUT mutual corroboration** — certify locale `i` against a pool computed **excluding `i`** | **BREAKS SELF-MEMBERSHIP BY CONSTRUCTION:** `Ĝ^{(−i)}` is chosen from `{ĝ_j : j ≠ i}`, so `ĝ_i` is never its own certifier. Probe: **13/13 corroborated on all 5 headline fields** (max deviation 5.273 vs envelope 14.0) and **mean 0.16/13 on noise**, with the L3 leak scene (45584) going **0/13** | **GENUINE (individually) — the one that survives; BUILT below** |
| **C4** | **cross-frame / temporal persistence** ("does the anchor persist across ticks?") | **UNAVAILABLE AND EXTERNAL.** The world has exactly ONE test frame per scene and no temporal axis — `lighting_l2_world.add_frame` (`domains/lighting_l2_world.py:43`) builds a static 1-D chain, and no adapter draws any cross-tick edge. Using it would require assuming **illuminant stationarity across ticks**, which is a new assumption of exactly the white-patch kind | **EXTERNAL** (assumes stationarity) — not measurable here, and reported as such |
| **C5** | **a physical invariant — the frame's own dynamic-range ceiling** | **ALREADY KILLED, AND RE-EXHIBITED HERE.** `VISION_COLOUR_BOUND_K1_RESULTS.md:100` rejected the measured-dynamic-range idiom **by a non-locality measurement**: same codebook, same observation, verdict FLIPS refused→admitted because of an **unrelated patch elsewhere in the field**. It also assumes a known sensor ceiling — which is *literally* the white-patch assumption ("the brightest possible value is white") | **EXTERNAL + NON-LOCAL** |
| **C6** | **redundancy across the cone channels** — require `Ĝ` to be near-achromatic (a wrong anchor identity makes `ĝ` chromatic by a reflectance ratio) | **UNSOUND, MEASURED.** It assumes an **achromatic illuminant** (the classic grey-world assumption). The substrate's OWN landed scenes violate it: T3/L1's chromatic uniform gain **(1.5, 2.5, 3.3)** yields `ĝ` chromaticity **2.169–2.314**, and **182 of 325 noise locales (56%) sit BELOW that**. Any threshold that admits the landed scene admits the majority of the noise | **EXTERNAL** (assumes achromatic illuminant) **+ unsound at the landed operating point** |

**THE AUDIT'S VERDICT: exactly one candidate — C3, leave-one-out — survives, and it
survives only in the INDIVIDUAL sense.** It removes every locale's *self*-certification.
It does **not** certify the SET, and STEP 2's REGRESS arm is designed to exhibit that
remaining hole **by measurement rather than by assertion.**

---

# STEP 2 — PRE-REGISTRATION

## §0 The mechanism to be built (composition; NO new Rust, NO new constant)

New seed **`vision_lighting_l3b`** (depends on `vision_lighting_l3`), flag
`LightingL3bParams.lighting_l3b`, **default 0.0**, read **absence-tolerantly** via
`MaxOver(..., default 0.0)` — **NEVER `PickUnique`** (process rule 3).

| rule | what it does |
|---|---|
| `l3b_pool_loo` | **THE RUNG.** Per locale `i`, the **LEAVE-ONE-OUT** scene estimate: `Argmin` over `Filter(has_locale, j ≠ i)` of `MaxOver` over the same filtered set of the L∞ disagreement. `Eq` on `Value::Node` compares by id (`runners/dsl/src/value.rs:225`), so `Not(Eq(j, loc))` is the exclusion. |
| `l3b_dev` | Records **both** deviations as first-class floats: `l3b_dev_cheb` (against L3's own `l3_G*` — **this is how the C1 circularity is EXHIBITED on the graph, not asserted**) and `l3b_dev_loo`. |
| `l3b_corroborate` | The **SAME envelope as L3**, against the locale's OWN leave-one-out pool: `ra_i,ch · \|ĝ_i,ch − Ĝ^{(−i)}_ch\| ≤ N·LS + HS + HS`. |
| `l3b_recognize` | L3's verdict with the corroboration conjunct **SWAPPED** (`l3_corr` → `l3b_corr`) and **nothing else changed** — so **L3's own `l3_*` arm, read off the SAME graph in the SAME tick, IS the exact leave-one-out ABLATION** (§13.2), exactly as L2's arm was L3's pooling ablation. |
| `l3b_refuse_uncorroborated` / `l3b_refuse_bound` | Refusal as a **POSITIVE datum**, SPLIT BY REASON (§1.1 clause 4). |

**Numeric literal set: `{0.0, 0.5, 1.0, 1.0e9}` — IDENTICAL to L2's and L3's.** The bound
is L1's own falls-out one lattice step, inherited unchanged; the envelope is L3's own,
inherited unchanged. **Nothing is re-derived and nothing is tuned.**

**THE `Times` TRAP (process rule 4).** `Times`/`Plus`/`Max` take an **`items` LIST**
(`runners/dsl/src/jsonio.rs:1274`/`:1269`/`:1403`); the `a`/`b` form parses to an **EMPTY
product = 1**, silently turning an invariant into `Eq(1,1)`. Every constructor states its
form and **the gate is positive-controlled against exactly this defect.**

## §3 Arms, decision rules, and §13.1 ENTAILED vs RISKED

Seeds: **52000–52099** noise (100 × 13 = 1300 surfaces) · **52100–52119** out-of-class
floor · **52200–52203** the regress exhibition. All comparisons are **within-run, on the
SAME graph in the SAME tick** — L3's `l3_*` arm is the ablation, so the 45560–45659 block
is NOT reused and L3's `5/1300` is quoted only as the prior rung's number on ITS OWN block.

| arm | statistic | PRE-REGISTERED decision rule | class |
|---|---|---|---|
| **A LEAVE-ONE-OUT — the sharpest candidate** *(headline)* | noise surfaces claiming under `l3b_*`, LIVE codebook, 52000–52099 | **`A ≤ 1/1300`**, and **strictly less than the L3 arm measured on the SAME seeds** | **RISKED** |
| **A′ THE ABLATION** | the SAME seeds under L3's `l3_*` arm (self-including pool) | **`> A`** — the leak must RETURN when self-membership is restored | **RISKED** |
| **B NO REGRESSION — THE CONJUNCTION** | L3's 60/60 fields · L2's 46/46 · L1 19/19 · T3 27/27 | **L3b ≥ 57/60 under the fields, ≥ 91/96 uniform, 0 false; sibling gates UNMOVED at 27/27, 19/19, 46/46, 39/39** | **RISKED** |
| **B′ DISAGREEMENT** *(process rule 5)* | rows L3 admits and L3b refuses | **NON-EMPTY on noise** (else L3b is a no-op) **and EMPTY on the headline fields** (else it costs the crossing) | **RISKED** |
| **C DISCRIMINATION** | cross-material false identities under L3b | **== 0** — declared **WEAK** in advance: a refuse-everything build scores this perfectly | **RISKED but WEAK** |
| **R1 REGRESS EXHIBITED — the C1 circularity, MEASURED** | `l3b_dev_cheb` at the Chebyshev-centre locale, over the noise block | **EXACTLY 0.0 at ≥1 locale in ≥95/100 scenes** — the certifier's own deviation is 0 **by construction, exhibited not asserted** | **ENTAILED** (declared; reported as consistency, NOT banked) |
| **R2 REGRESS NOT CLOSED — the κ-SCALE exhibition** | test reflectances scaled by **κ = 2.0**, illuminant unchanged | **L3b corroborates 13/13** while the recovered `Ĝ ≈ κ·g_true` (**4.0 vs a true gain of 2.0**) and **0 false identities** — unanimous mutual corroboration on a scene whose illuminant estimate is **wrong by a factor of 2**, undetectable by any statistic in this family | **RISKED** |
| **R3 THE TWIN RESIDUAL** | corroborated locales whose `l3b_dev_loo` is **exactly 0.0** (two locales sharing an estimate ⇒ leave-one-out can still return `ĝ_i`) | **REPORTED** — the honest residual of C3; stated with its count | reported |
| **F FLOOR** | fast-varying out-of-class fields, 52100–52119 | **≤ 25% claimed, 0 false** | **RISKED** |
| **G CANDIDATES INSIDE THE BOUND** *(process rule 7)* | `l3b_ncand` over admitted rows | **min/median/max REPORTED** | reported |
| **X OFF-DAY** (§9) | flag at default 0 | **no `l3b_*` attribute written anywhere**; T3/L1/L2/L3 unmoved; bench **200/0**; sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved | **ENTAILED** |

### PROCESS RULE 6 — every RISKED arm's FAILING INPUT, confirmed IN RANGE before the run

| arm | the input that would REDDEN it | confirmed in range? |
|---|---|---|
| **A** | a noise scene whose leave-one-out pool still corroborates the leaking locale | **YES** — L3 leaks on this class (seed 45584 measured); the 52000-block is the same generator, and the probe shows leaks are produced at ~1 per 25 scenes |
| **A′** | L3's self-including pool leaking **0** on 52000–52099 (then the ablation shows nothing) | **YES** — L3 measured 5/1300 on its own block and 1/25 scenes in probe; a 0 is possible and would redden A′ |
| **B** | any locale refused on a headline field ⇒ < 60/60 | **YES** — max leave-one-out deviation is **5.273** against an envelope of **14.0**; a mechanism error pushes any locale over |
| **B′** | an empty disagreement set on noise (no-op) **or** a non-empty one on the headline (cost) | **YES** — both directions are reachable and both are asserted |
| **C** | any admitted row whose `l3b_id ≠ expected_id` | **YES** — the noise and out-of-class arms admit rows by construction |
| **R2** | κ=2.0 corroborating **< 13/13** (then mutual corroboration DOES see the scale error) | **YES — and the boundary is measured:** deviation grows with κ (κ=2.0 → 7.75, κ=3.0 → 9.33, **κ=4.0 → 13.18**, envelope **14.0**), so this arm sits well inside a regime where it could have failed |
| **F** | > 25% claimed or any false identity | **YES** — L3 measured 3/240 on the same construction |

### §13.1 declared IN ADVANCE

- **ENTAILED (reported, NOT banked):** **X** (the seed is not boot-loaded and every rule
  is flag-gated at 0); **R1** (the Chebyshev centre's deviation from itself is 0 by
  construction — the measurement makes it VISIBLE, it does not make it surprising);
  the containment `L3b ⊆ L2` (one swapped conjunct on top of L2's verdict).
- **RISKED — this is the result:** **A**, **A′**, **B**, **B′**, **C**, **R2**, **F**.

### §12.3 POSITIVE CONTROLS — against BOTH failure modes (process rule 5, confirmed SIX times)

**A refuse-everything build scores PERFECT FLOORS and leaves discrimination GREEN. Floors
are NOT a gate.** The gate will be demonstrated red under **two independently injected
defects**, and the arms that must catch each are named **now**:

1. **REFUSE-EVERYTHING** (`LATTICE_STEP = −1.0`): must redden **B** (no-regression) and
   **B′** (the disagreement set becomes non-empty on the headline). **C and A and F will
   stay GREEN** — that is the point.
2. **ADMIT-EVERYTHING** (the corroboration envelope raised to `1.0e9`, i.e. the
   corroboration made vacuous): must redden **A** (the leak returns to the ablation's
   value) and **B′** (the disagreement set on noise becomes empty). **B, C and F stay
   green.**
3. **THE `Times` EMPTY-PRODUCT TRAP**: the a/b form injected into the envelope; must
   redden the composition tests.

**Neither floor alone is a gate; the CONJUNCTION is.** If the composition changes after
this document is committed, the arm each defect should redden will be **re-derived and
recorded** (process rule 4).

## §8 BOUNDS declared in advance

- **If the regress is real, this rung says so plainly.** The expected outcome is
  **BOTH**: leave-one-out is a real mechanism that removes the individual circularity,
  **AND** the regress is not closed — what remains is a **SET-level** hole (R2).
- **The predicted terminal statement:** *constancy on this substrate is **ANCHOR-RELATIVE**
  — the illuminant estimate is determined only up to a global reflectance/illuminant
  scale, every corroboration statistic in this family is blind to that scale, and the
  anchor is therefore an **explicit declared CHOICE, not a measurement.***
- **MULTI-ILLUMINANT scenes remain UNSOLVED regardless of this rung's outcome.**
- Inherited and NOT re-opened: reflectance GIVEN at abstract cone-triple grain;
  locale-grain registration and adjacency GIVEN, not grown; identity correspondence NOT
  given; a 1-D chain of 13 surfaces and six hand-chosen materials; the narrow admissible
  field `ρ−1 ≲ 1/c_max`.

## §5 NO METRIC SURGERY

The leak metric, the envelope, the bound, the codebook and the verdict are **inherited
verbatim from L2/L3**. Nothing in the measure may be changed to rescue a failed arm. If
**A** fails its rule, **it is reported as a failure and pinned at its measured value** —
exactly as L3 pinned its own `== 5`.

## §10 PROVENANCE

The self-audit will diff **`b7c3eaeb..<this rung's own commit SHA>`**, **tracked files
only** — both endpoints FIXED. **NOT** base→working-tree, **NOT** base→`HEAD` (HEAD moves
the moment anything merges; this exact defect has bitten three rungs), **NOT** a
repo-wide untracked scan.

## Deliverables

`seeds/vision_lighting_l3b.json` (builder `tools/build_vision_lighting_l3b.py`) ·
`domains/lighting_l3b_world.py` · `scripts/lighting_l3b_measure.py` ·
`tests/test_lighting_l3b_migrated.py` · `results/lighting_l3b_measure.json` ·
`VISION_LIGHTING_L3B_RESULTS.md` · ledger + ladder entries in `VISION_PROTOCOL.md`.
