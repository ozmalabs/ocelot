# ARC 6 — A18: THE RE-ARM DEADLOCK, CLOSED WITHOUT RUNNING ANYTHING

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A18** (`AR18a`-`AR18d`),
registered **before** this build.
**Base commit:** `c4f7b3a` (detached worktree `/home/matt/ocelot-arc6-rearm-deadlock`,
branch `arc6-rearm-deadlock`).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`,
copied into this worktree and **verified resolving from inside it** —
`substrate_rs._native.__file__` is
`/home/matt/ocelot-arc6-rearm-deadlock/runners/dsl/python/substrate_rs/_native.abi3.so`
— the **same** binary A15/A16/A17 measured on (the box's committed `.so` has
not moved since). Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.4.0** (bumped from v1.3.0), emitted by
`tools/build_arc_executor_seed.py` and gated byte-identical against it — **6
rules** (the shipped 5 plus `ax_world_probe_epoch`).
**Gate:** `tests/test_arc_executor_migrated.py` — **69 collected, 68 passed,
1 failed (pre-existing)**; `tests/test_arc_decompose_migrated.py` and the
other four arc-6 suites — **174 collected, 172 passed, 1 failed
(pre-existing), 1 skipped**.

**SCOPE: exactly AR18a-AR18d — measure whether the re-arm deadlock
(`PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md` §5) still reproduces on the current
shipped graph, and, if so, build a second epoch producer that does not run
anything, without weakening `ax_rearm`'s own anti-oscillation latch.** The
silent order-N fallback, `ag_ask`/`ax_dispatch` general collapse-agreement,
`gr_condition_lapse`'s vocabulary, `results/arc6_import_impedance.json`, a
third `ExecClass`, and `source_claim`'s structural unresolvability are all
**untouched**, per the task's explicit boundary.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR18a — does the deadlock still reproduce, tested directly, before any fix?** | **YES — REPRODUCES, AND IS WORSE THAN "ONE EXECUTABLE GOAL"** | A real live execution retired the row-verdict goal; the OTHER shipped `ExecClass` (structural) was confirmed NOT organically stale on this engine, so the pool held **zero** executable `re_measure` goals at that moment — not one. A genuine world change (the fresh artifact removed) left the goal `retired`, out of the pool, epoch frozen at `"1"`, across **six** repeated probe/fixpoint cycles. §2 |
| **AR18b — the fix must not weaken anti-oscillation** | **PASS** | EXECUTOR.md's own four-cell `latch_cells` scene (churn does not re-mint; a single genuine re-failure does not re-mint; re-failed+epoch-advanced DOES re-mint; the world restoring returns to terminal) reproduces **byte-identically** with the new mechanism installed and live. A **second**, independent four-cell walk built on the new mechanism shows the SAME discriminator holds at the probe grain: one externally-triggered probe does not confirm drift; two separate ones do. §4, §5 |
| **AR18c — the fix closes the deadlock, demonstrated live, without ever running an executable order** | **PASS** | Starting from the exact AR18a stuck state, two SEPARATE calls to the adapter's existing `refresh_evidence_facts` (no subprocess, no `run_order`, no hand-poked `bump_measure_epoch`) confirm the drift; the adapter's new `world_probe_advance_epoch` bumps the epoch mechanically; the next fixpoint re-arms the goal (`rearm_count` 1.0 → 2.0). Exactly one `ExecOrder` ever reached `ran`/`closed` on the whole graph — `live_run`'s own, from EX1/EX2. §5 |
| **AR18d — no regression** | **PASS** | `test_arc_executor_migrated`: 68/69 (1 pre-existing red). The other five arc-6 suites combined: 172/173 (1 pre-existing red) + 1 skipped. Both reds are the **same two node ids** every rung since A12.1 has recorded. `seeds/arc_goals.json`, `seeds/goal_residuals.json`, `seeds/arc_magnitude.json`, `seeds/arc_decompose.json`, `seeds/program_synthesis.json` byte-identical to `HEAD`. `ROUTE`/`_routable`/`_dispatchable`/`_cue_matches`/`_r_dispatch`/`_r_rearm`/`_armed`/`_in_pool` in `tools/build_arc_executor_seed.py`, and `run_order`/`arm`/`reingest_evidence` in `domains/arc_executor.py`, are **AST-identical** to `HEAD`'s own source for the same functions. §6 |

**The one thing worth reading if you read nothing else.** The deadlock
EXECUTOR.md described with "exactly one executable goal" is, on the current
post-A17 graph, actually reached with **zero**: A15's own second `ExecClass`
does not give the loop a standing reserve goal to fall back on — its own
extension probe already showed both `re_measure` goals retire in the
ordinary course of execution and leave **no permanent trace** on the pool.
The fix does not touch `ax_rearm`. It gives the epoch a second, narrower
producer — "the world was checked twice, independently, and it still says
the same thing" — that is structurally incapable of firing on a single
observation, which is exactly the property that keeps it from reintroducing
the churn `ax_rearm`'s own latch was built to prevent.

---

## 1. THE PROBLEM, RESTATED, AND WHY IT NEEDED RE-MEASURING NOT RE-QUOTING

`PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md` §5, quoted because it is this rung's
charter: *"Cell D needed an epoch bump from OUTSIDE this loop. The executor
is the epoch's producer, but it only produces one by RUNNING a goal, and a
retired goal is not in the pool to be run. With exactly one executable goal,
a genuinely re-failed condition cannot bring it back on its own."*

Five rungs landed since (A11-A17) without touching this. Two of them changed
the shape of the graph the deadlock lives on:

- **A15** added a SECOND `ExecClass` (the structural-ceiling residual,
  `arc6.structural.enum_op_table`) — a second thing that CAN be run.
- **A17** added a THIRD retirement mechanism (`mg_tier_retire`, for
  `decomposition_tier` children) — a second way a goal can LEAVE the pool
  without being run.

Either of these could, in principle, have already defused the deadlock —
more executable capability sitting in reserve, or fewer things needing the
epoch to move. Neither did, and the reasons are structural, read from the
code rather than assumed:

1. **`arc_measure_epoch` has exactly ONE producer anywhere in the tree, and
   it does not care WHICH order ran.** `domains/arc_executor.py::run_order`
   calls `agi.bump_measure_epoch(sub)` once, unconditionally, after ANY
   successful run. `grep -rn bump_measure_epoch domains/*.py` (pre-fix)
   returns exactly this one call site. A15's second `ExecClass` does not add
   a second epoch producer — it adds a second thing `run_order` can be asked
   to run, through the SAME function.
2. **A17's `mg_tier_retire` is a retirement mechanism, not an epoch
   producer.** `domains/arc_decompose_ingest.py` never calls
   `bump_measure_epoch` and never calls `run_order` (zero hits by grep). It
   retires a `decomposition_tier` child via the same `headroom_n -> 0`
   pool-exit `ax_rearm` never inspects, entirely outside the
   executor/dispatch machinery.
3. **A15's own "bonus extension probe"
   (`PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md` §6) already measured, live,
   that the NATURAL trajectory with BOTH `ExecClass`es reaches a state with
   ZERO executable goals, not one.** Quoted: *"the FINAL steady-state
   composition, once both retire, [is] composition-identical to A14's own
   already-measured 'state 1' — pool_n=7 ... Once a re_measure goal retires
   it leaves no permanent trace on POOL()."* So the ordinary end state of
   this loop, after everything currently executable has run, is the
   deadlock's precondition made WORSE than EXECUTOR.md described it — not a
   corner case reachable only by construction.

This amendment tested that reasoning directly rather than trusting it, per
the task's own instruction not to assume either way.

---

## 2. AR18a — THE DEADLOCK, MEASURED LIVE, BEFORE ANY FIX EXISTED

`scripts/arc6_rearm_deadlock_measure.py` was run **before** `domains/
arc_executor.py`, `tools/build_arc_executor_seed.py` or `seeds/
arc_executor.json` had been touched by this rung — the only prior artifacts
were this file's own eventual existence and the A18 prereg amendment. It
reuses the SAME `live_run`-shaped scene `tests/test_arc_executor_migrated.py`
already gates: boot, let the collapse settle, answer the one open question
(conditioned), dispatch, and **run the row-verdict re-measurement for real**
(139.8 s), then walk the graph through repeated real-world perturbations.

```
0_before_execution               status=pursued in_pool=True  epoch=0 stale=1.0
1_after_real_execution_retired   status=retired  in_pool=False epoch=1 stale=0.0
2_churn_3x_run_rules             status=retired  in_pool=False epoch=1 stale=0.0
3_refailed_ONE_probe             status=retired  in_pool=False epoch=1 stale=1.0
4_repeat_probe_1..5              status=retired  in_pool=False epoch=1 stale=1.0  (x5, identical)
5_world_restored                 status=retired  in_pool=False epoch=1 stale=0.0
```

**Confirmed at step 1: zero executable goals, not one.** The structural
residual's own `stale` reads `0.0` at this point (organically holding on
this engine, matching A15's own finding) and no `re_measure`-kind goal other
than the retired one is present in the pool — the EXACT precondition
EXECUTOR.md's own deadlock needs, reached by the ordinary course of one real
execution, no fixture arranging it.

**Confirmed across steps 2-4 (six repeated cycles): the residual genuinely
re-fails (`stale` 0.0 → 1.0, real — the artifact was actually moved off
disk) and NOTHING internal to the unmodified tree ever moves the epoch or
the goal's status.** Not once, not on the sixth repeat. `results/
arc6_rearm_deadlock_before_fix.json` carries the full trace, engine-stamped
(`c5e50801d48a…`), and is read back directly by
`test_a18_AR18a_the_deadlock_REPRODUCED_live_on_the_UNFIXED_graph` rather
than re-derived.

**Protected files.** `results/arc6_verdict_before/after/pricing.json` and
`seeds/program_synthesis.json` were sha-verified byte-identical
before and after this run (the runner's own `finally` restore, checked
against `HEAD`/the pre-run shas, not merely against the runner's own claim).

---

## 3. THE MECHANISM

**One new rule, `ax_world_probe_epoch` (`seeds/arc_executor.json`), and a
small mechanical addition to the adapter's existing `refresh_evidence_facts`
— no change to `ax_rearm`, no new DSL Term, no new Rust.**

### 3.1 The adapter carries its own prior reading across the probe boundary

`refresh_evidence_facts` already re-probes the world every time it is
called (file presence, content sha, the value-layer probe) — it is what
EX4's own cell C already used to demonstrate a genuine re-failure, and
EXECUTOR.md's own docstring already calls it *"pure measurement... called
once per loop iteration by the driver."* It now does one more mechanical
thing, at the START of every call, BEFORE it overwrites anything:

```python
for n in sub.nodes("GoalResidual"):
    sub.set_attr(n, "stale_at_last_probe", sub.node(n)["attrs"].get("stale"))
```

A plain read and a plain `set_attr` — the `ARM_CARRY` precedent
(`arm`, the tick-boundary stamp carry `ax_dispatch`'s own two-tick fix
introduced) applied at the PROBE-CALL boundary instead. It decides nothing;
it hands the rule the one thing it needs: what the PREVIOUS, separate probe
found, as opposed to what THIS one just found.

### 3.2 The rule: confirmed only on two separate observations

```python
"match": HUB + [["agenda", "has_arc_goal", "g"], ["r", "remeasure_goal", "g"]],
"where": AND(
    EQ(A(V("g"), "status"), L("retired")),
    EQ(A(V("r"), "stale"), L(1.0)),
    EQ(A(V("r"), "stale_at_last_probe"), L(1.0)),
    NOT(EQ(A(V("g"), "retired_epoch"), L(None))),
    NOT(EQ(A(V("g"), "retired_epoch"), L(CONSUMED))),
    EQ(A(V("g"), "retired_epoch"), MEASURE_EPOCH()),
),
"effects": [
    ["set_attr", "g", "world_drift_confirmed", 1.0],
    ["set_attr", "g", "world_drift_confirmed_epoch", T(MEASURE_EPOCH())],
],
```

Same match shape as `ax_rearm`. **A single probe cannot satisfy this** —
`stale_at_last_probe` still holds the PRE-drift reading the first time
`stale` flips to `1.0`, so the conjunction fails on the first sighting by
construction, not by a guard bolted on afterward. The last clause
(`retired_epoch == MEASURE_EPOCH()`) means the rule only ever has anything
to say while the clock is genuinely stuck since retirement — the moment
anything else advances the epoch, `ax_rearm`'s own conjunction is already
satisfied and this rule declines.

### 3.3 The adapter's mechanical half

```python
def world_drift_confirmed_goals(sub) -> List[str]:
    return sorted(sub.node(n)["attrs"].get("agid") for n in sub.nodes("ArcGoal")
                  if sub.node(n)["attrs"].get("status") == "retired"
                  and sub.node(n)["attrs"].get("world_drift_confirmed") == 1.0)

def world_probe_advance_epoch(sub) -> Optional[dict]:
    confirmed = world_drift_confirmed_goals(sub)
    if not confirmed:
        return None
    before = agi.measure_epoch(sub)
    agi.bump_measure_epoch(sub)
    return {"triggered_by": confirmed, "epoch_before": before,
            "epoch_after": agi.measure_epoch(sub)}
```

A pure query (the same shape as `pending_orders`) and a mechanical act (the
SAME `bump_measure_epoch` `run_order` already calls). It decides nothing —
the rule already decided; this reads the flag and performs the act, exactly
`ax_dispatch` → `run_order`'s own division of labour, one level down.

### 3.4 Why this design, and what it was checked against before being written

**Investigated and rejected first:** coupling the epoch bump directly to
the SAME single detection event `stale` is computed from (i.e. bump the
epoch the instant a probe finds re-failure). This was rejected BEFORE
writing any rule, because it collapses EX4's own cell C into cell D: cell
C's existing gate calls `refresh_evidence_facts` exactly once after moving
the artifact, specifically to prove a SINGLE genuine re-failure does not,
by itself, re-mint. A design that lets one probe both detect and grant
would make that bar impossible to state, let alone pass. The two-probe
persistence requirement is the direct analogue of `ax_dispatch`'s own
two-tick agreement fix (EXECUTOR.md §8 item 1) — reused at the
externally-triggered-probe grain instead of the internal-fixpoint-tick
grain, because that is the same shape of hazard (reading a value before it
has settled) at a different scale.

**The tradeoff, named rather than hidden.** `arc_measure_epoch`'s
documented meaning was *"a measurement happened"* — narrowly, "a
remeasurement subprocess ran." This rung widens that to *"a measurement OR
a confirmed, twice-observed, genuine drift happened."* Both are real events
probed from the world, never authored — but every OTHER epoch-gated
mechanism (the testimony reply's one-epoch life, the unanswered question's
lapse, `ax_impotent`'s own lapse) now also expires slightly more readily,
on an event cheaper than a full remeasurement. AR18b (below) is the check
that this widening does not go further than the two-probe floor — a single
detection must still not be enough, in this design or any other, and it
was gated on precisely that.

---

## 4. AR18b — ANTI-OSCILLATION, RE-CHECKED, NOT MERELY RE-ASSERTED

EXECUTOR.md's own five-cell `latch_cells` walk (A: after execution, B:
3× churn, C: genuinely re-failed at the SAME epoch, D: re-failed AND epoch
advanced, E: world restored) was re-run **with the new mechanism installed
and live on the graph** — not a fixture that skips it.

| cell | status | in_pool | epoch | stale | rearm_count |
|---|---|---|---|---|---|
| A — after execution | retired | False | 1 | 0.0 | — |
| B — churn ×3 | retired | False | 1 | 0.0 | — |
| C — refailed, SAME epoch | retired | False | 1 | 1.0 | — |
| D — refailed AND epoch advanced (manual bump) | non-terminal | True | 2 | 1.0 | 1.0 |
| E — world restored | retired | False | 2 | 0.0 | 1.0 |

**Byte-identical to EXECUTOR.md's own recorded shape.** Traced through the
new code by hand and confirmed live: at cell C, `refresh_evidence_facts` is
called for the SECOND time ever on this graph (the first was inside
`live_run`) — `ax_world_probe_epoch`'s guard needs `stale_at_last_probe ==
1.0`, and at cell C it is still `0.0` (the value from cell A/B), so the
guard cannot fire. `world_drift_confirmed` is never set at cell C; nothing
about it changed.

**A second, independent four-cell walk, built on the mechanism itself.**
`world_probe_cells` continues the SAME live graph from cell E (retired
again, epoch 2) with no subprocess anywhere in it:

| cell | status | in_pool | epoch | stale | world_drift_confirmed | rearm_count |
|---|---|---|---|---|---|---|
| F — start (= cell E) | retired | False | 2 | 0.0 | — | 1.0 |
| G — refailed, FIRST probe only | retired | False | 2 | 1.0 | not 1.0 | 1.0 |
| H — refailed, SECOND separate probe | retired\* | False | 2 | 1.0 | **1.0** | 1.0 |
| I — after the second producer fired | non-terminal | True | **3** | 1.0 | 1.0 | **2.0** |
| J — world restored again | retired | False | 3 | 0.0 | 1.0 | 2.0 |

\*status at H is read BEFORE `world_probe_advance_epoch` is called in that
same step; the epoch bump happens between H and I.

`test_a18_AR18b_a_SINGLE_world_probe_does_NOT_confirm_drift_or_advance_the_epoch`
asserts cell G directly: `world_drift_confirmed != 1.0` and
`axe.world_probe_advance_epoch(s) is None` — **the mechanical epoch-advance
call itself is a no-op after exactly one probe.** This is the discriminator
AR18b names: a design that let one probe be enough would fail this
assertion, not merely read differently in a write-up.

---

## 5. AR18c — THE DEADLOCK CLOSES, AND NOTHING WAS EVER RUN

Continuing the same walk: at cell H, the SECOND separate probe (world still
broken, same as before) makes `r.stale == 1.0` AND `r.stale_at_last_probe ==
1.0` both true for the first time — `ax_world_probe_epoch` fires,
`world_drift_confirmed` is stamped. `axe.world_probe_advance_epoch(s)`
(called mechanically, exactly as the adapter would) returns:

```
{"triggered_by": ["arc.remeasure.arc6.verdict.row_verdict_seed_only"],
 "epoch_before": "2", "epoch_after": "3"}
```

The NEXT `run_rules()` (cell I) is where `ax_rearm` — completely unedited —
sees `retired_epoch ("2") != arc_measure_epoch ("3")` and fires: the goal
re-arms, `rearm_count` goes `1.0 → 2.0`, exactly the SAME re-entry shape
cell D used, driven by a DIFFERENT producer.

**No order was ever run to make this happen.** `test_a18_AR18c_NO_order_
was_EVER_run_to_close_this_deadlock` reads every `ExecOrder` on the graph:
exactly one ever reached `status in ("ran", "closed")` — `live_run`'s own,
from EX1/EX2, 139.8 s, the ONLY subprocess this entire rung's tests ever
invoke. (A SECOND `ExecOrder` node does legitimately get MINTED — never
run — at cell D, because a re-armed goal is again the collapse's winner and
`ax_dispatch`'s own two-tick agreement can be satisfied by the STALE `armed_
*` stamp `live_run`'s original `axe.arm` call left behind; EXECUTOR.md's
own §5 already documented exactly this for cell D as *"the loop working,
not a defect."* Once minted, `ax_dispatch`'s own "at most one OUTSTANDING
order globally" guard blocks a third — this rung neither introduces nor
needs to suppress that pre-existing property, and the test checks the
narrower, correct claim: no order ever reached `ran`.)

**The round trip closes a second time.** Cell J: world restored, `stale`
back to `0.0`, `ag_remeasure_retire` (unedited) fires, `status` back to
`retired`, `retired_epoch` freshly stamped `"3"`, `rearm_count` stays `2.0`
(it must not re-arm a third time on its own) —
`test_a18_AR18c_the_round_trip_CLOSES_again` asserts exactly this.

---

## 6. AR18d — REGRESSION, A LIST OF NODE IDS, NEVER A COUNT

Both arms below ran on the **same binary** (`c5e50801d48a`), in this
worktree; the **before** arm (AR18a's own measurement) was made before any
code file was touched.

| suite | before (baseline) | after (with the fix) | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 60 passed, 1 failed (61 collected) | 68 passed, 1 failed (**69** collected — 8 new AR18 gates) | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` | 28 / 28 | 28 / 28 (1 pin inverted with a docstring, see §6.1) | — |

Both pre-existing reds are the **same two node ids every rung since A12.1
has recorded**: `results/` is untracked in this checkout (`git show
HEAD:results/…` returns empty for a gitignored path) and this engine's
short sha is not in `test_gr4`'s three-entry allowlist. Neither is this
rung's to fix, and neither was touched.

**Confinement, asserted not promised.**

- `seeds/arc_goals.json`, `seeds/goal_residuals.json`,
  `seeds/arc_magnitude.json`, `seeds/arc_decompose.json`,
  `seeds/program_synthesis.json` — byte-identical to `HEAD`
  (`git diff --exit-code`, green).
- `runners/dsl/src/*` — byte-identical to `HEAD` (`git diff`, empty). No new
  Rust.
- `tools/build_arc_executor_seed.py`'s `ROUTE`, `_routable`,
  `_dispatchable`, `_cue_matches`, `_r_dispatch`, `_r_rearm`, `_armed`,
  `_in_pool` — **AST-identical** to `HEAD`'s own source for the same
  functions (`ast.unparse`, compared function-by-function, not a whole-file
  diff — the file as a whole DOES change, by design: it gains
  `_r_world_probe_epoch` and a version bump).
- `domains/arc_executor.py`'s `run_order`, `arm`, `reingest_evidence` — same
  AST-identity check, same result.
- `seeds/arc_executor.json` regenerates byte-identically from its own
  (edited, version-bumped 1.3.0 → 1.4.0) emitter.
- The adapter source audit (`test_a18_AR18d_the_source_audit_still_passes_
  on_the_EDITED_adapter`, mirroring `test_ex6_the_adapter_CANNOT_contain_a_
  hidden_decision`): no `import substrate_rs`, no `.evaluate(`, no
  `run_rules`, no `graph_rewrite`/`make_rule`/`._match`/`._apply`; every
  substrate call in the edited file is one of `add_node` / `node` / `nodes`
  / `set_attr` / `remove_node` / `load_seed_manifest` / `add_edge_unchecked`.

### 6.1 One pin inverted, named, not silently removed — the WH1 precedent, twice

`test_a15_the_seed_added_ZERO_new_rules` (`tests/test_arc_executor_
migrated.py`) asserted the seed's rule set was EXACTLY the five names A15
shipped. A18 adds a sixth (`ax_world_probe_epoch`), so the exact-set
assertion is now false by construction — inverted to a subset check with a
docstring explaining why, and the exact new total is asserted separately
by `test_a18_AR18d_the_new_rule_is_the_ONLY_addition_to_the_seed`.

`test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED` (`tests/test_arc_
decompose_migrated.py`, A17's own gate) asserted `domains/arc_executor.py`
and `tools/build_arc_executor_seed.py` were whole-file byte-identical to
`HEAD` — A17's OWN cost bar, about THAT rung, not a standing invariant.
Inverted to check the SPECIFIC route-matching Term builders A17's own
docstring actually named (`ax_dispatch`/`ROUTE`/`_routable`), read back by
function via `ast` and compared against `HEAD`'s own source for the same
functions — the §6 AST-identity check, reused here rather than duplicated.

Neither pin was silently loosened or deleted; both now assert the SAME
underlying claim their authors intended, against the wider set of files
that now legitimately change.

---

## 7. EVERYTHING THAT BROKE

Recorded because the process is the result (A11-A17's own standing
practice).

1. **The worktree mtime hazard, reproduced a further time.** `git worktree
   add` left every `.rs` source newer than the committed `.so`
   (`domains.engine_provenance.EngineProvenanceError: STALE — 84 .rs newer
   than the binary`), which silently failed 18 tests with `subprocess.
   CalledProcessError` before the cause was read from the actual error
   text. Fixed exactly per the A12.2/A15/A16/A17 playbook: `touch` the
   `.so`, confirm its sha unchanged, confirm zero `.rs` files newer.
   Recorded again because this is now the FIFTH time this exact class has
   been hit in this arc, always on a fresh worktree.
2. **`results/` needed symlinking to the canonical tree, and was not
   present by default** — `ln -s /home/matt/ozmadev/ocelot/results results`
   before any measurement, matching A12.1/A15/A17's own established
   practice. Without it, over 80 tests failed with `FileNotFoundError` or
   "no such goal" (the SPEC-driven boot could not find any of the six
   committed evidence artifacts), which read initially like a large,
   alarming regression and was, in full, an environment-setup step.
3. **The first draft of `test_a18_AR18c_NO_order_was_EVER_run_to_close_
   this_deadlock` asserted the wrong property** (`len(orders) == 1`) and
   failed live: a SECOND `ExecOrder` legitimately mints (never runs) at
   cell D, because a re-armed goal is again the collapse's winner and
   `ax_dispatch`'s two-tick agreement is satisfied by the stale `armed_*`
   stamp `live_run`'s ORIGINAL `axe.arm` call left behind —
   EXECUTOR.md's own §5 already documented exactly this for cell D
   ("status may read `pursued`... that is the loop working, not a
   defect"). Corrected to assert the actual claim (no order ever reached
   `ran`/`closed` a second time) once the mechanism was understood, not by
   suppressing the mint.
4. **`test_a15_the_seed_added_ZERO_new_rules` and `test_ar17_no_new_rust_
   and_ax_dispatch_UNTOUCHED` both needed the WH1 "invert, don't delete"
   treatment** (§6.1) — found by running the full suite, not anticipated in
   advance, though the shape of the fix was already established practice
   in this arc.
5. **Nothing was corrupted, nothing needed recovery.** Every protected-file
   sha (`arc6_verdict_before/after/pricing.json`, `seeds/program_
   synthesis.json`) was checked before AND after every live-touching run in
   this rung (the AR18a measurement, the fix-verification run, the full
   regression sweep) and matched throughout. No timeout was hit; every
   invocation used an explicit, generous tool-level timeout (400-580s) for
   any command containing a live fixture, per A12.2/A14/A15/A17's own
   registered rule.

---

## 8. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The two-probe requirement is a chosen floor, not a proof of
   sufficiency against every possible noise source.** It closes the
   SPECIFIC hazard this rung investigated and rejected (coupling the bump
   to the same single detection event that computes `stale`) and is
   measured to hold against every scene this suite constructs — but it is
   an engineering judgement about how much independence is enough, the
   same way `ax_dispatch`'s own two-tick agreement is, not a formal
   guarantee that no sequence of adapter calls could ever satisfy it
   spuriously.
2. **This does not touch, and does not claim to touch, the impotence gap
   `ax_impotent`/`ag_ask` still have** (A11/A12's own named residual: the
   ask fires on a tie, not on impotence, and the two collapses can still
   read different winners). A18 only ever affects whether a RETIRED goal
   can come back; it says nothing about which goal the collapse picks next
   once it does.
3. **`world_probe_advance_epoch` is exposed as a function, not wired into
   any standing driver loop.** Nothing in the shipped tree calls it
   automatically on a schedule — exactly like `refresh_evidence_facts`
   itself, which EXECUTOR.md's own docstring already described as "called
   once per loop iteration by the driver" without there being a standing
   driver in production. A real deployment would need to decide HOW OFTEN
   to probe; this rung built the mechanism and the gate, not a scheduler.
4. **The seed's now-widened epoch semantics affect every OTHER epoch-gated
   mechanism** (testimony one-epoch life, unanswered-question lapse,
   `ax_impotent`'s own lapse), named explicitly in §3.4 as the tradeoff —
   measured to not weaken the SPECIFIC latch this rung targeted (AR18b),
   but the broader interaction across every consumer of `arc_measure_epoch`
   was not separately swept.
5. **Whether this actually grows A14's real-only impotent-state count is
   NOT measured here**, per the task's own instruction that a full
   impotence-campaign re-sweep need not be repeated unless cheap — and,
   per A15 §8 item 3's own finding (re-quoted in §1 above), a new epoch
   PRODUCER is not the same shape of capability as a new RETIREMENT for a
   `supply_blocker`/`source_claim` goal, so there is no a priori reason to
   expect it would.
6. **The silent order-N fallback, `ag_ask`/`ax_dispatch` collapse
   agreement in general, and `gr_condition_lapse`'s closed vocabulary are
   untouched**, per the task's explicit scope boundary, and none was
   exercised by any scene in this rung in a way that would have required
   touching them.

---

## 9. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | +~60 lines: `_r_world_probe_epoch`, added to `_rules()`, version 1.3.0 → 1.4.0, description text extended. Every OTHER function byte/AST-identical to `HEAD`. |
| `seeds/arc_executor.json` | **regenerated**, v1.4.0, 6 rules, gated byte-identical against its emitter |
| `domains/arc_executor.py` | +~55 lines: the `stale_at_last_probe` snapshot inside `refresh_evidence_facts`, `world_drift_confirmed_goals`, `world_probe_advance_epoch`, module docstring extended. `run_order`/`arm`/`reingest_evidence` AST-identical to `HEAD`. |
| `tests/test_arc_executor_migrated.py` | +~190 lines: 8 new `test_a18_*` gates, 1 pin inverted (`test_a15_the_seed_added_ZERO_new_rules`) |
| `tests/test_arc_decompose_migrated.py` | 1 pin inverted (`test_ar17_no_new_rust_and_ax_dispatch_UNTOUCHED`), now an AST-level check on the specific named functions |
| `scripts/arc6_rearm_deadlock_measure.py` | new, ~180 lines — the AR18a "before any fix" live measurement, no Python decision (reads graph state, writes an artifact, decides nothing about what to build) |
| `results/arc6_rearm_deadlock_before_fix.json` | the AR18a artifact, engine-stamped, read directly by the gate |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | amendment A18 appended, registered before the build |
| `PROGRAM_SYNTHESIS_ARC6_REARM_DEADLOCK.md` | this file |

---

## 10. REPRODUCE

```bash
# --- the worktree ---------------------------------------------------------
git worktree add --detach /home/matt/ocelot-arc6-rearm-deadlock c4f7b3a
cd /home/matt/ocelot-arc6-rearm-deadlock
git checkout -b arc6-rearm-deadlock
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine -------------------------------------------------------------
cp /home/matt/ozmadev/ocelot/runners/dsl/python/substrate_rs/_native.abi3.so \
   runners/dsl/python/substrate_rs/_native.abi3.so
touch runners/dsl/python/substrate_rs/_native.abi3.so   # mtime hazard, §7 item 1
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so
#   c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567

# --- the coherence probe ---------------------------------------------------
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"

# --- AR18a -- the deadlock, measured BEFORE any fix (~140s live) ----------
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/arc6_rearm_deadlock_measure.py
#   writes results/arc6_rearm_deadlock_before_fix.json ; DEADLOCK_REPRODUCES: true

# --- the seed is EMITTED, never hand-edited --------------------------------
python3 tools/build_arc_executor_seed.py          # writes seeds/arc_executor.json (v1.4.0)
python3 tools/build_arc_executor_seed.py --check  # "up to date"

# --- the gate (includes a REAL ~140s live row-verdict remeasurement --
#     ALWAYS an explicit, generous tool-level timeout, never only a
#     shell-level one) --------------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 68 passed, 1 failed (pre-existing)

# --- the regression arms (test_goal_residual_migrated.py includes a
#     REAL ~80s live MBPP battery -- same timeout discipline) -------------
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
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`, resolving
from inside `/home/matt/ocelot-arc6-rearm-deadlock`.

**Contamination.** No MBPP test-split content was read by anything new this
rung added — `ax_world_probe_epoch`/`world_drift_confirmed_goals`/
`world_probe_advance_epoch` are pure graph arithmetic and a mechanical
counter bump over facts `refresh_evidence_facts` (unmodified in every other
respect) already probes. Nothing new entered a codebook, a route table, or
a cue table.
