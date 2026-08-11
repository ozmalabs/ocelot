# ARC 6 — A20: `ag_ask` AND `ax_dispatch`, READING DIFFERENT COLLAPSES — CHARACTERIZED, STRESSED, AND MADE OBSERVABLE

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A20** (`AR20a`–`AR20d`),
registered **before** this measurement/build.
**Base commit:** `207d764` (`main`, detached worktree
`/home/matt/ocelot-arc6-ask-dispatch-safety`, branch
`arc6-ask-dispatch-safety`).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
— copied from the canonical tree, **verified resolving from inside this
worktree** (`substrate_rs._native.__file__` is
`/home/matt/ocelot-arc6-ask-dispatch-safety/runners/dsl/python/substrate_rs/
_native.abi3.so`), `engine_provenance.source_match == "own"`, `stale_rust: []`.
**The same binary A19 measured on**; the canonical tree's copy has not moved.
Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.6.0** (bumped from v1.5.0), emitted
by `tools/build_arc_executor_seed.py` and gated byte-identical against it —
**10 rules** (the shipped 8 plus `ax_ask_divergence_active` /
`ax_ask_divergence_cleared`).
**Gates:** `tests/test_arc_executor_migrated.py` — **91 collected, 90
passed, 1 failed (pre-existing)**; the other five arc-6 suites combined —
**174 collected, 172 passed, 1 failed (pre-existing), 1 skipped**.
**Artifact:** `results/arc6_ask_dispatch_safety.json` (engine-stamped;
0.47 s, no live subprocess — every scene this rung needed is a boot +
`run_rules()` + graph read).

**SCOPE: exactly AR20a–AR20d — characterize the `ag_ask`/`ax_dispatch`
collapse divergence, stress it adversarially, decide GO/NO-GO on an
observability fix per a pre-registered criterion, and build only if
warranted.** `gr_condition_lapse`'s closed vocabulary,
`results/arc6_import_impedance.json`/`scripts/arc6_import_impedance.py`,
and anything under `docs/research/theory_convergence/` or
`docs/research/adventure_mechanics/` are all **untouched**, per the task's
explicit boundary. `ag_ask`/`seeds/arc_goals.json` are **byte-identical to
`HEAD`** throughout — the amendment's own stated preference, held.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR20a — characterize divergence on constructed scenes, as a table** | **PASS** | a depletion sweep (both with and without the tier ladder, 8 steps each), the shipped-boot reproduction, and a scope-channel adversarial probe — **17 constructed states total, `arc_sel_agid`/`mg_sel_agid` read at every one**. Finding: divergence is **not** spread or arbitrary — it is bounded by a provable structural fact (§2.3) and empirically confirmed on every constructed state (`bound_held_every_step: true`, 17/17). §2 |
| **AR20b — an adversarial scene designed to make divergence bite, report what actually happens** | **PASS, and it is a clean, well-evidenced NULL** | two probes: (i) a scope-charge scene engineered to be the single most adversarial one-lever construction available, measuring how close it comes to breaking the structural bound (**32.7 dominance margin vs a 25.0 charge — it does not break, but the margin is only 7.7**); (ii) a live reply-to-`ag_ask` scene showing the human's answer has **zero causal path** to what `ax_dispatch` acts on (`dispatched_goal_unchanged_by_the_reply: true`), traced to the two goals' **non-overlapping signature regions**. §3 |
| **AR20c — GO/NO-GO for an observability fix, registered before the answer was known** | **GO** (per the amendment's own pre-registered criterion) | divergence is real (WH1's own finding, reproduced fresh here) and the fix is buildable in A19's exact cheap shape — verified, not assumed: zero new DSL Term, zero new node/edge type, zero edit to `ag_ask`/`seeds/arc_goals.json`, zero change to `ax_dispatch`'s own dispatch decision (re-verified live on the WH1 and WH3 scenes, byte-identical). §4 |
| **AR20d — no regression, `ag_ask`/`seeds/arc_goals.json` frozen** | **PASS** | the six gate suites produce the **same** failing-node-id lists before and after, paired and named below. `seeds/arc_goals.json` and every rule body in `tools/build_arc_goals_seed.py` are byte-identical to `HEAD` — asserted structurally by a gate (`test_a20_AR20d_the_seeds_below_this_rung_including_arc_goals_are_still_UNTOUCHED`), not merely claimed. §5 |

**The one thing worth reading if you read nothing else.** WIRE_HANDS §8
named this uncertainty and explicitly declined to resolve it: *"the question
and the action are about the same thing" has quietly stopped being true and
nothing asserts it either way.* This rung asserts it. The measurement found
the divergence is **structurally bounded** on this seed's shipped policy —
`ax_dispatch` can only ever act on the goal `ag_ask` named as its winner or
the one it named as the alternative, never an undisclosed third goal — but
that bound is **not enforced anywhere** and came within **7.7** of breaking
under a single, real, adversarially-chosen scope declaration. Nothing was
found that a human/operator reading `ag_ask`'s question is actively misled
by *today*, but the one honest "bad" finding is real: **a human's answer to
`ag_ask` has no causal path to what actually executes**, confirmed by
directly replying and re-measuring, not argued from the mechanism alone. A
third `AgendaVerdict` mint/clear pair, in the exact shape A19 used for the
order-N fallback, now makes both facts — the divergence, and (via its stored
stamps) the structural bound — standing, queryable graph state. `ag_ask` was
not touched.

---

## 1. WHAT CHANGED

Three files edited (one a regenerated artifact of another), one added.
**No new DSL Term, no new node type, no new edge type, no new adapter
function, no engine source change, no edit to `ag_ask`/`seeds/
arc_goals.json`.**

```
tools/build_arc_executor_seed.py        +2 rule builders
                                         (ax_ask_divergence_active /
                                         _cleared), +2 helpers, version bump,
                                         docstring text
seeds/arc_executor.json                 REGENERATED from that emitter (never
                                         hand edited).  v1.5.0 -> v1.6.0
tests/test_arc_executor_migrated.py     12 new test_a20_* gates, 1 pin
                                         inverted (the WH1/A18/A19 precedent,
                                         applied a third time)
scripts/arc6_ask_dispatch_safety_measure.py  NEW -- the measurement runner
results/arc6_ask_dispatch_safety.json   NEW -- the artifact
PROGRAM_SYNTHESIS_ARC6_PREREG.md        amendment A20 appended
PROGRAM_SYNTHESIS_ARC6_ASK_DISPATCH_SAFETY.md  NEW -- this file
```

`domains/arc_executor.py` needed **zero** edits, the same finding A19 made
and re-checked here independently: `agenda_verdicts(sub, kind=None)` was
already generic over `kind`, so a third `kind` value
(`"ask_dispatch_divergence"`) is additive by construction
(`test_a20_AR20d_the_adapter_is_BYTE_IDENTICAL_to_HEAD`, green).

### 1.1 The mechanism is A19's own reversible pair, applied to a different comparison

```python
def _dispatch_differs_from_ask_winner():
    return AND(
        NOT(EQ(SEL_AGID(), L(None))),
        NOT(EQ(A(V("agenda"), "arc_sel_agid"), L(None))),
        NOT(EQ(SEL_AGID(), A(V("agenda"), "arc_sel_agid"))),
    )

def _r_ask_divergence_active():   # mint-once while active
    ...
    "where": AND(_dispatch_differs_from_ask_winner(),
                NOT(_ask_divergence_verdict_active())),
    "effects": [add_node AgendaVerdict{kind:'ask_dispatch_divergence',
                          active:1.0, asked_about_agid, asked_about_runner_up_agid,
                          dispatch_target_agid, dispatch_matches_runner_up, ...}]

def _r_ask_divergence_cleared():  # flip active -> 0.0 the instant they agree
    ...
    "where": AND(NOT(_dispatch_differs_from_ask_winner()),
                 EQ(avd.kind, 'ask_dispatch_divergence'), EQ(avd.active, 1.0)),
    "effects": [set_attr avd active 0.0, set_attr avd cleared_epoch ...]
```

`SEL_AGID()` is `ax_dispatch`'s **own** Term (the same ITE `ag_select`'s
order-1 stamp and `mg_select`'s order-N stamp both feed), imported unchanged;
`arc_sel_agid` is the plain attr `ag_ask` itself reads. Both new rules read
these **verbatim**, so they cannot drift from what `ax_dispatch` actually
does, by the same construction guarantee A19's pair has via
`_order_n_is_not_live()`
(`test_a20_AR20c_the_guard_TERM_reuses_arc_sel_agid_and_SEL_AGID_VERBATIM`,
a structural term-walk, not a behavioural inference).

**Why a direct reversible pair and not the epoch-lapse idiom
(`ax_impotent`'s own choice).** Same reasoning as A19 §1.1: this question is
not epoch-shaped. A scope reply or a testimony reply can move `arc_sel_agid`
or `SEL_AGID()` with **no epoch bump anywhere in the scene** (proven live,
§2.4's transition test), so a self-monitoring agent asking "do they agree
RIGHT NOW" needs the current truth of the comparison, not a description
valid only until the next measurement.

**Descriptive fields, never read by any guard.** `asked_about_runner_up_agid`
and `dispatch_matches_runner_up` record whether the dispatch target is at
least the goal `ag_ask` named as its *alternative* — the structural-bound
finding (§2.3), stamped as data because a future policy edit could falsify
it and this is exactly the fact that would catch it.

---

## 2. AR20a — CHARACTERIZING DIVERGENCE: A STRUCTURAL BOUND, NOT A SPREAD

### 2.1 The mechanism that produces every divergence on this seed

`VALUE` (`ag_select`, order-1) and `VALUE_N` (`mg_select`, order-N,
`tools/build_arc_magnitude_seed.py::VALUE_N`) are the **same** term — same
`PENALTY`, same policy weights — with exactly two edits: (a)
`headroom_n → orderN_headroom_n`, live only for a goal holding a non-stale
tier-ladder projection, and (b) a scope charge, live only while a
`ArcConstraint{ckind:'scope'}` names a different `sig_seam`. **On the shipped
8-goal pool exactly ONE goal ever carries a ladder**
(`arc.supply....missing_structural_primitive`, "SB_MSP"), and with no scope
constraint ever answered, channel (b) is silent. So on the shipped boot,
divergence has exactly one source: SB_MSP's own repricing.

### 2.2 The shipped-boot scene, reproduced fresh (not re-quoted from WIRE_HANDS)

```
A (ag_ask winner, arc_sel_agid)        = arc.supply....missing_structural_primitive
B (ag_ask alternative, runner_up_agid) = arc.remeasure....row_verdict_seed_only
C (ax_dispatch target, SEL_AGID())     = arc.remeasure....row_verdict_seed_only
arc_sel_margin = 2.30   mg_sel_margin = 26.06
collapses_disagree: true    C_in_{A,B}: true    (C == B)
```

Byte-for-byte the same numbers WIRE_HANDS §2.1 recorded. The standing fact
mints here: `AgendaVerdict{kind:'ask_dispatch_divergence', active:1.0,
asked_about_agid: A, dispatch_target_agid: C, dispatch_matches_runner_up:
1.0}`.

### 2.3 The structural bound, proved and then measured across 17 constructed states

**Claim, proved from the algebra in §2.1 (channel (b) off).** Let `A` be the
order-1 winner and `B` its runner-up. Since `VALUE_N(g) = VALUE(g)` for every
`g` except the single laddered goal, the ranking of *every other goal*
relative to each other is **identical** between the two collapses. Two
cases: if `A` is the laddered goal, the best of "everything else" under
either collapse is exactly `B` by definition of runner-up, so
`C = argmax(VALUE_N(A), VALUE(B)) ∈ {A, B}`. If `A` is *not* the laddered
goal, the ladder discount can only ever **decrease** the laddered goal's
value (it is a `1.0`-tier-survival product, never a bonus), so it can never
overtake `A`, which already beat it under order-1 — hence `C = A`. **In
either case, `C ∈ {A, B}`, with no scope constraint in play.** This is not
an empirical pattern; it follows from the shipped `VALUE_N` term.

**Measured across every constructed state.** The depletion sweep (A14's own
`_leave_pool` mechanism, one goal removed at a time, both with and without
the ladder) plus the shipped-boot scene: **17 states, `C ∈ {A, B}` in all
17** (`results/arc6_ask_dispatch_safety.json →
AR20a_structural_bound_summary`, `bound_held_every_step: true`). Divergence
(`A ≠ C`) itself occurred in exactly 2 of the 17 readings (both the same
underlying scene, counted once in the sweep and once in the shipped-boot
reproduction) — i.e. **divergence occurs precisely when, and only when, the
laddered goal SB_MSP is both in the pool and the order-1 winner**; remove it
and the two collapses agree on every remaining state, with or without the
ladder:

| step (goals removed, ladder ON) | A | B | C | disagree | C∈{A,B} |
|---|---|---|---|---|---|
| none (shipped boot) | SB_MSP | row_verdict | row_verdict | **yes** | yes |
| −SB_MSP | row_verdict | budget | row_verdict | no | yes |
| −SB_MSP,row_verdict | budget | seam_b | budget | no | yes |
| −…,budget | seam_b | seam_d | seam_b | no | yes |
| −…,missing_dimension | seam_b | seam_d | seam_b | no | yes |
| −…,seam_b | seam_d | tier0 | seam_d | no | yes |
| −…,seam_d | tier0 | valuelayer | tier0 | no | yes |
| −…,tier0 (1 left) | valuelayer | valuelayer | valuelayer | no | yes |

(the no-ladder sweep is the same 8 removal steps with `A == C` at every
single one, i.e. the two collapses are identical throughout when nothing is
ever discounted — the expected control, confirmed live).

### 2.4 The fact clears with no epoch bump, exactly like A19's own transition test

Starting from the divergent scene (fact active), removing SB_MSP from the
pool (the validated `headroom_n → 0` pool-exit, never `status → 'retired'`)
converges the two collapses on the same winner (`row_verdict_seed_only`) in
the very next `run_rules()` pass, and the **same node** flips `active` from
`1.0` to `0.0` with the measurement epoch unchanged
(`test_a20_AR20a_the_fact_CLEARS_when_the_collapses_AGREE_no_epoch_bump`,
green).

---

## 3. AR20b — THE ADVERSARIAL SCENE, DESIGNED TO MAKE DIVERGENCE BITE

Two probes, both constructed to be the sharpest test available, both real
(no hand-set attrs standing in for a mechanism — `attach_constraint_reply`
and `attach_reply` are the adapter's own translations, the same ones every
prior rung in this arc used).

### 3.1 Probe (i) — trying to break the structural bound via the scope channel

§2.3's proof holds **only** while channel (b) (scope) is silent. The scope
charge is the *only* other repricing lever this seed ships, so the sharpest
adversarial construction is a scope declaration engineered to knock the
`ax_dispatch` target (B, `row_verdict_seed_only`) out of scope while
exempting a currently-buried goal (`SB_BUDGET`) — the one shot most likely to
promote a genuine third goal to `C`:

```
before (no scope):  VALUE_N(row_verdict) = 7.7      VALUE_N(SB_BUDGET) = -25.0
                     dominance margin = 32.7
scope reply: con_kind='scope', scope_seam='budget'  (SB_BUDGET exempted;
                                                      row_verdict CHARGED -25)
after:               VALUE_N(row_verdict) = -17.3    VALUE_N(SB_BUDGET) = -25.0
                     C stays row_verdict.  bound held.  margin by which it
                     held: 32.7 - 25.0 = 7.7
```

**The bound holds, but it is fragile, and the fragility is now a number, not
a guess.** `w_out_of_scope` (the authored charge weight) is `25.0`;
`row_verdict`'s natural dominance over the strongest exempted alternative is
`32.7`. Since `25.0 < 32.7`, a single scope declaration cannot flip the
winner-of-the-rest under the **current** policy weights — but a future edit
to `w_out_of_scope` (or to any weight that narrows this margin below `25.0`)
would. This is exactly the "not a structural impossibility, a currently-true
empirical fact about the authored weights" honesty this arc's culture
requires (echoing the impotence campaign's own §9 item 1 on `PENALTY`).

### 3.2 Probe (ii) — does a human's answer to `ag_ask` change what executes?

The sharpest test of "does the divergence mislead a human/operator": reply
to `ag_ask`'s own literal rendered question and measure whether the reply
has **any** causal path to what `ax_dispatch` acts on.

```
question rendered to the human:
  "I hold two arc goals I cannot separate. (A) ...missing_structural_
  primitive -- headroom 42 of 53.0 tasks. (B) ...row_verdict_seed_only --
  headroom 11.0 of 15.0 tasks. Their values differ by only 2.3... What
  would have to change for one of these to be worth trying?"

control (no reply ever sent):     ExecOrder minted for row_verdict_seed_only
                                   (selected_by: order_n_mg_select)
after a real, unconditioned reply to the SAME question:
                                   ExecOrder minted for row_verdict_seed_only
                                   (selected_by: order_n_mg_select)
dispatched_goal_unchanged_by_the_reply: true
mg_sel_agid_moved: false
```

**The reply provably has zero effect on what dispatches, on this scene.**
Traced to the mechanism, not merely asserted: `ag_ask`'s reply mints a
testimony `GoalResidual` keyed to the region of `A` — `sig_seam:
'missing_structural_primitive'` — while the dispatch target `C`'s own region
is `sig_seam: 'row_verdict'` (`AR20b_region_comparison`, `regions_match:
false`). `PENALTY` is the one term `VALUE` and `VALUE_N` share unedited,
and a testimony reply can only ever charge a goal whose signature matches the
region asked about (AG-5's own finding, "an unconditioned answer penalises
the region it is about, by weight, regardless of content") — so a reply
about `A`'s region structurally cannot reach `C` unless the two share a
signature, which on this scene they do not.

**The honest reading.** Nothing "broke" in a graph-correctness sense — no
wrong artifact executes, no stale evidence is acted on beyond what `_armed`'s
existing two-tick agreement already guards against. The finding is narrower
and still real: **a human reading `ag_ask`'s question reasonably infers that
answering it bears on what the agent does next; on the measured scene it
does not, at all, regardless of content.** Combined with WH2's own finding
that dispatch happens in the same synchronous `run_rules()`/`arm()` sequence
as the ask, with no pause for a reply built into the loop, the ask's
practical function has degraded from "informs the next action" to "records
an observation nothing downstream consumes for action" — exactly the "the
ask is now mostly irrelevant" language WIRE_HANDS already used, now measured
rather than asserted.

---

## 4. AR20c — THE GO/NO-GO DECISION, AGAINST THE BAR REGISTERED BEFORE THE ANSWER WAS KNOWN

The amendment's own criterion: **GO iff** (i) divergence is real, and (ii)
the fix is buildable in A19's exact cheap shape. **NO-GO iff** either fails,
**in particular** NO-GO (not a weaker build) if the only buildable fix
requires touching `ag_ask`.

- **(i) — MET.** §2.2 reproduces WIRE_HANDS' own divergence fresh; §2.3's
  sweep confirms it is not a one-off.
- **(ii) — MET, verified rather than assumed.** Zero new DSL Term (`SEL_AGID()`
  and `arc_sel_agid` both pre-exist); zero new node/edge type (`AgendaVerdict`
  + `has_agenda_verdict` already declared productions); zero new adapter
  function (`domains/arc_executor.py` byte-identical to `HEAD`, checked);
  zero edit to `ag_ask`/`seeds/arc_goals.json` (checked structurally, §5.3);
  zero change to `ax_dispatch`'s own dispatch decision — re-run live on both
  the WH1 scene (order-N dispatches `row_verdict_seed_only`,
  `selected_by: order_n_mg_select`, byte-identical) and the WH3 scene
  (order-1 fallback dispatches the same goal after a reply,
  `selected_by: order_1_ag_select`, byte-identical), both **with the two new
  rules installed** (§5.2 below).

**Decision: GO.** Built exactly the two-rule pair described in §1.

The amendment's escape hatch — build nothing if AR20b reveals a genuinely
bad outcome an `AgendaVerdict` fact could not surface — was checked and not
triggered: §3.2's finding (the reply is causally inert) is precisely the
kind of fact `dispatch_target_agid`/`asked_about_agid` on the new verdict
now surfaces directly, without needing `ag_ask` to change at all.

---

## 5. AR20d — NO REGRESSION. A LIST OF NODE IDS, NEVER A COUNT.

Both arms below ran on the **same binary** (`c5e50801d48a`) in this
worktree; the **before** arm was measured first, before any file in this
rung was touched (and recovered once from the documented timeout hazard,
§6).

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 79 passed, 1 failed (80 collected) | **90 passed, 1 failed (91 collected)** | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` | 28 / 28 | 28 / 28 | — |

The executor suite's collected count rises **80 → 91**: 12 new `test_a20_*`
gates, zero removed, one pin inverted (§5.1). Both pre-existing reds are the
**same two node ids every rung since A12.1 has recorded** — `results/`
untracked in this checkout, and this engine's short sha not in `test_gr4`'s
three-entry allowlist — neither this rung's to fix, neither touched.

### 5.1 One pin inverted, named, not silently removed — the WH1/A18/A19 precedent, a fourth time

`test_a19_AR19d_the_new_rules_are_the_ONLY_addition_to_the_seed` asserted the
seed's rule list was EXACTLY the eight names A19 shipped. A20 adds a ninth
and tenth (`ax_ask_divergence_active`, `ax_ask_divergence_cleared`), so the
exact-list assertion is now false by construction — inverted to a **prefix**
check (`names[:8] == [...]`) with a docstring explaining why, mirroring
A19's own treatment of A18's pin.
`test_a20_AR20d_the_new_rules_are_the_ONLY_addition_to_the_seed` now asserts
the full ten-name list, the version (`1.6.0`), and re-runs the emitter's own
`--check`.

### 5.2 Dispatch behaviour re-verified live, not merely claimed unchanged

`test_a20_AR20c_dispatch_behaviour_is_UNCHANGED_WH1_scene` and
`test_a20_AR20c_dispatch_behaviour_is_UNCHANGED_WH3_scene` re-run WIRE_HANDS'
own two live scenes with the new rules installed: order-N still dispatches
`row_verdict_seed_only` with `selected_by: order_n_mg_select` on the WH1
scene; order-1 still dispatches the same goal with
`selected_by: order_1_ag_select` on the WH3 scene, after a reply. Both
byte-identical to WIRE_HANDS' own recorded outcomes.

### 5.3 The source audit and the `ag_ask` freeze — both checked structurally

- `test_a20_AR20d_the_adapter_is_BYTE_IDENTICAL_to_HEAD` — `domains/
  arc_executor.py`, whole-file byte-identical to `HEAD`.
- `test_a20_AR20d_the_seeds_below_this_rung_including_arc_goals_are_still_
  UNTOUCHED` — `seeds/arc_goals.json` (i.e. `ag_ask` itself),
  `seeds/goal_residuals.json`, `seeds/program_synthesis.json`,
  `seeds/arc_magnitude.json`, `seeds/arc_decompose.json`, and their adapters
  — all byte-identical to `HEAD`. `tools/build_arc_goals_seed.py --check`
  green.
- `test_a20_AR20d_every_prior_rule_body_is_UNCHANGED` — the eight pre-A20
  rule bodies in `seeds/arc_executor.json`, diffed against `HEAD`'s own
  emitted copy, byte-identical.
- `test_a20_AR20c_the_guard_TERM_reuses_arc_sel_agid_and_SEL_AGID_VERBATIM` —
  the exact `Attr(agenda, 'arc_sel_agid')` subterm `ax_dispatch`'s own
  `where` embeds (via `SEL_AGID()`'s `ITE`) is asserted to appear,
  un-re-derived, inside both new rules' `where`.

---

## 6. THE TIMEOUT HAZARD, HIT A SIXTH TIME, RECOVERED CLEANLY

Recorded because the process is the result — the sixth time this exact class
has fired in this arc (WIRE_HANDS §7.5, REARM_DEADLOCK §7.1/§7.2,
SILENT_FALLBACK §6). The first baseline invocation of
`test_arc_executor_migrated.py` in this rung ran under the tool's default
2-minute timeout, not the `live_run` fixture's real ~140 s duration. The
runner was `SIGKILL`ed mid-flight inside its own `try`, so its
`finally`-based restore never ran, leaving `seeds/program_synthesis.json`
patched (`5aef8fdb…` instead of `HEAD`'s `4e866340…`) and
`results/arc6_verdict_before.json` overwritten by the killed run's own
`before` arm (fresh mtime, sha `3a76f2bd…` instead of the pristine
`ed90bf28…`).

**Recovery.** `seeds/program_synthesis.json` restored via `git checkout --`
(git is the authority for a tracked file), confirmed back at `4e866340…`.
`results/arc6_verdict_before.json` is untracked (gitignored, shared with the
canonical tree via the standard symlink), so it was recovered from the
runner's own crash-stash: **seven independent `/tmp/arc6_remeasure_*`
stashes**, spanning from an earlier rung's runs through this rung's own kill
(the newest, `q66xex6x`, created at the exact kill time), were checked by
sha and **all seven agreed** on `ed90bf281bd8dc812a10a75cf85b8935843296c98d
75290acc038a115f6aa7b0`. That value was copied back and reconfirmed. Both
trees' `git status --porcelain` were empty (modulo the expected symlinked
`data`/`results`) before any further measurement, and the re-run baseline
completed cleanly under an explicit, generous tool-level timeout. No
measurement in this document rests on the damaged window.

---

## 7. WHAT BROKE / REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The observability fact is descriptive, not actionable** — the same
   deliberately narrow scope A13/A19 both chose. Nothing reads
   `AgendaVerdict{kind:'ask_dispatch_divergence'}` and does anything about
   it. A graph on which the two collapses have long disagreed now SAYS so;
   it still acts exactly as it did before.
2. **The structural bound (§2.3) is a fact about the CURRENT `ArcMagPolicy`
   weights, not an engine-level guarantee.** It was proved from the shipped
   `VALUE_N` term and confirmed on 17 constructed states, but a future edit
   to `w_out_of_scope`, or a second laddered goal ever appearing in the
   pool, would need to be re-checked against the same proof — the new
   `AgendaVerdict` fact would still mint correctly in that world (it does
   not depend on the bound holding), but the **bound itself** is not
   asserted anywhere as a standing invariant, only measured here.
3. **Only one adversarial lever (scope) was tried against the bound.** The
   testimony-repricing channel was also investigated (§3.2) but for a
   different question (causal reach of a reply); a combined multi-reply,
   multi-scope-declaration sequence chaining several real mechanisms in
   series was not attempted, and might close the 7.7 margin faster than a
   single declaration does. Not built here because the amendment's own bar
   (AR20b) asked for one designed adversarial scene per probe, not an
   exhaustive search of the construction space, and the single scope probe
   already gave a load-bearing, quantitative answer.
4. **AR20b's "causal reach" finding (§3.2) was measured on the shipped-boot
   scene specifically (region mismatch between A and C).** A scene engineered
   so `A` and `C` share a signature region (constructible via the same
   sig-seam mechanism, not attempted here) would presumably show the reply
   DOES move `mg_sel_agid` — this is expected from the mechanism (§3.2's own
   `PENALTY`-sharing argument) and was not separately re-verified live,
   because the amendment's bar was to test the sharpest available
   *disconnect*, not to also demonstrate the connected case, which A19's own
   citation of AG-5 §8.3 already covers for the order-1-only channel.
5. **`ag_ask` and `ax_dispatch` still diverge — this rung makes it visible,
   it does not close it.** Per the amendment's own preference and the
   evidence gathered (the divergence is bounded and, on every constructed
   scene, causally inert on what executes), touching `ag_ask` was
   deliberately not attempted. If a future rung ever finds a scene where the
   bound breaks or a reply's effect is genuinely misleading rather than
   inert, that would be the evidence this amendment named as the bar for
   reconsidering.

---

## 8. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | +2 rule builders (`_r_ask_divergence_active`, `_r_ask_divergence_cleared`), +2 helpers (`_dispatch_differs_from_ask_winner`, `_ask_divergence_verdict_active`), registered in `_rules()`, version 1.5.0 → 1.6.0, module docstring extended. Every pre-A20 rule builder unedited. |
| `seeds/arc_executor.json` | **regenerated**, v1.6.0, 10 rules, gated byte-identical against its emitter |
| `tests/test_arc_executor_migrated.py` | +12 `test_a20_*` gates; 1 pin inverted (`test_a19_AR19d_the_new_rules_are_the_ONLY_addition_to_the_seed`, prefix-checked with a docstring, the WH1/A18/A19 precedent a fourth time) |
| `scripts/arc6_ask_dispatch_safety_measure.py` | new — the measurement runner: the depletion sweeps, the structural-bound summary, the scope-channel adversarial probe, the reply-causality probe, region comparison, twin-run determinism — all in one process, 0.47 s (no live subprocess needed) |
| `results/arc6_ask_dispatch_safety.json` | the artifact, engine-stamped, carrying every trace quoted above |
| `domains/arc_executor.py` | **UNCHANGED** — byte-identical to `HEAD`, checked (§5.3) |
| `PROGRAM_SYNTHESIS_ARC6_ASK_DISPATCH_SAFETY.md` | this file |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | **amendment A20** appended |

**One thing in this worktree's `git status` that is NOT part of the change,
flagged so a reviewer does not stage it:** `data` and `results` appear as
untracked — they are **symlinks** into the canonical tree (the standard
practice every arc-6 rung since A12.1 has used). `runners/dsl/python/
substrate_rs/_native.abi3.so` is **not** modified in this worktree — it was
copied in already built, unlike WIRE_HANDS, which had to rebuild.

**Nothing in the canonical tree changed** beyond this rung's own registered
`PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment. `git status --porcelain`
there is empty (after the §6 recovery) and its `_native.abi3.so` is
byte-identical throughout.

---

## 9. REPRODUCE

```bash
# --- verify main's tip, then the worktree ---------------------------------
git -C /home/matt/ozmadev/ocelot log --oneline -1 main   # 207d764...
git worktree add --detach /home/matt/ocelot-arc6-ask-dispatch-safety 207d764
cd /home/matt/ocelot-arc6-ask-dispatch-safety
git checkout -b arc6-ask-dispatch-safety
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine (already built) --------------------------------------------
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
touch runners/dsl/python/substrate_rs/_native.abi3.so   # mtime hazard
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe ---------------------------------------------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- the seed is EMITTED, never hand-edited --------------------------------
python3 tools/build_arc_executor_seed.py          # writes seeds/arc_executor.json (v1.6.0)
python3 tools/build_arc_executor_seed.py --check  # "up to date"

# --- the measurement (all probes, ~0.5s, no live subprocess) --------------
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:.:scripts \
  python3 scripts/arc6_ask_dispatch_safety_measure.py
#   -> results/arc6_ask_dispatch_safety.json

# --- the gate.  CRITICAL: this suite's live_run fixture is a REAL ~140s
#     re-measurement -- ALWAYS an explicit, generous tool-level timeout,
#     NEVER a shorter one (SS6 above; the sixth time this hazard has fired
#     in this arc) --------------------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 90 passed, 1 failed (pre-existing)

# --- the regression arms.  test_goal_residual_migrated.py includes a REAL
#     ~80s live MBPP battery -- same timeout discipline ------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_goals_migrated.py \
    tests/test_goal_residual_migrated.py tests/test_arc6_valuelayer_migrated.py \
    tests/test_arc_magnitude_migrated.py tests/test_arc_decompose_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf
    # 172 passed, 1 failed (pre-existing), 1 skipped
```

**`--confcutdir=$PWD` on every pytest invocation** — same reason as every
prior arc-6 rung: this worktree is not nested inside the canonical repo.

**Engine provenance.** Every number in this document was produced by
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`,
resolving from inside `/home/matt/ocelot-arc6-ask-dispatch-safety`.

**Contamination.** No MBPP test-split content was read by anything this
rung added — `ax_ask_divergence_active`/`ax_ask_divergence_cleared` are pure
graph arithmetic over two Terms (`SEL_AGID()`, `arc_sel_agid`) that already
existed and were already load-bearing. Nothing new entered a codebook, a
route table, or a cue table.
