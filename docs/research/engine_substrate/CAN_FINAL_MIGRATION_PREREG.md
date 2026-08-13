# The final CAN consumer migration — closing the arc with the three built primitives — PREREG

Base `main @ 84ed599` ("Fix stale cross-rung test assumption in
test_evidence_decay_blocked_when_frozen"), verified via `git log --oneline -1
main` before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-final-migration`, branch
`can-final-migration`.

This is the coordinating rung for the whole day's CAN arc. It reads, in
order: `CAN_CONSUMER_MIGRATION_RESULTS.md` (the original 7-consumer audit:
1/7 migrated, 6/7 blocked on three named root causes — Blocker A [no native
non-mutating counterfactual predictor], Blocker B [Hebbian graded
reweighting non-materializing], decay/identity-dynamics [no native design at
all]); `CAN_COUNTERFACTUAL_PREDICTOR_RESULTS.md` (Blocker A closed:
`domains/can_counterfactual.py`); `CAN_HEBBIAN_MATERIALIZATION_RESULTS.md`
(Blocker B closed: `domains/can_native_hebbian_bridge.py` + a real policy-gate
fix); `CAN_DECAY_IDENTITY_RESULTS.md` (decay closed, identity dynamics closed
for READING only, FEEDBACK explicitly unbuilt); and the most recent commit on
`main` (`84ed599`), a live example of the exact cross-rung coherence risk the
original audit named for consumer 4/6 sharing one Mt.

## 0. What this rung is actually deciding

The three prior rungs each proved a PRIMITIVE works in isolation. None of
them wired a primitive into any of the six still-blocked consumer files
(confirmed: each rung's own §6/§8/§9 "what this rung does NOT establish"
section states its target consumer files are byte-unchanged). This rung's
job is the WIRING — and wiring surfaces facts about the surrounding
orchestration that no isolated-primitive rung could see. Two such facts were
found during this rung's own investigation (§1 below), before any code was
written, and they are the load-bearing decisions this PREREG registers.

## 1. Investigation findings (measured, not assumed) — the two facts that shape every decision below

**Finding 1 — `run_rules()` is graph-global, with no per-Mt scope
argument.** Read directly (`runners/dsl/src/py.rs:3381`,
`fn run_rules(&mut self, py, max_steps) -> usize`) and confirmed live with a
throwaway two-Mt probe (not part of this rung's committed diff): a
`Microtheory` A with a co-activating pair and a SEPARATE, unrelated
`Microtheory` B (`discrete_mode="3state"`, one Concept with
`external_field=5.0`, `state=0.0`, not yet touched this "step") were both
loaded under `can_native_reimplementation.json`. Calling `inner.run_rules()`
"on behalf of Mt A" (to let `can_native_hebbian_mint`/`_reweight` fire for
A's pair) also flipped Mt B's untouched concept from `state=0.0` to
`state=1` via `can_native_update_3state` — a Microtheory the caller never
intended to touch on this call, mutated as an unrequested side effect:

```
BEFORE any run_rules(): mt_b/b1 state = 0.0
AFTER run_rules() called 'for mt_a': mt_b/b1 state = 1
```

**Finding 2 — every native CAN rule's match pattern is unscoped across
Microtheories.** Read directly, both seeds: `can_native_update_3state`/
`_2state`/`can_native_note_coactivation`/`can_native_hebbian_mint`/
`_reweight` (`seeds/can_native_reimplementation.json`) and
`can_native_evidence_decay`/`can_native_identity_evidence_sample`/`_decay`
(`seeds/can_decay_identity.json`) all match `[mt, has_concept, c]` or
`[mt, has_concept, a], [mt, has_concept, b], ...` with NO Mt-identity
constraint — every one of the eight rules considers EVERY `Microtheory` node
in the graph on every `run_rules()` call. Finding 1 is not a fluke of one
scenario; it is the necessary consequence of this match shape.

**Consequence for `self_improvement_loop.py::self_improvement_step`
specifically.** That function iterates `for mt in
substrate.nodes("Microtheory")`, and for each Mt calls
`insight_detection.consolidate_insight` / `insight_propagation.
propagate_insight` (which, per its own docstring and the Hebbian
materialization rung's own reading, is called on `other_mt` values drawn
from that SAME `substrate.nodes("Microtheory")` set — confirmed by
`insight_propagation.py:99` `find_connected_mts`, which walks
`substrate.nodes("Microtheory")` again). If ANY of these per-Mt functions
called `run_rules()` to let a native rule fire for the Mt it was nominally
scoped to, that call would ALSO advance every OTHER native-tagged Mt in the
graph — including ones `self_improvement_step`'s own loop has not reached
yet this iteration (whose `pre_audit`/`post_audit` continuous read is still
pending) and ones it already finished (whose `_stash_post_state` already
ran, now stale). This is the abstract "shared-Mt coherence risk"
`CAN_CONSUMER_MIGRATION_RESULTS.md` §1 row 4 named for consumers 4+6 sharing
one Mt — this rung's own reading confirms it is not merely a risk between
two files' relaxation mechanisms on ONE shared Mt, but a risk between ANY
per-Mt native call and EVERY OTHER Mt in the whole graph, the moment
`run_rules()` is the trigger.

**Consequence for `mt_audit_basin`/`mt_distance_to_target` (the task's
named possible "fourth gap").** Read directly
(`runners/dsl/src/can_ops.rs:384-463`): `audit_basin`'s own three
observable numbers (`energy`, `frustration`, `coverage`) are computed by
`mt_energy`/`mt_frustration_given_state` (both already proven
representation-agnostic pure functions of a `{NodeID: f32}` marginal dict —
`CAN_COUNTERFACTUAL_PREDICTOR_RESULTS.md` §1 already reuses
`mt_frustration_given_state` this way) plus a trivial `|v|>0.05` count.
`mt_target`/`distance_to_target` are equally representation-agnostic (a
per-Concept attr read + pure vector arithmetic). **The ONLY continuous-
specific step in either function is HOW the `marginal`/`current` dict itself
gets populated** — `audit_basin` calls `mt_mean_field_marginal` internally;
a native equivalent would need to read `state` directly instead. That
substitution is a small, real, buildable Python composition (reusing
`mt_energy`/`mt_frustration_given_state` exactly as `can_counterfactual.py`
already does) — but USING it correctly requires the SAME thing Finding 1/2
block: confidence that `state` already reflects a native fixed point, which
depends on `run_rules()` having already been invoked by *something*, on
THIS Mt, without corrupting every other Mt in the graph. **Conclusion:
`mt_audit_basin`/`mt_distance_to_target` are NOT a fourth, independent gap —
they reduce to the SAME run_rules()-orchestration blocker as Hebbian/decay,
not a separately-sized problem.** Per the task's explicit instruction ("if
they turn out to be a genuine fourth gap, name and size it, don't build
it") — named here, not built.

## 2. What this means for each of the seven original blockers, restated precisely

| Blocker | Primitive status (per prior 3 rungs) | Wiring status (this rung's own finding) |
|---|---|---|
| A — no native non-mutating counterfactual predictor | CLOSED (`can_counterfactual.py`, zero graph mutation, zero `run_rules()` call anywhere in the module — confirmed by the doc's own §3 non-mutation test) | **WIREABLE, safely** — this module never touches Finding 1/2's hazard at all. |
| B — Hebbian graded reweighting non-materializing | CLOSED as a primitive (bridge + policy gate, `can_native_hebbian_bridge.py`) | **BLOCKED, precisely** — materializing REQUIRES `run_rules()` to fire `can_native_hebbian_mint`/`_reweight`; Finding 1/2 make that unsafe from inside any of the three per-Mt consumer functions. |
| Decay | CLOSED as a primitive (`can_decay_identity.json`'s `can_native_evidence_decay`) | **BLOCKED, same precise reason as B** — `can_native_evidence_decay` has the identical unscoped match shape (Finding 2); it is a RULE, requiring the SAME unsafe `run_rules()` trigger. |
| Identity dynamics (reading) | CLOSED for reading (`can_native_identity_evidence_sample`/`_decay`) | **BLOCKED, same precise reason** — also a rule, same hazard. |
| Identity dynamics (feedback) | Explicitly UNBUILT (`CAN_DECAY_IDENTITY_RESULTS.md` §8.1) — out of this rung's scope per the task | **BLOCKED** — no primitive exists to wire regardless of the orchestration question. |
| `mt_audit_basin`/`mt_distance_to_target` | Never addressed by name in any of the three rungs | **NOT a fourth gap** — reduces to the SAME run_rules()-orchestration blocker (§1 above), named/sized, not built. |

**The honest reframing this rung is making, registered before writing any
code**: Blocker B and decay are not STILL blocked for their ORIGINAL stated
reasons (non-materializing render; no native design) — those are now
factually false, the primitives exist. They are blocked for a NEWLY FOUND,
MORE PRECISE reason: wiring any rule-based native mechanism into a per-Mt
Python loop requires deciding WHEN `run_rules()` fires relative to that
loop, system-wide — and no rung in this arc, including this one, has been
asked to design that (it is a `self_improvement_step`-level orchestration
redesign, not a per-function swap). This is the SAME "coordinated pass, not
piecemeal function swaps" finding `CAN_CONSUMER_MIGRATION_RESULTS.md`
already flagged in the abstract; this rung's contribution is confirming it
concretely, with a live repro, rather than leaving it as a hypothesis.

## 3. Per-consumer migration plan

### 1. `domains/drive_curiosity.py::probe_via_what_if`

**MIGRATE.** `can_counterfactual.py` never calls `run_rules()` or mutates
the graph — Finding 1/2's hazard does not apply. Add a `discrete_mode`
gate: if `substrate.node(mt)["attrs"].get("discrete_mode")` is
`"2state"`/`"3state"`, call `can_counterfactual.predicted_info_gain` and
reshape its return into the EXACT SAME dict shape `probe_via_what_if`
already returns (drop-in, no caller changes needed in `run_curiosity`/
`run_curiosity_all_mts`); otherwise, keep the existing
`mt_mean_field_marginal`/`mt_mean_field_with_h_override` path byte-for-byte.
This is the GATED design `CAN_COUNTERFACTUAL_PREDICTOR_RESULTS.md` §7 left
as the one open decision — resolved here as gated, not unconditional,
because an Mt with no `discrete_mode` has no `state`/`temperature`
vocabulary the native formula expects (the doc's own stated reason) and
because forcing every Mt onto the native path would silently change
behaviour for every pre-existing continuous-mode caller, which the task
explicitly warns against ("do not force a full migration if real behaviour
would be degraded").

`find_ambivalent_nodes` is unchanged — already reads `state` directly,
representation-agnostic.

### 2. `domains/insight_detection.py::consolidate_insight`

**STAYS BLOCKED**, for the precise reason in §2 (not the original Blocker
B). Zero lines touched.

### 3. `domains/insight_seeking.py`

**`predict_perturbation_impact` — MIGRATE, gated identically to #1.** For a
`discrete_mode` Mt: build `current_marginal` by direct `state` read (no
relax call), call `can_counterfactual.predict_ripple`, and score both
current and predicted marginals via the ALREADY-representation-agnostic
`mt_energy`/`mt_frustration_given_state` — this is a genuine SIMPLIFICATION
over the continuous path, not just a swap: the existing `:88-103` energy
field-correction hack exists ONLY because `mt_mean_field_with_h_override`'s
marginal doesn't reflect the override consistently at the probed node under
`mt_energy`'s live-`h` read; `predict_ripple`'s own state already does,
confirmed in `CAN_COUNTERFACTUAL_PREDICTOR_RESULTS.md` §7, now actually
built rather than only sketched. For a continuous Mt: byte-unchanged.

**`find_hot_nodes` — NOT migrated, because there is nothing to migrate.**
`node_local_frustration` (`can_ops.rs:553-585`) reads `state`/`weight`
attrs directly with no relaxation call inside it at all — it is ALREADY
representation-agnostic (the same class as `sparseness_signal.py`'s
pre-existing status). `CAN_COUNTERFACTUAL_PREDICTOR_RESULTS.md` §7's own
speculation that this needs "a separate, unbuilt native twin" is corrected
here, by direct reading of the Rust source, before writing any code: no twin
is needed, none will be built, and this is reported as a positive finding
(one fewer real gap than the prior rung believed), not a null.

**`seek_insights` — ONE guard added.** It unconditionally calls
`substrate.mt_relax_to_marginal(mt)` before finding hot nodes
(`:157`). For a `discrete_mode` Mt this would CONTAMINATE `state` with the
continuous mechanism's own tanh relaxation — a latent correctness bug this
rung would otherwise be landing by only fixing `predict_perturbation_impact`
in isolation. The fix is the same shape as every other gate in this rung:
skip the relax call when `discrete_mode` is set (the documented convention
this whole arc already uses — `state` is kept current by whatever
externally drives `run_rules()` for a native Mt, exactly the same
precondition `can_counterfactual.py`'s own `predict_current_target` sanity
test documents). This is a defensive correctness fix enabled by, not
separate from, this consumer's own migration — zero new mechanism, one
`if`.

### 4. `domains/insight_propagation.py::propagate_insight`

**STAYS BLOCKED**, transitively (calls `insight_detection.
consolidate_insight`, #2, unmigrated) AND directly (`mt_relax_to_marginal`/
`mt_audit_basin` calls on `other_mt`, `:108-109,131-132`, have no native
equivalent reachable without the SAME `run_rules()` hazard). Zero lines
touched. This confirms — by direct code reading, not by re-assuming the
original audit's finding — that items 2 and 4 really are one blocker
(`consolidate_insight` is the shared call site), consistent with the task's
own instruction to assess them together.

### 5. `domains/sparseness_signal.py`

No direct `can_ops` calls (confirmed again by re-grep, §5 below). Inherits
consumer 6's status. **Zero lines touched, none needed** — matches the
original audit exactly.

### 6. `domains/self_improvement_loop.py`

**Operation-by-operation, per the task's own required granularity:**

| Operation | Verdict | Why |
|---|---|---|
| `relax()` (`mt_relax_to_marginal`) | STAYS continuous | A native equivalent means driving `run_rules()` per-Mt inside this file's own loop — Finding 1/2's hazard, directly. |
| `maybe_hebbian` | STAYS continuous | Same — the primitive (Blocker B) is real, the wiring is unsafe per §2. |
| `maybe_decay_J`/`maybe_decay_h` | STAYS continuous | Same — decay's primitive is real, the wiring is unsafe per §2. |
| `maybe_update_identity` | STAYS continuous | Feedback half never built (explicitly out of scope) AND the reading half is rule-based (same hazard) even if it weren't. |
| `nudge_identity_on_flipped` | STAYS continuous | Depends on the same unbuilt feedback half. |
| `self_improvement_step`'s `mt_audit_basin`/`mt_distance_to_target` calls | STAYS continuous | Not a fourth gap (§1) — reduces to the same orchestration blocker. |

**Zero lines touched in this file.** This is a real, complete answer to the
task's own question ("investigate precisely which of its seven real
operations can migrate now and which genuinely still can't") — the answer
is zero of seven, for ONE unifying, newly-precise reason rather than three
separate ones, which is itself the main finding of this rung for this
consumer.

## 4. What is explicitly NOT being built here (per the task's own scope)

- The identity-feedback mechanism.
- Any fix to `mt_audit_basin`/`mt_distance_to_target` (correctly named as
  not a fourth gap, not built regardless).
- A `self_improvement_step`-level redesign of WHEN `run_rules()` fires
  relative to the per-Mt loop — this is the real follow-on this rung
  surfaces, named precisely here so a future rung can size it: it would
  need to decide (a) whether native and continuous Mts can coexist in one
  step at all without cross-contamination, (b) whether `run_rules()` should
  be called ONCE per step (for the whole graph) rather than never, and (c)
  how `detect_insight`'s per-step frustration comparison behaves for an Mt
  whose `state` may have been advanced by a native rule mid-step. Not
  attempted here.
- Any change to `can_ops.rs`'s live math, any new Rust Term.

## 5. Removal analysis plan (phase 3)

Re-run the task's own 16-function grep across `domains/*.py`, `worlds/*.py`,
`scripts/*.py`, `tests/*.py` AFTER the two migrations above land. Given both
migrations are GATED (dual-path, continuous branch preserved byte-for-byte),
the expectation, stated before running it: every continuous-mechanism
function (`mt_mean_field_marginal`, `mt_mean_field_with_h_override`,
`mt_energy`, `mt_frustration_given_state`, `mt_audit_basin`,
`mt_relax_to_marginal`, `node_local_frustration`) keeps its existing real
call sites (the continuous branches, byte-unchanged) alongside the new
native branches — meaning no removal is expected from the two migrated
files. Every function used exclusively by unmigrated consumers 2/4/6
(`mt_hebbian_update_J`, `mt_decay_J`, `mt_decay_h`, `mt_update_identity_
dynamics`, `concept_nudge_identity`, `mt_distance_to_target`) is expected to
remain fully real, unchanged. `mt_conflicting_nodes`/`mt_pairwise_
similarity` (used by `conflict_detection.py`/`redundancy_detection.py`, not
among the six named consumers) are out of scope and expected to remain
real. `concept_apply_evidence` (Bigville) is untouched, expected to remain
real. `mt_target` will be checked precisely for whether its ONLY Python
call sites are test-direct (`s.mt_target(mt)` in `test_can_ops.py`/
`test_can_migration.py`) versus a real indirect use via
`mt_distance_to_target`'s own internal Rust call
(`py.rs:2350`) — if the latter, `mt_target` is a real, active dependency of
a real, active, unmigrated consumer (`self_improvement_loop.py:161`) despite
having no DIRECT Python caller, and is not a removal candidate. This
prediction will be checked against the actual re-run grep, not assumed.

## 6. Regression plan

Run and report per-file (not aggregated), the task's own required file set:
`test_can_ops.py`, `test_can_migration.py`, `test_identity_field.py`,
`test_insight_seeking.py`, `test_insight_detection.py`,
`test_insight_propagation.py`, `test_drive_curiosity.py`,
`test_sparseness_signal.py`, `test_self_improvement_loop.py`,
`test_can_native_reimplementation.py`, `test_can_hebbian_materialization.py`,
`test_can_decay_identity.py`, `test_can_counterfactual.py`,
`test_can_belief_quantization.py`, `test_bigville_can_native_migration.py`,
`test_evidence_axis_infer.py`, `test_causal_attitude_networks.py`, plus the
new dedicated test file this rung adds
(`tests/test_can_final_migration.py`, following this arc's own convention of
one new file per rung with the real before/after demonstrations). Run the
FULL merged set together early (not just at the end), per the standing
house instruction — the most recent commit on `main` found exactly this
kind of cross-rung interaction bug by doing so.

No Rust build expected unless phase 3 finds a genuine removal candidate; if
it does, `scripts/engine_build.sh` under the documented toolchain +
`systemd-run` memory guard, then full `cargo test --release --lib
-- --test-threads=1`.
