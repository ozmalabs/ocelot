# ARC 6 — MG4: ORDER-N DECOMPOSITION, THE PIECE A9 DESIGNED AND THREE RUNGS DECLINED TO BUILD

**Date:** 2026-08-11
**Prereg:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment **A16** (`MG4a`–`MG4d`),
registered before this build; corrected in place during the build (§7 item 1)
the same way the amendment itself records.
**Design:** `PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md` §6 ("MG4 — THE DESIGN. NOT
BUILT."); scoping note `PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md` §10; interaction
context `PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md`.
**Base commit:** `d9c0ee0` (detached worktree `/home/matt/ocelot-mg4-decompose`,
branch `arc6-mg4-decompose`).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`,
copied into this worktree and **verified resolving from inside it** —
`substrate_rs._native.__file__` is
`/home/matt/ocelot-mg4-decompose/runners/dsl/python/substrate_rs/_native.abi3.so`.
Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**. This engine sha differs from every prior rung's
(`8311d4356082…`/`953b8e3fa647…`) — the box's committed binary has been
rebuilt since (per the task brief, most recently for the gamma-fixes rung) —
and behavioural equivalence is measured the same way A12.1 measured it: the
five pre-existing gate suites reproduce their known baseline exactly (§5).
**Seeds:** `seeds/arc_decompose.json` v1.0.0, sha256
`41b2e0c4593f2dca13bb9c889f7e50f08fc82ee905ca24a7396d3d7e0eff24af` (new, 3
rules); `seeds/arc_magnitude.json` v1.1.0 (bumped from v1.0.0), sha256
`b31e3c7669943b7691fc06140851b3f9b19d0ce55220b1d6aa4880d9f00d2e7f` (ONE
additive guard). Both emitted, gated byte-identical to their own emitters.
**Gate:** `tests/test_arc_decompose_migrated.py` — **19/19 green**.

**SCOPE: MG4 — the order-N decomposition consumer §6 designed and left
unbuilt.** Not in scope, unchanged from A13–A16's own boundary: the re-arm
deadlock, the silent order-N fallback, `ag_ask`/`ax_dispatch`
collapse-agreement, `gr_condition_lapse`'s closed vocabulary, fold-up, and
any `ExecClass` for a decomposition-tier goal.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **MG4a — the registered arithmetic identity, both directions** | **PASS, with a named and measured exception** | `Sum(children.headroom_n × tier_survival) == parent.orderN_headroom_n` holds **exactly** (13.637248) against the value captured **before** a horizon truncates the reading; a corrupted `tier_survival` is shown to break the same check. **Does NOT hold, and is not hidden**, against the parent's own **post-decompose, horizon-truncated** `orderN_headroom_n` (0.0) at the natural push_back trigger — because that trigger, by construction, always zeroes the parent's own reading. §2 |
| **MG4b — a decomposed parent leaves the pool, paired lists** | **PASS** | pool **8 → 11**: `{parent} ` leaves, `{tier1, tier2, tier3, tier4}` join — full agid lists, both directions, not a bare delta. §3 |
| **MG4c — no double-counting, live** | **PASS** | parent absent from `POOL()` under **both** `ag_select` (order-1) and `mg_select` (order-N) the instant `headroom_n → 0.0` is stamped; children present; parent unreachable as either collapse's winner, read off each collapse's own stamp. §4 |
| **MG4d — no regression, node-id lists not counts** | **PASS** | the five pre-existing gate suites reproduce the **same two** failing node ids, before and after, unchanged; `seeds/arc_goals.json`/`goal_residuals.json`/`program_synthesis.json` byte-identical to `HEAD`; both new/edited seeds regenerate byte-identically from their own emitters; the ONE additive guard on `mg_goal_order_n_default` is inert on `arc_magnitude`'s own 43 gates and on the executor's 60. §5 |

**The one thing worth reading if you read nothing else.** A first draft of
this rung's own design (registered in A16, before any code was written)
gated child-minting on the tier's own `in_horizon` flag, reasoning this would
make the arithmetic identity hold "by construction". **It was wrong, and
measured wrong before it shipped**: `decompose_required == 1.0` and
`EXISTS tier t, in_horizon(t)` are **mutually exclusive for any ladder,
always** — the same trigger comparison (`cost_first > horizon_net`) that
sets `decompose_required` also, by definition, makes the cheapest tier (and
therefore every tier, by monotonicity) fail `in_horizon`. Gating the mint on
`in_horizon` would have made `mg_decompose` **permanently dead under its own
trigger** — exactly the `qd_decompose` failure mode `PROGRAM_SYNTHESIS_ARC6_
MAGNITUDE.md` §1 (JOB 0) found and named as *worse* than merely unreached.
Corrected before the gate was written (§7 item 1): every tier mints
unconditionally, and each child is re-priced **individually** by the
unmodified `mg_rung` — which is what §6.3 of the design actually asked for.

---

## 1. MECHANISM — WHAT WAS BUILT

```
seeds/arc_decompose.json          NEW seed. 0 nodes, 0 edges, 1 production,
                                  3 rules. self_load_only. depends_on
                                  [goal_residuals, arc_goals, arc_magnitude].
                                  NOT dependent on arc_executor.

  mg_decompose        mints ONE child ArcGoal per un-materialised tier of a
                       goal whose decompose_required==1.0 — EVERY tier, not
                       only in-horizon ones (§7 item 1). One mint per
                       fixpoint pass, per goal (Argmin-ONE_OF serializer,
                       the ag_mint_blocker/pcon_mint idiom). Child carries
                       headroom_n (raw increment_n), tier_survival (carried
                       alongside, not multiplied in), magnitude_cost_units
                       AND cost_bits (both = cum_cost_units, so mg_rung's
                       existing cost fallback prices it), parent_agid,
                       parent_ladder_key (NOT proposed_seam — confinement
                       against re-decomposition), inherited sig_seam/
                       sig_lever/sig_target, reach_class_factor=1.0.
  mg_decompose_retire  moves the parent to status='decomposed' (descriptive,
                       parallel to ax_retired_epoch's 'retired') once EVERY
                       tier has a child AND at least one child exists. THE
                       LOAD-BEARING EFFECT is headroom_n → 0.0: POOL()'s OWN
                       pre-existing Gt(headroom_n, 0.0) clause then excludes
                       the parent from BOTH ag_select's and mg_select's pool
                       — ZERO edits to seeds/arc_goals.json.
  mg_child_order_n     a decomposition child's own orderN_headroom_n =
                       headroom_n × tier_survival — the discounted value the
                       arithmetic identity sums.

seeds/arc_magnitude.json v1.1.0   ONE additive guard: mg_goal_order_n_default
                                  now also excludes a goal carrying
                                  parent_agid. Without it, that rule's
                                  UNCHANGED original guard (no ladder) would
                                  match every decomposition child too and
                                  silently overwrite mg_child_order_n's
                                  discounted value back to the undiscounted
                                  headroom_n every pass — the SAME order-1-
                                  credit inflation trap §6.2(4) names, one
                                  layer up. Inert on every scene that never
                                  loads arc_decompose (no goal on the shipped
                                  graph carries parent_agid) — confirmed by
                                  re-running arc_magnitude's own 43 gates.

domains/arc_decompose_ingest.py   the world adapter — self-load
                                  (ensure_arc_decompose) + pure read-off
                                  helpers (children_of, decomposed_goals,
                                  pool_agids). No decisions; passes the
                                  module-specific source audit.

tools/build_arc_decompose_seed.py the emitter. Imports Term idioms from
                                  tools/build_arc_magnitude_seed.py, so a
                                  change there makes this seed go out of
                                  date loudly.

tests/test_arc_decompose_migrated.py   the gate — 19/19.
```

### 1.1 The pool-exit mechanism, and why `seeds/arc_goals.json` is untouched

`PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md` §6.2(2) considered adding a
`"decomposed"` status disjunct to `POOL()`'s filter and declined because it
required editing the byte-frozen `arc_goals.json`. `PROGRAM_SYNTHESIS_ARC6_
EXECUTOR.md` §10 reported this was "no longer" required, without saying how.
**It is not required because `POOL()` already excludes on
`Gt(headroom_n, 0.0)`** — the exact narrow pool-exit technique A13 §7.1 and
A15 §4.2 validated for constructing scenes, used here as the production
mechanism rather than a test fixture. `mg_decompose_retire` stamps
`headroom_n = 0.0` on the parent; `POOL()` — shared, unmodified, imported
verbatim by both `ag_select` (order-1) and `mg_select` (order-N, machine-
lifted from the same `Filter`) — excludes it from **both** collapses with one
write. `status: "decomposed"` is written too, exactly parallel to
`ax_retired_epoch`'s `"retired"`, but purely as a descriptive, legible
terminal token — never itself the exclusion mechanism.

### 1.2 The correction, and what it means for §6.3's promise

Once every tier mints unconditionally, each child is a genuinely separate
`ArcGoal`, and the **unmodified** `mg_rung` (it matches every `ArcGoal`, no
restriction) prices it on its own `cost_bits` against whatever horizon is
held — this is exactly §6.3's stated purpose: *"A child whose cum_cost_units
≤ horizon_net is absorb; the others stay push_back."* On the shipped,
**nested** ladder (`cum_cost_units` is genuinely cumulative — B1 CONTAINS
B0's eight units, so a child cannot be priced at a smaller marginal cost
without breaking the nesting), a REAL residual falls out of this, reported
honestly in §6 rather than smoothed over: on THIS ladder, tier 1's
`cum_cost_units` (8) **is** `cost_first`, the exact number
`decompose_required`'s own trigger already compared against the SAME
horizon — so no child, at the horizon that triggered decomposition, can be
individually **more** affordable than what the trigger already implied.
§6.3's promise materialises only once the horizon **later widens** past the
ladder's minimum tier cost (§6, computed illustration).

---

## 2. MG4a — THE ARITHMETIC IDENTITY, BOTH DIRECTIONS, AND THE HONEST MISMATCH

### 2.1 The positive scene

`test_mg4a_the_identity_holds_against_the_PRE_horizon_captured_value`:
`orderN_headroom_n` is captured at boot, **before** any horizon is held —
`13.637248`, the ladder's full projected value (no horizon truncates it: on
this engine `NO_HORIZON()` makes `in_horizon` read `1.0` for every tier). A
real horizon reply (5.0 units, the same value the natural push_back scene
below uses) then drives decomposition through the ordinary reply mechanism.
Post-decompose:

| | value |
|---|---|
| `orderN_headroom_n` captured at boot (pre-horizon) | **13.637248** |
| `Sum(children.headroom_n × tier_survival)` | **13.637248** |
| difference | **0.0** (< 1e-6) |

### 2.2 The negative control (A7's own discipline)

`test_mg4a_the_identity_is_a_check_that_CAN_fail`: the same correctly-built
decomposition, then `tier_survival` on one child is corrupted to `0.0` (the
scene A10 itself registered — *"including a scene where a child's survival
is dropped, which must fail the gate"*). The recomputed sum moves from
`13.637248` to `3.637248` — a difference of `10.0`, well outside tolerance.
**The check notices.**

### 2.3 The honest mismatch — measured, not hidden

`test_mg4a_the_NATURAL_trigger_shows_the_HONEST_mismatch`: the same
horizon=5.0 reply, but the comparison is against the parent's **live,
post-decompose** `orderN_headroom_n` instead of the value captured before
the reply arrived:

| | value |
|---|---|
| parent `magnitude_rung` | `push_back` |
| parent `orderN_headroom_n` (post-decompose, live) | **0.0** |
| `Sum(children.headroom_n × tier_survival)` | **13.637248** |
| `Sum(children) == parent.orderN_headroom_n`, as literally worded | **FALSE** |

This is not a bug: `orderN_headroom_n` is horizon-truncated by
`mg_goal_order_n`'s own, unmodified `_order_n_sum` — and the natural
push_back trigger is, by the mathematical fact in §0, always the state where
that truncation zeroes every tier. **The registered bar holds against the
quantity it was written to protect** (the ladder's real, undiscounted-by-
horizon total is preserved across the split, and cannot be inflated or
dropped) **but not against the live post-decompose attribute**, because that
attribute answers a different question ("what is the parent worth right
now, under this horizon") than the one the split's integrity check needs
answered ("did splitting change the total"). Recorded here as a genuine
tension in the original bar wording, per A16's own correction, for whoever
revisits it — not patched into invisibility.

---

## 3. MG4b — THE PARENT LEAVES THE POOL, PAIRED LISTS

Measured live at the natural push_back trigger (horizon=5.0):

**Before** (8 members):
```
arc.remeasure.arc6.verdict.row_verdict_seed_only
arc.supply.arc6.seam_a.import_oracle.budget
arc.supply.arc6.seam_a.import_oracle.missing_dimension
arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive   <- the parent
arc6.claim.seam_b_signature_39_of_257
arc6.claim.seam_d_verbatim_35_of_36
arc6.claim.tier0_hs1_0_of_10
arc6.claim.valuelayer_supersedes_row_verdict
```

**After** (11 members):
```
arc.remeasure.arc6.verdict.row_verdict_seed_only
arc.supply.arc6.seam_a.import_oracle.budget
arc.supply.arc6.seam_a.import_oracle.missing_dimension
arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive.tier1.0   <- child
arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive.tier2.0   <- child
arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive.tier3.0   <- child
arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive.tier4.0   <- child
arc6.claim.seam_b_signature_39_of_257
arc6.claim.seam_d_verbatim_35_of_36
arc6.claim.tier0_hs1_0_of_10
arc6.claim.valuelayer_supersedes_row_verdict
```

`before − after = {…missing_structural_primitive}` (exactly the parent);
`after − before = {…tier1.0, …tier2.0, …tier3.0, …tier4.0}` (exactly the
four children). Net **+3** (8→11), reported as the paired sets, not the
bare delta, per the registered bar.

Per-child values, measured:

| child | tier | headroom_n | tier_survival | orderN_headroom_n | cost_bits | ratio (h=5) | rung |
|---|---|---|---|---|---|---|---|
| `.tier1.0` | B0 | 10.0 | 1.0 | 10.0 | 8.0 | 1.6 | push_back |
| `.tier2.0` | B1 | 16.0 | 0.192 | 3.072 | 18.0 | 3.6 | push_back |
| `.tier3.0` | B2 | 6.0 | 0.06144 | 0.36864 | 24.0 | 4.8 | push_back |
| `.tier4.0` | B3 | 10.0 | 0.0196608 | 0.1966080 | 28.0 | 5.6 | push_back |

Note the four **different** ratios — each child is priced on its own
`cost_bits`, not the parent's single 28/5 ratio, demonstrated live
(`test_mg4b_each_child_is_INDIVIDUALLY_repriced_by_the_UNCHANGED_mg_rung`).

**Computed illustration, not asserted live (§1.2's residual):** at
horizon=10 (not naturally reachable together with `decompose_required` on
this ladder — see §7 item 2), tier 1 alone reads `magnitude_ratio =
8.0/10.0 = 0.8` → **`absorb`**, while the un-decomposed parent's own ladder
ratio at the same horizon (`28.0/10.0 = 2.8`) would not be. This is where
§6.3's promise actually pays out — once the horizon widens past the ladder's
cheapest tier — and it is why the parent's disappearance (§1.1) is not a
loss: the fragment that becomes affordable later is still there to become
`absorb`-able, where the atomic 42-task goal never would have been at that
same horizon (it would have read `balance`, competing as one lump, per the
existing MG3 table).

---

## 4. MG4c — NO DOUBLE-COUNTING, LIVE

`test_mg4c_the_parent_and_its_children_are_NEVER_simultaneously_pooled`:
at the same horizon=5.0 scene, the parent's agid is absent from `POOL()`
while all four children's agids are present — read via
`domains/arc_decompose_ingest.pool_agids`, a Python mirror of `POOL()`'s own
predicate (status not retired/settled, `headroom_n > 0`), never the
authority itself.

**Structural**, not merely by absence from a printed rank
(`test_mg4c_the_parents_own_value_is_STRUCTURALLY_unreachable_once_excluded`):
read off each collapse's **own stamped winner**.

| collapse | winner at horizon=5, post-decompose |
|---|---|
| `ag_select` (order-1), `arc_sel_agid` | `arc.remeasure.arc6.verdict.row_verdict_seed_only` |
| `mg_select` (order-N), `mg_sel_agid` | `arc.remeasure.arc6.verdict.row_verdict_seed_only` |

Neither collapse names the parent or any child as its winner here (the
re-measurement goal, unaffected by this rung, still wins both) — but the
structural point is that `MaxOver` runs over `POOL()`'s own `Filter`, so the
parent (excluded from that `Filter`) cannot be selected by either collapse
by construction, not merely "happens not to be" on this particular scene.

The negative half (`test_mg4c_decomposition_does_NOT_fire_when_nothing_is_
required`): at horizon=40 (`absorb`) and horizon=20 (`balance`), `status`
never becomes `"decomposed"` and zero children mint — the existing MG3
scenes are unaffected by loading `arc_decompose`.

---

## 5. MG4d — REGRESSION, NODE-ID LISTS NOT COUNTS

Both arms run on the **same binary** (`c5e50801d48a`) in this worktree; the
**before** arm was measured first, before any code file was touched (only
this file's own eventual existence and the A16 prereg-amendment doc edit
preceded it).

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 60 passed, 1 failed (61 collected) | 60 passed, 1 failed (61 collected) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` (this rung, new) | n/a | **19 / 19** | — |

Both pre-existing reds are the **same two node ids every prior rung since
A12 has recorded**: `results/` is untracked in this checkout (`git show
HEAD:results/…` returns empty, failing `test_ex1`'s byte-identity check
against a file that was never committed) and this fresh binary's short sha
is not in `test_gr4`'s three-entry allowlist. Neither is this rung's to fix,
and neither was touched. **`test_mg5_JOB0_qd_decompose_is_RESIDENT_AND_DEAD_
and_the_probe_can_tell` is GREEN in this environment** (checked explicitly,
per the task brief) — `results/` carries **zero tracked files** in this
checkout (`git ls-files results/` is empty), so the self-referential
`git grep -l has_subgoal_spec` this test performs finds only
`seeds/question_driving.json`, matching its assertion. This is
**environment-conditional, exactly as A12.1 recorded it** ("the same test at
the same commit returns opposite verdicts depending only on which artifacts
happen to be tracked") — not a fix, and not claimed as one.

**Confinement.** `seeds/arc_goals.json`, `seeds/goal_residuals.json`,
`seeds/program_synthesis.json`, `domains/arc_goal_ingest.py`,
`domains/goal_residual_ingest.py` are byte-identical to `HEAD`
(`git diff --exit-code`, gated in both `test_arc_decompose_migrated.py` and
the updated `test_ex6` in `test_arc_executor_migrated.py`).
`seeds/arc_decompose.json` and `seeds/arc_magnitude.json` both regenerate
byte-identically from their own (current, edited) emitters. The one new
adapter (`domains/arc_decompose_ingest.py`) passes the module-specific
source audit (no `.evaluate(`, no `run_rules`, no raw `substrate_rs`
import). Both seeds ship `self_load_only` and are confirmed **not** globbed
into every agent (`_read_seeds` skips both; the on-demand loader installs
each idempotently).

**One test in a DOWNSTREAM rung's suite required updating, named as a
decision (§7 item 3):** `test_arc_executor_migrated.py::test_ex6_the_seeds_
below_this_rung_are_UNTOUCHED` asserted `seeds/arc_magnitude.json`
byte-identical to `HEAD` — true before A10–A15, false now that this rung
owns and evolves that seed too. Per the WH1 precedent (invert a pin with a
docstring, never remove it silently), the assertion was narrowed to the
seeds genuinely below this rung's own scope and a replacement check added:
`arc_magnitude.json` still regenerates byte-identically from its **own**
current emitter. The executor's 60 other gates are unaffected (confirmed:
`parent_agid` is absent from every goal the executor's own scenes mint, so
the new guard is inert there by the same construction `test_arc_magnitude_
migrated`'s 43 gates already confirm it inert on).

---

## 6. COMPUTED ILLUSTRATION — WHAT DECOMPOSITION ACTUALLY BUYS

Not asserted live (constructing it would require a second horizon reply in
the same scene, which `mg_ask_constraints`'s once-per-epoch rate bound
refuses without an epoch bump this rung does not build — §7 item 2), but
directly computable from the measured numbers above and worth stating
plainly, because it is the answer to the question this whole apparatus
exists for:

| horizon | undecomposed parent's own rung | tier 1 alone, once decomposed |
|---|---|---|
| 5 (the natural trigger) | `push_back` (would be, if never decomposed) | `push_back` (8/5 = 1.6) |
| 10 | `balance` (28/10=2.8, 8/10=0.8) — competes as ONE 28-unit lump | **`absorb`** (8/10=0.8) — executes outright |

At horizon=10, an undecomposed 42-task goal competes in the collapse as one
lump it cannot fully afford. The SAME goal, decomposed earlier under a
tighter horizon, has already become four separately-priced fragments — and
the cheapest one crosses into `absorb` the moment the horizon permits it,
with the other three still individually ranked and askable. This is
decomposition's actual value on a NESTED ladder: not "unlock a cheaper
price today" (§1.2's residual — it cannot, on this ladder, at the horizon
that triggers it) but "convert an all-or-nothing competition into a
piecewise absorb+compete mixture once time or budget grows" — the B0 tier,
8 units, 10 tasks, zero new TermNode variants, exactly the answer
`PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md` §6.3 named as the reason to build
this.

---

## 7. EVERYTHING THAT BROKE

Recorded because the process is the result (A11–A16's own standing
practice).

1. **The in-horizon gate — designed, registered, built, and retracted
   before the gate was written.** A16 registered decision 2 (gate each
   child's mint on the tier's own `in_horizon` flag) as the way to make the
   arithmetic identity hold "by construction". Measured false while writing
   the first scene: `decompose_required == 1.0` requires
   `magnitude_ratio_first_tier > 1`, i.e. `cost_first > horizon_net`, where
   `cost_first` **is** the cheapest tier's own `cum_cost_units` — the exact
   quantity `in_horizon` compares against the same `horizon_net`. Because
   tier cost is cumulative and monotonic, this makes `decompose_required==1`
   and `EXISTS t, in_horizon(t)` mutually exclusive for **any** ladder,
   always — an in-horizon gate would have made `mg_decompose` permanently
   dead under its own trigger. Caught by re-deriving the inequality
   algebraically before shipping the seed (§0), and corrected in the same
   sitting: A16 itself carries the correction, in the open, rather than a
   silently rewritten registration. `tools/build_arc_decompose_seed.py`'s
   own module docstring carries the full derivation.
2. **A raw attribute poke on `decompose_required` does NOT survive
   `run_rules()`, even once, and repeating it does not help — a genuine
   engine-ordering finding, not a test mistake.** The first draft of MG4a's
   "constructed scene" tried poking `decompose_required = 1.0` directly with
   no horizon held, expecting `mg_decompose` to read the poke exactly as
   `mg_decompose`'s own `where` Term does when evaluated directly
   (confirmed `True` on every sub-clause via `s._inner.evaluate(...)`
   **before** calling `run_rules()`). After `run_rules()`, zero children had
   minted. Root cause: **rules from different, later-loaded seeds are not
   evaluated against one shared pre-pass snapshot** — `mg_rung`
   (`arc_magnitude`, loaded first) reads and overwrites `decompose_required`
   back to `0.0` (its own unconditional, every-pass recompute under
   `NO_HORIZON`) before `mg_decompose` (`arc_decompose`, loaded after) gets
   its turn in the same pass, and this repeats identically on every
   subsequent poke. **The `pcon_mint` "effects apply against pre-effect
   reads" guarantee is about ONE rule's own multiple candidate matches in a
   pass — it is not a cross-rule, cross-seed guarantee.** No prior rung in
   this arc had two seeds' rules racing to write the SAME attribute in one
   pass, because no prior rung added a rule that both reads AND could
   conflict with an always-firing rule (`mg_rung`, `where: L(True)`) in an
   earlier-loaded seed. Fixed by abandoning the poke entirely and using the
   real horizon-reply mechanism (`_answer_horizon`/`_drive_natural_
   decompose`), which does not need to survive a race because `mg_rung`
   recomputes the SAME `decompose_required=1.0` from the SAME held fact
   every single pass — agreement, not contention. **Registered as standing
   practice for this arc, mirroring A12.2's timeout finding:** a poke is
   safe only against a rule that does not itself unconditionally recompute
   the same attribute every pass; where one does, use the real mechanism
   that produces agreement instead of a race.
3. **A downstream rung's own gate needed a narrow, named update.**
   `test_arc_executor_migrated.py::test_ex6_the_seeds_below_this_rung_are_
   UNTOUCHED` asserted `seeds/arc_magnitude.json` byte-identical to `HEAD` —
   true when A10–A15 wrote it, false now that this rung is the seed's
   second owner. Per the WH1 precedent, narrowed rather than removed, with a
   docstring naming exactly why and a replacement check
   (regenerates-byte-identically-from-its-own-emitter) in its place. §5.
4. **A crash-recovery repeat of A12.2's own hazard, on the SAME node id,
   tripped mid-baseline.** Running `test_arc_executor_migrated.py` under
   this harness's own default 2-minute tool timeout (with an inner shell
   `timeout 480` that never got the chance to matter) killed the ~140s live
   re-measurement runner inside its own `try`, leaving
   `seeds/program_synthesis.json` patched and, in the canonical tree via the
   symlinked `results/`, `results/arc6_verdict_before.json` overwritten by
   the killed run's own `before` arm. Recovered exactly per A12.2/A15 §7
   item 6's playbook: the tracked seed via `git checkout --`, the untracked
   artifact from the killed run's own surviving `/tmp/arc6_remeasure_*`
   stash, **sha-cross-checked against three older, independent stashes that
   all agreed on the same pristine hash** (`ed90bf281bd8…`) before copying
   back. Both trees verified clean (`git status --porcelain`) before any
   further measurement. Every subsequent invocation of that suite passed an
   explicit, generous **tool-level** timeout (400000 ms), not only a shell
   one — the exact rule A15 §7 item 6 already registered, tripped here on a
   fresh box regardless.

---

## 8. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The registered arithmetic identity, as literally worded, does not hold
   at the mechanism's own natural trigger.** §2.3 is not a corner case —
   it is what happens **every time** decomposition fires without a human
   or a test deliberately capturing the pre-horizon value first. A live
   agent acting on `orderN_headroom_n` alone, post-decompose, would see `0`
   and have no record that the split preserved `13.637248` unless it (or a
   later rung) also retains the pre-decompose reading. **Not fixed here**:
   doing so would mean either changing what `orderN_headroom_n` means for a
   decomposed parent (a bigger edit, and one this rung's own registered
   scope did not include) or stamping a NEW field (e.g.
   `orderN_headroom_n_at_decompose`) purely for audit — a small, deferred,
   named follow-up.
2. **§6.3's promised benefit (a cheap tier becomes individually actionable)
   does not materialise AT the horizon that triggers decomposition, on this
   specific nested ladder** — only once the horizon later widens past the
   ladder's cheapest tier, and that scene is currently only a computed
   illustration (§6), not a live gate, because testing it live would need a
   second horizon reply in one scene, which `mg_ask_constraints`'s
   once-per-epoch rate bound refuses without an epoch bump. A future rung
   that wires the epoch producer to something other than a real
   re-measurement (or accepts a second, epoch-bumped `_boot()`) could close
   this gap live.
3. **Child pricing uses each tier's CUMULATIVE cost (`cum_cost_units`), not
   a marginal/incremental one** — correct given the ladder's own nesting
   (§1.2), but it means a decomposed child never reads as "cheaper" than
   the parent's own `cost_first` implied at the same horizon. A different
   ladder shape (non-nested, independently buildable tiers) would behave
   differently and is untested here — this rung's only measured ladder is
   the one shipped structural-primitive bundle.
4. **Fold-up was not built**, named explicitly in A16 rather than silently
   dropped: nothing in this tree resolves a decomposition child's status
   (no `ExecClass` targets a structural-primitive tier), so a twinned
   `qd_compound_resolve`/`_wall` rule would be dead code with nothing to
   trigger it — the same shape JOB 0 found for `qd_decompose` itself. The
   child shape (`parent_agid`, `tier_order`) is legible to a future
   fold-up rule; none is written.
5. **The reach is one ladder, one goal.** Exactly as AG-5's uncertainty #1
   and A15's uncertainty #1 both name for their own mechanisms: the ONE
   measured tier ladder in this tree (the structural-primitive bundle) is
   the only scene decomposition has ever split. A second, independently-
   measured ladder (were one to exist) would be the honest test of whether
   `_undecomposed_tiers`'s dedup and `mg_decompose`'s Argmin serializer
   generalise, exactly as a second `reach_class_counts` payload would be
   for `ag_mint_blocker`.
6. **This rung never exercised decomposition under a LIVE `ax_dispatch`/
   executor scene** (`arc_executor` is deliberately not a dependency, §1).
   Whether a decomposed pool's children ever become the executor's own
   `arc_sel_agid`/`mg_sel_agid` winner (none of the shipped classes route a
   `decomposition_tier` kind, so today they cannot) is unmeasured and,
   per this rung's own explicit scope boundary, not built here.
7. **The re-arm deadlock and the silent order-N fallback are untouched**,
   per the task's explicit scope boundary, and neither was exercised by
   any scene in this rung in a way that would have required touching them.

---

## 9. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/ocelot-mg4-decompose d9c0ee0
cd /home/matt/ocelot-mg4-decompose
git checkout -b arc6-mg4-decompose
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine -------------------------------------------------------------
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe ---------------------------------------------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the seeds are EMITTED, never hand-edited ------------------------------
python3 tools/build_arc_magnitude_seed.py   # writes seeds/arc_magnitude.json (v1.1.0)
python3 tools/build_arc_decompose_seed.py   # writes seeds/arc_decompose.json (v1.0.0)
python3 tools/build_arc_magnitude_seed.py --check
python3 tools/build_arc_decompose_seed.py --check

# --- the gate ---------------------------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_decompose_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 19 passed

# --- the regression arms (test_arc_executor_migrated.py includes a REAL
#     ~140-200s live re-measurement — ALWAYS an explicit, GENEROUS
#     tool-level timeout, never only a shell-level one) -------------------
for s in test_arc_goals_migrated test_goal_residual_migrated \
         test_arc6_valuelayer_migrated test_arc_magnitude_migrated; do
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
    PYTHONPATH=runners/dsl/python:. \
    python3 -m pytest tests/$s.py --confcutdir=$PWD -q -p no:randomly -rf
done
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 60 passed, 1 failed (pre-existing)
```

**`--confcutdir=$PWD` on every pytest invocation** — same reason as every
prior arc-6 rung: this worktree is not nested inside the canonical repo.

**Engine provenance.** Every number in this document was produced by
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`, resolving
from inside `/home/matt/ocelot-mg4-decompose`.

**Contamination.** No MBPP test-split content was read by anything this rung
added — `mg_decompose`/`mg_decompose_retire`/`mg_child_order_n` are pure
graph arithmetic over `ArcGoal`/`ArcTier` data already resident from the
magnitude rung's own artifact reads. Nothing new entered a codebook, a
route table, or a cue table.

---

## 10. FILES

| file | what |
|---|---|
| `seeds/arc_decompose.json` | the seed — 0 nodes, 0 edges, 1 production, **3 rules**. `self_load_only`. Emitted, not hand-written |
| `tools/build_arc_decompose_seed.py` | the emitter; imports Term idioms from `tools/build_arc_magnitude_seed.py`, carries the full in-horizon-gate retraction derivation in its module docstring |
| `seeds/arc_magnitude.json` | **v1.0.0 → v1.1.0** — ONE additive guard on `mg_goal_order_n_default`, inert on every existing scene |
| `tools/build_arc_magnitude_seed.py` | edited: `_is_decomposition_child`, the guard, version bump |
| `domains/arc_decompose_ingest.py` | the world adapter — self-load + read-off helpers. Mechanical I/O only |
| `tests/test_arc_decompose_migrated.py` | the gate — **19/19** |
| `tests/test_arc_executor_migrated.py` | one pin narrowed (`test_ex6_…`), named, per the WH1 precedent |
| `docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A16 appended, registered before the build, corrected in place during it |
