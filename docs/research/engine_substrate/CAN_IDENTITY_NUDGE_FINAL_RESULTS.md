# The final CAN issue: a bounded, event-triggered identity nudge for `nudge_identity_on_flipped` — RESULTS

Prereg: `CAN_IDENTITY_NUDGE_FINAL_PREREG.md`, same worktree/branch, base
`main @ 0784015` ("Merge can-identity-feedback: writes identity_field,
closes `maybe_update_identity`, finalises the CAN arc at 6/7, GO"), verified
via `git log --oneline -1 main` before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-identity-nudge-final`, branch
`can-identity-nudge-final`.

This is the true closing rung of the whole CAN arc. `CAN_IDENTITY_FEEDBACK_
RESULTS.md` §6.2 left `nudge_identity_on_flipped` genuinely unmigrated —
event-triggered, target-directed, recurrence-scaled, with no input surface
on the ambient per-tick rule. This rung asked whether a genuinely BOUNDED
version of that real contract (event-triggered, target-directed, but
capped at the already-proven-safe step size, never the continuous path's
unbounded `log(recurrence)` growth) could be built and proven safe.

**Verdict, up front: GO.** A new sibling native rule,
`can_native_identity_nudge_on_flip` (`seeds/can_decay_identity.json`
v1.3.0), closes it. Zero new Rust. **120 real draws × 18 real
`run_rules`-driving operations each (15 ticks + 3 real synthesized flip
events with post-event re-checks) = 2160 operations with BOTH native
identity rules (ambient + event-triggered) live alongside the discrete
update: 0 non-convergent draws, 0 non-convergent operations, for both
`3state` and `2state`.** `nudge_identity_on_flipped` now dispatches to the
native mechanism for native Mts, continuous branch byte-preserved and
unconditional as always. **`self_improvement_loop.py` is now 7 of 7
operations natively migrated — the whole CAN arc's own consumer-6 blocker
list, opened this morning at 0/7, is closed.**

---

## 1. What was confirmed by direct read before designing anything (not assumed)

- **`detect_insight`** (`domains/insight_detection.py:92-150`), read in
  full: a pure, substrate-agnostic Python comparison of two audit
  snapshots. It calls no continuous-only mechanism anywhere in its body —
  confirmed, not assumed. It is unmodified by this rung (confirmed by the
  diff, §7).
- **`nudge_identity_on_flipped`**'s real, pre-existing continuous call
  shape (`domains/self_improvement_loop.py:320-371`, `runners/dsl/src/
  py.rs:2547` `concept_nudge_identity`, `can_ops.rs::nudge_identity`):
  `identity_field ← identity_field + α·target_sigma` — an ADDITIVE push in
  the SIGN AND MAGNITUDE of `target_sigma`, scaled by
  `alpha_eff = base_alpha·(1+ln(recurrence))`, confirmed by direct read of
  the Rust primitive's own doc comment, not inferred from the Python
  wrapper alone.
- **`recurrence_count` is ALREADY graph-resident**, not a Python-only
  value: `domains/insight_naming.py::record_insight` (called BEFORE
  `nudge_identity_on_flipped` in `self_improvement_step`, confirmed by
  reading the call order in `domains/self_improvement_loop.py:~445-463`)
  writes/increments `recurrence_count` on a graph `InsightEvent` node
  (`Mt -has_insight-> InsightEvent`) and mirrors it onto the Python
  `insight` dict. This rung's design (§2) treats this as a PASSTHROUGH of
  an already-graph-resident value, not an invented signal.
- **Attr-read default, confirmed by reading the evaluator**
  (`runners/dsl/src/term.rs:4677-4694`): a missing `Attr` key evaluates to
  `Value::None`. Verified live (§4, `test_untouched_concept_never_fires_
  default_epochs_equal`): a Concept that never receives a pending event
  never fires, with no explicit pre-initialisation required for the gate
  itself to be inert (this rung's tests still initialise explicitly
  everywhere, for parity with every other test in this seed).
- **Zero pre-existing writers/readers of the new marker attrs**, confirmed
  by grep run before any code was written:
  ```
  $ grep -rn "pending_identity_nudge\|identity_nudge_applied_epoch\|insight_nudge_seq" seeds/*.json domains/*.py
  (no output)
  ```

---

## 2. The decision: a NEW graph rule, event-triggered by a graph-resident marker — not a Python-computed delta

Two shapes were weighed (`PREREG` §1), matching the task's own explicit
menu:

1. **A thin Python function computing the bounded delta itself.**
   **Rejected.** Deciding the nudge's SIGN (from `target_sigma`) and, since
   recurrence is meant to matter, the STEP SIZE (from `recurrence_count`)
   are both decisions over graph-resident state — `CLAUDE.md`'s
   architecture rule is explicit that this is a Rule, not Python, and every
   one of this arc's six prior closes reaches a native RULE via
   `scoped_settle`, none computes its own decision in Python and pokes
   `set_attr`. Doing so here would have been the first architectural
   regression in the arc.
2. **A new graph rule, mirroring `can_native_identity_field_feedback`'s own
   shape, triggered by a graph-resident EVENT MARKER instead of the
   ambient per-tick `can_tick` epoch.** **Adopted** — see §3.

Zero new Rust — confirmed against the Term list every prior rung in this
seed reused (`Attr`/`Eq`/`Not`/`And`/`Or`/`Gt`/`Lt`/`Plus`/`Minus`/
`IfThenElse`/`Lit`), all pre-existing:

```
$ git diff --stat main -- '*.rs'
(empty)
```

---

## 3. The bounded design, built exactly as registered

### 3.1 What Python writes — mechanical translation, not a decision

`domains/self_improvement_loop.py:320-406` (`nudge_identity_on_flipped`,
native branch). For each `{node, after}` in `insight["flipped_nodes"]`
belonging to `mt`:

```
pending_identity_nudge_target_sigma   ← after                 (passthrough)
pending_identity_nudge_recurrence     ← insight["recurrence_count"]  (passthrough,
                                                                       already
                                                                       graph-
                                                                       resident,
                                                                       §1)
pending_identity_nudge_epoch          ← mt.insight_nudge_seq + 1  (a plain
                                                                     monotonic
                                                                     sequence
                                                                     number,
                                                                     bookkeeping)
```

No comparison, no threshold, no branch on graph *content* in Python — only
"this event happened, tag it with the next number." Everything else (sign,
step size, whether to fire at all) is decided by the rule.

### 3.2 `can_native_identity_nudge_on_flip` (`seeds/can_decay_identity.json`
v1.3.0)

Match: `mt -has_concept-> c` (identical to every rule in this seed).

`where`: `And(Not(Eq(pending_identity_nudge_epoch, identity_nudge_applied_
epoch)), <the byte-identical allow_h_drift Or-policy-gate every rule in
this seed already uses>)`.

`effects`:

```
step := IfThenElse(Gt(pending_identity_nudge_recurrence, 1), 2.0, 1.0)

identity_field ←
  IfThenElse(Gt(pending_identity_nudge_target_sigma, 0), identity_field + step,
    IfThenElse(Lt(pending_identity_nudge_target_sigma, 0), identity_field - step,
      identity_field))    # target_sigma==0: no directional evidence

identity_nudge_applied_epoch ← pending_identity_nudge_epoch   # consumes the event
```

This is registered, precisely, as the answer to the task's own central
question: recurrence is preserved as a BOUNDED, BINARY two-tier step (1.0
first occurrence, 2.0 recurring) — never `log(recurrence)` growth — and
`target_sigma`'s DIRECTION (the event's own injected payload, not the
ambient rule's own AMBIENT log-odds render) drives the sign, so the event's
real signal survives the bound.

### 3.3 Boundedness demonstrated, not merely asserted

`tests/test_can_identity_nudge_final.py::test_rule_step_bounded_regardless_
of_how_large_recurrence_grows` and `test_real_flip_event_nudges_specific_
flipped_node_bounded_not_unbounded`:

```
bounded nudge trajectory across growing recurrence [1, 2, 5, 20, 100, 500]: [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
for contrast only (NOT applied): continuous alpha_eff at recurrence=500 would have been 0.3607
```

The per-event step at `recurrence=500` is IDENTICAL to the step at
`recurrence=2` (both +2.0) — asserted directly. The continuous path's own
`alpha_eff` at the same recurrence (0.3607, printed for contrast, never
applied) keeps growing without limit as recurrence grows further; this
rung's step does not.

### 3.4 Same-event race — checked, not assumed

`pending_identity_nudge_*`/`identity_nudge_applied_epoch` are the ONLY new
attr names this rung introduces; only `nudge_identity_on_flipped`'s native
branch writes the pending attrs, only this one new rule reads/writes any
of them (confirmed by grep, §1). No race is structurally possible, the
SAME class of check every prior rung in this arc ran for its own first
writer.

---

## 4. Live demonstrations — all four (plus rule-shape unit coverage), real numbers, on the real engine

`tests/test_can_identity_nudge_final.py`, run via
`PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/
test_can_identity_nudge_final.py -q -s`: **14 passed**.

### (a) A real flip event nudges the specific flipped node's `identity_field` toward `target_sigma`, bounded

`test_real_flip_event_nudges_specific_flipped_node_bounded_not_unbounded` —
a real `insight` dict (shaped like `detect_insight`'s own output) drives
the REAL `nudge_identity_on_flipped` entry point on a native
(`discrete_mode="3state"`) Mt, repeated six times with growing
`recurrence_count` (1, 2, 5, 20, 100, 500):

```
bounded nudge trajectory across growing recurrence [1, 2, 5, 20, 100, 500]: [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
```

First event (occurrence 1): +1.0. Every subsequent event (recurring):
exactly +2.0, regardless of how large `recurrence_count` grows — the
boundedness claim, demonstrated on the real orchestration path, not just
the isolated rule.

### (b) A non-flipped sibling node is untouched by the same event

`test_sibling_non_flipped_concept_untouched_by_the_same_event` — a second
Concept `b` on the same Mt, not named in `flipped_nodes`:

```
a.identity_field=2.0 (flipped, nudged), b's nudge-relevant attrs unchanged=True
```

(`recurrence_count=3` on this event, so `a`'s step is the recurring 2.0
tier, correctly.) `b`'s `identity_field` and this rule's own marker attrs
are confirmed byte-identical before/after — the event's scoping to the
SPECIFIC flipped node set is real. (The ambient sibling rules' own
UNRELATED bookkeeping ticks legitimately advance for every Concept on the
Mt regardless of which node flipped — that is pre-existing, already-proven
behaviour, out of scope for this comparison; the assertion is correctly
scoped to what this rule could plausibly have touched, and the diff
confirms it touched nothing on `b`.)

### (c) Convergence — the load-bearing result

See §5.

### (d) Two-Mt isolation with the event-triggered rule active

`test_two_mt_isolation_holds_with_event_triggered_nudge_active` — a second,
untouched sibling Mt receives 3 real flip events fired on the FIRST Mt:

```
mt_native a.identity_field=5.0 after 3 events
mt_other (untouched control) unchanged=True
```

(`5.0 = 1.0 + 2.0 + 2.0` across the three recurrence-1/2/3 events, matching
the design exactly.) Every attr on the sibling Mt's Concepts confirmed
byte-unchanged.

### Rule-shape unit coverage (isolated from the ambient sibling rule)

Ten additional tests directly exercise the new rule's own shape in
isolation (`discrete_mode="static"`, ambient sibling neutralised via an
already-consumed `identity_field_tick`, per the isolation discipline
`test_can_identity_feedback.py`'s own (a)/(b) tests established one level
further): positive/negative first-occurrence step, recurring 2-quantum
step, boundedness under `recurrence=500`, `target_sigma==0` no-op, exactly-
once-per-event firing (no refire on repeated `run_rules` without a new
pending epoch), frozen-Mt never fires, untouched-Concept default-epoch
inertness, and a direct confirmation that `recurrence_count` is read as a
plain passthrough of the `insight` dict's own field (not invented
bookkeeping).

---

## 5. Convergence validation — the load-bearing check, real numbers

### 5.1 The scenario, as registered

`_build_draw` (byte-identical to `test_can_identity_feedback.py`'s own,
N=8 complete graph, symmetric `causal_influence`, `external_field ~
Uniform(-1,1)`, coarse/fine weight vocab), both native seeds loaded (ambient
feedback rule + the new event-triggered rule + the discrete update all live
in the SAME `run_rules` fixpoint). Per draw, across `N_TICKS=15` real
ticks: every tick advances `can_tick` and calls `run_rules(3000)`; at ticks
3, 7, and 11, a REAL flip event is synthesized from LIVE `state` (2 of the
8 concepts, alternating which pair, `recurrence_count` alternated 1/2/3 so
both step tiers are exercised in every draw) and fired through the REAL
`nudge_identity_on_flipped` entry point, followed by an additional
`run_rules(3000)` re-check.

### 5.2 Sample size and result

**60 real draws** (30 coarse + 30 fine) for `discrete_mode="3state"` (the
deadzone case, this arc's own recurring headline condition) plus the same
60-draw sweep for `2state` — **120 real draws total, 18 real
`run_rules`-driving operations each (15 ticks + 3 post-event re-checks) =
2160 total operations**:

```
[3state] coarse   nonconv_draws=0/30 nonconv_calls=0/540
[3state] fine     nonconv_draws=0/30 nonconv_calls=0/540
[3state] TOTAL nonconv_draws=0/60 nonconv_calls=0/1080

[2state] coarse   nonconv_draws=0/30 nonconv_calls=0/540
[2state] fine     nonconv_draws=0/30 nonconv_calls=0/540
[2state] TOTAL nonconv_draws=0/60 nonconv_calls=0/1080
```

**Zero non-convergent draws, zero non-convergent operations, across 120
real draws with BOTH native identity rules live alongside real synthesized
flip events layered on real ticks.** This is the GO result registered
before any result was seen (`PREREG` §3.3). No fallback to the single-step
design (`PREREG` §5) was needed — the FULL registered design (target_sigma
direction + binary recurrence step) passed clean on the first sweep.

### 5.3 Why this is not merely "it didn't crash" — and what it does not prove

This is an EMPIRICAL result on 120 real draws, not a re-derivation of the
Lyapunov guarantee under two simultaneous feedback terms — the SAME
epistemic status every convergence-adjacent rung in this arc has reported
for its own sweep. This rung's own scenario is a strict superset of the
prior rung's (same draws, same ticks, PLUS 3 real events per draw with a
second `run_rules` re-check each) — the risk this rung was built to check
(a LARGER, event-triggered perturbation on top of an already-live ambient
perturbation) was genuinely exercised, not merely inherited from the prior
clean result. No non-convergent draw was found anywhere in this rung's
search; this does not prove none exists at other N, β, vocabulary
granularities, tick counts, event timings, or event magnitudes.

---

## 6. What was built, precisely

- `seeds/can_decay_identity.json` v1.2.0 → v1.3.0: one new rule
  (`can_native_identity_nudge_on_flip`), one new declarative
  `DimensionGenerator` (local_id 6, `identity_nudge_on_flip` — documentation
  only, matching local_id 1/2/4/5's own convention), one new `Concept`
  documentation node. Top-level `description` and the `can_native_identity_
  as_evidence_axis` concept's `why` field both appended (not rewritten) with
  the v1.3.0 status. **Every pre-existing rule/generator/concept body in
  this seed is confirmed byte-unchanged** (direct dict-equality check
  against `main`'s copy of the file, per-entry, run before any regression
  suite):
  ```
  can_native_evidence_decay UNCHANGED
  can_native_identity_evidence_sample UNCHANGED
  can_native_identity_evidence_decay UNCHANGED
  can_native_external_field_decay UNCHANGED
  can_native_identity_field_feedback UNCHANGED
  gen evidence_decay / identity_evidence / external_field_decay / identity_field_feedback UNCHANGED
  concept can_native_evidence_decay / can_native_external_field_decay / can_native_identity_field_feedback UNCHANGED
  ```
- `scripts/_build_can_identity_nudge_seed.py`: one-off authoring script
  (the `tools/*`-class precedent), idempotent, only ever appends/replaces
  entries whose NAME matches this rung's own new rule/concept/generator.
- `domains/self_improvement_loop.py`: `nudge_identity_on_flipped` gains the
  native branch; docstring rewritten to MIGRATED, explaining the design and
  citing this rung's own results doc. Continuous branch byte-unchanged
  (confirmed by diff, §7) and unconditional.
- `tests/test_can_identity_nudge_final.py`: 14 new tests, all passing, all
  printing real numbers (§4, §5).

---

## 7. What was explicitly NOT touched, confirmed by the diff

```
$ git status --short
 M domains/self_improvement_loop.py
 M seeds/can_decay_identity.json
?? docs/research/engine_substrate/CAN_IDENTITY_NUDGE_FINAL_PREREG.md
?? docs/research/engine_substrate/CAN_IDENTITY_NUDGE_FINAL_RESULTS.md
?? scripts/_build_can_identity_nudge_seed.py
?? tests/test_can_identity_nudge_final.py

$ git diff --stat main -- '*.rs'
(empty)
```

`can_native_identity_field_feedback` (the ambient rule) is untouched —
confirmed by the per-entry dict-equality check in §6, not just "no diff in
that region." `can_native_evidence_decay`, `can_native_identity_evidence_
decay`, `can_native_external_field_decay`, `can_native_hebbian_mint`/
`_reweight`, `can_native_update_3state`/`_2state`'s own formula, and
`detect_insight`'s own comparison logic are all confirmed byte-unchanged or
unmodified. `runners/dsl/src/*.rs` is untouched.

---

## 8. Regression

**New test file alone:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_identity_nudge_final.py -q -s
14 passed in 1.25s
```

**Task-named regression set (5 files + this rung's new file), 66/66 passed:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_identity_feedback.py tests/test_can_decay_identity.py \
  tests/test_can_native_reimplementation.py tests/test_can_mt_scoped_consumers.py \
  tests/test_self_improvement_loop.py tests/test_can_identity_nudge_final.py -q
66 passed in 3.00s
```

**Broader CAN-adjacent sweep (the same file list prior CAN rungs used, plus
this rung's new file), 227/227 passed:**
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
  tests/test_can_external_field_decay.py tests/test_can_identity_feedback.py \
  tests/test_can_identity_nudge_final.py -q
227 passed in 12.60s
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

**No stale "BLOCKED"/"blocked" language remains** for `nudge_identity_on_
flipped`'s CURRENT status (confirmed by grep — the one remaining hit,
`domains/self_improvement_loop.py:333`, is inside the docstring's own
HISTORICAL sentence explaining what the prior rung found, not a live status
marker).

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty; zero `.rs` files touched anywhere in this branch.

---

## 9. What this rung does NOT establish

1. **Boundedness of `identity_field` ACROSS MANY events is not a hard
   construction guarantee** — the PER-EVENT step is provably bounded
   (∈ {1.0, 2.0}, demonstrated §3.3/§4a), but across many repeated events
   `identity_field` can still accumulate without a hard ceiling, the SAME
   honest limitation `can_native_identity_field_feedback` itself carries
   (no `-β·identity_field` decay term for this attr exists; building one
   is out of scope for both rungs, and explicitly out of scope for this
   one per the task).
2. **The convergence result is empirical, on 120 real draws at N=8, β=2.0,
   complete graphs, 15 ticks + 3 events per draw** — not a re-derivation of
   the Lyapunov guarantee under two simultaneous feedback terms. Zero
   non-convergent draws were found; this does not prove none exist at
   other N, β, vocabulary granularities, tick counts, event timings, or
   event magnitudes (§5.3).
3. **The binary two-tier recurrence step (1.0/2.0) is one design point
   among several that would have satisfied "bounded."** A different fixed
   ceiling, or a three-tier scheme, was not swept — the binary choice was
   registered as the smallest non-trivial response to "does recurrence
   matter at all" before any data was seen (`PREREG` §2.3), and it passed
   clean, so no fallback or alternative tiering was tried or is reported as
   compared.
4. **`detect_insight` and `record_insight`/`insight_naming.py`'s own
   fingerprint-dedup mechanism are unmodified and NOT independently
   re-validated by this rung** — `record_insight`'s own graph-edge write
   (`Mt -has_insight-> InsightEvent`) requires seeds beyond the minimal
   two-seed CAN test substrate this rung's tests load (confirmed live: a
   direct probe found the edge silently fails to add under the
   admissibility grammar this substrate has loaded, and `record_insight`
   swallows that failure by design — `try/except: pass`). This rung's own
   tests correctly work around this by driving `nudge_identity_on_flipped`
   with a plain `insight` dict shaped exactly like `self_improvement_step`
   actually passes, rather than re-exercising `record_insight` itself,
   which is pre-existing, unmodified machinery outside this rung's scope.
5. **Whether any of this reflects real human belief/identity-formation
   dynamics** remains exactly as open as every prior rung in this arc left
   it — this document is about this SUBSTRATE's own best-fitted mechanism.

---

## 10. The whole CAN arc, final state

| Rung | What it built | Consumer-6 operations closed |
|---|---|---|
| `CAN_CONSUMER_MIGRATION_RESULTS.md` | Bigville schema fix + migration; full 7-consumer audit | 0/7 (audit only) |
| `CAN_MT_SCOPED_RULES_RESULTS.md` | `run_rules_scoped` | `relax`, `_audit_basin`/`_stash_post_state` (2) |
| `CAN_HEBBIAN_MATERIALIZATION_RESULTS.md` | Native Hebbian mint/reweight | `maybe_hebbian`, `maybe_decay_J` (2, cumulative 4) |
| `CAN_DECAY_IDENTITY_RESULTS.md` | Native evidence decay + identity reading half | 0 new closes (decay folded into existing) |
| `CAN_EXTERNAL_FIELD_DECAY_RESULTS.md` | Native `external_field` decay | `maybe_decay_h` (1, cumulative 5) |
| `CAN_IDENTITY_FEEDBACK_RESULTS.md` | Native identity FEEDBACK (ambient) | `maybe_update_identity` (1, cumulative 6) |
| **`CAN_IDENTITY_NUDGE_FINAL_RESULTS.md` (this rung)** | **Native identity nudge (event-triggered sibling rule), bounded, validated against a real 120-draw/2160-operation convergence sweep with BOTH native identity rules live alongside real flip events** | **`nudge_identity_on_flipped` (1, cumulative 7 — ALL of self_improvement_loop.py's seven operations)** |

**Final tally: 7 of 7 `self_improvement_loop.py` operations natively
migrated. The whole CAN arc's consumer-6 blocker list, which opened this
morning at 0/7 with three named blockers (decay, Hebbian materialization,
identity dynamics), is closed.** The prior rung's own honest 6/7 was not a
shortfall this rung had to route around — it was a genuinely open question
(can an event-triggered, target-directed, recurrence-scaled nudge be
bounded without losing its real signal) that this rung investigated,
designed against, and validated, rather than assumed either way going in.
Every rung in this arc that touched a decay or feedback rule used the SAME
shape (fixed-quantum step, epoch-gated, policy-gated via the identical
`allow_h_drift` `Or` subtree) — zero new Rust across the entire arc, zero
arbitrary rate constants introduced anywhere, and every place a
magnitude-or-recurrence-scaled alternative was seriously considered (the
prior rung for the ambient rule, this rung for the event-triggered one), it
was resolved by measurement against real data, not by assertion either way.

**7/7 is the honest number, earned by building the genuinely different
mechanism the prior rung correctly declined to fake, not by finding a way
to declare the prior rung's own honest 6/7 "good enough."**
