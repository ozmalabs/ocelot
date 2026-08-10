# VISION — COLOUR IDENTITY'S REFUSAL BOUND: the PACKING RADIUS of the minted codebook (PRE-REGISTRATION)

*Written and COMMITTED BEFORE the confirmatory run (§3). Base `main` HEAD
**afc195b9** (`git merge-base --is-ancestor afc195b9 HEAD` verified, §11). Branch
`gamma-substrate/colour-refusal-bound-t1`. Engine **`7d5f50c18673`** @
`runners/dsl/python/substrate_rs/_native.abi3.so` — shared build, **Rust source
byte-identical** to canonical (this rung adds **NO Rust**, so the shared build is
legitimate, §10.1 rule 4). Baseline vision bench measured on this worktree **BEFORE
any file was added: 200 passed / 0 failed** with `data/` symlinked (§10.2); its
no-python-thresholds scan reports *"(none — every knob is graph data)"*.*

*A DEFECT FIX for a LANDED rung. `VISION_UNIQUENESS_RESULTS.md` (L1b) audited every
merged codebook rung for the silent-`Argmin` hazard and found `ci_assign`
(`seeds/vision_colour_identity.json`) to be **the worst case in the table**: an
`Argmin` over `NodesOfType(ColourCategory)` with **ZERO `Lte`** — no admission bound
of any kind. A probe at opponent distance **269.52** is confidently assigned; the
equidistant probe is decided by a margin of **exactly 0.0000**. It cannot refuse,
ever. This rung adds a refusal bound that **FALLS OUT of the construction** (§13),
flag-gated **OFF by default** (§9), and MEASURES the delta to the two landed rungs
that depend on colour identity. Written and COMMITTED BEFORE the confirmatory run
(§3). Seeds (burned-seed ledger) **50000–50999** — none used before this rung
(highest prior burn: 49999).*

## STEP 1 — AUDIT (§12.4, file:line): what could yield a falls-out bound, and does it compose?

**VERDICT: COMPOSE — the bound is the codebook's own PACKING RADIUS. NO new Rust.
NO new seed. ONE seed edit (v1.1.0 → v1.2.0), flag OFF by default.**

### The defect, in the source

`ci_assign` (`tools/build_vision_colour_identity.py:219`, emitted to
`seeds/vision_colour_identity.json`) has this `where`:

```
Gt(A(PickCIP(),"identity"), Lit(0.5))          # flag
NoAchromatopsia()                              # lesion guard
_all_op_done                                   # opponent field complete
Gt(Count(NodesOf("ColourCategory")), Lit(0))   # a codebook exists
Not(Eq(A(R,"assigned_epoch"), A(scene,"epoch")))  # re-decode re-arm
```

There is **no predicate on `_dist` at all** (`:211-217`). The `Argmin` at `:217`
ranks; nothing admits. Confirmed against L1b's raw measurement
(`results/uniqueness_measure.json:135-190`): `has_admission_bound: false`,
`far_out_of_gamut.sign_dist = 269.5199`, `refused = 0`, `equidistant.margin = 0.0`.

### The four candidate derivations — audited, three REJECTED on measurement

| candidate | derivable? | value on the landed codebook | verdict |
|---|---|---|---|
| **mint cluster extent** | yes, but **degenerate** | `ci_mint_category` clusters by EXACT value (`Eq(crg)∧Eq(cby)`, `:127-131`), so every member sits at distance **0** from its prototype. Empirical extent ≡ **0**. | **REJECTED — REGRESSES.** A bound of 0 admits only exact matches and refuses colour-identity's own landed arm A(b) (the off-prototype probe at `(6,0)` → `(10,0)` at **dist 4**). |
| **lattice step** (L1's falls-out bound: ONE step of the in-frame integer lattice) | yes | **1.0** | **REJECTED — REGRESSES.** 1.0 < 4 ⇒ refuses arm A(b). |
| **MDL radius from `m_min`/`d`** | **no** | `m_min = 3` is a **COUNT** gate (`m > d/(d−1)`, `:164-170`). The seed's cost model charges `k·d + N` — 1 unit per label, residual treated as free — so it constrains how MANY members a category needs, **never how far a member may lie**. There is no radius anywhere in the MDL accounting. | **REJECTED — NOT DERIVABLE.** Any radius read out of it would be invented, not derived. |
| **PACKING RADIUS of the codebook** (half the minimum inter-prototype distance) | **yes** | **7.8102** on the 3-category codebook `{(−10,0),(0,12),(10,0)}`; **10.0** on achromatopsia's 2-category codebook `{(±10,0)}`; **undefined** at k=1 | **ACCEPTED** (derivation below). |

### THE DERIVATION — why the packing radius falls out

`ci_assign` is a **dequantizer**: it decodes an observation against a codebook of
minted quanta. For a codebook `{c_i}`, the largest ball around a prototype that is
guaranteed to lie entirely inside that prototype's own Voronoi cell — equivalently,
the largest radius at which the codebook's own quanta **do not overlap** — is

  **r_i = ½ · min_{j≠i} ‖c_i − c_j‖**

the codebook's **packing radius**. Two balls of radius `r` around prototypes
separated by `D` are disjoint iff `2r ≤ D`; that is the *definition* of
non-overlapping quanta, not a tuned quantity. So the admission test is

  **admit iff `2 · dist(R, winner) ≤ min_{c ≠ winner} dist(winner, c)`**

**Why this is a falls-out bound and not a magic number (§13):**

1. It is a **function of the minted codebook**, not a literal. It is recomputed as
   the codebook grows (the `codebook_epoch` re-arm already re-decodes).
2. **It takes different values on different codebooks and I chose neither** —
   7.8102 on colour-identity's 3-category scene, 10.0 on achromatopsia's
   2-category scene. A tuned threshold would be one number written once; this is an
   expression that yields whatever the codebook implies.
3. It reuses **the exact distance `ci_assign` already computes** (`_dist`, `:211`)
   — the same cross-frame opponent metric, now applied prototype-to-prototype. No
   new metric, no new frame (the frame/continuum invariant is preserved: the
   coordinates stay integer, the continuous stays in the cross-frame comparison).
4. The only literal introduced is **`2`**, in `2r ≤ D` — the definitional
   non-overlap factor, exactly the sense in which L1b's `Gte(count, 2)` is "the
   definition of more than one" and not a threshold.

**The honest weakness, stated in advance (§8): at k=1 the packing radius is
UNDEFINED** (there is no other prototype). The bound is then vacuous and `ci_assign`
still cannot refuse. This is correct vector-quantization semantics — a lone quantum
owns all of space — but it means **the defect is NOT fixed in the k=1 regime**. This
is why achromatopsia's FLOOR and SPLIT_CLEAN arms (both k=1) are predicted unchanged.

### Composition — held Terms only, NO new Rust

| needed | held Term | where |
|---|---|---|
| admission comparison | `Lte` | `runners/dsl/src/jsonio.rs:1094` |
| minimum over the other prototypes | `MinOver` | `jsonio.rs:1174` (used in committed `figure_ground.json`, `region_grouping.json`, `grid_navigation.json`, `ballistics.json`, `arc3_game.json`) |
| "the other prototypes" | `Filter` + `Not` + `Eq` | `jsonio.rs:1149`, `:1266`, `Eq` compares `Value::Node` by id (the `retire_duplicate_gap` precedent) |
| absence tolerance at k=1 | `Count` + `Lt` | `jsonio.rs:1148` — **`Count(...) < 1`, NEVER `PickUnique` on a params node** (process rule 3) |
| the winner | `Argmin` | already in `ci_assign` (`:217`) — reused verbatim, not re-derived |
| the distance | `Sqrt`/`Minus`/`Times`/`Plus` | already in `_dist` (`:211-214`) — reused verbatim |
| the flag | `Gt`/`Lt` on `ColourIdentityParams` | the same idiom `identity` and `achromatopsia` already use |

**`Times` TRAP (process rule 4):** every `Times` in this rung is the **`items` LIST**
form (`Times([Lit(2.0), d])`). The `a`/`b` form parses to an **EMPTY PRODUCT = 1**,
which would silently turn the bound into the constant `1.0` and refuse arm A(b).
**Positive-controlled** — see §12.3 controls below.

## Hypothesis (two-sided, §3.1)

**H1:** A refusal bound derived as the minted codebook's PACKING RADIUS refuses
observations that lie outside every quantum's non-overlapping ball — including L1b's
far probe (dist 269.52) and its 0.0000-margin equidistant probe — **while admitting
every observation the landed rungs already assign**, so no committed result changes.
**H0:** either (a) the bound fails to refuse the far probe (it is vacuous — no fix),
or (b) it refuses observations the landed rungs assign (it regresses colour identity
and/or achromatopsia). Either is a clean negative, reported and diagnosed (§7), NOT
rescued by re-deriving the bound after seeing the numbers (§5).

## The statistic, exactly (§3.2)

Rules added to `seeds/vision_colour_identity.json` (v1.2.0), gated on a **new
`bound` flag on `ColourIdentityParams`, default `0.0` = OFF (§9)**:

- `ci_assign` gains ONE `where` clause:
  `Or([ Lt(bound, 0.5), BOUND_OK ])` — vacuously true when the flag is OFF, so
  behaviour at default is unchanged.
- **`BOUND_OK`** = `Or([ Lt(Count(others), Lit(1)),
  Lte(Times([Lit(2.0), d_win]), MinOver(others, "o", dist(winner, o))) ])`
  where `others = Filter(NodesOf("ColourCategory"), "o", Not(Eq(V("o"), winner)))`.
  The first disjunct is the **absence-tolerant k=1 case** (process rule 3).
- **NEW rule `ci_refuse`** — fires on the complement (`Gt(bound,0.5)` AND
  `Not(BOUND_OK)`), writes `ci_refused = 1.0` and `ci_refused_dist`, and sets
  `assigned_epoch` so it fires once per epoch and `run_rules` terminates.
  Following L1b's load-bearing lesson it writes **only NEW attributes** and never
  touches `sign_rg`/`sign_by`/`sign_dist` — a refused region keeps the adapter's
  initial `sign_dist = −1.0`, which is exactly the `refused` readout L1b's own audit
  used (`sign_dist < 0`).

All arms are deterministic except E and F (n=100 each, seeds pre-registered below).

### Arm A — DEFECT_REPRODUCED (the premise; RISKED)
Flag **OFF**. Reproduce L1b exactly on the 3-cluster codebook
`{(−10,0),(0,12),(10,0)}`: far probe `cL=200,cM=5,cS=9` ⇒ obs `(195,−196)`.
- **PASS(A)** = far probe assigned with `sign_dist == 269.5199` and `ci_refused == 0`;
  equidistant probe `cL=10,cM=10,cS=20` ⇒ obs `(0,0)` assigned with `sign_dist == 10.0`
  and runner-up margin `== 0.0`.
- **CAN FAIL IF:** `ci_assign` already refused, or L1b's numbers do not reproduce.

### Arm B — BOUND_REFUSES (the reason to exist; RISKED)
Flag **ON**, same scene and probes.
- **PASS(B)** = far probe `ci_refused == 1` and `sign_dist == −1.0` (never assigned).
- **CAN FAIL IF:** the bound is vacuous. **Failure input is in range:** the probe sits
  at **269.52** against a bound of **7.8102** — 34× outside. A `Times` a/b-form defect
  (bound ≡ 1.0) still refuses here, which is why B alone is NOT the gate; C is.

### Arm C — NO_REGRESSION (THE CONJUNCTION, §1.1; RISKED)
Flag **ON**. Every observation the landed colour-identity rung assigns must STILL be
assigned, at the same category and the same distance:
- (a) the 36-cell E scene: `n_assigned == 36`, `n_refused == 0`, all `sign_dist == 0`;
- (b) **the off-prototype probe at `(6,0)`** — landed arm A(b) — still assigned to
  `(10,0)` at `sign_dist == 4.0`, `ci_refused == 0`;
- (c) a NEW instance of a seen colour still recognized at `sign_dist == 0` without
  re-minting (`n_cats` 1→1).
- **PASS(C)** = all three.
- **CAN FAIL IF:** the bound is tighter than **4.0**. **Failure input is in range and
  this is the arm that discriminates:** (b) sits at **dist 4.0** against a bound of
  **7.8102** — margin **3.81**, genuinely inside the risk region. The exact-extent
  bound (0), the lattice-step bound (1.0) and a refuse-everything build **all fail
  here**. This is the arm process rule 5 demands, and it is positive-controlled below.

### Arm D — AMBIGUITY (the 0.0000-margin case; RISKED)
Flag **ON**, equidistant probe obs `(0,0)`, both `(±10,0)` at distance exactly 10.0.
- **PASS(D)** = `ci_refused == 1`, AND the refusal is **independent of which side the
  `Argmin` tie falls** (both candidates are at 10.0 > 7.8102, so either winner
  refuses). The ambiguity is resolved by the SAME bound — **no special case, no tie
  rule**.
- **CAN FAIL IF:** the bound were ≥ 10.0, in which case the 0-margin tie is silently
  assigned exactly as L1b found. **In range:** 10.0 vs 7.8102.

### Arm E — BOUNDARY_EXACT (n=100, seeds **50000–50099**; RISKED)
100 iid uniform random opponent probes (`cL,cM,cS ∈ [0,60]`) decoded against the E
scene's 3-category codebook with the flag ON. For each, compare the SEED's
admit/refuse decision against the packing-radius predicate computed independently in
the runner.
- **PASS(E)** = **0 disagreements / 100**, AND the sample is non-degenerate: **both**
  outcomes occur (≥1 admitted and ≥1 refused), so neither a refuse-everything nor an
  admit-everything build can pass.
- **CAN FAIL IF:** any off-by-one, the `Times` a/b trap, a `MinOver` default swallow,
  or a wrong winner. This arm is what makes the bound **load-bearing** (§13.2): it
  shows the seed's decision IS the derived predicate, pointwise.

### Arm F — NOISE_FLOOR (n=100, seeds **50100–50199**; RISKED)
100 iid colour-noise fields (cones `[0,99]`, the committed `arm_N` construction) with
the flag ON.
- **PASS(F)** = **0/100** mint any `ColourCategory` AND 0 signs assigned — no false
  structure, and the bound introduces none.

### Arm X — OFFDAY (§9; ENTAILED)
Flag at default `0.0`.
- **PASS(X)** = committed `test_colour_identity_migrated.py` (6/6) and
  `test_achromatopsia_migrated.py` (5/5) reproduce EXACTLY; rung-7 vision bench
  **200 passed / 0 failed** with `data/`; the sd orbit law **{2:1,3:2,4:2,6:2,12:4}**
  unmoved; no `ci_refused` attribute written anywhere.

### Δ — DELTA_ON (§9 measurement; REPORTED, NOT GATED)
Re-run colour identity's 6 arms and achromatopsia's 5 arms with the bound flag **ON**
and report **every** number that changes. This is the measurement the parent asked
for; it is reported whatever it shows and does not gate the rung.

## n, fixed in advance (§3.3)
Arms A–D and X are deterministic (fixed synthetic stimuli, exact statistics). Arms E
and F are n=100 each, fixed in advance, seeds pre-registered. No sweeps.

## Confirmatory seeds never used before (§3.4)
**50000–50099** (arm E), **50100–50199** (arm F). Previously unburned (highest prior
burn 49999). 50200–50999 reserved, unconsumed.

## Decision rule (§3.5)
Report ALL arms. The fix holds iff **A AND B AND C AND D AND E AND F AND X** all
PASS — **the conjunction, not any single arm** (process rule 5: a refuse-everything
build scores a perfect floor on B, D and F, and is caught ONLY by C and E). If C
fails, the bound regresses a landed rung and the fix is REJECTED as derived — a clean
negative, reported and diagnosed, NOT re-derived to fit (§5). DELTA_ON is reported,
never gated.

## Exactly the listed tests. No sweeps (§3.6)
The eight items above plus the committed byte-identity re-runs. No threshold search.
A different bound needs a NEW prereg with a NEW derivation.

## My prediction, stated in advance (§3.7)
I predict **A–F and X all PASS**, and **DELTA_ON is EMPTY — not one landed number
changes.** Provisos:
1. **No landed observation lies outside its packing ball.** Every assignment in both
   landed rungs is at `dist 0` (exact recognition) or `dist 4` (arm A(b)), against
   bounds of 7.8102 (colour identity) and 10.0 (achromatopsia). If a landed
   assignment IS refused, C fails and the fix is rejected — reported, not patched.
2. **Achromatopsia's FLOOR and SPLIT_CLEAN are k=1** (one achromatic (0,0) category),
   so the packing radius is undefined and the absence-tolerant disjunct admits. They
   must be unchanged **for a reason I am stating in advance** — the k=1 hole, not
   because the bound happens to be loose.
3. **`ci_refuse` terminates.** It sets `assigned_epoch`, so its re-arm guard goes
   false; `run_rules` terminates on exact value equality (§2.1). If the fixpoint
   diverges I mis-wrote the guard — check and report.
4. **The refusal is tie-independent** (arm D): both tied candidates sit at 10.0 >
   7.8102, so the `Argmin`'s arbitrary choice cannot change the verdict. If it can, D
   is not measuring what I claim.

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run
- **ENTAILED (reported as consistency, NOT banked):** **X** (the flag ships at 0 and
  every new clause is a vacuously-true disjunct at that value, so inertness is
  entailed by construction).
- **RISKED (this is the result):** **A** (the premise could fail to reproduce), **B**,
  **C** (the discriminating arm — a bound below 4.0 makes it red), **D**, **E** (a
  pointwise agreement test that fails on any arithmetic defect), **F**.
- Each risked arm's failure input is stated above and **confirmed in range** — no arm
  passes while sitting outside the region where it could fail.

## §12.3 positive controls — to be RUN, not asserted
1. **The `Times` a/b trap** (process rule 4): rewrite `Times([Lit(2.0), d])` as the
   `a`/`b` form ⇒ empty product ⇒ bound ≡ 1.0. **Must turn arm C red** (the dist-4
   probe refused). Revert must restore the seed **byte-equal** to the committed one.
2. **The refuse-everything build** (process rule 5): force `BOUND_OK` false.
   **Must turn arms C and E red** while B, D and F stay green — demonstrating that
   the floor arms alone are not a gate and the conjunction is.
3. **The vacuous-bound build**: force `BOUND_OK` true (the pre-fix behaviour).
   **Must turn arms B, D and E red** while C stays green.

## Scope — what is NOT shown (§8)
- A REFUSAL BOUND for `ci_assign` only. It does **not** widen any invariance class:
  no colour refused before is assigned now; the bound can only turn an assignment
  into a refusal.
- **The k=1 hole is NOT fixed** (packing radius undefined with one quantum). Stated
  in the derivation, predicted in the provisos, and re-reported in the results.
- The bound is a **codebook-geometry** bound. It says nothing about whether the
  minted categories are the RIGHT ones — that is the mint's MDL gate, untouched.
- **NOT the perceptual-nearness frontier**: minting stays exact-value; this rung
  changes only assignment's admission. The continuous colour metric in MINTING
  remains the named, unreached frontier.
- **NOT a margin gate.** L1b named L1c (the margin instrument) and left it; this rung
  does not build it either. The packing radius is a DISTANCE bound, not a margin
  between rival candidates — arm D refuses the 0-margin probe because it is far from
  both, not because they are close to each other.
- The other rungs L1b flagged (`df_recognize` structurally; T1's near-vacuous bound)
  are **untouched** — this rung fixes `ci_assign`, nothing else.
- Whether to FLIP the default is explicitly **NOT decided here**: this rung measures
  the delta and leaves the flag OFF (parent's call).

## Provenance (§10) — recorded in the RESULTS on the run.
