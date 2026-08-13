# Exact junction-tree inference for low-treewidth CAN networks — RESULTS

Prereg: `CAN_JUNCTION_TREE_PREREG.md`, same worktree/branch, base
`main @ 76b8aea`, verified via `git log --oneline -1 main` before branching.
Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-junction-tree`,
branch `can-junction-tree`.

**Verdict, up front: GO.** Built a real, reusable treewidth
checker/bound-finder (`domains/graph_treewidth.py`), real junction-tree
construction + exact min-sum message passing
(`domains/can_junction_tree.py`), and wired them as a genuinely new,
explicit opt-in toolbox entrypoint (`junction_tree_exact_settle`) —
**exact global-minimum-energy inference**, not a widened heuristic search.
Proven correct on real Bigville residents against literal brute-force
enumeration (5/5 exact matches, float-tight), cross-checked against the
LIVE Rust `substrate.mt_energy`, shown to honestly refuse (no mutation, no
exponential attempt, sub-2ms) on the genuinely high-treewidth N=16 stress
case, and shown to find a strictly better (lower-energy) state than
`multi_start_settle_and_pick_best` on a real-cycle-topology network where
both tools apply. Zero new Rust. `domains/can_native_orchestration.py` was
not touched at all (collision-avoidance design decision, §5). 132/132
regression tests pass (117 pre-existing + 15 new), zero pre-existing test
touched.

---

## 0. What was built, where

Three new files, nothing else touched:

- `domains/graph_treewidth.py` — reusable, CAN-agnostic treewidth
  computation + elimination-tree construction.
- `domains/can_junction_tree.py` — CAN-specific network extraction,
  the min-sum message-passing algorithm, the toolbox entrypoint
  (`junction_tree_exact_settle`), and the brute-force ground-truth
  function used for the correctness proof.
- `tests/test_can_junction_tree.py` — 15 new tests, all with printed real
  numbers (`pytest -s`).

```
$ git status --short
?? docs/research/engine_substrate/CAN_JUNCTION_TREE_PREREG.md
?? domains/can_junction_tree.py
?? domains/graph_treewidth.py
?? tests/test_can_junction_tree.py

$ git diff --stat main -- '*.rs'
(empty)

$ git diff --stat main -- domains/can_native_orchestration.py
(empty)
```

---

## 1. Was the prior rung's treewidth code reusable? No — extracted and
generalized

`scripts/can_solver_tractability_measure.py::exact_treewidth` (read in
full before writing anything) was **one-off script code**: a free
function defined inside a single-purpose measurement script, never
imported by any other file in the tree (confirmed by grep), with no
upper-bound path for graphs too large to brute force — its own N=16 case
was handled by a hand-written closed-form `N-1` shortcut written directly
in the script, not by the function generalizing to that case. `domains/
graph_treewidth.py::exact_treewidth` is the SAME branch-and-bound
algorithm (identical pruning shape), now:

- importable/reusable by any caller, not script-local;
- gated by an explicit `max_exact_n` parameter (default 10) instead of
  being silently left to hang on a graph too large to enumerate;
- paired with a genuinely new function, `min_fill_upper_bound`, that the
  original script never had — a fast, ALWAYS-runs heuristic upper bound
  for exactly the graphs `exact_treewidth` now honestly refuses.

---

## 2. Treewidth-bound strategy — exact vs heuristic, timed

**Re-derivation, confirming the reused algorithm reproduces the prior
rung's own measured numbers exactly:**

```
Bigville structural template exact_treewidth=2 (CAN_SOLVER_TRACTABILITY_RESULTS.md sec2 measured 2)
N=16 complete graph: exact_treewidth refused (n>max_exact_n), min_fill_upper_bound=15
  (CAN_SOLVER_TRACTABILITY_RESULTS.md sec2's own closed-form/brute-force cross-check found the true value is 15)
```

**The exact-vs-heuristic cutover, actually timed (not merely asserted) —
this is the "what bound is practical to compute exactly vs needs a
heuristic" investigation the task named**:

```
n=8  (sparse, 16 edges)   exact_treewidth=4  time=0.051s
n=9  (sparse, 18 edges)   exact_treewidth=4  time=0.453s
n=10 (sparse, 20 edges)   exact_treewidth=4  time=5.065s
n=9  complete (worst case, no pruning benefit)  exact_treewidth=8  time=0.467s
n=10 complete (worst case, no pruning benefit)  exact_treewidth=9  time=5.121s
```

`n!` permutations dominate; the branch-and-bound pruning helps a lot on
sparse graphs that admit an early good bound, but the WORST case (complete
graph — no elimination ordering is ever better than any other, so pruning
never fires) is what actually bounds runtime, and it lands at ~5s for
`n=10`. **`max_exact_n=10` (the module's default) is chosen on this
measured worst-case timing**: `n=11` would be ~11× slower (≈56s, per the
`n!` growth rate observed between 9 and 10) — uncomfortable as a default
for a function a caller might invoke synchronously. Every REAL network
this project has measured so far (Bigville's 5-node template) sits
comfortably inside this cap with a wide margin (5 vs 10).

`min_fill_upper_bound` always runs regardless of size — confirmed on the
N=16 case above (15, matching the already-known-exact value, though the
tool honestly reports it as a heuristic upper bound rather than claiming
exactness it didn't compute, since `16 > max_exact_n`).

`treewidth_bound_check` (the caller-facing composition of both):

```
bound-check: Bigville within_bound=True (tw=2), N=16 within_bound=False (tw=15, heuristic)
```

---

## 3. Junction-tree construction and message passing — the algorithm

Standard elimination-tree construction (`build_elimination_triangulation`,
`domains/graph_treewidth.py`): one bag per node (`{v} ∪ v's still-live
neighbours at elimination time`), parent = the first later-eliminated
neighbour. Message passing (`junction_tree_map`,
`domains/can_junction_tree.py`) is min-sum (minimizing the SAME
`H(σ) = -Σ h_i σ_i - Σ_{i<j} J_ij σ_i σ_j` energy `can_ops.rs::mt_energy`
already defines, per the PREREG §1 registered target — NOT
`mt_frustration_given_state`, which omits the field terms and is used
elsewhere in this arc only as a cross-candidate comparison metric, never
as the network's actual energy): one leaf-to-root sweep computing, per
bag, the best achievable energy for every possible assignment to its
separator with its parent (folding in every child's already-computed
message), then one root-to-leaf backtrack reconstructing one
globally-optimal full state.

**Isolated algorithm correctness (no CAN/substrate involved at all)** —
two synthetic networks, checked against literal brute-force enumeration:

```
synthetic path graph (4 nodes, treewidth 1): junction-tree energy=-2.600000 brute-force energy=-2.600000
synthetic triangle+pendant (5 nodes, treewidth 2 -- Bigville's own real shape): jt=-4.084777 bf=-4.084777
```

Both exact, confirming the message-passing implementation itself is
correct before any CAN-specific extraction layer is involved.

---

## 4. THE correctness proof — real Bigville residents vs. literal
brute-force enumeration

**Registered pass criterion (PREREG §1): junction-tree's reported global
minimum energy must equal literal brute-force enumeration over ALL
`3^5=243` states, on ≥3 real resident networks.** Ran on 5
(`resident_index in {0, 1, 2, 17, 63}`, spanning the cast, not
cherry-picked):

```
resident #0:  junction-tree energy=-2.259000  brute-force (243-state enum) energy=-2.259000  mt_energy_confirmed(live Rust)=-2.259000
resident #1:  junction-tree energy=-2.825800  brute-force (243-state enum) energy=-2.825800  mt_energy_confirmed(live Rust)=-2.825800
resident #2:  junction-tree energy=-2.418200  brute-force (243-state enum) energy=-2.418200  mt_energy_confirmed(live Rust)=-2.418200
resident #17: junction-tree energy=-4.223550  brute-force (243-state enum) energy=-4.223550  mt_energy_confirmed(live Rust)=-4.223550
resident #63: junction-tree energy=-4.359800  brute-force (243-state enum) energy=-4.359800  mt_energy_confirmed(live Rust)=-4.359800
```

**5/5 exact matches, float-tight (`< 1e-6` for the JT-vs-brute-force
comparison in Python; `< 1e-4` for the cross-check against the live Rust
`substrate.mt_energy`, which round-trips through `f32` — the Python side
computes in `f64`).** The `mt_energy_confirmed` column is not a second
run of this module's own formula agreeing with itself — it is the
committed state read back and scored by the SAME `can_ops.rs::mt_energy`
function the real engine uses for every other CAN consumer in this
codebase, confirming this module's graph-extraction (`can_network_from_mt`)
correctly captures the same potentials the Rust engine holds, not merely
that this module's internal arithmetic is self-consistent.

Every one of these residents' networks was independently confirmed
treewidth 2 by `exact_treewidth` (not assumed from the structural-template
number — each resident's own instantiated network, with different
per-resident quantized weights, was measured) inside
`junction_tree_exact_settle` itself (`treewidth_is_exact: True` in every
result).

---

## 5. Honest refusal on the genuinely high-treewidth N=16 stress case

```
N=16 stress case refusal: {'attempted': False, 'exact': False, 'treewidth': 15,
  'treewidth_is_exact': False, 'treewidth_bound': 4,
  'reason': 'treewidth 15 (heuristic upper bound) exceeds bound 4 -- refusing
  exponential exact inference, not attempting it blindly'}
refusal wall-clock: 0.0015s
```

**No graph mutation** — every Concept's `state` attr was confirmed
byte-identical before and after the refused call (test:
`test_junction_tree_honestly_refuses_n16_stress_case_no_mutation_attempted`).
**No exponential work attempted** — the refusal completes in ~1.5ms
(`min_fill_upper_bound` alone, no brute-force treewidth search since
`16 > max_exact_n=10`, no `3^16≈43M`-state enumeration) — a real safety/scope
guard, not a performance nicety: a naive "compute exact treewidth then
decide" design would have hung on `16!` permutations; this tool's
heuristic-first gate for oversized graphs avoids that entirely.

---

## 6. Junction-tree vs. `multi_start_settle_and_pick_best` — a genuine,
measured comparison between two toolbox members

On a real-cycle-topology (8-node ring) network — small enough to verify
treewidth directly, distinct from both the Bigville template and the
frustrated-complete-graph stress case already used elsewhere in this arc:

```
ring(n=8) treewidth=2
junction-tree (exact) energy=-5.743322   multi-start (K=20, widened-ICM) energy=-5.102397
```

**Junction-tree found a strictly LOWER (better) energy than 20 independent
random-restart ICM runs on the identical network** — the concrete,
measured demonstration of what "exact" buys over "widened search": the
multi-start tool can only find the best among the `K` basins its random
restarts happen to land in; junction-tree is not searching basins at all,
it is computing the global optimum directly. (Two independently-built,
same-seed/same-topology substrates were used for the two tools — verified
not to contaminate each other's state.)

---

## 7. Regression

```
$ git diff --stat main -- '*.rs'
(empty)

$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py tests/test_can_solver_tractability.py \
  tests/test_bigville_can_native_migration.py tests/test_can_junction_tree.py \
  tests/test_can_crossover_point.py tests/test_can_belief_quantization.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_bigville_can_integration.py tests/test_can_migration.py \
  tests/test_can_final_migration.py tests/test_can_identity_feedback.py \
  tests/test_can_decay_identity.py tests/test_can_hebbian_materialization.py \
  -q
132 passed in 9.81s
```

117 pre-existing (all task-named files + the broader CAN suite this arc's
prior rung already ran) + 15 new, zero failures, zero pre-existing test
file touched. Per-file for the new file:
`tests/test_can_junction_tree.py` 15 passed (0.40s standalone).

---

## 8. Design decisions, stated and justified (per task's explicit asks)

### 8.1 Python, not a new Rust Term

**Decided: pure Python.** Treewidth computation and junction-tree
construction/message-passing operate on a plain, already-read `(nodes,
edges, unary, pairwise)` snapshot — the same class of "math over data
already pulled out of the graph" as this arc's own prior
`measure_low_rank`'s SVD call (`scripts/can_solver_tractability_measure.py`).
It is not a decision over live agent/graph cognition state
(`CLAUDE.md`'s actual target), it does not need `run_rules`'s fixpoint
(one call, one exact answer — no repeated re-matching), and it does not
need the admissibility grammar's generativity (a pure function of a
read-only snapshot, not a decision about what the agent's graph may
contain). The two places this DOES touch live substrate state are both
precedented mechanical shapes: reading `external_field`/
`identity_field`/edge `weight` via the same `Term("Edges", ...)`/
`Term("EdgeAttr", ...)` composition `domains/can_counterfactual.py`
already uses (confirmed live before writing any code — `Edges` evaluates
directly to `(src, edge_type, tgt)` tuples, `EdgeAttr` evaluates directly
to the raw float weight), and committing the already-decided winning
state via `set_attr`, the same mechanical-commit shape
`multi_start_settle_and_pick_best`'s own final step already uses. Full
reasoning in `CAN_JUNCTION_TREE_PREREG.md` §4.

### 8.2 Integration point — new file, explicit opt-in, no automatic
dispatch

**Decided: `domains/can_junction_tree.py`, a new standalone module, NOT a
new function inside `domains/can_native_orchestration.py`, and NOT
automatic treewidth-gated dispatch inside any existing entrypoint.**
Three reasons, in order of weight: (1) this arc's own established
precedent is one file per CAN capability
(`can_counterfactual.py`/`can_native_hebbian_bridge.py`/
`reasoning_can_bridge.py` are all separate from `can_native_
orchestration.py`), and junction-tree inference shares NONE of that
file's internal shape (it never calls `run_rules`/`scoped_settle` — it
computes the optimum directly, it does not relax anything); (2)
collision-avoidance under house discipline point 2 — two sibling
worktrees active this session already touch CAN files
(`can-synchronous-update-fix`, `can-solver-worktree`); a new file has zero
merge-conflict surface with any concurrent edit to `can_native_
orchestration.py`, confirmed by this rung's own `git diff --stat main --
domains/can_native_orchestration.py` being empty; (3) automatic dispatch
was explicitly considered and rejected — silently swapping solving
strategies inside an existing entrypoint based on a computed treewidth
would hide a genuinely different GUARANTEE (exact vs. heuristic-widened)
behind one call site and would silently change behaviour for every
existing `multi_start_settle_and_pick_best` caller the moment their
network happened to cross the bound. A toolbox exposes distinct tools
with distinct guarantees; it does not pick one for the caller. Full
reasoning in `CAN_JUNCTION_TREE_PREREG.md` §5.

---

## 9. What this rung does NOT establish

1. **No deployed Bigville behaviour changed.** `junction_tree_exact_settle`
   is a new, opt-in tool. Nothing in this codebase calls it automatically;
   wiring it as the default solving path for any real caller (e.g.
   `self_improvement_loop.py`) is a separate, unbuilt decision — this rung
   deliberately keeps it opt-in (§8.2).
2. **Treewidth was measured for exactly the same two real graphs the
   prior rung already measured** (Bigville's 5-node template, the N=16
   synthetic stress case) plus one new synthetic ring network built for
   the multi-start comparison — this rung does not sweep new topologies
   or claim anything about the treewidth of any OTHER real or hypothetical
   `causal_influence` network this project might build in the future.
3. **The min-fill heuristic upper bound's tightness on graphs BETWEEN
   the two measured real extremes (treewidth 2 and 15) is untested.**
   Nothing in this project's real deployed data currently sits between
   them.
4. **This rung targets exact MAP (global-minimum-energy state), not exact
   marginals.** A Boltzmann-weighted sum-product pass at the Mt's own
   `temperature` (exact marginals rather than the exact optimum) is a
   real, separate, unbuilt extension — PREREG §7 registered this choice
   in advance; it was not discovered as a limitation after the fact.
5. **`max_exact_n=10`'s worst-case ~5s timing was measured on this
   machine, this session, once.** It is a reasonable default, not a
   portable guarantee across hardware; a caller with a harder latency
   budget should pass a smaller `max_exact_n` explicitly.
6. **The comparison in §6 is ONE network, ONE seed, ONE run of
   multi-start (K=20).** It demonstrates the qualitative claim ("exact
   finds what a widened random search may miss") concretely and with real
   numbers, but is not a systematic sweep of how OFTEN or by HOW MUCH
   multi-start under- performs junction-tree across many networks/seeds —
   that would be a natural, larger follow-on measurement in the shape of
   `CAN_SOLVER_TRACTABILITY_RESULTS.md`'s own condition-A/condition-B
   design, not attempted here.
7. **Two sibling worktrees' own concurrent CAN work was not merged or
   reconciled here** — this rung only confirmed its own diff has zero
   overlap with `domains/can_native_orchestration.py`; whatever those
   siblings build is unexamined and untouched by this rung.

---

## 10. Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-junction-tree
git log --oneline -1 main   # 76b8aea, verified before branching

PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_junction_tree.py -q -s

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py tests/test_can_solver_tractability.py \
  tests/test_bigville_can_native_migration.py tests/test_can_junction_tree.py \
  tests/test_can_crossover_point.py tests/test_can_belief_quantization.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_bigville_can_integration.py tests/test_can_migration.py \
  tests/test_can_final_migration.py tests/test_can_identity_feedback.py \
  tests/test_can_decay_identity.py tests/test_can_hebbian_materialization.py \
  -q

git diff --stat main -- '*.rs'
git diff --stat main -- domains/can_native_orchestration.py
```
