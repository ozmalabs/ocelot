# The final CAN issue: a bounded, event-triggered identity nudge for `nudge_identity_on_flipped` — PREREG

Base: `main @ 0784015` ("Merge can-identity-feedback: writes identity_field,
closes `maybe_update_identity`, finalises the CAN arc at 6/7, GO"), verified
via `git log --oneline -1 main` before branching. Worktree to be created at
`/home/matt/ozmadev/ocelot-worktrees/can-identity-nudge-final`, branch
`can-identity-nudge-final`.

This is the true closing rung of the whole CAN arc. `CAN_IDENTITY_FEEDBACK_
RESULTS.md` §6.2 left `nudge_identity_on_flipped`
(`domains/self_improvement_loop.py:320-371`) genuinely unmigrated, for a
reason distinct from every other blocker this arc closed: it is
EVENT-triggered (fires once, on insight consolidation), targets a SPECIFIC
set of flipped node ids, carries an injected `target_sigma` per node (the
insight's own new σ), and scales its step by `recurrence_count` via an
UNBOUNDED `base_alpha * (1.0 + math.log(max(1, recurrence)))`. The sibling
ambient rule `can_native_identity_field_feedback` (`seeds/
can_decay_identity.json` v1.2.0) is a per-tick, epoch-gated, whole-Mt sampler
driven by AMBIENT σ — it has no input surface for a specific target/
recurrence signal, and routing this function through it (rejected in §6.2)
would silently discard the event's own signal.

This document registers, BEFORE any code is written, whether a genuinely
bounded, event-triggered version of this function's own real contract can be
built without reintroducing the rejected unbounded shape.

---

## 0. What was confirmed by direct read before designing anything (not assumed)

- **`detect_insight`** (`domains/insight_detection.py:92-150`) is a pure,
  substrate-agnostic Python comparison of two audit snapshots
  (`previous_frustration`/`previous_state` vs `current_audit`). It calls NO
  continuous-only mechanism anywhere in its body — confirmed by reading the
  full function. It returns a plain dict (`flipped_nodes`, `mt_id`,
  `magnitude`, …), never touches the graph itself. **This function is not
  what blocks migration and needs no change** (and none is made — out of
  scope, confirmed unmodified in this rung).
- **`nudge_identity_on_flipped`** (`domains/self_improvement_loop.py:320-371`)
  reads `insight["flipped_nodes"]` (list of `{node, before, after, delta}`)
  and `insight.get("recurrence_count", 1)`, looks up each flipped node's live
  handle via `substrate.neighbours(mt, "has_concept")`, and calls
  `substrate.concept_nudge_identity(c, target_sigma, alpha_eff)` — the
  CONTINUOUS Rust primitive (`runners/dsl/src/py.rs:2547`,
  `identity_field ← identity_field + α·target_sigma`,
  `runners/dsl/src/can_ops.rs`'s `nudge_identity`). This confirms the
  continuous formula's real shape: an ADDITIVE push in the SIGN (and
  magnitude) of `target_sigma`, scaled by `alpha_eff`, not a
  "move-toward-target" interpolation.
- **`recurrence_count` is ALREADY graph-resident**, not a Python-only value.
  `domains/insight_naming.py::record_insight` (called in
  `self_improvement_step`, `domains/self_improvement_loop.py:~445-463`,
  BEFORE `nudge_identity_on_flipped`) writes/increments `recurrence_count` on
  a graph `InsightEvent` node (`Mt -has_insight-> InsightEvent`) and mirrors
  it onto the Python `insight` dict via `event["recurrence_count"] =
  new_count`. So by the time `nudge_identity_on_flipped` runs, the
  recurrence signal already has a graph home — it does not need to be
  invented.
- **Attr-read default, confirmed by reading the evaluator**
  (`runners/dsl/src/term.rs:4677-4694`): `Attr` on a missing key returns
  `Value::None` (not a numeric 0), and `Eq` uses
  `eq_with_string_coercion` (`term.rs:5433-5437`). This matters for the
  marker-attr design below: two never-set attrs both read `None`, and
  `Eq(None, None)` is expected true (same-variant equality) — the "no
  pending event" case is inert without needing explicit pre-initialisation,
  though this rung still initialises explicitly everywhere for parity with
  every other rule/test in this seed.

---

## 1. The decision: NEW graph rule, event-triggered by a graph-resident marker

Per the task's own explicit menu, two shapes were weighed:

1. **A thin Python function computing the bounded delta itself** (an
   `IfThenElse`-shaped comparison of `target_sigma` against `identity_field`,
   or against 0, executed in Python, then `substrate.set_attr`'d directly).
   **Rejected.** `CLAUDE.md`'s architecture rule is explicit: "Any `if`/`else`
   that reads graph state and decides what to do next is a Rule, not
   Python." Deciding the SIGN of the nudge (and, if recurrence is to matter,
   deciding the STEP SIZE from a recurrence count) are both decisions over
   graph-resident state (`identity_field`, `recurrence_count`) — exactly the
   shape this arc has, without exception, always expressed as a graph Rule's
   `where`/`effects`, never as Python conditionals. Every one of this arc's
   six prior closes (`maybe_hebbian`, `maybe_decay_J`, `maybe_decay_h`,
   `_audit_basin`, `relax`, `maybe_update_identity`) reaches a native RULE via
   `scoped_settle`; none computes its own decision in Python and pokes
   `set_attr`. Doing so here — even bounded — would be the first
   architectural regression in the arc, not a simplification.
2. **A new graph rule, mirroring `can_native_identity_field_feedback`'s own
   shape, but triggered by a graph-resident EVENT MARKER instead of the
   ambient per-tick `can_tick` epoch.** **Adopted.** This preserves every
   precedent this arc has built (fixed-quantum `IfThenElse` step, own epoch
   attr, the same `allow_h_drift` policy-`Or` subtree, zero new Rust) while
   giving the rule an input surface the ambient rule structurally lacks: a
   per-Concept `target_sigma` and `recurrence_count`, injected onto the
   SPECIFIC flipped nodes only, by the ONE Python write this rung needs
   (mechanical translation of the already-computed, substrate-agnostic
   `insight` dict into graph attrs — the same class of write `ChatWorld`
   does for an inbound Message, not a decision).

**Zero new Rust is needed** — confirmed against the same Term list every
prior rung in this seed reused (`Attr`/`Eq`/`Not`/`And`/`Or`/`Gt`/`Lt`/
`Plus`/`Minus`/`IfThenElse`/`Lit`), all pre-existing.

---

## 2. The bounded design, registered before the seed is written

### 2.1 What Python writes (mechanical translation, not a decision)

For each `{node, after}` entry in `insight["flipped_nodes"]` whose node
belongs to `mt` (looked up the same way the continuous branch already does):

```
pending_identity_nudge_target_sigma   ← after                 (float, passthrough)
pending_identity_nudge_recurrence     ← recurrence_count       (int, passthrough
                                                                 of the ALREADY
                                                                 graph-resident
                                                                 InsightEvent
                                                                 counter, §0)
pending_identity_nudge_epoch          ← mt.insight_nudge_seq + 1
```

`insight_nudge_seq` is a plain per-Mt monotonic counter Python increments
unconditionally on every native-branch call (the SAME "sequence number"
class of write as a Message's own id, or `can_tick` itself — bookkeeping,
never a decision over WHAT to write, only WHEN to bump). No comparison, no
threshold, no branch on graph *content* — only "this event happened, tag it
with the next number." This is the ONLY Python write in the native branch;
everything else (sign, step size, whether to fire at all) is decided by the
rule below.

### 2.2 The new rule, `can_native_identity_nudge_on_flip`

Match: `mt -has_concept-> c` (identical match clause to every rule in this
seed).

`where`: `And(Not(Eq(pending_identity_nudge_epoch, identity_nudge_applied_
epoch)), <the byte-identical allow_h_drift Or-policy-gate every rule in this
seed already uses>)` — an EQUALITY-gated own-epoch marker (not the `Gt`
per-tick pattern the ambient rules use, because this event is sparse and
Python-injected rather than monotonically advancing every tick; still the
SAME "own epoch attr, consumed by writing it back" idiom `can_native_
evidence_decay`'s own `decay_tick` and every sibling rule in this seed
already use).

`effects`:

```
step := IfThenElse(Gt(pending_identity_nudge_recurrence, 1), 2.0, 1.0)

identity_field ←
  IfThenElse(Gt(pending_identity_nudge_target_sigma, 0), identity_field + step,
    IfThenElse(Lt(pending_identity_nudge_target_sigma, 0), identity_field - step,
      identity_field))   # target_sigma == 0 carries no directional evidence,
                          # mirrors can_native_identity_evidence_sample's own
                          # state==0 guard (seeds/can_decay_identity.json,
                          # "sigma==0 is no evidence")

identity_nudge_applied_epoch ← pending_identity_nudge_epoch   # consume the event
```

**This is registered, precisely, as the answer to the task's own central
question**: recurrence is preserved as a BOUNDED, BINARY two-tier step
(1.0 first occurrence, 2.0 recurring) — never an unbounded
`log(recurrence)` growth — and `target_sigma`'s DIRECTION (not the ambient
rule's own AMBIENT log-odds render) drives the sign, so the event's real
signal (which node, toward what σ, first-vs-repeat) survives the bound
instead of being silently discarded the way routing through the ambient
rule alone would have discarded it (`CAN_IDENTITY_FEEDBACK_RESULTS.md`
§6.2's own rejected option 1).

### 2.3 Why binary (not three- or N-tier) recurrence, registered before data

A binary distinction is the SMALLEST possible response to "does recurrence
matter at all" that is not simply "ignore it" — anything finer (three tiers,
a capped linear scale) is additional unbounded-in-principle machinery this
task's own charter asks to avoid defaulting into. If the convergence sweep
(§3) finds the binary 2× step destabilises anything, the fallback registered
here is to drop to a SINGLE fixed step (no recurrence distinction at all,
matching the ambient rule exactly) rather than widen the tiers — narrowing
toward the already-proven-safe shape, never away from it.

### 2.4 Same-tick / same-event race — checked, not assumed

`pending_identity_nudge_*`/`identity_nudge_applied_epoch` are BRAND NEW attr
names. Confirmed by grep (run before this doc was written):

```
$ grep -rn "pending_identity_nudge\|identity_nudge_applied_epoch\|insight_nudge_seq" seeds/*.json domains/*.py
(no output before this rung's changes)
```

Zero pre-existing writers or readers anywhere — the SAME structural
situation `external_field`/`identity_field` were in before their own first
writer rules (`CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` §2, `CAN_IDENTITY_
FEEDBACK_RESULTS.md` §2.5). Only `nudge_identity_on_flipped`'s native branch
writes the pending attrs; only this new rule reads/writes them. No race is
structurally possible.

### 2.5 Boundedness — the honest claim, registered up front

Per-event, the magnitude added to `identity_field` is bounded to exactly
±1.0 or ±2.0 (never more, never scaled by `magnitude`/`delta_F`/anything
continuous). Across MANY events, `identity_field` can still accumulate
without a hard ceiling — this is the SAME honest, registered limitation
`can_native_identity_field_feedback` itself carries (`CAN_IDENTITY_FEEDBACK_
RESULTS.md` §2.4: no `-β·identity_field` decay term exists for this attr;
building one is out of scope for both rungs). What IS new and load-bearing
here: the PER-EVENT step is now provably bounded (∈ {1.0, 2.0}) where the
rejected continuous-mirroring design's per-event step was UNBOUNDED
(`base_alpha·(1+ln(recurrence))` grows without limit as recurrence grows).
That is the actual claim this rung stands or falls on, and §3 is the check
of it, not an assertion.

---

## 3. Convergence validation — the load-bearing check, registered before it is run

### 3.1 Why the ambient sweep alone is insufficient here

`CAN_IDENTITY_FEEDBACK_RESULTS.md` §3 validated the AMBIENT rule alone (no
flip events). This rung's own risk is different: BOTH mechanisms are live
simultaneously in real usage (`self_improvement_step` calls `maybe_update_
identity` — the ambient rule's orchestration entry point — AND (this rung)
`nudge_identity_on_flipped` in the same step), and this rung's own nudge is
a LARGER single-shot perturbation (up to ±2.0 in one event, vs. the
ambient rule's ±1.0 per tick) landing on the SAME `identity_field` the
discrete update's local-field sum reads. The convergence question this rung
must answer that the prior rung did not: does an ambient-feedback-active
draw ALSO survive one or more real, larger, event-triggered nudges without
losing the discrete-async fixpoint property.

### 3.2 The scenario, registered before running

Reuse `test_can_identity_feedback.py::_build_draw` byte-identically (N=8
complete graph, symmetric `causal_influence`, `external_field ~
Uniform(-1,1)`, coarse/fine weight vocab), loading BOTH `seeds/
can_native_reimplementation.json` and `seeds/can_decay_identity.json` (now
carrying the new rule), so the ambient feedback rule, the discrete update,
AND the new event-triggered rule are all live in the SAME `run_rules`
fixpoint.

Per draw, across `N_TICKS=15` real ticks (matching the prior rung's own
tick count):
  - every tick: advance `can_tick`, `run_rules(3000)` (drives the discrete
    update + ambient feedback, exactly as the prior sweep did);
  - at ticks 3, 7, and 11 (three real, spaced flip EVENTS per draw, not one):
    synthesize a real flip event from the CURRENT `state` reading of a
    deterministically chosen subset of concepts (2 of the 8, alternating
    which 2 across the three events so no single node monopolises the
    signal), call `nudge_identity_on_flipped(inner, mt, insight)` with a
    real `insight` dict shaped exactly like `detect_insight`'s own return
    (`flipped_nodes` with real `node`/`after` values pulled from live
    `state`; `recurrence_count` alternated 1/2/3 across the three events so
    BOTH the first-occurrence and recurring step tiers are exercised in
    every draw, not just one).
  - after each event call, `run_rules(3000)` again (the event's own
    `scoped_settle` already does this internally; the sweep's own outer
    loop additionally re-checks the fixpoint after the event to catch any
    non-convergence the event itself might introduce).

**Non-convergence bar, registered**: `steps >= 3000` on ANY of the 15 ticks'
`run_rules` calls, OR on any of the 3 post-event `run_rules` calls, counts
as a non-convergent draw — the SAME bar `_drive_and_check_convergence`
already uses, extended to also cover the post-event calls.

### 3.3 Sample size, registered before running

**60 real draws** (30 coarse + 30 fine) for `discrete_mode="3state"` (the
deadzone case, the same headline condition the prior rung used) — reusing
the prior rung's own 60-draw precedent rather than inventing a new size, on
the grounds that this rung's scenario is a strict superset of the prior
rung's (same draws, same ticks, PLUS 3 real events per draw) and the prior
sample size was itself derived from `CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`'s
"0/60 non-convergent draws" precedent. A secondary 60-draw `2state` sweep
repeats the check (`identity_field` is read by both discrete-update rules).
**120 real draws total, 15 ticks + 3 events each = 1800 real `run_rules`
tick-calls + 180 real event calls, 1980 total `run_rules`-driving
operations** — larger than the prior rung's own 1800, because this rung adds
the event calls on top of the same tick schedule.

**GO bar, registered before any result is seen**: 0/120 non-convergent
draws, mirroring the prior rung's own bar exactly.

---

## 4. Live demonstrations to build, registered before code

1. A real flip event (a real `insight` dict, shaped like `detect_insight`'s
   own output) correctly nudges the SPECIFIC flipped node's `identity_field`
   toward its `target_sigma`'s sign, by exactly the bounded step (1.0 first
   occurrence, 2.0 recurring) — not unbounded growth as `recurrence_count`
   is repeated many times (a control demonstrating the OLD continuous
   formula's `alpha_eff` would have kept growing past this rung's fixed
   ceiling, this rung's own does not).
2. A NON-flipped node (a sibling Concept on the same Mt, not named in
   `flipped_nodes`) has its `identity_field` UNCHANGED by the same event —
   the event-scoping (as opposed to the ambient rule's whole-Mt scope) is
   real, not accidental.
3. The convergence numbers from §3, real, printed.
4. (mirroring the prior rung's own §4d) two-Mt isolation: an untouched
   sibling Mt's Concepts are unaffected by a flip event fired on the target
   Mt.

---

## 5. What would count as the honest "permanent boundary" outcome instead — registered now, before any result is seen

If §3's convergence sweep finds ANY non-convergent draw with the bounded
design as registered in §2, the fallback named in §2.3 (drop to a single
fixed step, no recurrence distinction) is tried ONCE, re-swept at the same
sample size. If THAT also fails to reach 0/120, this rung stops and reports
a permanent, principled boundary: even the smallest non-trivial
event-triggered perturbation to `identity_field` (a single fixed quantum, no
recurrence signal at all) destabilises the discrete-async fixpoint when
layered on the ambient rule — meaning `identity_field` cannot safely accept
BOTH an ambient per-tick writer AND ANY event-triggered writer under this
substrate's current Lyapunov argument, a genuine architectural ceiling, not
a design failure of this rung specifically. This would be reported in
`CAN_IDENTITY_NUDGE_FINAL_RESULTS.md` with the exact failing scenario
(seed, tick, event) reproduced, per the task's own explicit requirement that
a boundary claim be evidenced, not asserted.

If §3 is clean (0/120) with the FULL registered design (target_sigma
direction + binary recurrence step), that is reported as GO and `nudge_
identity_on_flipped` migrates, mirroring `maybe_update_identity`'s own
`_is_native` dispatch exactly, continuous branch byte-preserved and
unconditional as always.

---

## 6. Explicitly out of scope, restated (nothing here changes any of these)

`can_native_identity_field_feedback` (the ambient rule) itself; `can_native_
evidence_decay`/`can_native_identity_evidence_decay`/`can_native_external_
field_decay`/`can_native_hebbian_mint`/`_reweight`; `can_native_update_
3state`/`_2state`'s own formula; `detect_insight`'s own comparison logic
(confirmed unmodified, §0). No new Rust Term — confirmed against the Term
list in §1.

---

## 7. Regression set (registered, to be run before and after)

`tests/test_can_identity_feedback.py`, `tests/test_can_decay_identity.py`,
`tests/test_can_native_reimplementation.py`, `tests/test_can_mt_scoped_
consumers.py`, `tests/test_self_improvement_loop.py`, plus a new `tests/
test_can_identity_nudge_final.py` for this rung's own live demonstrations
and convergence sweep.
