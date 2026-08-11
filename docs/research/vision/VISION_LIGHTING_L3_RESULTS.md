# ADVANCED LIGHTING — RUNG L3: GLOBAL ILLUMINANT INFERENCE — RESULTS

*Confirmatory run of `VISION_LIGHTING_L3_PREREG.md`, authored and **committed BEFORE the
run** at **`d6c35a1f`** (§3). Runner `scripts/lighting_l3_measure.py`; seed
`seeds/vision_lighting_l3.json` (builder `tools/build_vision_lighting_l3.py`); adapter
`domains/lighting_l3_world.py`; gate `tests/test_lighting_l3_migrated.py`; pinned raw
`results/lighting_l3_measure.json`. Seeds **45560–45659** (noise floor) + **45660–45679**
(out-of-class fast-varying). Base `main` HEAD **3fbfe2a8**
(`git merge-base --is-ancestor 3fbfe2a8 HEAD` verified). Branch
`gamma-substrate/vision-lighting-l3-global`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `…/runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()` reads
  *"shared build from … — Rust source identical"*). **This rung adds NO Rust**, so the
  shared build is a legitimate build of this tree's source (§10.1 rule 4). **No new
  engine hash — there is truly no `.rs` change.**
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE any
  file was added: 200 passed / 0 failed.** After the rung: **200/0**, unchanged.
- **NO new Rust, NO new constant, ONE new seed** (`vision_lighting_l3`, NOT boot-loaded;
  ships `LightingL3Params{lighting_l3:0.0}` **OFF by default**). **NO committed seed file
  is edited** — T3's, L1's, L1b's and L2's seeds are byte-identical. The only edit to a
  committed file is the additive `domains/seed_registry.py` registration (the same
  mechanism L2 used), which installs nothing unless the seed is explicitly requested.

---

## VERDICT — **THE MECHANISM WORKS AND THE HEADLINE RULE FAILS**

**The leak shrinks by more than half — 12/1300 → 5/1300 — at ZERO cost to L2's crossing,
and the V4 dissociation holds cleanly. But my pre-registered rule was ≤3/1300, and
5 > 3, so THE HEADLINE ARM FAILS ITS OWN PRE-REGISTERED DECISION RULE.**

**The residual is diagnosed, architectural, and verified — not a statistical tail:**

> **The pooled scene estimate `Ĝ` IS some locale's own `ĝ`. That locale's deviation from
> it is therefore EXACTLY 0, so it corroborates UNCONDITIONALLY — the pool's own centre
> can never be refused by the corroboration it defines.** On noise it is the **ONLY**
> locale that corroborates (verified: the corroborated set equals the Chebyshev-centre set
> in 10/10 inspected scenes; mean 1.03 of 13 locales). **So the white-patch assumption is
> not eliminated — it is PUSHED UP ONE LEVEL, from every locale to exactly ONE per scene.
> L3 removed 12 of the 13 exposures and cannot remove the 13th. That is THE ANCHOR OF THE
> ANCHOR, and it is the next rung's problem.**

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A LEAK CLOSED** *(headline; RISKED)* | noise surfaces claiming, L3 on, LIVE codebook (45560–45659) | **5/1300 (0.385%)** | ≤3/1300 — **✗ FAILS** |
| **A′ …but strictly reduced** *(the half that holds)* | same seeds, same graph | **5 vs 12 — a 58% reduction** | strictly < ✓ |
| **B NO REGRESSION — THE CONJUNCTION** *(RISKED)* | L3 correct / 60 fields, / 96 uniform | **60/60 and 96/96, 0 false**; T3 and L1 unmoved; sibling gates T3 **27/27**, L1 **19/19**, L2 **46/46** | ≥57/60, ≥91/96 ✓ |
| **B′ DISAGREEMENT** *(RISKED, process rule 5)* | rows L2 admits and L3 refuses | **7 on noise, 0 on the headline** | non-empty / empty ✓ |
| **C DISCRIMINATION** *(RISKED but declared WEAK)* | cross-material false identities | **0** | ==0 ✓ |
| **D POOLING IS LOAD-BEARING** (§13.2, RISKED) | leak with pooling ABLATED (= L2's arm, same graph) | **12/1300 — the leak RETURNS** | ≥10 ✓ |
| **D-alive** *(§1.1 cl. 4)* | the ablation arm under the fields | **12/12 — ALIVE** | ✓ |
| **E THE V4 DISSOCIATION** *(RISKED)* | lesioned arm, both halves | **CONSTANCY ABOLISHED 0/60 (intact 60/60); DISCRIMINATION INTACT 12/12, 0 false** | ✓ **HOLDS** |
| **F OUT-OF-CLASS FLOOR** *(RISKED, 45660–45679)* | fast-varying fields | **3/240 (1.25%), 0 false** | ≤25%, 0 false ✓ |
| **F′ NOVEL-MATERIAL FLOOR** | never-minted material | **0 claimed** | 0 ✓ |
| **G CANDIDATES INSIDE THE BOUND** *(process rule 7)* | `l3_ncand` over admitted rows | **min 1 / median 1 / max 1** | reported |
| **H THE COST** *(reported)* | correct rows corroboration also refuses | **0** | reported |
| **X OFF-DAY** (§9; ENTAILED) | flag at default 0 | **no `l3_*`/`l3l_*` attribute written anywhere**; T3/L1/L2 unmoved | ✓ |

---

## THE HEADLINE FAILURE, AND WHY IT IS THE MOST USEFUL THING HERE

**I predicted 0–3 of 1300 and measured 5.** The prediction was in the right direction and
the wrong place, and the rule is pinned at its measured value by
`test_A_BOUND_the_leak_SHRINKS_but_FAILS_its_pre_registered_rule` — which asserts
`== 5` **and** `> 3`, so it cannot drift into an unexamined pass.

**The failure is informative because the residual has a mechanism, and the mechanism was
verified rather than asserted:**

| noise scene | corroborated locales | Chebyshev-centre locale | leaks at |
|---|---|---|---|
| 45584 | `[0]` | `[0]` | `[0]` |
| 45607 | `[0]` | `[0]` | `[0]` |
| 45612 | `[0]` | `[0]` | `[0]` |
| 45619 | `[0]` | `[0]` | `[0]` |
| 45654 | `[0]` | `[0]` | `[0]` |
| 45573 | `[9, 10]` | `[9, 10]` | — |
| 45581 | `[12]` | `[12]` | — |
| 45600 | `[9]` | `[9]` | — |

**In every inspected scene the corroborated set IS the Chebyshev-centre set.** The centre
is self-corroborating **by construction**: `Ĝ = ĝ_{L*}`, so `|ĝ_{L*} − Ĝ| = 0 ≤` any
envelope. Corroboration is a statement each locale makes *against the pool*, and the
locale that *defines* the pool has nothing to make it against.

**All five surviving leaks are at residual EXACTLY 0.0** (gated), i.e. they are the SAME
architectural mode L2 diagnosed — a surface that IS its locale's maximum, rendered onto
itself exactly — surviving in the one locale corroboration cannot touch. All five sit at
`pos 0`, the boundary locale, which has only 2 members instead of 3 (so `P(centre is the
max)` is higher) and whose lower maximum makes it a frequent Chebyshev centre.

**The honest arithmetic, which is less flattering than the headline number.** L2 exposed
13 locales per scene and leaked 12/1300. L3 exposes **1** locale per scene — 100 at-risk
surfaces — and leaks 5. **Per exposed locale the rate went UP (0.92% → 5%), not down.**
L3 did not make the anchor assumption safer; **it reduced how many places the scene is
forced to make it.** That is a real and useful gain — and it is emphatically not the same
claim as "corroboration fixes the white-patch assumption".

---

## THE MECHANISM DOES A GREAT DEAL OF WORK — quantified

- **On noise, corroboration refuses ~12 of 13 locales** (mean corroborated **1.03/13**),
  gated by `test_corroboration_refuses_nearly_every_noise_locale`.
- **On the headline fields it refuses NOTHING** — 13/13 locales corroborate at every one
  of the five fields, and the cost in correct rows is **0**.
- **On the fast-varying out-of-class field it also corroborates 13/13** — so this is *not*
  a mechanism that simply refuses anything unusual. It discriminates a scene whose local
  estimates cohere from one whose local estimates do not, which is exactly the property a
  scene-level illuminant is supposed to have.

The pooled estimate tracks the true field: at `ρ=1.012` over `g: 2.0 → 2.31` the scene
estimate is `Ĝ_L = 2.182`, sitting inside the field's range as a centre should.

### The bound is DISCRIMINATIVE (process rule 7)

**`l3_ncand` = 1 for EVERY admitted row at every condition** — including the five leaks.
L1b's hazard (a landed rung whose bound never bound, ≥2 candidates inside it in 63/63 of
its headline regime, invisible because only the winner's residual was reported) **does not
reproduce here.** Gated by `test_G_the_candidate_count_INSIDE_the_bound_is_reported`.

---

## THE V4 DISSOCIATION — the biology's own signature, and it HOLDS

`l3_recognize_lesioned` removes the constancy stage entirely (`ĝ ≡ 1` — no anchor, no
ratio, no pooling), keeping the same codebook, the same L∞ verdict and the same bound. It
is always computed on the same graph.

| | under the illuminant FIELDS | at the REFERENCE illuminant |
|---|---|---|
| **intact** | **60/60 correct** | 12/12 correct |
| **LESIONED** | **0/60 — CONSTANCY ABOLISHED** | **12/12 correct, 0 false — DISCRIMINATION INTACT** |

**Both halves were required and both were measured.** The second half is what makes this a
dissociation rather than a dead arm (§1.1 clause 4): a lesion that killed recognition
everywhere would have scored a perfect "abolition" and meant nothing. **V4 damage leaves
colour discrimination intact but abolishes constancy — and that is what the lesioned graph
does.** Gated by `test_E_v4_CONSTANCY_is_ABOLISHED_by_the_lesion` and
`test_E_v4_DISCRIMINATION_SURVIVES_the_lesion`.

**Declared in advance (proviso 3):** the abolition half is partly ENTAILED — `ĝ ≡ 1`
obviously fails under a ×2 gain. The genuinely risked half is discrimination surviving,
and it is the half that is reported as informative.

---

## AUDIT (§12.4) — composition, with file:line

**VERDICT: COMPOSE. NO new Rust. NO new constant. A scene-level estimate with anchor
corroboration is fully expressible in held Terms.**

| reused | where |
|---|---|
| **the pool (local → scene)** | `Argmin` (`runners/dsl/src/jsonio.rs:1194`) over `Neighbours(frame,"has_locale")` (`:1121`) of `MaxOver` (`:1180`) — a nested fold, both held |
| the disagreement metric | `Abs`/`Minus`/`Max` (`:1267`/`:1270`/`:1403`) — the SAME L∞ `l2_recognize`'s verdict uses |
| the per-locale illuminant estimate | `Div` (`:1275`) over L2's stored `l2_a*`/`l2_ra*` (`tools/build_vision_lighting_l2.py:293`, `:344`) |
| the scene's extent `N` | `Count` (`:1148`) — **read from the DATA**, exactly as L1's envelope counted `n` |
| "every locale has an estimate" | `Not` + `Exists` (`:1159`) — T3's `li_mint` guard construction (`tools/build_vision_lighting.py:232`) |
| the verdict, render, codebook, bound | **extracted VERBATIM from `l2_recognize`** (`build_vision_lighting_l2.py:430`–`:521`) |
| the candidate counter | `Count` + `Filter` (`:1148`/`:1149`) — L1b's `uq_admit` construction, as a REPORTER |
| the bound `1.0` | **L1's own falls-out ONE LATTICE STEP**, inherited through L2, not re-derived, not re-tuned |
| absence-tolerant config read | `MaxOver(…, default 0.0)` — **never `PickUnique`** (process rule 3) |

**Deliberately NOT used, though held:** `Sum`/`Prod` (`:1164`/`:1170`). **A mean would be
dragged by the very outlier the corroboration exists to catch**, so the pool is the
Chebyshev centre. Gated by `test_the_pool_is_GLOBAL_over_the_frames_locales`.

**Not reused, because it does not exist:** any edge attribution, any multi-illuminant
decomposition. Named below as the frontier.

**The seed's entire numeric literal set is `{0.0, 0.5, 1.0, 1.0e9}` — identical to L2's**
(gated by `test_this_rung_adds_NO_new_constant`). The corroboration envelope
`ra·|ĝ − Ĝ| ≤ N·LS + HS + HS` falls out of L2's own per-adjacency drift budget with `N`
counted from the data.

**§0 / CLAUDE.md compliance:** every decision — the estimate, the pool, the corroboration,
the verdict, the two refusals, the lesion — is a seed **RULE**. The adapter
(`domains/lighting_l3_world.py`) contains **no conditional at all**; it is source-audited
on the **AST** (`test_no_python_decision_in_the_adapter`).

### THE ABLATION IS L2'S OWN ARM — a structural fact, gated

`l3_recognize` is `l2_recognize`'s where-clause **plus exactly one conjunct** (modulo each
seed's own flag read), asserted term-by-term by `test_L3_is_L2_plus_EXACTLY_ONE_conjunct`.
So **L2's `l2_*` arm, read off the SAME graph in the SAME tick, IS the pooling ablation** —
no duplicate rule ships — and **L3 can only ever SUBTRACT claims from L2, never widen an
invariance class.**

---

## THE POSITIVE CONTROLS (§12.3, process rules 4 and 5) — measured, not asserted

**Control 1 — the `Times` EMPTY-PRODUCT trap.** Injected the a/b form (empty product = 1):
**26 of 39 tests go RED.** Reverting restores **39/39** with the seed **byte-equal** to the
committed one (verified by `cmp`).

**Control 2 — the REFUSE-EVERYTHING build** (`LATTICE_STEP = −1.0`): **26 of 39 go RED,
including ALL 13 `test_B_no_regression_*` and BOTH `test_B_prime_*`** — precisely the arms
pre-registered to catch it. Reverting restores **39/39**, seed byte-equal.

**AND §1.1 REPEATED ITSELF FOR THE FOURTH TIME IN THIS ARC.**
`test_C_discrimination_is_exact_zero` **stayed GREEN under BOTH defects**, exactly as
pre-registered in §7. **Neither floor alone is a gate; the CONJUNCTION is.**

**TWO FURTHER HONEST NOTES ON THE CONTROLS, both stated in advance or found by them:**

1. **Arm A is a FLOOR and a refuse-everything build SCORES IT PERFECTLY.** The
   pre-registered rule "≤3/1300" would have **passed** on a build that recognizes nothing.
   It reddened in control 2 only because the gate pins the **exact measured value** (`== 5`)
   rather than the inequality. **This was written into the prereg §7 before the run**, and
   it is the reason the headline number is never reported without arm B beside it.
2. **Arm D did NOT redden under either defect** — and it could not have. D reads L2's arm,
   which my defects do not touch. **D is a test of the pooling's necessity, not a detector
   of L3-internal breakage**, and it should not be counted as one.

---

## TWO PROCESS DEFECTS FOUND IN MY OWN INSTRUMENTS — recorded, not smoothed

1. **`test_no_new_rust_is_required` walked the seed's `nodes` list as if it were Term
   trees**, so the params node's `"type": "LightingL3Params"` was reported as a missing
   Term. The instrument, not the seed, was wrong; fixed to walk `seed["rules"]` only.
2. **`test_L3_is_L2_plus_EXACTLY_ONE_conjunct` ignored that the two rules necessarily read
   DIFFERENT flags** (each seed gates on its own params node), so it counted two
   differences and failed. Fixed to compare modulo the flag conjunct — **while asserting
   that the flag read is the only other difference**, which is a strictly stronger check
   than the version that failed.

Both were caught by running the gate rather than by reading it, and neither changed a
measured result.

---

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run, honoured here

**ENTAILED — reported as consistency, NOT banked:**

- **X.** The seed is not boot-loaded and every rule is flag-gated at 0, so inertness is
  entailed by construction.
- **The `L3 ⊆ L2` containment** — structural, one added conjunct.
- **The constancy-abolition half of E** — `ĝ ≡ 1` under a ×2 gain. Declared as such in
  prereg proviso 3.

**RISKED — this is the result:** **A** (**FAILED**, 5 vs ≤3), **A′**, **B** (demonstrated
red under an injected refuse-everything build), **B′**, **C**, **D**, **E**'s
discrimination half, **F**.

---

## §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**. Its
  no-Python-thresholds scan reports *"(none — every knob is graph data)"*.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED.**
- **Sibling gates: 174 passed in one process** — T3 lighting **27/27** · L1 lighting
  **19/19** · L2 lighting **46/46** · L1b uniqueness · continuous-pose · category ·
  engine-provenance + the new gate.
- **New gate `tests/test_lighting_l3_migrated.py`: 39 passed**, and **verified to fail on
  two independently injected defects** (26 red and 26 red).
- The seed is **not boot-loaded** and ships its flag at **0**; **no committed seed file is
  edited**, so §9 holds on the files as well as at the flag.

---

## BOUNDS (§8) — what this rung does NOT do

**L3 is ONE scene-level illuminant estimate with anchor corroboration, and nothing more.**

- **THE RESIDUAL LEAK RATE IS 5/1300 = 0.385%**, and it is **the white-patch assumption
  surviving at exactly one locale per scene — the pool's own self-corroborating centre.**
  **NOT closed. NAMED, NOT BUILT (§5):** the fix would need an anchor whose identity is
  established without reference to any single locale's estimate — a genuinely
  identity-level corroboration, not an agreement-level one. Bolting a second pass on after
  seeing this failure is exactly what §5 forbids; it needs its own pre-registration.
- **Per exposed locale the leak rate did not improve** (0.92% → 5%); the gain is in
  reducing exposures from 13 to 1. Stated here so the headline number cannot be read as
  the stronger claim.
- **L4 — shadow-vs-reflectance edge ATTRIBUTION: NOT solved.** L2 already recovers
  identities on both sides of a discontinuity **without ever knowing an edge exists**;
  this rung does not touch attribution.
- **MULTI-ILLUMINANT scenes — unsolved even computationally.**
- **CORROBORATION IS NECESSARY, NOT SUFFICIENT.** A scene in which the majority of anchors
  are wrong *in the same way* would corroborate a wrong pool. That is the mechanism's
  declared failure mode and **it is NOT tested here.**
- **THE POOL IS ONE LOCALE'S ESTIMATE, not a synthesised one.** A Chebyshev centre is a
  medoid, so `Ĝ` is always some locale's `ĝ` — which is what creates the residual above.
- **SPATIAL REGISTRATION AT LOCALE GRAIN IS GIVEN** (inherited from L2, strictly stronger
  than T3/L1's frame-level `compares_to`). **ADJACENCY IS GIVEN, NOT GROWN.** **IDENTITY
  correspondence is NOT given** — that is what recognition decides.
- **A 1-D chain of 13 surfaces, radius-1 locales, six hand-chosen materials.** Every
  number here is a property of THESE materials and THIS dynamic range, **not a universal
  constant**.
- **Inherited from T3/L1/L2:** abstract cone-triple grain, **reflectance GIVEN**, the
  intrinsic global-scale ambiguity, the narrow admissible field (`ρ−1 ≲ 1/c_max`),
  deformation, style, and the learned axis-codebook at natural-image scale.

---

## Why this is believed

Because **the mechanism does what it claims where it claims it and fails where it must,
and the failure is the part that carries information.** Corroboration refuses 12 of 13
locales on noise and 0 of 13 on the crossing — it discriminates rather than filtering.
The pooling ablation restores the leak on the same graph in the same tick. The V4 lesion
abolishes constancy while leaving discrimination intact, both halves measured. Two
independently injected defects turn 26 and 26 tests red, and **both times the
discrimination floor stayed green** — the fourth demonstration in this arc that neither
floor alone is a gate.

And the two most useful outputs are the two least flattering: **a pre-registered headline
rule that failed at 5 vs ≤3 and is pinned at its measured value**, and **a residual leak
whose mechanism turns out to be the rung's own pooling operator corroborating itself** —
which is a sharper statement of the remaining problem than anything a passing run would
have produced.
