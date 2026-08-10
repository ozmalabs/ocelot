# ARC 6 — A11: WIRING THE HANDS TO THE ORDER-N COLLAPSE

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A11** (`WH1`–`WH4`),
registered **before** this change.
**Base commit:** `26ca9ffaa8` (detached worktree `/home/matt/arc6-wire-hands`).
**Engine:** `953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85`
— **built fresh in this worktree**, because the committed `_native.abi3.so`
**does not import on this machine** and the crate **does not compile on the
available compiler**.  That is a condition on every number below and §6 states
it in full.  `_native.__file__` resolves from inside this worktree
(`/home/matt/arc6-wire-hands/…/runners/dsl/python/substrate_rs/_native.abi3.so`),
not the canonical tree's; the canonical tree's binary is byte-unchanged.
Archived out of tree at `~/ozma-engine-archive/_native.abi3.so.953b8e3f` per
A1.1.  Behaviourally probed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**, asserted inside the gate's own boot.
**Artifact:** `results/arc6_wire_hands.json` (engine stamped; 356.3 s, four WH1
arms + two WH2 loops + five suites, one real 138.6 s re-measurement inside it).
**Seed:** `seeds/arc_executor.json` **v1.1.0**, sha256
`4d85c1a3f31adb069a66dc1f43eafa82d39498f91ebb8e0bb53dccd38f62a8ba`, emitted by
`tools/build_arc_executor_seed.py` and gated byte-identical against it.
**Gate:** `tests/test_arc_executor_migrated.py` — **40 collected, 39 green**,
the one red **pre-existing and environment-conditional**, enumerated by node id
in §4.

**SCOPE: WH1, WH2, WH3.  WH4 IS DESIGNED, NOT BUILT** (§5) — no rule, no seed
edit, no adapter line.  A11 said "state the trade-off and pick — but do not
implement it in this rung", and AG-5 §10 is the precedent for actually stopping.

**NO ENGINE SOURCE CHANGE.**  Zero `.rs` edited.  A new *binary* was
nevertheless required (§6), so A1.2's isolation requirement is honoured the
strongest way available: **both arms of the headline comparison run in ONE
process on ONE binary**, and the pre-change arm is `HEAD`'s own
`seeds/arc_executor.json` loaded out of git into a second substrate.  The arms
differ by the seed and by nothing else.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **WH1 — the stamp swap is behaviourally visible** | **PASS** | in one scene with **zero human replies**, the order-1 collapse names the 42-task blocker (10.0) and the executor mints an `ExecOrder` for the **order-N** winner instead (`…row_verdict_seed_only`, 7.7), stamped `selected_by: order_n_mg_select` and carrying **both** collapses' stamps.  `HEAD`'s seed, same process, same engine, same scene: **zero orders**.  §2 |
| **WH2 — the loop acts WITHOUT being asked** | **PASS** | end to end, `human_replies_sent: 0`: the re-measurement **ran live** (138.6 s), the condition refreshed, the residual un-staled, the goal **retired**, pool **8 → 7**, epoch **0 → 1**, order **closed**.  Then it stopped.  `HEAD`'s wiring under the same silence: **0 executions, 0 iterations of work**.  §3 |
| **WH3 — no regression** | **PASS** | the failing-node-id **list** is identical before and after — `{test_ex1_the_frozen_artifacts_are_STILL_byte_identical, test_gr4_the_live_mbpp_pass_ids_are_unchanged}`, both pre-existing and environment-conditional.  48 pass ids and 95 accepted ids **byte-identical**, `lost: []`.  Source audit passes.  `ag_ask` untouched.  §4 |
| **WH4 — the impotence term: DESIGNED, NOT BUILT** | **PASS (as scoped)** | three candidates weighed, **(c) terminate honestly** picked, with the deciding argument stated as an asymmetry rather than a preference: it is the only one that produces the measurement that would justify the other two.  Nothing implemented.  §5 |

**The one thing worth reading if you read nothing else.**  AG-5 ended holding a
pool it could act on only after a human replied, and its §8.9 recorded that
*"the route by which this loop could close with nobody in it is sitting one
stamp away."*  It was.  Moving one stamp — with **no** new mechanism, no new
rule, and a strictly **dumber** adapter — closed it: the loop now boots, picks
the one goal it can run, runs a real 138-second measurement, retires the goal,
and stops, **and nobody is in it**.

---

## 1. WHAT CHANGED

Four files edited (one of them a regenerated artifact of another), three added.
**No new rule, no new node type, no engine source, no new mechanism.**

```
tools/build_arc_executor_seed.py   the emitter.  SEL_AGID / SEL_VALUE /
                                   ARMED_AGID / ARMED_VALUE / COLLAPSE_NAME,
                                   and `_armed` rewritten to read them
seeds/arc_executor.json            REGENERATED from that emitter (never hand
                                   edited).  v1.0.0 -> v1.1.0
domains/arc_executor.py            `arm` copies a CONSTANT TABLE of four stamps
                                   instead of two.  Strictly less logic.
tests/test_arc_executor_migrated.py  the pre-A11 pin INVERTED, + 6 new gates
scripts/arc6_wire_hands_measure.py   NEW — the measurement runner
results/arc6_wire_hands.json         NEW — the artifact
PROGRAM_SYNTHESIS_ARC6_PREREG.md     amendment A12 appended
PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md NEW — this file
```

### 1.1 The decision is a Term, and the adapter got dumber

The whole change is one `IfThenElse` in `ax_dispatch`'s `where`:

```
SEL_AGID   = ITE(Eq(agenda.mg_sel_agid, null), agenda.arc_sel_agid,
                                               agenda.mg_sel_agid)
ARMED_AGID = ITE(Eq(agenda.mg_sel_agid, null), agenda.arc_exec_armed_agid,
                                               agenda.arc_exec_armed_mg_agid)
```

…and the same pair for the values.  `_armed`'s *shape* is untouched — it is
still the two-tick agreement AG-5 built, still `armed == goal.agid` **and**
`armed == selection` **and** `armed_value == selection_value` **and**
`armed != null`.  Only the pair of stamps it reads moved, and **both sides of
every comparison move together**, so the guard can never straddle two rankings
(gated structurally: every stamp-selecting `IfThenElse` in the shipped `where`
is asserted to pair a stamp with its own twin under the *same* absence test).

The adapter's half is the tick-boundary carry, and it is now a module-level
constant:

```python
ARM_CARRY = (("arc_sel_agid",  "arc_exec_armed_agid"),
             ("arc_sel_value", "arc_exec_armed_value"),
             ("mg_sel_agid",   "arc_exec_armed_mg_agid"),
             ("mg_sel_value",  "arc_exec_armed_mg_value"))
```

`arm` iterates it and **never inspects a value**.  It used to copy one pair; it
now copies the table; it still cannot tell which one the rule will read.  A
missing stamp copies as `None` and the rule's own non-null guard refuses it —
the adapter does not test for absence, it carries what is there.  This is the
point of the split and it is gated (`test_wh1_the_adapter_carry_is_a_CONSTANT_
TABLE_not_a_choice`).

### 1.2 A SOFT dependency on `arc_magnitude`, stated as a decision

`seeds/arc_magnitude.json` is `self_load_only` and is **deliberately not** in
`arc_executor`'s `depends_on`.  Making it hard would (i) change what every
EX1–EX6 scene boots, and (ii) put an order-N collapse into every graph that
merely wants hands.  The soft form leaves those scenes byte-identical and lets
a graph that holds the better collapse use it.

**The cost is that the fallback is silent** — a graph on which `mg_select` stops
firing reverts to the collapse the magnitude rung measured as mispriced, and
nothing would say so.  Mitigated, not prevented: the `ExecOrder` now records
`selected_by`, `selected_value`, `order1_sel_agid` and `orderN_sel_agid`, so
which collapse the hands followed is a **countable graph fact** and "the
executor acted on a goal order-1 did not choose" is readable off the order
itself rather than inferred from prose.  §8.1 keeps this as a live uncertainty.

---

## 2. WH1 — THE STAMP SWAP, IN FOUR ARMS, ONE PROCESS, ONE BINARY

`results/arc6_wire_hands.json → WH1_the_stamp_swap_is_behaviourally_visible`.
The scene is **the shipped boot**.  Nobody replies to anything in any arm
(`no_human_reply_in_any_arm: true`).

| arm | executor seed | tier ladder | `arc_sel_agid` (order-1) | `mg_sel_agid` (order-N) | orders minted |
|---|---|---|---|---|---|
| **A** | worktree **v1.1.0** | installed | `…missing_structural_primitive` **10.0** | `…row_verdict_seed_only` **7.7** | **1 — `…row_verdict_seed_only`** |
| **B — CONTROL** | **`HEAD` v1.0.0** | installed | `…missing_structural_primitive` 10.0 | `…row_verdict_seed_only` 7.7 | **0** |
| **C — CONTROL** | worktree v1.1.0 | **withheld** | `…missing_structural_primitive` 10.0 | `…missing_structural_primitive` 10.0 | **0** |
| **D — CONTROL** | worktree v1.1.0 | n/a — **`arc_magnitude` absent** | `…missing_structural_primitive` 10.0 | **absent** | **0** |

The order arm A minted, read off the graph:

```
agid            arc.remeasure.arc6.verdict.row_verdict_seed_only
runner          arc6_remeasure_row_verdict
selected_by     order_n_mg_select
selected_value  7.699999999999999
order1_sel_agid arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive
orderN_sel_agid arc.remeasure.arc6.verdict.row_verdict_seed_only
```

**`agid != order1_sel_agid` on the order itself.**  That is WH1's bar, as a
graph fact.

### 2.1 The mechanism, re-measured rather than re-quoted

Per-goal `orderN_headroom_n` on the shipped boot, this binary:

| goal | `headroom_n` (order-1) | `orderN_headroom_n`, ladder **installed** | ladder **withheld** |
|---|---|---|---|
| `arc.supply.…missing_structural_primitive` | 42 | **13.637248** | 42 |
| `arc.remeasure.…row_verdict_seed_only` | 11.0 | **11.0** | 11.0 |
| `arc.supply.…budget` | 7 | 7 | 7 |
| `arc.supply.…missing_dimension` | 4 | 4 | 4 |
| the four `arc6.claim.*` | 1.0 | 1.0 | 1.0 |

MG2's attrition ladder doing exactly what it was built to do: 42 tasks of paper
inventory discount to **13.64**, while the re-measurement goal's headroom is
undiscounted because completing it unlocks nothing.  The magnitude rung's
`42 → 13.64` reproduces to six figures on a binary it never ran on.

### 2.2 Why each control is there, and what each rules out

- **B** rules out *"the difference is the day, the tree, or the binary."*  It is
  the same process, the same engine, the same scene, the same fixture — and
  `HEAD`'s own emitted seed, read out of git.  It mints nothing.  **The
  difference is the seed.**
  Sharper than that, and deliberately so: **the adapter is COMMON to both
  arms.**  Arm B runs `HEAD`'s `ax_dispatch` against *this* rung's `arm`, which
  writes the two order-1 stamps exactly as it always did and two extra attrs the
  old rule does not read.  So B−A isolates **the rule**, not the adapter — which
  is the direction that matters, since the whole claim of this rung is that the
  decision moved into the rule and the adapter got dumber.
- **C** rules out *"loading `arc_magnitude` is what did it."*  With the seed
  loaded and the **measured ladder withheld**, the two collapses **agree** on
  the blocker and nothing dispatches.  The divergence is the **ladder's**, which
  is precisely where AG-5 §8.9 located it, measured now in both positions on a
  second binary.
- **D** rules out *"the fallback is decorative."*  With `arc_magnitude` absent,
  `mg_sel_agid` is null, `SEL_AGID` takes the order-1 branch, and the shipped
  boot behaves exactly as it did before A11 — armed on the settled unroutable
  winner, nothing mints.

All three non-A arms refuse for the **same structural reason**: the winner they
hold has no `ExecClass`, so the route `Argmin` is empty.  The refusal is not a
check that could be deleted.

**Twin-run determinism:** `wh1_stamp_swap()` run twice in one process is
**byte-identical** (verdicts, arms, stamps, values).

---

## 3. WH2 — THE LOOP ACTS WITHOUT BEING ASKED

AG-5's EX5 loop with **one** thing changed: nobody answers anything.  AG-5's own
arm 1 replied to every open question each iteration, and its §8.3 recorded that
*the reply is what let the loop act at all* — an unconditioned answer penalises
the region it is about, which is what dropped the blocker below the
re-measurement goal.  Here `answer_questions=False` and `human_replies_sent`
is **0**.

### 3.1 The trace, order-N wired

```
iter 0   epoch 0   pool 8   open questions 1  (ag_ask fired; NOBODY ANSWERED)
         arc_sel  supply.missing_structural_primitive   10.0   margin  2.30
         mg_sel   remeasure.row_verdict                  7.7   margin 26.06
         armed -> ax_dispatch mints ExecOrder (selected_by order_n_mg_select)
         -> THE MEASUREMENT RUNS LIVE, 138.62 s, on engine 953b8e3fa647
            artifact results/arc6_verdict_pricing_remeasure_wh2n_i0_e0.json
            sha 787e85d379a6aa60704d3d420a7598658cd0fa2f9e0bc5643175678097dde16d
            protected files restored byte-identical: True
         -> conditions re-anchored -> residual un-stales (1.0 -> 0.0)
         -> goal RETIRED, retired_because source_residual_no_longer_stale
         -> pool 8 -> 7          -> epoch 0 -> 1   -> order CLOSED
                                    (outcome goal_retired_source_residual_
                                     no_longer_stale)

iter 1   epoch 1   pool 7   open questions 0  (the unanswered question LAPSED
                                               at the epoch bump)
         arc_sel  supply.missing_structural_primitive    10.0     margin 35.00
         mg_sel   supply.missing_structural_primitive   -18.36    margin  6.64
         kind `supply_blocker` has no ExecClass -> NO ORDER
         STOP: no_executable_goal_was_selected
```

Control, `HEAD`'s seed, identical silence: **1 iteration, 0 executions**, stop
`no_executable_goal_was_selected`.  Under the old wiring an unanswered agenda
does nothing at all.

### 3.2 The reading, including the parts A11 did not ask for

**The bar is met and it is not close.**  A11 registered *"with order-N wired,
the loop should reach the executable goal without needing the ask.  Report what
actually happens — including if it does not."*  It does, on the **first
iteration of the first boot**, with a real measurement rather than a fixture.

Three things fell out that were not registered, reported because they are the
kind of thing that gets quietly enjoyed otherwise:

1. **The ask still fires; it is simply irrelevant now.**  `ag_ask` minted one
   question at iteration 0 (it reads `arc_sel_*`, where the margin is 2.30 —
   under threshold).  Nobody answered it, and it **lapsed** at the epoch the
   executor produced — read off the graph, the question's `status` goes
   `"open"` → `"unanswered_lapsed"` between iterations 0 and 1.  So the loop did
   not merely proceed without a reply; it proceeded past a question it had
   asked, and the question expired through `ag_question_retire` — the Angluin
   mechanism, ticking, with no human.
2. **The pool arithmetic is clean for the first time.**  AG-5 §3 could only show
   `8 → 7` under a *conditioned* reply, because an unconditioned one mints a
   fresh re-measurement goal from the expired testimony and the net count hides
   the retirement (its §8.4).  With **no reply at all** there is no testimony,
   so the retirement is visible in the net count directly: `8 → 7`,
   `left_the_pool: [arc.remeasure.…row_verdict_seed_only]`,
   `joined_the_pool: []`.  The arm AG-5 needed a fixture to isolate is now the
   default.
3. **Order-N and order-1 disagree about the endgame too, and order-N is the
   more honest of the two.**  At iteration 1 order-1 prices the remaining
   blocker at **+10.0** and order-N at **−18.36**.  Order-1 still says the
   agenda is worth 10 tasks; order-N says the whole remaining pool is negative.
   Neither can act on it.  This is the impotence case (§5), reached under the
   new wiring at margins **35.0** (order-1) and **6.64** (order-N) — **not a
   tie under either collapse**, so `ag_ask` is silent and the loop stops without
   saying anything, exactly as A11 describes.

**What did NOT change: it still stops after one execution.**  AG-5's EX5
reading — *"it did not converge on cheap re-measurement"* — survives the swap.
The anti-oscillation latch and the retire rule are what stop it, both measured
firing in AG-5 §5 and unmodified here.  The swap changed **who starts the
loop**, not **how it ends**.

---

## 4. WH3 — NO REGRESSION.  A LIST OF NODE IDS, NEVER A COUNT.

CLAUDE.md's standing rule is that a baseline must be an enumerated list, because
*"a count can be held; a list has to be read."*  Both arms below ran on the same
binary in this worktree, the **before** arm on the unmodified tree.

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 34 passed, **1 failed** (35 collected) | **39 passed, 1 failed** (40 collected) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | **37 / 37** | **37 / 37** | — |
| `test_goal_residual_migrated` | 29 passed, **1 failed**, 1 skipped | 29 passed, **1 failed**, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | **35 / 35** | **35 / 35** | — |
| `test_arc_magnitude_migrated` | **43 / 43** | **43 / 43** | — |

The executor suite's collected count rises **35 → 40**: the pre-A11 pin was
**inverted** (−1, §7.6) and **six** gates added (+6, listed in §9).  The one
skip is also the same id in both arms —
`test_gr4_the_synthesis_seed_diff_is_confined_to_two_rules`, which skips with
*"nothing to diff against"* because its `PRE_RUNG_REV` does not resolve in this
single-commit repository.  Same condition class as §4.1's first red.

### 4.1 The two reds, enumerated with their conditions, neither caused here

**`test_ex1_the_frozen_artifacts_are_STILL_byte_identical`.**  It asserts
`git show HEAD:results/arc6_verdict_before.json` is non-empty.  In this repo
snapshot `results/` is **gitignored and untracked**, so the command returns the
empty string and the assert fires on `assert head, rel`.  **Condition:** any
checkout where `results/` is not tracked.  The runner's own claim —
`protected_files_restored_byte_identical is True` — is asserted one line earlier
and **passes** in every run here, so the property the gate is *about* holds;
what fails is its chosen witness.  Red before, red after, same id.

**`test_gr4_the_live_mbpp_pass_ids_are_unchanged`.**  It asserts the engine's
short sha is in a three-entry **allowlist** (`8311d4356082`, `4a9a492936bb`,
`39c4dbb7f2ed`).  This rung's engine is `953b8e3fa647` and had to be (§6).
**Condition:** any freshly built binary.  Red before, red after, same id.

**And the id lists it measures are byte-identical, which is the substance of the
bar.**  The gate writes `results/arc6_verdict_gr4_gate.json` live on every run;
the before and after documents compare exactly:

```
pass_ids     n=48   identical: True   lost: []   gained: []
[16, 20, 58, 59, 69, 82, 84, 85, 89, 90, 120, 127, 132, 135, 138, 139, 142,
 145, 161, 227, 233, 234, 249, 257, 266, 272, 276, 278, 281, 290, 309, 312,
 393, 394, 404, 406, 410, 413, 418, 433, 436, 443, 450, 457, 458, 460, 472, 477]

accepted_ids n=95   identical: True   lost: []   gained: []
```

**The allowlist was NOT widened.**  Adding `953b8e3fa647` to it is the procedure
that gate's own comment describes ("it was ADDED (not substituted) after
measuring that the pass ids below are byte-identical"), the measurement that
would justify it is above, and it is still a one-line edit to a downstream gate
this rung was not scoped to touch.  Named as the follow-up, deliberately not
taken.

### 4.2 `test_arc_magnitude_migrated` is 43/43 here and AG-5 recorded 42/43 — and that is a finding, not a win

AG-5 §8.10 recorded one pre-existing failure,
`test_mg5_JOB0_qd_decompose_is_RESIDENT_AND_DEAD_and_the_probe_can_tell`,
which asserts `git grep -l has_subgoal_spec == ["seeds/question_driving.json"]`
and returned five paths there because four of the magnitude rung's own artifacts
mention the token **and had become tracked**.

It is **green here** — because in this repo snapshot those artifacts live under
an untracked `results/`, so `git grep` cannot see them.  **Same test, same
assertion, opposite verdicts, decided entirely by which files happen to be
tracked.**  That is the retraction shape CLAUDE.md names, one level down inside
a gate, and the honest reading is *not* "the pre-existing failure was fixed" —
it is that **this assertion measures the tracking state of the repository, not
the property it names**.  Recorded, not absorbed, not fixed.

### 4.3 `ag_ask` was not touched, and is not made worse

A11's WH3 requires that `ag_ask`'s unfixed transient-Argmax exposure *"must not
be made worse."*  `seeds/arc_goals.json` is byte-identical to `HEAD`
(asserted by `test_ex6_the_seeds_below_this_rung_are_UNTOUCHED`, green), so
`ag_ask` is unchanged in every particular: it still reads `arc_sel_agid` /
`arc_sel_margin` inside the same fixpoint that writes them, and it still has no
two-tick agreement.  **A new consequence of the swap is recorded in §8.3
instead: the ask and the hands now read different collapses**, which is a
divergence in what they are *about*, not a change to `ag_ask`'s exposure.

### 4.4 The source audit still passes

`test_ex6_the_adapter_CANNOT_contain_a_hidden_decision` — green.  The adapter
still never imports `substrate_rs`, never calls `.evaluate(`, never calls
`run_rules`, and its substrate contact is still only
`add_node` / `node` / `nodes` / `set_attr` / `add_edge_unchecked` /
`load_seed_manifest`.  The change moved logic **out** of Python, not in.

---

## 5. WH4 — THE IMPOTENCE TERM: DESIGNED, NOT BUILT

**Nothing in this section is implemented.  No rule, no node type, no seed edit,
no adapter line.**  AG-5 §10 declined MG4 for the reason that applies here
verbatim: *"adding a second mechanism on top of a one-node demonstration is how
a measured result becomes a story."*  This rung's own mechanism still has a
reach of one node.

### 5.1 The situation, stated precisely

`ag_ask` fires on a **tie** — `margin < threshold` under mutual ignorance.  The
case it cannot see is **impotence**: a non-empty pool in which *nothing is
routable*, and no tie anywhere.  WH2 §3.1 iteration 1 is that case under the new
wiring — margins 35.0 (order-1) and 6.64 (order-N), pool of 7, zero
`ExecClass` matches, and the loop stops **silently**.

**The first design point, and it is a correction to how the case is currently
detected.**  The loop's stop string, `no_executable_goal_was_selected`, is
computed **in a measurement script** (`_why_no_dispatch`) from the **winner
alone**.  That is the wrong quantifier: a pool holding one routable goal ranked
second is *not* impotent, and the winner-only reading cannot tell the two apart.
Any real term must quantify over the pool —
`Not Exists(pool, g, routable(g))` — which is expressible today with no new
mechanism, because `_routable` is already a Term and `Exists(POOL_AS(…))` is
already how both collapses guard themselves.  **The term is cheap.  The
question is what it should do.**

### 5.2 The three candidates A11 names, weighed

**(a) Ask a DIFFERENT question from the tie-ask.**  Mint an
`ArcQuestion{kind:"capability_gap"}` naming the winner's kind and the
`ExecClass` set actually held: *"I hold 7 goals and can run none of them; the
nearest wants a `supply_blocker` runner and I have only `re_measure`."*

- **For:** it reuses the ask/reply/testimony/lapse machinery verbatim — one
  rule, zero new mechanism — and it is honest about who can fix it, since only a
  human can supply a runner.
- **Against, and it is measured rather than hypothetical:** AG-5 §8.3
  established that *asking and getting **any** answer penalises the region it is
  about, by weight, regardless of content* — the content is never read.  An
  impotence ask about the top goal therefore charges the top goal, reorders the
  pool, and can promote a **different** unroutable goal to winner, which
  re-triggers the ask.  That is a repricing loop with no fixed point, and in a
  trace it is indistinguishable from progress.  It also borrows a semantics that
  is simply wrong here: a human's answer cannot *make* a goal routable.

**(b) Mint a goal to acquire the missing capability.**  Mint
`ArcGoal{kind:"acquire_capability", missing_exec_class: <kind>}` behind a
mint-once edge latch (the `remeasure_goal` precedent).

- **For:** it is the only candidate that puts the gap **on the agenda**, where
  the whole apparatus already applies — pool membership, value, residual
  penalty, retirement, and eventually decomposition.  It is also self-similar:
  this tree already turns *"a measurement is stale"* into a goal, and *"a hand
  is missing"* is the same move one level up.  It is what a person would do.
- **Against, and this is decisive today:** the minted goal is **itself
  unroutable**, because acquiring a capability means writing a runner and
  editing a seed, and nothing in this tree can do either.  So each impotence
  event grows the pool by one permanently-unroutable member; the impotence term
  then fires on the enlarged pool.  Latched, it still makes the agenda
  monotonically *less* actionable while the trace reads as activity.  It
  converts a silent stop into a growing agenda, which is worse than a silent
  stop because it looks like progress.

**(c) Terminate honestly.**  A rule writes the fact —
`AgendaVerdict{kind:"impotent", epoch, pool_n, pool_agids, exec_classes_held,
nearest_unroutable_kind}` — keyed once per (pool signature, epoch), lapsing
through the existing condition machinery when the world moves.

- **For:** it says the true thing and adds **no feedback path** into the
  collapse.  It converts a stop string invented by a *measurement script* into a
  **graph fact the agent holds**, which is exactly this project's migration
  direction.  And it is countable, so *"how often does this loop end unable to
  act, and on which missing `ExecClass`"* becomes measurable.
- **Against:** announcing is not acting.  A planning layer that only ever
  reports its impotence has gained no capability.  It also risks the flooding
  pattern CLAUDE.md warns about — mitigated by keying on the pool signature so
  it mints once per *distinct* impotence, not once per tick.

### 5.3 The pick, and why — an asymmetry, not a preference

**PICK (c) — terminate honestly, as graph data.  (a) and (b) deferred behind
the count (c) produces.**

The deciding argument is not that (c) is nicest.  It is that **(c) is the only
one of the three that produces the measurement that would justify choosing
between (a) and (b)**, and neither is justified by any measurement today.
Nobody has counted how often this loop ends impotent, nor whether the impotence
concentrates on **one** missing `ExecClass` — which favours (b), a single
capability to supply — or spreads across **many** — which favours (a), a
question about priorities.  Building either now is choosing without the
measurement, which is the mistake this arc's ceiling-probe discipline exists to
prevent, and which A2 recorded the cost of.

The risk register is also asymmetric.  (a)'s registered risk is a repricing loop
with no fixed point, driven by a mechanism AG-5 measured as *the loop's only
path to acting* — so it is dangerous in proportion to how well the rest works.
(b)'s registered risk is an agenda that grows monotonically less actionable
while reading as activity.  (c)'s single registered risk — that announcing is
mistaken for acting — is the only one of the three that is **cheap to retract**,
and the only one that does not touch the collapse.

Finally, (c) **composes with** the other two rather than excluding them: both
(a) and (b) would want to read an impotence fact rather than re-derive the
condition, so building (c) first is not a detour on the way to either.

**Registered for whoever builds it:** the term must quantify over the **pool**,
not the winner (§5.1); the fact must be keyed on the pool signature, not on the
tick; and it must lapse through `gr_condition_lapse` like every other conditioned
fact, so an agenda that becomes actionable again does not carry a stale verdict.

---

## 6. THE ENGINE — why this rung is not on `8311d4356082`, stated as a condition

Every arc-6 rung before this one measured on `8311d4356082…` (or `4a9a492936bb`
/ `39c4dbb7f2ed`).  This one could not, and the reason is environmental, not
methodological:

1. **The committed `_native.abi3.so` does not import on this machine.**
   `ImportError: /lib/x86_64-linux-gnu/libm.so.6: version 'GLIBC_2.43' not
   found` — the binary in the tree was linked against a newer glibc than this
   box's (Ubuntu 2.39).  Nothing runs at all without a rebuild.
2. **The crate does not compile on the available compiler.**  The system
   toolchain is `rustc 1.87.0` (Homebrew); `runners/dsl/src/l1_hot_paths.rs` and
   `l3_lqr.rs` use AVX-512 intrinsics and `#[target_feature(enable="avx512f")]`,
   which were unstable then — **29 `E0658` errors**.  Resolved by installing
   `rustup` stable (`rustc 1.97.1`) and rebuilding.  `runners/dsl/.cargo/config.toml`'s
   `jobs = 4` cap was respected; build time 1 m 34 s.

**What that costs, and what it does not.**  It costs the ability to say "same
binary as AG-5."  It does **not** cost the isolation A1.2 exists to protect,
because **this rung's intervention comparison never spans two binaries**: arms A
and B of WH1, and the WH2 loop and its control, all run in one process on
`953b8e3fa647`, and the pre-change arm is `HEAD`'s own seed loaded from git.
`B − A` in A1.2's sense is structurally zero here.

**Evidence the binary is behaviourally the one the arc has been using**, on the
load-bearing measurements rather than by assertion:

| | AG-5 / prior rungs (`8311d4356082`) | this rung (`953b8e3fa647`) |
|---|---|---|
| live MBPP pass ids | 48, listed | **48, byte-identical list** |
| accepted ids | 95 | **95, byte-identical list** |
| list vs tuple distinct | yes | **yes** (probed before every measurement) |
| re-measurement: newly accepted | `[222]` | **`[222]`** |
| accepts requiring the list/tuple collapse | `[]` | **`[]`** |
| witness verdict on 222 | coincidental | **coincidental** |
| `bar_2_zero_false_accepts…` / GO-NO-GO | PASS / NO-GO | **PASS / NO-GO** |
| blocker `orderN_headroom_n` with the ladder | 13.64 | **13.637248** |

The one place the difference is visible is `test_gr4`'s **allowlist**, which is
a provenance guard doing its job (§4.1).  The binary is archived at
`~/ozma-engine-archive/_native.abi3.so.953b8e3f`; the canonical tree's binary is
byte-unchanged (`62272924d26f…`), verified after the build.

---

## 7. EVERYTHING THAT BROKE

Recorded because the process is the result.

1. **THE TREE DOES NOT BUILD OR RUN OUT OF THE BOX ON THIS MACHINE** — §6.  Two
   independent failures, glibc and rustc, either of which alone stops every
   measurement in the repository.  Worth stating plainly because a rung that
   "just reproduced the numbers" would have hidden both.
2. **A COUNT-SHAPED ASSERTION IN MY OWN NEW GATE, CAUGHT BY IT FAILING.**  The
   first draft of `test_wh1_the_adapter_carry_is_a_CONSTANT_TABLE_not_a_choice`
   asserted `where.count('"mg_sel_agid"') == where.count('"arc_sel_agid"')` as a
   proxy for "both sides of every comparison move together."  It failed
   **7 == 1** — because the absence test `Eq(mg_sel_agid, null)` is repeated once
   per `IfThenElse`, so the token count says nothing about the pairing.
   Replaced by a **structural walk** over the shipped term tree that asserts each
   stamp-selecting `IfThenElse` pairs a stamp with its own twin under the same
   condition.  Recorded because it is CLAUDE.md's *"a count can be held; a list
   has to be read"* one level down, inside a term tree, in a gate written by the
   person quoting the rule.
3. **`test_arc_magnitude_migrated`'s known failure VANISHED, and that is worse
   than it failing** — §4.2.  Its verdict is decided by which files are tracked,
   not by the property it names.
4. **`results/` IS A SYMLINK INTO THE CANONICAL TREE IN THIS WORKTREE.**
   `data/` (39 G) and `results/` (21 G) are gitignored and do not fit on the
   40 G free, so both are symlinked.  The live re-measurement therefore writes
   into the **canonical** `results/`: it creates
   `arc6_verdict_pricing_remeasure_*.json`, rewrites `arc6_verdict_gr4_gate.json`
   (by design — that gate rewrites it every run), and **restores**
   `arc6_verdict_before.json`, `arc6_verdict_after.json` and
   `arc6_verdict_pricing.json` byte-identically in a `finally`, asserted every
   run.  This is AG-5's uncertainty #7 realised: it is safe single-process and
   nothing enforces that.  No tracked file in the canonical tree was modified.
5. **I TRIPPED AG-5's UNCERTAINTY #7 MYSELF, AFTER WRITING IT UP AS A RISK.**
   AG-5 §9.7 records that the runner *"is a subprocess chain over three scripts
   that mutate the tree and restore it"* and that *"the window between `apply`
   and `revert` is real."*  After the final measurement had completed and the
   tree was verified clean, I ran one more confirmation `pytest` under a
   **2-minute timeout**.  The suite's session-scoped `live_run` fixture starts
   the ~140 s re-measurement regardless of `-k`, so the timeout **killed the
   runner inside its own `try`** — the `finally` never ran, and it left:
   - `seeds/program_synthesis.json` in the **patched** state (`5aef8fdb…`
     instead of `HEAD`'s `4e866340…`), and
   - `results/arc6_verdict_before.json` **overwritten** by the killed run's
     `before` arm (`b8c76313…` instead of `ed90bf28…`) — in the **canonical**
     `results/`, via the symlink of §7.4.

   Both restored and verified by sha: the tracked seed from `git checkout`
   (git is the authority for a tracked file, not the runner's stash), and the
   untracked artifact from the runner's own stash `/tmp/arc6_remeasure_1oiko27u`,
   which survived precisely *because* the `finally` never ran and which was
   hash-checked against the pristine values **before** being copied back.  Both
   trees are now byte-correct: canonical `git status --porcelain` empty, and the
   three protected artifacts back at `ed90bf28…` / `db47ad2c…` / `1815d381…`.

   **Three things worth carrying forward, none of them "be more careful".**
   (i) The hazard is not hypothetical and it is not rare — it fired on a
   *read-only confirmation run* that was not supposed to measure anything.
   (ii) **A timeout is an attacker.** Any wrapper that can `SIGKILL` the runner
   defeats a `finally`-based restore, so save/restore in Python is not a
   sufficient guard for a tree-mutating measurement; the protection would have
   to be a lock plus a **startup** reconciliation that restores from a stash it
   finds on disk, not only a shutdown one.  (iii) The asymmetry that made
   recovery possible is worth keeping: the tracked file was restorable from
   **git**, the untracked one only from a temp directory that happened to
   survive.  §7.4's symlinked `results/` is what put a canonical-tree artifact
   in reach of that.  **None of this rung's measurements ran during the damaged
   window** — every number above predates it and was taken with the tree
   verified clean.
6. **THE OLD PIN HAD TO BE DELETED TO LAND THE CHANGE**, which is the pin
   working, not a regression.
   `test_the_hands_follow_ag_select_NOT_the_magnitude_collapse` asserted the
   pre-A11 wiring and said in its own docstring that it existed *"so that wiring
   order-N in is a LOUD change rather than a silent one."*  It has been
   **inverted, not removed** — `test_wh3_arming_on_the_ORDER_1_winner_no_longer_
   dispatches_under_order_N` asserts the mirror property, so the wiring is still
   gated in both directions and reverting it would still be loud.

---

## 8. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **THE FALLBACK IS SILENT, AND IT FAILS TOWARD THE COLLAPSE THE ARC MEASURED
   AS MISPRICED.**  If `mg_select` ever stops firing — a boot without
   `arc_magnitude`, an empty pool at the wrong moment, a future edit to its
   guard — `SEL_AGID` reverts to order-1 and nothing raises an alarm.  This is
   mitigated after the fact (`selected_by` on the order) and **not prevented**.
   The alternative designs both have worse failure modes: a hard dependency
   changes what every existing scene boots, and a *required* order-N stamp
   bricks the executor on graphs that legitimately lack it.  This is the line to
   attack.
2. **THE HANDS NOW ACT ON THE FIRST BOOT, UNASKED.**  That is the result, and it
   is also the hazard: an agent booting `arc_goals` + `arc_magnitude` +
   `arc_executor` with the measured ladder will **run a 138-second measurement
   nobody requested**.  Only `self_load_only` stands between that and every
   agent in the tree, and AG-5's uncertainty #6 (activation is one key and a
   paired sweep) is now materially more expensive to get wrong.
3. **ORDER-N'S OWN KNOWN RESIDUAL IS NOW LOAD-BEARING FOR THE HANDS.**  A11
   states it: the survival law's **shape** is authored though its factors are
   read from artifacts, so this is *"better calibrated"*, not *"calibrated."*
   Before this rung that residual priced a ranking nobody acted on.  It now
   decides what runs.
4. **`ag_ask` AND THE HANDS NOW READ DIFFERENT COLLAPSES.**  `ag_ask` is frozen
   and reads `arc_sel_*`; `ax_dispatch` reads `mg_sel_*`.  On the shipped boot
   they name **different goals**, so the agent can ask about one goal while
   acting on another in the same fixpoint — measured live at iteration 0 of WH2.
   Nothing broke, and the ask is now mostly irrelevant, but *"the question and
   the action are about the same thing"* has quietly stopped being true and
   nothing asserts it either way.
5. **THE TWO-TICK AGREEMENT IS STILL AN AGREEMENT TEST, NOT A QUIESCENCE
   PROOF** — AG-5's uncertainty #3, inherited unchanged and arguably with more
   surface: the order-N stamps are written by a four-rule guard chain
   (`mg_select` → `mg_select_audit` → `mg_select_runner_up` → `mg_select_margin`)
   rather than one rule, so there is more of the fixpoint during which they are
   transient.  Every scene here is stable and gated; this engine still offers no
   way to express fixpoint completion.
6. **THE REACH IS STILL ONE NODE.**  One `ExecClass`, one executable goal, one
   runner.  The swap changed which collapse selects; it did not widen what can
   be selected.  A second re-measurable residual remains the honest test.
7. **`mg_sel_agid` INHERITS `arc_sel_agid`'S POOL EXPOSURE EXACTLY.**  Measured
   rather than argued (`test_wh3_the_ORDER_N_stamp_OUTLIVES_the_pool_and_the_
   pool_guard_catches_it`): `mg_select`'s guard is the same lifted
   `Exists(POOL_AS(…))`, so with the pool emptied the order-N stamp **does**
   outlive its goal's membership — and `ax_dispatch` mints nothing anyway,
   because `_in_pool` is re-asserted on the **bound goal** and does not care
   which stamp bound it.  The comment item (3) AG-5 wrote for order-1 transfers
   verbatim.  **No new hazard, and the check that covers it was already there** —
   but it is the guard doing the work, not the stamp being safe.
8. **ONE EXECUTION IS STILL ONE EXECUTION.**  §3.2: the swap changed who starts
   the loop, not how it ends.  The re-arm deadlock (AG-5 §5) and the missing
   impotence term (§5) are both still live holes.

---

## 9. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | the emitter — `SEL_AGID` / `SEL_VALUE` / `ARMED_AGID` / `ARMED_VALUE` / `COLLAPSE_NAME`, `_armed` rewritten, `ax_dispatch` comment + effects, version 1.1.0 |
| `seeds/arc_executor.json` | **regenerated** from that emitter, never hand-edited; gated byte-identical by `test_ex6_the_seed_REGENERATES_byte_identically` |
| `domains/arc_executor.py` | `ARM_CARRY` + `arm` — four verbatim copies from a constant table, no branch |
| `tests/test_arc_executor_migrated.py` | the pre-A11 pin **inverted**, plus six gates: `test_wh1_the_hands_now_follow_the_ORDER_N_collapse`, `test_wh1_CONTROL_without_the_tier_ladder_the_two_collapses_AGREE`, `test_wh1_the_adapter_carry_is_a_CONSTANT_TABLE_not_a_choice`, `test_wh3_the_fallback_when_the_order_N_collapse_is_NOT_on_the_graph`, `test_wh3_arming_on_the_ORDER_1_winner_no_longer_dispatches_under_order_N`, `test_wh3_the_ORDER_N_stamp_OUTLIVES_the_pool_and_the_pool_guard_catches_it` |
| `scripts/arc6_wire_hands_measure.py` | the measurement runner — four WH1 arms, two WH2 loops, the suites; the pre-change control is `HEAD`'s seed loaded from git |
| `results/arc6_wire_hands.json` | the artifact, engine-stamped, carrying every trace quoted above |
| `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` | this file |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | **amendment A12** appended |

**Two things in this worktree's `git status` that are NOT part of the change,
flagged so a reviewer does not stage them:**

- **`runners/dsl/python/substrate_rs/_native.abi3.so` reads as modified.**  It is
  the rebuilt engine (§6), it is machine-specific, and the committed one does
  not run here.  Whether the tracked binary should be replaced is a decision
  about the repository, not about this rung — **it is deliberately left for the
  reviewer** and nothing in this rung depends on the answer.
- **`data` and `results` appear as untracked.**  They are **symlinks** into the
  canonical tree (§7.4); `.gitignore`'s `data/` and `results/` patterns match
  directories, not symlinks, so `git status` lists them.  They must not be
  staged.

**Nothing in the canonical tree changed.**  `git status --porcelain` there is
empty and its `_native.abi3.so` is byte-identical (`62272924d26f…`), verified
after every build and after the live re-measurement.

---

## 10. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/arc6-wire-hands 26ca9ffaa8
cd /home/matt/arc6-wire-hands
ln -s /home/matt/ozmadev/ocelot/data    data        # 39G, gitignored
ln -s /home/matt/ozmadev/ocelot/results results     # 21G, gitignored

# --- the engine.  THE COMMITTED .so DOES NOT IMPORT HERE (glibc), AND THE
#     CRATE DOES NOT COMPILE ON rustc 1.87 (avx512 intrinsics).  See SS6.
curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable \
     --profile minimal --no-modify-path        # -> rustc 1.97.1
export PATH="$HOME/.cargo/bin:$PATH"
bash scripts/engine_build.sh                   # respects .cargo/config.toml jobs=4
#   NB its last line prints `python: command not found` on a box with only
#   `python3` on PATH.  That is the provenance ECHO, after the install; the
#   `cp --remove-destination` has already happened and the sha below is correct.
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85
mkdir -p ~/ozma-engine-archive && cp --remove-destination \
  runners/dsl/python/substrate_rs/_native.abi3.so \
  ~/ozma-engine-archive/_native.abi3.so.953b8e3f          # A1.1

# --- the coherence probe.  STOP if these read back the same. --------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the seed is EMITTED, never hand-edited ------------------------------
python3 tools/build_arc_executor_seed.py            # writes seeds/arc_executor.json
python3 tools/build_arc_executor_seed.py --check    # "up to date"

# --- the measurement: WH1 four arms, WH2 two loops, WH3 five suites ------
#     ~13 min; the WH2 order-N arm runs a REAL 138s re-measurement.
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:.:scripts \
  python3 scripts/arc6_wire_hands_measure.py       # -> results/arc6_wire_hands.json
#   add --no-suites for WH1+WH2 only (~5 min)

# --- the gate ------------------------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf        # 39 passed, 1 failed (SS4.1)

# --- the WH3 arms, run identically before and after the change -----------
for s in test_arc_executor_migrated test_arc_goals_migrated \
         test_goal_residual_migrated test_arc6_valuelayer_migrated \
         test_arc_magnitude_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done
```

**`--confcutdir=$PWD` on every pytest invocation.**  This worktree is *not*
nested inside the canonical repo, so the parent-`conftest.py` failure the
value-layer rung documented does not arise here — the flag is kept anyway
because it is the invocation every other arc-6 rung's numbers were taken under,
and an arm that differs by a flag is an arm that differs.

**Engine provenance.**  Every number in this document was produced by
`953b8e3fa6471a285f5e4d5fb731a721667ecf6e4fffba1f3feca52b96683a85`, resolving
from inside `/home/matt/arc6-wire-hands`, with
`engine_provenance.source_match == "own"` and `stale_rust: []`.  §6 is the
condition that goes with it and must be quoted alongside it.

**Contamination.**  No MBPP test-split `code` was read except by the existing
verdict battery and witness sweep, whose reads are the measurement itself and
which were untouched by this rung.  Nothing entered a codebook, a cue table or a
route table: the route table is the same one `ExecClass` AG-5 shipped.
