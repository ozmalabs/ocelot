# ARC 6 — A19: THE SILENT ORDER-N FALLBACK, MADE OBSERVABLE

**Date:** 2026-08-11
**Bars:** `PROGRAM_SYNTHESIS_ARC6_PREREG.md` **amendment A19** (`AR19a`–`AR19d`),
registered **before** this build.
**Base commit:** `ce013b228b973b8492021abc809a3513912eda4e` (`main`, detached
worktree `/home/matt/ocelot-arc6-silent-fallback`, branch
`arc6-silent-fallback`).
**Engine:** `c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
— copied from the canonical tree, **verified resolving from inside this
worktree** (`substrate_rs._native.__file__` is
`/home/matt/ocelot-arc6-silent-fallback/runners/dsl/python/substrate_rs/
_native.abi3.so`), zero `.rs` files newer than the binary. The **same**
binary A15–A18 measured on; the canonical tree's copy has not moved.
Coherence probe passed before every measurement:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` and
`(1,2,3)` **distinctly**.
**Seed:** `seeds/arc_executor.json` **v1.5.0** (bumped from v1.4.0), emitted
by `tools/build_arc_executor_seed.py` and gated byte-identical against it —
**8 rules** (the shipped 6 plus `ax_fallback_silent` / `ax_fallback_cleared`).
**Gates:** `tests/test_arc_executor_migrated.py` — **80 collected, 79
passed, 1 failed (pre-existing)**; the other five arc-6 suites combined —
**174 collected, 172 passed, 1 failed (pre-existing), 1 skipped**.

**SCOPE: exactly AR19a–AR19d — make the silent order-N fallback observable,
without changing when it fires.** `ag_ask`/`ax_dispatch`'s general
collapse-agreement question, `gr_condition_lapse`'s closed vocabulary,
`results/arc6_import_impedance.json`/`scripts/arc6_import_impedance.py`, and
anything under `docs/research/theory_convergence/` or
`docs/research/adventure_mechanics/` are all **untouched**, per the task's
explicit boundary.

---

## 0. VERDICTS

| bar | verdict | what it rests on |
|---|---|---|
| **AR19a — a standing fact mints when order-N is absent** | **PASS** | booting with no `arc_magnitude` on the graph at all, `AgendaVerdict{kind:'order_n_fallback', active:1.0}` mints the instant `mg_sel_agid` reads absent, readable through the existing, unmodified `agenda_verdicts(sub, "order_n_fallback")`; mint-once holds across three further `run_rules()` passes (same `_id`). §2 |
| **AR19b — the SAME fact does NOT appear (or clears) when order-N is live** | **PASS** | two demonstrations: (i) a negative control — `arc_magnitude` + the tier ladder loaded from the start (the WH1 scene) never mints the fact, and neither does the WH1-CONTROL-C scene (ladder withheld, collapses merely agree, `mg_select` still fires); (ii) a transition — starting from the fact active, loading `arc_magnitude` onto the SAME live graph flips the SAME node's `active` to `0.0` on the very next fixpoint, with the measurement epoch **unchanged** (`"0" → "0"`) — the clearing does not depend on an epoch bump. §3 |
| **AR19c — dispatch behaviour is UNCHANGED** | **PASS** | the existing WH1/WH3 live scenes reproduce byte-identically WITH the two new rules installed: order-N still wins and dispatches (`selected_by: order_n_mg_select`) when live, order-1 still wins and dispatches (`selected_by: order_1_ag_select`) when it is not, and the fact coexists with both outcomes without perturbing either — `ax_dispatch`/`SEL_AGID`/`ARMED_AGID`/`ARMED_VALUE`/`COLLAPSE_NAME`/`_armed`/`ROUTE`/`_routable` are byte-identical to `HEAD`, asserted structurally, not merely re-run. §4 |
| **AR19d — no regression** | **PASS** | the six gate suites produce the **same** failing-node-id lists before and after, paired and named. `domains/arc_executor.py` is **byte-identical to `HEAD`** — the design's own prediction that the mechanism needs zero adapter changes, checked rather than claimed. `seeds/arc_goals.json`, `seeds/goal_residuals.json`, `seeds/arc_magnitude.json`, `seeds/arc_decompose.json`, `seeds/program_synthesis.json` byte-identical to `HEAD`; every pre-A19 rule body in `seeds/arc_executor.json` byte-identical to `HEAD`'s own emitted copy. §5 |

**The one thing worth reading if you read nothing else.** WIRE_HANDS §8
ranked this uncertainty first by damage and named the fix precisely:
*"mitigated after the fact (`selected_by` on the order) and **not
prevented**."* Nothing about the fallback's firing changed here — it still
reverts to order-1 exactly when it always did, exactly as WIRE_HANDS
designed it to. What changed is that the graph now **says so while it is
happening**, not just after an order has already been minted:
`AgendaVerdict{kind:'order_n_fallback', active:1.0}` sits on the agenda the
whole time the fallback is in effect, flips to `0.0` the moment order-N
comes back, and a self-monitoring agent — or a human, or a future rung —
can ask "is the fallback active right now" instead of reconstructing the
answer order by order from `selected_by`.

---

## 1. WHAT CHANGED

Four files edited (one of them a regenerated artifact of another), two
added. **No new DSL Term, no new node type, no new edge type, no new
adapter function, no engine source change.** `domains/arc_executor.py` is
untouched — the design investigation (§2 below) predicted this and it held.

```
tools/build_arc_executor_seed.py       +2 rule builders (ax_fallback_silent /
                                        ax_fallback_cleared), +1 helper
                                        (_fallback_verdict_active), version
                                        bump, docstring/description text
seeds/arc_executor.json                REGENERATED from that emitter (never
                                        hand edited).  v1.4.0 -> v1.5.0
tests/test_arc_executor_migrated.py    11 new test_a19_* gates, 1 pin
                                        inverted (the WH1 precedent, applied
                                        to A18's own exact-rule-list pin)
scripts/arc6_silent_fallback_measure.py NEW -- the measurement runner
results/arc6_silent_fallback.json      NEW -- the artifact
PROGRAM_SYNTHESIS_ARC6_PREREG.md       amendment A19 appended
PROGRAM_SYNTHESIS_ARC6_SILENT_FALLBACK.md NEW -- this file
```

`domains/arc_executor.py` needed **zero** edits: `agenda_verdicts(sub,
kind=None)` was already generic over `kind` (every existing caller already
passes an explicit `kind="impotent"`), so a second `kind` value is additive
by construction and the adapter needed no new function, no new branch, and
no edit to its module-specific source-audit allow-list. Confirmed by a
byte-identity check against `HEAD`, not merely by absence of a diff in this
session (§5.3).

### 1.1 The mechanism is a direct reversible pair, not the epoch-lapse idiom

Two new rules in `seeds/arc_executor.json`, mirroring `ax_impotent`'s
mint-once idiom for the ON direction and `gr_condition_lapse`/
`gr_condition_hold`'s reversible-pair SHAPE for the OFF direction — but,
deliberately, **not** their epoch-lapse mechanism:

```python
def _order_n_is_not_live():
    return EQ(A(V("agenda"), "mg_sel_agid"), L(None))   # SEL_AGID's OWN test

def _fallback_verdict_active():
    return EXISTS(NOT_("AgendaVerdict"), "avfa",
                  AND(EQ(A(V("avfa"), "kind"), L("order_n_fallback")),
                      EQ(A(V("avfa"), "active"), L(1.0))))

def _r_fallback_silent():          # mint-once while active
    ...
    "where": AND(_order_n_is_not_live(), NOT(_fallback_verdict_active())),
    "effects": [add_node AgendaVerdict{kind:'order_n_fallback', active:1.0,
                                        epoch, reason}, add_edge ...]

def _r_fallback_cleared():         # flip active -> 0.0 the instant it is live
    ...
    "where": AND(NOT(_order_n_is_not_live()),
                 EQ(avf.kind, 'order_n_fallback'), EQ(avf.active, 1.0)),
    "effects": [set_attr avf active 0.0, set_attr avf cleared_epoch ...]
```

Both rules read `_order_n_is_not_live()` **verbatim** — the identical Term
`SEL_AGID`/`ARMED_AGID`/`ARMED_VALUE`/`COLLAPSE_NAME` already branch on, via
`_armed()` inside `ax_dispatch`'s own `where` — so they can never disagree
with `ax_dispatch` about which collapse is live, by construction, the same
guarantee `ax_impotent` has via `_routable`/`ROUTE` reused verbatim. §4.2
proves this structurally, not just by design intent.

**Why not `ax_impotent`'s own `fact_equals(arc_measure_epoch)` lapse
idiom.** That idiom is right for `ax_impotent`, whose verdict describes a
POOL STATE as of one epoch and is meant to go stale only when a new
measurement might have moved the world. The fallback's liveness is not
epoch-shaped: `arc_magnitude` can be loaded onto an already-running graph
with **no epoch bump anywhere in the scene** — exactly how
`test_wh3_the_fallback_when_the_order_N_collapse_is_NOT_on_the_graph` and
`test_wh1_the_hands_now_follow_the_ORDER_N_collapse` differ (one boots
without `arc_magnitude`, one with it, from the same `boot()`/
`_boot_with_magnitude()` split). A self-monitoring agent asking "is the
fallback active right now" wants the CURRENT truth of the Term, not a
description that stays valid only until the next remeasurement — so the
clearing rule reads the live Term directly. Measured, not merely argued:
§3.3 demonstrates the epoch does not move across the exact transition that
clears the fact.

---

## 2. AR19a — THE FACT MINTS THE INSTANT ORDER-N IS ABSENT

`results/arc6_silent_fallback.json → AR19a`. A boot with **no**
`arc_magnitude` seed on the graph at all — the real shape WIRE_HANDS §8.1
names, *"a boot without `arc_magnitude`"* — read back, engine-stamped:

```
before any run_rules():           mg_sel_agid = null      fallback = []
after the FIRST run_rules():      mg_sel_agid = null      fallback =
  [{"kind": "order_n_fallback", "active": 1.0,
    "reason": "mg_sel_agid_absent_order_n_collapse_not_producing_a_stamp",
    "epoch": "0", "_id": "#90"}]
after THREE MORE run_rules() passes (no change to the graph otherwise):
                                   fallback = [ ... same _id "#90" ... ]
```

**Mint-once holds**: three additional fixpoint passes over an unchanged
absent-order-N graph produce the identical single verdict, same `_id` —
the `ax_impotent`-precedent guard (`NOT(_fallback_verdict_active())`)
working exactly as `test_a19_AR19a_mint_once_repeated_passes_do_not_
double_mint` gates it.

**Before the first `run_rules()`, the fact does not exist** — nothing has
run yet, so this is not a boot-time constant; it is the graph's own
conclusion, reached the first time the collapse settles.

---

## 3. AR19b — THE SAME FACT DOES NOT APPEAR, OR CLEARS, WHEN ORDER-N IS LIVE

Two demonstrations, both live, both read directly off
`results/arc6_silent_fallback.json`.

### 3.1 Negative control (i) — order-N live from the start (the WH1 scene)

```
AR19b_control_ladder:
  arc_sel_agid   arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive
  mg_sel_agid    arc.remeasure.arc6.verdict.row_verdict_seed_only
  collapses_disagree: true
  fallback_after_dispatch: []
  orders: [{"agid": "arc.remeasure...row_verdict_seed_only",
            "selected_by": "order_n_mg_select"}]
```

The two collapses disagree exactly as WIRE_HANDS' WH1 recorded, order-N
dispatches, and the fallback fact **never mints** — not even transiently —
across the whole scene through dispatch.

### 3.2 Negative control (ii) — the WH1-CONTROL-C discriminator

The sharper control: `arc_magnitude` loaded, the tier ladder **withheld**.
WIRE_HANDS' own arm C showed the two collapses merely **agree** here —
`mg_select` still fires, it just names the same winner as order-1. A wrong
implementation that mistook "the two collapses agree" for "order-N is
absent" would mint the fallback fact here; the correct one does not,
because `mg_sel_agid` is genuinely non-null:

```
AR19b_control_no_ladder:
  arc_sel_agid   arc.supply...missing_structural_primitive
  mg_sel_agid    arc.supply...missing_structural_primitive   (SAME agid — agree, not absent)
  collapses_agree: true
  fallback: []
```

### 3.3 The transition — order-N goes live mid-graph, epoch unchanged

The strongest demonstration, and the reason the mechanism is a direct
reversible pair rather than an epoch-lapse (§1.1): start from AR19a's exact
scene (fact active, `_id` `#90`), load `arc_magnitude` onto the **same live
graph** — no re-boot — and run one more fixpoint:

```
AR19b_transition:
  epoch_before: "0"        epoch_after: "0"        epoch_unchanged: true
  mg_sel_agid_before: null mg_sel_agid_after: arc.remeasure...row_verdict_seed_only
  fallback_before: [{"active": 1.0, "_id": "#90", ...}]
  fallback_after:  [{"active": 0.0, "_id": "#90", "cleared_epoch": "0", ...}]
  same_node_id: true
```

**The same node** (`_id: "#90"` throughout) flips `active` from `1.0` to
`0.0` on the very next `run_rules()` after order-N goes live — with the
measurement epoch reading `"0"` on both sides of the transition. Nothing
about this clearing waited for, or depended on, a measurement ever running.

---

## 4. AR19c — DISPATCH BEHAVIOUR IS UNCHANGED

### 4.1 Both outcomes, unperturbed, with the fact coexisting

```
AR19c_order1_dispatch_alongside_fact (boot() -- no arc_magnitude):
  fallback_present_before_dispatch: [{"active": 1.0, ...}]
  orders_before_reply: []                     # unroutable order-1 winner, as always
  orders_after_reply:  [{"agid": "arc.remeasure...row_verdict_seed_only",
                          "selected_by": "order_1_ag_select"}]
  fallback_still_present: [{"active": 1.0, ...}]
```

This is `test_wh3_the_fallback_when_the_order_N_collapse_is_NOT_on_the_
graph`'s own scene, unmodified, reproducing byte-identically **with the two
new rules installed**: the fallback still fires exactly as before
(`selected_by: order_1_ag_select`), and the standing fact simply sits
alongside it, undisturbed, both before and after dispatch. §3.1 is the
mirror case on the order-N side (`selected_by: order_n_mg_select`,
`fallback_after_dispatch: []`).

### 4.2 Structural proof, not just re-run behaviour

`test_a19_AR19c_the_guard_TERM_is_IDENTICAL_to_SEL_AGIDs_own_absence_test`
walks the regenerated seed's own JSON and confirms, by term equality (not
string matching): the exact `Eq(agenda.mg_sel_agid, null)` dict that
appears (four times, once each via `SEL_AGID`/`SEL_VALUE`/`ARMED_AGID`/
`ARMED_VALUE`) inside `ax_dispatch`'s own `where` is **the same dict,
literally**, as `ax_fallback_silent`'s first conjunct and the negation
inside `ax_fallback_cleared`'s first conjunct. The two new rules cannot
drift from `ax_dispatch`'s own notion of "order-N is not live" because they
are not a re-derivation of it — they are the identical Term, imported from
the identical Python function.

`test_a19_AR19d_ax_dispatch_and_every_prior_rule_body_is_UNCHANGED` reads
every pre-A19 rule (`ax_dispatch`, `ax_retired_epoch`, `ax_rearm`,
`ax_close`, `ax_impotent`, `ax_world_probe_epoch`) back off the regenerated
seed and diffs each one against `HEAD`'s own emitted copy: byte-identical,
all six.

---

## 5. AR19d — NO REGRESSION. A LIST OF NODE IDS, NEVER A COUNT.

Both arms below ran on the **same binary** (`c5e50801d48a`) in this
worktree; the **before** arm was measured first (§ baseline, run before any
file in this rung was touched).

| suite | before | after | failing node ids — **identical before and after** |
|---|---|---|---|
| `test_arc_executor_migrated` | 68 passed, 1 failed (69 collected) | **79 passed, 1 failed (80 collected)** | `test_ex1_the_frozen_artifacts_are_STILL_byte_identical` |
| `test_arc_goals_migrated` | 37 / 37 | 37 / 37 | — |
| `test_goal_residual_migrated` | 29 passed, 1 failed, 1 skipped | 29 passed, 1 failed, 1 skipped | `test_gr4_the_live_mbpp_pass_ids_are_unchanged` |
| `test_arc6_valuelayer_migrated` | 35 / 35 | 35 / 35 | — |
| `test_arc_magnitude_migrated` | 43 / 43 | 43 / 43 | — |
| `test_arc_decompose_migrated` | 28 / 28 | 28 / 28 | — |

The executor suite's collected count rises **69 → 80**: 11 new
`test_a19_*` gates, zero removed, one pin inverted (§5.1). Both pre-existing
reds are the **same two node ids every rung since A12.1 has recorded** —
`results/` untracked in this checkout, and this engine's short sha not in
`test_gr4`'s three-entry allowlist — neither this rung's to fix, neither
touched.

### 5.1 One pin inverted, named, not silently removed — the WH1 precedent, a third time

`test_a18_AR18d_the_new_rule_is_the_ONLY_addition_to_the_seed` asserted the
seed's rule list was EXACTLY the six names A18 shipped. A19 adds a seventh
and eighth (`ax_fallback_silent`, `ax_fallback_cleared`), so the exact-list
assertion is now false by construction — inverted to a **prefix** check
(`names[:6] == [...]`) with a docstring explaining why, mirroring A18's own
treatment of `test_a15_the_seed_added_ZERO_new_rules`.
`test_a19_AR19d_the_new_rules_are_the_ONLY_addition_to_the_seed` now
asserts the full eight-name list, the version (`1.5.0`), and re-runs the
emitter's own `--check`.

### 5.2 The source audit — a stronger claim than usual, and it is checked

`test_a19_AR19d_the_adapter_is_BYTE_IDENTICAL_to_HEAD` asserts `domains/
arc_executor.py` is **whole-file byte-identical** to `HEAD` — stronger than
the module-specific source audit every prior rung runs (which only proves
no *new* banned call was added), because this rung's design investigation
predicted the adapter needs no edit at all, and the prediction is checked
here rather than left as an unverified claim.

### 5.3 Confinement, asserted not promised

- `seeds/arc_goals.json`, `seeds/goal_residuals.json`, `seeds/arc_
  magnitude.json`, `seeds/arc_decompose.json`, `seeds/program_
  synthesis.json`, `domains/arc_goal_ingest.py`, `domains/goal_residual_
  ingest.py`, `domains/arc_magnitude_ingest.py` — byte-identical to `HEAD`
  (`test_a19_AR19d_the_seeds_below_this_rung_are_still_UNTOUCHED`, green;
  `tools/build_arc_magnitude_seed.py --check` also green).
- `runners/dsl/src/*` — byte-identical to `HEAD` (no new Rust).
- `tools/build_arc_executor_seed.py`'s pre-A19 rule builders
  (`ROUTE`/`_routable`/`_dispatchable`/`_r_dispatch`/`_r_rearm`/
  `_r_impotent`/`_r_world_probe_epoch`) are unedited — the emitted JSON for
  every pre-A19 rule name is byte-identical to `HEAD`'s own emitted copy
  (§4.2), which is the behavioural consequence that actually matters.
- `seeds/arc_executor.json` regenerates byte-identically from its own
  (edited, version-bumped 1.4.0 → 1.5.0) emitter.
- `domains/arc_executor.py` — byte-identical to `HEAD`, whole file (§5.2).

---

## 6. THE TIMEOUT HAZARD, HIT A FIFTH TIME, RECOVERED CLEANLY

Recorded because the process is the result — this is now the fifth time
this exact class has fired in this arc (WIRE_HANDS §7.5, and named again in
REARM_DEADLOCK §7.1/§7.2 as a standing hazard to check for before every
run).

**What happened.** The very first baseline invocation of
`test_arc_executor_migrated.py` in this rung was run under the tool's
**default 2-minute timeout**, not the `live_run` fixture's real ~140s
duration plus margin. The runner was `SIGKILL`ed mid-flight, inside its own
`try`, so its `finally`-based restore never ran. `git status --porcelain`
in **both** this worktree and the canonical tree immediately after showed
`seeds/program_synthesis.json` modified; `results/arc6_verdict_before.json`
had a fresh mtime (`17:25:17`, matching the kill) and a **different sha**
(`57920902…`) from its two untouched siblings (`arc6_verdict_after.json`,
`arc6_verdict_pricing.json`, both `2026-08-10 21:59:02`, unmoved).

**Recovery, verified rather than assumed.** `seeds/program_synthesis.json`
was restored via `git checkout --` (git is the authority for a tracked
file) and its sha confirmed back at `4e866340…`, matching `HEAD`.
`results/arc6_verdict_before.json` is untracked (gitignored), so it was
recovered from the runner's own crash-stash under `/tmp/arc6_remeasure_*`
— **six independent stash directories**, from six different historical
runs spanning 2026-08-10 21:59 through this rung's own kill, were checked
by sha, and **all six agreed** on `ed90bf281bd8dc8…` for the pristine
content, including the stash captured at the exact start of the killed run
(`/tmp/arc6_remeasure_u9iu1knw`, created `17:24:08`, matching the kill
window). That value was copied back and the sha reconfirmed. Both trees'
`git status --porcelain` were empty (module the expected symlinked
`data`/`results` entries) before any further measurement was taken, and the
re-run baseline (§ above) then completed cleanly under an explicit
580-second tool-level timeout.

**What this confirms, once more.** (i) The hazard fires on the FIRST
invocation of any command containing a live fixture, not only on later,
"should be fast now" confirmation runs — REARM_DEADLOCK's own account was
from a post-hoc confirmation run; this one was the baseline itself.
(ii) Cross-checking multiple independent stash snapshots by sha, rather
than trusting the single newest one, is worth the extra thirty seconds — it
would have caught a stash corrupted by an even earlier interrupted run.
**No measurement in this document rests on the damaged window** — every
number above was taken after the tree was verified clean by sha, under an
explicit, generous timeout.

---

## 7. REMAINING UNCERTAINTIES

Ordered by how much damage being wrong would do.

1. **The fact is descriptive, not actionable.** Exactly per this rung's own
   scope boundary: nothing reads `AgendaVerdict{kind:'order_n_fallback'}`
   and does anything about it — no `ArcQuestion`, no minted
   capability-acquisition goal, no change to what `ax_dispatch` runs. A
   graph that has been running on the order-1 fallback for a long time now
   SAYS so, but still does nothing differently, which is the honest and
   deliberately narrow scope this rung was given (WH4's own §5 candidate
   (a)/(b) survey, and A13's identical "terminate honestly" pick, both
   apply here unchanged — announcing is not acting).
2. **`_order_n_is_not_live()` is read by two more rules now than before —
   a widened, not narrowed, surface for the SAME Term.** Nothing in this
   rung's design or measurement suggests this is a hazard (the Term is a
   pure boolean read with no side effect, and §4.2 proves the new rules
   cannot disagree with `ax_dispatch` about its value), but it is now
   evaluated in three rule bodies instead of one, and a future edit to
   `_order_n_is_not_live()` itself (not exercised by anything in this
   rung) would now have three, not one, consumers to keep behaviourally
   coherent.
3. **The fact does not distinguish "never loaded `arc_magnitude`" from
   "loaded it, but `mg_select`'s own guard has not matched yet" from
   "loaded it, and it matched once, long ago, on a graph that has since
   changed shape."** All three read as `mg_sel_agid == null` today (the
   first two structurally; the third cannot currently arise, because
   `mg_select` has no `unset_attr` path and this engine has none — §7 item
   7 of WIRE_HANDS, transferred here unchanged: once written, `mg_sel_
   agid` does not revert to null on its own). If a future rung ever gives
   `mg_sel_agid` a path back to null, `reason` would still read
   `"...not_producing_a_stamp"`, which remains true, but would no longer
   distinguish "never" from "used to, and stopped" — a real distinction a
   human operator might want. Not built here because nothing in this
   rung's own investigation (§2 of the PREREG amendment) found a live path
   to that state, and building a discriminator for an unreachable state
   would be exactly the kind of "solving a problem that cannot currently
   arise" this arc's own discipline warns against.
4. **The reach is still the order-N/order-1 fallback specifically.** This
   rung does not generalise to "make every silent decision in this seed
   observable" — `ax_impotent`'s own pool-quantified reasoning and
   `ax_rearm`'s latch are already observable via their own existing
   effects (`AgendaVerdict{kind:'impotent'}`, `rearm_count`); this closes
   the one gap WIRE_HANDS §8 named first, not a survey of every implicit
   graph fact that could, in principle, be made explicit.

---

## 8. FILES

| file | what |
|---|---|
| `tools/build_arc_executor_seed.py` | +2 rule builders (`_r_fallback_silent`, `_r_fallback_cleared`), +1 helper (`_fallback_verdict_active`), registered in `_rules()`, version 1.4.0 → 1.5.0, module docstring + `description` text extended. Every pre-A19 rule builder byte/AST-identical to `HEAD`. |
| `seeds/arc_executor.json` | **regenerated**, v1.5.0, 8 rules, gated byte-identical against its emitter |
| `tests/test_arc_executor_migrated.py` | +11 `test_a19_*` gates; 1 pin inverted (`test_a18_AR18d_the_new_rule_is_the_ONLY_addition_to_the_seed`, prefix-checked with a docstring, the WH1 precedent a third time); `test_every_rule_in_this_seed_is_shown_to_FIRE_live` extended to cover `ax_fallback_silent` |
| `scripts/arc6_silent_fallback_measure.py` | new — the measurement runner: AR19a, both AR19b controls, the AR19b transition, and AR19c, all in one process, ~0.3s (no live subprocess needed — no rule this rung adds ever calls one) |
| `results/arc6_silent_fallback.json` | the artifact, engine-stamped, carrying every trace quoted above |
| `domains/arc_executor.py` | **UNCHANGED** — byte-identical to `HEAD`, checked (§5.2) |
| `PROGRAM_SYNTHESIS_ARC6_SILENT_FALLBACK.md` | this file |
| `PROGRAM_SYNTHESIS_ARC6_PREREG.md` | **amendment A19** appended |

**One thing in this worktree's `git status` that is NOT part of the
change, flagged so a reviewer does not stage it:** `data` and `results`
appear as untracked — they are **symlinks** into the canonical tree
(the standard practice every arc-6 rung since A12.1 has used, `.gitignore`'s
`data/`/`results/` patterns match directories, not symlinks). They must not
be staged. `runners/dsl/python/substrate_rs/_native.abi3.so` is **not**
modified in this worktree — it was copied in already built (§ engine
provenance above), unlike WIRE_HANDS, which had to rebuild.

**Nothing in the canonical tree changed.** `git status --porcelain` there
is empty (after the §6 recovery) and its `_native.abi3.so` is
byte-identical throughout.

---

## 9. REPRODUCE

```bash
# --- verify main's tip, then the worktree ---------------------------------
git -C /home/matt/ozmadev/ocelot log --oneline -1 main   # ce013b2...
git worktree add --detach /home/matt/ocelot-arc6-silent-fallback ce013b2
cd /home/matt/ocelot-arc6-silent-fallback
git checkout -b arc6-silent-fallback
ln -s /home/matt/ozmadev/ocelot/data    data
ln -s /home/matt/ozmadev/ocelot/results results

# --- the engine (already built, unlike WIRE_HANDS) ------------------------
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
python3 tools/build_arc_executor_seed.py          # writes seeds/arc_executor.json (v1.5.0)
python3 tools/build_arc_executor_seed.py --check  # "up to date"

# --- the measurement (both directions, ~0.3s, no live subprocess) --------
OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:.:scripts \
  python3 scripts/arc6_silent_fallback_measure.py   # -> results/arc6_silent_fallback.json

# --- the gate.  CRITICAL: this suite's live_run fixture is a REAL ~140s
#     re-measurement -- ALWAYS an explicit, generous tool-level timeout,
#     NEVER a shorter one (SS6 above; the fifth time this hazard has fired
#     in this arc) --------------------------------------------------------
COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  PYTHONPATH=runners/dsl/python:. \
  python3 -m pytest tests/test_arc_executor_migrated.py \
    --confcutdir=$PWD -q -p no:randomly -rf   # 79 passed, 1 failed (pre-existing)

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
resolving from inside `/home/matt/ocelot-arc6-silent-fallback`.

**Contamination.** No MBPP test-split content was read by anything this
rung added — `ax_fallback_silent`/`ax_fallback_cleared` are pure graph
arithmetic over a Term (`_order_n_is_not_live()`) that already existed and
was already load-bearing. Nothing new entered a codebook, a route table, or
a cue table.
