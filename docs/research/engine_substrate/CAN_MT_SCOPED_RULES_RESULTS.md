# Per-Mt scoped rule fixpoint — closing the `run_rules()`-orchestration blocker — RESULTS

Prereg: `CAN_MT_SCOPED_RULES_PREREG.md`, same worktree/branch, base
`main @ d9edae8` ("Merge can-final-migration: wire the three closed
primitives, find the real reason 4/6 stay blocked, GO"), verified via
`git log --oneline -1 main` before branching. Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-mt-scoped-rules`, branch
`can-mt-scoped-rules`.

**Verdict, up front:** the scoping primitive is real, additive, and proven
on the real engine — backward compatibility holds byte-for-byte (structurally
guaranteed, not merely tested-to-match), and two independent Microtheories
demonstrably stay isolated in both directions on live numbers. Three of the
four named consumers are migrated with the same gated dual-path pattern
prior CAN rungs established (`consolidate_insight`, `propagate_insight`,
four of `self_improvement_loop.py`'s seven operations); `maybe_decay_h`,
`maybe_update_identity`, and `nudge_identity_on_flipped` stay honestly
blocked for two DIFFERENT, precisely-identified reasons that are NOT the
orchestration hazard this rung fixes — one semantic (no native quantity
plays h's role), one the confirmed-independent identity-feedback gap named
by the task's own point 4.

---

## 1. The matching-loop investigation — where the filter goes, and why

**Two matching engines exist, not one — the first finding, made before any
code was written.** `runners/dsl/src/rewrite.rs::run_rules`/`run_rules_opts`
(confirmed by direct read, `:2116-2148` at this rung's base commit) is a
free-function fixpoint matcher. But the PRODUCTION entry point every Python
caller actually reaches — `Substrate::run_rules`/`run_rules_opts`
(`substrate.rs:4114-4166`, delegating to `run_rules_opts_filtered` at
`:4168-4326`) — is a SEPARATE, much larger engine: a dirty-bit-tracked
incremental scheduler (`attempt_one_rule`, `substrate.rs:3606+`) with
per-rule cursors (`try_incremental_match`), predicate retraction
(`try_predicate_retraction`), an "empty-match provably" fast exit, and a
projection cold path. Retrofitting per-Mt scope into THAT machinery safely,
as a strictly additive change, would mean touching cursor invalidation,
predicate-retraction bookkeeping, and the projection cold path — none of
which have any per-Mt dimension today. **Decision: do not touch it.** The
scoped runner is a freshly-written, always-full-rematch loop
(`rewrite::run_rules_opts_scoped`, `rewrite.rs:2291-2374`) reached only via
a brand-new `Substrate::run_rules_scoped` method
(`substrate.rs:4360-4402`) whose `scope_mt=None` arm calls the EXISTING
`self.run_rules_opts(...)` directly — not a re-implementation, the literal
same call. This is why "None reproduces exact behaviour" is a structural
guarantee here, not an empirical hope: there is no new code on that path at
all.

**Where the filter goes: POST-match, not pre-match.** Two options existed:
narrow the candidate node set before the backtracking matcher runs
(cheaper, but needs knowing WHICH pattern variable denotes "the Mt" per
rule — not declared anywhere in `RewriteRule`), or let `match_rule_each`
enumerate exactly as it does today and discard any binding that doesn't
TOUCH the target Mt's owned nodes afterward (safe regardless of which
variable carries the Mt reference, at the cost of not pruning the search).
**Decision: post-match**, per the task's own explicit correctness-over-
performance framing. Implemented as `binding_touches_scope`
(`rewrite.rs:2268-2280`): a binding is in-scope iff AT LEAST ONE of its
bound `NodeID`s is a member of `owned(mt)`.

**Ownership definition reused, not invented.** `mt_owned_nodes`
(`rewrite.rs:2244-2258`) is `{mt} ∪ neighbours(mt, has_concept)` — literally
`can_ops.rs::mt_concepts`'s own membership definition
(`g.neighbours(mt_id, Some(has_concept))`, `can_ops.rs:156-158`), plus the
Mt node itself.

**Named limitation, checked against the real rule corpus, not assumed.**
This is "touches ANY", not "touches ONLY" — a hypothetical rule whose
pattern spans two different Mts would fire when scoped to either. Direct
read of every rule in both native CAN seeds
(`can_native_reimplementation.json`: `can_native_update_3state`/`_2state`,
`can_native_basin_decode`, `can_native_note_coactivation`,
`can_native_hebbian_mint`/`_reweight`; `can_decay_identity.json`:
`can_native_evidence_decay`, `can_native_identity_evidence_sample`/`_decay`)
confirms every one binds a single `mt` variable consistently across its
whole pattern — none spans two Mts. In every real case today, the general
"touches ANY" filter reduces to an exact `binding["mt"] == target` check.

---

## 2. Backward-compatibility proof — byte-identical, verified directly

`tests/test_can_mt_scoped_rules.py::test_run_rules_scoped_none_is_byte_identical_to_run_rules_on_can_scenario`
reuses `test_can_native_reimplementation.py::_build_draw` verbatim (same
seed formula, same N=8 complete-graph construction) across 48 scenarios
(2 coarseness levels × 2 discrete modes × 12 seeds): for every one, the
EXISTING `run_rules(3000)` and the NEW `run_rules_scoped(3000, False,
None)` are called on independently-built-but-identically-seeded graphs, and
both the step count AND every Concept's final `state` are asserted equal.

```
backward-compat: 48 scenarios, run_rules_scoped(None) byte-identical to run_rules() on every one
```

A second test
(`test_run_rules_scoped_none_same_object_same_call_sequence`) cross-checks
one scenario built twice from the same seed, one path calling
`run_rules_scoped(None)` and the other the old `run_rules`, same result.
Both pass. Combined with §1's structural guarantee (the `None` arm IS
`run_rules_opts`, not a lookalike), this is the strongest form of the
correctness property the task named as non-negotiable.

---

## 3. Two-Mt isolation demonstration — real numbers, both directions, plus a negative control

Two independent, disjoint `Microtheory`s (`discrete_mode="3state"`, N=8
each, random `causal_influence` couplings + external fields, same
`_build_draw` construction, different seeds so both have real pending
updates) in ONE graph.

**Scoped to Mt A:**
```
scoped(mt_a): steps=9
  mt_a before=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  mt_a after =[0.0, 1.0, -1.0, -1.0, 1.0, -1.0, -1.0, 1.0]
  mt_b before=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  mt_b after =[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```
Mt A advanced (7 of 8 concepts flipped off zero); Mt B is byte-identical to
its pre-call snapshot.

**Scoped to Mt B, same graph, symmetric direction:**
```
scoped(mt_b): steps=12
  mt_a before=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  mt_a after =[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  mt_b before=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  mt_b after =[-1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0, -1.0]
```
Mt B advanced; Mt A is untouched.

**Negative control — the same scenario, the OLD unscoped call, proving the
isolation above is a property of scoping and not of the scenario happening
not to interact:**
```
unscoped run_rules(): mt_b changed = True
```
The unmodified `run_rules()` on this exact two-Mt graph DOES let Mt A's
rules touch Mt B — reproducing `CAN_FINAL_MIGRATION_RESULTS.md` §0's own
live probe on a fresh scenario, and confirming the isolation tests above are
not vacuous.

All four tests: `tests/test_can_mt_scoped_rules.py`, 5/5 passed.

---

## 4. Four-consumer migration table

| # | Consumer | Verdict | Reason / mechanism |
|---|---|---|---|
| 1 | `insight_detection.py::consolidate_insight` | **MIGRATED (gated)** | native branch: `run_rules_scoped(mt)` via `can_native_orchestration.scoped_settle`, isolated to the target Mt. `can_native_hebbian_mint`/`_reweight` already carry their own policy gate in the rule's `where`-clause — confirmed both never mint for a FROZEN native Mt (§4a). |
| 2 | `insight_propagation.py::propagate_insight` | **MIGRATED (gated)** | native branch for `other_mt`: `relax`/`_audit_basin` (both discrete_mode-gated in `self_improvement_loop.py`) replace `mt_relax_to_marginal`/`mt_audit_basin`, isolated to `other_mt` only (§4b). |
| 3 | `domains/sparseness_signal.py` | **Inherits #6 — 0 lines touched** | re-confirmed by direct re-grep: zero `can_ops`/`substrate.mt_*` calls in this file, only a docstring reference to `mt_audit_basin`. |
| 4 | `self_improvement_loop.py`, 7 operations | **4 of 7 migrated (gated), 3 stay honestly blocked** | see §4c table below. |

### 4a. `consolidate_insight` — live numbers

Adaptive native Mt, isolated pair, `discrete_mode="3state"`, equal strong
external fields (so the discrete update converges both concepts to the
SAME committed state and stays there — satisfying
`can_native_hebbian_mint`'s `Eq(state_a,state_b)`/`Not(Eq(state,0))` guards):

```
consolidate_insight tick1 (native, adaptive): scoped_steps=6 edge=False
consolidate_insight tick2 (native, adaptive): scoped_steps=4 edge=True
```
Mints on cross-tick recurrence, not on first sight — the SAME mint-on-
recurrence shape `test_can_native_reimplementation.py`'s own engine-level
test proves, now reached through the CONSUMER function, isolated to one
Mt via `run_rules_scoped`, not the engine-level API directly.

Frozen native Mt, same construction:
```
consolidate_insight (native, FROZEN): edge=False
```
Never mints — `can_native_hebbian_mint`'s own policy gate blocks it even
though `consolidate_insight`'s native branch no longer duplicates the
`mt_allows` check (the gate lives in the rule, not the Python orchestration,
by design — CAN_HEBBIAN_MATERIALIZATION_RESULTS.md).

Continuous Mt (no `discrete_mode`), unchanged path:
```
consolidate_insight (continuous): edges_updated=0
```

**A genuine simplification, reported not smoothed over**: the native
branch's return value is the scoped fixpoint's total progressing-step
count, not an "edges consolidated" count — the native mechanism has no
continuous `eta` knob (mint/reweight are threshold/counter-based). This
mirrors the precedent `CAN_FINAL_MIGRATION_RESULTS.md` §2.2 already set for
`predict_perturbation_impact`.

### 4b. `propagate_insight` — live numbers

Two native `3state` Mts sharing one Concept (`shared`), disjoint otherwise:
```
shared concepts: {5}
cascades: 1
  target_mt=4 shared=[5]
```
`find_shared_concepts` correctly identifies the shared node; the native
branch relaxes/audits `other_mt` (Mt B) via `run_rules_scoped(other_mt)` +
`native_audit_basin`, isolated from `source_mt` (Mt A) — the cascade record
is produced without either Mt corrupting the other, on the real engine.

### 4c. `self_improvement_loop.py`, operation by operation

| Operation | Verdict | Reason |
|---|---|---|
| `relax` | **MIGRATED (gated)** | native branch: `run_rules_scoped(mt)`. Continuous branch (`mt_relax_to_marginal`) byte-unchanged. |
| `maybe_hebbian` | **MIGRATED (gated)** | native branch: `run_rules_scoped(mt)`; `eta` unused there (no native analog), documented. |
| `maybe_decay_J` | **MIGRATED (gated), RE-TARGETED quantity** | native branch: `run_rules_scoped(mt)` lets `can_native_evidence_decay` fire — decays Hebbian `evidence_confirm`/`evidence_disconfirm` COUNTERS on the Coactivation ledger, not a graded `causal_influence` weight (native CAN has none). Reported as the closest real analog, not claimed equivalent. |
| `maybe_decay_h` | **STAYS BLOCKED** | Confirmed by direct read of BOTH native seeds: no rule anywhere decays `external_field`. This is a semantic gap, not the orchestration hazard — scoping cannot fix a quantity that doesn't exist. |
| `mt_audit_basin`/`mt_distance_to_target` calls (`_audit_basin` helper, `_stash_post_state`) | **MIGRATED (gated)** | native branch reads `state` directly (`native_marginal_from_state`) and composes `mt_energy`/`mt_frustration_given_state`/`mt_target`'s existing representation-agnostic math — the "small, real composition" `CAN_FINAL_MIGRATION_RESULTS.md` §0 named as buildable and did not build, now safe because it is a pure read, never calling `run_rules()` at all. |
| `maybe_update_identity` | **STAYS BLOCKED** | Identity-feedback gap (§5) — independent of scoping, confirmed by direct read. |
| `nudge_identity_on_flipped` | **STAYS BLOCKED** | Same identity-feedback gap. |

**4 of 7 operations migrated** (`relax`, `maybe_hebbian`, `maybe_decay_J`,
the `mt_audit_basin`/`mt_distance_to_target` composition); **1 of 7 stays
blocked for a semantic reason** (`maybe_decay_h`); **2 of 7 stay blocked for
the identity-feedback reason** (§5), confirmed genuinely separate from
orchestration.

**A real architectural finding, measured not assumed**: because
`run_rules_scoped` always runs a Mt's rules to a FULL fixpoint (every
gated-open native rule, not just the one the caller "meant"), the first
gated call in a `self_improvement_step` iteration (`relax`) can already
advance Hebbian mint/reweight and evidence decay for that Mt in the SAME
call. The later `maybe_hebbian`/`maybe_decay_J` calls are then idempotent
no-ops for the same `can_tick` (returning 0 steps) unless something changes
between calls. Observed live in the mixed end-to-end test:
```
native relax/hebbian/decay_J steps: relax=6 hebbian=0 decay_j=0
```
`relax` did all the settling work (6 progressing steps across whichever
native rules were dirty and gated-open); the subsequent `maybe_hebbian`/
`maybe_decay_J` calls found nothing left to do. This is a genuine
difference from the continuous path's four separate formula calls, not a
bug — the graph's own rule-priority order already decided what needed to
happen, and re-asking is safely idempotent. Reported here rather than
smoothed into "all four ran as if independent."

**End-to-end, mixed native + continuous, no crash, no leak**
(`test_self_improvement_step_mixed_native_and_continuous_no_crash_no_leak`):
```
self_improvement_step mixed result keys: [3, 6]
  mt=3 policy=adaptive pre_frust=0.0000 post_frust=0.0000 edges_hebbian=0
  mt=6 policy=adaptive pre_frust=0.5196 post_frust=0.5190 edges_hebbian=1
```
`self_improvement_step`'s real per-Mt loop runs on a graph with one native
and one continuous adaptive Mt, both produce correctly-shaped result dicts
(native Mt's `pre_audit` is the `native_audit_basin` composition,
`concept_count=2`, matching its own `has_concept` set), and neither Mt's
result depends on the other.

All consumer tests: `tests/test_can_mt_scoped_consumers.py`, 6/6 passed.

---

## 5. Identity-feedback investigation (task point 4) — CONFIRMED INDEPENDENT of scoping

Direct read, this rung, before writing this section:

- `can_native_update_3state`'s local-field sum
  (`can_native_reimplementation.json`, rule body) READS `identity_field` —
  confirmed present in its where/effects (grepped literally: 4 hits).
- `can_native_identity_evidence_sample`/`_decay`
  (`can_decay_identity.json`) maintain `identity_evidence_confirm`/
  `_disconfirm`/`_tick` — a SEPARATE ledger, never touching
  `identity_field` at all (confirmed: their `effects` arrays write only
  `identity_evidence_confirm`, `identity_evidence_disconfirm`,
  `identity_decay_tick`/`identity_evidence_tick`).
- **No rule anywhere writes `identity_field`.** Grepped both seeds'
  `effects` arrays for `identity_field` as a `set_attr` target: zero hits.
  It is read by the discrete update, never set by anything.

**Verdict: scoping does NOT resolve this gap, and it was never going to —
they are independent by construction.** Scoping is an ORCHESTRATION
property (which Mt a rule pass is allowed to touch); this gap is a
RULE-BODY property (whether any rule's effects write `identity_field` at
all). `run_rules_scoped` changes WHICH bindings a rule pass considers; it
adds no new effects to any rule. `maybe_update_identity` and
`nudge_identity_on_flipped` both need the feedback half built — a rule (or
rule edit) that writes `identity_field` from the evidence-count reading —
which `CAN_DECAY_IDENTITY_RESULTS.md` §2 already named and explicitly did
not build, and which remains out of THIS rung's scope per the task's own
instruction (§ "any change to CAN's actual relaxation/Hebbian/decay math
... only the SCOPING/orchestration layer is in scope").

---

## 6. Regression

### 6a. Full Rust suite (elevated, per task)

```
$ export PATH="/home/matt/.cargo/bin:$PATH"
$ RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH" \
  systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G -- \
  bash -c 'cd runners/dsl && cargo test --release --lib -- --test-threads=1'
...
test result: ok. 774 passed; 0 failed; 4 ignored; 0 measured; 0 filtered out
```
**774 passed, 0 failed, 4 ignored (pre-existing, unrelated to this rung).**
No paired failing-test list needed — nothing failed.

### 6b. CAN-adjacent Python suite (every file named in the task, plus this
rung's own two new test files)

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
  tests/test_can_final_migration.py tests/test_can_mt_scoped_rules.py tests/test_can_mt_scoped_consumers.py -q
198 passed in 10.28s
```
187 pre-existing (byte-unchanged, matching `CAN_FINAL_MIGRATION_RESULTS.md`
§5's own 187/187 baseline exactly) + 5 new engine-level scoping tests + 6
new consumer-migration tests = 198. Zero failures, zero regressions.

### 6c. Broad, non-CAN-specific sweep

A naive single-threaded `pytest tests/ -k migrated` was tried first and
found to be impractically slow in this environment (782 files, still only
~22% complete after 55 minutes of wall-clock — a per-process pytest
overhead problem, not a regression signal). Switched to this tree's OWN
sanctioned tool for exactly this measurement,
`scripts/failure_baseline_sweep.py` (the same tool `results/
failure_baseline.json` — cited by `CLAUDE.md`'s "optional-dep note" — was
built with): per-file subprocess isolation, parallel workers, an honest
`NOT_ESTABLISHED` status for anything that exceeds its budget rather than
recording a false red.

```
$ PYTHONPATH=".:runners/dsl/python" python3 scripts/failure_baseline_sweep.py \
  --workers 8 --timeout 300 --glob "tests/test_*migrated*.py" \
  --out results/can_mt_scoped_rules_sweep_raw.json
== 782 files, workers=8, wall_s=2286.3
GREEN: 592   RED: 145   NOT_ESTABLISHED: 27   ALL_SKIPPED: 18
```

**145 red files is consistent with this tree's own documented,
condition-dependent baseline** (`CLAUDE.md`'s "optional-dep note":
under the `data/` **absent** condition — this worktree's condition, not
symlinked — the documented figure is ~147 red files / 565 red node ids;
145 here is inside that same population, not a new number this rung
introduced). This is reported as a LIST cross-check, not a bare count, per
that same note's own standing rule:

- **Zero of the 145 RED files touch anything this rung changed.** Filtered
  the red file list for every CAN/insight/self-improvement-adjacent
  keyword (`can_`, `insight`, `self_improv`, `hebbian`, `decay`,
  `identity`): exactly ONE hit, `tests/test_decay_gradient_migrated.py` —
  read directly and confirmed to be the VISION "edge-anchored decaying
  gradient" (Cornsweet illusion) rung, entirely unrelated to CAN decay; its
  failure is a pre-existing `FileNotFoundError` for a missing
  `results/paint_measurement...` artifact, nothing to do with this rung's
  diff.
- **The two adjacent "migrated" files that DO share this rung's own
  vocabulary are both GREEN**: `tests/test_insight_migrated.py` and
  `tests/test_self_improvement_visibility_migrated.py` — direct
  confirmation, not inference, that the gated changes to
  `insight_detection.py`/`insight_propagation.py`/`self_improvement_loop.py`
  did not regress either.
- **None of the 27 `NOT_ESTABLISHED` (300s-budget-exceeded) files are
  CAN-adjacent either** — they are conversation/comprehension/vision
  integration files (`test_comprehension_cutover_migrated.py`,
  `test_recount_*_migrated.py`, `test_topic_route_selfheal_migrated.py`,
  etc.), unrelated to this rung's diff, exceeding budget for reasons
  predating this branch.
- **The CAN-specific suite (§6b, 198/198) is the decisive check for this
  rung's own diff** — every file this rung actually touched
  (`self_improvement_loop.py`, `insight_detection.py`,
  `insight_propagation.py`) has its OWN dedicated, exhaustive test
  coverage there, run directly against the gated code, not sampled
  through an 8-worker timeout-bounded sweep. This broad sweep's job was to
  catch anything the CAN-scoped check alone would miss elsewhere in the
  tree, and it found nothing.

Raw data: `results/can_mt_scoped_rules_sweep_raw.json` (782 per-file
entries, node ids + messages for every red/not-established file).

---

## 7. What this rung does NOT establish

1. **The scoped runner is unoptimised by design** (§1) — no incremental
   cursor reuse, no JIT where-clause, no rayon parallel collection. It is
   correct, not fast. A production-scale caller driving thousands of Mts
   per tick would need the incremental engine to grow a scope dimension —
   named, not built, per the task's own blast-radius discipline.
2. **The "touches ANY" filter is a documented generalisation, not proven
   exhaustive** — every rule in the real corpus binds one `mt` var
   consistently, so it reduces to an exact check today; a future rule that
   genuinely spans two Mts would need re-examination (§1).
3. **`maybe_decay_h` stays blocked because no native quantity plays h's
   role** — this is not a gap scoping could ever have closed. Building a
   native external-field decay rule (if one is ever wanted) is a rule-body
   design question, not an orchestration one, and is out of this rung's
   scope per the task's own instruction.
4. **Identity-feedback (§5) remains exactly as unbuilt as
   `CAN_DECAY_IDENTITY_RESULTS.md` left it** — confirmed independent of
   scoping by direct read, not built here, per the task's explicit
   instruction not to build it.
5. **The "one shared fixpoint" finding (§4c) is reported, not resolved
   into a cleaner API** — `self_improvement_step`'s four separate native
   calls per Mt (relax/hebbian/decayJ/decayh) still exist as four call
   sites even though the FIRST one now does most of the real work for a
   native Mt. Collapsing them into one explicit call is a real, un-sized
   follow-on this rung does not attempt (it would change
   `self_improvement_step`'s own control flow beyond the gated-dispatch
   pattern every other CAN rung in this arc has used).
6. **Whether any of this reflects real human causal-network, Hebbian, or
   self-improvement cognition** remains exactly as open as every prior
   rung in this arc left it — this document is about this substrate's own
   best-fitted mechanism.

---

## 8. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-mt-scoped-rules
git log --oneline -1 main   # d9edae8, verified before branching

export PATH="/home/matt/.cargo/bin:$PATH"
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH" \
  bash scripts/engine_build.sh
# NOTE: this environment's `engine_build.sh` fails its own final
# `record_build()` step because `python` (not `python3`) is not on PATH —
# a pre-existing environment gap, unrelated to this rung. Work around it:
PYTHONPATH=".:runners/dsl/python" python3 -c \
  "from domains.engine_provenance import record_build; record_build()"

# Core engine proof: backward-compat + two-Mt isolation, real numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_mt_scoped_rules.py -q -s

# Consumer migrations, real numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_mt_scoped_consumers.py -q -s

# Full Rust suite
systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G -- \
  bash -c 'cd runners/dsl && cargo test --release --lib -- --test-threads=1'

# Full CAN-adjacent Python regression
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py tests/test_self_improvement_loop.py \
  tests/test_can_native_reimplementation.py tests/test_can_hebbian_materialization.py \
  tests/test_can_decay_identity.py tests/test_can_counterfactual.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_native_migration.py \
  tests/test_evidence_axis_infer.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_integration.py tests/test_can_crossover_point.py \
  tests/test_can_final_migration.py tests/test_can_mt_scoped_rules.py tests/test_can_mt_scoped_consumers.py -q
```
