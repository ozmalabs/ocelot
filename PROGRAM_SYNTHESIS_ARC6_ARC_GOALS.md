# ARC 6 — ARC-GRAIN GOAL MINTING: RESULTS (phase 2, AG-1 … AG-4)

**Date:** 2026-08-04
**Design (implemented, not redesigned):** `PROGRAM_SYNTHESIS_ARC6_ARC_GOALS_DESIGN.md`
**Base commit:** `b29ac875ec` (detached worktree `/home/matt/arc6-arc-goals`)
**Engine:** `8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`,
copied into this worktree and **verified resolving from inside it** —
`_native.__file__` is
`/home/matt/arc6-arc-goals/…/runners/dsl/python/substrate_rs/_native.abi3.so`,
not the canonical tree's.  Behaviourally probed before every measurement:
`add_node({"lst":[1,2,3],"tup":(1,2,3)})` reads back `[1,2,3]` and `(1,2,3)`
**distinctly**.
**Artifact:** `results/arc6_arc_goals.json` (engine stamped).
**Gate:** `tests/test_arc_goals_migrated.py` — **37/37 green**.

**SCOPE: AG-1, AG-2, AG-3, AG-4.  AG-5 IS NOT BUILT.**  The executor —
winner → run a measurement → produce an artifact → re-ingest → residual →
epoch bump — is the real rung and it is not here.  **Without it this is a
planning layer with no hands**, and that is stated rather than implied.  §10
records what made me want to build it anyway, as an observation, not as a
change.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AG1 — mint fires, on a testable prediction** | **PASS** | the re-measurement goal fires **on a clean boot**, unprompted, because `row_verdict_seed_only` is stale as shipped on this engine.  Live, §2 |
| **AG2 — dimensionality is right** | **PASS** | `row_verdict` does **not** rank equal to `ir_retarget`; ordering follows absolute headroom, both directions.  And on the shipped graph the two readings **invert at the top**.  §4 |
| **AG3 — vocabulary extends, once** | **PASS** | three tokens minted from measured artifact paths, one per pass, recognised on re-decode, second pass mints nothing, terminates.  §5 |
| **AG4 — the ask discriminates** | **PASS** | fires under ignorance, does **not** fire under refutation at the **same margin**; an unconditioned reply is stale at the next epoch and a conditioned one is not.  §6 |
| **AG5 — no regression** | **PASS** | `test_goal_residual_migrated` **31/31** + `test_arc6_valuelayer_migrated` **35/35** = **66 passed**, including `test_gr4_the_live_mbpp_pass_ids_are_unchanged` (the **48** pass ids / 95 accepted ids, as paired lists, `lost: []` `gained: []`).  Two wider sweeps (420 and 820 collected) add **no** red attributable to this rung — **controlled, not characterised**.  §7 |
| **AG6 — no Python decisions** | **PASS** | the source audit passes; minting, matching, ranking, lapsing and asking are all Rules/Terms.  §7 |

**The annihilation trap does not bite** — measured in both directions (§3).
**Design uncertainty #4 is CLOSED, and the design's assumption was WRONG** (§1).

---

## 1. JOB 0 — `gap_prioritization` / `stopping_policy` are **NOT** live on the synthesis path

The design assumed they are, *because they are in the `seeds/*.json` glob*.
**Being in the glob is not being live.**  Measured by running, not by reading
(`results/arc6_arc_goals.json → JOB0_are_the_policies_live`):

| condition | `gap_priority` | `should_continue` | `CapabilityGap` nodes |
|---|---|---|---|
| **the synthesis-path boot** (`domains.prog_synthesis.ensure_program_synthesis` — the boot `scripts/mbpp_endgame_battery.py` and every MBPP arm use) | **absent** | **absent** | 0 |
| the full `load_all_seeds` boot (632 seeds) | present | present | **0** |

**It fails twice over, and the second failure is the sharper one.**  The
synthesis boot installs **zero `Program` nodes at all**, so neither policy is
resident on the path this rung sits on.  On the full boot both Programs *are*
resident — and there are still **zero `CapabilityGap` nodes**, so
`gap_priority`'s `Argmax` has an **empty pool** and `should_continue` returns
its `default: -1.0`, i.e. STOP.  **Resident is not live either**: that
population is written entirely by `domains/gap_prioritization.py`, so both
Programs are inert unless a Python driver mints the gaps first.

This is the same shape §7 of the goal-residual doc warned about, and it
**confirms two of the design's decisions rather than undermining them**:

- §3's refusal to mint arc goals as `CapabilityGap`s — that population *is*
  Python-resident, and reusing it would have put the arc loop's state back
  into Python;
- §6.3's decision that `ag_select` is a **Rule** inside `run_rules`, not a
  `Program` evaluated from Python.  Adopting `gap_priority`'s invocation style
  would have imported its Python driver along with its shape, and the measured
  emptiness above is what that driver's absence looks like.

Nothing was built on the unverified premise.

---

## 2. AG-1 — THE MINT

### 2.1 The headline: it fires on a clean boot, on a testable prediction

`value_layer_list_eq_tuple` measures **`"0"`** on engine `8311d4356082`
(list and tuple are distinguished), which falsifies
`arc6.verdict.row_verdict_seed_only`'s own condition (`expected_str: "1"`).
`gr_condition_lapse` stales the residual and `ag_mint_remeasure` turns the
stale ceiling into an **open goal**:

```
arc.remeasure.arc6.verdict.row_verdict_seed_only
  kind          re_measure          source_kind  residual_stale
  sig_*         row_verdict / verdict / mbpp_test_257   (its SOURCE's signature)
  headroom_n    11.0  of  denominator_n 15.0            (MEASURED, in tasks)
  evidence      results/arc6_verdict_pricing.json
```

Its content — *"the row-verdict ceiling was measured under a value layer that
no longer exists; re-measure it"* — is a true statement about this tree that
previously lived **only in a markdown correction**.  Nothing is injected: the
boot measures the fact, the existing lapse rule stales the residual, the new
rule mints the goal.

### 2.2 The mint source is the MEASURED BLOCKER SPLIT, not `reach_class`

`reach_class` alone is measured nearly inert (all six residuals
`operator_blocked`; `missing_dimension_ids: []`), so the design's own
correction is what shipped.  `ag_mint_blocker` reads seam A's
`reach_class_counts` payload **graph-natively** —
`DictGet(FromJsonString(Attr(r,"reach_class_counts")), Attr(bk,"name"))`, no
Python parse — against authored `ArcBlockerKey` names, and the **count is the
headroom**:

| goal | headroom (tasks) | proposed seam |
|---|---|---|
| `arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive` | **42** | `missing_structural_primitive` |
| `arc.supply.arc6.seam_a.import_oracle.budget` | 7 | `budget` |
| `arc.supply.arc6.seam_a.import_oracle.missing_dimension` | 4 | `missing_dimension` |

*"Supply the structural primitive that blocks 42 tasks"* is a **different goal
with a different signature** from *"rebuild seam A"* — which is why there is no
annihilation here.  And none of the three blocker names is a `sig_seam` token,
so this source **forces the vocabulary question** (§5) on real measured data
rather than on a fixture.

Plus four `not_ingested` source-claim goals (§4.3's designed cheap-goal probe)
and, in scene, the `SelfConcern` channel — minted **unsignatured**, because
free text is never parsed into a signature.

**Eight goals on a clean boot.  A second `run_rules` mints nothing and moves
nothing.**

---

## 3. THE ANNIHILATION CHECK — measured, both directions

The trap: a goal minted from residual *R* that carries *R*'s own signature
would be charged *R*'s full weight the instant it entered the pool — mint and
penalty cancel, and the mechanism looks inert while actually being
self-defeating.  The re-measure goal **does** carry its source's signature.

| probe | result |
|---|---|
| penalty on the re-measure goal **while its source is stale** | **0.0** |
| penalty on the **same** goal once the source un-stales | **51.333333** |
| status once the condition genuinely returns | **`retired`**, `retired_because: source_residual_no_longer_stale` |

**It does not bite**, and for the reason the design predicted: the lifted
matcher's `Exists` requires `Not(Eq(stale, 1.0))` — **a stale residual charges
nothing**.  That is a property of the *existing* matcher, not a fix.

The refuting direction is measured in the same run, because *a bug in the
refuting direction is indistinguishable from an honest null*: un-stale the
source and the same goal is charged 51.33, so the 0.0 is about staleness and
not about a matcher that never matches.

**The explicit retire rule the design identified is implemented and fires**
(`ag_remeasure_retire`).  It is needed: `gr_condition_hold` is deliberately not
latched, so a lapsed residual can come back, and relying on the weight alone
would leave a dead goal sitting in the pool forever.  It is **not a veto** —
it removes a request whose *reason* has gone, not a goal on the strength of
evidence.

---

## 4. AG-2 — THE COLLAPSE, AND THE DIMENSIONALITY

`ag_select` is `ps_move_select`'s **rule form** at `gap_priority`'s **grain**,
stated as a new selector.  What is genuinely reused is the `PENALTY` sub-term,
and *"copied character for character"* is a claim, so it is **machine-lifted
and gated**: `tools/build_arc_goals_seed.py` extracts `gr_move_penalty`'s own
`residual_penalty` subtree out of `seeds/goal_residuals.json` at build time and
alpha-renames one variable;
`test_ag6_the_PENALTY_subtree_really_is_gr_move_penaltys_own` re-derives the
lift and diffs.  If `gr_move_penalty` ever changes, this seed goes out of date
**loudly** instead of silently diverging from the rule it claims to copy.

**The design's own load-bearing distinction is pinned**
(`test_ag6_gr_move_penalty_MATCHES_ON_AN_EDGE_…`): `gr_move_penalty` matches on
the `has_move_candidate` **edge**, so it can never see an `ArcGoal` however
well its attrs line up.  The goal-residual doc's "grain-agnostic" claim is true
of the **predicate** and not of the **rule** — so this rung ships its own twin.

### 4.1 The value term is ABSOLUTE HEADROOM IN TASKS

```
value(g) = w_headroom × headroom_n(g) × reach_class_factor(g)
         − w_residual × PENALTY(g)          # gr_move_penalty's own subtree
         − w_mdl      × novelty_bits(g)
         − w_cost     × cost_bits(g)
         − w_unsig    × [g has no sig_seam]
```

`w_headroom 1.0 / w_residual 1.0 / w_mdl 4.0 / w_cost 1.0 / w_unsignatured
25.0` are **AUTHORED** policy on an `ArcGoalPolicy` node — graph data, tunable
without touching a rule (the `RESIDUAL_SCALE = 100` precedent).  Declared
authored, not dressed as findings.

### 4.2 THE INVERSION, measured on the shipped graph

The registered bar was *"`row_verdict` must not rank equal to `ir_retarget`"*.
It is met — and the shipped graph gives something stronger than the synthetic
scene.  **The two readings of the same eight goals invert at the top:**

| reading | rank 1 |
|---|---|
| **absolute headroom, in tasks** | `…missing_structural_primitive` (42 tasks) |
| the **dimensionless ratio** | `arc6.claim.seam_b_signature_39_of_257` (1 task of 1, ratio 1.0) |

The ratio is a **completeness score**, and a value term denominated in
completeness converges on the *smallest possible target*: four 1-task claims
rank ahead of a blocker covering 42.  That is the design's §6.2 defect,
measured rather than argued.

**The control is shown capable (A7).**  The synthetic pair
(`test_ag2_HEADLINE_dimensionality_…`) builds two goals with an *identical*
ratio by construction — 11/15 and 188.4/257 — so the dimensionless reading
returns "identical".  That is only informative because the **same instrument,
reading the same two nodes**, separates them by 177 tasks and decides on it.
A control returning "identical" through a channel that cannot represent the
distinction has measured the channel.  **Both directions**: give the
15-denominator goal more headroom *in tasks* and it wins.

### 4.3 Weight, not veto — made structural, and measured

`test_ag2_four_scenes_lifted_from_GR1` lifts GR1's structure verbatim:

| scene | measured |
|---|---|
| control, no residual held | the higher-headroom goal wins, penalty `0.0` |
| residual held on its signature | the collapse **flips** |
| raise its headroom | it wins **again, while still charged 63.396226** |
| look-alike differing in exactly **one** dimension, **same scene** | charged **exactly 0.0** |

The look-alike is asserted alongside a *non-zero* charge, so a matcher stuck
at zero cannot pass the negative half.

Structurally (`test_ag2_the_residual_is_a_WEIGHT_…`): across the four selector
rules, `GoalResidual` appears in **no** `where`, in **no** ranking `Argmax`
source, and in **every** ranking `Argmax` value.  The count of ranking terms is
**pinned at 3**, not bounded — a structural gate that finds nothing to check
passes vacuously.

`ag_ask` is deliberately out of that gate's scope and says so: its guard reads
residuals *because* the ignorance/refutation distinction is its job, and it
excludes no goal from the collapse.

### 4.4 The cheap-goal probe: the collapse does **not** converge on cheap

The four `not_ingested` claims are the cheapest goals available, so if the
collapse converged on them the value term would be wrong.  Measured: they rank
**last** (value −25.0 each), and the winner's `source_kind` is
`residual_blocker`.  Absolute headroom denominates value in the thing that
matters, and the unsignatured cost prices their illegibility on top.

`w_unsignatured` is the design's own least-confident line (§12.3) and it gets a
**two-position test**: at 25 the unsignatured goal still wins on merit
(30 − 25 = 5 beats a charged 20 − 90); at 200 it loses; at 0 it wins again.  A
policy that cannot change the outcome is not a policy.

### 4.5 The tie-break — MEASURED, and stated as measured

The design asked for an explicitly pinned tie-break (agid-lexical or
`minted_epoch`) rather than an inherited one.  **A lexical tie-break is not
expressible with the shipped Term set** — there is no string-ordering
primitive, and `sorted`-on-strings is a known-unfixed defect in this tree.  So
`ArcGoalPolicy.tie_break` records the **measured** behaviour,
`insertion_order_stable` (this engine's `Argmax` returns the first-inserted
node under a tie), and the gate pins the property the failure mode actually
needs: the same graph state yields the same winner, and re-running does not
alternate.  **This is a residual, not a solved requirement** (§9).

---

## 5. AG-3 — THE VOCABULARY EXTENDS, ONCE, AND TERMINATES

On the shipped graph, three unrecognised `sig_seam` tokens — `budget`,
`missing_dimension`, `missing_structural_primitive` — **extend** the
vocabulary rather than being rejected.  `arc_vocab_epoch` reaches **3.0**: one
mint per pass (the `pcon_mint` `Argmin` serializer, gated at the pass level
with `apply_rule_batch` because `run_rules` is a fixpoint and would drain both
regardless), each bumping the epoch, `ag_revocab` re-arming, terminating when
every proposal is explained.  **A second pass mints nothing.**

**Provenance is the real bound.**  Every minted token carries the
`evidence_artifact` and `evidence_path` it was quoted from, so *the vocabulary
grows only as fast as measurement grows*.  Without a resolving path the mint is
**refused** and the goal reaches the terminal `unsourced` status with
`vocab_refused_because` — legibly, so *"the agent wanted a word it could not
source"* is a readable fact, not a silent drop.  Both directions in one scene:
the sourced twin mints.

**The closure audit is re-pointed to the LIVE graph** (design §5.3), which is
the strengthening direction: an audit that reads the manifest is un-auditing
minted tokens *by construction*.  The anti-Seam-D shape runs over the minted
set against the MBPP prompts.  *(One correction en route: my first version ran
it against the **evidence artifact** and failed — of course it did.  A token
being present in its own evidence is what provenance **means**; the failure
mode is a token lifted from a task **prompt**, which is how Seam D's 36/36
became LOO 0/36.)*

**Rung 2 (aliases) ships EMPTY and is exercised explicitly**, since a rule that
never fires proves nothing: with an authored `SeamAlias{token, alias_of}` the
goal adopts `alias_of` at 1 novelty bit; without it the identical goal falls
through to the mint at 8.  The difference between the two scenes is **one node
a human wrote down**, never a string comparison.  No arc-goal rule may use a
string-similarity Term, asserted structurally.

**Rung 3 — new *dimensions* — stays deferred**, with its Term-free marker twin
(`ag_dim_check_mark`) shipped for the measured reason the sd loop recorded: the
seed loader drops a rule **wholesale** when any effect references an unknown
Term, so an unlanded rung-3 rule would never install, `dim_checked` would never
be set, and the mint would deadlock for **every** goal.  **The closed-vocabulary
ceiling is lowered from dimensions to tokens, not removed.**

---

## 6. AG-4 — THE ASK DISCRIMINATES

The ask is a candidate in the same collapse, not a gate.  Trigger: **T1**
margin < `ArcAskPolicy.margin_threshold` (`cascade_pick`'s
`Lt(margin, threshold)` shape) **AND T2** `Not(Exists(matching non-stale
residual))` for **both** tied candidates — the same `Exists` term
`gr_move_penalty` already computes, negated.

### 6.1 The discriminating pair — same margin, two worlds

Adding a residual would normally *move* the margin, which would confound the
trigger with the ranking.  So the charged goal's headroom is raised by exactly
the charge (`w_headroom = 1`, `reach_class_factor = 1`), and the gate asserts
the two scenes agree on winner and margin before asserting they disagree on
asking:

| | winner | margin | penalty on the winner | asked? |
|---|---|---|---|---|
| **ignorance** | A | 2.0 | **0.0** | **1 question** |
| **refutation** | A | 2.0 | **63.396226** | **none** |

Tied under refutation, the evidence is already held and a human answer would
be **weaker** than the ceiling already on the node.  Tied under ignorance,
nothing is held either way, so a reply is not redundant with anything.

**On the shipped graph the ask fires, and it fires under ignorance** — the
winner's seam was minted this pass (no residual can cover it) and the
runner-up's source residual is stale (a stale residual charges nothing *and
holds nothing*).  The emitted text:

> *"I hold two arc goals I cannot separate. (A) …missing_structural_primitive
> — headroom 42 of 53 tasks. (B) …row_verdict_seed_only — headroom 11 of 15
> tasks. Their values differ by only 2.3. **I hold NO non-stale measurement
> covering either**, so I am not re-litigating a ceiling — I do not know.
> **What would have to change** for one of these to be worth trying? **Name a
> checkable condition**, so your answer can lapse when its reason does."*

A yes/no question would have reproduced the gate and its zero bits.

### 6.2 The reply is a residual, with a condition — or it expires

The reply mints a `GoalResidual` (**the same node type as the six measured
ceilings**) with `evidence_kind: 'utterance'` and a `holds_under` edge, so
`gr_condition_lapse` / `gr_condition_hold` apply **verbatim** — zero new lapse
machinery.  Two honest differences: `reach_class_factor` is
`TestimonyPolicy.factor` = 0.5 (weight 50.0, declared authored, because
testimony is not measurement); and the condition:

| reply | condition | at the next `arc_measure_epoch` bump |
|---|---|---|
| names a checkable reason | that reason (`fact_equals(some_named_reason)`) | **`stale = 0.0`** — survives, and lapses only when the named reason is falsified |
| names none | `fact_equals(arc_measure_epoch == "0")` | **`stale = 1.0`** — expires |

Both directions in one gate, because a conditioned residual that *also* expired
would mean (a) was measuring the bump rather than the default.

**Rate bound**: one open `ArcQuestion` per region per measurement epoch —
re-entry gated on **new measurement, never on graph churn**.  Three further
`run_rules` passes re-ask nothing; a `bump_measure_epoch` produces exactly one
new question and retires the old one as `unanswered_lapsed` (an unanswered
question is itself data: it says the loop ran without input).

### 6.3 The ask never blocks a mint

Measured as a **non-interference** property, not asserted: the mint outcome is
identical with the ask enabled (`margin_threshold 100`, one question) and with
it structurally impossible (`margin_threshold 0`, no question) — same minted
token either way.  The ask cannot be on the mint's causal path.

---

## 7. AG-5 / AG-6 — NO REGRESSION, NO PYTHON DECISIONS

**AG5.**  `test_goal_residual_migrated` **31/31** and
`test_arc6_valuelayer_migrated` **35/35** — **66 passed** in one run on this
engine.  The four-suite confirmation run (those two, plus
`test_arc_goals_migrated` 37/37 and `test_arc6_tier0_migrated`) is
**123 passed, 1 failed**, and the single failure is the untracked-file red
described in §8.6 — no assertion anywhere moved (the gr4 gate rewrote its own output again; restored, §8.8).  That includes `test_gr4_the_live_mbpp_pass_ids_are_unchanged`, which
runs the full 257-task split and pins the **48 pass ids and 95 accepted ids as
paired lists** against a freshly measured pre-patch baseline on the same
engine.  `lost: []`, `gained: []`.

**TWO WIDER SWEEPS, EACH WITH A CONTROL.**

| sweep | `-k` filter | result |
|---|---|---|
| A | `migrated and (goal or arc6 or gap or shape_decode)` | **415 passed, 5 failed** |
| B | `migrated and (goal or arc6 or capability or gap or shape_decode or seed)` | **793 passed, 7 skipped, 20 failed** |

In each, **exactly one** failure is this rung's: the untracked-file red on
`test_arc6_tier0_migrated::test_no_python_decision_was_added` (§8.6).

The other 4 and 19 are **not in `results/failure_baseline.json`** — that
baseline was measured at head `0e61f60e8d` on engine `d657468d9e1f` with **no
`data/` symlink**, so it is not comparable to this run and *"it's in the
baseline"* was **not available as an answer**.  The standing rule in this tree
is that a status line must not be reusable as an excuse, so they were
**controlled, not characterised**: this rung's six files were **physically
moved out of the tree** and the same test files re-run.

| control | reproduced | extra |
|---|---|---|
| sweep A's 4 | **4/4** | +2 (`test_search_reach_migrated` is order/session-sensitive) |
| sweep B's 19 | **19/19** | +4 (two more `test_run67_migrated`, two more `test_search_reach_migrated`) |

**Every red reproduces with this rung removed — a strict superset in both
cases.  None is attributable to this work.**  (That the control produces
*more* reds than the sweep is itself the honest reading: several of these
files are order-dependent, which is a property of the tree, not of the
change.)

The confinement is structural and asserted against `HEAD`
(`test_ag5_the_synthesis_path_seeds_are_UNTOUCHED`):
`seeds/program_synthesis.json`, `seeds/goal_residuals.json`,
`seeds/gap_prioritization.json` and `seeds/stopping_policy.json` are
**byte-identical to `HEAD`**.  The last two deliberately — their population is
Python-written and adding to it has perturbed a gate before
(`concern_to_target_bridge.json`'s own `_non_resident_note`: a resident copy
shifted `test_gap_is_idempotent`'s `CapabilityGap` count 0→1).

**The seed ships `self_load_only: true`, and that is a decision, not an
oversight.**  `substrate/boot_all.py::_read_seeds` **globs `seeds/*.json`** and
installs every match at boot, so a file there is live in **every agent in the
tree** the moment it lands.  Phase 2 is not a tree-wide-sweep rung, so the seed
takes the design's own §11 *"safer for a first landing"* route: `_read_seeds`
skips it, `seed_loader.manifest_for` still reads it by path, and
`domains/arc_goal_ingest.ensure_arc_goals` self-loads it on demand (the
`reading_collapse::_ensure_role_decode_loop` precedent).
`test_ag5_the_seed_is_NOT_globbed_into_every_agent_in_the_tree` asserts **both
halves** — that a full `_read_seeds` does not pick it up, and that the
on-demand route still works, so "absent" cannot be mistaken for "safe".
**Removing that key is the tree-wide activation and needs the paired sweep A5
requires.**

**AG6.**  `domains/arc_goal_ingest.py` never imports `substrate_rs`, never
calls `.evaluate(`, never calls `run_rules`, and its only substrate contact is
`add_node` / `node` / `nodes` / `set_attr` / `remove_node` /
`add_edge_unchecked` / `load_seed_manifest` — so there is no place in it for a
decision over graph state to hide.  *(The audit reads the module through `ast`
with string literals stripped: a source audit that greps the raw file greps its
own docstring, and this one describes the banned calls in prose.  My first
version failed on itself.)*  The seed regenerates **byte-identically** from
`tools/build_arc_goals_seed.py --check`.

**Every rule is asserted to INSTALL and to FIRE.**  *An unknown op or field
name is a silent no-op, not a trap*, and a gate written to catch that trap has
already fallen into it in this tree — so
`test_ag1_every_rule_in_the_seed_actually_INSTALLED` checks the loader kept all
19, and four `test_every_rule_…` scenes exercise the rules no other scene
reaches (`ag_vocab_alias`, `ag_revocab`, `ag_mint_self_concern`,
`ag_dim_check_mark`), each in both directions.

---

## 8. EVERYTHING THAT BROKE

Recorded because the process is the result.

1. **`Lt(null, 0.0)` is `True` in this engine — a missing attr sorts BELOW any
   number — and it silently broke the Occam ladder.**  Written literally,
   `ag_revocab`'s epoch guard re-armed **every never-decoded goal on the very
   first pass**, which cleared `dim_explained` and so **erased the deferred
   rung 3's claim before rung 4 looked at it**.  An Occam-order violation
   caused by a null, not by a rule.  Caught by
   `test_every_rule_ag_dim_check_mark_…`'s refuting half — the direction that
   exists precisely because a bug there is indistinguishable from an honest
   null.  Fixed by coalescing, and **both** the engine behaviour and the
   coalesce are now pinned
   (`test_a_MISSING_attr_sorts_BELOW_any_number_…`).
2. **`StringConcat` SILENTLY DROPS numeric parts.**  Two numeric attrs
   concatenated with two literals produce `'f= i='`.  The AG-4 bar requires the
   question to carry the *measured numbers*, so every number goes through
   `ToJsonString` first — and `test_ag4_the_question_carries_the_MEASURED_
   NUMBERS_…` is what says so if that regresses.  (Found by probing, before it
   could become a question that looked fine and said nothing.)
3. **The naive seed emitted at 2.4 MB.**  Deriving the runner-up inside its own
   pool predicate embeds the whole `PENALTY` subtree once per use *and*
   evaluates it once per pool element.  Fixed by splitting the selector into a
   guard chain — `ag_select` → `ag_select_audit` → `ag_select_runner_up` →
   `ag_select_margin`, each binding by the previous one's stamped `agid`.  This
   engine has **no rule ordering**, so a dependency has to be a guard chain
   anyway; making it explicit is the honest form, and the seed is now 284 KB.
4. **The weight/veto structural gate initially failed on its own subject.**
   `PENALTY` contains an inner `Argmax` over `GoalResidual` — that one **is**
   the weight — so a naive "no `GoalResidual` in any `Argmax` source" walks
   into it.  The gate now scopes to the terms whose source is the arc-goal
   pool, and pins the count at 3 so it cannot pass vacuously.
5. **The live-graph verbatim audit pointed at the wrong corpus** (§5).
6. **`test_arc6_tier0_migrated::test_no_python_decision_was_added` is RED in
   this worktree**, and will be until the orchestrator commits: it asserts
   `git status --porcelain domains seeds` is empty, and the two new files
   (`domains/arc_goal_ingest.py`, `seeds/arc_goals.json`) are untracked.
   Verified to be **exactly** those two entries — no existing file under
   `domains/` or `seeds/` is modified.  The other 20 tier-0 gates are green.
7. **The `results/run*_checkpoints` symlinks were REMOVED before handing the
   worktree over.**  The brief calls for symlinking them so their absence does
   not manufacture reds; in this worktree they are real directories already,
   and the symlinks I added showed as **untracked files** (`.gitignore`'s
   pattern is directory-scoped) — which is a live risk if a commit is made
   with `git add -A`, because a symlink into another worktree would be
   committed.  Removed, and the four suites above re-verified green without
   them.  **`git status --porcelain` is now exactly the deliverables plus the
   two draft deletions.**
8. **`results/arc6_verdict_gr4_gate.json` was rewritten by running the gr4
   gate** (it is the gate's own output).  `pass_ids` and `accepted_ids` are
   byte-identical; only `measured_at` / `elapsed_seconds` / the worktree path
   in `engine_provenance` moved.  **Restored with `git checkout --`** rather
   than carried as this rung's change.

---

## 9. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **AG-5 is not built, and it is the real rung.**  Everything here makes goals
   *exist*, *rank*, *lapse* and *ask*.  None of it makes the loop **run**.  The
   `arc_measure_epoch` fact — which the whole testimony-expiry mechanism turns
   on — is bumped by `domains/arc_goal_ingest.bump_measure_epoch`, i.e. **by a
   caller, not by a measurement**.  That is honest as an adapter (a measurement
   happening is a fact about the world) and it is also exactly the seam AG-5
   would close.  **Until then, "an unconditioned answer expires at the next
   measurement epoch" is true of a counter nobody increments automatically.**
2. **The tie-break is measured, not authored** (§4.5).  `insertion_order_stable`
   is a description of this engine's `Argmax`, not a property the seed
   enforces.  A lexical tie-break needs a string-ordering Term that does not
   exist here.  The oscillation property *is* gated; the pinned mechanism is
   not the one the design asked for.
3. **`cost_bits` is authored and therefore gameable** — most acutely once the
   agent authors its own goals.  The cheap-goal probe (§4.4) shows the collapse
   does *not* currently converge on cheap, but that is a measurement of today's
   population, not a bound.  The design's §8.3 hole is untouched.
4. **`w_unsignatured = 25.0` is an invented number.**  It has a two-position
   test (it can flip the outcome in both directions) and no principled value.
   Set too high it suppresses the `SelfConcern` channel `CLAUDE.md` treats as
   the agent's primary self-discovery route.
5. **Rung 3 of the vocabulary ladder is deferred**, so a goal that is not a
   (seam, lever, target) triple still has no way in.
6. **The seed is `self_load_only`, so nothing in the tree loads it yet.**  Every
   result above is measured on a boot that asks for it explicitly.  That is the
   right first landing, and it means **the tree-wide behaviour of this seed is
   unmeasured**.  Activation is one key and a paired sweep.
7. **`ag_mint_blocker` fires on exactly one residual today** — seam A is the
   only one carrying a `reach_class_counts` payload.  The mechanism is general;
   its current reach is one node, and a second payload would be the honest test
   of the dedup keying.
8. **§8.2's STATUS-LIFECYCLE anti-oscillation guard is NOT implemented.**  The
   design's second oscillation guard is *"a selected goal moves to a terminal
   status and only re-enters the pool on a `measure_epoch` bump"*.  `ag_select`
   filters `retired` and `settled` out of the pool, but **nothing ever writes
   `selected` / `pursued` / `settled`** — because moving a goal to a terminal
   status with no executor would empty the pool with nothing done.  The guard
   that IS implemented is determinism (same state → same winner, repeatedly,
   gated).  The lifecycle half belongs with AG-5 and is named, not silently
   absent.
9. **The question-rate-as-observable claim is still untested.**  One question
   fires on the shipped graph.  A rate needs epochs, and epochs need AG-5.

---

## 10. WHAT MADE ME WANT TO BUILD AG-5 — reported, not taken

Three specific pulls, each a place where the mechanism is complete right up to
the point where something has to *run*:

- **The re-measurement goal is the executor's own best first job.**  It names
  an artifact (`results/arc6_verdict_pricing.json`), a condition
  (`value_layer_list_eq_tuple`), and a 15-task denominator.  Re-running that
  measurement is a bounded, already-scripted action — `scripts/arc6_verdict_
  battery.py` exists.  The loop is one `route_pick`-shaped dispatch away from
  closing on the goal it minted about itself.
- **`arc_measure_epoch` is a counter with no producer** (§9.1).  Writing the
  bump into the executor is a two-line change and it would make the testimony
  expiry *mean* something rather than *be able to* mean something.
- **The ask is answered by a human who is not there.**  One question sits open
  on the shipped graph; `ag_question_retire` will lapse it at the next epoch
  that never comes.

I did not build any of it.  An executor that runs arbitrary measurement code
chosen by a graph collapse is a materially different proposition from
everything above, the designer named it as both the real rung and the largest
uncertainty, and it was explicitly out of scope.

---

## 11. FILES

| file | what |
|---|---|
| `seeds/arc_goals.json` | the seed — 16 nodes, 8 edges, 17 productions, **19 rules**.  `self_load_only`.  Emitted, not hand-written |
| `tools/build_arc_goals_seed.py` | the emitter; lifts `gr_move_penalty`'s PENALTY subtree at build time |
| `domains/arc_goal_ingest.py` | the world adapter — self-load, the measurement epoch, a reply's structured condition.  Mechanical I/O only |
| `tests/test_arc_goals_migrated.py` | the gate — **37/37** |
| `scripts/arc6_arc_goals_measure.py` | the measurement runner |
| `results/arc6_arc_goals.json` | the artifact, engine-stamped |
| `drafts/arc_goals/` | phase-1 draft seed + gate **removed** (they had diverged from what shipped); `SUPERSEDED.md` left as the pointer |
