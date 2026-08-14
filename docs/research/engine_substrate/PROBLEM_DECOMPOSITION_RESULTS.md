# Problem decomposition via racing coupling-graph guesses — RESULTS

See `PROBLEM_DECOMPOSITION_PREREG.md` for the full design record (registered
before building, including a live mid-build amendment, §7). Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/problem-decomposition`,
branch `problem-decomposition`, base `main @ 551dad9`. New code:
`domains/problem_decomposition.py` (~430 lines), `tests/
test_problem_decomposition.py` (10 tests). `domains/graph_treewidth.py` and
`domains/can_junction_tree.py` are UNCHANGED — no defect found in either, so
none needed patching (both reused verbatim, per the task's own instruction
to stop and report rather than silently edit a function three other things
now depend on).

**GO.**

---

## 1. The three pieces, as built

1. **Candidate projections** — five builders, each reading one REAL
   representation already resident in this codebase:
   - `project_can_identity` / `project_can_complete`
     (`domains/problem_decomposition.py:78-102`) — the CAN belief network's
     own `causal_influence` edges (reusing `can_junction_tree.
     can_network_from_mt` unchanged) vs. every-pair-coupled.
   - `project_deduction_shared_attr` / `project_deduction_complete`
     (`:141-180`) — real `ShapeSignature{kind:"knowledge_logical"}` nodes
     minted from real English prose via `propositional_deduction.
     mint_logical_schema`, coupled by shared antecedent/consequent attr, vs.
     every-pair-coupled.
   - `project_situation_model_shared_event` (`:183-213`) — real `SmEntity`
     nodes from `situation_model_reader.read_into_situation_model`, coupled
     by co-occurring as `agent`/`theme`/`goal` roles of the same `SmEvent`.
2. **Racing** (`race_projections`, `:216-262`) — `min_fill_upper_bound`
   (unchanged) on each candidate; one `ProjectionRaceSession` +
   N `ProjectionCandidate` nodes minted via a Γ production
   (`install_projection_race_productions`, mirrors `can_native_
   orchestration.install_multi_start_productions` exactly); the winner
   (lowest treewidth) decided by `Term("Argmin", ...)` over
   `Attr(Var("cand"), "treewidth")` — the identical selection idiom
   `multi_start_settle_and_pick_best` already uses for `frustration`. No
   Python `min()` anywhere in the decision path.
3. **Decompose-or-refuse** (`decompose_or_refuse`, `:269-292`) —
   `treewidth_bound_check` + `build_elimination_triangulation` (both
   unchanged) on the winning projection; within bound returns
   bags/parent/elim_index/order for a caller to act on; above bound returns
   `attempted: False` + a `reason` string, touching no substrate at all (the
   function takes only `(nodes, edges, bound)`, so "zero mutation" on
   refusal is true by construction, not merely tested).

`decompose_problem` (`:398-433`) composes all three into the single
caller-facing entrypoint.

---

## 2. Demonstration 1 — discriminating race, real deduction schemas

Five real sentences minted via the general reading pipeline
(`tests/test_problem_decomposition.py::FOREST_SENTENCES`):

```
if X is a robin, X is a bird       -> robin => bird
if X is a bird, X can fly          -> bird  => can_fly
if X is a fish, X can swim         -> fish  => can_swim
if X is a fish, X is a vertebrate  -> fish  => vertebrate
if X is a vertebrate, X can breathe -> vertebrate => can_breathe
```

`project_deduction_shared_attr` produces two disjoint chains
(`{robin⇒bird, bird⇒can_fly}` and `{fish⇒can_swim, fish⇒vertebrate,
vertebrate⇒can_breathe}`) — **treewidth 1**.
`project_deduction_complete` (K5, ignoring which attrs are actually shared)
— **treewidth 4**.

**Measured** (`test_discriminating_race_on_real_deduction_schemas_and_multi_clique_split`):

```
bad-alone (complete K5): treewidth=4 attempted=False   [bound=1]
good-alone (shared-attr forest): treewidth=1 attempted=True
race+decompose: winner=deduction_shared_attr treewidth=1 attempted=True
  race_candidates=[{'name': 'deduction_shared_attr', 'treewidth': 1, ...},
                    {'name': 'deduction_complete_overcoupled', 'treewidth': 4, ...}]
```

The bad guess, run alone under bound=1, refuses. Raced against the good
guess, the race picks the good one and decomposes — **the racing step does
real discriminating work**, not merely "the one candidate handed to it
happened to be fine." **Genuine multi-clique split**: 5 bags (one per
schema, all size ≤2), across **two disconnected trees** (`roots=[#834,
#848]`) — not one bag containing everything.

---

## 3. Demonstration 2 — CAN correctness anchor

`test_can_identity_projection_reproduces_can_junction_tree_exactly`,
3 real Bigville residents (indices 0, 1, 17):

```
resident #0:  direct tw=2  general-path tw=2  winner=can_identity
resident #1:  direct tw=2  general-path tw=2  winner=can_identity
resident #17: direct tw=2  general-path tw=2  winner=can_identity
```

For each: `can_junction_tree.py`'s own direct
`treewidth_bound_check`+`build_elimination_triangulation` call is compared,
node-for-node, against the general `decompose_problem(substrate, [identity,
complete], bound=4)` path. **Bags (as frozensets), parent structure, and
elimination order are asserted equal, not merely "close"** — and pass. This
is the expected, registered outcome (both paths call the identical unchanged
functions on the identical `(nodes, edges)` list), and it held: **the
general path is not secretly doing anything CAN-specific**, confirming the
racing/decompose machinery is genuinely domain-agnostic, not a narrower
CAN-only tool wearing a general interface.

---

## 4. Demonstration 3 — honest refusal, all candidates exceed the bound

`test_refusal_when_every_candidate_exceeds_bound_zero_mutation`, the
already-measured N=16 complete-graph CAN stress network (treewidth 15,
`CAN_SOLVER_TRACTABILITY_RESULTS.md` §2):

```
N=16 stress: candidates=[('can_identity', 120), ('can_complete_overcoupled', 120)]
refusal: attempted=False treewidth=15
  winner=can_identity
  reason=treewidth 15 (heuristic upper bound) exceeds bound 4 -- refusing
  decomposition, not attempting it blindly
```

(`can_identity` and `can_complete_overcoupled` are byte-identical here
because this specific stress fixture is ALREADY a complete graph by
construction — a real, honest edge case: even the "trivial" identity
projection is, for this network, the worst-case guess too.) Both candidates
exceed bound=4; `decompose_problem` refuses, `attempted: False`.
**Zero mutation of the problem's own graph state** — the 16 Concepts'
`state` attrs are read before and after and asserted byte-identical
(`before == after`). (Racing DOES mint its own bookkeeping
`ProjectionRaceSession`/`ProjectionCandidate` nodes — by design, Γ-generated
— but never touches the problem's own Concepts/edges; this is the same
distinction `multi_start_settle_and_pick_best`'s own session/candidate
scaffold already draws.)

A companion test
(`test_refinement_is_honest_no_improvement_on_can_domain_no_rescue`)
confirms refinement does not silently "fix" this: with `refine_budget=5`,
`refine_projection` reports `stop_reason="no_improvement"`,
`rounds_used=0` immediately — the CAN candidates carry no `edge_reason`
provenance (a real `causal_influence` edge has no "reason" to blame), so
there is nothing cheap to perturb, and the tool says so honestly rather than
fabricating a perturbation.

---

## 5. Demonstration 4 (live amendment, PREREG §7) — bounded, residual-driven refinement

The user's own two-pass correction mid-build: (1) a failed round-0 should
cheaply NARROW the space before full refusal, not treat round 1 as
definitive; (2) the first response to that (a hardcoded "1-2 extra rounds"
cap) was itself the F-16-shaped scalar-knob mistake — the fix is an **effort
knob** (caller-supplied budget) plus a **residual signal** (the real
`gap = width - bound` shrinking round over round) plus a **decision** with
three honest, named stop conditions, never an open loop.

**Real scenario**: 7 schemas minted via the general reading pipeline —
`CLIQUE_SENTENCES_A` (4 sentences, all consequent `animal`: dog/cat/
ostrich/shark) forms a K4 (6 edges); `CLIQUE_SENTENCES_B` (3 sentences, all
consequent `vehicle`: truck/scooter/glider) forms a K3 (3 edges), disjoint
from group A. Round-0 width = 3 (K4's own treewidth), bound = 1 — every
candidate fails.

**`refine_budget=5`**
(`test_bounded_refinement_gap_shrinks_over_two_real_rounds_to_bound_met`):

```
round0: treewidth=3 attempted=False
refinement log: [
  {'round': 0, 'candidate': 'deduction_shared_attr',                                'treewidth': 3, 'gap': 2},
  {'round': 1, 'candidate': "deduction_shared_attr_trim['animal']",                 'treewidth': 2, 'gap': 1},
  {'round': 2, 'candidate': "deduction_shared_attr_trim['animal']_trim['vehicle']", 'treewidth': 0, 'gap': -1},
]
stop_reason=bound_met rounds_used=2 final_treewidth=0
```

Round 1 finds `"animal"` (6 edges) the worst-offending reason — bigger than
`"vehicle"` (3 edges) — drops it: width 3→2, gap 2→1 (genuinely, but only
partially, improving; NOT resolved in one perturbation, so this is not the
"contrived single-perturbation toy" the coordinator explicitly asked this
demo avoid). Round 2 finds `"vehicle"` now the (only remaining) worst
reason, drops it: width 2→0, gap 1→−1, **`bound_met`**. **The gap shrinks
monotonically, 2 → 1 → −1, over two real rounds** — asserted directly in the
test (`gaps == [2, 1, -1]`).

**`refine_budget=1`, same scenario**
(`test_bounded_refinement_honestly_reports_budget_exhausted`):

```
budget=1: stop_reason=budget_exhausted rounds_used=1
  log=[{'round': 0, ..., 'gap': 2}, {'round': 1, ..., 'gap': 1}]
```

Partial progress (gap 2→1) is logged honestly; the pipeline reports
`attempted: False` — **it does not silently claim success it did not
reach.** Both a rescue (budget=5) and an honest stop-for-cause (budget=1) on
the SAME real scenario are demonstrated, per the amended GO criterion.

**Default unchanged** (`test_refine_budget_zero_is_byte_identical_to_no_refinement`):
`refine_budget=0` (the default) is byte-identical to calling
`decompose_or_refuse` directly — every existing/registered single-round
behaviour from §4 of the PREREG is preserved exactly; refinement is
strictly additive, opt-in.

**What this explicitly does NOT do** (registered in advance, PREREG §7.4,
confirmed as built): `refine_projection` never decides to try a DIFFERENT
projection-generation strategy on `no_improvement` — it only returns the
named stop reason. Choosing a different coupling-graph FAMILY when a
perturbation family plateaus is real agent-level judgment, explicitly
out of scope for this pure-graph-algorithm module (same scoping §5 of the
PREREG already gives the whole file).

---

## 6. Bonus — third candidate family generalizes too

`test_situation_model_shared_event_projection_discriminates`: a real
two-sentence narrative ("John gave Mary the pen. Mary took the cup.") run
through `situation_model_reader.read_into_situation_model` yields 2 real
`SmEvent`s and their role-linked `SmEntity` nodes. The shared-event
projection (2 edges) beats a complete-coupling alternative (6 edges) in the
race:

```
situation-model race: winner=situation_model_shared_event
  good_edges=2 bad_edges=6 treewidth=1
```

Confirms the racing mechanism is not special-cased to the two domains named
"at minimum" in the task — a third, independently-grounded real facility
(`agent`/`theme`/`goal` role edges) composes with `race_projections`/
`decompose_or_refuse` with zero changes to either.

---

## 7. Regression

Required suite (`tests/test_can_junction_tree.py`,
`tests/test_deduction_generalization.py`, `tests/test_deduction_extension.py`,
`tests/test_quantified_deduction.py`) plus this rung's new
`tests/test_problem_decomposition.py` (10 tests):

```
81 passed in 5.26s
```

No regressions; no pre-existing-failure list needed for this scope (all 81
green).

**Broader diligence check, and its honest limits.** `pytest tests/ -k
migrated` (the wider bench CLAUDE.md's own migration-completeness note
refers to) hit **22 pre-existing collection errors**, all confirmed
unrelated to this rung's changes before being set aside (per house
discipline's stale-baseline warning — verified, not assumed):
`ModuleNotFoundError: No module named 'av'` (test_communication.py, this
environment's `av` package is genuinely absent — confirmed via a bare
`python3 -c "import av"` outside any worktree), `ModuleNotFoundError: No
module named 'scipy'` (test_conditional_relational_migrated.py and
siblings, same direct confirmation for `scipy`), and `FileNotFoundError`
for `results/prog_synthesis_battery.json` (test_prog_descent_migrated.py) —
a generated artifact matched by `results/*` in `.gitignore`
(`git check-ignore -v` confirmed), present in the main working tree as an
untracked build artifact but absent by construction in any fresh worktree.
None of these 22 files import or reference `domains/problem_decomposition.py`
or anything this rung touched; this rung's changes are purely additive (two
new files, one new doc). A `pytest --continue-on-collection-errors` re-run
past those 22 to see the full migrated suite's pass/fail was attempted but
exceeded an 8-minute budget and was not completed — **this is named
honestly as unexecuted, not silently assumed green.** The REQUIRED
regression scope (§ above, the 4 named files + this rung's own tests) is
the load-bearing evidence for this rung's GO; the broader sweep was extra
diligence that surfaced pre-existing environment gaps, not a regression.

---

## 8. GO/NO-GO

**GO.** All five registered criteria (PREREG §4) plus the amended §7
criterion are met:

- (a) discriminating race: demonstrated, §2.
- (b) CAN correctness anchor, exact reproduction: demonstrated, §3.
- (c) genuine multi-clique split: demonstrated, §2 (2 disconnected trees, 5
  bags, max bag size 2).
- (d) honest refusal, zero mutation: demonstrated, §4.
- (e) regression green: demonstrated, §7.
- (f, live amendment) bounded residual-driven refinement — genuine
  multi-round gap shrinkage to `bound_met`, and an honest
  `budget_exhausted` stop on the same real scenario at a smaller budget:
  demonstrated, §5.

`domains/graph_treewidth.py` and `domains/can_junction_tree.py`: **zero
defects found, zero changes made.**

---

## 9. What this rung does NOT establish (honest, per PREREG §6)

1. **No per-clique solver.** `decompose_or_refuse` returns bags/parent
   structure; dispatching the right solving facility per clique (the
   shape-decode-based meta-selection work discussed live) is NOT built
   here — named as the natural follow-on this rung's output feeds.
2. Whether the shared-attr / shared-event coupling notions generalize
   beyond the specific real cases built and measured here — not swept.
3. Whether `min_fill_upper_bound`'s heuristic width is a reliable enough
   proxy for TRUE treewidth to always pick the EXACT-treewidth-optimal
   projection (as opposed to lowest heuristic upper bound) among the raced
   candidates — inherited, unresolved limitation from
   `CAN_JUNCTION_TREE_PREREG.md` §7.3.
4. **The refinement mechanism is a single, specific perturbation family**
   (drop the worst shared-reason group) — it composes with any candidate
   that carries `edge_reason` provenance, but this rung does not claim it
   is the ONLY or the best possible cheap perturbation; a future dispatcher
   choosing among several perturbation FAMILIES on `no_improvement` is
   explicitly named as out of scope (§5 above), not built.
5. The broader `pytest -k migrated` sweep past the 22 pre-existing
   collection errors was not completed within budget — §7 names this
   honestly rather than assuming a clean result.
