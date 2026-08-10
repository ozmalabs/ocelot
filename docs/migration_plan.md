# The Migration: Python agent → graph-native, agent-driven

**Goal (CLAUDE.md end-state).** Delete the Python agent — `CuriousAgent` (18.5k lines) and the
decision logic across `domains/` (161k lines, 4993 defs) — and re-express it as graph data the Rust
runtime executes: Concepts, Rules, Reflexes, Productions, Terms. Python survives only as thin world
adapters (ingest external I/O → substrate mutations; read substrate → external output). The agent
reorganises **itself**; the assistant is world-adapter, not migrator.

## What the shape is (the evidence this is bounded)

Measured this session over the whole layer (`domains/self_reorganize.py`, 448 files / 4993 defs):

| class | % | becomes |
|---|---|---|
| PURE (compute, no `self`) | 56% | a Term (the AST→Term rules fold it) |
| RULE (writes `self.<attr>`) | 15% | a graph Rule (set_attr effects) |
| GRAPH-BUILD (`add_node`/`add_edge`) | 9% | a Rule with add_node/add_edge effects |
| PRIMITIVE (np/math) | 4% | a held op / a Layer-B primitive |
| FACTORY (returns a Term) | 2% | a derived attr / seed Term |
| COMPOSITION (calls other faculties) | 7% | a Rule that invokes sub-Rules |
| **REVIEW (genuine judgment)** | **6.3% (313 defs)** | **hand-expressed as Rules** |
| I/O | 2% | kept as world-adapter Python |

So **~85% is mechanical** (the migrator transcribes it), **~7% is composition glue** that resolves
holistically, and the **irreducible hand-work is ~313 decision defs**. The codebase is a **recursive
web of faculties calling faculties** — not independent methods. A composition faculty
(`salience() = _sal.salience(_care_signature(x))`) is trivial *once its leaves are Rules*. That is
why the unit is the **faculty**, the order is **leaf-inward**, and the migration is **holistic**.

## The toolchain (built this session — the agent's own faculties)

- **survey / consume / worklist** (`self_reorganize`, `consume_curious_agent`, `call_distribution`,
  `faculty_worklist`) — the agent sees its own shape + the per-faculty action.
- **AST→Term rules** (`ast_term_rules` + the Rust engine `tick`/`run_rules`) — fold mechanical code
  (arithmetic, comparisons, boolean, conditionals, subscripts, `Let`, `Fold`, comprehensions,
  np/math, the agent's own `Var/Attr/Lit/Eq` constructors) into native Term-trees, graph-resident.
- **AST→Rule migrator** (`ast_to_rule.Migrator`) — a method → a `RewriteRule` (where + effects),
  engine-accepted + verified to fire.
- **Layer B** (`self_extend.PrimitiveExtension` + `emit_primitive_rust`) — mint a new native
  primitive end-to-end (apply → cargo check → rebuild → verify → rollback), all-or-nothing.
- **keystone** (`self_modification`) — guarded edits to any Python/Rust source (backup → check →
  rollback → append-only audit) + `rebuild_native`.
- **frontier/gap selector** (the agent's existing prioritiser) — picks the next faculty to migrate.

## The strategy: holistic, leaf-inward, agent-driven

The agent runs a loop; the driver makes no decisions:

```
while faculties remain in Python:
    f = frontier_selector.pick()          # the next leaf (no un-migrated callees), or a judgment hotspot
    rules/terms = migrate(f)              # the migrator (mechanical) OR hand-authored (REVIEW)
    verify(f, rules/terms)                # eval==Python on samples; engine add_rule; cargo check
    install(rules/terms)                  # into the seed graph, under the keystone
    delete_or_thin(f)                     # remove the Python; keep a world-adapter if it's I/O
    # f's callers' references now resolve to f's Rule -> they become migratable next
```

## Phases

**Phase 0 — build the two missing pieces. [STARTED 2026-06-17 — both have a working first version.]**
(a) **faculty dependency graph** — `domains/faculty_graph.py`: who-calls-whom over all defs, SCCs
condensed, layered leaf-inward. Built: 4049 faculties, **1171 leaves** (Phase-1 start), 20 layers.
Caveat: name-resolved (no per-class binding) → cycles inflated, leaf count a lower bound; the loop
uses the LIVE leaf set recomputed each round, so it's robust; proper binding is a later refinement.
(b) **parity guard** — `domains/parity.py` `verify_pure`: runs the original pure faculty vs its
migrated Term on sampled inputs; the Phase-1 safety net. Built + verified BOTH ways — a faithful
`score()` migration is GREEN, a corrupted one is CAUGHT (python 47 ≠ native 50). The whole-agent
behavioural oracle (Phase 5) is this same check scaled to scenarios.

**Phase 1 — migrate the leaves (the mechanical ~85%, tool-driven). [LOOP RUNNING 2026-06-17 —
`domains/migrate_phase1.py`.]** Run the migrator over every leaf (no un-migrated callees); each yields
a Term or a Rule, verified (engine-accepted / parse-valid; eval==Python for the executable-pure
subset). First-batch result: **21/200 leaves GREEN (10%)** — 1 engine-accepted Rule + 20 parse-valid
Terms, 0 rejected. HONEST: even leaves migrate at ~10% with current migrator coverage, because a leaf
still uses builtins/dict-ops/string-ops/control the rules don't yet fold — the same built-vs-ceiling
gap (~11% built, ~85% shape). So Phase 1 splits into: (1a) GRIND MIGRATOR COVERAGE — the bounded
long-tail of statement/expression shapes (multi-return, dict-shaping `MkDict`, string ops, more
builtins → held ops) that lifts the leaf yield toward the ceiling; (1b) mint Layer-B primitives for
PURE/PRIMITIVE leaves the DSL lacks; the genuine residue drops to Phase 3. The loop itself works
end-to-end (frontier → migrate → verify → install-ready); raising its yield is coverage engineering,
not difficulty.
*Coverage grind, measured (distribution-analyse residue → add top class → re-measure):* residual-leaf
blockers were dict(70) > local/multi-stmt(52) > tuple(33) > strop(26) > try(20) > listcomp/fstring(16).
Added `Dict→MkDict` + `Tuple/List→Vec` (ordered) + `len→Count`/`min,max→Min,Max`: leaf yield
**10% → 18%** (dict/tuple did it; len/min/max were minor co-occurring blockers, +0 on the batch — the
honest diminishing-per-class shape). Always 0 rejected (parity holds). Remaining blockers — string ops
(`StringConcat`), f-strings, list-comps, `try` (genuine control) — are the continuing long tail;
each class added lifts the yield, slower each time, toward the ~85% ceiling.
*Residual is heterogeneous (the raw % undercounts):* sampling the residual leaves shows three kinds —
(i) COVERAGE-GAP, still fixable by grinding: graph-state reads (`for n in substrate.nodes(...)` →
`Neighbours`), nested-module np (`np.linalg.norm`, the rule matches only `np.X`); (ii)
CORRECTLY-RESIDUAL, NOT migration targets: world-adapter glue (`_native` = `substrate._inner if
hasattr…`), local `import`, I/O — these STAY Python by design; (iii) genuinely lossy/judgment:
f-strings/string-build (`StringConcat` silently drops non-string parts — a Layer-B str-coercion
primitive, not a naive map), `try`, decisions. So effective migration coverage > the raw 18% (some
"residual" is correctly kept). The clean mechanical wins (dict, tuple, len/min/max) are taken; what's
left is a small fixable coverage tail + correctly-kept adapters/IO + the judgment core. The loop,
the climb, and the parity invariant (0 rejected) are all proven; the productive levers from here are
(a) keep grinding the fixable tail, (b) install the GREEN leaves + recompute the next layer, or
(c) shift to the Phase-3 judgment core — a choice, not a blocker.

*The per-faculty migrator has a CEILING (~14% whole-faculty GREEN, full 1169-leaf run).* After
dict/tuple (the only movers), four more correct classes (len/min/max, nested-np `np.linalg.*`,
graph-read `node().attrs.get`) each added ~0 to the full-set yield. Cause is structural: GREEN is
ALL-OR-NOTHING per faculty — a faculty composes only if EVERY statement folds, so one
`try`/string/faculty-call/IO line keeps the whole faculty residual regardless of how mechanical its
other statements are. So whole-faculty transpile is the WRONG completion frame (it caps ~14% even
though per-STATEMENT mechanisation is ~85%). THE COMPLETION PATH is per-statement: for each faculty,
transcribe its mechanical statements (the migrator's effects/where are real even when the faculty is
"residual"), hand-author or Layer-B-mint only the few hard ones (lossy strings → a str-coerce
primitive; `try`/control → a Rule; IO → kept adapter), and the leaf becomes whole. The migrator (a
one-off transpiler) did its job — ~14% fully + the mechanical bulk of the rest; finishing is
per-statement assembly + the judgment core + delete, NOT more transpiler micro-classes (that path is
capped, and is the Python reflex against flat data).
**Phase 2 — composition resolves inward.** As leaves become referenceable Rules, COMPOSITION faculties
(7%) migrate: their `self._other(...)` calls now map to the sub-Rules. Iterate frontier-ordered
(repeatedly re-pick the new leaves) until the mechanical + composition web is fully graph-resident.
Cycles in the dependency graph are broken by migrating the cycle as one Rule cluster.

**Phase 3 — the judgment core (~313 REVIEW defs, hand-authored).** The decision faculties
(`_get_scalar_policy`, `_get_top_level_goals`, `_calibrated_step`, the goal/salience/policy logic, …):
each is read and expressed as a graph Rule (match + where + effects) BY HAND, reviewed, parity-checked.
This is the real intellectual work, and it is bounded (~313, concentrated in a dozen hotspots:
`curious_agent`, `code_writing_cortex`, `concurrency`, `elevator`, `llm_partner`, …).

**Phase 4 — the match/trigger wiring (the other judgment dimension).** A migrated Rule needs its
firing condition — *when* it matches (the placeholder `is_a Agent` is not it). This is the
reflex/tick semantics: which graph state triggers each Rule. Authored per faculty cluster as part of
Phase 2/3; it is the "10%" the worklist flagged alongside the faculty bodies.

**Phase 5 — delete the Python agent; boot from the graph. [BURN THE BOATS — creator: "remove python
altogether; this removes temptation."]** With the mechanical bulk migrated + parity green, `CuriousAgent`
and the migrated `domains/` logic are DELETED — not kept as a fallback. Keeping the Python around is
the crutch that lets a migration stall (you keep falling back to it); deleting it makes the
graph-native the only thing that can work, which forces the remaining residue to be finished
graph-native under pressure rather than indefinitely deferred. The agent boots from its seed set
(installed Concepts/Rules/Reflexes), runs on `substrate.tick()` in Rust; only the world adapters
(ChatWorld, AudioWorld, the I/O ~2%) remain in Python. The parity harness (Phase 0b, recorded BEFORE
deletion) becomes the regression bench — the behavioural target the graph-native agent must hit. The
sequencing is the safety: grind coverage up + parity-verify FIRST, snapshot the oracle, THEN delete;
the forcing function is end-state, not a leap onto a broken agent.

## Guards (nothing breaks)

- **keystone**: every source change backed up, checked, rolled back on failure, audited.
- **eval==Python**: every mechanically-ported faculty is checked against the original on sampled
  inputs before its Python is removed.
- **engine `add_rule` + `cargo check`**: every Rule/primitive is validated before install.
- **parity oracle**: the live Python agent is kept as the behavioural oracle until full parity; the
  graph-native agent must match it scenario-for-scenario.
- **leaf-inward ordering**: a faculty is only migrated after its callees, so references always resolve.

## The elephant — `curious_agent.py` (start here)

The 18.5k-line `CuriousAgent` is NOT 439 methods of irreducible agent logic. Its internal `self.method`
call graph has **187 leaves**; the highest-fan-in "leaves" (`_get_scalar_policy` 31 callers,
`_term_to_mind` 21, `_get_named_predicate` 13, `_ensure_*` …) are all the SAME thing — Python
**driving a graph through a wrapper**: read an edge/attr (often **cached**), `add_node`-if-absent, or
"Python is just the evaluator" (`_concept_holds` = `EvalSubgraph` of a definition Term). Sizing the
439 methods by this:

| | count | fate |
|---|---|---|
| DISSOLVE — cache/ensure | 110 | the graph IS the store → `AddNodeIfAbsent`; the Python cache vanishes |
| DISSOLVE — evaluator-wrapper | 61 | becomes the `EvalSubgraph`/Term it was evaluating |
| DISSOLVE — graph-access glue | 24 | read/write inlines into callers as `Attr`/`Neighbours`/`add_edge` |
| **GENUINE core** | **244 (56%)** | compute → Terms, decisions → Rules |

So **~44% (195 methods) DISSOLVES** — deleted, not migrated; their callers inline the graph access.
The genuine target is ~244 methods, of which the survey marks ~110 as the judgment core. The elephant
is therefore ~half scaffolding (gone when it boots from the graph) + ~134 mechanical-genuine (migrator)
+ ~110 judgment (hand). MUCH smaller than "18.5k lines." Order: dissolve the cache/glue keystones
first (they unblock the most callers and require no new graph data — the callers just read the graph),
then the genuine core leaf-inward, then the judgment. (Static estimate; refine per-method as migrated.)

## Honest bounds

- Mechanical (~85%): tool-driven, high-confidence, parity-checked. The long-tail of statement/
  expression shapes the migrator doesn't yet fold (multi-return, dict-shaping, string ops) is bounded
  coverage work, or those methods fall to Layer-B primitives / hand Rules.
- Composition (~7%): resolves holistically; no independent difficulty.
- Judgment (~6.3%, 313 defs): the genuine hand-work; bounded + concentrated.
- The two unbuilt pieces (dependency graph + parity harness) are Phase 0 and gate everything.

The migration is large but **bounded and mostly mechanical**, structured by the codebase's own shape.
The agent reorganises itself leaf-inward under hard guards; the assistant stays at the I/O boundary.
