# Identity-feedback: writing `identity_field` from the evidence render — RESULTS

Prereg: `CAN_IDENTITY_FEEDBACK_PREREG.md`, same worktree/branch, base
`main @ d80682d` ("Merge can-external-field-decay: native external_field
decay, closes `maybe_decay_h`, GO"), verified via `git log --oneline -1
main` before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-identity-feedback`, branch
`can-identity-feedback`.

This is the closing rung of today's entire CAN arc. It builds the ONE
thing every prior rung named and explicitly declined to build: a native
rule that WRITES `identity_field` from `can_native_identity_evidence_
sample`'s own log-odds render, so `can_native_update_3state`/`_2state`'s
own local-field sum — which already reads `identity_field` six times —
actually feels it.

**Verdict, up front: GO.** `can_native_identity_field_feedback` (`seeds/
can_decay_identity.json` v1.2.0) is built, zero new Rust. The design is a
**fixed 1-quantum step toward the sign of the current identity log-odds
render** — the same shape every decay rule in this seed already uses — with
a magnitude/recurrence-scaled step investigated and **rejected on
stability grounds before it was built**, not after a failure. The single
most important check this rung ran — real discrete-async convergence with
the feedback loop live — came back **0/60 non-convergent draws for
`3state`, 0/60 for `2state`, 120/120 real draws total, zero exceptions**.
`maybe_update_identity` migrates cleanly, mirroring `maybe_decay_h`'s exact
pattern. `nudge_identity_on_flipped` genuinely does not — investigated, not
assumed, and reported honestly as staying on the continuous path. One
real, honest test regression was found and fixed: an existing
`test_can_external_field_decay.py` demonstration's assertion changed
because of a genuine, correctly-predicted compositional interaction
between the new rule and the sibling identity-evidence sampler — reported
as a finding, not smoothed over. **`self_improvement_loop.py` is now 6 of
7 operations natively migrated**, up from 5/7 this morning.

---

## 1. What already existed (confirmed by direct read before designing
anything new)

- **The reading half** (`CAN_DECAY_IDENTITY_RESULTS.md` §2, §4b):
  `can_native_identity_evidence_sample` accumulates a per-Concept
  `identity_evidence_confirm`/`identity_evidence_disconfirm` ledger from
  sampled σ; the graded reading is the non-materializing Term
  `Log(Div(Plus(confirm,1), Plus(disconfirm,1)))`, evaluated live, never
  written back by any rule before this one.
- **The consuming formula**: `can_native_update_3state`/`_2state`
  (`seeds/can_native_reimplementation.json:143-350` and the mirrored
  `_2state` block, `:350-680`) reads `identity_field` inside the SAME
  `Plus` subtree as `external_field` and the neighbour-coupling sum, six
  occurrences total (`:166,250,350,434,566,652`), confirmed by direct grep
  before writing anything.
- **The closest structural template**, `can_native_external_field_decay`
  (`CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` §1): epoch-gated own-tick attr,
  the byte-identical `allow_h_drift` policy `Or` subtree, symmetric
  `Max`/`Min` clamp-toward-zero. Transferred: the machinery (epoch gate,
  policy gate, `Max`/`Min` clamp idiom, own epoch attr). NOT transferred
  literally: the target — decay-toward-zero is the wrong shape for a rule
  that must move TOWARD the current evidence sign, not unconditionally
  toward zero.

---

## 2. The design decision, registered before any code was written, built
exactly as registered

### 2.1 Fixed 1-quantum step toward the render's SIGN

```
logodds = Log(Div(Plus(confirm,1), Plus(disconfirm,1)))
identity_field ←
  IfThenElse(Gt(logodds, 0), identity_field + 1,
    IfThenElse(Lt(logodds, 0), identity_field - 1,
      # logodds == 0 (neutral/flip-flop): decay toward zero, the SAME
      # Max/Min clamp can_native_external_field_decay already uses
      clamp_toward_zero(identity_field)))
```

Built exactly as registered in `scripts/_build_can_identity_feedback_seed.py`
and confirmed live (§5 below). No new scalar rate anywhere — the quantum is
the SAME `1` every other rule in this seed steps by.

### 2.2/2.3 Rejected: magnitude- or recurrence-scaled step

**Investigated, not assumed, and rejected BEFORE the rule was built**
(`CAN_IDENTITY_FEEDBACK_PREREG.md` §2.2/§2.3): using the render's own
`ln`-scaled magnitude, or `nudge_identity_on_flipped`'s own
`base·(1+ln(recurrence))`, as the STEP size (not merely its sign) would
make the per-tick perturbation to `identity_field` — a term that directly
enters `can_native_update_3state`'s own threshold comparison — GROW every
tick sustained evidence continues. A per-tick bias perturbation that grows
in size is precisely the shape the discrete-async update's own Lyapunov/
energy convergence argument (`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2:
"every committed flip strictly decreases a bounded energy function... a
period-2 cycle is mathematically impossible BY THE SHAPE OF THE UPDATE")
was never built to withstand — a FIXED, bounded-per-tick, worst-case
perturbation is a strictly safer choice, and this is what §3's convergence
sweep exists to check, not merely assert.

### 2.4 Boundedness — reported honestly, not solved by inventing a cap

Under literally sustained single-direction evidence forever, this design's
`identity_field` grows without a hard ceiling — there is no
`-β·identity_field` decay term (the continuous formula's own stabiliser),
because building one was out of this rung's scope (touching the
already-shipped decay rules is explicitly forbidden by the task, and
`identity_field` itself has no existing decay rule to extend). **This
mirrors `evidence_confirm`'s own existing design exactly** — it too grows
unboundedly under sustained reinforcement, with no cap, confirmed by
direct read of `can_native_evidence_decay`'s own body. No new cap constant
was invented, per the standing `CLAUDE.md` "SHAPES, NOT NUMBERS" rule.
Within any finite observed run — every live demonstration below, and every
real system in practice — the magnitude is of course bounded; this is
reported as the honest, weaker claim this design actually supports, not
overstated as a hard ceiling.

### 2.5 Epoch gate, no same-tick-race guard needed — confirmed by grep,
not assumed

Own epoch attr `identity_field_tick`. Direct grep, run BEFORE the rule was
written (`CAN_IDENTITY_FEEDBACK_PREREG.md` §3, re-confirmed live in this
rung):

```
$ grep -n '"identity_field"' seeds/can_native_reimplementation.json seeds/can_decay_identity.json
seeds/can_native_reimplementation.json: 6 hits, all inside the READ-side local-field sum
seeds/can_decay_identity.json (pre-branch): 0 hits
```

`identity_field` had ZERO writers anywhere before this rung — this rule is
the FIRST writer, structurally identical to `external_field`'s own
situation (`CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` §2). The new rule only
READS `identity_evidence_confirm`/`_disconfirm` (never writes them) and
only WRITES `identity_field`/`identity_field_tick` (which no other rule
reads or writes) — no same-tick race is structurally possible.

### 2.6 Policy gate

The byte-identical `Or(update_policy==adaptive, And(update_policy==hybrid,
Not(allow_h_drift==0)))` subtree every rule in this seed uses.

---

## 3. Convergence validation — the single most important check in this
rung, real numbers

### 3.1 The scenario

Reused `test_can_native_reimplementation.py`'s own `_build_draw` (N=8
complete graph, symmetric `causal_influence` edges, `external_field ~
Uniform(-1,1)`, `causal_influence.weight ~ Uniform(-1,1)` rounded to
coarse/fine vocabulary) byte-identically, loading BOTH
`seeds/can_native_reimplementation.json` AND `seeds/can_decay_identity.json`
so the identity-feedback rule is live in the SAME `run_rules` fixpoint as
the discrete update. Per the PREREG's own registered addition (§4.2): each
draw is driven across **15 real ticks** (not a single tick), calling
`run_rules(3000)` at every tick, so the identity-feedback rule gets
repeated real opportunities to perturb `identity_field` WHILE the discrete
update is also live — the scenario that actually exercises the named risk.

### 3.2 Sample size and result

**60 real draws** (30 coarse + 30 fine) for `discrete_mode="3state"` (the
deadzone case, the higher theoretical risk named in
`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §5.1) as the headline number, plus
the same 60-draw sweep for `discrete_mode="2state"` as a secondary check
(`identity_field` is read by both rules) — **120 real draws total**,
mirroring `CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`'s own "0/60
non-convergent draws" precedent for "proven, not assumed" convergence.

```
[3state] coarse   nonconv_draws=0/30 nonconv_ticks=0/450
[3state] fine     nonconv_draws=0/30 nonconv_ticks=0/450
[3state] TOTAL nonconv_draws=0/60 nonconv_ticks=0/900

[2state] coarse   nonconv_draws=0/30 nonconv_ticks=0/450
[2state] fine     nonconv_draws=0/30 nonconv_ticks=0/450
[2state] TOTAL nonconv_draws=0/60 nonconv_ticks=0/900
```

**Zero non-convergent draws, zero non-convergent ticks, across 120 real
draws × 15 ticks each = 1800 individual `run_rules(3000)` calls with the
identity-feedback loop live.** This is the GO result the PREREG (§4.3)
registered as the bar before any result was seen. `tests/
test_can_identity_feedback.py::test_discrete_async_convergence_holds_with_
identity_feedback_active` is now a permanent, re-runnable regression check
(not a one-off script) — `pytest.mark.parametrize("discrete_mode",
["3state", "2state"])`.

### 3.3 Why this is not merely "it didn't crash" — and what it does not
prove

This is an EMPIRICAL result on 120 real draws, not a re-derivation of the
Lyapunov guarantee under the new feedback term — exactly the same epistemic
status `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §2 gave the undisturbed
3-state rule's own guarantee ("empirically clean, exactly as the PoC
found, reported as an empirical fact, not a proof"). The fixed-quantum
step design (§2.2's rejection of magnitude scaling) was chosen SPECIFICALLY
because it is the shape least likely to break the argument informally —
this sweep is what checks that choice against real data, not a
post-hoc rationalisation after a clean result. No non-convergent draw was
found ANYWHERE in this rung's search (120 draws × 15 ticks); this does not
prove no such draw exists at other N, β, vocabulary granularities, or tick
counts — the same honest bound every prior convergence-adjacent rung in
this arc has reported.

---

## 4. Live demonstrations — all four, real numbers, on the real engine

`tests/test_can_identity_feedback.py`, run via
`PYTHONPATH=".:runners/dsl/python" python3 -m pytest
tests/test_can_identity_feedback.py -q -s`:

### (a) Consistent σ → strongly-committed, growing, bounded `identity_field`

`test_identity_field_grows_and_commits_under_consistent_sigma` —
`discrete_mode="static"` (isolates the feedback rule from the discrete
update, the SAME isolation the reading-half's own consistent/flipper test
uses), `state=+1.0` held for 10 ticks:

```
identity_field trajectory (consistent sigma=+1, 10 ticks): [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
```

Same sign every step, strictly monotonic, never negative, bounded within
this finite 10-tick run at exactly `10.0` (per §2.4's honest framing — no
hard cap by construction, bounded because the run itself is finite). The
mirror-image negative-σ case
(`test_identity_field_grows_negative_under_consistent_negative_sigma`)
confirms the symmetric direction: `[-1.0, -2.0, -3.0, -4.0, -5.0, -6.0]`.

### (b) Flip-flopping σ → `identity_field` decays to zero

`test_identity_field_decays_toward_zero_under_flip_flop_sigma` — same
isolation, σ alternating `+1.0`/`-1.0` every tick, 10 ticks (the same
even/odd split the reading-half's own flipper test uses, ending on a tick
where `confirm==disconfirm`):

```
identity_field trajectory (flip-flop sigma, 10 ticks): [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
final ledger: confirm=5 disconfirm=5
```

Ends EXACTLY at `0.0` — mirroring `can_ops.rs:774`'s own docstring,
"flipping σ averages to near zero → identity decays toward zero," via the
neutral-branch clamp. `max(trajectory) <= 1.0` — a flip-flopping Concept
never builds meaningful commitment (asserted and confirmed).

An independent cross-check
(`test_identity_field_feedback_matches_independent_logodds_sign_readback`)
re-evaluates the SAME log-odds Term via `Substrate.evaluate` (not the
rule's own internal computation) against a mostly-positive-with-one-dissent
σ trajectory: `independent logodds readback=1.2528 identity_field=7.0` —
the rule's own sign decision agrees with an independently-evaluated render.

Policy respect confirmed
(`test_identity_field_feedback_frozen_never_fires`): frozen, 8 ticks of
σ=+1 → `identity_field=0.0 identity_field_tick=-1` — the rule never fires
at all under `frozen`, matching every sibling rule's own precedent.

### (c) Convergence — §3 above, the load-bearing result.

### (d) Two-Mt isolation with identity-feedback active

`test_two_mt_isolation_holds_with_identity_feedback_active` — reuses
`test_can_mt_scoped_consumers.py`'s own `_isolated_pair` pattern, drives
`maybe_update_identity` (the real orchestration entry point, not a direct
rule call) across 5 ticks on `mt_native`, with an untouched sibling
`mt_other` in the same graph:

```
mt_native after 5 ticks: a.identity_field=5.0 b.identity_field=5.0
mt_other (untouched control) can_tick=0
```

Every attr checked (`state`, `identity_field`, `external_field`,
`identity_evidence_confirm`, `identity_evidence_disconfirm`) on the sibling
Mt's Concepts is confirmed byte-unchanged, and `mt_other`'s own `can_tick`
never advances — the same two-Mt isolation guarantee every native rung
this arc built has confirmed, now re-proven with identity-feedback active.

---

## 5. A real, honest test regression — found, explained, fixed (not
smoothed over)

Running the task-named regression set surfaced one real failure:
`test_can_external_field_decay.py::test_external_field_decay_composes_
with_local_field_formula_and_flips_state` — previously asserted
`state_trajectory == [1, 1, 0, 0, 0]` (external_field's decay eventually
flips state away from +1). With `can_decay_identity.json` v1.2.0 loaded,
this Concept's `state=1` ALSO gets sampled every tick by the sibling
`can_native_identity_evidence_sample` rule (it always did — that rule is
unconditional on any nonzero `state` under an adaptive Mt — but had no
observable effect before v1.2.0, since nothing read `identity_field`
back). `identity_field` now grows `+1`/tick from the SAME sustained σ=+1,
exactly offsetting `external_field`'s `-1`/tick floored decay:

```
field trajectory: [2.5, 1.5, 0.5, 0, 0]
identity trajectory: [1.0, 2.0, 3.0, 4.0, 5.0]
state trajectory: [1, 1, 1, 1, 1]   <- was [1, 1, 0, 0, 0] before this rung
```

**This is a real, structural, CORRECT consequence of identity-feedback,
not a bug** — a Concept's own sustained commitment increasingly
self-sustains through the identity axis even as the ORIGINAL external
evidence that first caused it fades, exactly matching `can_ops.rs`'s own
documented continuous intent ("identity emerges from sustained σ... with
reinforcement, it strengthens"). The test's assertion was updated to the
new, correct trajectory, with the mechanism explained in the docstring
(not a silent edit). A companion test
(`test_external_field_decay_still_flips_state_when_identity_does_not_
offset_it`) confirms the ORIGINAL claim — decay still flips state — still
holds when identity does NOT offset it (a Concept pre-seeded with heavy
disconfirming identity evidence, pulling `identity_field` negative instead
of positive):

```
field trajectory (disconfirm-pinned identity): [2.5, 1.5, 0.5, 0, 0]
identity trajectory: [-1.0, -2.0, -3.0, -4.0, -5.0]
state trajectory: [1, 0, -1, -1, -1]
```

No other test in the named regression set required any change — confirmed
by running the full set (§7).

---

## 6. `maybe_update_identity` migrates; `nudge_identity_on_flipped` does
NOT — investigated, not assumed, reported honestly either way

### 6.1 `maybe_update_identity` — MIGRATED

`domains/self_improvement_loop.py:282-311`, mirroring `maybe_decay_h`'s
exact pattern:

```python
def maybe_update_identity(substrate, mt, alpha=0.01, beta=0.001) -> int:
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    if not mt_allows(substrate, mt, "allow_h_drift"):
        return 0
    return substrate.mt_update_identity_dynamics(mt, alpha, beta)
```

Native branch: `scoped_settle(substrate, mt)`, the SAME isolated
`run_rules_scoped` mechanism every other migrated operation in this module
uses — `alpha`/`beta` have no native analog (fixed 1-quantum step) and are
silently unused, the same precedent `maybe_decay_h`/`maybe_decay_J` already
set. Continuous branch byte-unchanged. Demonstrated live in §4(d).

### 6.2 `nudge_identity_on_flipped` — investigated, genuinely does NOT
migrate cleanly, stays on the continuous path

Registered as genuinely open in the PREREG (§6), not pre-committed either
way. The investigation: `nudge_identity_on_flipped`
(`domains/self_improvement_loop.py:308-...`) is EVENT-triggered — it fires
once, immediately, on insight consolidation, targeting SPECIFIC flipped
node ids with an insight-supplied `target_sigma` (the new σ the insight
committed to, not necessarily what `state` already reads) and a
`recurrence_count`-scaled `alpha_eff`. `can_native_identity_field_feedback`
is a per-tick, epoch-gated, whole-Mt sample step driven entirely by the
AMBIENT observed σ each Concept already has — it has no input surface for
a specific target node set, an injected target σ, or a recurrence count.

**The magnitude/recurrence-scaled step §2.2/§2.3 rejected for
`maybe_update_identity` applies here even more directly** — this
function's whole point is an IMMEDIATE, LARGER nudge on insight
consolidation, exactly the unbounded-single-step shape the convergence
sweep (§3) was built to guard against for the ambient per-tick rule. Two
options were considered and both rejected:

1. Route the native branch through `scoped_settle` anyway, letting the
   ambient per-tick rule fire if epoch-eligible. **Rejected**: this would
   silently discard the event's own `target_sigma`/`recurrence_count`
   signal and do whatever the ambient tick-based rule would have done
   regardless of whether an insight consolidated — not a real migration of
   this function's contract, just a same-named no-op wearing the
   function's name.
2. Build a SEPARATE event-triggered native rule accepting an injected
   target/recurrence. **Out of scope**: this would need a new rule design
   (a genuinely different mechanism from the per-tick sampler, likely
   needing its own magnitude-scaled step — exactly the stability risk
   §2.2/§2.3 registered as rejected) and was not attempted here, per the
   task's own explicit permission to leave this one function honestly
   blocked rather than force a shaky design through.

`nudge_identity_on_flipped`'s docstring
(`domains/self_improvement_loop.py:308-...`) is updated to state this
precisely — not left as stale "STAYS BLOCKED" boilerplate copied from
`maybe_update_identity`'s own now-superseded text, but the SPECIFIC,
different reason this function stays blocked. **This is the honest partial
result the task's own charter explicitly permitted**: "a clean, honest
partial... is still a complete, valuable, arc-finalizing outcome."

---

## 7. What was built, precisely

- `seeds/can_decay_identity.json` v1.1.0 → v1.2.0: one new rule
  (`can_native_identity_field_feedback`), one new declarative
  `DimensionGenerator` (local_id 5, `identity_field_feedback` —
  documentation only, matching local_id 1/2/4's own "declared, never
  literally invoked" convention), one new `Concept` documentation node
  (`can_native_identity_field_feedback`). Top-level `description` and the
  `can_native_identity_as_evidence_axis` concept's `why` field both updated
  to the resolved status (no stale "un-sized follow-on"/"NOT resolved"
  language remains — confirmed by grep, §9). Zero new
  productions/edges.
- `scripts/_build_can_identity_feedback_seed.py`: one-off authoring script
  (the `tools/*`-class precedent), idempotent.
- `domains/self_improvement_loop.py`: `maybe_update_identity` gains the
  native branch (§6.1); docstring rewritten to MIGRATED. `nudge_identity_
  on_flipped`'s docstring rewritten to the specific, honest reason it stays
  blocked (§6.2) — its behaviour is byte-unchanged (still unconditionally
  continuous).
- `tests/test_can_identity_feedback.py`: 8 new tests, all passing, all
  printing real numbers (§3, §4).
- `tests/test_can_external_field_decay.py`: one existing test's assertion
  + docstring updated honestly (§5); one new companion test added.

Zero new Rust — confirmed:

```
$ git diff --stat main -- '*.rs'
(empty)
```

`Log`/`Div`/`Plus`/`Minus`/`Max`/`Min`/`IfThenElse`/`Gt`/`Lt`/`Eq`/`Not`/
`And`/`Or`/`Attr`/`Lit` all pre-existed and are reused exactly as prior
rungs already use them.

---

## 8. What was explicitly NOT touched, confirmed by the diff

```
$ git status --short
 M domains/self_improvement_loop.py
 M seeds/can_decay_identity.json
 M tests/test_can_external_field_decay.py
?? docs/research/engine_substrate/CAN_IDENTITY_FEEDBACK_PREREG.md
?? docs/research/engine_substrate/CAN_IDENTITY_FEEDBACK_RESULTS.md
?? scripts/_build_can_identity_feedback_seed.py
?? tests/test_can_identity_feedback.py
```

`can_native_update_3state`/`_2state`'s own threshold/local-field FORMULA is
byte-unchanged — only ADDED a rule that WRITES `identity_field`, which the
existing formula already READ. `can_native_evidence_decay`,
`can_native_identity_evidence_decay`, `can_native_external_field_decay`
(the rule bodies) and the Hebbian mechanism are all byte-unchanged.
`runners/dsl/src/*.rs` is untouched (§7).

---

## 9. Regression

**New test file alone:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_identity_feedback.py -q -s
8 passed in 0.84s
```

**Task-named regression set (5 files + this rung's new file), 59/59
passed:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_decay_identity.py tests/test_can_native_reimplementation.py \
  tests/test_can_mt_scoped_consumers.py tests/test_self_improvement_loop.py \
  tests/test_can_external_field_decay.py tests/test_can_identity_feedback.py -q
59 passed in 2.05s
```
Per-file: `test_can_decay_identity.py` 8, `test_can_native_reimplementation.py`
11, `test_can_mt_scoped_consumers.py` 6, `test_self_improvement_loop.py` 19,
`test_can_external_field_decay.py` 7 (was 6; +1 companion, §5), `test_can_
identity_feedback.py` 8 (new).

**Broader CAN-adjacent sweep (the same file list every prior CAN rung
today used, plus this rung's new file), 213/213 passed:**
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
  tests/test_can_external_field_decay.py tests/test_can_identity_feedback.py -q
213 passed in 11.41s
```

**Module import sanity**:
```python
from domains.self_improvement_loop import maybe_update_identity, nudge_identity_on_flipped, _is_native
```
imports and runs cleanly.

**Full boot regression** (`load_all_seeds` on a fresh `WorldAdapter`):
identical 8 pre-existing failures to the documented baseline
(`acoustic_cue_vocab`, `character_tom`, `reading_constructions`,
`conceptual_categories`, `cue_investigator`, `named_compound_heads`,
`reading_skeleton`, `vision_change`, all `ValueError: seed node missing
local_id`), 0 `rules_skipped` — `can_decay_identity.json` remains correctly
excluded from the sweep (`self_load_only: true`, unchanged).

**No stale "BLOCKED"/"blocked" language remains for `maybe_update_identity`**
(confirmed by grep — `grep -n "BLOCKED\|blocked" domains/
self_improvement_loop.py` now returns exactly one hit, inside `nudge_
identity_on_flipped`'s own honestly-updated, SPECIFIC docstring, §6.2).

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty; zero `.rs` files touched anywhere in this branch.

---

## 10. What this rung does NOT establish

1. **Boundedness of `identity_field` is not a hard construction guarantee**
   (§2.4) — under literally sustained single-direction evidence forever,
   it grows without a ceiling, mirroring `evidence_confirm`'s own existing
   design. This was a deliberate, registered choice (no arbitrary cap
   invented), not an oversight, but it is a real, honest difference from
   the continuous leaky integrator's own asymptotic steady state.
2. **The convergence result is empirical, on 120 real draws at N=8, β=2.0,
   complete graphs, 15 ticks per draw** — not a re-derivation of the
   Lyapunov guarantee under the new feedback term. Zero non-convergent
   draws were found; this does not prove none exist at other N, β,
   vocabulary granularities, or tick counts (§3.3).
3. **`nudge_identity_on_flipped` remains genuinely unmigrated** (§6.2) — a
   real, separate design gap (an event-triggered, target/recurrence-scaled
   nudge has no clean native analog under the stability constraint this
   rung established), not a deferred convenience.
4. **The Hebbian materialization sibling gap is untouched** — this rung
   says nothing about it, positively or negatively, confirmed by the diff
   (§8).
5. **Whether any of this reflects real human belief/identity-formation
   dynamics** remains exactly as open as every prior rung in this arc left
   it — this document is about this SUBSTRATE's own best-fitted mechanism.

---

## 11. The whole CAN arc, final state

Starting point (`CAN_CONSUMER_MIGRATION_RESULTS.md`, this morning): **1 of
7 real consumers migrated** (Bigville only), with `domains/
self_improvement_loop.py` (consumer 6) itself carrying **3 independent
blockers across 7 internal operations** — decay (no native analog
anywhere), Hebbian materialization (the render was intentionally
non-materializing), and identity dynamics (no native design existed at
all).

| Rung | What it built | Consumer-6 operations closed |
|---|---|---|
| `CAN_CONSUMER_MIGRATION_RESULTS.md` | Bigville schema fix + migration; full 7-consumer audit | 0/7 (audit only) |
| `CAN_MT_SCOPED_RULES_RESULTS.md` | `run_rules_scoped` — isolates per-Mt fixpoints, removing the orchestration hazard blocking `relax`/basin-audit composition | `relax`, `_audit_basin`/`_stash_post_state` (2) |
| `CAN_HEBBIAN_MATERIALIZATION_RESULTS.md` (sibling, same day) | Native Hebbian mint/reweight with graded evidence counters | `maybe_hebbian`, `maybe_decay_J` (re-targeted quantity) (2, cumulative 4) |
| `CAN_DECAY_IDENTITY_RESULTS.md` | Native evidence decay (`can_native_evidence_decay`); identity dynamics READING half (`can_native_identity_evidence_sample`/`_decay`) — feedback half explicitly named unresolved | 0 new closes (decay folded into existing; identity reading has no orchestration entry point of its own) |
| `CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` | Native `external_field` decay (`can_native_external_field_decay`), the FIRST writer of that attr | `maybe_decay_h` (1, cumulative 5) |
| **`CAN_IDENTITY_FEEDBACK_RESULTS.md` (this rung)** | **Native identity FEEDBACK (`can_native_identity_field_feedback`), the FIRST writer of `identity_field`; validated against a real 120-draw convergence sweep** | **`maybe_update_identity` (1, cumulative 6). `nudge_identity_on_flipped` investigated and honestly reported as NOT migrating — event-shape mismatch, not a deferred convenience.** |

**Final tally: 6 of `self_improvement_loop.py`'s 7 operations natively
migrated. The 7th (`nudge_identity_on_flipped`) is not blocked by a gap
this arc failed to close — it is blocked by a genuine, investigated,
reported mismatch between an event-triggered nudge and a per-tick sampled
field, discovered specifically BECAUSE this rung finally built the
feedback mechanism the other six operations needed.** Of the seven
consumers named this morning, 2 are now fully migrated (Bigville,
`self_improvement_loop.py` at 6/7) and the module's own remaining gap is
precisely named rather than approximated. Every rung in this arc that
touched a decay or feedback rule used the SAME shape (fixed-quantum step,
epoch-gated, policy-gated via the identical `allow_h_drift` `Or` subtree)
— zero new Rust across the entire arc, zero arbitrary rate constants
introduced anywhere, and the one place a magnitude-scaled alternative was
seriously considered (this rung, §2.2/§2.3), it was rejected on a
stability argument checked directly against real data, not asserted.

The arc's own repeated, hard-won discipline held to the end: this rung
could have declared a round "7/7" by wiring `nudge_identity_on_flipped`
through `scoped_settle` as a silent no-op-in-practice — §6.2 explains
precisely why that was rejected instead. **6/7, with the 7th operation's
gap named exactly, is the honest number.**

---

## 12. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-identity-feedback
git log --oneline -1 main   # d80682d, verified before branching

# Rebuild the seed from the authoring script (idempotent)
python3 scripts/_build_can_identity_feedback_seed.py

# This rung's own live demonstrations, with printed numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_identity_feedback.py -q -s

# Task-named regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_decay_identity.py tests/test_can_native_reimplementation.py \
  tests/test_can_mt_scoped_consumers.py tests/test_self_improvement_loop.py \
  tests/test_can_external_field_decay.py tests/test_can_identity_feedback.py -q

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
  tests/test_can_external_field_decay.py tests/test_can_identity_feedback.py -q

# Full boot regression (8 pre-existing failures only, unrelated to this rung)
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
a = WorldAdapter(seeds=())
rep = load_all_seeds(a)
print('failed:', len(rep['failed']), 'rules_skipped:', len(rep['rules_skipped']))
for f in rep['failed']: print(' ', f)
"

# Zero Rust touched
git status --short
git diff --stat main -- '*.rs'
```
