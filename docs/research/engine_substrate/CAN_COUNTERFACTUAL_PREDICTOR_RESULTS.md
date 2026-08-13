# Blocker A — a native, non-mutating "what-if" counterfactual predictor for the discrete CAN mechanism — RESULTS

Prereg: `CAN_COUNTERFACTUAL_PREDICTOR_PREREG.md`, same worktree/branch, base
`main @ 299ace3` ("Merge can-consumer-migration: 1/7 migrated (Bigville),
6/7 honestly blocked, GO"). Worktree
`/home/matt/ozmadev/ocelot-worktrees/can-counterfactual-predictor`, branch
`can-counterfactual-predictor`.

**Verdict, up front: GO, with an honest, measured, non-fatal residual.**
The orchestrating session's lead held: a native, non-mutating "what-if"
predictor for the discrete CAN mechanism can be built ENTIRELY from
existing Term-evaluation machinery — zero new Rust, confirmed by
`git diff --stat main -- '*.rs'` returning empty. Two primitives were
built in `domains/can_counterfactual.py`:

1. **Zero-hop, single-node prediction** — EXACT, by construction, verified
   live on the real engine (predict-then-verify against actually running
   `run_rules()`, not merely asserted).
2. **Bounded, multi-round, Gauss-Seidel "ripple" prediction** (the
   network-wide equilibrium `probe_via_what_if`/`predict_perturbation_
   impact` actually need) — genuinely non-mutating, and **empirically
   accurate on 88/90 real predict-then-verify trials across three network
   shapes (97.8%)**, with **one honest, reproducible, named failure mode**:
   on some real draws it converges to a genuinely DIFFERENT (both
   individually valid) Hopfield attractor than `run_rules()` reaches,
   exactly the registered open question in the PREREG, now answered with
   real numbers rather than left open.

---

## 1. What was built

`domains/can_counterfactual.py` — a Term-builder + thin orchestration
driver, zero new Rust, zero graph mutation anywhere in the module:

- `local_field_term(node_var, external_field_var, node_state_overrides)` —
  a verbatim structural twin of `can_native_update_3state`/`_2state`'s own
  local-field sub-expression (`seeds/can_native_reimplementation.json:
  112-121` et al.): `external_field(c) [or a `Var` override] +
  identity_field(c) + Sum_{e in Edges(c,'causal_influence')}
  EdgeAttr(e,'weight') * state(target(e))` — with any neighbour's `state`
  read substitutable, per-edge, for a `Lit` baked in at TERM-BUILD time
  (Python already knows the override set before building the term; no
  dynamic `env` resolution is needed for this half).
- `target_state_term(local_term, mt_var, mode)` — the discrete Hopfield
  threshold ladder, verbatim twin of the seed's own `IfThenElse` chain
  (`ATANH_HALF = math.atanh(0.5)`, 3-state scales by `temperature`,
  2-state does not — matching the seed's own asymmetry exactly, confirmed
  by reading both rule bodies before writing this module, not assumed
  symmetric).
- `predict_single_step_target` / `predict_current_target` — ONE
  `Substrate.evaluate()` call each; the hypothetical `external_field`
  value is bound via `env` (`{"h_ovr": new_value}`), confirming the
  PREREG's own finding (`py.rs:948-969`'s `pydict_to_env` binds a `Var`
  name to ANY `Value` via `py_to_value`, not only node handles).
- `predict_ripple` — the bounded multi-round predictor: a Python loop over
  every `Concept` under `mt`, IN PLACE (Gauss-Seidel, matching
  `run_rules()`'s own "commit immediately, next read sees the update"
  cold-path semantics, `rewrite.rs:2183-2214`), each round re-evaluating
  `target_state_term` per Concept with every OTHER Concept's latest
  in-memory hypothetical state baked in as `Lit`s, stopping when a full
  round makes no change or at `max_rounds`. Every value change lives only
  in a returned Python dict; nothing is written to any node/edge attr.
- `predicted_info_gain` / `predicted_frustration` — the counterfactual
  twins of `probe_via_what_if`'s return shape and
  `predict_perturbation_impact`'s ΔF, the latter reusing
  `mt_frustration_given_state` (a pure, non-iterative, O(edges) closed-form
  utility — the SAME reuse `CAN_CONSUMER_MIGRATION_RESULTS.md` §2.2
  already established as legitimate for the Bigville migration) evaluated
  on THIS module's own predicted marginal instead of the continuous
  mechanism's.

**No agent decision lives in this module.** The one branching computation
that matters — the discrete Hopfield threshold — is entirely inside
`target_state_term`'s `IfThenElse`, evaluated by the Rust Term evaluator
every single call. Python's only choices are (a) which node's term to
build next and (b) when to stop a bounded sweep — the same shape
`drive_curiosity.py::run_curiosity_all_mts` and
`insight_seeking.py::seek_insights` already have today, looping over
Mts/hot-nodes/h-deltas without holding agent state.

---

## 2. Live demonstration (a) — zero-hop prediction is EXACT

`tests/test_can_counterfactual.py::test_zero_hop_prediction_is_exact_on_an_isolated_node`.
A single Concept with no `causal_influence` edges (nothing else CAN move);
five hypothetical `external_field` overrides (`-3.0, -0.2, 0.0, 0.3, 5.0`),
each: (1) confirmed non-mutating (byte-identical `dict(node.attrs)` before
and after the predict call), (2) confirmed EXACT — predicted value equals
the REAL state after actually committing the override and running
`run_rules()` to convergence, for all five overrides.

## 3. Live demonstration (b) — non-mutation on a real N=8 network

`test_predictor_never_mutates_graph_state_on_a_real_network`. A real N=8
complete-graph draw (the same shape `tests/test_can_native_reimplementation.
py::_build_draw` uses), relaxed to a real converged baseline via
`run_rules(3000)` first. All 9 nodes' (1 Mt + 8 Concepts) full attrs
snapshotted, then FIVE different predictor calls made
(`predict_single_step_target`, `predict_current_target`, `predict_ripple`,
`predicted_info_gain`, `predicted_frustration`), then re-snapshotted:

```
non-mutation check: 9 nodes byte-identical before/after 5 predictor calls;
ripple rounds=1 converged=True
```

Byte-identical, confirmed, every attr, every node, after every one of the
five predictor entry points — matching the exact check
`LOGODDS_GENERATOR_RESULTS.md` §4(b) used for its own render.

## 4. Live demonstration (c) — bounded ripple predict-then-verify accuracy, real numbers, both the successes and the honest failure

**The registered accuracy sweep** (`test_ripple_predict_then_verify_against_
real_run_rules`, N=6 complete graphs, coarse weights, strong ±3.0
perturbations, 20 real predict-then-verify trials — predict via
`predict_ripple` [confirmed non-mutating each time], THEN actually commit
the SAME evidence and run `run_rules()` to real convergence, compare):

```
ripple predict-then-verify: 20/20 exact full-network matches (100.0%)
```

**Extended sweep, run manually in this rung to characterise the boundary
(not gated as a pytest assertion beyond the 50% registered floor, reported
here as real measured numbers):**

| network | perturbation | trials | exact matches | rate |
|---|---|---|---|---|
| N=6, coarse weights | ±3.0 | 20 | 20 | 100.0% |
| N=8, fine weights | ±1.0 | 30 | 30 | 100.0% |
| N=10, coarse weights | ±0.5 | 30 | 30 | 100.0% |
| N=10, **fine** weights | ±3.0 | 30 | **28** | **93.3%** |

**Round-count distribution, confirming genuine multi-hop propagation is
being exercised (not trivially converging in round 1 every time):** across
40 N=6 draws, rounds ranged 1-4 (`[1×15, 2×17, 3×7, 1×1]`-shaped, printed
distribution: `1,1,...,1(x15),2,2,...,2(x17),3,3,...,3(x7),4`); the N=10
fine-weight sweep ranged 1-5 rounds. The predictor is genuinely simulating
propagation across several Gauss-Seidel sweeps, not degenerating to a
single-step check.

**The honest divergence, found, characterised, and pinned as a
deterministic regression test — `test_ripple_can_converge_to_a_different_
attractor_than_run_rules` (seed 9011, N=10, fine weights, probe concept
index 1, `new_h=-3.0`, reproduced deterministically 3/3 times while writing
this test):**

```
honest divergence case: predicted != actual on 3/10 nodes:
{4: (-1.0, 1.0), 7: (-1.0, 1.0), 9: (1.0, -1.0)} (predictor rounds=3)
```

**Confirmed this is a genuine different-attractor landing, not a predictor
bug**: the test re-evaluates `predict_current_target` (the SAME formula)
on the REAL committed outcome for every Concept and asserts it reproduces
itself exactly — i.e. the REAL outcome is independently confirmed to be a
genuine fixed point of the identical formula the predictor uses, and
separately `predict_ripple`'s own `converged=True` confirms the PREDICTED
state is also a genuine fixed point of its own sweep. Both are real,
independently self-consistent Hopfield attractors; the two mechanisms
(Python round-robin Gauss-Seidel vs. `run_rules()`'s own internal binding
order) landed in different ones on this specific near-tie-prone, strongly
perturbed draw — **exactly the PREREG's registered open question
(prediction 2), now answered concretely: it happens, it is rare on the
measured sample (2/90 ≈ 2.2% pooled across the four-condition sweep above,
concentrated entirely in the fine-grained/strong-perturbation condition,
0% in the other three conditions), and it is independently verifiable
(not silently wrong) because both landings are checkable fixed points of
the same formula.**

## 5. Live demonstration (d) — predicted frustration matches actual

`test_ripple_predicted_frustration_matches_actual_after_commit`:

```
predicted_frustration=4.0000 actual_frustration=4.0000
```

Exact match — expected, since `mt_frustration_given_state` is a
deterministic function of the state vector, and this draw's `predict_
ripple` state vector matched the real committed outcome exactly (per §4).

## 6. Sanity check — a converged network is a fixpoint of the SAME formula

`test_predict_current_target_is_a_noop_on_a_converged_network`: for a real
N=8 network relaxed via `run_rules(3000)`, every Concept's `predict_
current_target` (no override) exactly equals its own already-committed
`state` — confirms `target_state_term` really is reading the identical
formula `can_native_update_3state` converges to, not a divergent
reimplementation.

---

## 7. Migration sketch — what changes in the two blocked consumers (NOT built this rung, per the task's explicit scope)

**`domains/drive_curiosity.py::probe_via_what_if` (`:65-103`).** Replace:

```python
current_marginal = substrate.mt_mean_field_marginal(mt)
predicted_marginal = substrate.mt_mean_field_with_h_override(mt, concept, new_h)
```

with:

```python
result = can_counterfactual.predicted_info_gain(substrate, mt, concept, new_h, mode=mt_discrete_mode)
```

`predicted_info_gain` already returns `info_gain_total_change`/
`info_gain_max_node_change`/`predicted_flipped_count` in the SAME shape
`probe_via_what_if` currently builds by hand from the two marginal dicts —
the function body's `for nid, predicted_sig in predicted_marginal.items():`
loop (`:84-91`) becomes unnecessary, already done inside
`predicted_info_gain`. `find_ambivalent_nodes` (`:43-62`) is unaffected —
it only reads `Concept.state`, not the continuous marginal. **One real
design decision this migration would need to make, not resolved here**:
`probe_via_what_if` is currently mechanism-agnostic in its CALLER
(`run_curiosity`, `:106-123`) — a coordinated migration needs to decide
whether the discrete predictor REPLACES the continuous call unconditionally
or is gated by `Mt.discrete_mode` being set (a Concept-network Mt not yet
migrated to discrete mode has no `state`/`temperature` vocabulary the
native formula expects) — this is exactly the "consumer coherence across
shared Mts needs a coordinated pass" concern
`CAN_CONSUMER_MIGRATION_RESULTS.md` §1 row 4 already named for a different
pair of consumers, and applies here too.

**`domains/insight_seeking.py::predict_perturbation_impact` (`:69-134`).**
Replace the `mt_mean_field_with_h_override` call and the by-hand energy
field-correction (`:88-103`, itself a workaround for `mt_energy` reading
`h` from the LIVE graph attrs rather than the hypothetical) with:

```python
ripple = can_counterfactual.predict_ripple(substrate, mt, concept, new_h, mode=mt_discrete_mode)
predicted_marginal = ripple["predicted_state"]
predicted_energy = substrate.mt_energy(mt, predicted_marginal)      # already correct -- no field-correction hack needed
predicted_frustration = substrate.mt_frustration_given_state(mt, predicted_marginal)
```

**This migration is a strict SIMPLIFICATION of the current code, not just
a mechanism swap**: `predict_perturbation_impact`'s own `:88-103` hand-
written energy correction exists ONLY because `mt_energy` reads `h` off
the live graph attrs while the marginal was computed under a hypothetical
override the graph never saw — the native predictor has no such gap, because
`predicted_state` already reflects the override consistently at every node
that reacted to it (including the probed node itself), so `mt_energy` can
be called on it directly with no correction term. `find_hot_nodes`
(`:37-66`) reads `node_local_frustration` which assumes the network is
ALREADY relaxed (`seek_insights` calls `mt_relax_to_marginal` first,
`:157`) — a coordinated migration would need `find_hot_nodes` to read
`state` (already the discrete mechanism's own equilibrium if `run_rules()`
was used to reach it) rather than call a continuous relax function; this
rung does not resolve whether `find_hot_nodes` itself needs a native
twin of `node_local_frustration` (a genuinely separate, unbuilt piece —
`node_local_frustration`'s own per-Concept contribution formula was not
investigated in this rung, named here as the ONE additional piece a full
migration would need beyond what `can_counterfactual.py` already provides).

**Both sketches are UNBUILT** — `git diff --stat main -- domains/drive_
curiosity.py domains/insight_seeking.py domains/insight_propagation.py`
is empty, confirmed.

---

## 8. Regression

**The task's own required file, byte-unchanged, still green:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_native_reimplementation.py -q
11 passed
```

**New file:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_counterfactual.py -q -s
6 passed
```

**Full scoped CAN + consumer regression, one run, 157/157 passed:**
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_self_improvement_loop.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_can_crossover_point.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_native_migration.py tests/test_can_counterfactual.py -q
157 passed in 9.38s
```

Per-file: every one of the 16 pre-existing files reports the SAME pass
count as `CAN_CONSUMER_MIGRATION_RESULTS.md` §3's own table (151 total
there); `tests/test_can_counterfactual.py` is the one new file (6 tests).
**No paired failing-node-id lists to report** — zero failures anywhere,
before or after.

**No Rust build was needed or run** — `git diff --stat main -- '*.rs'` is
empty; zero `.rs` files touched anywhere in this branch, confirmed.

**Full boot regression** (`load_all_seeds` on a fresh `WorldAdapter`):
identical **8 pre-existing failures** to the documented baseline
(`acoustic_cue_vocab`, `character_tom`, `reading_constructions`,
`conceptual_categories`, `cue_investigator`, `named_compound_heads`,
`reading_skeleton`, `vision_change`, all `ValueError: seed node missing
local_id`), **0 rules_skipped** — unrelated to this rung, matching every
prior rung in this arc.

**Sibling-worktree collision check.** Two sibling worktrees confirmed
running concurrently at branch time (`can-hebbian-materialization` @
299ace3, `can-synchronous-update-fix` @ b9f4429). This rung touches
`domains/can_counterfactual.py` (new), `tests/test_can_counterfactual.py`
(new), and two new docs — `seeds/can_native_reimplementation.json` and
`can_ops.rs` are READ-ONLY in this rung (`git diff --stat main --
'seeds/can_native_reimplementation.json' 'runners/dsl/src/can_ops.rs'` is
empty), so no collision is possible with whatever either sibling does to
those files.

---

## 9. What this rung does NOT establish

1. **`drive_curiosity.py`/`insight_seeking.py`/`insight_propagation.py`
   are NOT migrated** — explicitly out of scope; §7 is a sketch, not a
   build. `git diff --stat` on all three is empty.
2. **The bounded ripple predictor is not exact in general** — §4 measured
   a real, reproducible 2/90 (pooled) divergence rate concentrated in
   fine-grained/strongly-perturbed networks, where the Python round-robin
   Gauss-Seidel visitation order can land in a different (but equally
   valid) Hopfield attractor than `run_rules()`'s own internal binding
   order. This is a genuine property of asynchronous update order-
   dependence in multi-attractor networks, not a bug — but it means the
   predictor's output should be read as "the network's most likely new
   equilibrium under this perturbation," not as a guaranteed-identical
   simulation of what `run_rules()` would produce. A caller that needs a
   GUARANTEED match would need to either (a) accept the residual, sized
   here at ~2-7% depending on network conditions, or (b) match `run_
   rules()`'s own internal binding order exactly, which this rung did not
   attempt (the internal order is an engine implementation detail, not
   part of the documented cold-path contract beyond "one progressing
   binding per rule per pass, committed immediately").
3. **`node_local_frustration`'s own native twin was not investigated** —
   `find_hot_nodes` (`insight_seeking.py:37-66`) is not covered by this
   rung's predictor at all; a full migration of that consumer needs a
   separate, unbuilt piece (named in §7, not sized).
4. **`max_rounds` is a registered bound (12-30 across this rung's own
   tests), not derived from any convergence proof for the bounded
   predictor itself** — Hopfield's classical guarantee is for `run_
   rules()`'s OWN asynchronous update, not for this module's independent
   Gauss-Seidel sweep; this rung's own measured round counts (1-5 observed
   across all sweeps) suggest the bound is generous in practice on
   networks this size, but no bound is PROVEN for arbitrary N or coupling
   density.
5. **Nothing in this rung investigated `Mt.discrete_mode`-gating or
   backward compatibility with Mts still running the continuous
   mechanism** — the migration sketch (§7) names this as an open decision
   the coordinated final migration rung would need to make, consistent
   with `CAN_CONSUMER_MIGRATION_RESULTS.md` §1 row 4's own "coordinated
   pass, not piecemeal function swaps" finding.
6. **The Hebbian-materialization and decay/identity-dynamics sibling
   rungs are untouched and uninvestigated here** — this rung's own file
   footprint is disjoint from both by construction (§8).
7. **Whether any of this reflects real human counterfactual/what-if
   cognition remains exactly as open as every prior rung in this arc left
   it** — this document is about this SUBSTRATE's own best-fitted
   mechanism.

---

## 10. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-counterfactual-predictor
git log --oneline -1 main   # 299ace3, verified before branching

# The new predictor's own live demonstrations (-s for printed numbers)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_counterfactual.py -q -s

# The task's own required unchanged file
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py -q

# Full scoped CAN + consumer regression
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_ops.py tests/test_can_migration.py tests/test_identity_field.py \
  tests/test_insight_seeking.py tests/test_self_improvement_loop.py \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_insight_detection.py tests/test_insight_propagation.py \
  tests/test_drive_curiosity.py tests/test_sparseness_signal.py \
  tests/test_can_native_reimplementation.py tests/test_evidence_axis_infer.py \
  tests/test_can_crossover_point.py tests/test_causal_attitude_networks.py \
  tests/test_bigville_can_native_migration.py tests/test_can_counterfactual.py -q

# Zero Rust touched
git diff --stat main -- '*.rs'

# Full boot regression (pre-existing failures only, unrelated to this rung)
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
a = WorldAdapter(seeds=())
rep = load_all_seeds(a)
print('failed:', len(rep['failed']), 'rules_skipped:', len(rep['rules_skipped']))
for f in rep['failed']: print(' ', f)
"
```
