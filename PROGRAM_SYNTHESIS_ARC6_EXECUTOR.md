# ARC 6 — AG-5: THE EXECUTOR AND THE STATUS LIFECYCLE

**Date:** 2026-08-04
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A10** (`EX1`–`EX6`),
registered **before** this build.
**Base commit:** `a3d3fcb8d3` (detached worktree `/home/matt/arc6-executor`).
**Engine:** `8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`,
copied into this worktree and **verified resolving from inside it** —
`_native.__file__` is
`/home/matt/arc6-executor/…/runners/dsl/python/substrate_rs/_native.abi3.so`,
not the canonical tree's.  Behaviourally probed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Artifact:** `results/arc6_executor.json` (engine stamped).
**Gate:** `tests/test_arc_executor_migrated.py` — **35/35 green**.

**SCOPE: the executor, the terminal status, the epoch producer, and
anti-oscillation.  DECOMPOSITION (MG4) IS NOT BUILT.**  This rung unblocks it;
§10 records what made me want to build it anyway, as an observation, not as a
change.

**NO ENGINE CHANGE.**  Zero `.rs`, zero rebuild — so A1.2's three arms and
A1.1's archive requirement do not apply, and every measurement below is on the
single binary named above.  Nothing under `domains/`, `seeds/` or `scripts/`
that already existed was edited: this rung is **six new files** plus its
results artifact (§11).

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **EX1 — it actually runs, and the condition refreshes** | **PASS** | the executor re-ran the row-verdict ceiling **live** — two 257-task battery arms, the seed patch applied and reverted, and the constructed-witness report — in **88.1 s** on this binary; the residual's condition was re-anchored `"1"` → `"0"` and `gr_condition_hold` un-staled it (`stale` 1.0 → 0.0).  §2 |
| **EX2 — terminal status, and the pool shrinks by exactly one** | **PASS** | pool **8 → 7**, `left_the_pool: [arc.remeasure.…row_verdict_seed_only]`, `joined_the_pool: []`, status `retired`, `retired_because: source_residual_no_longer_stale` — **the existing rule**.  §3 |
| **EX3 — the epoch clock starts** | **PASS** | epoch `"0"` → `"1"`, produced by the measurement itself; a pending **unconditioned** reply's testimony residual goes `stale 0.0 → 1.0` at that bump, and a **conditioned** one does not.  §4 |
| **EX4 — anti-oscillation, both directions** | **PASS** | four cells: churn → no re-mint; condition genuinely re-failed at the **same** epoch → no re-mint; re-failed **and** epoch advanced → back in the pool, `rearm_count 1.0`; world restored → terminal again.  Each half of the latch shown load-bearing.  §5 |
| **EX5 — run the loop end to end and report what happened** | **PASS (reported)** | one execution, then **it stopped because nothing left is executable**.  **It did NOT converge on re-measurement.**  It asked in one arm and did **not** ask in the other — and the reason is a finding.  §6 |
| **EX6 — no regression** | **PASS** | executor **35/35**, `arc_goals` **37/37**, `goal_residual` **31/31**, `arc6_valuelayer` **35/35**, `arc_magnitude` **42/43** with the single failure **pre-existing at HEAD and independent of this rung** (§8.10).  The **48** live MBPP pass ids preserved as a paired list, `lost: []`.  Source audit passes.  §7 |

**Confinement is structural, and the shipped boot exercises it for free**: on a
clean boot the collapse's winner is the 42-task blocker goal, which has no
`ExecClass`, so **zero orders mint** without any fixture arranging it.

---

## 1. WHAT WAS BUILT

Four rules, a two-node route table, one adapter, one runner.

```
seeds/arc_executor.json        2 nodes, 1 edge, 3 productions, 4 rules
                              self_load_only, depends_on [goal_residuals, arc_goals]

  ax_dispatch        the collapse → action seam.  route_pick's own
                     Argmin-over-cues shape, keyed on (kind, evidence_artifact,
                     source_rid), binding the winner by ag_select's OWN stamp
  ax_retired_epoch   stamps WHEN a goal reached terminal status
  ax_rearm           the anti-oscillation latch (the arc-goal design's §8.2
                     guard, which that rung recorded as NOT implemented)
  ax_close           a completed execution becomes a countable graph fact

domains/arc_executor.py        the adapter — self-load, arm, run, re-ingest,
                               bump the epoch.  Mechanical I/O only.
scripts/arc6_remeasure_row_verdict.py   the ONE runner in the capability table
```

**The decision of what to run is the rule.**  `ax_dispatch`'s `Argmin` over the
`ExecClass` cues, applied to the collapse's own winner, *is* the choice.  The
adapter reads the resulting `runner` **name**, looks it up in a frozen
one-entry table, and invokes it.  The table is a **permission boundary** — the
same shape as `seed_loader.manifest_for` — not a decision: a name with no entry
is recorded and refused, and the string is never a path, never an argv word and
never reaches a shell.

**What "re-measure" means here, exactly.**  `results/arc6_verdict_pricing.json`
was produced by three existing scripts run in sequence
(`arc6_verdict_battery.py before` → `arc6_verdict_patch.py apply` →
`arc6_verdict_battery.py after` → `revert` → `arc6_verdict_report.py`).  The
runner re-runs **that same sequence, unmodified**, on the current binary.
Nothing is re-implemented and nothing is approximated.

---

## 2. EX1 — IT RAN, AND WHAT IT MEASURED IS ITSELF A RESULT

### 2.1 The run

```
runner                     arc6_remeasure_row_verdict
elapsed                    88.1 s   (two 257-task arms + the witness sweep)
fresh artifact             results/arc6_verdict_pricing_remeasure_uncond_i0_e0.json
engine of the fresh number 8311d4356082…  (== this process's engine)
frozen artifacts restored  byte-identical: True
```

`arc6_verdict_report.py` hard-codes its input labels (`before`/`after`) and its
output path, so the runner **saves the three committed artifacts and
`seeds/program_synthesis.json` and restores them byte-for-byte in a `finally`**
— including the seed patch's revert.  A run that dies half way leaves the tree
exactly as it found it.  The gate asserts this **against `HEAD`**, not against
the runner's own claim, and `git status` after every run in this rung shows
only this rung's own new files.

### 2.2 The condition refreshes — and this is the rung's one modelling choice

Before, the residual holds under `value_layer_list_eq_tuple == "1"`; the live
value on this engine is `"0"`; so it is **stale**, which is why the goal existed
at all.

After, the condition reads `expected_str: "0"` and a **second** condition
appears — `remeasured_evidence_present.arc6.verdict.row_verdict_seed_only ==
"1"`.  `gr_condition_hold` — an existing rule, untouched — un-stales the
residual.  The adapter **never writes `stale`**.

**Stated in the open, because it is the load-bearing choice.**  A
`ResidualCondition` in this tree records *the world-state a measurement was
taken under* — five of the six shipped ones say *"the artifact this residual
quotes is still on disk with the sha it was ingested at"*.  A **re**-measurement
is a new measurement, so its provenance is the world **as probed at the moment
it ran**, and the adapter copies that probe onto the conditions.  It never
writes a value chosen to make a condition hold: it writes what
`goal_residual_ingest.probe_facts` measured, in-process, on this engine.

**The proof that this is not a tautology is that the re-anchored conditions can
and do re-fail.**  Gated in both directions in one scene
(`test_ex1_the_reanchor_is_NOT_a_tautology_it_can_re_fail`): move the fresh
artifact off the disk → the fact is re-probed → `gr_condition_lapse` stales the
residual; restore it → it holds again.  A condition that could only ever hold
would have measured the write and not the world.

### 2.3 THE RE-MEASUREMENT'S OWN RESULT — the refutation is gone

The residual carried arc 6's row-verdict **NO-GO**: *12 false accepts caused by
list and tuple being one `Value::Tuple`*.  Re-measured on `8311d4356082`, where
they are not:

| | measured `48da7257` (the residual's evidence) | re-measured `8311d4356082` |
|---|---|---|
| newly accepted by the seed-only fix | 15 ids | **`[222]`** |
| accepts that REQUIRE the list/tuple collapse | 12 | **`[]`** |
| accepts failing the corpus's own `assert` semantics | 12 | **`[]`** |
| `bar_2_zero_false_accepts_from_list_tuple_collapse` | **FAIL** | **PASS** |
| `bar_1_three_of_five_known_convert_with_witnesses` | FAIL | FAIL — *for the opposite reason* |
| GO / NO-GO | NO-GO | NO-GO |
| residual `ceiling_honest_n` / `denominator_n` | 4 / 15 | **0 / 1** |

**The mechanism that made it a NO-GO no longer exists.**  What is left is a much
smaller and different claim: the comparator swap now moves exactly one task
(222), and the witness sweep judges that one a **coincidental fit** — a
`Fraction(1,1)` accepted where a `bool` is expected.  `bar_1` fails now because
the *baseline* arm on this engine already accepts the five known ids, so there
is nothing left for the fix to convert.

This is what the goal was **for**: the row-verdict ceiling was measured under a
value layer that no longer exists, and it has now been re-measured rather than
re-quoted.  Every number above is a read-off from an artifact this loop
produced.

---

## 3. EX2 — THE TERMINAL STATUS, AND THE POOL

```
pool_before  8   [remeasure.row_verdict, supply.budget, supply.missing_dimension,
                  supply.missing_structural_primitive, claim.seam_b, claim.seam_d,
                  claim.tier0, claim.valuelayer]
pool_after   7   (the same, minus the re-measurement goal)
shrank_by    1
left_the_pool    ['arc.remeasure.arc6.verdict.row_verdict_seed_only']
joined_the_pool  []
status           retired
retired_because  source_residual_no_longer_stale     ← the EXISTING rule
retired_epoch    "1"
order status     closed  (outcome: goal_retired_source_residual_no_longer_stale)
```

`ag_remeasure_retire` already existed and already had the right guard; what it
never had was a **cause**.  The executor supplies it: a real measurement makes
the source residual describe the world again, and the goal that asked for the
measurement is done.

**This is the thing the magnitude rung was blocked on.**  Its §6.2(2) recorded
that a decomposed parent must leave the pool or parent + children double-count
the same 42 tasks, and that *nothing in this tree ever writes a terminal
status*.  Something does now, and `ax_retired_epoch` gives it a timestamp the
latch can compare against.

**Measured caveat, and it is a finding, not a caveat about the bar.**  The `8 →
7` above is the arm where the world's reply named a checkable reason.  Under an
**unconditioned** reply the net count is `8 → 8`: the expired testimony residual
mints a *new* re-measurement goal (§8.3).  The retirement is identical in both
arms — `left_the_pool` is the same single id — but the net count hides it, which
is exactly why the two arms are reported separately rather than averaged.

---

## 4. EX3 — THE EPOCH CLOCK STARTS

`arc_measure_epoch` has been *"a counter with no producer"* through two rungs,
named as uncertainty #1 by the arc-goal write-up and #8 by the magnitude one.
It has one now, and it counts **measurements**, not ticks: `run_order` bumps it
after the runner returns, and nowhere else.

```
epoch before the measurement   "0"
epoch after                    "1"
testimony residual before      arc.testimony.missing_structural_primitive  stale 0.0
testimony residual after       arc.testimony.missing_structural_primitive  stale 1.0
```

**The Angluin mechanism ticking for the first time.**  An unconditioned reply
mints a `GoalResidual{evidence_kind: "utterance"}` holding under
`fact_equals(arc_measure_epoch == <epoch at reply>)` — *an answer with no
counterexample carries ~0 bits and lasts one epoch*.  Until this rung that was
true of a counter nobody incremented.

**The control (A7).**  The identical scene, the identical bump, with the ONLY
change being whether the reply named a checkable reason:

| reply | testimony `stale` after the bump |
|---|---|
| unconditioned | **1.0** — expired |
| conditioned (`arc6_structural_ceiling_present == "1"`) | **0.0** — still standing |

The instrument can express the difference; a one-armed demonstration would have
measured the bump rather than the mechanism.

**And the other expiry fires too.**  `ag_question_retire` — *"one question sits
open on the shipped graph; it will lapse at the next epoch that never comes"* —
now lapses it: `open` → `unanswered_lapsed` at the first epoch the executor
produces.

---

## 5. EX4 — ANTI-OSCILLATION, BOTH DIRECTIONS

`ax_rearm` is the arc-goal design's §8.2 guard, which that rung recorded as **not
implemented** because *"moving a goal to a terminal status with no executor
would empty the pool with nothing done."*  It is a **conjunction**: a terminal
goal re-enters the pool only when its source residual is **genuinely stale
again** AND the **measurement epoch has advanced** past its retirement.

Walked through four cells on the live post-execution graph.  Cell C's re-failure
is a real world change — the fresh artifact leaves the disk — not a graph poke.

| cell | condition | epoch | `stale` | status | in pool |
|---|---|---|---|---|---|
| **A** after the execution | holds | 1 | 0.0 | `retired` | no |
| **B** three more fixpoints | holds | 1 | 0.0 | `retired` | no |
| **C** artifact removed | **re-failed** | 1 | **1.0** | `retired` | **no** |
| **D** epoch advances | re-failed | **2** | 1.0 | **non-terminal** | **yes**, `rearm_count 1.0` |
| **E** artifact restored | holds | 2 | 0.0 | `retired` (`retired_epoch "2"`) | no |

- **Direction 1** — B and C: churn does not re-mint, and neither does a genuine
  re-failure on its own.
- **Direction 2** — D: it *does* come back when the condition genuinely
  re-fails and the clock has moved.
- **Each half load-bearing** — C holds the epoch fixed and the goal stays
  terminal; E holds the condition fixed at *holding* with a later epoch and the
  goal returns to terminal.  Without both cells, "it did not re-mint" would be
  consistent with the rule never firing at all.
- **The round trip closes** — E is `retired` again with a **fresh**
  `retired_epoch`, not the stale one, so the latch compares against a live
  number on the second lap.  (A `__consumed_by_ax_rearm__` sentinel does that
  work; this engine has no `unset_attr`.)

**In cell D the status may read `pursued` rather than `minted`** — once back in
the pool it is again the collapse's winner and `ax_dispatch` orders it in the
same fixpoint.  That is the loop working, so the bar is asserted as
*non-terminal and in the pool*, not as one particular string.

**THE DEADLOCK THIS EXPOSES — reported, not patched.**  Cell D needed an epoch
bump from **outside** this loop.  The executor is the epoch's producer, but it
only produces one by *running* a goal, and a retired goal is not in the pool to
be run.  **With exactly one executable goal, a genuinely re-failed condition
cannot bring it back on its own.**  Per A9 the missing term is *what else makes
an epoch advance*, and a missing term is not a guard — so nothing was added.

---

## 6. EX5 — WHAT THE LOOP ACTUALLY DID

The primary bar.  Run end to end, twice, differing in exactly one thing:
whether the world's reply named a checkable reason.

### 6.1 Arm 1 — the world answers with no reason (unconditioned)

```
iter 0   epoch 0   pool 8
         winner  supply.missing_structural_primitive   value 10.0
         runner-up  remeasure.row_verdict              value  7.7
         margin 2.3  <  threshold 5.0   and neither is covered by a live
                                        measurement                → IT ASKS
         world replies, unconditioned
         → testimony residual (weight 50) lands in region
           `missing_structural_primitive`; gr_move_penalty charges the blocker
           goal; the collapse now settles on  remeasure.row_verdict  (7.7)
         armed → ax_dispatch mints an ExecOrder → THE MEASUREMENT RUNS (88.1 s)
         → condition re-anchored → residual un-stales → goal RETIRED
         → epoch 0→1 → the unconditioned testimony EXPIRES
         → the expired testimony mints  arc.remeasure.arc.testimony.
           missing_structural_primitive   (pool 8 → 8 net)

iter 1   epoch 1   pool 8
         winner  supply.missing_structural_primitive   value 10.0 (uncharged
                                                       again — the testimony
                                                       expired)
         margin 9.5  >  threshold 5.0                  → IT DOES NOT ASK
         armed → kind `supply_blocker` has no ExecClass → NO ORDER
         STOP: no_executable_goal_was_selected
```

### 6.2 Arm 2 — the world answers with a reason (conditioned)

```
iter 0   identical up to the execution; the testimony does NOT expire, so
         pool 8 → 7 and the retirement is visible in the count
iter 1   epoch 1   pool 7
         winner  supply.budget   value −25.0   margin 0.0   → IT ASKS AGAIN
         after the reply the winner is  claim.seam_b  (−25.0), kind
         `source_claim` → no ExecClass → NO ORDER
         STOP: no_executable_goal_was_selected
```

### 6.3 The reading

**It did not converge on cheap re-measurement.**  A10 registered that as the
outcome to report honestly if it happened; it did not.  **Exactly one
execution** in each arm, and the goal then left the pool and stayed out.  The
anti-oscillation latch and the retire rule are what stopped it, and both were
measured firing (§5).

**A10's expected trajectory is confirmed up to its last clause.**  *re-measure →
condition refreshes → residual un-stales → goal retires → the pool holds only
unexecutable goals* — all four, live.  **→ it asks** is where it is only
*contingently* true:

> **The ask fires on a TIE, not on impotence.**  `ag_ask`'s trigger is
> `margin < threshold` under mutual ignorance.  In arm 1 the loop ended with a
> margin of **9.5** and stopped **silently**, holding a pool of goals it cannot
> act on and saying nothing.  In arm 2 the remaining goals happened to tie at
> −25.0, so it did ask.  **There is no term for "I cannot act on my own
> agenda."**

Per A9 that is a **missing term, not a missing guard**, and it was not added.
It is the sharpest thing this loop surfaced: a planning layer that has just
discovered every remaining goal is beyond its hands has something very specific
to say, and no way to say it.

---

## 7. EX6 — NO REGRESSION, NO PYTHON DECISIONS, CONFINEMENT

| suite | result |
|---|---|
| `test_arc_executor_migrated` | **35 / 35** |
| `test_arc_goals_migrated` | **37 / 37** |
| `test_goal_residual_migrated` | **31 / 31** |
| `test_arc6_valuelayer_migrated` | **35 / 35** |
| `test_arc_magnitude_migrated` | **42 / 43** — the one failure is **pre-existing at HEAD** and independent of this rung (§8.10) |

**The 48 live MBPP pass ids**, re-measured during this run by
`test_gr4_the_live_mbpp_pass_ids_are_unchanged` and reported as a **paired
list**:

```
[16, 20, 58, 59, 69, 82, 84, 85, 89, 90, 120, 127, 132, 135, 138, 139, 142,
 145, 161, 227, 233, 234, 249, 257, 266, 272, 276, 278, 281, 290, 309, 312,
 393, 394, 404, 406, 410, 413, 418, 433, 436, 443, 450, 457, 458, 460, 472, 477]
lost: []
```

**Frozen things stayed frozen.**  `seeds/arc_goals.json`,
`seeds/arc_magnitude.json`, `seeds/goal_residuals.json`,
`seeds/program_synthesis.json`, `domains/arc_goal_ingest.py` and
`domains/goal_residual_ingest.py` are asserted byte-identical to `HEAD` by the
gate.  `git status` shows only this rung's own new files **plus
`results/arc6_verdict_gr4_gate.json`**, which
`test_goal_residual_migrated::test_gr4_the_live_mbpp_pass_ids_are_unchanged`
rewrites on every run by design — its `pass_ids` and `accepted_ids` are
**identical** to `HEAD`'s; only `measured_at`, `elapsed_seconds`,
`determinism` timings and the engine's worktree **path** differ.

### 7.1 No Python decisions

The adapter passes the module-specific source audit in the stronger form
`domains/arc_goal_ingest.py` already passes: it **never imports `substrate_rs`,
never calls `.evaluate(`, never calls `run_rules`**, and its only substrate
contact is `add_node` / `node` / `nodes` / `set_attr` / `add_edge_unchecked` /
`load_seed_manifest`.  With no evaluator and no rule engine reachable from it
there is nowhere for a decision over graph state to hide.  The runner is
audited too — it never touches the substrate at all.

### 7.2 Confinement is structural, and it was tested by attack

Every goal was made the collapse's **genuine** winner in turn (all others
retired — spoofing the stamp does not work, see §8.1) and the executor armed on
it:

| goal | kind | orders minted |
|---|---|---|
| `arc.remeasure.arc6.verdict.row_verdict_seed_only` | `re_measure` | **1** |
| `arc.supply.…missing_structural_primitive` | `supply_blocker` | 0 |
| `arc.supply.…budget` | `supply_blocker` | 0 |
| `arc.supply.…missing_dimension` | `supply_blocker` | 0 |
| `arc6.claim.seam_b_signature_39_of_257` | `source_claim` | 0 |
| `arc6.claim.seam_d_verbatim_35_of_36` | `source_claim` | 0 |
| `arc6.claim.tier0_hs1_0_of_10` | `source_claim` | 0 |
| `arc6.claim.valuelayer_supersedes_row_verdict` | `source_claim` | 0 |
| `arc.remeasure.arc.testimony.missing_structural_primitive` | **`re_measure`** | **0** — §8.2 |

The refusal is **the empty route `Argmin`**, not a check that could be deleted.
And a forged `ExecOrder` naming a runner outside the capability table is
recorded `refused` with `refused_because:
runner_name_not_in_the_capability_table` — it never reaches an interpreter.

---

## 8. EVERYTHING THAT BROKE

Recorded because the process is the result.  The first two are defects **in this
rung**, found by running it.

1. **THE ARGMAX STAMP IS A TRANSIENT INSIDE THE FIXPOINT THAT WRITES IT — and
   the first draft of `ax_dispatch` acted on it.**  On the shipped boot it
   minted an `ExecOrder` for `arc.remeasure.arc6.verdict.row_verdict_seed_only`
   while the fixpoint's **final** `arc_sel_agid` was
   `arc.supply.…missing_structural_primitive`.  **The executor ordered the
   runner-up.**  Nothing errored — this is the `children_of` hazard class
   exactly: the wrong thing simply happens.  `run_rules` is a fixpoint with no
   rule ordering, so `ag_select`'s stamp is whatever it happens to hold while
   `ag_mint_*` is still populating the pool and `ag_vocab_mint` is still pricing
   novelty.  Closed by a **two-tick agreement**: the adapter copies the settled
   `arc_sel_agid` / `arc_sel_value` into `arc_exec_armed_*` at the tick boundary
   — a verbatim copy, no comparison, no branch — and `ax_dispatch` requires the
   *next* fixpoint's selection to agree on **both**.  The comparison is the
   rule's.  Gated in both directions.
   **`ag_ask` (in the byte-frozen `arc_goals` seed) reads the same two stamps in
   the same fixpoint and has the same exposure.**  Not touched; reported.
2. **`kind` ALONE UNDERDETERMINES THE JOB, and the tree produced the
   counter-example unprompted.**  An expired unconditioned testimony makes
   `ag_mint_remeasure` fire **on the testimony**, minting
   `arc.remeasure.arc.testimony.missing_structural_primitive` with
   `kind: "re_measure"` and **no** `evidence_artifact`.  A route keyed on `kind`
   alone — which this rung shipped first — would have handed *the human's own
   expired answer* to the row-verdict runner.  The route key is now
   **(kind, evidence_artifact, source_rid)**, and that case is a gate.
3. **AN UNCONDITIONED ANSWER, WHATEVER IT SAYS, PENALISES THE REGION IT IS
   ABOUT.**  `ag_reply_mints_testimony_*` mints a `GoalResidual` with weight
   `scale × factor = 50` in the question's region; `gr_move_penalty` then charges
   every goal carrying that signature.  So *asking and getting any answer at
   all* makes the asked-about goal lose.  **This is what let the loop act**: the
   blocker goal dropped from 10.0 and the re-measurement goal became the winner.
   Defensible as *"a human weighed in, so this is no longer pure ignorance"* —
   but it is a **weight applied for the existence of an answer, not for its
   content**, and the content is never read.  Shipped behaviour, not this
   rung's; named because the loop's only path to acting runs through it.
4. **THE POOL DOES NOT NET-SHRINK UNDER AN UNCONDITIONED REPLY** (§3), because
   the expired testimony mints a fresh re-measurement goal.  The retirement is
   identical; the net count hides it.  Isolated with the conditioned arm rather
   than averaged away.
5. **THE RE-ARM DEADLOCK** (§5).  One executable goal ⇒ a genuinely re-failed
   condition cannot bring it back without an epoch from elsewhere.
6. **THE ASK HAS NO INEXECUTABILITY TERM** (§6.3).  The loop can end holding a
   pool it cannot act on and say nothing.
7. **`arc6_verdict_report.py` HARD-CODES ITS LABELS AND OUTPUT PATH**, so a
   re-measurement necessarily disturbs three committed artifacts and the shipped
   `seeds/program_synthesis.json`.  Handled by save/restore in a `finally` with
   a byte-identity assert against `HEAD` — but a measurement script that cannot
   be pointed at a different output is a re-measurement hazard, and the next
   runner will hit it again.
8. **`type_collapse.mechanism` IS AUTHORED PROSE INSIDE A MEASUREMENT SCRIPT,
   AND IT IS NOW FALSE.**  The re-measurement reproduces, verbatim, *"Python
   list and Python tuple are BOTH `Value::Tuple` in this substrate, **verified
   live**"* — on an engine where they are not — while the **measured** fields
   two lines below it in the same block read
   `newly_accepted_whose_accept_needs_the_collapse: []`.  That string is what
   `goal_residual_ingest` ingests into the residual's `mechanism` attr, so the
   graph now holds a re-measured residual whose *numbers* are current and whose
   *mechanism sentence* is stale.  This is CLAUDE.md's own retraction shape —
   a claim quoted without its condition — one level down, inside the instrument.
   **Reported, not patched**: fixing it edits a measurement script mid-rung.
9. **THERE ARE TWO COLLAPSES ON THIS GRAPH AND THE HANDS FOLLOW THE OLDER ONE.**
   `ax_dispatch` binds `ag_select`'s `arc_sel_agid`.  The magnitude rung's
   order-N collapse writes a **separate** stamp, `mg_sel_agid`.  Measured with
   `seeds/arc_magnitude.json` live and its measured tier ladder installed:

   | | winner | value |
   |---|---|---|
   | `arc_sel_agid` (order-1) | `arc.supply.…missing_structural_primitive` | 10.0 |
   | `mg_sel_agid` (order-N + constraints) | **`arc.remeasure.…row_verdict_seed_only`** | 7.7 |

   The cause is MG2's own mechanism doing exactly what it was built to do: the
   42-task blocker goal's **order-N headroom is 13.64, not 42** — discounted by
   the measured attrition ladder — while the re-measurement goal's is
   undiscounted at 11.0, because completing it unlocks nothing and its order-1
   value *is* its total value.  **Without the tier ladder installed the two
   collapses agree** (both pick the blocker at 10.0), so the divergence is the
   ladder's, and it is measured in both positions.

   **Order-N picks exactly the goal this executor can run — with no human reply
   at all.**  Armed on the order-N winner, `ax_dispatch`
   mints **nothing**, because its guard requires the armed agid to equal
   `arc_sel_agid`.  So the magnitude rung's whole repricing is currently
   invisible to the hands, and the route by which this loop could close with
   nobody in it is sitting one stamp away.  **Reported, not wired**: which
   collapse the hands follow is a design decision above this rung's scope, and
   A10 named `ag_select`'s winner as the thing to dispatch.
10. **A PRE-EXISTING GATE FAILURE, VERIFIED INDEPENDENT OF THIS RUNG.**
   `test_arc_magnitude_migrated::test_mg5_JOB0_qd_decompose_is_RESIDENT_AND_DEAD_and_the_probe_can_tell`
   asserts `git grep -l has_subgoal_spec == ["seeds/question_driving.json"]`.
   It now returns five paths, four of them **the magnitude rung's own
   artifacts** — which mention the token and were *untracked* in that rung's
   worktree when it measured 43/43.  A self-referential grep that went stale the
   moment its own results were committed.  None of this rung's own files
   contains the token; `git grep -l has_subgoal_spec HEAD` returns the same five.
   Recorded, not absorbed and not fixed.

---

## 9. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The executor's reach is ONE NODE.**  One `ExecClass`, one executable goal,
   one runner.  The mechanism is general — the route is a cue table and the
   re-ingest reads `goal_residual_ingest.SPEC` by rid — but *"the executor
   dispatches the collapse's winner"* is currently demonstrated by one goal.
   A second re-measurable residual would be the honest test of the route's
   dedup, exactly as a second `reach_class_counts` payload would be for
   `ag_mint_blocker`.  **The mechanism is measured; its reach is one node.**
2. **The provenance re-anchor is the rung's one modelling choice** (§2.2).  It
   is defended by the shipped condition idiom and by the re-failure control, but
   *"a re-measurement re-anchors its residual's conditions to the world it was
   measured under"* is a **claim about what a `ResidualCondition` means**, not a
   measurement.  A reader who thinks a condition asserts *truth* rather than
   *provenance* will read this rung as making its own condition hold.  I do not,
   and §2.2 says why — but this is the line to attack.
3. **The two-tick agreement is SUFFICIENT IN THE SCENES MEASURED, not a proof of
   quiescence.**  A second fixpoint could in principle pass transiently through
   the armed (agid, value) pair without having settled there.  Both components
   must match, which makes it unlikely, and every scene here is gated — but the
   guard is an agreement test, not a fixpoint-completion predicate, and this
   engine offers no way to express the latter.
4. **Every scene in §2–§6 runs WITHOUT `seeds/arc_magnitude.json`.**  The loop
   was measured on the order-1 collapse alone, because that is the stamp A10
   named.  §8.9 measures what happens when the magnitude layer is present —
   the two collapses disagree and the hands follow order-1 — but **the loop
   itself has never been run under order-N**, and under it the very first boot
   would have selected an executable goal with no human in the scene.  That is
   the single most informative thing left undone here.
5. **The re-arm deadlock** (§5) and **the missing inexecutability term** (§6.3)
   are both live holes in the loop, deliberately unfilled.
6. **The seed is `self_load_only`, so nothing in the tree loads it yet.**  Every
   result here is on a boot that asks for it explicitly.  Its tree-wide
   behaviour is **unmeasured**; activation is one key and a paired sweep — and
   an executor that dispatches jobs is the last thing that should arrive in
   every agent by a glob.
7. **The runner is a subprocess chain over three scripts that mutate the tree
   and restore it.**  Byte-identity is asserted after each run, but the window
   between `apply` and `revert` is real: a concurrent reader of
   `seeds/program_synthesis.json` during those ~48 seconds sees the patched
   seed.  Single-process, single-worktree, this is safe; it is not safe in
   general and nothing enforces that.
8. **`ax_close` proves the goal retired, not that the measurement was
   *correct*.**  A runner that produced a garbage artifact whose paths still
   resolve would close the order just the same.  The residual's numbers moving
   (4/15 → 0/1) is evidence the artifact is real; nothing checks that it is
   right.
9. **MG4 is now unblocked and still not built** — the status lifecycle exists,
   so the parent can leave the pool.  §10.

---

## 10. WHAT MADE ME WANT TO BUILD MG4 — reported, not taken

Three pulls, and the first is new information rather than a preference:

- **The blocker MG4 named is gone, and I can see the exact shape of what
  replaces it.**  `ax_retired_epoch` + `ax_rearm` are a general status
  lifecycle: a goal reaches terminal, is stamped with an epoch, and re-enters
  the pool only on a conjunction.  A decomposed parent needs precisely that,
  with `"decomposed"` in place of `"retired"` — and `ag_select`'s pool filter
  already excludes on status, so it is one more terminal token and one more
  guard clause.  The magnitude rung declined the interim `"decomposed"` status
  because it required editing `seeds/arc_goals.json`; **it no longer does**, an
  additive rule in this seed can write it.
- **`decompose_required` is still a flag nothing consumes**, and it is now the
  only thing between the tier ladder and a goal.  The ladder is already graph
  data, already keyed by a measured population join, already carrying its own
  survival factors.
- **The registered bar is arithmetic I could check today.**
  `Sum(children.headroom_n × children.tier_survival) == parent.orderN_headroom_n`
  is a `Count`-and-`Times` over neighbours; both sides already exist on the
  shipped graph.

**I did not build any of it.**  A10 scoped this rung to the executor and said
plainly that MG4 is unblocked by it, not included in it — and the honest reason
to stop is §9.1: this rung's own mechanism has a reach of one node, and adding
a second mechanism on top of a one-node demonstration is how a measured result
becomes a story.

---

## 11. FILES

| file | what |
|---|---|
| `seeds/arc_executor.json` | the seed — 2 nodes, 1 edge, 3 productions, **4 rules**.  `self_load_only`.  Emitted, not hand-written |
| `tools/build_arc_executor_seed.py` | the emitter; **imports** the Term idioms (`MEASURE_EPOCH`, `ONE_OF`, `HUB`, the null-coalescing `ITE`) from `tools/build_arc_goals_seed.py`, so a change there makes this seed go out of date loudly |
| `domains/arc_executor.py` | the world adapter — self-load, the tick-boundary arm, the run, the provenance re-ingest, the epoch bump.  Mechanical I/O only; passes the module-specific source audit |
| `scripts/arc6_remeasure_row_verdict.py` | the ONE runner: re-runs the three existing scripts in sequence, restores every frozen file in a `finally` |
| `tests/test_arc_executor_migrated.py` | the gate — **35/35**, including one ~100 s **live** re-measurement every downstream gate reads |
| `scripts/arc6_executor_measure.py` | the measurement runner |
| `results/arc6_executor.json` | the artifact, engine-stamped, carrying the full EX5 trace |
