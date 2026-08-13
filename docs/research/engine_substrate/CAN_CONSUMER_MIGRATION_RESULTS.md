# The seven real CAN consumers — migration executed against the PREREG audit — RESULTS

Prereg: `CAN_CONSUMER_MIGRATION_PREREG.md`, same worktree/branch, base
`main @ 41232aa` ("Merge logodds-diminfer: TimeInfer automatic recognition
of the evidence-accumulation generator, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-consumer-migration`, branch
`can-consumer-migration`.

**Verdict, up front: 1 of 7 consumers migrated (Bigville), 6 of 7 correctly
left on the continuous mechanism, each with a precisely named, real
blocker.** The charter's own instruction ("remove the old can and replace
it with the new one") is honoured at the depth the actual code supports,
not forced: `can_ops.rs`/`causal_attitude_networks.json` are UNTOUCHED
(`git diff --stat main -- '*.rs' '*.json'` empty) because every one of the
functions they declare has at least one real, currently-irreplaceable
consumer — confirmed per-function, not assumed. Two of the seven
consumers required no code change at all to reach their honest final
state: `sparseness_signal.py` was already representation-agnostic (it
reads a stashed attr, not a can_ops call), and five of the remaining six
files needed literally zero lines touched because the PREREG audit found
their blockers were real, not because they were skipped. Only two files
changed: `worlds/bigville_can_beliefs.py` (the named schema fix + the
migration) and `tests/test_can_native_reimplementation.py` (one stale
assertion, updated honestly, not silently left wrong, per this session's
own standing practice).

---

## 1. The seven-consumer audit table, as executed

Reproduced from the PREREG (§1), now marked with the executed outcome.
File:line citations confirmed by direct read in this rung, not carried
over from the pre-dispatch grep.

| # | Consumer | Real can_ops call site(s) | Blocker | Outcome |
|---|----------|---------------------------|---------|---------|
| 1 | `domains/drive_curiosity.py` | `probe_via_what_if` (`:76-78`, `mt_mean_field_marginal` + `mt_mean_field_with_h_override`) | **Blocker A** — no native non-mutating counterfactual predictor exists anywhere in this arc; `run_rules()` always mutates. | **BLOCKED**, unchanged, 0 lines touched. |
| 2 | `domains/insight_detection.py` | `consolidate_insight` (`:167`, `mt_hebbian_update_J`) | **Blocker B** — the native log-odds render is intentionally non-materializing (`LOGODDS_GENERATOR_RESULTS.md` §2/§4(b): confirmed live, never writes graph state); nothing wires it back to `causal_influence.weight`. | **BLOCKED**, unchanged, 0 lines touched. Pre-dispatch grep's `:156 relax_to_marginal` attribution corrected — that line is a docstring mention, not a call (confirmed: `grep -n "relax_to_marginal" domains/insight_detection.py` returns exactly one hit, the docstring). |
| 3 | `domains/insight_seeking.py` | `find_hot_nodes` (`:53`, `node_local_frustration`); `predict_perturbation_impact` (`:81,82,85,98,108`); `seek_insights` (`:157`, `mt_relax_to_marginal`) | **Blocker A**, compounded — `mt_energy`/`mt_frustration_given_state` are evaluated on an UNGROUNDED hypothetical marginal dict never written to the graph; no native decode/rule path can evaluate a state that was never committed. | **BLOCKED**, unchanged, 0 lines touched. |
| 4 | `domains/insight_propagation.py` | `propagate_insight` (`:108,109,132`, relax+audit; `:129` calls `insight_detection.consolidate_insight`) | **Blocker B**, transitively, plus a genuine coherence risk: the relax+audit half is individually native-shaped, but swapping only that half while `consolidate_insight` (Blocker B) and `self_improvement_loop.py`'s own separate per-tick relax (consumer 6) both keep running continuously on the SAME Mt would run two never-jointly-validated relaxation mechanisms against one shared Mt across different code paths. | **BLOCKED**, unchanged, 0 lines touched. |
| 5 | `domains/sparseness_signal.py` | **None, directly.** Reads `attrs["coverage"]`, stashed exclusively by consumer 6. | Inherited from consumer 6. | **BLOCKED, transitively — confirmed by direct read that ZERO can_ops calls exist in this file.** 0 lines touched (none were ever needed; the file is already representation-agnostic). |
| 6 | `domains/self_improvement_loop.py` | `relax()` (`:97`); `maybe_hebbian` (`:69,76`, Blocker B); `maybe_decay_J`/`maybe_decay_h` (`:84,91`); `maybe_update_identity` (`:188`); `nudge_identity_on_flipped` (`:215-216`); `self_improvement_step` (`:266,286,332`, `mt_audit_basin`; `_stash_post_state` `:161`, `mt_distance_to_target`) | **Three independent blockers on the SAME step function**: (a) decay — confirmed, across all three prior rungs, to have NO native analog proposed anywhere, and explicitly out of this rung's scope to build; (b) Blocker B (Hebbian); (c) identity dynamics — never one of the five claims the spike mapped, no native design exists at all. | **BLOCKED**, unchanged, 0 lines touched. Even a partial relax+audit swap would leave this function calling `can_ops.rs` for 5 of its 7 real operations every tick, so nothing in `can_ops.rs` could be removed regardless, and it would propagate the same mixed-mechanism risk named in consumer 4 into every downstream consumer's shared Mt state. |
| 7 | `worlds/bigville_can_beliefs.py` | `build_resident_can_mt` (structural edges); `apply_scenario_evidence` (`concept_apply_evidence`) | Named, sized, verified-backward-compatible one-line fix (`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §7) | **MIGRATED.** See §2. |

**Tally: 1/7 migrated, 6/7 correctly blocked.** Of the six blocked, three
distinct root causes account for all of them: Blocker A (no native
counterfactual predictor: consumers 1, 3), Blocker B (Hebbian graded
reweighting's native half is non-materializing: consumers 2, 4, 6), and
decay/identity dynamics having no native design at all (consumer 6 only).
Consumer 5 is the special case of a file with zero direct dependency,
blocked only by inheritance.

---

## 2. The Bigville migration — built and demonstrated

### 2.1 The schema fix

`worlds/bigville_can_beliefs.py`'s `STRUCTURAL_EDGES` loop
(`build_resident_can_mt`, was `:176-181`) now mints BOTH directions of
every structural coupling with the SAME weight:

```python
s.add_edge(concepts[a], "causal_influence", concepts[b], {"weight": q_j})
s.add_edge(concepts[b], "causal_influence", concepts[a], {"weight": q_j})
```

**Confirmed additive-risk-only for the continuous mechanism, measured
both ways, not assumed.** The exact pre-fix numbers on `main@41232aa`
(via `git stash` on this branch, re-running `pick_demo_residents`'
own lo/hi pair through the UNMODIFIED `scripts/bigville_can_integration_
demo.py::run_one`):

```
PRE-FIX  continuous lo frustration: 2.247044801712036   coupling_count: 5
PRE-FIX  continuous hi frustration: 1.6207002401351929  coupling_count: 5
POST-FIX continuous lo frustration: 2.247044801712036   coupling_count: 5
POST-FIX continuous hi frustration: 1.6207002401351929  coupling_count: 5
```

Byte-identical, to the last printed digit — exactly as
`build_couplings`'s in-edge de-dup (`can_ops.rs:180-191`) and
`enumerate_couplings`'s undirected-pair de-dup (`can_ops.rs:293-322`)
predicted. Gated as a regression:
`tests/test_bigville_can_native_migration.py::
test_symmetric_edge_fix_does_not_change_continuous_mechanism_numbers`.

**Confirmed the fix actually fixes the named visibility gap**, measured
directly: `claim_credible`'s IN-neighbour set is now a subset of its
OUT-neighbour set (both `{trust_mayor, debtor_trustworthy}`, i.e. `#2,#6`
in the test's node numbering) — before the fix, `trust_mayor` was
IN-only and invisible to the native rule's out-edges-only local field
(this is the exact fact `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §7
measured to make its "not a clean swap today" call). The pre-existing
test that measured the bug
(`tests/test_can_native_reimplementation.py::
test_bigville_schema_is_asymmetric_native_rule_reads_only_out_edges`) is
**updated, not silently left wrong** — renamed
`test_bigville_schema_symmetric_fix_makes_all_couplings_visible_to_native_
rule`, its docstring explains the history, and its assertion is inverted
(`len(in_only) == 0`, was `> 0`) to become the fix's own regression guard,
matching this session's own precedent (`LOGODDS_GENERATOR_RESULTS.md` §6,
the `test_ground_reductions_and_comprehend_theorem_untouched` scope-guard
update) for updating a stale assertion honestly rather than leaving a
red or a silently-wrong green.

### 2.2 The native migration itself

`tests/test_bigville_can_native_migration.py::
test_native_relaxation_reproduces_the_continuous_mechanisms_divergence`:
builds each of the two real demo residents' (lowest/highest
`resolution_bins`, `pick_demo_residents`' own selection —
`resolution_bins` 2 vs 11) CAN belief Mt with the fixed symmetric-edge
schema, applies the SAME `apply_scenario_evidence` unchanged, sets
`Mt.discrete_mode="3state"`, and runs the SEEDED `can_native_update_
3state` rule to a fixpoint via `run_rules()` — **replacing
`mt_relax_to_marginal`'s iterative mean-field relaxation entirely**,
confirmed by a source-inspection test
(`test_native_relaxation_never_calls_the_continuous_relaxation_op`) that
no `mt_relax_to_marginal`/`mt_mean_field_marginal`/`mt_mean_field_with_h_
override` call exists anywhere in the native demo path. Frustration on
the resulting DISCRETE state is read via `mt_frustration_given_state` —
reused unmodified as a closed-form, non-iterative, O(edges) scoring
utility, the SAME idiom `tests/test_can_native_reimplementation.py`'s own
`_frustration` helper already established for scoring native-produced
states (not a new pattern invented for Bigville).

**Real measured numbers, both mechanisms, same two real residents, same
scenario evidence:**

```
                        lo-res (bins=2)   hi-res (bins=11)   lo > hi ?
continuous (post-fix)   2.247045          1.620700           YES
native (this rung)      2.000000          1.285714           YES
```

Native relaxation converged in 3 `run_rules()` steps for both residents
(`steps < 3000`, `converged=True`, gated by
`test_native_relaxation_reproduces_the_continuous_mechanisms_divergence`'s
own assertion). Native discrete states, for the record:

```
lo-res: {trust_mayor:1.0, claim_credible:1.0, world_safe:1.0, self_worth:1.0, debtor_trustworthy:1.0}
hi-res: {trust_mayor:0.0, claim_credible:1.0, world_safe:1.0, self_worth:1.0, debtor_trustworthy:1.0}
```

**Confirmed: the native mechanism reproduces the SAME qualitative
divergence the continuous mechanism established in
`BIGVILLE_CAN_INTEGRATION_RESULTS.md`** — the low-resolution resident is
more frustrated/incoherent than the high-resolution resident on
identical evidence. The hi-res resident's `trust_mayor` settling at the
3-state deadzone (`0.0`, genuinely undecided) rather than committing is
itself a real, native-only observation the continuous (2-state-like,
never-exactly-zero in practice) mechanism does not expose the same way —
reported as an honest difference in HOW the two mechanisms represent
"not committed," not a discrepancy in the qualitative divergence being
tested.

### 2.3 What the Bigville migration does NOT cover

The existing demo script's `multi_start_basin_count` (genuine multi-start
enumeration, built entirely in Python on top of repeated CONTINUOUS
relaxation calls, `scripts/bigville_can_integration_demo.py:44-70`) is
UNCHANGED and stays on the continuous mechanism — per the spike's own
§3.1/§6 finding, enumeration has no native analog, and building one is
explicitly out of this rung's scope. `tests/test_bigville_can_integration.
py`'s existing `multi_start_sweep`-based assertion
(`test_low_resolution_resident_shows_more_rounding_error_and_more_
frustration`) continues to exercise the CONTINUOUS path unchanged and is
not claimed as migrated — confirmed still green, unmodified (§3 below).

---

## 3. Regression, per file, as required

**Full named + surfaced set, one run, 151/151 passed:**

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_self_improvement_loop.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_can_crossover_point.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_native_migration.py -q
151 passed in 8.91s
```

**Per-file (the task's own required granularity — no bare aggregate
count):**

| file | result | change vs. pre-branch |
|---|---|---|
| `tests/test_can_ops.py` | 12 passed | unchanged |
| `tests/test_can_migration.py` | 8 passed | unchanged |
| `tests/test_identity_field.py` | 9 passed | unchanged |
| `tests/test_insight_seeking.py` | 11 passed | unchanged |
| `tests/test_self_improvement_loop.py` | 19 passed | unchanged |
| `tests/test_can_belief_quantization.py` | 11 passed | unchanged |
| `tests/test_bigville_can_integration.py` | 12 passed | unchanged (fix confirmed additive-risk-only, §2.1) |
| `tests/test_insight_detection.py` | 11 passed | unchanged |
| `tests/test_insight_propagation.py` | 7 passed | unchanged |
| `tests/test_drive_curiosity.py` | 8 passed | unchanged |
| `tests/test_sparseness_signal.py` | 7 passed | unchanged |
| `tests/test_can_native_reimplementation.py` | 11 passed | ONE assertion updated honestly (§2.1), still 11/11 (same count, same test names except the one rename) |
| `tests/test_evidence_axis_infer.py` | 5 passed | unchanged |
| `tests/test_can_crossover_point.py` | 5 passed | unchanged |
| `tests/test_causal_attitude_networks.py` | 11 passed | unchanged |
| `tests/test_bigville_can_native_migration.py` | 4 passed | NEW file, this rung |

**No paired failing-node-id lists to report** — zero failures, before or
after, across every file in the set (confirmed by running the full set
BEFORE any code change, §0 of the working session, and again after).

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty; zero `.rs` files touched anywhere in this branch, matching the
PREREG's own §3 prediction that Phase 3 removal would find zero
zero-consumer functions to remove.

---

## 4. What was actually removed from `can_ops.rs`/`causal_attitude_networks.json`

**Nothing.** Confirmed by the diff itself
(`git diff --stat main -- '*.rs' '*.json'` returns empty) and by the
per-consumer audit (§1): every can_ops.rs function this arc's four prior
docs and this rung's own reading touch — `mt_mean_field_marginal`,
`mt_mean_field_with_h_override`, `mt_energy`, `mt_frustration_given_
state`, `node_local_frustration`, `audit_basin`/`mt_audit_basin`,
`hebbian_update_J`, `decay_J`, `decay_h`, `update_identity_dynamics`,
`nudge_identity`, `relax_to_marginal`, `apply_evidence_h` — has at least
one real, currently-irreplaceable Python consumer, OR (for
`mt_frustration_given_state` specifically) is reused unmodified, on
purpose, as a closed-form scoring utility by the Bigville migration
itself. This is the honest, expected, non-forced outcome the PREREG
predicted (§3) before any code was written, not a shortfall discovered
after the fact.

---

## 5. What this rung does NOT establish

1. **Six of seven consumers are unchanged code**, not migrated-and-
   reverted or migrated-and-hidden — confirmed by `git diff --stat`
   touching only two files. Their blockers (Blocker A, Blocker B, decay,
   identity dynamics) are REAL and were measured/read from source in this
   rung, not merely carried over from the task's own pre-dispatch grep
   (which, per §1 consumer 2, had at least one imprecise line
   attribution, corrected here).
2. **Blocker A (no native counterfactual predictor) is not sized as a
   follow-on rung here** — the PREREG names it precisely (§0) but building
   one (graph snapshot/restore semantics, or a pure functional multi-step
   evaluator) is real, unscoped design work, explicitly out of this
   rung's charge to attempt.
3. **Blocker B (log-odds render not wired to a weight write-back) is
   likewise not sized as a follow-on build** — `LOGODDS_GENERATOR_
   RESULTS.md`'s own deliberate non-materializing design for the render
   is a real constraint this rung respects rather than routes around;
   whether wiring a write-back is even the RIGHT fix (versus changing the
   discrete update rule to read log-odds directly) is an open design
   question this rung does not adjudicate.
4. **Decay and identity dynamics remain exactly as unbuilt, natively, as
   every prior rung in this arc left them** — this rung adds no new
   finding about either beyond confirming (again, by direct source read)
   that no proposal exists anywhere in `seeds/can_native_reimplementation.
   json`, `seeds/evidence_axis_infer.json`, or the four prior docs.
5. **The Bigville native migration covers the relaxation + frustration-
   scoring half only** — the multi-start basin-count enumeration half of
   the existing demo stays entirely on the continuous mechanism, by
   design (§2.3), per the spike's own explicit, unchanged finding that
   enumeration has no native analog.
6. **The native mechanism's `trust_mayor=0.0` (deadzone) outcome for the
   hi-res resident is reported as observed, not investigated further** —
   whether the 3-state deadzone is the RIGHT representation for "genuinely
   undecided" in a population-modeling context like Bigville (as opposed
   to the 2-state forced-commitment variant) is a real, open question this
   rung does not take a position on.
7. **This rung says nothing new about whether any of this reflects real
   human belief-network or social-population dynamics** — unchanged from
   every prior rung's own honest scope boundary.

---

## 6. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-consumer-migration
git log --oneline -1 main   # 41232aa, verified before branching

# Full named + surfaced regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_self_improvement_loop.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_can_crossover_point.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_native_migration.py -q

# The Bigville native migration demonstration specifically, with printed
# numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_bigville_can_native_migration.py -q -s

# Zero Rust/seed-JSON touched
git diff --stat main -- '*.rs' '*.json'
```
