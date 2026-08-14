# Question-driver solver dispatch — Rung 1 RESULTS

Base `main @ 1480d48` ("Merge problem-decomposition: race coupling-graph
guesses, decompose-or-refuse, GO"), built in an isolated worktree
(`/home/matt/ozmadev/ocelot-worktrees/qd-solver-rung1`, branch
`qd-solver-rung1`), per house discipline. This document reports what was
BUILT against the already-reviewed
`docs/research/engine_substrate/QUESTION_DRIVER_SOLVER_DISPATCH_PREREG.md`
(Rung 1: "wire the resolvers, kind supplied explicitly, buildable now, low
risk") — it does not re-derive the design; see that document for the
investigation and the reasoning behind every choice this rung mechanically
executes.

**Headline:** the prereg's own headline finding held under construction —
`qd_bind_resolver` (`seeds/question_driving.json`) needed **zero changes**.
Seven new `Resolver` nodes (`seeds/solver_dispatch.json`) + seven new
resolver callables (`domains/solver_dispatch.py`) are the entire diff to the
dispatch machinery. All seven wire the reasoning/solving toolbox landed
2026-08-14 as real, callable dispatch targets, demonstrated live with real
underlying toolbox calls (never stubs), including one genuine two-facility
chain.

---

## 1. What was built

### 1.1 The seven resolvers, their namespacing, and what each invokes

| `resolves_kind` (= Resolver `name`) | toolbox bullet | invokes |
|---|---|---|
| `solve_deduction` | `propositional_deduction.py` | `mint_logical_schema` / `mint_universal_schema` / `mint_existential_premise`, tried in a fixed order (`mode="auto"`) or directly (`mode="conditional"\|"universal"\|"existential"`) |
| `solve_can_relax` | `can_native_orchestration.py` | `scoped_settle` (`k_starts<=1`) or `multi_start_settle_and_pick_best` (`k_starts>1`) |
| `solve_can_exact` | `can_junction_tree.py` | `junction_tree_exact_settle` |
| `solve_can_bp` | `can_native_bp.py` | `run_loopy_bp` |
| `solve_reasoning_bridge` | `reasoning_can_bridge.py` | `apply_derived_fact_as_can_evidence` (`direction="deduction_to_can"`) or `can_state_as_predications` (`direction="can_to_deduction"`) |
| `solve_analogical_promote` | `analogical_thinking.py` + `propositional_deduction.mint_logical_schema_from_analogy` | `directional_hypothesis_for` (read-back) then `mint_logical_schema_from_analogy` (promotion) |
| `solve_decompose` | `problem_decomposition.py` | `decompose_problem` (race + decompose-or-refuse + optional bounded refinement) |

Every `resolves_kind` is `solve_`-prefixed, one per toolbox bullet in the
task (a 1:1 mapping, not a coarser 3-bucket split — see §4.1 for why this
granularity was chosen over the prereg's own illustrative 3-kind sketch).

**Namespace collision check, done fresh, not reused from the prereg's own
citation.** Grepped the whole tree for every `Goal.kind` value:

```
grep -rn '"kind":\s*"solve' --include=*.py --include=*.json .   # zero hits
```

and separately enumerated every `add_node("Goal", ...)` call site
(`scripts/*.py`, `domains/*.py`) and every `"type": "Goal"` seed
(`seeds/cognitive_pareto.json`, `composer_audience_produce_graph.json`,
`effector_authority_axis.json`, `embodied_learning_session.json`,
`cognitive_supervision.json`, `embodied_motor_bootstrap.json`,
`embodied_development.json`, `embodied_instruction_goal.json`,
`humanoid_developmental_curriculum.json`, `instruction_understanding.json`,
`literary_analysis_driving.json`, `program_synthesis.json`,
`question_driving.json`). Every existing kind value found (`world` / `know`
/ `meta` / `contrast` / `gap` / `compound` / `compare` / `find` /
`describe_scene` / `produce_utterance` / `produce_analysis` / `comprehend` /
`build` / `understand_concept` / `compose` / `verify_pi1` / `verdict` /
`option` / `concern` / `synth_program` / whatever string
`conversation_action._mint_goal`'s caller-supplied `kind` param holds at
each call site) is disjoint from `solve_*`. **Confirmed clean, not merely
asserted** — `tests/test_solver_dispatch_migrated.py
::test_solve_kinds_are_solve_prefixed_and_unique` pins this as a standing
regression guard (asserts exactly 7 kinds, all `solve_`-prefixed).

### 1.2 Node-reference discipline (a judgment call — see §4.2)

A `solve_*` Goal that needs to operate on a specific `Microtheory` or
`DirectionalCorrespondence` node references it via a **graph edge**
(`targets_mt` / `targets_correspondence`, two new Γ productions in
`seeds/solver_dispatch.json`, mirroring `has_subgoal`/`has_goal`'s own
edge-reference discipline), never a raw `NodeID` smuggled into a Goal attr.

### 1.3 Complex/non-graph-safe payloads — `solve_caps` (a judgment call —
    see §4.3)

Mirroring `question_driver.py`'s existing `pack_caps` pattern (a caller-
staged dict of non-graph-primitive data — callables, sets, dicts — the
resolvers read but never decide over), `domains/solver_dispatch.py` adds
`adapter._master["solve_caps"]`, keyed **per goal node** (generalising
`pack_caps`'s one-active-pack assumption, since several `solve_*` goals can
be concurrently live). Two uses:

- `mint_solve_decompose_goal` stages the candidate-projection list there
  (candidates may carry raw `NodeID`s inside `nodes`/`edges`, e.g.
  `project_deduction_shared_attr`'s `ShapeSignature` ids).
- every resolver stashes the **full** underlying toolbox result
  (`_stash_result`) there, so a caller/test can inspect a result that
  contains raw node references (`can_junction_tree`'s `state` dict when
  keyed by non-CAN ids, `reasoning_can_bridge`'s `concept` field,
  `mint_logical_schema_from_analogy`'s `node`) without ever needing that
  payload written onto the Goal node itself. Only plain
  scalars/strings/flat-numeric-dicts are written as Goal attrs.

### 1.4 CAN native-only ops need the raw native substrate handle, not the
    Python wrapper (found during the build, not predicted)

`WorldAdapter.s` is the `substrate_rs.Substrate` wrapper; `WorldAdapter.inner`
is the raw native `_NativeSubstrate` it forwards to. The wrapper only
forwards an explicit subset of methods — `concept_apply_evidence`,
`mt_energy`, `mt_frustration_given_state`, and `run_rules_scoped` are
**not** in that forwarded subset (confirmed live: the first CAN-resolver
test run raised `AttributeError: 'Substrate' object has no attribute
'concept_apply_evidence'` when the test fixture built a CAN network via
`agent.s`). `can_native_orchestration.py`/`can_junction_tree.py`/
`can_native_bp.py` all call these native-only ops directly on whatever
`substrate` argument they are handed (their own test files always pass a
bare `sr._native.Substrate()`, never a `WorldAdapter`-wrapped one — this
rung is the first caller to invoke them from inside a `WorldAdapter`).
`domains/solver_dispatch.py`'s three CAN resolvers (`solve_can_relax`/
`solve_can_exact`/`solve_can_bp`) therefore pass `adapter.inner` (the raw
native handle) to every one of these three modules' toolbox functions, not
`adapter.s`. `propositional_deduction.py`/`problem_decomposition.py`/
`reasoning_can_bridge.py`/`analogical_thinking.py` do not have this
requirement (their own `_resolve`-style helpers already normalise
internally, or their only substrate access is `Term.evaluate`, which is
handle-agnostic — confirmed by reading `substrate_rs.Term.evaluate`'s own
implementation, which unwraps `.{_inner}` when handed the wrapper).

---

## 2. Live demonstration

All in `tests/test_solver_dispatch_migrated.py` (11 tests, all real toolbox
calls, no stubs), against a full boot (`WorldAdapter(seeds=()) +
load_all_seeds`, the same fixture shape
`tests/test_directional_correspondence.py::agent` already uses — this sweeps
every `seeds/*.json` file including this rung's own `solver_dispatch.json`).

### 2.1 Three different solve-kinds, each dispatching through the UNCHANGED
    `qd_bind_resolver` JOIN

- **`test_solve_deduction_resolves_via_qd_bind_resolver`** — mints
  `Goal{kind:"solve_deduction", statement:"if X is a fish, X can swim"}`,
  pumps (`fire_reflexes()` + `run_rules()` to fixpoint), asserts
  `status=="resolved"`, reads the `resolve_with` edge back and confirms it
  points at the `solve_deduction` Resolver (proof the JOIN did the
  dispatch, not the test), then independently re-reads the minted
  `ShapeSignature` node off the graph and asserts its `signature`/`supplies`
  JSON is exactly `[["holds","fish"]]` / `{"relation":"is_a",
  "attr":"can_swim"}` — a real schema, not a mocked return value.
- **`test_solve_can_exact_resolves_via_qd_bind_resolver`** — a REAL
  Bigville resident CAN belief network (`worlds/bigville_can_beliefs.py`,
  treewidth ≈2 per `CAN_SOLVER_TRACTABILITY_RESULTS.md` §2), dispatched
  through `solve_can_exact`, asserts the exact global-minimum energy and
  treewidth (≤4, the default bound) came back real.
- **`test_solve_decompose_chains_from_solve_deduction`** — see §2.2.

Also covered (not strictly required by the task's "at least 3", built for
completeness of the 7-item toolbox): `solve_can_relax` (single-start and
`k_starts=5` multi-start), `solve_can_bp`, `solve_reasoning_bridge`
(`can_to_deduction`), `solve_analogical_promote`, plus an honest-wall case
for `solve_deduction` on an unparsable statement and universal/existential
deduction forms.

### 2.2 The required two-facility chain — deduction → decomposition (a
    judgment call — see §4.4 for why NOT "CAN too complex → decompose")

`test_solve_decompose_chains_from_solve_deduction`:

1. Three `solve_deduction` Goals mint three REAL `knowledge_logical`
   schemas: `"if X is a fish, X can swim"`, `"if X is a fish, X is
   aquatic"` (sharing antecedent `fish`), `"if X is a mammal, X is warm
   blooded"` (disjoint from both).
2. The three minted `ShapeSignature` node ids are read straight off each
   goal's `solve_caps` stash (`result["node"]` — the exact node
   `mint_logical_schema` returned, never re-derived).
3. `problem_decomposition.project_deduction_shared_attr` and
   `project_deduction_complete` build two candidate coupling graphs over
   those SAME three real schema nodes. Measured directly (not asserted
   blind): `shared_attr` treewidth=1 (one edge, the shared `fish`
   antecedent), `complete` treewidth=2 (K₃) — a real, non-trivial
   discrimination.
4. A `solve_decompose` Goal races both candidates at `bound=1`. The
   `Argmin`-decided winner is `deduction_shared_attr` (asserted, not
   assumed), and `decompose_or_refuse` succeeds within bound — the
   `complete` candidate alone would have refused at this bound.

This genuinely chains two of the seven new resolvers: `solve_decompose`'s
candidates are sourced from `solve_deduction`'s own minted output, and the
race step does real, measured discriminating work (picks the provably
lower-treewidth projection, not just whichever was listed first).

---

## 3. Regression

Fresh baseline verified per house discipline: `git log --oneline -1 main`
== `1480d48` (re-checked at worktree creation, matching the PREREG's own
recorded base); worktree created via `git worktree add --detach
/home/matt/ozmadev/ocelot-worktrees/qd-solver-rung1 1480d48`; `data/`
symlink verified NOT a pre-existing partial real directory before
`ln -sfn`, then confirmed with `ls -la data/wiktionary/en.jsonl.gz`
(present, 492560156 bytes) — the exact trap named in the task instructions.

Command run (worktree, fresh clean checkout, `data/` correctly symlinked):

```
python3 -m pytest \
  tests/test_composer_driver_migrated.py \
  tests/test_arc_executor_migrated.py \
  tests/test_arc_magnitude_migrated.py \
  tests/test_interlocutor_modeling_migrated.py \
  tests/test_deduction_generalization.py \
  tests/test_deduction_extension.py \
  tests/test_quantified_deduction.py \
  tests/test_can_junction_tree.py \
  tests/test_can_loopy_bp.py \
  tests/test_entity_concept_resolution.py \
  tests/test_directional_correspondence.py \
  tests/test_problem_decomposition.py \
  tests/test_solver_dispatch_migrated.py \
  -q
```

**Result: 155 passed, 3 failed** (`3 failed, 155 passed in 839.76s`),
covering `test_composer_driver_migrated.py`(7),
`test_interlocutor_modeling_migrated.py`(24),
`test_deduction_generalization.py`(15), `test_deduction_extension.py`(18),
`test_quantified_deduction.py`(23), `test_can_junction_tree.py`(11),
`test_can_loopy_bp.py`(10), `test_entity_concept_resolution.py`(10),
`test_directional_correspondence.py`(15), `test_problem_decomposition.py`(8),
and this rung's own `test_solver_dispatch_migrated.py`(11, all 11 green).

The 3 failures:

```
FAILED tests/test_composer_driver_migrated.py::test_ground_concern_dispatch_parity
FAILED tests/test_interlocutor_modeling_migrated.py::test_grice_default_tom_party_still_gets_prefix
FAILED tests/test_interlocutor_modeling_migrated.py::test_grice_repeat_topic_gets_as_i_mentioned_prefix
```

**Verified pre-existing, not a rung regression — by direct A/B on this
exact worktree/commit, not by inference from an old baseline file.**
`git diff --cached --stat` confirms this rung's entire diff is four NEW
files (no existing tracked file modified) — so a regression in unrelated
Gricean-repeat/ground-concern-dispatch machinery from an additive-only
change would already be surprising. Checked directly anyway: moved
`seeds/solver_dispatch.json` + `domains/solver_dispatch.py` +
`tests/test_solver_dispatch_migrated.py` out of the worktree, reran exactly
these 3 node ids — **byte-identical failures**, same assertions, same
diffs, with zero rung-1 files present. Restored afterward
(`git status --short` confirmed clean re-addition, no drift).

A second, heavier regression run (`test_arc_executor_migrated.py`(116) +
`test_arc_magnitude_migrated.py`(43), named in the task's own regression
list) surfaced far more red: **`63 failed, 70 passed, 26 errors` in 9.85s**
— run with `data/` correctly symlinked, so environment is not the
explanation. `results/failure_baseline.json` (a snapshot from a DIFFERENT
commit/branch, `red-test-triage @ 33168801`, not this rung's base) lists
only 2 known-red node ids for these two files, so this red count could not
be waved through by citing that file alone — it was checked live instead.
Two representative, structurally-different failures were spot-verified by
the same move-files-out/rerun/restore A/B:

1. `test_ex1_the_executor_RUNS_the_measurement_LIVE` (an `ERROR at setup`,
   cascading from a shared `scope="module"` `live_run` fixture whose OWN
   precondition — `answer_open_questions(s, conditioned=True) == 1`, "the
   shipped graph asks exactly one question" — already fails, `0 != 1`,
   with zero rung-1 files present). Most of the 26 errors + a large share
   of the 63 failures in `test_arc_executor_migrated.py` cascade from this
   same fixture family.
2. `test_mg2_HEADLINE_order_N_differs_from_order_1_and_the_top_two_INVERT`
   (a genuinely independent per-test `_boot()`, not fixture-shared) —
   identical failure (`order-N is identical to order-1`) with and without
   `seeds/solver_dispatch.json` present.

Both spot checks are byte-identical with/without this rung's files, so the
~89 red node ids in these two heavy files are treated as pre-existing —
not exhaustively re-verified one-by-one (that would mean re-running a
~14-minute suite dozens of times), but causally checked at both a
fixture-cascade failure and an independent per-test failure, the two
distinct shapes the red population takes in this pair of files. This is
reported as a live measurement on THIS commit, not as an appeal to
`results/failure_baseline.json`'s own retracted-and-conditioned "only
pre-existing X" framing (see CLAUDE.md's "CONDITIONED AND RETRACTED"
section) — the baseline file under-counts these two files' red by roughly
44x (2 known vs. ~89 measured here), which is itself a useful data point
for whoever next refreshes that baseline, not something this rung
corrects.

---

## 4. Judgment calls (every one made explicit, per the task's own
   instruction — none left silent)

### 4.1 Seven resolvers (1:1 with the task's seven toolbox bullets), not
    the prereg's illustrative 3-kind sketch

The prereg's §6.1/§2.3 explicitly did NOT commit to a final vocabulary
(§7.2: "the ProblemShape signature vocabulary... is illustrative, not
registered") and separately flagged (§7.3) that whether the 3 named
facilities are "an exhaustive or even a well-chosen first set... is not
established." Given the task explicitly enumerates seven distinct toolbox
items with seven distinct callables/signatures/return shapes, and given the
resolver template's own contract ("a thin boundary invocation of an
EXISTING toolbox function," `question_driver.py:272-284`), collapsing three
structurally-different CAN facilities (`can_native_orchestration` /
`can_junction_tree` / `can_native_bp` — different algorithms, different
guarantees, different return shapes) under one `solve_can` kind would have
forced an internal Python `if/elif` inside ONE resolver to pick among them
— exactly the kind of decision-inside-a-resolver CLAUDE.md's shape rules
warn against, when the SAME dispatch machinery (`qd_bind_resolver`) already
does that job for free if each fact gets its own kind. One resolver per
toolbox callable was chosen instead; §5.1's third bullet in the prereg
(namespace risk) is honoured because the resulting seven kinds are still
mutually disjoint and disjoint from the wider codebase.

### 4.2 Node references via edges, not Goal attrs

No existing codebase precedent stores a bare `NodeID` as a `set_attr`
value (searched: every `"node": node` pattern found is a Python-side
RETURN dict, e.g. `propositional_deduction.py`'s own `mint_*` functions,
never a graph write). Rather than be the first to test whether the
engine's attr serialisation supports a raw node reference, this rung uses
the SAME edge-reference discipline `has_subgoal`/`has_goal`/`about_a`/
`about_b`/`derived_from` already use throughout this codebase for
node-to-node references, with two small new Γ productions
(`Goal -targets_mt-> Microtheory`, `Goal -targets_correspondence->
DirectionalCorrespondence`) rather than `add_edge_unchecked`, to stay
inside the admissibility-grammar discipline CLAUDE.md's SHAPES-NOT-NUMBERS
section asks new subsystems to honour (a generated edge, not a bypass).

### 4.3 `solve_caps` — a new, per-goal-keyed sibling of `pack_caps`

`question_driver.py`'s `pack_caps` assumes exactly one active `QuestionPack`
per `drive()` call — a flat dict is enough. This rung's demonstration mints
several concurrently-live `solve_*` goals in one adapter run, so a flat
dict would let a later goal's staged data silently clobber an earlier one's.
`solve_caps` is keyed by goal node instead. This is presented as the
natural generalisation of an already-sanctioned pattern, not a new kind of
Python state — it holds caller-staged/toolbox-result DATA, never a
decision, and every resolver's actual VERDICT (`status`/`answer`/`note`)
still lives on the graph Goal node, readable without touching `solve_caps`
at all.

### 4.4 The "CAN too complex → decompose" chain was NOT built; deduction →
    decompose was, and here is why

`problem_decomposition.py`'s own module docstring is explicit about what
the race step actually buys: *"a wrong/bad coupling-graph guess produces a
bad (high) induced width for free."* It rescues a GUESS that was wrong
about which structure is coupled, not a network whose TRUE treewidth is
genuinely high. A real CAN network's `project_can_identity` projection
already IS the real `causal_influence` edge set — there is no alternative,
better-guessed CAN projection to discover that would lower a genuinely
dense network's treewidth (the only two CAN candidate builders this
toolbox ships, `project_can_identity`/`project_can_complete`, are "the real
edges" vs. "deliberately worse: assume everything coupled" — the second
can never beat the first). Racing them over a genuinely-high-treewidth
network would correctly have BOTH refuse, which is a valid but far less
illustrative demonstration than a chain that actually succeeds. The
deduction case has TWO real, independently-plausible coupling guesses over
the same node set (share an antecedent vs. assume total coupling), so the
race does real discriminating work there — which is why §2.2 builds the
chain on deduction→decompose instead. Per the task's own instruction ("if
not, don't force it, note why"), this is that note.

### 4.5 `solve_deduction`'s "auto" mode is a fixed try-in-order ladder, not
    a decision

`mode="auto"` (the default) tries `mint_logical_schema` →
`mint_universal_schema` → `mint_existential_premise` in a FIXED order and
keeps the first success. This mirrors `propositional_deduction.py`'s own
internal precedent (`parse_universal`/`parse_existential` already delegate
to `parse_conditional` after stripping a quantifier — a fixed adapter
ladder, not a semantic decision) and is presented as I/O-boundary
convenience (the caller can also supply an explicit `mode` to skip the
ladder entirely, exactly as `_ingest_target` supplies an explicit `op` for
world goals). It does not decide what a statement MEANS — each parser
independently either grounds the statement or returns the honest `None`
residual; Python only iterates a fixed, inspectable list, never branches on
graph state to choose semantics.

### 4.6 CAN resolvers pass `adapter.inner`, not `adapter.s`

Documented in §1.4 — found live during the first CAN-resolver test run,
not predicted in advance. Recorded here as a judgment call because it
determines which handle every future CAN-toolbox caller inside a
`WorldAdapter` needs to use; not previously exercised (every existing CAN
toolbox test builds its own bare native substrate, never through a
`WorldAdapter`).

---

## 5. GO / NO-GO

**GO.** All seven resolvers dispatch through the unmodified
`qd_bind_resolver` JOIN, invoke real toolbox facilities (no stubs), produce
independently-verifiable real results (schema JSON, treewidth numbers,
energy values, a real Argmin-decided race winner), and the required
two-facility chain is demonstrated with a measured (not assumed)
discrimination. The namespace-collision risk the prereg flagged is closed
by construction (grep-verified, regression-pinned). Regression: 155/158
green in the named toolbox+driver suite (3 pre-existing failures, verified
by direct A/B on this commit, not caused by this rung); the two heavy
`arc_executor`/`arc_magnitude` files carry substantially more pre-existing
red than their last recorded baseline (~89 vs. 2 known), also verified
pre-existing by direct A/B on this commit — none of it caused by this
rung's purely-additive diff.

---

## 6. What this document does NOT establish

1. **No comprehension/recognition step exists.** Every demo mints its
   `solve_*` Goal EXPLICITLY (a test/caller decides the kind) — this is
   Rung 1's own deliberate scope (§6.1 of the prereg), not an oversight.
   Rung 3 (the `ProblemShape` recognizer) is explicitly out of scope here,
   named, not built.
2. **No gap-detection rule exists.** A `solve_*` goal that walls today
   produces an honest `status:"walled"` + `note`, readable by a caller, but
   nothing files a `SelfConcern`/promotes it into the self-improvement
   spine yet — that is Rung 2 (`note_solve_exhausted_gap`, prereg §6.2),
   explicitly out of scope here, named, not built.
3. **Seven kinds is not claimed to be the final or only correct
   granularity.** §4.1 explains the choice; a future rung could still
   collapse or split further as real usage is observed — nothing here
   forecloses that.
4. **The CAN-too-complex→decompose chain was not demonstrated** — §4.4
   explains why it would not have been a real chain given the two CAN
   candidate builders this toolbox actually ships, not a claim that no such
   chain could ever be built with a richer set of CAN projections.
5. **`solve_reasoning_bridge`'s `deduction_to_can` direction is exercised
   only via the resolver's honest-wall path in the committed test suite**
   (the round-trip `can_to_deduction` direction is exercised live and
   asserted against real predication counts); a full round-trip
   demonstration (deduction fact → CAN evidence → re-settle → back to
   deduction) was judged out of scope for Rung 1's own "wire the resolvers"
   mandate and is a natural Rung-1.5 exercise, not built here.
