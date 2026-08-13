# Native `external_field` decay, closing `maybe_decay_h` — PREREG

Base `main @ 08989e6` ("Merge can-mt-scoped-rules: additive run_rules_scoped,
isolates per-Mt fixpoints, GO"), verified via `git log --oneline -1 main`
before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-external-field-decay`, branch
`can-external-field-decay`.

This rung closes the ONE named remaining blocker in
`CAN_MT_SCOPED_RULES_RESULTS.md` §4c: `maybe_decay_h`
(`domains/self_improvement_loop.py:136-151`) "STAYS BLOCKED for native Mts
... no rule anywhere decays `external_field`." Explicitly out of scope:
identity-feedback (`maybe_update_identity`/`nudge_identity_on_flipped`),
any change to `can_native_update_3state`/`_2state`'s own local-field READ of
`external_field`, any change to the continuous `can_ops.rs::decay_h`, any
new Rust Term.

---

## 0. Re-verification of the exact blocker, live, before any code change

Direct read, this session, of `domains/self_improvement_loop.py:136-151`
(quoted verbatim in the task) — confirmed unchanged from the task's own
quote. Direct grep of both native CAN seeds for `external_field` as a
`set_attr` effect target:

```
$ grep -n '"external_field"' seeds/can_native_reimplementation.json seeds/can_decay_identity.json
seeds/can_native_reimplementation.json:158,242,342,426,558,644   (all READS, inside where/effects local-field formula)
seeds/can_decay_identity.json: (zero hits)
```

Confirmed: `external_field` is read 6 times (3-state ×2 branches, 2-state
×... — both discrete-mode update rules' own `IfThenElse` local-field
formula), written zero times, in either native seed. `domains/
can_counterfactual.py` reads it (`local_field_term`) and ALSO never writes
it to the real graph — every counterfactual override lives in an in-memory
`env` dict passed to `Term.evaluate`, never `substrate.set_attr` (confirmed
by direct read, `can_counterfactual.py:27-29`'s own docstring claim: "Nothing
in this module calls `run_rules()` or writes to any node/edge attr" — cross-
checked against the actual function bodies, `predict_single_step_target`/
`predict_ripple`/`predicted_info_gain`, none contain a `set_attr` call).

**The blocker is exactly as the task states it: a genuine rule-body gap, not
an orchestration hazard.** This rung's job is to close it with a THIRD decay
rule, mirroring `can_native_evidence_decay` (`seeds/can_decay_identity.json`
rule 1) and `can_native_identity_evidence_decay` (rule 3).

---

## 1. The rule design — same shape, one required generalisation

### 1a. What transfers directly

Both existing decay rules share this shape, applied per-tick:
- Epoch-gated: `Gt(mt.can_tick, <ledger>.<own>_decay_tick)` — fires at most
  once per external tick.
- Policy-gated: the SAME `Or(update_policy==adaptive, And(update_policy==
  hybrid, Not(allow_h_drift==0)))` Term, re-expressing `mt_allows(mt,
  "allow_h_drift")` as graph data (not a Python check).
- ONE rule bumps every ledger field via `IfThenElse` (not sibling
  confirm/disconfirm rules) — reusing `CAN_NATIVE_REIMPLEMENTATION_RESULTS.
  md` §3's starvation-fix lesson pre-emptively.
- Writes its own `..._decay_tick` = `mt.can_tick` so the epoch gate paces it.

This all transfers to `external_field` unchanged in spirit: same epoch-gate
shape, same policy-gate Term (byte-identical subtree, copy-pasted), same
"one rule, IfThenElse-branched" shape, own `external_field_decay_tick` attr
(own epoch counter — never shared with the Hebbian or identity ledgers'
own tick attrs, matching rule 3's own stated reason for NOT sharing
`identity_evidence_tick`: a decay tick must not be misread as a different
event's sampling tick).

### 1b. What does NOT transfer verbatim, and why — the one required
generalisation

`evidence_confirm`/`evidence_disconfirm`/`identity_evidence_confirm`/
`identity_evidence_disconfirm` are all **non-negative integer counts,
incremented by exactly +1 by the SAME rule family that will decay them**
(`can_native_hebbian_reweight`, `can_native_identity_evidence_sample`, both
`Plus(x, 1)`). Their existing decay body is:

```
IfThenElse(Gt(x, 0), Plus(x, -1), x)
```

This is floor-correct ONLY because `x` is guaranteed to be a non-negative
integer: `Gt(x,0)` implies `x >= 1` (integer), so `x - 1 >= 0` always. It is
NOT a general "clamp toward zero" — it relies on integrality and one-
sidedness.

`external_field` (h) is neither. Confirmed by direct read,
`tests/test_can_native_reimplementation.py:75-76`: `h = field_rng.uniform(
-1, 1)` — a REAL, SIGNED float, set exogenously (by whichever world adapter
or test harness constructs the Concept), never incremented by any native
rule in integer steps. Applying the existing body verbatim to a value like
`h=0.3` would give `0.3 - 1 = -0.7` — NEGATIVE, breaking the "never
negative" floor guarantee the other two rules earned, and for `h<0` the
existing body's `Gt(x,0)` guard would simply never fire, so a negative field
would never decay at all under literal copy-paste.

**Registered prediction, to be checked against the build**: the correct
generalisation is a SYMMETRIC clamp-toward-zero, using `Max`/`Min` — both
pre-existing Rust Terms (confirmed already used declaratively in unrelated
seeds, e.g. `seeds/arousal_window_coreg.json:1104,1143,1188`, zero new Rust
needed):

```
new_h = IfThenElse(Gt(h, 0), Max([Minus(h, 1), Lit(0)]),
        IfThenElse(Lt(h, 0), Min([Plus([h, 1]), Lit(0)]), h))
```

i.e. `max(h-1, 0)` when positive, `min(h+1, 0)` when negative, unchanged at
exactly 0. This is registered as the SAME "linear step toward zero, floored
at the boundary" SHAPE the other two rules use, generalised (not
redesigned) to handle a signed quantity — the one explicit deviation this
rung registers up front, exactly as `CAN_DECAY_IDENTITY_RESULTS.md` §1
registered its own floor-at-0 deviation from bare `translate` up front.

### 1c. Registered prediction — the quantum-magnitude mismatch

**Predicted before building, to be checked against the live demo**: unlike
the two existing ledgers (whose natural unit is 1 because their own
accumulation rule ALSO steps by exactly 1, so growth and decay are
naturally commensurate — `can_ops.rs:733`'s "persistent co-activation
maintains J; transient fades" property depends on this), `external_field`
has NO native accumulation rule at all (§0) — it is set once, exogenously,
typically to a value in `[-1, 1]` per this codebase's own test-harness
convention (`field_rng.uniform(-1, 1)`). A fixed quantum of magnitude 1
applied to a field of that typical magnitude will fully zero it out on the
FIRST eligible decay tick, not over a multi-tick trajectory — a materially
different dynamic from the continuous `h *= (1 - 0.0001)` (~1000s of ticks
to decay meaningfully) or from the other two ledgers (whose demonstrated
decay trajectories in `CAN_DECAY_IDENTITY_RESULTS.md` §4 span 4-10 ticks
because their accumulated counts are typically > 1). To demonstrate a
genuine multi-tick trajectory (mirroring that RESULTS doc's own demo
convention), this rung's live demo will deliberately seed `external_field`
at a magnitude > 1 (e.g. ±3.5) — legitimate, since nothing constrains `h` to
`[-1,1]`; that is only the random-draw test harness's own convention, and
`can_counterfactual.py` already treats `external_field` as an unconstrained
float. **This will be reported as a genuine, honest asymmetry** — not
smoothed into "works exactly like the other two" — in the RESULTS doc's
tunability section (task point 3).

---

## 2. Same-tick-race investigation — registered prediction

`CAN_DECAY_IDENTITY_RESULTS.md` §3 found and fixed a real race: decay could
fire on the SAME tick as reinforcement for the Hebbian ledger, because
`can_native_hebbian_reweight` (the writer) and the decay rule are BOTH
eligible once `can_tick` advances, and a `+1`/`-1` same-tick pair cancels to
net zero under persistent reinforcement — contradicting "persistent
co-activation maintains J."

**Registered prediction, to be checked by direct read before writing the
rule**: this race does NOT apply to `external_field`, because — unlike the
Hebbian/identity ledgers — **no native rule anywhere writes `external_field`
at all** (§0's grep is definitive: zero `set_attr` hits on `external_field`
in either seed, and `can_counterfactual.py` never calls `substrate.set_attr`
on it either). A same-tick race requires a writer to race against; decay
would be the ONLY writer this attr ever gets under the native mechanism.
**If confirmed, the new rule needs no same-tick-skip guard** — its epoch
gate (`Gt(mt.can_tick, c.external_field_decay_tick)`) is sufficient pacing,
with no `evidence_tick == can_tick`-style exclusion needed (there is no
`evidence_tick` for this attr to check). This will be verified by direct
read (repeating §0's grep) immediately before writing the rule, and the
result reported honestly either way.

---

## 3. Wiring into `maybe_decay_h` — registered prediction

`maybe_decay_J` (`domains/self_improvement_loop.py:113-133`) is the direct
template:

```python
def maybe_decay_J(substrate, mt, decay_rate: float = 0.001) -> int:
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    if not mt_allows(substrate, mt, "allow_Hebbian_J"):
        return 0
    return substrate.mt_decay_J(mt, decay_rate)
```

**Registered plan**: `maybe_decay_h` gets the SAME shape — native branch
calls `scoped_settle(substrate, mt)` (isolated `run_rules_scoped`, letting
whichever native rule is dirty and gated-open fire, exactly `maybe_decay_J`'s
own precedent and `CAN_MT_SCOPED_RULES_RESULTS.md` §4c's "one shared
fixpoint" finding — the new external-field decay rule will very likely
already have fired inside an earlier `relax()`/`maybe_hebbian()` call this
same step, same as `maybe_decay_J` already documents for itself); continuous
branch (the `mt_allows` check + `substrate.mt_decay_h(mt, decay_rate)`)
stays BYTE-UNCHANGED. `decay_rate` stays silently unused on the native
branch, matching `maybe_decay_J`'s own precedent exactly (no native analog
for a continuous rate parameter — registered, not newly invented, by this
rung).

---

## 4. Decay-rate tunability — registered question

Task point 3 asks whether `external_field`'s decay needs an independently
tunable rate. **Registered answer, to be checked against the build**: NO —
for consistency with the standing discipline (`CLAUDE.md` "SHAPES, NOT
NUMBERS": *"a scalar knob is not a simplification... it is the unpaid
debt"*), the new rule reuses the exact fixed 1-quantum shape, no new
parameter. The interesting finding (§1c) is not that a rate parameter is
missing, but that the FIXED quantum's relationship to `external_field`'s
typical magnitude is qualitatively different from its relationship to the
other two ledgers' typical magnitudes — reported as an honest asymmetry, not
resolved by adding a knob.

---

## 5. Live demonstration plan (mirrors `CAN_DECAY_IDENTITY_RESULTS.md` §4
exactly, adapted to `external_field`)

1. **Adaptive, unreinforced, multi-tick decay, floored at 0**: a Concept
   seeded with `external_field = 3.5` (magnitude > 1, per §1c), `run_rules`
   driven through several `can_tick` advances with no writer touching
   `external_field`; expect trajectory `[2.5, 1.5, 0.5, 0.0, 0.0, ...]`,
   never negative.
2. **Negative field, symmetric ceiling at 0**: `external_field = -3.5`,
   same drive; expect `[-2.5, -1.5, -0.5, 0.0, 0.0, ...]`, never positive —
   proves the Max/Min generalisation (§1b) is genuinely symmetric, not a
   one-sided floor copy-paste that happens to work for positive values only.
3. **Frozen policy — blocked completely**: same setup, `update_policy=
   "frozen"`; `external_field` must stay byte-unchanged across many ticks,
   and (matching rule 1's own precedent) `external_field_decay_tick` should
   never even be written.
4. **Composition with the local-field formula**: a 2-Concept native `3state`
   Mt where one Concept's `external_field` is set large enough to dominate
   the local-field sum and force `state=+1`; decay `external_field` toward 0
   over several ticks (via the scoped native mechanism, not manual
   `set_attr`) while re-running `can_native_update_3state`; expect the
   Concept's OWN `state` decision to flip away from `+1` once the decayed
   field can no longer clear the `atanh(0.5)`-scaled threshold — demonstrating
   the decayed value is genuinely READ by the SAME formula that already
   consumes `external_field`, not just changed in isolation.
5. **Same-tick-race check (if §2's prediction is wrong)**: if direct read at
   build time finds any writer, add and demonstrate the matching
   same-tick-skip guard, mirroring `CAN_DECAY_IDENTITY_RESULTS.md` §3's own
   `test_evidence_decay_never_races_reinforcement_in_the_same_tick`.

---

## 6. Regression plan

`tests/test_can_decay_identity.py`, `tests/test_can_native_reimplementation.
py`, `tests/test_can_mt_scoped_consumers.py`, `tests/
test_self_improvement_loop.py` must all stay green. New file:
`tests/test_can_external_field_decay.py`. Scoped CAN regression sweep
(the same file list `CAN_DECAY_IDENTITY_RESULTS.md`/
`CAN_MT_SCOPED_RULES_RESULTS.md` both used) re-run in full.

---

## 7. Out of scope, restated

Identity-feedback (`maybe_update_identity`/`nudge_identity_on_flipped`);
any change to `can_native_update_3state`/`_2state`'s READ of
`external_field`; any change to `can_ops.rs::decay_h`; any new Rust Term (if
this rung finds it genuinely needs one, it stops and reports why — predicted
NOT needed, since `Max`/`Min` already exist and are already used
declaratively elsewhere in this tree).
