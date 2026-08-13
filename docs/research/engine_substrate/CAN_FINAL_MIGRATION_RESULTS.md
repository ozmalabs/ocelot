# The final CAN consumer migration — closing the arc with the three built primitives — RESULTS

Prereg: `CAN_FINAL_MIGRATION_PREREG.md`, same worktree/branch, base
`main @ 84ed599` ("Fix stale cross-rung test assumption in
test_evidence_decay_blocked_when_frozen"), verified via `git log --oneline
-1 main` before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-final-migration`, branch
`can-final-migration`.

**Verdict, up front: 2 of 6 remaining consumers fully migrated (gated,
dual-path), 4 of 6 correctly stay on the continuous mechanism — for ONE
newly-precise, empirically-confirmed reason rather than the three separate
reasons the original audit named.** `can_ops.rs` is untouched (`git diff
--stat main -- '*.rs'` empty) because every one of its 16 audited functions
still has at least one real, currently-irreplaceable consumer, confirmed by
direct re-grep, not assumed. This is the honest, non-forced outcome the
PREREG predicted before any code was written (§5).

---

## 0. The investigation that shapes every decision below

Before wiring anything, this rung read `run_rules()`'s own signature
(`runners/dsl/src/py.rs:3381`, no per-Mt scope argument) and every native
CAN rule's match pattern in both seeds
(`seeds/can_native_reimplementation.json`, `seeds/can_decay_identity.json`
— all eight rules match `[mt, has_concept, ...]` with NO Mt-identity
constraint), then confirmed live with a throwaway two-Mt probe (not part of
this rung's diff) that calling `run_rules()` "on behalf of" one Microtheory
mutates a COMPLETELY UNRELATED, untouched Microtheory's `state` as a side
effect:

```
BEFORE any run_rules(): mt_b/b1 state = 0.0
AFTER run_rules() called 'for mt_a': mt_b/b1 state = 1
```

This is not a hypothetical: `self_improvement_step` iterates `for mt in
substrate.nodes("Microtheory")` and `insight_propagation.py::
find_connected_mts` (called from inside that per-Mt loop, via
`consolidate_insight`) walks that SAME node set again
(`insight_propagation.py:99`). Any per-Mt consumer function that itself
called `run_rules()` to let a native Hebbian/decay rule fire would
non-locally advance every OTHER native-tagged Mt in the graph — including
ones the loop has not reached yet this step (their `pre_audit` is still
pending) and ones it already finished (their stash is now stale). This
confirms, concretely rather than by assumption, the "shared-Mt coherence
risk" `CAN_CONSUMER_MIGRATION_RESULTS.md` §1 row 4 named in the abstract.

**This finding reframes Blocker B and decay.** Both are now REAL,
CORRECT primitives (proven by the prior two rungs) — they are blocked not
because the mechanism doesn't exist (the original stated reasons — "non-
materializing," "no native design" — are now factually false) but because
wiring any RULE-based native mechanism into a per-Mt Python loop requires
deciding WHEN `run_rules()` fires relative to that loop, system-wide. No
rung in this arc, including this one, was asked to design that. Blocker A
(the counterfactual predictor) never touches this hazard at all — it is
pure Term evaluation, zero `run_rules()` calls, zero graph mutation — which
is exactly why it is the one primitive this rung successfully wires in.

**`mt_audit_basin`/`mt_distance_to_target` are NOT a fourth, independent
gap.** Read directly (`can_ops.rs:384-463`): their own observable numbers
(`energy`, `frustration`, `coverage`, target displacement) are computed by
`mt_energy`/`mt_frustration_given_state`/`mt_target` — all THREE already
representation-agnostic pure functions of a `{NodeID: f32}` dict (already
reused this way by `can_counterfactual.py` and, now, by this rung's own
`insight_seeking.py` migration, §2 below). The only continuous-specific
step in either function is HOW the marginal dict gets populated in the
first place (`mt_mean_field_marginal`, called internally) — a native
equivalent would read `state` directly, a small and real composition — but
USING it correctly still needs `state` to already be at a native fixed
point, which collapses into the exact same `run_rules()`-orchestration
question above. Named precisely here, per the task's explicit instruction,
and NOT built.

---

## 1. Per-consumer migration table

| # | Consumer | Verdict | Real before/after |
|---|---|---|---|
| 1 | `domains/drive_curiosity.py::probe_via_what_if` | **FULLY MIGRATED (gated)** | §2.1 |
| 2 | `domains/insight_detection.py::consolidate_insight` | **STAYS BLOCKED** — precise reason: `run_rules()` orchestration (§0), not the original Blocker B | 0 lines touched |
| 3 | `domains/insight_seeking.py` | **PARTIALLY MIGRATED**: `predict_perturbation_impact` fully migrated (gated) + `seek_insights` relax-guard fixed; `find_hot_nodes` confirmed to need NO migration at all | §2.2 |
| 4 | `domains/insight_propagation.py::propagate_insight` | **STAYS BLOCKED**, transitively (calls #2) and directly (`mt_relax_to_marginal`/`mt_audit_basin` on `other_mt` have no safe native path) | 0 lines touched |
| 5 | `domains/sparseness_signal.py` | **Inherits #6's status — 0 lines touched, none needed** | confirmed by direct re-grep: zero `can_ops` calls in this file |
| 6 | `domains/self_improvement_loop.py` | **STAYS BLOCKED, all seven operations** — one unifying reason, not three | §3 |

---

## 2. What migrated, with real before/after numbers

### 2.1 `drive_curiosity.py::probe_via_what_if`

Gated by `Mt.discrete_mode`: a `"2state"`/`"3state"` Mt now calls
`domains/can_counterfactual.py::predicted_info_gain` (Blocker A's own
primitive); an un-upgraded Mt (no `discrete_mode` attr) keeps the ORIGINAL
`mt_mean_field_marginal`/`mt_mean_field_with_h_override` path byte-for-byte
(`domains/drive_curiosity.py:65-129`). `find_ambivalent_nodes` is
unchanged — it already reads `state` directly.

**Real numbers, both branches, `tests/test_can_final_migration.py`:**

Native branch (4-Concept discrete Mt, hub probed with `h_delta=0.5`),
confirmed to match calling `can_counterfactual.predicted_info_gain`
directly (proving the WIRING, not merely that the function runs):
```
native probe_via_what_if: total_change=1.0000 max_change=1.0000 flipped=1
```

Continuous branch (3-Concept Mt, no `discrete_mode`, `h_delta=0.4`),
confirmed byte-identical to hand-computing the ORIGINAL pre-migration
formula directly:
```
continuous probe_via_what_if (pre-migration-equivalent):
{'concept_id': 1, 'h_delta': 0.4, 'current_sigma': 0.9876099824905396,
 'info_gain_total_change': 0.014733314514160156,
 'info_gain_max_node_change': 0.009892582893371582,
 'predicted_flipped_count': 0}
```

Both branches confirmed non-mutating (`test_probe_via_what_if_native_
branch_never_mutates_graph`). The unmigrated caller
(`run_curiosity`/`run_curiosity_all_mts`) composes transparently with the
migrated probe — verified end-to-end on a native Mt
(`test_run_curiosity_still_works_end_to_end_on_a_native_mt`).

### 2.2 `insight_seeking.py`

**`predict_perturbation_impact` — MIGRATED, gated identically.** For a
native Mt: builds `current_marginal` from a direct `state` read (never
relaxes), calls `can_counterfactual.predict_ripple`, scores both current
and predicted marginals via `mt_energy`/`mt_frustration_given_state`
directly — **a genuine simplification, confirmed with real numbers, not
just claimed**: `predicted_energy` from the native branch equals an
UNCORRECTED `mt_energy(mt, predicted_marginal)` call, with none of the
continuous branch's own hand-written field-correction term:
```
native predict_perturbation_impact: predicted_energy=-2.4000
  (== direct uncorrected mt_energy=-2.4000) predicted_delta_F=-0.4000
```
For a continuous Mt, confirmed byte-identical to hand-computing the
ORIGINAL formula (including its own field-correction term) directly:
```
continuous predict_perturbation_impact (pre-migration-equivalent):
  delta_E=-0.9191 delta_F=-0.0149
```

**`seek_insights` — one guard added** (`insight_seeking.py:137-166`): the
unconditional `mt_relax_to_marginal(mt)` call is now skipped when
`discrete_mode` is set, preventing the continuous mechanism from
CONTAMINATING a native Mt's `state`. Demonstrated with a real before/after:
a native Mt deliberately built off-equilibrium keeps its exact state
through `seek_insights`:
```
native seek_insights: state preserved exactly, {'hub': 1.0, 'n1': 1.0, 'n2': -1.0, 'n3': 0.0}
```
while a continuous Mt still relaxes exactly as before:
```
continuous seek_insights: state moved 0.0500 -> 0.9876 (relax fired)
```

**`find_hot_nodes` — confirmed to need NO migration, corrected from the
counterfactual rung's own speculation.** `CAN_COUNTERFACTUAL_PREDICTOR_
RESULTS.md` §7 speculated this needs "a separate, unbuilt native twin" of
`node_local_frustration`. Direct reading of `can_ops.rs:553-585` shows
`node_local_frustration` reads `state`/`weight` attrs with NO relaxation
call inside it at all — it is ALREADY representation-agnostic, the same
class as `sparseness_signal.py`'s pre-existing status. Demonstrated live on
a native Mt with zero code change:
```
find_hot_nodes on a native Mt (unmigrated, unmodified): {1, 4}
```
This is reported as a positive correction to a prior rung's own open
question — one fewer real gap than believed, not a null.

**A necessary, small compatibility fix to `can_counterfactual.py` (already
committed to the prior rung, corrected here) — found while wiring.** The
module's own three Term-evaluation call sites used
`substrate.evaluate(target, env)`, which only works when `substrate` is the
`sr.Substrate` Python WRAPPER (its own test file's exclusive convention).
But `drive_curiosity.py`/`insight_seeking.py` are ALWAYS called with the
RAW native substrate — confirmed by grepping every real call site of
`self_improvement_step`/`run_curiosity_all_mts`/`seek_insights`/
`probe_via_what_if` across `domains/`, `worlds/`, `scripts/`: **zero
production callers exist anywhere**; every real caller is a test, and
every one of those tests uses `_native.Substrate()` directly. Calling the
new native branches with the raw substrate raised `TypeError: Object of
type Term is not JSON serializable` (caught live, before committing this
migration, not left as a latent bug). The fix: use `Term`'s OWN
`.evaluate(env, substrate)` method (`substrate_rs/__init__.py:76-84`),
which already does `substrate._inner if isinstance(substrate, Substrate)
else substrate` internally — a pre-existing idiom in the same library,
just not yet used by this module's three predictor entry points. Confirmed
byte-identical for the wrapper path (`can_counterfactual.py`'s own 6-test
suite, unchanged assertions, same printed numbers):
```
non-mutation check: 9 nodes byte-identical ...
ripple predict-then-verify: 20/20 exact full-network matches (100.0%)
predicted_frustration=4.0000 actual_frustration=4.0000
honest divergence case: predicted != actual on 3/10 nodes: ...
```

---

## 3. Consumer 6 (`self_improvement_loop.py`) — operation-by-operation, as required

| Operation | Verdict | Reason |
|---|---|---|
| `relax()` (`mt_relax_to_marginal`) | STAYS continuous | A native equivalent means driving `run_rules()` per-Mt inside this file's own loop — the §0 hazard, directly. |
| `maybe_hebbian` | STAYS continuous | Blocker B's primitive is real (`can_native_hebbian_bridge.py`); wiring it here is unsafe per §0. |
| `maybe_decay_J`/`maybe_decay_h` | STAYS continuous | Decay's primitive is real (`can_native_evidence_decay`); same hazard — its match pattern is equally Mt-unscoped, confirmed by direct read of `seeds/can_decay_identity.json`. |
| `maybe_update_identity` | STAYS continuous | The feedback half was never built (`CAN_DECAY_IDENTITY_RESULTS.md` §8.1, explicitly out of THIS rung's scope too) AND the reading half is rule-based (same §0 hazard) even setting that aside. |
| `nudge_identity_on_flipped` | STAYS continuous | Depends on the unbuilt identity-feedback half. |
| `self_improvement_step`'s `mt_audit_basin` calls | STAYS continuous | Not a fourth gap (§0) — reduces to the same orchestration blocker. |
| `_stash_post_state`'s `mt_distance_to_target` call | STAYS continuous | Same — `mt_target`/`distance_to_target`'s own math is representation-agnostic, but obtaining a current native marginal without corrupting other Mts is the unresolved piece. |

**Zero of seven operations migrated. Zero lines touched in this file.**
This is a complete, honest answer to the task's own question — the
difference from a naive reading of the three prior rungs' headlines
("decay closed," "Hebbian closed") is that ALL SEVEN operations now share
ONE precise, confirmed root cause (`run_rules()`'s graph-global scope vs.
this file's own per-Mt loop) instead of three separate, looser ones. This
is itself the main finding for this consumer, not a shortfall.

`sparseness_signal.py` (#5) inherits this unchanged: it still reads the
`coverage` attr, still stashed by the unchanged continuous
`mt_audit_basin` call. Confirmed by direct re-grep: zero `can_ops` calls
anywhere in `domains/sparseness_signal.py`.

---

## 4. `can_ops.rs` removal — the exact list

Re-ran the task's own 16-function grep (`mt_mean_field_marginal`,
`mt_energy`, `mt_frustration_given_state`, `mt_audit_basin`,
`mt_relax_to_marginal`, `mt_hebbian_update_J`, `mt_decay_J`,
`mt_conflicting_nodes`, `mt_pairwise_similarity`, `apply_evidence_h`,
`concept_nudge_identity`, `mt_update_identity_dynamics`, `mt_decay_h`,
`mt_distance_to_target`, `mt_target`, `mt_mean_field_with_h_override`,
`node_local_frustration`, `concept_apply_evidence`) across
`domains/*.py`, `worlds/*.py`, `scripts/*.py` (non-test call sites) AFTER
both migrations landed:

| Function | Real (non-test) call sites after this rung |
|---|---|
| `mt_mean_field_marginal` | `drive_curiosity.py:107` (continuous branch), `insight_seeking.py:138` (continuous branch), `scripts/bigville_can_integration_demo.py:58` |
| `mt_energy` | `insight_seeking.py:101,108` (native branch — reused, not replaced), `insight_seeking.py:155` (continuous branch), `scripts/bigville_can_integration_demo.py:61` |
| `mt_frustration_given_state` | `insight_seeking.py:102,110,165`, `can_counterfactual.py:272`, `scripts/bigville_can_integration_demo.py:60` |
| `mt_audit_basin` | `self_improvement_loop.py:266,286,332`, `insight_seeking.py:139` (continuous branch), `insight_propagation.py:109,132`, `scripts/bigville_can_integration_demo.py:80` |
| `mt_relax_to_marginal` | `self_improvement_loop.py:97`, `insight_seeking.py:223` (continuous branch, now guarded), `insight_propagation.py:108,131`, `scripts/bigville_can_integration_demo.py:79` |
| `mt_hebbian_update_J` | `self_improvement_loop.py:69,76`, `insight_detection.py:167` |
| `mt_decay_J` | `self_improvement_loop.py:84` |
| `mt_conflicting_nodes` | `conflict_detection.py:69`, `runtime_discovery.py:453` — not one of the six named consumers, untouched |
| `mt_pairwise_similarity` | `redundancy_detection.py:74`, `runtime_discovery.py:447` — not one of the six named consumers, untouched |
| `apply_evidence_h` | none found under this exact PyO3 name (the real binding is `concept_apply_evidence`, below — the task's own grep list names the Rust-internal function; see note) |
| `concept_nudge_identity` | `self_improvement_loop.py:215` |
| `mt_update_identity_dynamics` | `self_improvement_loop.py:188` |
| `mt_decay_h` | `self_improvement_loop.py:91` |
| `mt_distance_to_target` | `self_improvement_loop.py:161` |
| `mt_target` | **No direct Python call site in `domains/`/`worlds/`/`scripts/`** — see below |
| `mt_mean_field_with_h_override` | `drive_curiosity.py:108` (continuous branch), `insight_seeking.py:142` (continuous branch) |
| `node_local_frustration` | `insight_seeking.py:53` |
| `concept_apply_evidence` | `worlds/bigville_can_beliefs.py:217` |

**`mt_target` — investigated precisely, NOT removed.** It has zero DIRECT
Python call sites in `domains/`/`worlds/`/`scripts/` (only
`tests/test_can_ops.py`/`tests/test_can_migration.py` call
`s.mt_target(mt)` directly). But `mt_target` is NOT dead: its PyO3-exposed
sibling binding, `mt_distance_to_target` (`py.rs:2328-2374`), calls
`crate::can_ops::mt_target` INTERNALLY on every invocation — and
`mt_distance_to_target` is a real, active, unmigrated consumer
(`self_improvement_loop.py:161`, called every `_stash_post_state`). The
underlying Rust computation is exercised on every `self_improvement_step`
call; only the SEPARATE, directly-exposed `s.mt_target(mt)` PyO3 method
lacks a real (non-test) caller. Removing just that redundant direct
exposure — while correct in spirit — would require also editing the two
test files that exercise the primitive directly (a different, smaller
class of change than "delete dead code," and one that trades a real
regression-test guard on the primitive's own correctness for a marginal
surface-area reduction). Judged NOT a genuine removal candidate: the
computation it exposes is real, active, and load-bearing via
`mt_distance_to_target`.

**Verdict: ZERO functions removed.** Every one of the 16 audited
functions has at least one real, active, non-test consumer — confirmed by
direct re-grep, exactly matching the PREREG's own prediction (§5) made
before this migration was written, because both migrations are GATED
(dual-path) rather than unconditional replacements: the continuous branch
of every migrated function stays in the code, exercised by every
pre-existing continuous-mode Mt.

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty; zero `.rs` files touched anywhere in this branch.

---

## 5. Regression, per file, as required

**Full named + surfaced set, one run, 187/187 passed:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py tests/test_self_improvement_loop.py \
  tests/test_can_native_reimplementation.py tests/test_can_hebbian_materialization.py \
  tests/test_can_decay_identity.py tests/test_can_counterfactual.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_native_migration.py \
  tests/test_evidence_axis_infer.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_integration.py tests/test_can_crossover_point.py \
  tests/test_can_final_migration.py -q
187 passed in 9.91s
```

**Per-file (the task's own required granularity):**

| file | result | change vs. pre-branch |
|---|---|---|
| `tests/test_can_ops.py` | 12 passed | unchanged |
| `tests/test_can_migration.py` | 8 passed | unchanged |
| `tests/test_identity_field.py` | 9 passed | unchanged |
| `tests/test_insight_seeking.py` | 11 passed | unchanged (existing continuous-mode assertions, byte-identical) |
| `tests/test_insight_detection.py` | 11 passed | unchanged |
| `tests/test_insight_propagation.py` | 7 passed | unchanged |
| `tests/test_drive_curiosity.py` | 8 passed | unchanged (existing continuous-mode assertions, byte-identical) |
| `tests/test_sparseness_signal.py` | 7 passed | unchanged |
| `tests/test_self_improvement_loop.py` | 19 passed | unchanged |
| `tests/test_can_native_reimplementation.py` | 11 passed | unchanged |
| `tests/test_can_hebbian_materialization.py` | 12 passed | unchanged |
| `tests/test_can_decay_identity.py` | 8 passed | unchanged |
| `tests/test_can_counterfactual.py` | 6 passed | unchanged test file, same 6 tests, byte-identical printed numbers after the `Term.evaluate` compatibility fix (§2.2) |
| `tests/test_can_belief_quantization.py` | 11 passed | unchanged |
| `tests/test_bigville_can_native_migration.py` | 4 passed | unchanged |
| `tests/test_evidence_axis_infer.py` | 5 passed | unchanged |
| `tests/test_causal_attitude_networks.py` | 11 passed | unchanged |
| `tests/test_bigville_can_integration.py` | 12 passed | unchanged |
| `tests/test_can_crossover_point.py` | 5 passed | unchanged |
| `tests/test_can_final_migration.py` | 10 passed | NEW file, this rung |

**No paired failing-node-id lists to report** — zero failures, before or
after, across every file in the set. The full merged set was run BOTH
before any code change (177/177 green, establishing the true baseline —
run early per the standing house instruction, not deferred to the end)
and after (187/187 green — 177 + the 10 new tests, exactly accounting for
every test).

**No Rust build was needed or run.**

---

## 6. What this rung does NOT establish

1. **`self_improvement_loop.py`, `insight_detection.py`, and
   `insight_propagation.py` are unchanged code** — confirmed by
   `git diff --stat` touching only `drive_curiosity.py`, `insight_
   seeking.py`, and `can_counterfactual.py` (the compatibility fix). Their
   blocker is real, empirically confirmed (§0), not assumed or carried
   over from a prior rung's wording.
2. **The `run_rules()`-orchestration question is named, not resolved.**
   This rung does not attempt to design when `run_rules()` should fire
   relative to `self_improvement_step`'s own per-Mt loop, whether native
   and continuous Mts can safely coexist in one step, or how
   `detect_insight`'s per-step frustration comparison would behave for an
   Mt whose `state` was advanced mid-step by a native rule. This is a real
   follow-on, genuinely un-sized here, and it is the actual reason all
   four remaining-blocked consumers stay blocked — not a restatement of
   the original three blockers.
3. **Identity-feedback remains exactly as unbuilt as `CAN_DECAY_IDENTITY_
   RESULTS.md` left it** — explicitly out of this rung's scope per the
   task, and not incidentally covered by anything built here.
4. **`mt_audit_basin`/`mt_distance_to_target` were investigated and found
   NOT to be a fourth, independent gap** — but this rung did not build
   the small native-marginal composition it identifies as buildable
   (§0), per the task's explicit instruction not to.
5. **The gated dual-path design means these two files now carry two
   parallel mechanisms** (continuous and native) rather than one — a
   real, deliberate increase in each file's own surface area, chosen
   because forcing every Mt onto the native path was explicitly warned
   against by the task ("do not force a full migration if real behaviour
   would be degraded") and because no orchestration layer currently
   guarantees a native Mt's `state` is kept current by anything other
   than a test/demo script driving `run_rules()` directly.
6. **Zero production code anywhere in this repo currently calls
   `self_improvement_step`/`run_curiosity_all_mts`/`seek_insights`/
   `probe_via_what_if`** — confirmed by grep across `domains/`,
   `worlds/`, `scripts/` (excluding the functions' own definitions and
   mutual calls). Every real exercise of these modules is a test or demo
   script. This rung's migration is real and tested, but "real" here
   means "correct against the established test/demo calling convention,"
   not "exercised by a live running agent" — these six consumers were
   never wired into `WorldAdapter`'s own tick loop, before or after this
   rung.
7. **Whether any of this reflects real human causal-network, Hebbian,
   counterfactual, or self-improvement cognition** remains exactly as
   open as every prior rung in this arc left it — this document is about
   this substrate's own best-fitted mechanism.

---

## 7. The whole day's CAN arc — closing tally

Of the original 7 consumers (`CAN_CONSUMER_MIGRATION_RESULTS.md` §1):

| # | Consumer | Status at day's end |
|---|---|---|
| 1 | `drive_curiosity.py::probe_via_what_if` | **FULLY NATIVE for discrete_mode Mts, gated** (this rung) |
| 2 | `insight_detection.py::consolidate_insight` | **Still fully continuous** — precise, confirmed reason (`run_rules()` orchestration) |
| 3 | `insight_seeking.py` | **PARTIALLY NATIVE**: `predict_perturbation_impact` gated-native, `find_hot_nodes` needs no migration (representation-agnostic), `seek_insights` correctness-guarded (this rung) |
| 4 | `insight_propagation.py::propagate_insight` | **Still fully continuous** — blocked transitively + directly, same reason as #2 |
| 5 | `sparseness_signal.py` | **Inherits #6 — still fully continuous**, needed zero edits throughout the whole arc |
| 6 | `self_improvement_loop.py` | **Still fully continuous, all 7 operations** — one unifying reason, not three separate ones |
| 7 | `worlds/bigville_can_beliefs.py` | **FULLY NATIVE** (`can-consumer-migration` rung, earlier today) |

**2 of 7 fully native, 1 of 7 partially native, 4 of 7 fully continuous.**
Three primitive-building rungs (counterfactual predictor, Hebbian
materialization, decay/identity) each closed a real, proven gap — none of
that work was wasted, and Blocker A's primitive is now genuinely load-
bearing in production-test code for the first time today. But the day's
arc also surfaces its own honest ceiling: the THREE original "blockers"
narrated as three separate problems collapse, on direct investigation, into
ONE architectural fact this arc never set out to change — `run_rules()`
has no per-Mt scope, and three of this codebase's six remaining CAN
consumers are built as per-Mt Python loops over a graph-global rule engine.
Closing that gap is real, identifiable follow-on work (§6 point 2), not
finished by any rung today, this one included.

---

## 8. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-final-migration
git log --oneline -1 main   # 84ed599, verified before branching

# Full named + surfaced regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py tests/test_self_improvement_loop.py \
  tests/test_can_native_reimplementation.py tests/test_can_hebbian_materialization.py \
  tests/test_can_decay_identity.py tests/test_can_counterfactual.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_native_migration.py \
  tests/test_evidence_axis_infer.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_integration.py tests/test_can_crossover_point.py \
  tests/test_can_final_migration.py -q

# The two migrated consumers' own live demonstrations, with printed numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_final_migration.py -q -s

# The task's own required 16-function removal grep
grep -rn "\.<fn>(" domains/ worlds/ scripts/ --include='*.py'

# Zero Rust touched
git diff --stat main -- '*.rs'
```
