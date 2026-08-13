# Exact junction-tree inference for low-treewidth CAN networks — PREREG

Base `main @ 76b8aea` ("Merge reasoning-facility-bridge: two naming-convention
bridges land, low-rank hypothesis tested for real, GO"), verified via
`git log --oneline -1 main` before branching. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-junction-tree`,
branch `can-junction-tree`.

**Collision check (house discipline point 2, five sibling agents may be
running concurrently).** `git worktree list` at branch time shows five other
active worktrees touching this project; two touch CAN files directly
(`can-synchronous-update-fix` at `b9f4429`, `can-solver-worktree` at
`6e08be2`, both based on an OLDER `main` predating this arc's current
`docs/research/engine_substrate/CAN_*` layout — their `git diff main --stat`
shows those files as full deletions, i.e. those branches' history predates
several renames/restructurings already merged to today's `main`, not a live
edit conflict). Neither sibling branch's own diff is inspectable for
*uncommitted* changes from here (separate worktrees, separate working
trees) — the concrete mitigation, decided below, is to avoid editing
`domains/can_native_orchestration.py` at all and ship this rung's new code
as new, additively-named files only (`domains/graph_treewidth.py`,
`domains/can_junction_tree.py`, one new test file, two new docs). This
makes the eventual merge additive/conflict-free regardless of what the
siblings do to the existing orchestration file.

---

## 0. What this rung is

`CAN_SOLVER_TRACTABILITY_RESULTS.md` §2 measured (brute force, exact) that
Bigville's real per-resident CAN template
(`trust_mayor`/`claim_credible`/`world_safe`/`self_worth`/
`debtor_trustworthy`, `STRUCTURAL_EDGES`) has treewidth **2** — a triangle
(`trust_mayor`-`claim_credible`-`debtor_trustworthy`) plus a pendant path
(`trust_mayor`-`world_safe`-`self_worth`) — while the same rung's own
adversarial N=16 complete-graph stress case has treewidth **15** (worst
case, `N-1` by construction). That rung explicitly declined to build a
junction-tree solver ("out of scope, not sized here") but corrected the
"unreachable by construction" framing: *"junction-tree-exact inference is
not unreachable by construction for the graphs this project actually
deploys — it was never attempted, but nothing about their real topology
rules it out."*

This rung builds that solver. The existing toolbox has:

- the discrete-async native update (`can_native_update_3state`/`_2state`,
  proven convergent, but only to *a* stable state — an ICM-style local
  minimum of the pairwise+field Ising energy `mt_energy`, `can_ops.rs:327`);
- `multi_start_settle_and_pick_best` (`domains/can_native_orchestration.py`)
  — widens the search across `K` random restarts and keeps the
  lowest-*frustration* winner via an `Argmin` Term; still only a heuristic
  improvement, not a proof of global optimality;
- (a sibling rung, not this one) loopy-BP — approximate, general, no
  treewidth requirement, but not exact and known to lose convergence in
  frustrated/low-temperature regimes.

None of these is *exact*. Junction-tree inference over a low-treewidth
network is: for treewidth `w`, exact inference costs `O(n · |vocab|^(w+1))`
— genuinely tractable at Bigville's real `w=2` (bags of size ≤3, `3^3=27`
states per bag for the 3-state vocabulary) and a real, provable global
optimum, not a widened search.

---

## 1. What "exact" means here, precisely (registered before building)

The native discrete update's own local-field threshold rule reads, verbatim
(`seeds/can_native_reimplementation.json::can_native_update_3state`):
`local(c) = external_field(c) + identity_field(c) + Σ_e weight(e)·state(target(e))`,
compared against a temperature-scaled deadzone. This is literally
coordinate-wise ICM (iterated conditional modes) on the SAME energy
`can_ops.rs::mt_energy` already defines:

```
H(σ) = -Σ_{i<j} J_ij·σ_i·σ_j - Σ_i (h_ext_i + h_id_i)·σ_i
```

(`mt_energy`, `can_ops.rs:327-354`, confirmed by reading the function body —
field term first, then one pass over `enumerate_couplings`'s deduped
undirected pairs). **This rung's junction-tree solver targets the GLOBAL
minimum of this exact same `H(σ)`** — not `mt_frustration_given_state`
(`can_ops.rs:360-379`, which deliberately omits the field terms and is used
elsewhere in this arc only as a *comparison* metric across multi-start
candidates, not as the network's actual physical energy). Targeting the
same `H(σ)` the native dynamics already locally minimizes is the only
choice that makes "exact" a meaningful, apples-to-apples upgrade over the
existing ICM/multi-start tools — a solver that exactly minimizes a
*different* objective would not be comparable.

**Correctness proof design, registered now:** on a graph small enough to
brute-force literally (Bigville's real 5-node template, 3 states →
`3^5=243` total states — cheap to enumerate exhaustively), compute
`min H(σ)` two ways — (a) junction-tree message passing, (b) literal
enumeration of all 243 states via `substrate.mt_energy` — and require
BYTE-IDENTICAL (float-tolerance) minimum energy and an ENERGY-EQUAL state
(not necessarily identical state — a symmetric/degenerate network can have
several exact co-optimal states; the registered pass criterion is
`energy(junction_tree_state) == min(all brute-force energies)`, not state
identity). This is decided BEFORE running it, per house discipline.

**Honest-refusal design, registered now:** on the N=16 complete graph
(treewidth 15, already measured exact in `CAN_SOLVER_TRACTABILITY_RESULTS.md`
§2), the tool must (a) NOT attempt `3^16 ≈ 43M`-state exact enumeration or
`16!`-permutation exact treewidth search, (b) cheaply detect via the
min-fill heuristic upper bound that the graph is far over the treewidth
gate, and (c) return a clearly-marked non-exact refusal — no partial or
silently-approximate answer, no graph mutation.

---

## 2. Treewidth-bound strategy (registered)

`scripts/can_solver_tractability_measure.py::exact_treewidth` (read in
full before this doc was written) is **one-off script code**: a free
function inside a single-purpose measurement script, not imported by
anything else in the tree, no upper-bound path for graphs too large to
brute force (its own N=16 case is handled by a hand-written closed-form
`N-1` shortcut in the SAME script, not by the function itself). This rung
extracts and generalizes it into a real reusable module,
`domains/graph_treewidth.py`:

- `exact_treewidth(nodes, edges, max_exact_n=10)` — the SAME
  branch-and-bound brute force over elimination-ordering permutations
  (correct, not heuristic), gated to `n ≤ max_exact_n`. **Bound choice,
  reasoned before measuring:** `9!=362,880`, `10!=3,628,800` — both
  finish in low single-digit seconds in pure Python with the existing
  pruning (the original script's own 5-node/4-node/6-node/8-node runs were
  effectively instant; `8!=40,320` was the largest permutation count it
  actually ran). `max_exact_n=10` is chosen as the default cap — high
  enough to cover every REAL network this project has measured so far
  (Bigville's template is 5 nodes) with headroom, low enough that a caller
  who accidentally asks for exact treewidth on something N=16-sized gets a
  fast `None` instead of a multi-hour hang. This default will be measured
  for actual wall-clock cost at `n=10` in the RESULTS doc, not merely
  asserted.
- `min_fill_upper_bound(nodes, edges)` — greedy min-fill heuristic
  elimination ordering (standard chordal-graph triangulation heuristic),
  runs regardless of graph size, ALWAYS returns a valid (not necessarily
  minimum) elimination ordering and its induced width — a safe upper
  bound. This is the cheap gate a caller uses to decide whether to even
  attempt exact treewidth or junction-tree construction on an
  unknown-sized graph.
- The **elimination ordering itself** (from either function) is reused
  directly as the triangulation for junction-tree construction — a valid
  elimination ordering of width `w` IS a valid tree decomposition of width
  `w`, independent of whether `w` is the true minimum. Exactness of the
  final inference does not require the MINIMUM treewidth, only A CORRECT
  one — this is the standard textbook fact this rung's design leans on to
  avoid needing exact-minimum treewidth for large graphs at all: the
  min-fill heuristic ordering is enough to BUILD a correct (if possibly
  wider-than-necessary) junction tree; `exact_treewidth` is only needed to
  REPORT the true minimum width honestly when it's cheap to compute.

---

## 3. Junction-tree construction and message passing (registered)

Standard elimination-tree construction (Koller & Friedman shape, no
novelty claimed): given an elimination order, each eliminated node `v`'s
**bag** is `{v} ∪ (v's remaining neighbours at the moment v is eliminated)`
— one bag per original node (n bags total; no separate maximal-clique
merge pass, since a non-maximal bag does not break correctness of message
passing, only its efficiency, and every real network in this rung's scope
is small enough that the extra bags cost nothing measurable). Each bag's
**parent** in the tree is the bag of `v`'s remaining neighbour with the
smallest elimination index (the first later-eliminated neighbour) — this
is the standard elimination-tree construction, and its running-intersection
property is a textbook guarantee, not re-derived here.

**Potential assignment:** each unary term `h_i` is assigned to bag `i`
(always contains `i` by construction); each pairwise term `J_ij` is
assigned to whichever of `i`, `j` has the smaller elimination index (that
node's bag is guaranteed to contain the other, again by construction) — so
every term in `H(σ)` is assigned to exactly one bag, with no double
counting (mirrors `enumerate_couplings`'s own single-count-per-undirected-pair
discipline, `can_ops.rs:288-322`).

**Message passing (min-sum, exact on a tree — NOT loopy BP):** leaves
towards the root in elimination order — for each bag, minimize over its
own variable given each possible assignment to its separator with its
parent, folding in every child's already-computed message (whose separator
variables are, by the running-intersection property, always a subset of
the current bag's own variables). At the root (empty separator — the
last-eliminated node in a connected component has no remaining neighbours)
the minimum message value IS the global minimum energy. Backtracking
top-down (root to leaves, reverse elimination order) reconstructs one
globally-optimal full state. This is textbook exact inference over a tree
— the "NOT loopy, provably correct" property the task asks this rung to
demonstrate is a structural fact of running message passing on an
acyclic bag-tree, not a new algorithm.

---

## 4. Python-vs-Rust-Term design decision (registered, per house discipline
point 3)

**Decision: pure Python, no new Rust Term.** Reasoning:

1. Treewidth computation and junction-tree construction are graph
   algorithms over plain `(nodes, edges)` data — the SAME class of
   computation `can_solver_tractability_measure.py::exact_treewidth`
   already did in pure Python (and `measure_low_rank`'s SVD call), not a
   decision over LIVE agent/graph cognition state. `CLAUDE.md`'s
   prohibition targets Python that runs the rule engine, decides what to
   add to the graph via `if`/`else` over graph state, or holds agent
   state — none of which applies to computing an elimination ordering
   over a read-only snapshot of `(nodes, edges)` pairs.
2. The one place this DOES touch live graph state is (a) reading
   `external_field`/`identity_field`/`weight` off the real Concepts/edges
   (mechanical read, same shape as `native_marginal_from_state`), and (b)
   committing the winning state back via `set_attr` (mechanical write of
   an ALREADY-decided value, same shape as
   `multi_start_settle_and_pick_best`'s own final commit step). Both are
   precedented mechanical I/O, not new decision surface.
3. Building message passing as a NEW Rust Term (e.g. a `JunctionTreeSolve`
   Term operating on graph-resident bag/potential nodes) would be a much
   larger lift — new Term variants for tree-structured DP, new graph
   node/edge types (`Bag`, `has_separator`) with matching Γ productions,
   and a new evaluator loop — for a computation that has NO benefit from
   living in the Term algebra: it doesn't need `run_rules`' fixpoint
   (there's no repeated re-matching — one call, one exact answer), doesn't
   need to be re-triggered by graph mutations elsewhere, and doesn't need
   the admissibility grammar's generativity (it's a pure function of a
   read-only snapshot, not a decision about what the agent's graph is
   allowed to contain). Per `CLAUDE.md`'s own "When a new primitive is
   needed → Rust" section, the bar is "the existing DSL truly can't
   express something" — here the right characterization is "this
   computation doesn't belong in the DSL at all," the same conclusion
   `exact_treewidth`/`measure_low_rank`'s SVD already reached for their
   own math.
4. This composes with the task's own explicit hint: pure graph-algorithm
   work is "plausibly cleaner in Python... investigate and decide" — this
   is that investigation, concluded in Python's favour for the reasons
   above.

**Where the mechanical graph I/O happens (Python, precedented shape):**
`domains/can_junction_tree.py::can_network_from_mt` reads
`external_field`/`identity_field` (node attrs) and `causal_influence`
edges' `weight` attr via the SAME `Term("Edges", ...)` +
`Term("EdgeAttr", ...)` composition `domains/can_counterfactual.py` already
uses (confirmed live against a real Bigville resident network before
writing this doc — `Edges` returns `(src, edge_type, tgt)` tuples directly
usable for target-node extraction without a further `Nth` evaluate call;
`EdgeAttr` evaluate returns the raw float). No new Term needed for this
either.

---

## 5. Integration point (registered, per task's own explicit question)

**Decision: a new, separate, explicit opt-in module
(`domains/can_junction_tree.py`), NOT a new function bolted onto
`domains/can_native_orchestration.py`, and NOT automatic
treewidth-gated dispatch inside any existing entrypoint.** Reasoning:

1. **Toolbox framing, as the task itself frames it**: multiple tools, one
   per solving strategy, caller chooses. `can_native_orchestration.py`
   already hosts `scoped_settle` (bare ICM) and
   `multi_start_settle_and_pick_best` (widened ICM) as two DISTINCT
   callable functions in the SAME file because they share the "orchestrate
   the existing native rule, mechanical Argmin-decided selection" shape.
   Junction-tree inference shares NONE of that shape — it never calls
   `run_rules`/`scoped_settle` at all (it doesn't relax anything; it
   computes the optimum directly), so it is not a natural addition to that
   file's own internal coherence.
2. **Separate-file-per-capability is this arc's own existing precedent**:
   `can_counterfactual.py`, `can_native_hebbian_bridge.py`,
   `reasoning_can_bridge.py` are all standalone CAN-capability modules,
   not folded into `can_native_orchestration.py`. A new exact-inference
   tool fits that precedent as its own file.
3. **Collision avoidance (house discipline point 2)**: two sibling
   worktrees already touch CAN files this session. A new file has zero
   merge-conflict surface with any concurrent edit to
   `domains/can_native_orchestration.py`; a new function inserted into
   that file would not.
4. **Automatic dispatch is explicitly rejected**: silently swapping
   solving strategies inside an existing entrypoint based on a computed
   treewidth would hide a genuinely different GUARANTEE (exact vs.
   heuristic-widened) behind one call site, and would silently change
   behaviour for every existing caller of `multi_start_settle_and_pick_best`
   the moment their network happened to cross the bound — a correctness
   surprise, not a toolbox. The caller who KNOWS (or cheaply checks) their
   network is low-treewidth gets a strictly stronger guarantee by opting
   in explicitly; a caller who doesn't check keeps the existing behaviour
   unchanged. `junction_tree_exact_settle`'s own internal treewidth check
   is a SAFETY REFUSAL (don't attempt exponential work blindly), not a
   dispatcher to a different algorithm.

---

## 6. GO/NO-GO criteria (registered before running)

- **GO** iff: (a) `exact_treewidth` on Bigville's real 5-node template
  reproduces treewidth 2 (a re-derivation check, not a new claim — this
  number is already measured in `CAN_SOLVER_TRACTABILITY_RESULTS.md` §2);
  (b) junction-tree MAP energy on that same network matches literal
  243-state brute-force minimum energy, exactly, on ≥3 independently-built
  real resident networks (not just one, to guard against a single lucky
  coincidence); (c) the tool honestly refuses (no attempted computation,
  no graph mutation) on the N=16 treewidth-15 network under a default
  bound that Bigville's own treewidth clears; (d) all named regression
  files stay green.
- **NO-GO / partial** iff any brute-force cross-check disagrees with the
  junction-tree result on ANY of the ≥3 tested networks, or the refusal
  path silently attempts exponential work instead of refusing.

---

## 7. What this rung will NOT establish (registered in advance)

1. Whether junction-tree inference, once built, changes any DEPLOYED
   Bigville behaviour — this rung builds and proves the tool; wiring it as
   the DEFAULT solving path for any real caller is a separate, unbuilt
   decision (§5 above explicitly keeps it opt-in).
2. Treewidth for any CAN network other than the two already measured
   (Bigville's 5-node template, the N=16 synthetic stress case) — this
   rung's own correctness proof re-uses those two, it does not sweep new
   topologies.
3. Whether the min-fill heuristic upper bound is TIGHT on graphs between
   these two extremes — untested here, out of scope (the two real
   endpoints this project has are treewidth 2 and treewidth 15; nothing in
   between has been measured or is known to exist as a real deployed
   network).
4. Marginal (sum-product, Gibbs-weighted) inference — this rung targets
   the MAP/global-optimum state (§1's registered target), matching the
   "prove exactness against the BEST state" framing the task and the prior
   rung's own "not the BEST one" language both use. Exact marginals under
   a Boltzmann distribution at the Mt's own `temperature` are a real,
   separate, unbuilt extension.
