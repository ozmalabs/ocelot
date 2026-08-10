# ARC 6 — CONSTRAINTS, ORDER-N PROJECTED VALUE, AND THE MAGNITUDE LADDER

**Date:** 2026-08-04
**Prereg:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment **A9** (`MG1`–`MG5`),
registered before this work.
**Base commit:** `d566f6dbe3` (detached worktree `/home/matt/arc6-magnitude`).
**Engine:** `8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`,
copied into this worktree and **verified resolving from inside it** —
`_native.__file__` is
`/home/matt/arc6-magnitude/…/runners/dsl/python/substrate_rs/_native.abi3.so`,
not the canonical tree's. Behaviourally probed before every measurement:
`add_node({"lst":[1,2,3],"tup":(1,2,3)})` reads back `[1,2,3]` and `(1,2,3)`
**distinctly**, asserted inside the gate's own boot (`_assert_engine_coherent`).
**Artifact:** `results/arc6_magnitude.json` (engine stamped).
**Gate:** `tests/test_arc_magnitude_migrated.py` — **43/43 green**.

**SCOPE: MG1, MG2, MG3, MG5. MG4 IS DESIGNED, NOT BUILT** (§6) — and the
design's load-bearing finding is that decomposition is **blocked on the same
missing rung the last one named**, the executor and its status lifecycle.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **MG1 — constraints are conditioned facts that LAPSE** | **PASS** | an `ArcConstraint` lapses and restores through `gr_condition_lapse`/`gr_condition_hold` **verbatim, zero new mechanism**; **ONE horizon answer reprices the pool — 6 pairs, 7 goals, changing relative order.** §2 |
| **MG2 — order-N value, attrition READ not authored** | **PASS** | order-N differs from order-1 **on the shipped graph and the top two INVERT**; every factor is a `Div` of two numbers read from a named artifact at a named path; the seed stores **no attrition number as a value**. Unmeasured projections expire. §3 |
| **MG3 — the ladder routes by RATIO** | **PASS** | the same goal runs `absorb → balance → push_back → balance → absorb` when **only the horizon changes**. The only number in `mg_rung` is `1.0`. §4 |
| **MG4 — designed, not built; liveness reported** | **PASS (as scoped)** | JOB 0 answered by running (§1); the design is §6; nothing splits anything. |
| **MG5 — no regression, no Python decisions** | **PASS** | `test_arc_goals_migrated` **37/37**, `test_arc6_valuelayer_migrated` **35/35**, `test_goal_residual_migrated` **31/31** — including `test_gr4_the_live_mbpp_pass_ids_are_unchanged`, the **48 pass ids / 95 accepted ids** as paired lists. Source audit passes. §5 |

**The one thing worth reading if you read nothing else:** the order-1 value term
was **already a projection**. It credited a goal with 42 tasks of paper
inventory as if they were converted. Putting the project's own measured
attrition on it reprices that goal from 42 to 13.64 and **loses it the top of
the ranking** — and the arithmetic that does so is the same arithmetic the
prereg's own HS1 bar ran (10 × 0.32 ≈ 3.2), which returned 0.

---

## 1. JOB 0 — are `question_driving.json`'s decompose / fold-up rules LIVE?

Measured by running, not by reading (`results/arc6_magnitude.json →
JOB0_are_decompose_and_foldup_live`). **The answer is a split, and the split is
the finding.**

| | `qd_decompose` | fold-up (`qd_compound_resolve` / `_wall`) |
|---|---|---|
| synthesis-path boot (`ensure_program_synthesis`) | **not resident** (0 `Resolver` nodes) | **not resident** |
| full 632-seed boot | **resident** | **resident** (5 `Resolver` nodes) |
| population on that boot | **0 `SubgoalSpec`**, 0 `Goal`, 0 `GapSpec` — `run_rules` mints none | same |
| reachable at all in this tree? | **NO — structurally** | **YES**, via a Python driver |

**`qd_decompose` is RESIDENT AND STRUCTURALLY DEAD, and that is stronger than
the `gap_prioritization` finding.** `gap_priority` was inert for want of a
Python driver that *could* have populated it. `qd_decompose`'s input type is
minted **nowhere in this tree**: `add_node("SubgoalSpec")` has zero occurrences
tree-wide, and `has_subgoal_spec` appears in exactly one file —
`seeds/question_driving.json`, the seed that declares it. The reason is written
in `domains/question_driver.py:548` in its own words: *"a comprehended
TargetSpec becomes a graph-resident Goal (+ **SubgoalSpec-FREE recursion** for
compound/compare…)"*. `_ingest_target` **recurses in Python** over
`target.subgoals` and mints the child `Goal`s directly. The rule was superseded
by the adapter it was supposed to replace.

**The fold-up half is different, and better.** It is resident *and reached* —
whenever `question_driver` ingests a compound target, `qd_compound_resolve`
composes the children's answers and `qd_compound_wall` propagates a walled
child. But the **decomposition that feeds it is Python**, so what exists is a
graph-native *fold-up* over a Python-native *split*.

### The A7 capability control — run before the word "dead" was written

A probe that reports "dead" through a channel that cannot report "alive" has
measured the channel. So the same probe was given the population these rules
need:

| | measured |
|---|---|
| 2 constructed `SubgoalSpec` children | `qd_decompose` **FIRED**, minting `['a','b']` |
| both children resolved | `qd_compound_resolve` **FIRED** → `status: resolved`, `answer: "Aa Ab"` |
| one child walled (fresh scene) | `qd_compound_wall` **FIRED** → `status: walled` |

All three fire; the fold-up fires in **both** directions. **The zero counts are
a fact about the population, not about the instrument.** Gated
(`test_mg5_JOB0_qd_decompose_is_RESIDENT_AND_DEAD_and_the_probe_can_tell`) so
the finding cannot rot.

**Consequence for MG4: it is a BUILD for the split and a HOOK for the fold-up.**
That is the answer the brief asked for, and §6 is written against it.

---

## 2. MG1 — CONSTRAINTS AS CONDITIONED FACTS

### 2.1 Zero new lapse machinery, and it is structural rather than promised

`gr_condition_lapse` / `gr_condition_hold` match on
`[["r", "holds_under", "c"]]` with **no type restriction on their left var**.
So an `ArcConstraint` carrying a `holds_under` edge to a `ResidualCondition`
lapses through them unchanged. **No lapse rule was added, copied or
parameterised**, and that is asserted structurally: no rule in
`seeds/arc_magnitude.json` writes `stale` on anything
(`test_mg1_the_lapse_rules_are_NOT_redefined_in_this_seed`).

Verified live **before the seed was written**, and again in the gate, both
directions:

| | `stale` |
|---|---|
| a conditioned horizon while its named condition holds | **0.0** |
| the same constraint once the condition is **falsified** | **1.0** — and every goal returns to rung `unknown_no_horizon` |
| once the condition **returns** | **0.0** — and the rungs come back |

The reverse direction is not decoration: a one-way lapse would itself be a claim
that cannot be revised, which is the defect `gr_condition_hold` exists to
prevent.

**An unconditioned answer expires.** A horizon reply naming no checkable reason
gets `fact_equals(arc_measure_epoch == <epoch at reply>)` — the same default
`ag_reply_mints_testimony_unconditioned` uses, on the same `ResidualFact`,
consumed by the same lapse branch — and is `stale` one epoch later, at which
point the pool **visibly** returns to `unknown_no_horizon` rather than silently
carrying a dead deadline. The refuting half is measured in the same shape: a
*conditioned* horizon survives the identical bump, so the first result is about
the default and not about the bump.

### 2.2 THE BAR: one horizon answer reprices the pool

One utterance — *horizon = 5 operator units*, unconditioned — against the
order-N collapse:

| rank | before (no horizon) | after |
|---|---|---|
| 1 | `…row_verdict_seed_only` **7.70** | `…row_verdict_seed_only` **7.70** |
| 2 | `…missing_structural_primitive` **−18.36** | `…budget` −25.0 |
| 3–7 | `…budget` / four claims −25.0 | four claims −25.0 |
| 8 | `…missing_dimension` −28.0 | `…missing_dimension` −28.0 |
| — | | **`…missing_structural_primitive` −32.0 (last)** |

**6 pairs changed relative order, across 7 goals**; the structural goal moved
from rank 2 to rank 8 and its rung became `push_back`. The bar asked for ≥2.

**And that asymmetry is the entire argument for asking constraints rather than
permissions.** A per-goal approval returns **one bit about one goal**. One
horizon answer repriced every goal that has a ladder, because the horizon
**truncates the order sum** — a tier whose cumulative cost exceeds the net
horizon is not buyable and contributes nothing.

**The control that makes this admissible.** "The pool was repriced" must not be
able to mean "a `Message` was added". So a reply of the *same shape* naming a
**scope** instead of a horizon is measured in the same scene: it produces **no**
reordering and leaves the rung at `unknown_no_horizon`
(`test_mg1_the_repricing_is_the_HORIZON_and_not_the_reply_arriving`).

### 2.3 Scope is a WEIGHT; competing requirements consume the HORIZON

**Scope.** An out-of-scope goal is charged `w_out_of_scope` **inside the value
term** and stays in the pool — measured: with scope pinned to `row_verdict`, the
structural goal's value drops by exactly 25.0 and it is still ranked. A9's
framing correction is the reason: *do not add a guard where a term is missing.*
Scope was a missing **input**, so it is a **term**. `w_out_of_scope = 25.0` is
**AUTHORED** and declared as such (§7.3).

**Competing requirements.** Modelling them as a second charge would have been a
second knob. They instead **consume the horizon** (`net = gross − Σ competing`),
so they reprice through the channel that already exists. Measured: at horizon
30 the structural goal is `absorb`; add a competing claim of 25 and the same
goal is `push_back`, with nothing else changed. A goal is not smaller because
someone else is busy — the budget is.

### 2.4 The ask fires under T2 ignorance, and is withheld when a horizon holds

The discriminating pair takes the **same** measurement-epoch bump in both
worlds, so the trigger cannot be confounded with the bump:

| world | questions at boot | after the same epoch bump |
|---|---|---|
| **ignorant** (no horizon held) | 1 | **2** — a new question |
| **held** (conditioned horizon) | 1 | **1** — none |
| held, then its condition **falsified** | 1 | **2** — the ask comes back |

The third row matters: `_live_constraints` reads `stale` rather than mere
existence, so **a lapsed answer is ignorance again**. And the instrument is
shown able to mint a second question *before* it is used to show one was
withheld (A7).

The emitted text carries the **measured** numbers — every one through
`ToJsonString`, because `StringConcat` silently drops numeric parts and would
have produced a question that looked fine and said nothing:

> *"I am ranking 6 arc goals and I hold NO horizon, so I am pricing every one of
> them in a vacuum. My largest candidate carries a MEASURED tier ladder costing
> **28.0** operator units end to end, with its smallest buyable increment at
> **8.0**. I am not asking you to approve a goal — that would return one bit
> about one goal. **WHAT IS THE HORIZON**, in those same units? One answer
> reprices all of them, because a horizon truncates how far down a ladder I can
> buy. Name a checkable condition with it, so the answer can lapse when its
> reason does; without one it expires at my next measurement epoch."*

---

## 3. MG2 — ORDER-N PROJECTED VALUE

### 3.1 The attrition factors are READ. The seed stores no attrition number.

A9: *"the per-order factors must be READ from results artifacts and traceable to
them. An authored projection is unbounded in the dangerous direction — worse
than an authored `cost_bits`, because it justifies rather than restrains."*

The strongest available form of "read, not authored" is not a number with a
citation beside it — it is **no number stored as a value**. An `ArcAttritionKey`
carries a name, an artifact and two dotted paths and nothing numeric
(`test_mg2_THE_SEED_CONTAINS_NO_ATTRITION_NUMBER` walks every attr and asserts
its numeric VALUE list is empty; the figures appear only inside explanatory
`_why` prose, which is the citation and not the input). The adapter opens the file and writes
`numerator_n` / `denominator_n`; **`mg_attrition_factor` computes the ratio in a
Term.**

| factor | artifact | numerator path | denominator path | value |
|---|---|---|---|---|
| `inventory_to_strict_reach` | `results/arc6_structural_ceiling.json` | `strict_reach.witness_and_in_budget_ids\|len` = 6 | `ceilings.honest_B0_zero_new_termnode.n` = 10 | **0.6** |
| `reach_to_conversion` | `results/arc6_structural_ceiling.json` | `s4_reach_vs_conversion_prior.s4_fully_correct_pass` = 8 | `s4_reach_vs_conversion_prior.s4_moved_off_enumerate_failed` = 25 | **0.32** |
| `seam_a_honest_vs_cherry_picked` | `results/arc6_a_ceiling.json` | `ceilings.honest_all_families.n` = 14 | `ceilings.cherry_picked_concept.n` = 27 | 0.5185 — **read, reported, NOT used** |

**These two are not a choice.** The artifact names them itself:
`inventory_ceiling_is_not_reach.consequence` — *"the honest expected CONVERSION
for a bundle is its inventory count discounted twice — once by size/reach, once
by the S4 pass-rate prior (8/25 = 32% of moved tasks were fully correct)."* The
factors used **are those two, at those paths**, and the gate re-derives each one
from the file and re-checks the division.

**Seam A's 5 / 8 / 14 / 27 / 60 is READ AND DELIBERATELY NOT USED as an order
ladder**, and declining to use it is recorded in the seed rather than left
silent. It is a **granularity** ladder — the same tasks renamed at finer grain —
not nested increments. Feeding it into an order sum would count the same tasks
four times, which is the inflation the prereg's own standing rule names: *in an
import seam audit the NAMING; in a structural seam audit the PRICE.*

**The survival law**, with its reason:

```
survival(1)   = 1.0                                    order 1 is MEASURED headroom
survival(k≥2) = f_size × f_pass^(k−1)                  orders ≥2 are PROJECTIONS
```

Order 1 is *not* discounted, and that is the design, not a concession. Order 1
is the same kind of number every other goal's `headroom_n` already is;
discounting it here and not there would silently rescale every goal instead of
repricing the one with a ladder. Orders ≥2 are reachable only if the order below
them **converted**, so each compounds one more `reach_to_conversion` on top of
the one-off size discount.

### 3.2 The tier ladder, and a key established by a MEASURED population join

`results/arc6_structural_ceiling.json → bundles` is a real ladder with per-tier
cost. Read, with the increments as differences of read numbers:

| order | bundle | cumulative unlocked | **increment** | cumulative cost (units) | new TermNodes | survival | expected conversions |
|---|---|---|---|---|---|---|---|
| 1 | B0_zero_new_termnode | 10 | **10** | 8 | 0 | 1.0 | 10.0 |
| 2 | B1_plus_stdlib_terms | 26 | **16** | 18 | 10 | 0.192 | 3.072 |
| 3 | B2_plus_order_boundary_dict | 32 | **6** | 24 | 14 | 0.06144 | 0.369 |
| 4 | B3_everything | 42 | **10** | 28 | 17 | 0.019661 | 0.197 |

**Which blocker class does this ladder describe?** Not an authored mapping — a
per-goal ladder assignment would be Seam D's 36/36 wearing a fourth name. The
adapter reads `arc6_a_ceiling.json::blocker_split.ids_over_live_unreached`
(three id lists, one per blocker name) and
`arc6_structural_ceiling.json::population.structural_42_ids`, and reports which
name's id list is **set-equal** to the ladder's own population. Exactly one is:
`missing_structural_primitive`. A zero-match or multi-match leaves the ladder
**unkeyed** rather than picking one. The gate re-derives the join from both
files.

### 3.3 THE HEADLINE — order-N differs from order-1, and the top two INVERT

**The A7 control is structural.** "Order-N differs from order-1" is only a
measurement if the two readings are the **same instrument**. `VALUE_N` is
**machine-lifted** out of `ag_select_margin`'s own value effect and modified by
exactly two mechanical edits — the single `Attr(_, "headroom_n")` becomes
`Attr(_, "orderN_headroom_n")`, and a scope charge is subtracted outside.
`test_mg2_VALUE_N_is_ag_selects_OWN_value_term_with_ONE_substitution`
re-derives the lift and asserts the serialised trees are **equal after that one
string substitution**. There is exactly one difference to detect, so the control
cannot fail to be capable of detecting it. `mg_select` ranks `ag_select`'s
**own pool**, lifted and gated the same way.

| reading | rank 1 | rank 2 | margin |
|---|---|---|---|
| **order-1** (`ag_select`, shipped) | `…missing_structural_primitive` **10.0** | `…row_verdict_seed_only` 7.70 | 2.30 |
| **order-N** (`mg_select`) | `…row_verdict_seed_only` **7.70** | `…missing_structural_primitive` **−18.36** | **26.06** |

**WHICH GOALS MOVE — exactly one, and it is the winner.**

| goal | headroom order-1 | headroom order-N | value order-1 | value order-N | basis |
|---|---|---|---|---|---|
| `…missing_structural_primitive` | **42** | **13.637** | 10.0 | **−18.36** | `measured_tier_ladder` |
| `…row_verdict_seed_only` | 11 | 11 | 7.70 | 7.70 | `no_ladder_order_1_IS_total_value` |
| `…budget`, `…missing_dimension`, ×4 claims | unchanged | unchanged | unchanged | unchanged | `no_ladder_order_1_IS_total_value` |

Seven of eight goals do not move, and **that is the mechanism working, not a
weak result.** A9 states the case verbatim: *"Re-measurement's order-1 value IS
its total value (completing it unlocks nothing)."* A goal with no measured
ladder has no orders above 1, so order-N **is** order-1 for it. Order-N reprices
the goals that project and leaves alone the goals that do not — which is exactly
what a uniform rescaling would not do.

**The reading, and it is the finding of this rung.** The order-1 term credited
the structural goal with **42 tasks of paper inventory** — every task the ladder
would *ever* cover, in full and at once, at zero discount. **That was already a
projection; it simply had no attrition on it**, which is precisely the unbounded
direction A9 registers. Under the measured attrition it is worth 13.64: B0's 10
measured directly, plus 16 / 6 / 10 discounted by the project's own numbers.

**And it retrodicts.** 42 → 13.64 → the 10 that cost zero Term variants → an
expected ≈1.9 conversions. That is the same arithmetic the prereg's HS1 bar ran
(10 × 0.32 ≈ 3.2 expected). **HS1 returned 0.**

### 3.4 A projection carries a condition, or it expires

Two lanes, mirrored guards, exactly one fires — the
`ag_reply_mints_testimony_conditioned`/`_unconditioned` shape applied to the
agent's **own** projections rather than to a human's answer.

| lane | condition | measured |
|---|---|---|
| **measured basis** (both factors resolved) | `fact_equals(arc6_structural_ceiling_present == "1")` | `stale 0.0`; falsify that fact → `stale 1.0`, and the goal falls back to `order_n_basis: projection_expired_fell_back_to_order_1`, `orderN_headroom_n: 42` |
| **no measured basis** (a path did not walk) | `fact_equals(arc_measure_epoch == <epoch at mint>)` | `stale 0.0` at mint; **`stale 1.0` after one epoch bump** |

A9's bar, mechanical: *a projection with no measured basis must default-expire
at the next epoch, exactly as an unconditioned human answer does.* The refuting
half is the measured lane above — a projection that expired **whatever** its
basis would mean the test was measuring the bump rather than the basis.

**And the dangerous-direction trap is closed.** With no attrition resolved, the
structural goal's order-N headroom is **10.0** — orders ≥2 contribute **zero**,
not their undiscounted increments. That is not automatic: `Times(x, null)`
returns `x` on this engine (§7.1), so written naively an **unmeasured**
projection would have been worth **more** than a measured one.

### 3.5 The calibration record — read, reported, and NOT multiplied in

| case | projected | returned |
|---|---|---|
| A-ceiling | a strict kernel-verified set (prereg quotes 5 ids; this artifact's own path reads 8 — a narrower hand-audit of the same set, recorded rather than reconciled) | **0 conversions** |
| Seam D | 36/36 on its own authored population | **LOO 0/36**, `loo_survivor_ids: []` |
| Tier 0 | **≈3.2**, from 10 B0 ids × the 32% prior — **this rung's own factor** | **0**, `converted_b0_ids: []`, HS1 **FAIL** |

**0 of 3 projections returned. It is reported and deliberately not used as a
factor.** As a point estimate that is 0.0, which would zero every projection and
make order-N identical to order-1 *by construction* — **single-source deciding,
the standing failure this project has nulled on five times, and the exact shape
A9's framing correction warns about.** Three trials do not bound a rate; the
Wilson upper bound on 0/3 is far above zero. The attrition that *is* applied
comes from measurements with denominators of 25 and 10, not 3.

Tier 0 is nevertheless the sharpest calibration point available, **because the
projection was made with this rung's own arithmetic** — and the order-N number
lands where that projection landed.

---

## 4. MG3 — THE MAGNITUDE LADDER

### 4.1 The rungs, and why there is no authored cutoff

```
r       = cost_total  / horizon_net            both in OPERATOR UNITS
r_first = cost_of_the_smallest_measured_increment / horizon_net

r ≤ 1                     ABSORB      the whole goal fits — execute, do not ask
r > 1 and r_first ≤ 1     BALANCE     part of it fits — compete in the collapse
r_first > 1               PUSH_BACK   not even the smallest measured increment
                                      fits → ask for scope AND decompose
no horizon held           UNKNOWN_NO_HORIZON
```

**The only number in `mg_rung` is `1.0`, and `1.0` is not a knob.** Cost and
horizon are both denominated in *operator units* — the unit
`arc6_structural_ceiling.json::bundles.n_units` is already in — so `1.0` is what
**"fits" MEANS**, not a threshold anyone chose. There is no `small_ratio` and no
`huge_ratio` on the policy node to tune, which is the whole difference between
this and `cost_bits`. Gated structurally: every numeric literal in `mg_rung`'s
effects is in `{0.0, 1.0, −1.0}`, and the policy node carries no key containing
`ratio`, `threshold` or `cutoff`.

`unknown_no_horizon` is a **fourth** outcome, checked **first**, for two
independent reasons: `Gt(x, null)` is `True` and `Div(x, null)` is `0.0` on this
engine, so a graph that had simply never been asked would otherwise have read as
one that fits perfectly; and *"we have not been told"* is a real state that must
not masquerade as *"it fits"* — it is precisely the state `mg_ask_constraints`
exists to leave.

### 4.2 THE BAR: the same goal changes rung when only the horizon changes

Six boots. The goal, its ladder, its costs and its attrition are identical in
all six; **the only thing that differs is one number in one utterance.**

| horizon (units) | cost_total | r | r_first | **rung** | decompose_required | order-N headroom |
|---|---|---|---|---|---|---|
| — (none held) | 28 | −1 | −1 | `unknown_no_horizon` | 0.0 | 13.637 |
| 40 | 28 | 0.70 | 0.20 | **`absorb`** | 0.0 | 13.637 |
| 20 | 28 | 1.40 | 0.40 | **`balance`** | 0.0 | 13.072 |
| 5 | 28 | 5.60 | 1.60 | **`push_back`** | **1.0** | **0** |
| 20 | 28 | 1.40 | 0.40 | **`balance`** | 0.0 | 13.072 |
| 40 | 28 | 0.70 | 0.20 | **`absorb`** | 0.0 | 13.637 |

`absorb → balance → push_back` **and back again**. Both directions, because a
rule that only ever ratchets one way is indistinguishable from one that fires
once.

Note the order-N headroom moving with the horizon too (13.637 → 13.072 → 0):
that is the horizon **truncating the order sum**, which is the same mechanism
that produced §2.2's repricing. The rung and the value are not two systems.

### 4.3 Push back is TWO actions, and only one of them is built

- **ask for scope** — **BUILT** (`mg_ask_constraints`), measured in §2.4.
- **decompose** — **DESIGNED, NOT BUILT.** `mg_rung` sets
  `decompose_required = 1.0` and stamps `decompose_ladder_key` with the measured
  ladder a split would use. **Nothing splits it**, and the gate asserts that:
  after a `push_back` there are still exactly 8 `ArcGoal` nodes and no goal
  carries a parent.

---

## 5. MG5 — NO REGRESSION, NO PYTHON DECISIONS, CONFINEMENT

| suite | result |
|---|---|
| `test_arc_goals_migrated` | **37/37** |
| `test_arc6_valuelayer_migrated` | **35/35** |
| `test_goal_residual_migrated` | **31/31**, including `test_gr4_the_live_mbpp_pass_ids_are_unchanged` over the full 257-task split — **48 pass ids / 95 accepted ids**, paired lists, `lost: []` `gained: []` |
| `test_arc_magnitude_migrated` (this rung) | **43/43** |

**The confinement is structural and asserted against `HEAD`.**
`seeds/arc_goals.json`, `seeds/goal_residuals.json`,
`seeds/program_synthesis.json`, `seeds/gap_prioritization.json`,
`seeds/stopping_policy.json` and `seeds/question_driving.json` are
**byte-identical to `HEAD`** (`git diff --exit-code`, gated). This rung adds a
**second seed** rather than editing the first — which is not merely tidy: it is
what makes the order-1/order-N comparison possible at all, since **both
collapses run on one graph at one time** and neither has to be re-derived.

Positively re-checked: with `arc_magnitude` loaded, `ag_select` still picks the
structural goal at value **10.0** with margin **2.3** — the exact numbers
`test_arc_goals_migrated` pins.

**`self_load_only: true` is kept**, and both halves are gated: a full
`_read_seeds` does **not** pick it up, and the on-demand route still works. The
seed *depends on* `arc_goals`, which is itself deliberately gated, so shipping
this one globbed would activate a chain whose base is gated. **Removing that key
is the tree-wide activation and needs the paired sweep A5 requires.**

**No Python decisions.** `domains/arc_magnitude_ingest.py` never imports
`substrate_rs`, never calls `.evaluate(`, never calls `run_rules`, and its only
substrate contact is `add_node` / `node` / `nodes` / `set_attr` /
`remove_node` / `add_edge_unchecked` / `load_seed_manifest`. Audited through
`ast` with string literals stripped — a source audit that greps the raw file
greps its own docstring, and this one names the banned calls in prose. The seed
regenerates **byte-identically** from `tools/build_arc_magnitude_seed.py
--check`.

**All 17 rules are asserted to INSTALL** (the loader drops a rule *wholesale*
when any effect references an unknown Term) **and every one is asserted to have
MOVED something**, including the four no other scene reaches
(`mg_projection_mint_unmeasured`, `mg_scope_charge`,
`mg_constraint_from_reply_unconditioned`, `mg_ask_constraints`). The fixpoint is
gated to terminate and the collapse to be deterministic across repeated runs.

---

## 6. MG4 — THE DESIGN. NOT BUILT.

Decomposition splits a huge goal on its **measured tier ladder**, not a
heuristic. The ladder is already graph data (`ArcTier{ladder_key, order,
increment_n, cum_cost_units, survival}`), keyed by a measured population join —
so **decomposition is the projection of an existing measured object into goals,
not an invention.** That is the whole reason it is tractable.

### 6.1 The rule (`mg_decompose`, unwritten)

```
match:   [["agenda", "has_arc_goal", "g"]]
where:   decompose_required == 1.0
         AND EXISTS a tier t with t.ladder_key == g.proposed_seam
         AND NOT EXISTS a child with parent_agid == g.agid AND tier_order == t.order
         AND t == Argmin(<un-materialised tiers of g>)      ← one mint per pass
effects: add_node child ArcGoal{
             agid: g.agid + ".tier" + order,
             parent_agid: g.agid,  tier_order: t.order,
             headroom_n: t.increment_n,        ← the MEASURED increment
             tier_survival: t.survival,        ← carried, see 6.2(4)
             magnitude_cost_units: t.cum_cost_units,
             sig_seam/sig_lever/sig_target: inherited from g,
             parent_ladder_key: g.proposed_seam,   ← NOT proposed_seam, see 6.2(1)
             novelty_bits: 0, status: "minted" }
         add_edge g -has_subgoal-> child
         add_edge agenda -has_arc_goal-> child
```

The `Argmin` serializer is not optional: this engine applies effects against
**pre-effect reads**, so four tiers in one pass would all mint before any dedup
saw the others. That is the `pcon_mint` idiom, and the same reason
`ag_mint_blocker` needs it.

### 6.2 Four things the design must get right, each with a measured reason

**(1) The child must NOT carry `proposed_seam`.** `_has_ladder` matches on
`Eq(tier.ladder_key, g.proposed_seam)`, so a child carrying it would match the
same ladder and re-decompose into four grandchildren — an unbounded mint. The
child carries `parent_ladder_key` instead: legible, not re-decomposable. This
engine has **no rule ordering**, so the guard chain *is* the ordering — the
AG-3 vocabulary-ladder lesson, applied.

**(2) THE BLOCKER, and it is the finding.** The parent must leave the pool, or
the parent and its four children are all ranked and the pool **double-counts the
same 42 tasks**. `ag_select`'s pool filters on
`status ∉ {retired, settled} ∧ headroom_n > 0`. So the parent must move to a
terminal status — and the previous rung recorded, as its uncertainty #8, that
**nothing in this tree ever writes `selected` / `pursued` / `settled`**, because
*"moving a goal to a terminal status with no executor would empty the pool with
nothing done."*

> **Decomposition is blocked on the status lifecycle, and the status lifecycle
> belongs with AG-5, the executor.** That is the same missing rung the arc-goals
> write-up named as its own largest uncertainty. It is not a coincidence: a
> planning layer with no hands cannot retire a goal, and a decomposition that
> cannot retire its parent inflates the pool it is trying to make tractable.

The interim workaround — a `"decomposed"` status added to the pool filter —
requires editing `seeds/arc_goals.json`, which this rung deliberately keeps
byte-identical and whose pinned margin of 2.3 the edit would move. **Declined,
and recorded rather than done quietly.**

**(3) Fold-up: twin it, do not reuse it.** JOB 0 found the fold-up already
exists and works in both directions — but on `Goal`, with a status vocabulary
(`waiting`/`resolved`/`walled`) the arc layer does not use, in a population
`question_driver.py` writes **from Python**. Minting arc children as `Goal`
nodes would put arc state back into a Python-written population — **exactly the
`CapabilityGap` mistake the arc-goals rung refused (§3 of its design).** So:
**twin it**, as `ag_select` twinned `gr_move_penalty`. The fold-up predicate is
pure `Count`-over-neighbours arithmetic and lifts to `ArcGoal` unchanged, so it
should be **machine-lifted** from `seeds/question_driving.json` at build time,
the way the `PENALTY` subtree is — then it goes out of date **loudly** if
`qd_compound_resolve` ever changes.

**(4) The split must not inflate — and this is the trap.** If each child got
order-1 credit for its raw increment, decomposition would be a way to launder
42 paper tasks into four goals of 10 / 16 / 6 / 10 that each look cheap. **That
is the A-ceiling's granularity inflation (5 → 27 → 60) reappearing at arc
grain**, and it is the single most likely way for this to go wrong.

> **Registered bar for whoever builds it:**
> `Sum(children.headroom_n × children.tier_survival) == parent.orderN_headroom_n`,
> gated, **both directions** — including a scene where a child's survival is
> dropped, which must fail the gate. Each child inherits its tier's `survival`,
> so the arithmetic is already on the graph and needs no new term.

### 6.3 What decomposition buys, once the executor exists

A child whose `cum_cost_units ≤ horizon_net` is `absorb`; the others stay
`push_back` and are themselves candidates for the ask. So decomposition plus the
horizon produce the actual answer to *"what can I do in two weeks"* — **the B0
tier, 8 operator units, 10 tasks, zero new TermNode variants** — which is the
thing this whole apparatus is for, and it is one rule and one status lifecycle
away.

### 6.4 What must NOT be used as a decomposition ladder

**Seam A's 5 / 8 / 14 / 27 / 60.** It is a *granularity* ladder — the same tasks
renamed at finer grain — not nested increments. Splitting on it would produce
five goals covering the same tasks five times. Read into the graph and marked
`granularity_calibration_NOT_USED_AS_AN_ORDER` so that declining to use it is
**visible rather than silent**.

---

## 7. EVERYTHING THAT BROKE

Recorded because the process is the result.

1. **`Times(x, null) == x` — null is the MULTIPLICATIVE IDENTITY on this
   engine.** Written naively, `Times(increment, survival)` with an *unresolved*
   attrition factor returns the **undiscounted increment** — so an **unmeasured**
   projection would have been worth **more** than a measured one. That is
   precisely A9's *"an authored projection is unbounded in the dangerous
   direction"*, arrived at by accident rather than by intent. Caught by probing
   the engine before writing the seed, closed by routing every arithmetic read
   of a possibly-absent attr through an explicit coalesce (`NUM()`), and pinned
   in both directions
   (`test_hazard_NULL_IS_THE_MULTIPLICATIVE_IDENTITY`,
   `test_mg2_an_unmeasured_projection_is_worth_NOTHING_not_its_full_increment`).
2. **`Gt(8.0, null)` is `True` — any number sorts ABOVE a missing attr.** Read
   literally, `Gt(cum_cost, horizon)` with **no horizon held** truncates every
   tier, so a graph that had simply never been asked would have read as one on an
   impossible deadline — silently, and in the direction that makes everything
   look `push_back`. `NO_HORIZON()` is therefore checked **first** in both
   `mg_tier_in_horizon` and `mg_rung`, and `unknown_no_horizon` exists as a
   fourth rung for the same reason. This is the sibling of the `Lt(null, 0.0)`
   defect the last rung lost a deferred claim to; both are now pinned here.
3. **The ask-discrimination control was confounded on first measurement.** It
   compared "1 question when ignorant" against "1 question when a horizon is
   held" — the same number, because the boot mints one either way and no *new*
   question was the thing to look at. As written it could not have detected the
   difference it was used to rule out, which is A7 exactly. Rebuilt as a
   discriminating pair taking the **same** epoch bump, plus a third arm where the
   held horizon lapses and the ask correctly returns (1→2, 1→1, 1→2).
4. **`out_of_scope` was left `null` on a never-charged goal**, so *"in scope"*
   and *"never looked at"* were the same absent attr. Harmless today because
   `NUM()` coalesces it — but that is exactly the conflation that cost the last
   rung a deferred claim. `mg_scope_clear` now guards on `Not(Eq(_, 0.0))` rather
   than `Eq(_, 1.0)` and stamps the explicit `0.0`.
5. **Two `add_edge` effects referenced an unbound variable** (`agenda2`, not in
   the reply rules' match). This engine treats that as a **silent no-op**, so the
   rules would have installed, fired, and quietly written no edge. Found by
   reading the emitted seed against the match patterns; removed, and the
   constraint is found by `NodesOfType` instead. **Every rule is now gated to
   have MOVED something.**
6. **`results/arc6_verdict_gr4_gate.json` was rewritten by running the gr4
   gate** (it is the gate's own output) — the same thing the last rung recorded.
   `pass_ids` (48) and `accepted_ids` (95) verified **byte-identical**; only
   `measured_at` / `elapsed_seconds` / `determinism` / the worktree path in
   `engine_provenance` moved. **Restored with `git checkout --`** rather than
   carried as this rung's change.
7. **The `results/run*_checkpoints` symlinks were REMOVED before handing over.**
   They are real directories in this worktree, and the symlinks show as
   **untracked files** (`.gitignore`'s pattern is directory-scoped) — a live risk
   if a commit is made with `git add -A`. `git status --porcelain` is now exactly
   the six deliverables.
8. **The calibration record's first version quoted a path that resolved to 8
   while labelled `a_ceiling_strict_5`.** The prereg's "5 ids strict" is a
   narrower hand-audit than this artifact's own
   `STRICT_kernel_verified_AND_nothing_else_blocks.n`. Relabelled and the
   discrepancy recorded rather than reconciled — the calibration turns on the
   RETURNED figure (0), which is the same either way.

---

## 8. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The repricing reach is ONE GOAL today.** Exactly one measured tier ladder
   exists in this tree, so exactly one goal has orders above 1. The mechanism is
   general and its key is a measured population join, but *"order-N reprices the
   pool"* is currently demonstrated by one goal moving past seven others. A
   second artifact carrying a `bundles`-shaped ladder would be the honest test of
   the join's dedup, exactly as a second `reach_class_counts` payload would be
   for `ag_mint_blocker`. **The mechanism is measured; its reach is one node.**
2. **The survival law's SHAPE is authored even though its factors are not.**
   That orders ≥2 compound `reach_to_conversion` once per order, and that order 1
   is undiscounted, are **structural choices with arguments** (§3.1) — not
   measurements. The artifact justifies *"discounted twice"*; it does not
   justify *"once more per order"*. A different shape with the same factors would
   give a different number. **This is the least-defended line in the rung**, and
   it is stated rather than buried because it is the place where an authored
   projection could still get in.
3. **`w_out_of_scope = 25.0` is an invented number**, inheriting
   `w_unsignatured`'s problem exactly. It has the gated two-position property (it
   can flip the outcome) and no principled value.
4. **The horizon's UNIT is `operator units` because that is what the ladder is
   denominated in** — and no human has ever been asked to think in them. The
   ratio is honest arithmetic; whether *"the horizon is 20 operator units"* is a
   question a person can answer is untested. A wall-clock horizon would need a
   measured units-per-week, which does not exist in this tree.
5. **`cost_bits` is still authored and still gameable** for the goals with no
   ladder — their magnitude ratio is `cost_bits / horizon`, so they are `absorb`
   at essentially any horizon. The measured-cost path exists only where a ladder
   does. The design's hole is untouched.
6. **MG4 is blocked on the executor** (§6.2), so *"huge ⇒ push back = ask AND
   decompose"* is currently **half-built by construction**, and the built half is
   the ask.
7. **The seed is `self_load_only`, so nothing in the tree loads it yet.** Every
   result here is measured on a boot that asks for it explicitly. Its tree-wide
   behaviour is **unmeasured**; activation is one key and a paired sweep.
8. **`arc_measure_epoch` is still a counter with no producer.** Every expiry
   result in §2.1 and §3.4 turns on a bump that
   `domains/arc_goal_ingest.bump_measure_epoch` performs *when a caller asks*.
   Inherited from the last rung and not fixed here — *"an unconditioned
   projection expires at the next measurement epoch"* remains true of a counter
   nobody increments automatically.

---

## 9. WHAT MADE ME WANT TO BUILD MG4 — reported, not taken

Three pulls, each a place where the mechanism is complete right up to the point
where something has to be **split**:

- **The ladder is already in the graph, already keyed, already carrying its own
  survival factors.** `mg_decompose` is roughly forty lines of the same builder
  idioms, and the tier nodes it would read are the ones `mg_goal_order_n`
  already sums. It is the shortest rule in the design document.
- **`decompose_required` is a flag nothing consumes.** The rung computes it, the
  gate asserts it, and then it sits there — which is the same shape as
  `arc_measure_epoch` being a counter with no producer, one level up.
- **§6.3 is the answer to the question the whole rung is about.** *"What can I do
  in two weeks"* → the B0 tier, 8 units, 10 tasks, zero new TermNodes. The
  apparatus computes every number in that sentence and cannot yet emit it as a
  goal.

**I did not build any of it**, and the reason is not only that it was out of
scope: §6.2(2) found that a correct decomposition **cannot** be built without
the status lifecycle, and the status lifecycle belongs with the executor rung
the last write-up named as *its* largest uncertainty. Building the split without
it would have double-counted 42 tasks in the pool — an inflation that would have
looked like the mechanism working.

---

## 10. FILES

| file | what |
|---|---|
| `seeds/arc_magnitude.json` | the seed — 7 nodes across 3 types, 6 edges, 10 productions, **17 rules**. `self_load_only`. Emitted, not hand-written. **Stores no attrition number as a value** |
| `tools/build_arc_magnitude_seed.py` | the emitter; lifts `ag_select`'s POOL and VALUE at build time and swaps exactly one `Attr` key |
| `domains/arc_magnitude_ingest.py` | the world adapter — self-load, artifact-path resolution, the measured ladder + its population join, a constraint reply. Mechanical I/O only |
| `tests/test_arc_magnitude_migrated.py` | the gate — **43/43** |
| `scripts/arc6_magnitude_measure.py` | the measurement runner |
| `results/arc6_magnitude.json` | the artifact, engine-stamped |
