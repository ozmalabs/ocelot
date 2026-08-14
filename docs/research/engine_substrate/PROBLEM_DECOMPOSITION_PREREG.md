# Problem decomposition via racing coupling-graph guesses — PREREG

Base `main @ 551dad9` ("Merge shape-audit-sweep2: SHAPE_AUDIT.md remaining
findings, partial sweep, GO"), verified via `git log --oneline -1 main`
fresh before branching (per house discipline — main has moved repeatedly
today, no cached hash assumed). Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/problem-decomposition`,
branch `problem-decomposition`. This is the 7th item of today's
reasoning/solving toolbox arc (after `can_junction_tree.py`,
`can_native_bp.py`, entity-concept correspondence, quantified deduction,
directional correspondence, SHAPE_AUDIT sweep 2) — design agreed live with
the user in conversation, not sourced from a doc; this PREREG registers the
already-agreed design before building it, per house discipline.

---

## 0. What this rung is

Given an UNSEEN problem, you cannot know upfront which "what's coupled to
what" projection into a graph is the right one for exact treewidth-bounded
decomposition (`domains/graph_treewidth.py`, `domains/can_junction_tree.py`'s
own consumer of it). **The fix is not to get the projection right — it's to
make each guess cheap enough that being wrong doesn't matter, and to reuse
`min_fill_upper_bound`'s own output AS the verification signal.** A wrong
coupling-graph guess genuinely under- or over-couples the true problem
structure, and that shows up directly as a HIGH induced width in the SAME
greedy min-fill pass that would otherwise be spent computing the width for
its own sake. Propose and verify collapse into one cheap pass — there is no
separate "is this projection any good" check to build.

This rung builds that racing step as a new, standalone, domain-agnostic
module, `domains/problem_decomposition.py`, reusing
`domains/graph_treewidth.py`'s existing functions (`min_fill_upper_bound`,
`treewidth_bound_check`, `build_elimination_triangulation`) **completely
unchanged** — confirmed by direct read this session
(`domains/graph_treewidth.py:1-45`'s own docstring: "CAN-agnostic — works on
any undirected graph", and the function bodies operate on plain
`(nodes, edges)` tuples with zero CAN-specific types anywhere in the file).

---

## 1. The three pieces (registered before building)

1. **Candidate projection generation.** For a given problem source, a SMALL
   SET (2-4) of cheap alternative "coupling graph" guesses. Each candidate is
   a plain `{"name": str, "nodes": [...], "edges": [...]}` dict — the exact
   `(nodes, edges)` shape `graph_treewidth.py`'s functions already take.
   Building a candidate is NEVER a decision about which one is right (that's
   the race's job) — each builder just reads one REAL representation already
   resident in this codebase and reports one honest guess.

2. **Racing.** `min_fill_upper_bound` (unchanged) runs on each candidate.
   One `ProjectionCandidate` node per candidate is minted holding its name +
   treewidth; the winner (lowest treewidth) is selected via the graph-native
   `Argmin` Term (`term.rs:382`) over those candidates — the SAME selection
   idiom `domains/can_native_orchestration.py::multi_start_settle_and_pick_best`
   already uses for its own K-restart winner (confirmed by direct read this
   session, `can_native_orchestration.py:236-249`), not a Python `min()`.

3. **Decompose-or-refuse.** On the winning projection: `treewidth_bound_check`
   (unchanged) against a caller-supplied bound. Within bound: decompose via
   `build_elimination_triangulation` (unchanged), returning bags/parent
   structure for a caller to solve per-clique (NOT built here — see §6,
   explicitly out of scope, the natural follow-on). Above bound even for the
   best candidate: honest refusal, mirroring `can_junction_tree.py`'s own
   refusal shape exactly (`attempted: False`, zero mutation — this function
   never touches a live substrate at all, so there is nothing to mutate).

---

## 2. Candidate projections this rung builds (registered before measuring)

Grounded in REAL representations already in this codebase, not synthetic
fixtures, per the task's own explicit requirement:

1. **CAN belief network (identity projection).** The correctness anchor.
   `domains/can_junction_tree.py::can_network_from_mt` (unchanged, reused
   directly — confirmed live against real Bigville resident networks
   already, `CAN_JUNCTION_TREE_RESULTS.md`) reads a Mt's `causal_influence`
   edges into `(nodes, edges)` — this IS a coupling graph already,
   projected trivially. **Registered claim to verify:** running the general
   race+decompose path with this as (one of) the candidates on a real
   Bigville resident network must reproduce `can_junction_tree.py`'s own
   direct `treewidth_bound_check` + `build_elimination_triangulation` call
   EXACTLY (same treewidth, same bags, same parent structure) — both paths
   call the identical, unchanged functions on the identical `(nodes, edges)`
   list, so exact reproduction is the expected/registered outcome, not a
   coincidence to hope for; failing this would mean the general path is
   secretly doing something CAN-specific under the hood, and that failure
   would be reported as a defect, not patched around.
   A DELIBERATELY-BAD alternative CAN projection (every concept pair
   coupled, ignoring real `causal_influence` edges) is also built, over the
   SAME real node set, to test discrimination on this domain too.

2. **Deduction schemas — shared-attr coupling.**
   `ShapeSignature{kind:"knowledge_logical"}` nodes
   (`domains/propositional_deduction.py::mint_logical_schema`, minted from
   real English prose through the general reading pipeline — no toy strings
   invented, real sentences the reader actually grounds). Each schema holds
   `signature: [["holds", antecedent_attr]]` and
   `supplies: {"relation":..., "attr": consequent_attr}` (confirmed by
   direct read, `propositional_deduction.py:276-286`). **Coupling notion
   investigated and chosen:** two schemas are coupled iff they share an
   antecedent_attr or consequent_attr — the natural reading, because a
   schema whose consequent feeds another's antecedent (a chain: "robin ⇒
   bird", "bird ⇒ can_fly") or two schemas about the SAME variable are
   genuinely entangled for joint inference; two schemas about disjoint
   predicates ("robin ⇒ bird" vs "fish ⇒ can_swim") are not, and should NOT
   be coupled. A DELIBERATELY-BAD alternative (every schema pair coupled
   regardless of shared attrs — the "everything is related" null
   hypothesis) is built over the SAME schema set, to prove the racing step
   does real discriminating work, not just always pick the one
   obviously-good option handed to it.

3. **Situation-model entities — shared-event coupling (third candidate, used
   for generality, judgment call per the task's own "use your judgment"
   allowance).** `domains/situation_model_reader.py` mints `SmEvent` nodes
   with `agent`/`theme`/`goal` role edges to `SmEntity` nodes (confirmed by
   direct read, `situation_model_reader.py:394-435`) — this role structure
   already IS a coupling graph over entities: two `SmEntity` nodes are
   coupled iff they co-occur as roles of the SAME `SmEvent`. Read
   mechanically (no new decision — the role edge types are the ones that
   module already installs), over real text run through
   `situation_model_reader.read_into_situation_model`.

---

## 3. The racing mechanism (registered, mirrors an existing precedent)

`domains/problem_decomposition.py::race_projections(substrate, candidates)`:
run `min_fill_upper_bound` on each candidate's `(nodes, edges)`, mint one
`ProjectionRaceSession` + N `ProjectionCandidate` nodes (Γ production
registered exactly like `can_native_orchestration.install_multi_start_
productions` — a generated edge type, not a filter, per CLAUDE.md's
SHAPES-NOT-NUMBERS admissibility discipline), then decide the winner via
`Term("Argmin", source=Term("Neighbours", node=Lit(session),
edge_type="pr_candidate", any_type=False), var_name="cand",
value=Attr(Var("cand"), "treewidth"))` — the decision lives in the Term
evaluator, byte-identically to how `multi_start_settle_and_pick_best`
already decides its own winner by `frustration`. No Python `if`/`min()`
picks the winner.

---

## 4. GO/NO-GO criteria (registered before running)

- **GO** iff: (a) the discriminating-race demo shows a deliberately-bad
  single-candidate guess would refuse under a bound the SAME real problem's
  good projection clears, and the race (given both) picks the good one; (b)
  the CAN correctness anchor reproduces `can_junction_tree.py`'s own direct
  treewidth/bags/parent structure EXACTLY on a real Bigville resident
  network; (c) the cross-facility deduction case shows a genuine
  MULTI-CLIQUE split (≥2 bags with non-trivial structure, not one bag
  containing everything) on real minted schemas; (d) the refusal case shows
  `attempted: False` and zero graph mutation when every candidate exceeds
  the bound, on a real (previously-measured) high-treewidth network; (e) all
  named regression files (`test_can_junction_tree.py`,
  `test_deduction_generalization.py`, `test_deduction_extension.py`,
  `test_quantified_deduction.py`) plus this rung's new tests stay green.
- **NO-GO / partial** iff any of the above fails to reproduce, or the
  refusal path silently attempts exponential/expensive work instead of
  refusing, or `graph_treewidth.py`/`can_junction_tree.py` need modification
  to make this work (in which case: STOP, report the defect, do not
  silently patch a function three other things now depend on).

---

## 5. Python-vs-Rust design decision (registered)

**Decision: pure Python, no new Rust Term.** `Term.rs`'s `Argmin` (confirmed
present, `term.rs:382`, already used across ~10 seeds per its own comment at
that call site in `can_native_orchestration.py`) already does everything
this rung's selection step needs — no new Term. Building the candidate
`(nodes, edges)` lists is mechanical read-out of already-resident graph data
(the SAME class of computation `can_network_from_mt`/`can_junction_tree.py`
already does in Python, per that module's own PREREG §4 reasoning, reused
verbatim here) — not a decision over live agent/graph cognition, so it stays
Python per CLAUDE.md's own carve-out for graph-algorithm-over-a-snapshot
code. Racing (Argmin) and the decompose-or-refuse gate compose two
ALREADY-EXISTING graph-native/pure-function primitives; no new primitive is
needed at either layer.

---

## 6. What this rung will NOT establish (registered in advance)

1. **No per-clique solver.** Decompose-or-refuse returns bags/parent
   structure a caller can act on; dispatching the RIGHT solving facility per
   clique (the shape-decode-based meta-selection work discussed live but not
   yet built) is explicitly out of scope — named here as the natural
   follow-on this rung's output feeds, not built.
2. Whether the shared-attr / shared-event coupling notions generalize to
   deduction-schema or situation-model topologies other than the ones built
   and measured here — this rung demonstrates the mechanism works on real
   representative cases, it does not sweep the space of possible coupling
   notions per domain.
3. Whether racing helps on problems where NO candidate in the small set is
   any good — the racing step can only pick the best of what it's given; if
   every guess in the set is bad (the refusal demo constructs exactly this),
   the tool refuses honestly, it does not somehow recover a good projection
   nobody proposed.
4. Whether `min_fill_upper_bound`'s width is a reliable enough proxy for
   TRUE treewidth to always pick the projection with the lowest EXACT
   treewidth (as opposed to lowest heuristic upper bound) — untested here,
   same honestly-scoped limitation `CAN_JUNCTION_TREE_PREREG.md` §7.3
   already registered for the heuristic itself, inherited unchanged.

---

## 7. LIVE AMENDMENT (registered mid-build, before implementing) — bounded,
   effort-budgeted, residual-driven refinement, NOT a hardcoded round count

The user's own correction, live, in two passes:

**Pass 1** — "no view from nowhere — there is never a complete answer to a
sufficiently complex problem. Eliminate search space + cheap is the move.
Basically 80/20, iteratively." Refusal-on-first-round-failure treats round 1
as if it had to be complete; a failed round should cheaply NARROW the space
before falling back to full refusal — the same discipline `exact_treewidth`'s
own branch-and-bound pruning already applies at the elimination-order level
(`graph_treewidth.py:84-86`: `if best is not None and width >= best: pruned
= True; break` — eliminate a branch the moment continuing provably isn't
paying off, never exhaustively re-search it), applied one level up, at the
projection-choice level.

**Pass 2** — the first design response to Pass 1 (a fixed "1-2 extra rounds"
cap) was itself flagged, correctly, as the SAME scalar-knob mistake
CLAUDE.md's own "SHAPES, NOT NUMBERS" section names (F-16 arc: *"1/n asserts
stationarity → declare a floor 0.05 → ... each rate needs a rate"*). The
corrected shape, from the user directly: *"not 1-2 extra — an effort knob. A
residual feedback. A decision on whether to think more or to seek further
information/processes or to move on or whatever."*

**Registered design (before implementing):**

1. **Effort knob, not a hardcoded cap.** `decompose_problem` gains a
   caller-supplied `refine_budget: int` parameter (rounds; default `0` —
   NO refinement unless a caller opts in, so every existing/registered
   single-round GO criterion in §4 is preserved byte-for-byte as the default
   path). The budget lives on the CALL, never baked into the algorithm.
2. **Residual signal, not a boolean pass/fail.** `min_fill_upper_bound`
   already reports a width for free each round; the residual is
   `gap = width - bound`, tracked round over round, and `delta = prev_gap -
   gap` — genuinely new information each round produces, not merely "still
   failed."
3. **A decision, not a loop — three honest, named stop conditions, never an
   open-ended search:**
   - `"bound_met"` — `gap <= 0`, decompose-ready.
   - `"budget_exhausted"` — `refine_budget` rounds spent, still above bound.
   - `"no_improvement"` — `delta <= 0` (the gap did not shrink, OR the
     perturbation mechanism found nothing left to trim) — diminishing
     returns; stop even with budget remaining, mirroring the SAME
     `exact_treewidth` pruning precedent one level up (cited above).
4. **What this module explicitly does NOT do.** `"no_improvement"` does NOT
   trigger this module trying a DIFFERENT projection-generation strategy
   (e.g. a different coupling notion entirely) — that is a genuine
   agent-level decision (which facility/process to invoke next), out of
   scope for a module that is pure graph-algorithm-over-a-snapshot code
   (§5's own Python-vs-Rust reasoning already scopes this file that way).
   `refine_projection` only returns an honest, inspectable `stop_reason` a
   FUTURE caller/dispatcher (the shape-decode meta-selection work already
   named in §6.1 as this rung's follow-on, not built here) could act on.
5. **The perturbation mechanism itself, bounded and cheap.** Candidate
   builders that have a natural notion of "why was this edge added" (the
   deduction shared-attr / situation-model shared-event projections — NOT
   the CAN identity/complete projections, which carry no such provenance
   because a real `causal_influence` edge is not a projection artifact to
   blame) attach an `edge_reason` map alongside `(nodes, edges)`. One
   refinement round = find the SINGLE reason responsible for the MOST
   edges (the worst clique's projection cause) and drop exactly those
   edges, re-racing the result through the SAME `race_projections`
   primitive already built (a refinement round is just another race, not a
   new mechanism). When a candidate carries no `edge_reason` data,
   `no_improvement` fires immediately (correctly — there is nothing cheap
   to trim, and the CAN N=16 stress case's honest refusal, §2.1/§4(d),
   must stay a genuine refusal, not be silently rescued).

**GO criterion added for this piece specifically:** a real candidate set
(genuine minted `knowledge_logical` schemas, not a toy graph) whose round-0
race fails for every candidate, where a BOUNDED, budgeted refinement shows
the residual gap genuinely SHRINKING over >=2 real rounds (not resolved in
one perturbation) before hitting `bound_met`, AND a separate run of the SAME
scenario at a smaller budget demonstrates `budget_exhausted` honestly
(partial progress logged, no silent success). Both a rescue and a
stop-for-cause must be shown, not only the rescue.
