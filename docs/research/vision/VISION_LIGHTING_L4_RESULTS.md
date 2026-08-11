# ADVANCED LIGHTING — RUNG L4: SHADOW vs REFLECTANCE EDGES — RESULTS

*Confirmatory run of `VISION_LIGHTING_L4_PREREG.md`, authored and **committed BEFORE the
run** at **`76f3c9f0`** (§3). Runner `scripts/lighting_l4_measure.py`; seed
`seeds/vision_lighting_l4.json` (builder `tools/build_vision_lighting_l4.py`); adapter
`domains/lighting_l4_world.py`; gate `tests/test_lighting_l4_migrated.py`; pinned raw
`results/lighting_l4_measure.json`. Seeds **45680–45779** (noise floor) + **45780–45799**
(randomised layouts). Base `main` HEAD **`07eeda24`**
(`git merge-base --is-ancestor 07eeda24 HEAD` verified). Branch
`gamma-substrate/vision-lighting-l4-shadow-edge`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `…/runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()` reads
  *"shared build from … — Rust source identical"*). **This rung adds NO Rust**, so the
  shared build is a legitimate build of this tree's source (§10.1 rule 4).
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE any
  file was added: 200 passed / 0 failed.**
- **NO new Rust, NO new constant, ONE new seed** (`vision_lighting_l4`, NOT boot-loaded;
  ships `LightingL4Params{lighting_l4: 0.0}` **OFF by default**). **NO committed seed file
  is edited** — T3's, L1's, L1b's, L2's, L3's and border-ownership's seeds are
  byte-identical. The only edit to a committed file is the additive
  `domains/seed_registry.py` registration, gated as **purely additive** (zero removed
  lines).

---

## VERDICT — **CROSSING, WITH THE FLOOR FAILING ITS OWN RULE AND TWO PREDICTED NEGATIVES CONFIRMED**

**L4 closes the gap L2 named. L2 recovered identities on both sides of a shadow edge
*without the system ever knowing an edge was there*; L4 knows, says which kind, and — the
part that matters — makes a cast shadow STOP BEING AN OBJECT.**

> **Shown the RAW luminance field, the UNMODIFIED border-ownership seed mints TWO
> proto-objects: the material patch AND THE CAST SHADOW. Shown the field L4 decided, it
> mints ONE — the material patch, 16 members — and the shadow is gone. A shadow boundary
> is no longer an object boundary, and a material boundary still is.**

**And the rung's most useful outputs are its failures, all three declared in advance:**

> **The pre-registered NOISE FLOOR of exactly 0 FAILS at 2/1200, and both leaks are
> random triples that happen to be NEAR-PROPORTIONAL — i.e. arm H's constructed
> ambiguity arising BY CHANCE. The floor's residual is not a separate defect; it is the
> SAME irreducible failure mode, measured a second way.**
>
> **A CHROMATIC shadow is misclassified as a material boundary, 6/6. That is the
> physically common case (blue skylight in shade vs yellow sun in light), and this rung
> does NOT solve it.**

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A SHADOW EDGE CLASSIFIED** *(headline; **ENTAILED**, §13.1)* | neutral shadow edges reading `l4_illuminant` | **36/36** + the combined scene's 8\|9 = **37/37** | 37/37 ✓ |
| **B REFLECTANCE EDGE CLASSIFIED** *(RISKED — the discrimination)* | material pairs reading `l4_reflectance` | **15/15** + the combined scene's 5\|6 = **16/16** | ≥14/16 ✓ |
| **C1 THE DEFECT IS REAL** *(RISKED positive control)* | protos minted by unedited border-ownership on RAW | **2** — roots **26** (patch) and **91** (SHADOW) | exactly 2 ✓ |
| **C2 NOT AN OBJECT BOUNDARY** *(headline; RISKED)* | protos minted on the L4 field | **1** — root **26**, members **16**; shadow root 91 **absent** | exactly 1 ✓ |
| **D NO REGRESSION — THE CONJUNCTION** *(RISKED, process rule 5)* | sibling gates + bench + orbit law | T3 **27/27** · L1 **19/19** · L2 **46/46** · L3 **39/39** · border-ownership **9/9** · bench **200/0** · orbit law unmoved | ✓ |
| **D′ DISAGREEMENT** *(RISKED, process rule 5)* | classes in ONE graph, ONE tick | **illuminant `{8\|9}`, reflectance `{5\|6}`** — both non-empty | ✓ |
| **E PENUMBRA** *(RISKED)* | ramp adjacencies reading `l4_illuminant` | **7/7 at ρ=1.15 and 7/7 at ρ=1.3**, 0 sub-lattice | ✓ **with a caveat, below** |
| **F FLOOR — noise** *(RISKED, 45680–45779)* | noise adjacencies reading `l4_illuminant` | **2/1300 → 2/1200 (0.167%)** | ==0 — **✗ FAILS** |
| **F-alive** *(§1.1 clause 4)* | noise adjacencies classified at all | **1200/1200 (100%)** — 1198 reflectance, 2 illuminant, 0 silent | ≥99% ✓ |
| **G CHROMATIC SHADOW** *(RISKED, **predicted NEGATIVE**)* | chromatic shadows reading `l4_illuminant` | **0/6** — all read `l4_reflectance` | 0/6 ✓ **the cue FAILS, as predicted** |
| **H PROPORTIONAL MATERIALS** *(RISKED, **predicted NEGATIVE**)* | proportional pairs reading `l4_illuminant` | **2/2** — a real material edge misread | 2/2 ✓ **as predicted** |
| **I BOUND OCCUPANCY** *(process rule 7)* | margin distributions, both sides | illuminant **0.000 / 0.422 / 0.780**; reflectance **11.04 / 47.24 / 76.93**; **separation ×14.16** | reported |
| **J RANDOMISED LAYOUTS** *(RISKED, 45780–45799)* | material boundaries reading `l4_reflectance` | **205/205 (100%)** | ≥95% ✓ |
| **X OFF-DAY** (§9; ENTAILED) | flag at default 0 | **no `l4_*` attribute written anywhere**; 13 components (nothing merged) | ✓ |

---

## THE CROSSING — a shadow stops being an object

All of C1 and C2 read the **SAME scene** through the **SAME committed
`vision_border_ownership` seed**; the only thing that changes is the `val` field it is
shown.

| | field shown to border-ownership | distinct values | protos minted |
|---|---|---|---|
| **C1 RAW** | observed `cL` luminance | **3** (lit bg 23 / shadowed bg 9 / patch 28) | **2** — root 26 (patch, 16), **root 91 (SHADOW, 16)** |
| **C2 L4** | `l4_val`, the graph's own component decision | **2** (bg+shadow merged / patch) | **1** — root 26 (patch, 16) |

**C1 is the arm that makes C2 mean anything.** A cast shadow on raw luminance is a
closed, enclosed, singly-surrounded region — which is precisely border-ownership's
definition of a proto-object — so it mints one. **The spurious object is real, it is
measured, and it is what L4 removes.** Had C1 read 0 or 1, C2 would have been
demonstrating nothing, and the prereg said so in advance.

And the two rectangles are classified **oppositely, on all four sides of each**:

| rectangle | boundary kinds (all four sides, both axes) |
|---|---|
| material patch (rows 2–5 × cols 2–5) | **`{l4_reflectance}`** |
| cast shadow (rows 7–10 × cols 7–10) | **`{l4_illuminant}`** |

**The 1-D combined scene shows the same fact at the component grain:** `l4_val` =
`[0,0,0,0,0,0, 6,6,6,6,6,6,6]` — split **exactly at the material edge 5\|6**, and **not
split at the shadow edge 8\|9**, which the graph classified `l4_illuminant` in the same
tick.

---

## THE MECHANISM — L2's own clause, with the quantifier moved

**The audit's central finding, and it is why this rung needed no new Rust:**

> **L4's predicate IS `l2_slowvar`'s clause with the quantifier moved from SPACE to
> WAVELENGTH.**
>
> | | question | test |
> |---|---|---|
> | **L2** (`build_vision_lighting_l2.py:357`) | do two **LOCALES** agree on one gain? | `\|a_i·ra_j − ra_i·a_j\| ≤ LS·ra_j + HS·ra_j + HS·ra_i` |
> | **L4** (this rung) | do two **CHANNELS** agree on one gain across an adjacency? | `\|c_QX·c_RY − c_RX·c_QY\| ≤ HS·(c_QX+c_RY+c_RX+c_QY) + LS + HS` |
>
> Same operator, same cross-multiplication (**no ratio is ever divided into a float** —
> the frame/continuum invariant), same two-roundings envelope. The index pair is
> (locale, locale) there and (channel, channel) here.

### L4's assumptions are STRICTLY WEAKER than L2's and L3's

This is a finding, not an omission. L4 uses **no reference frame, no `compares_to`, no
`SurfaceIdentity` codebook, no locale pairing, no spatial registration, no per-locale
gain and no pooled scene estimate.** The discrimination is intra-frame and purely local.
**L4 does not sit on top of L2/L3 — it sits beside them.** It consequently neither
inherits nor repairs L3's self-corroborating-centre residual: **"the anchor of the
anchor" is untouched, because L4 uses no anchor at all.**

### No new constant (§13)

The seed's **entire numeric literal set is `{0.0, 0.5, 1.0}`** — a **strict subset** of
L2's and L3's `{0.0, 0.5, 1.0, 1.0e9}` (L4 has no codebook, so it needs no
empty-population sentinel). Gated by `test_this_rung_adds_NO_new_constant`. Every term
of the envelope is a rounding the observation already carries; the edge threshold is
**L1's own falls-out ONE LATTICE STEP**, inherited unchanged through L2 and L3.

### The bound IS discriminative — and it is HUGGED on one side (process rule 7)

| class | n | min margin | median | max |
|---|---|---|---|---|
| **illuminant** (neutral shadows) | 36 | 0.000 | 0.422 | **0.780** |
| **reflectance** (material pairs) | 15 | **11.04** | 47.24 | 76.93 |

**The illuminant side reaches 0.78 of the bound — hugged, not comfortable — while the
reflectance side never comes within ×11 of it. Separation ×14.16.** L1b's hazard (a
landed rung whose bound never bound, invisible because only the winner was reported)
**does not reproduce**: both distributions are reported, and they are separated by the
bound rather than in spite of it. The in-graph channel-pair count is **3/3 inside for
every illuminant edge** and **0–2 for reflectance**.

---

## THE NEGATIVES — three of them, all declared before the run (§7)

### 1. THE NOISE FLOOR FAILS ITS OWN RULE — 2/1200, and the residual is arm H

The pre-registered rule was **exactly 0**. **Measured: 2 of 1200 (0.167%).** I predicted
the failure in advance (prereg §5 proviso 1: *"0–5 of 1200"*), with its mechanism — and
the mechanism is confirmed rather than asserted:

| seed | adjacency | `cR` | `cQ` | per-channel ratio Q/R | margin |
|---|---|---|---|---|---|
| 45711 | 8\|9 | (100, 44, 70) | (48, 21, 34) | **0.480 / 0.477 / 0.486** | 0.314 |
| 45771 | 11\|12 | (41, 15, 63) | (74, 28, 115) | **1.805 / 1.867 / 1.825** | 0.472 |

**Both leaks are random triples that happen to be NEAR-PROPORTIONAL** — the three
channel ratios agree to within 2%. **That is arm H's constructed ambiguity arising by
chance.** The floor's residual is therefore **not a second defect** but the **same
irreducible one**, and it is gated as such
(`test_F_BOUND_the_noise_leaks_ARE_arm_H_arising_BY_CHANCE`, which asserts the
proportionality spread is <1.05 and would go red if the diagnosis were wrong).

**The rule is pinned at its MEASURED value** (`== 2` **and** `> 0`) rather than at the
inequality, so it can neither drift into an unexamined pass nor be quietly re-read as a
success — and so that a refuse-everything build, which scores this floor **perfectly**,
reddens here.

### 2. A CHROMATIC SHADOW IS MISCLASSIFIED — 6/6, and this is the rung's real bound

A shadow whose gain is spectrally non-neutral `(×4.0, ×4.4, ×5.2)` reads
**`l4_reflectance` on all six materials**, margins 3.61–13.04. **The cue is simply wrong
there, and this is the physically common case** — a real cast shadow is lit by blue
skylight while the surround is lit by yellow sun, so the ratios genuinely do change.
**L4 handles NEUTRAL shadows. It does not handle real ones.** Stated in the prereg as a
predicted negative and confirmed.

### 3. PROPORTIONAL MATERIALS ARE MISREAD AS SHADOWS — 2/2, irreducibly

`(10,20,30)` vs `(20,40,60)` and vs `(15,30,45)` both read **`l4_illuminant`**, margin
0.000. **A material change that IS a scalar multiple is indistinguishable from an
illuminant change by ANY local ratio cue** — separating them needs identity machinery
L4 deliberately does not use. Predicted, confirmed, and it is the mechanism behind
finding 1.

### 4. A CAVEAT ON ARM E THAT THE ARM DID NOT TEST

Arm E passed 7/7 at both ramps with **0 sub-lattice adjacencies** — but the prereg's
prediction had **two halves**, and only one was exercised. I predicted that a real
penumbra's shallowest part falls **below one lattice step** and is correctly not an edge.
**At ρ=1.15 and ρ=1.3 over a base of 23, every step clears the lattice, so that half of
the prediction was never put at risk.** Reported as an untested half rather than banked
as a pass.

---

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run, honoured here

**ENTAILED — reported as consistency, NOT banked:**

- **Arm A (the headline, 37/37).** §2.2's derivation makes the envelope a **valid upper
  bound on `|D_XY|` under the neutral-illuminant hypothesis**, so a neutral shadow
  **cannot** exceed it. This is §13.1's **third category — architecture that forces the
  signature** — and it is named against myself rather than presented as a discovery.
  **Confirmed empirically by the controls: all 36 arm-A tests stayed GREEN under a build
  that calls EVERY adjacency a shadow.** What arm A genuinely tests is that the seed
  computes what the algebra says.
  **The rung's evidence is the CONJUNCTION A ∧ B ∧ G ∧ H:** one envelope must ADMIT 36
  neutral shadows, REJECT 15 material pairs, REJECT 6 chromatic shadows, and ADMIT 2
  proportional pairs. **No single arm is the result.**
- **Arm X.** Not boot-loaded, every rule flag-gated at 0 ⇒ inertness by construction.
- **C2's shadow half, PARTLY.** Once `l4_flood` merges the shadow into the background it
  cannot mint — that is what merging means. **The risked half is that the PATCH still
  mints, with the right root and 16 members**, which is exactly what a merge-everything
  build fails.

**RISKED — this is the result:** **B**, **C1**, **C2**'s patch half, **D** (demonstrated
red under an injected refuse-everything build), **D′**, **E**, **F** (**FAILED**),
**G**, **H**, **I**, **J**.

---

## THE POSITIVE CONTROLS (§12.3, process rules 4 and 5) — measured, not asserted

**Control 1 — the `Times` EMPTY-PRODUCT trap.** Injected the a/b form (an empty product
is 1, so every `D_XY` collapses to `|1−1| = 0` and **every** adjacency reads as a
shadow): **21 of 74 tests go RED** — arms **B, C2, D′, G, J, I** and the rounding check,
precisely those pre-registered. Reverting restores **74/74** with the seed **byte-equal**
to the committed one (verified by `cmp`).

**Control 2 — the REFUSE-EVERYTHING build** (`LATTICE_STEP = HALF_STEP = −1.0`: the
envelope is unsatisfiable, so nothing is ever a shadow and nothing merges): **53 of 74 go
RED, including `test_C2_…` and ALL THREE `test_Dprime_*`** — the arms that exist for
exactly this. Reverting restores **74/74**, seed byte-equal.

**AND §1.1 REPEATED ITSELF FOR THE FIFTH TIME IN THIS ARC — in BOTH directions.**

- Under **control 1** (everything is a shadow), **all 36 `test_A_a_neutral_shadow_edge_reads_ILLUMINANT`
  stayed GREEN.** The headline arm passes a build that has no discrimination at all.
- Under **control 2** (nothing is a shadow), **`test_B_every_material_pair_reads_REFLECTANCE`
  and all 6 `test_G_a_CHROMATIC_shadow_is_MISCLASSIFIED_as_reflectance` stayed GREEN**,
  and **arm F scored a PERFECT 0/1200 floor.**

**Each floor is passed by exactly one of the two broken builds, and the two broken builds
are opposites. Neither floor alone is a gate. The CONJUNCTION is** — and the arms that
caught BOTH are **C2** and **D′**, which is why the prereg required them.

---

## AUDIT (§12.4) — composition, with file:line

**VERDICT: COMPOSE. NO new Rust. NO new constant.**

| reused | where |
|---|---|
| the cross-multiplied ratio-agreement test | `_slowvar_clause`, `tools/build_vision_lighting_l2.py:357` |
| `Times` (**`items` LIST**, never a/b) | `runners/dsl/src/jsonio.rs:1274` |
| `Abs` / `Minus` / `Plus` / `Max` | `jsonio.rs:1267` / `:1270` / `:1269` / `:1403` |
| `Lte` / `Count` / `Filter` / `Exists` | `jsonio.rs:1094` / `:1148` / `:1149` / `:1159` |
| `Neighbours` (hub-scoped, never a global grab, §12.1) | `jsonio.rs:437` / `:1121` |
| `Argmin` over a `Filter`ed neighbourhood — **the label flood** | `jsonio.rs:1194`; construction is `bo_label`'s, `tools/build_vision_border_ownership.py:176` |
| the min-flood-to-fixpoint idiom (O(N) per sweep under `run_rules`) | `bo_bgflood` / `bo_label`, same file |
| `IfThenElse` (the in-graph channel-pair COUNT, report-only) | `jsonio.rs:1405` |
| `Div` (report-only margin — a CROSS-FRAME ratio, never an in-frame coordinate) | `jsonio.rs:1275` |
| the edge threshold `1.0` | **L1's own falls-out ONE LATTICE STEP**, inherited through L2/L3 |
| absence-tolerant flag read `MaxOver(…, default 0.0)` — **never `PickUnique`** | L2's `ENABLED()`, `build_vision_lighting_l2.py:219` |
| the proto-object / figure-ground stage, **UNMODIFIED and UNEDITED** | `seeds/vision_border_ownership.json` |

**Not reused, because it does not exist:** any multi-illuminant decomposition, any
spectral model of the illuminant, any identity-level corroboration. Named below.

**§0 / CLAUDE.md compliance:** every decision — whether an adjacency is an edge, which
kind it is, and which cells merge — is a seed **RULE**. The adapter
(`domains/lighting_l4_world.py`) is source-audited **on the AST**
(`test_no_python_decision_in_the_adapter`: no `If`/`IfExp` node anywhere). **That gate
caught a real violation in my own adapter during the build** — a type-normalising
conditional in `render()` — which was removed by making the illuminant an explicit
3-vector (`neutral()`), **not by widening the gate**.

---

## A PROCESS DEFECT FOUND IN MY OWN INSTRUMENT — recorded, not smoothed

**`test_this_rung_EDITS_NO_COMMITTED_SEED` compared repo-relative paths against
tree-relative ones and failed on a correct diff.** The underlying fact was verified
FIRST and independently (`git diff --name-only 07eeda24..HEAD` lists exactly this rung's
eight files and nothing else); only then was the instrument fixed, with `--relative`
(§12.3: *verify the fact, then fix the gate — never the reverse*). Two **stronger**
provenance gates were added at the same time rather than fewer:
`test_PROVENANCE_the_rungs_whole_diff_is_only_files_it_OWNS` (an immutable commit range,
tracked files only) and `test_PROVENANCE_the_seed_registry_edit_is_PURELY_ADDITIVE`
(zero removed lines).

---

## §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED.**
- **Sibling gates at their committed values:** T3 lighting **27/27** · L1 **19/19** ·
  L2 **46/46** · L3 **39/39** · border-ownership **9/9**.
- **New gate `tests/test_lighting_l4_migrated.py`: 74 passed**, and **verified to fail on
  two independently injected defects** (21 red and 53 red).
- The seed is **not boot-loaded** and ships its flag at **0**; **no committed seed file is
  edited**, so §9 holds on the files as well as at the flag.

---

## BOUNDS (§8) — what this rung does NOT do

**L4 is SINGLE-ILLUMINANT, NEUTRAL-SHADOW edge attribution by a local chromatic-ratio
test, and nothing more.**

- **CHROMATIC (spectrally non-neutral) SHADOWS ARE NOT HANDLED — measured, 6/6
  misclassified.** This is the physically common case. **NAMED, NOT BUILT (§5):** the fix
  needs a model of the illuminant's SPECTRUM (two illuminants, not one gain), which is a
  different mechanism and needs its own pre-registration.
- **PROPORTIONAL MATERIALS ARE IRREDUCIBLY AMBIGUOUS — measured, 2/2 misread**, and this
  is also the noise floor's entire residual (2/1200).
- **MULTI-ILLUMINANT scenes — unsolved even computationally.** Untouched.
- **"THE ANCHOR OF THE ANCHOR" (L3's residual recursion) — untouched.** L4 uses no anchor,
  so it neither fixes nor inherits L3's self-corroborating centre.
- **L4 CLASSIFIES EDGES; IT DOES NOT RECOVER REFLECTANCE.** No L2 or L3 arm consumes an
  L4 attribute. **Wiring the attribution back into constancy is a FURTHER rung** — and it
  is the obvious next one, since L2's two refused straddling locales are exactly the rows
  an illuminant-edge label would explain.
- **The ratio-preserving relation is NOT transitive**, and `l4_flood` takes its transitive
  closure. A chain of individually admissible steps can merge two materials that are not
  ratio-preserving with each other. **NOT tested here; NAMED.**
- **ARM E's sub-lattice half was NOT exercised** (0 sub-lattice adjacencies at both ramps).
- **The 2-D arm has ONE shadow rectangle and ONE patch**, both axis-aligned, both 4×4,
  both strictly interior, on a 12×12 field. Every number is a property of THIS scene.
- **A shadow falling ACROSS a material boundary is not tested** — the two rectangles are
  deliberately non-adjacent.
- **Inherited from T3/L1/L2/L3:** the abstract cone-triple grain, **reflectance GIVEN**,
  adjacency GIVEN not grown, deformation, style, and the learned axis-codebook at
  natural-image scale.

---

## Why this is believed

Because **it fails where it must, it was predicted to fail there in advance, and the
failures share one mechanism.** A chromatic shadow is misread 6/6; two proportional
materials are misread 2/2; and the noise floor's only two leaks turn out to be that
same proportionality arising by chance — three arms, one diagnosis, none of it patched.
Two independently injected defects turn 21 and 53 tests red, and **each of them leaves a
different floor perfectly green** — the fifth demonstration in this arc that neither
floor alone is a gate, and the first where the two broken builds are exact opposites and
each passes the other's floor.

And the headline is the one number that is not mine to claim: **the unmodified
border-ownership seed, shown raw luminance, mints a proto-object for a cast shadow.**
L4 does not argue that it should not — it changes what the seed is shown, and the
spurious object disappears while the real one stays.
