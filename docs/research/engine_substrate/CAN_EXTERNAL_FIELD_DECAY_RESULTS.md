# Native `external_field` decay, closing `maybe_decay_h` — RESULTS

Prereg: `CAN_EXTERNAL_FIELD_DECAY_PREREG.md`, same worktree/branch, base
`main @ 08989e6` ("Merge can-mt-scoped-rules: additive run_rules_scoped,
isolates per-Mt fixpoints, GO"), verified via `git log --oneline -1 main`
before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-external-field-decay`, branch
`can-external-field-decay`.

This rung closes the ONE named remaining blocker in
`CAN_MT_SCOPED_RULES_RESULTS.md` §4c: `maybe_decay_h`
(`domains/self_improvement_loop.py:136-151`, quoted verbatim in the task) —
"STAYS BLOCKED for native Mts ... no rule anywhere decays `external_field`."

**Verdict, up front.** The blocker is closed: `can_native_external_field_decay`
(`seeds/can_decay_identity.json` v1.1.0) is the first native rule ever to
write `external_field`, and `maybe_decay_h` is now migrated with the same
gated dual-path pattern `maybe_decay_J` already established. Zero new Rust —
`Max`/`Min` (pre-existing Terms, already used declaratively elsewhere in
this tree) replace the existing rules' one-sided integer-floor body with a
symmetric clamp, a REQUIRED generalisation (not a redesign) because
`external_field`, unlike the two existing evidence ledgers, is a signed
float with no native accumulation rule. The same-tick race
`CAN_DECAY_IDENTITY_RESULTS.md` found and fixed for the Hebbian ledger does
**not** apply here — confirmed by direct grep, not assumed: no writer of
`external_field` exists anywhere for decay to race against. Composition
with `can_native_update_3state`'s own local-field formula is demonstrated
live: decaying `external_field` genuinely flips a Concept's discrete state
decision once the decayed value can no longer clear the threshold. The
whole-arc consequence, precisely: 5 of `self_improvement_loop.py`'s 7
operations are now natively migrated; the remaining 2
(`maybe_update_identity`/`nudge_identity_on_flipped`) stay blocked on the
SEPARATE, already-named identity-feedback gap, exactly as the task
predicted and scoped out.

---

## 0. Re-verification of the exact blocker, live

Direct read of `domains/self_improvement_loop.py:136-151` at this rung's
base commit confirmed byte-identical to the task's own quote. Direct grep,
both native seeds, for `external_field` as a `set_attr` effect target:

```
$ grep -n '"external_field"' seeds/can_native_reimplementation.json seeds/can_decay_identity.json
seeds/can_native_reimplementation.json: 6 hits, all inside where/effects
  local-field READS (can_native_update_3state / _2state)
seeds/can_decay_identity.json (pre-branch): 0 hits
```

`domains/can_counterfactual.py` reads `external_field`
(`local_field_term`) but never writes it to the real graph — confirmed by
direct read of `predict_single_step_target`/`predict_current_target`/
`predict_ripple`/`predicted_info_gain`: every override lives in an
in-memory `env` dict passed to `Term.evaluate`, zero `substrate.set_attr`
calls anywhere in the module. **The task's framing is exactly correct**: a
genuine rule-body gap, not an orchestration hazard — scoping could never
have closed this.

---

## 1. The rule design — same shape, one required generalisation

`can_native_external_field_decay` (`seeds/can_decay_identity.json` v1.1.0,
built via `scripts/_build_can_external_field_decay_seed.py`, the same
`tools/*`-class one-off authoring-script precedent
`scripts/_build_can_decay_identity_seed.py` already used, to avoid a
hand-typo in a nested Term-tree):

**What transfers directly from `can_native_evidence_decay`/`can_native_
identity_evidence_decay`:**
- Epoch-gated: `Gt(mt.can_tick, c.external_field_decay_tick)` — fires at
  most once per external tick.
- Policy-gated: the BYTE-IDENTICAL `Or(update_policy==adaptive,
  And(update_policy==hybrid, Not(allow_h_drift==0)))` Term subtree,
  re-expressing `mt_allows(mt, "allow_h_drift")` as graph data.
- ONE rule, `IfThenElse`-branched, not a sibling pair.
- Own epoch attr (`external_field_decay_tick`), never shared with the
  other two ledgers' own tick attrs.

**What does NOT transfer verbatim — registered in the PREREG, confirmed by
build:** `evidence_confirm`/`evidence_disconfirm`/`identity_evidence_
confirm`/`identity_evidence_disconfirm` are non-negative integer counts,
incremented by exactly `+1` by the SAME rule family that decays them
(`can_native_hebbian_reweight`, `can_native_identity_evidence_sample`).
Their existing decay body, `IfThenElse(Gt(x,0), Plus(x,-1), x)`, is
floor-correct ONLY because `x` is guaranteed a non-negative integer.
`external_field` is neither: confirmed by direct read,
`tests/test_can_native_reimplementation.py:75-76` (`h =
field_rng.uniform(-1, 1)`) — a real, SIGNED float set exogenously, never
incremented by any native rule in integer steps. Applying the existing
body verbatim to e.g. `h=0.3` would give `0.3 - 1 = -0.7` (negative,
breaking the floor guarantee); for `h<0` the existing `Gt(x,0)` guard would
never fire, so a negative field would never decay under literal
copy-paste.

**The generalisation built**, using `Max`/`Min` (pre-existing Rust Terms;
confirmed already used declaratively in unrelated seeds, e.g.
`seeds/arousal_window_coreg.json:1104,1143,1188` — zero new Rust needed,
confirmed by `git diff --stat main -- '*.rs'` being empty):

```
new_h = IfThenElse(Gt(h,0), Max([Minus(h,1), Lit(0)]),
        IfThenElse(Lt(h,0), Min([Plus([h,1]), Lit(0)]), h))
```

`max(h-1, 0)` when positive, `min(h+1, 0)` when negative, unchanged at
exactly 0 — the SAME "linear step toward zero, floored at the boundary"
SHAPE, generalised (not redesigned) to a signed quantity. This is this
rung's one explicit, registered deviation, exactly mirroring how
`CAN_DECAY_IDENTITY_RESULTS.md` §1 registered its own floor-at-0 deviation
from bare `translate`.

---

## 2. Same-tick-race investigation — CONFIRMED does not apply

`CAN_DECAY_IDENTITY_RESULTS.md` §3 found a real race for the Hebbian
ledger: decay and `can_native_hebbian_reweight` are both eligible the
instant `can_tick` advances, and a same-magnitude `+1`/`-1` pair cancels
exactly under persistent reinforcement, requiring a same-tick-skip guard
(`coact.evidence_tick == mt.can_tick`).

**Checked directly before writing the rule** (PREREG §2's registered
prediction): §0's grep is definitive — `external_field` has **zero
writers** anywhere in either native seed, and `can_counterfactual.py` never
writes it either. There is no reinforcement event for decay to race
against; decay is the ONLY writer this attr will ever get under the native
mechanism. **Confirmed: no same-tick-skip guard is needed.** The rule's
epoch gate (`Gt(mt.can_tick, c.external_field_decay_tick)`) is sufficient
pacing on its own — reported as a genuine, structural asymmetry with the
Hebbian/identity cases, not an oversight.

---

## 3. Wiring into `maybe_decay_h`

`domains/self_improvement_loop.py:136-163`, mirroring `maybe_decay_J`'s own
shape exactly:

```python
def maybe_decay_h(substrate, mt, decay_rate: float = 0.0001) -> int:
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    if not mt_allows(substrate, mt, "allow_h_drift"):
        return 0
    return substrate.mt_decay_h(mt, decay_rate)
```

Native branch: `scoped_settle(substrate, mt)` — isolated `run_rules_scoped`,
letting whichever native rule is dirty and gated-open fire (the SAME "one
shared fixpoint" architecture `CAN_MT_SCOPED_RULES_RESULTS.md` §4c already
documented for `relax`/`maybe_hebbian`/`maybe_decay_J`: an earlier call this
same step very likely already advanced `external_field_decay_tick` for this
`can_tick`, making this call idempotent — not a bug, the graph's own
priority order deciding what needed to happen). Continuous branch
(`mt_allows` check + `substrate.mt_decay_h(mt, decay_rate)`) is
**byte-unchanged** — confirmed by the diff (§7). `decay_rate` stays
silently unused on the native branch, matching `maybe_decay_J`'s own
precedent exactly.

---

## 4. Decay-rate tunability — finding

Task point 3 asked whether `external_field` needs an independently tunable
decay rate. **Answer: no new parameter was added, and the reasoning is not
"it obviously wasn't needed" — it is a genuine, reportable asymmetry.**

The other two ledgers' fixed quantum of 1 is *self-calibrating*: their own
growth rule (`can_native_hebbian_reweight`/`can_native_identity_evidence_
sample`) increments by the SAME `+1`, so decay-vs-reinforcement dynamics are
naturally commensurate — this is WHY `can_ops.rs:733`'s "persistent
co-activation maintains J; transient co-activation fades" property holds
for the native mechanism at all. `external_field` has **no native
accumulation rule of any kind** (§0) — it is set once, exogenously, by
whichever world adapter or test harness constructs the Concept, typically
to a magnitude in `[-1, 1]` per this codebase's own test-harness convention
(`field_rng.uniform(-1, 1)`, `tests/test_can_native_reimplementation.py:75`).
**A fixed quantum of 1 applied to a field of that typical magnitude fully
zeros it out on the FIRST eligible decay tick — a single-tick reset, not a
gradual multi-tick fade.** This is qualitatively different from the
continuous `h *= (1 - 0.0001)` (thousands of ticks to decay meaningfully)
and from the other two ledgers' demonstrated multi-tick trajectories
(`CAN_DECAY_IDENTITY_RESULTS.md` §4 spans 4-10 ticks because accumulated
counts are typically > 1 there).

**The design decision, made deliberately, not by default**: keep the fixed
1-quantum shape anyway, for consistency with the standing discipline
(`CLAUDE.md` "SHAPES, NOT NUMBERS": *"a scalar knob is not a
simplification... it is the unpaid debt"*) rather than open a fresh rate
parameter for one quantity. **The honest cost of that decision, reported
precisely**: for realistically-scaled `external_field` values (the
codebase's own `[-1,1]` convention), native `h`-decay behaves as an
effectively instantaneous reset under this rung's design, not a gradual
fade — a real, measured behavioural difference from the continuous
mechanism, demonstrated directly in §5's live numbers (this rung
deliberately seeds `external_field` at magnitude 3.5, ABOVE the codebase's
own typical range, specifically to make the multi-tick trajectory visible
at all — a field drawn from the typical `[-1,1]` range would show only ONE
non-trivial decay step before flooring/ceiling at 0). This is named as a
real, open design question for any FUTURE caller that relies on gradual
native h-decay at realistic field magnitudes — not resolved by this rung,
reported instead of smoothed over.

---

## 5. Live demonstrations — all on the real engine, real numbers

`tests/test_can_external_field_decay.py`, run via
`PYTHONPATH=".:runners/dsl/python" python3 -m pytest
tests/test_can_external_field_decay.py -q -s`:

### (a) Positive field, adaptive, decays toward zero, floored

```
external_field decay trajectory (adaptive, positive, from 3.5): [2.5, 1.5, 0.5, 0, 0, 0, 0, 0]
```
Exactly one quantum per tick, floors at 0 on the 4th tick, never negative
(per §4's finding, a field this large is deliberately chosen to show a
real multi-tick trajectory).

### (b) Negative field, adaptive, symmetric ceiling at zero

```
external_field decay trajectory (adaptive, negative, from -3.5): [-2.5, -1.5, -0.5, 0, 0, 0, 0, 0]
```
Confirms the Max/Min generalisation (§1) is genuinely symmetric, not a
one-sided floor that happens to work for positive values only — the exact
mirror-image trajectory, never crossing into positive territory.

### (c) Frozen policy — blocked completely

```
frozen, unreinforced through tick 7: external_field=3.5 external_field_decay_tick=-1
```
`external_field` stays byte-unchanged and `external_field_decay_tick` never
advances past its pre-set sentinel — the rule never fires at all under
`frozen`, matching `can_native_evidence_decay`'s own precedent
(`test_evidence_decay_blocked_when_frozen`: "never even written").

### Hybrid, both directions (bonus parity check, not explicitly required
but mirrors the established test suite's own convention)

```
hybrid allow_h_drift=0: external_field=3.5 (must stay 3.5)
hybrid allow_h_drift absent (default True): external_field=0 (must reach 0, 5 ticks of decay from 3.5)
```

### (d) Composition with `can_native_update_3state`'s own local-field
formula — the decayed value is genuinely READ, not just changed in isolation

Single Concept, no `causal_influence` edges (local field = `external_field`
+ `identity_field`(=0) + 0), `temperature=1.0`, threshold
`atanh(0.5)≈0.5493`:

```
field trajectory: [2.5, 1.5, 0.5, 0, 0]
state trajectory: [1, 1, 0, 0, 0]
```

`state` FLIPS from `+1` to `0` at exactly the tick the decayed field
(`0.5`) can no longer clear the threshold (`0.5 < 0.5493`) — both
`can_native_external_field_decay` and `can_native_update_3state` run inside
the SAME `run_rules` fixpoint each tick, and the discrete update genuinely
tracks the post-decay value. This proves composition, not merely
co-existence.

### Composition via `scoped_settle` (the exact mechanism `maybe_decay_h`
now calls), plus two-Mt isolation re-proven for this rule

```
scoped to mt_a only, 4 ticks: field_a=0 field_b=3.5 (must be unchanged 3.5)
```
`mt_a`'s own field decayed 4 quanta from 3.5 to 0 (floored); `mt_b`, an
independent native Mt in the SAME graph, is completely untouched —
`CAN_MT_SCOPED_RULES_RESULTS.md` §3's own two-Mt isolation guarantee holds
for this new rule too, reached through the exact orchestration function
`maybe_decay_h`'s native branch calls.

### Same-tick race — no test needed, structurally confirmed instead

Unlike `test_can_decay_identity.py`'s own
`test_evidence_decay_never_races_reinforcement_in_the_same_tick`, no
matching test was written here. Per §2, this is not an omission: there is
no writer of `external_field` anywhere for decay to race against, confirmed
by direct grep of the rule/module source (a structural fact about the code,
not something a runtime test could meaningfully strengthen — a test would
only be able to confirm "nothing else changed the value," which every test
above already does incidentally).

---

## 6. Whole-arc consequence — `self_improvement_loop.py`'s 7 operations

| # | Operation | Verdict | Reason |
|---|---|---|---|
| 1 | `relax` | MIGRATED | `CAN_MT_SCOPED_RULES_RESULTS.md` §4c, unchanged here |
| 2 | `maybe_hebbian` | MIGRATED | same, unchanged here |
| 3 | `maybe_decay_J` | MIGRATED (re-targeted quantity) | same, unchanged here |
| 4 | `maybe_decay_h` | **MIGRATED — closed by this rung** | `can_native_external_field_decay`, §1-3 above |
| 5 | `_audit_basin`/`_stash_post_state` (`mt_audit_basin`/`mt_distance_to_target` composition) | MIGRATED | same, unchanged here |
| 6 | `maybe_update_identity` | **STAYS BLOCKED** | identity-feedback gap (§below) — explicitly out of this rung's scope |
| 7 | `nudge_identity_on_flipped` | **STAYS BLOCKED** | same identity-feedback gap |

**5 of 7 operations are now natively migrated.** The remaining 2 are
blocked on a gap this rung was explicitly told NOT to solve: no native rule
anywhere writes `identity_field` from the identity-evidence reading
(`CAN_DECAY_IDENTITY_RESULTS.md` §2, `CAN_MT_SCOPED_RULES_RESULTS.md` §5,
both confirmed independent of this rung's diff — `identity_field` does not
appear anywhere in `seeds/can_decay_identity.json`'s new rule, confirmed by
direct read of the rule's own `effects`, which touch only `external_field`
and `external_field_decay_tick`). **This is exactly the outcome the task
itself predicted**: "if this closes `maybe_decay_h` cleanly ...
`maybe_update_identity`/`nudge_identity_on_flipped` remain genuinely
blocked on identity-FEEDBACK, a separate, already-named, still-open gap
this rung does NOT need to solve."

`self_improvement_loop.py`'s module docstring/comments were checked for
stale references: `maybe_decay_h`'s own docstring is rewritten (§3);
`maybe_update_identity`/`nudge_identity_on_flipped`'s "STAYS BLOCKED"
docstrings are untouched and remain accurate (they never referenced
`maybe_decay_h`'s status). No other stale "no native analog"/"blocked"
language for `external_field`/h-decay remains anywhere in the file —
confirmed by grep (`grep -n "BLOCKED\|blocked" domains/
self_improvement_loop.py`: only the two identity-feedback docstrings
remain, correctly).

---

## 7. What was built, precisely

- `seeds/can_decay_identity.json` v1.0.0 → v1.1.0: one new rule
  (`can_native_external_field_decay`), one new declarative
  `DimensionGenerator` (local_id 4, `external_field_decay` — documentation
  only, matching local_id 1/2's own "declared, never literally invoked"
  convention), one new `Concept` documentation node
  (`can_native_external_field_decay`). Zero new productions/edges.
- `domains/self_improvement_loop.py`: `maybe_decay_h` gains the native
  branch (§3); docstring rewritten to reflect MIGRATED status honestly.
  Continuous branch byte-unchanged.
- `scripts/_build_can_external_field_decay_seed.py`: one-off authoring
  script (the `tools/*`-class precedent), idempotent (replaces the named
  rule if re-run, never duplicates).
- `tests/test_can_external_field_decay.py`: 6 new tests (all passing, all
  printing real numbers — §5 above).

Zero new Rust — confirmed:

```
$ git diff --stat main -- '*.rs'
(empty)
```

`Max`/`Min` (used by the new rule's `effects`) and `Minus`/`Plus`/
`IfThenElse`/`Gt`/`Lt`/`Or`/`And`/`Not`/`Eq`/`Attr` (all reused from the
existing two decay rules) are all pre-existing Terms.

---

## 8. Regression

**New test file alone:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_external_field_decay.py -q -s
6 passed in 0.21s
```

**Task-named regression set (the 4 named files + this rung's new file):**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_decay_identity.py tests/test_can_native_reimplementation.py \
  tests/test_can_mt_scoped_consumers.py tests/test_self_improvement_loop.py \
  tests/test_can_external_field_decay.py -q
50 passed in 1.35s
```

**Broader CAN-adjacent sweep (the same file list `CAN_DECAY_IDENTITY_
RESULTS.md`/`CAN_MT_SCOPED_RULES_RESULTS.md` both used, plus this rung's
new file):**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_bigville_can_native_migration.py \
  tests/test_identity_field.py tests/test_self_improvement_loop.py \
  tests/test_can_decay_identity.py tests/test_can_counterfactual.py \
  tests/test_insight_seeking.py tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_hebbian_materialization.py \
  tests/test_can_final_migration.py tests/test_can_mt_scoped_rules.py tests/test_can_mt_scoped_consumers.py \
  tests/test_can_external_field_decay.py -q
204 passed in 10.65s
```

Zero failures, zero regressions, no paired failing-node-id list needed.

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty, matching `CAN_DECAY_IDENTITY_RESULTS.md`'s own precedent for a
seed-only rung.

**This rung did NOT re-run the full tree-wide `failure_baseline_sweep.py`
sweep** `CAN_MT_SCOPED_RULES_RESULTS.md` §6c ran (782 files, ~38 minutes) —
the task's own regression scope named 4 specific files + a new test file,
and this rung's diff touches exactly the same two files
(`domains/self_improvement_loop.py`, `seeds/can_decay_identity.json`) that
rung's own CAN-specific suite already covers exhaustively; the 24-file,
204-test sweep above is the decisive check for this rung's actual diff.
Reported as a scope choice, not an oversight.

---

## 9. What this rung does NOT establish

1. **Identity-feedback remains exactly as unbuilt as `CAN_DECAY_IDENTITY_
   RESULTS.md`/`CAN_MT_SCOPED_RULES_RESULTS.md` left it** — confirmed
   independent of this rung's diff (§6); explicitly out of scope per the
   task.
2. **The fixed 1-quantum decay rate is not claimed to be the correct
   cadence for `external_field` at realistic magnitudes** (§4) — for the
   codebase's own typical `[-1,1]` field range, this design decays a field
   to zero in a single eligible tick, not gradually. This is reported as an
   honest, load-bearing finding, not resolved by adding a rate parameter.
   Any future caller depending on gradual native h-decay at realistic
   magnitudes will need to revisit this — named, not solved, here.
3. **No same-tick-race TEST exists** (§5) because no race exists to guard
   against — this is a structural claim (confirmed by grep of the rule/
   module source), not something proven exhaustively by fuzzing every
   possible caller of `external_field`. A FUTURE Python module that starts
   writing `external_field` (none does today) would reopen exactly the
   hazard `CAN_DECAY_IDENTITY_RESULTS.md` §3 found and fixed for the
   Hebbian ledger, and would need the same same-tick-skip guard added to
   this rule at that time.
4. **`maybe_decay_h`'s native branch inherits the same "one shared
   fixpoint" idempotency behaviour `maybe_decay_J` already documented**
   (§3) — a real, reported architectural difference from the continuous
   path's four independent calls, not newly introduced by this rung.
5. **Whether any of this reflects real human belief/field-strength
   dynamics** remains exactly as open as every prior rung in this arc left
   it — this document is about this substrate's own best-fitted mechanism.

---

## 10. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-external-field-decay
git log --oneline -1 main   # 08989e6, verified before branching

# This rung's own live demonstrations, with printed numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_external_field_decay.py -q -s

# Task-named regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_decay_identity.py tests/test_can_native_reimplementation.py \
  tests/test_can_mt_scoped_consumers.py tests/test_self_improvement_loop.py \
  tests/test_can_external_field_decay.py -q

# Broader CAN-adjacent regression sweep
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_bigville_can_native_migration.py \
  tests/test_identity_field.py tests/test_self_improvement_loop.py \
  tests/test_can_decay_identity.py tests/test_can_counterfactual.py \
  tests/test_insight_seeking.py tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_hebbian_materialization.py \
  tests/test_can_final_migration.py tests/test_can_mt_scoped_rules.py tests/test_can_mt_scoped_consumers.py \
  tests/test_can_external_field_decay.py -q

# Zero Rust touched
git status --short
git diff --stat main -- '*.rs'
```
