# Does the native discrete-async CAN solver find GOOD solutions, or just A
stable one? — RESULTS

Prereg: `CAN_SOLVER_TRACTABILITY_PREREG.md`, same worktree/branch, base
`main @ 19fdddf` ("Merge mac-fac-a8: epick applicability-gate precompute,
closes the A1-A9 audit, GO"), verified via `git log --oneline -1 main`
before branching. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-solver-tractability`,
branch `can-solver-tractability`.

**Verdict, up front: GO — real, measured local-minimum risk, confirmed on
both a deliberately adversarial synthetic network AND, less frequently but
still really, on real deployed Bigville residents. Built the smallest
correctness-preserving fix the measurement justifies:
`multi_start_settle_and_pick_best` (`domains/can_native_orchestration.py`),
zero new Rust, the proven-convergent discrete-async update rule itself
never touched.** Bethe/loopy-BP is investigated concretely and found
buildable in the SAME shape (ordinary graph rules) but at genuinely larger
seed-authoring complexity than the discrete update — sized, not built, per
the task's own priority ordering. The low-rank/shared-generator hypothesis
is CONFIRMED on real data — not merely plausible: Bigville's real
100-resident coupling matrix has effective rank ≈1.98 out of 5, and every
edge's deviation correlates at exactly 1.0 with its own declared nuance
driver. Treewidth is measured exactly on both real graphs: Bigville's real
per-resident template is treewidth **2** (sparse, tractable); the N=16
complete graph used to stress-test local-minimum risk is treewidth **15**
(worst case, by construction) — the theory doc's own abstract §6.2 finding,
now confirmed on data that did not exist when it was written.

---

## 0. What was measured, on what, and why (method)

Four measurements, one script
(`scripts/can_solver_tractability_measure.py`), run once, output captured
verbatim in `scripts/can_solver_tractability_measure_results.json`. Every
number below is read directly from that run's stdout/JSON, not
hand-computed or simulated.

- **Measurement 1 (load-bearing)**: local-minimum risk, multi-start,
  same network, two conditions (§1).
- **Measurement 2**: exact treewidth, brute-force, on the two real graphs
  Measurement 1 itself uses (§2).
- **Measurement 3**: low-rank/shared-generator, SVD on the real 100-resident
  `true_j` coupling matrix (§3).
- **Investigation (not a measurement)**: Bethe/loopy-BP, concrete design
  analysis against this substrate's own Term vocabulary (§4).

---

## 1. Local-minimum risk — the load-bearing measurement, real numbers

### 1.1 Condition A (N=16 complete graph, random-sign coupling — frustrated/
dense, adversarial stress case)

30 draws (15 coarse-vocab + 15 fine-vocab), `K=20` random-init starts per
draw, 3-state discrete mode, using the SAME unmodified `can_native_update_
3state` rule (`seeds/can_native_reimplementation.json`, byte-unchanged —
confirmed by `git diff --stat main -- '*.json'` showing this file absent
from the diff):

```
median best_frustration=34.7500  median spread=9.0000  median_relative_spread=0.2590
median frac_at_best=0.3000       median n_distinct_final_states=8.5
all 30 draws fully converged (no run hit the 3000-step cap): True
```

Individual draws range from spread=9 to spread=13 among the first three
printed rows alone (`n_distinct_final_states` up to 16 out of 20 starts on
one draw — every single start landing on a DIFFERENT final configuration).
**Every draw converged** (the discrete-async mechanism's own proven
guarantee held on all 600 individual settle calls, 30 draws × 20 starts) —
this measurement is entirely about the QUALITY of what different starts
converge TO, never about whether they converge at all.

### 1.2 Condition B (real Bigville residents — sparse, deployed case)

30 real residents (10 lowest-`resolution_bins`, 10 highest, 10 random-
middle — a stratified, not cherry-picked, sample), `K=20` starts per
resident, real scenario evidence applied (`SCENARIO_EVIDENCE`,
`worlds/bigville_can_beliefs.py`, unmodified):

```
median best_frustration=2.0000  median spread=0.0000  median_relative_spread=0.0000
median frac_at_best=1.0000      median n_distinct_final_states=2.0
all 30 residents fully converged: True
```

**Read past the median, because it hides a real, structured minority
result** — the prereg's own §1.4 registered this exact possibility
("condition A shows real risk but condition B... negligible... in which
case the honest finding is X"), and here the honest finding is
sharper than either extreme: **14 of 30 real residents (46.7%) show
NONZERO spread**, not a rounding artifact — the raw rows include spread=2.0
at `frac_at_best` as low as 0.65-0.9 on multiple real residents (e.g.
resident #48: `best=2.0 worst=4.0 spread=2.0 n_distinct=7 frac_at_best=0.65`).
Stratified by the resident's own real `resolution_bins` trait:

| stratum | n | frac w/ nonzero spread | mean spread | mean relative spread |
|---|---:|---:|---:|---:|
| low bins (≤4, coarse) | 16 | 56.3% | 1.125 | 0.562 |
| mid bins (5-7) | 4 | 0.0% | 0.000 | 0.000 |
| high bins (≥8, fine) | 10 | 50.0% | 0.443 | 0.323 |
| **all 30** | 30 | **46.7%** | **0.748** | **0.408** |

**This is a real, structured finding, not noise**: local-minimum risk is
NOT confined to the adversarial N=16 synthetic stress case — it is present,
at real and non-trivial magnitude, in close to half of Bigville's actual,
already-deployed, currently-tested resident networks, on a graph this
rung's own Measurement 2 confirms has treewidth only 2. **A sparse,
near-tree topology does not, on this real data, guarantee a benign local-
minimum landscape** — a genuinely useful, non-obvious correction to the
naive expectation that "sparse ⟹ safe" this rung's own §1.3 P2 prediction
half-held (the MEDIAN resident is unaffected) and half-missed (a real,
sizeable minority is not).

### 1.3 GO/NO-GO, against the criteria registered in the PREREG before
this measurement ran

```
median_relative_spread > 0.05: 0.2590 -> True
median_frac_at_best    < 0.80: 0.3000 -> True
median_n_distinct_final_states > 1: 8.5 -> True
GO (condition A): True
```

All three registered bars clear on condition A, and condition B's own
46.7%-of-real-residents finding (§1.2) makes the case for building the fix
STRONGER, not weaker, than the prereg's own conservative framing
anticipated — this is not a purely synthetic/adversarial concern.

---

## 2. Treewidth — exact, brute-force, on the two real graphs Measurement 1
actually uses

```
Bigville structural template: nodes=5 edges=5 exact_treewidth=2
Complete-graph treewidth check (brute force, small N): {4: 3, 6: 5, 8: 7} (expect n-1 for each)
N=16 complete graph: exact_treewidth=15 (closed-form N-1, confirmed by the brute-force pattern for n=4,6,8 above)
```

Brute-force minimum induced width over ALL elimination orderings (correct,
not a heuristic estimate — tractable at these sizes: 5! and, for the
closed-form cross-check, 4!/6!/8! orderings). Bigville's real per-resident
topology (`trust_mayor`/`claim_credible`/`world_safe`/`self_worth`/
`debtor_trustworthy`, `STRUCTURAL_EDGES`) is a "near-tree-plus-one-triangle"
graph — treewidth 2, confirming the visual read (one 3-cycle:
`trust_mayor`-`claim_credible`-`debtor_trustworthy`, plus a
`trust_mayor`-`world_safe`-`self_worth` pendant path) exactly, not just
approximately. **This directly answers `CAN_SOLVER_THEORETICAL_LIMITS_
RESEARCH.md` §6.2's own open question on data that did not exist when it
was written**: that document could only observe that this project's TESTED
graphs (complete, N=4/8/16) were worst-case by construction, and
speculated a real graph-construction discipline was needed to ever reach
bounded treewidth. **The real, deployed Bigville template already has
bounded, small treewidth (2) — not by any deliberate treewidth-discipline
design, but as an incidental consequence of modelling five distinct belief
topics with a handful of named, real structural relationships** (each
`STRUCTURAL_EDGES` entry traces to an already-wired Bigville mechanic,
`worlds/bigville_can_beliefs.py:20-31`), which is itself a useful, honest
finding: **junction-tree-exact inference is not "unreachable by
construction" for the graphs this project actually deploys — it was never
attempted, but nothing about their real topology rules it out.** This
measurement does not build a junction-tree solver (out of scope, not sized
here) — it only corrects the "unreachable by construction" framing for the
one real template checked.

---

## 3. Low-rank/shared-generator — confirmed on real data, not merely
plausible

`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §6.4's own precise, falsifiable
condition: does compression correspond to a SMALL NUMBER OF SHARED LATENT
GENERATORS (true low rank — Hopfield/TAP tractability applies), or merely
to many edges landing on the same few numeric VALUES (value-alphabet
compression — it does not)? Measured on the real, unmodified, 100-resident
`true_j` coupling matrix (`worlds/bigville_can_beliefs.py::true_edge_j`,
read-only):

```
residents=100 edges=5
singular values (true_j, mean-centered): [1.0554, 0.8618, 0.0, 0.0, 0.0]
fraction variance explained per component: [0.6, 0.4, 0.0, 0.0, 0.0]
effective rank (participation ratio (sum s)^2/sum s^2): 1.980
components needed for 95% variance: 2 of 5
distinct quantized_j values across all 500 (resident,edge) cells: 17
per-edge correlation with its OWN nuance driver: [
  ('trust_mayor-claim_credible', 'mood_bias', 1.0),
  ('trust_mayor-world_safe', 'w_supergraph', 1.0),
  ('world_safe-self_worth', 'mood_bias', 1.0),
  ('claim_credible-debtor_trustworthy', 'w_supergraph', 1.0),
  ('trust_mayor-debtor_trustworthy', 'mood_bias', 1.0)]
```

**Both singular values beyond the top 2 are EXACTLY zero (to float
precision), not merely small** — the real coupling-deviation matrix is
literally rank-2, and the correlation of every single edge's deviation with
its OWN declared nuance driver (`mood_bias` or `w_supergraph`) is exactly
`1.0` for all five edges. **This is the cleanest possible confirmation of
§6.4's "genuine shared latent generators" condition, not the "value-
alphabet compression" alternative it warned against**: the real reason
Bigville's coupling matrix compresses is that only TWO underlying scalar
resident traits (`mood_bias`, `w_supergraph`) drive ALL of the variation
across five structural edges — exactly the Hopfield-style `J_ij = Σ_μ w_μ ·
f_μ(i) · f_μ(j)` shape §6.4 named as the condition the low-rank/TAP
tractability result actually needs, confirmed by direct SVD, not asserted
by analogy. The SEPARATE 17-distinct-quantized-value fact (§6.4's OTHER,
weaker candidate explanation) is also real but is now known to be a
CONSEQUENCE of the same rank-2 structure passing through quantization, not
an independent or competing explanation — both are true, and now there is a
real, checked reason WHY.

**Honest limit, stated precisely, matching §6.4's own scope**: this
confirms the STRUCTURAL CONDITION the low-rank/TAP tractability result
needs exists in real data — it does NOT build a `CausalLinkageShape`
compressor, does not test whether this project's existing `ShapeDecode`
codebook machinery currently recognizes this rank-2 structure (a SEPARATE,
unbuilt question, exactly as the PREREG named), and is a fact about ONE
real template (Bigville's), not a general claim that every `causal_
influence` network this project could ever build will be low rank — an
adversarially or independently hand-authored network need not share this
property.

---

## 4. Bethe/loopy-BP — concrete design investigation, not a build

**The question this rung answers**: is a loopy-BP update expressible as an
ordinary graph Rule, the SAME way the discrete-async update already is
(reusing `run_rules`/`run_rules_scoped`'s existing fixpoint), or does it
need real new Rust machinery?

**Confirmed, concretely, against this substrate's own real Term
vocabulary**: a pairwise-Ising BP message `μ_{i→j}(σ_j) = Σ_{σ_i}
ψ_{ij}(σ_i,σ_j)·φ_i(σ_i)·Π_{k∈N(i)\j} μ_{k→i}(σ_i)` is, structurally:

1. **A per-directed-edge, per-VALUE quantity** — for this substrate's own
   native 3-state vocabulary, each directed `causal_influence` edge would
   need THREE stored scalars (one message component per σ_j ∈
   {-1,0,+1}), not the single `weight` attr the discrete update reads
   today. This is a real, first-order representational change: the
   discrete update needs 1 float/edge; BP needs 3.
2. **The "leave-one-out" product** (`Π_{k∈N(i)\j}`) is expressible with
   EXISTING Terms, confirmed by direct composition, not assumed: `Prod
   {source: Filter{source: Edges(i,"causal_influence"), var_name:"e",
   predicate: Not(Eq(Nth(Var("e"),2), Lit(j)))}, var_name:"e", value:
   <message-component-read>}` — `Prod` (`term.rs:83`) and `Filter`
   (`term.rs:2931`, already used across ≥5 seeds, `seeds/acoustic_cue_
   vocab.json`/`seeds/affordance_basis.json`/etc.) compose directly; no new
   Term is needed for the exclusion itself.
3. **Enumerating σ_i's three values inside the sum** is very likely
   expressible via `Sum{source: Lit([-1.0,0.0,1.0]), var_name:"si", value:
   ...}` — `Sum`/`Prod`/`Fold`'s shared evaluator loop
   (`rewrite.rs`/`term.rs:5741` region) iterates any `Value` that supports
   `.snapshot()`, which list-shaped `Lit` values are expected to support —
   **not independently traced to a worked seed example in this pass**,
   named honestly as "very likely, not confirmed" rather than assumed,
   matching this arc's own standing practice for exactly this class of
   claim (`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md` §3.4's identical
   honesty convention for its own open Term-composition question).

**The concrete finding, stated without hedging**: **structurally, YES —
Bethe/loopy-BP is expressible as an ordinary graph Rule using ONLY
existing Terms (`Prod`, `Filter`, `Sum`, `EdgeAttr`, `IfThenElse`), the
SAME `run_rules`/`run_rules_scoped` fixpoint every native CAN rule already
uses, zero new Rust Term variants required by this analysis.** But this is
NOT a "small change" the way the discrete update's own `IfThenElse`
threshold rule was — the rule body is genuinely larger (three stored
message components per directed edge instead of one state scalar per node;
a nested Sum-over-3-values-of-Prod-over-excluded-neighbours structure,
roughly the complexity class of `can_counterfactual.py`'s own multi-step
Term assembly, not a one-line extension of `can_native_update_3state`) and
carries the SAME convergence caveat the theory doc already named (§4.4:
Bethe/BP is known to lose its own solution in the frustrated-plus-field,
low-temperature regime — an open problem in the literature itself, not
something this investigation resolves). **Recommendation, honestly sized**:
buildable in a follow-on rung at roughly the design/engineering weight of
`CAN_COUNTERFACTUAL_PREDICTOR_RESULTS.md`'s own build (a genuinely new
Term-tree assembly module, not a one-rule patch) — not attempted in this
rung, per the task's own explicit "investigate, report precisely, don't
build" instruction for this item, and because Measurement 1's own real
result (§1) justified a smaller, immediately buildable fix instead (§5).

---

## 5. What was built — `multi_start_settle_and_pick_best`

**Location**: `domains/can_native_orchestration.py` (the existing,
house-compliant precedent this whole module already establishes —
mechanical composition of existing primitives, zero decision-over-graph-
state in Python). Zero new Rust — confirmed:

```
$ git diff --stat main -- '*.rs'
(empty)
```

**Design, exactly as registered in the PREREG §5, built as registered**:

1. For `K` starts (default 20, matching this arc's own `N_RESTARTS`/
   `N_DRAWS` convention): mechanically draw a random initial `state` per
   Concept — the SAME class of operation as `scripts/bigville_can_
   integration_demo.py::multi_start_basin_count`'s own pre-existing
   `rng.choice(...)` re-seed loop.
2. Call `scoped_settle` — **the existing, UNMODIFIED, already-proven-
   convergent native rule, never touched by this change.** Confirmed by
   `git diff --stat main -- '*.json'` being empty: `seeds/can_native_
   reimplementation.json` (the file containing `can_native_update_3state`/
   `_2state`'s own rule body) is byte-identical to `main`. This preserves
   the Lyapunov/empirical convergence guarantee EXACTLY, per the task's
   explicit instruction and mirroring `CAN_IDENTITY_FEEDBACK_RESULTS.md`'s
   own care in protecting this exact guarantee — this build adds an OUTER
   selection layer around K independent, individually-unmodified runs.
3. Mints one `CanMultiStartCandidate` node per trial, holding its
   converged `frustration` (mechanically copied from `mt_frustration_
   given_state`, a pure computation) and per-Concept final `state` values
   as attrs.
4. **The SELECTION — which trial's state gets committed — is made by the
   `Argmin` Term** (`term.rs:382`, already used across ≥10 other seeds,
   e.g. `seeds/grid_navigation.json`, `seeds/arc_decompose.json`) over
   `Neighbours(session, "ms_candidate")` scored by `Attr(cand,
   "frustration")` — a graph-native decision, not a Python `if`/`min()`,
   matching `CLAUDE.md`'s standing rule precisely.
5. Committing the winner's stored state back onto the real Concepts is
   mechanical translation (read the winning node's attrs, `set_attr` them
   onto the already-decided winner's target Concepts) — no decision left
   in Python.

**One thing found and fixed while building, reported honestly (matching
this arc's own standing self-correction practice)**: the new
`CanMultiStartSession`/`CanMultiStartCandidate` edge types
(`ms_session`, `ms_candidate`) were initially rejected by Γ
(`InadmissibleEdge: type 'ms_session' not in vocabulary`) — no production
existed for them. Fixed with `install_multi_start_productions`, a small,
explicit, mechanically-registered Γ production pair (Microtheory→
CanMultiStartSession, CanMultiStartSession→CanMultiStartCandidate),
mirroring `worlds/bigville_can_beliefs.py::install_productions`'s own
precedent — **a Γ production, not a bypass of the admissibility check**,
matching `CLAUDE.md`'s SHAPES-NOT-NUMBERS discipline (a set of allowed
moves is a Γ production, never a filter worked around in Python).

### 5.1 Real before/after numbers, on the same networks Measurement 1 used

**Frustrated N=16 network (seed=42, coarse)**:
```
baseline (single zero-init settle) frustration=36.0000
multi-start (K=20) winner frustration=34.0000
```

**Winner-selection correctness, independently re-checked (not merely
trusting the Term's own return value)** — seed=123, K=15:
```
all 15 candidate frustrations: [36.0, 36.0, 36.0, 36.0, 36.0, 36.0, 36.0, 38.0, 38.0, 38.0, 38.0, 38.0, 42.0, 44.0, 44.0]
Argmin-selected winner frustration: 36.0000 true_min=36.0000
```

**Real Bigville resident #7** (well-behaved, no exception, no regression
even when the single-settle baseline was already optimal):
```
Bigville resident #7 baseline_frustration=0.0000 multi_start_frustration=0.0000
```

**Two-Mt isolation** (the standing check every native rung in this arc
runs, `CAN_FINAL_MIGRATION_RESULTS.md` §0's own hazard): confirmed
byte-unchanged sibling-Mt state after running multi-start on an unrelated
Mt in the same graph (`test_two_mt_isolation_holds_for_multi_start`,
passing).

---

## 6. Regression

No Rust touched (`git diff --stat main -- '*.rs'` empty) — Rust build/
`cargo test` not run, per house discipline point 3 ("likely needed only if
you build a real loopy-BP mechanism," which this rung did not build).

**New test file, with printed real numbers**:
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_solver_tractability.py -q -s
5 passed in 0.28s
```

**Task-named + broader CAN regression set, one run, 117/117 passed**:
```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py tests/test_can_crossover_point.py \
  tests/test_bigville_can_native_migration.py tests/test_can_belief_quantization.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_solver_tractability.py \
  tests/test_bigville_can_integration.py tests/test_can_migration.py \
  tests/test_can_final_migration.py tests/test_can_identity_feedback.py \
  tests/test_can_decay_identity.py tests/test_can_hebbian_materialization.py \
  -q
117 passed in 9.17s
```

Per-file: `test_can_native_reimplementation.py` 11,
`test_can_crossover_point.py` 5, `test_bigville_can_native_migration.py` 4,
`test_can_belief_quantization.py` 11, `test_causal_attitude_networks.py`
11, `test_can_ops.py` 12, `test_can_solver_tractability.py` 5 (new, this
rung), `test_bigville_can_integration.py` 12, `test_can_migration.py` 8,
`test_can_final_migration.py` 10, `test_can_identity_feedback.py` 8,
`test_can_decay_identity.py` 8, `test_can_hebbian_materialization.py` 12.
**Zero failures, before or after** — the 112 pre-existing tests are
unaffected (only `domains/can_native_orchestration.py` was modified, and
only by ADDING two new functions; every pre-existing function in that file
is byte-unchanged).

`git status --short`:
```
 M domains/can_native_orchestration.py
?? docs/research/engine_substrate/CAN_SOLVER_TRACTABILITY_PREREG.md
?? docs/research/engine_substrate/CAN_SOLVER_TRACTABILITY_RESULTS.md
?? scripts/can_solver_tractability_measure.py
?? scripts/can_solver_tractability_measure_results.json
?? tests/test_can_solver_tractability.py
```

---

## 7. What this rung does NOT establish

1. **`multi_start_settle_and_pick_best` widens the search, it does not
   deepen the guarantee** — it can only find the best among the `K`
   basins its random starts happen to land in; it is not a proof of global
   optimality and does not claim to be. A pathological network could still
   have its true global optimum missed by all `K` starts (unmeasured —
   would require comparing against exact/exhaustive ground-state search,
   out of scope here and NP-hard in general per the theory doc's own §3).
2. **The Bethe/loopy-BP investigation (§4) is a design analysis, not a
   build.** It does not resolve whether Bethe/BP, if built, would find
   BETTER solutions than multi-start-and-pick-best on this project's own
   frustrated networks, nor does it resolve the theory doc's own §4.4
   caveat (Bethe/BP's own known failure regime). The "very likely, not
   confirmed" Sum-over-literal-list claim (§4 point 3) was not traced to a
   worked example.
3. **The low-rank finding (§3) is specific to Bigville's own template-
   driven construction.** It does not establish that all `causal_
   influence` networks this project could build are low rank, and it does
   NOT establish that this project's existing `ShapeDecode`/codebook
   machinery currently exploits this structure — a separate, unbuilt
   question.
4. **The treewidth finding (§2) is exact for the two graphs measured.** It
   corrects "unreachable by construction" for Bigville's real template
   specifically; it does not build a junction-tree solver, and it says
   nothing about the treewidth of any OTHER real or hypothetical `causal_
   influence` network this project might construct in the future.
5. **Condition B's 46.7%-of-residents finding (§1.2) is measured on a
   stratified-but-not-exhaustive 30-resident sample** (of 100 real
   residents) — a full-population sweep (all 100) was not run in this rung;
   the stratification (10 lo/10 hi/10 random-mid) was chosen to avoid bias
   toward either extreme of the `resolution_bins` trait, not to guarantee
   the exact 46.7% figure would hold at n=100.
6. **`K=20` and the two-condition design were fixed in the PREREG before
   measuring** — this rung did not sweep `K` itself; whether `K=20` is the
   right budget for production use (versus, say, `K=5` for a cheaper,
   still-mostly-effective wrapper) is real, un-sized follow-on work.
7. **Whether any of this reflects real human belief-network, social-
   population, or causal-reasoning dynamics** remains exactly as open as
   every prior rung in this arc left it — this document is about this
   SUBSTRATE's own best-fitted mechanism's actual solution quality, not a
   new claim about cognition.

---

## 8. Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-solver-tractability
git log --oneline -1 main   # 19fdddf, verified before branching

# The four measurements (treewidth, low-rank, local-minimum risk conditions A+B)
PYTHONPATH=".:runners/dsl/python" python3 scripts/can_solver_tractability_measure.py
cat scripts/can_solver_tractability_measure_results.json

# multi_start_settle_and_pick_best, with printed real before/after numbers
PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_solver_tractability.py -q -s

# Task-named + broader CAN regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py tests/test_can_crossover_point.py \
  tests/test_bigville_can_native_migration.py tests/test_can_belief_quantization.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_solver_tractability.py \
  tests/test_bigville_can_integration.py tests/test_can_migration.py \
  tests/test_can_final_migration.py tests/test_can_identity_feedback.py \
  tests/test_can_decay_identity.py tests/test_can_hebbian_materialization.py \
  -q

# Zero Rust touched
git diff --stat main -- '*.rs'
```
