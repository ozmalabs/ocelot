# A real analogy-shaped sentence adapter for `solve_analogical_promote` — PREREG

Base `main @ dae5fbe` ("Merge solver-nl-adapter: first NL adapter for the six
unwired solve_* resolvers, GO"), verified via `git log --oneline -1 main`
immediately before creating this worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-analogy-adapter`, branch
`solver-analogy-adapter`.

## 0. What this task is checking

`SOLVER_NL_ADAPTER_RESULTS.md` §1 ranked `solve_analogical_promote` #2 of
six unwired resolvers, with the stated reason: *"there is no existing parser
anywhere in the tree for an analogy-shaped sentence ('X is like Y'/'X
corresponds to Y') — that half is genuinely new, unbuilt parsing work, not a
reuse."* That rung's own §2 grep was `analog*`/`correspond*` against
`seeds/reading_constructions.json` — it stopped at zero hits on those two
word-stems and moved on to build the cheaper `solve_reasoning_bridge`
adapter instead, exactly as its own task scope required ("build exactly
one, the cheapest"). This task's job is to check that specific claim more
carefully, the way `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` re-checked
`Sort`/`SetMap` and found them pure reuse where an earlier pass had assumed
new work.

**The grep was too narrow, and the claim does not survive a broader one.**

## 1. What `solve_analogical_promote` requires — read directly off the code

`domains/solver_dispatch.py:306-316`
(`mint_solve_analogical_promote_goal`) requires a `corr_node` — an
already-recorded `DirectionalCorrespondence` node, wired via a
`targets_correspondence` edge — before a Goal can even be minted; the
resolver itself (`domains/solver_dispatch.py:564-592`) does nothing but
read that node's own already-decided direction
(`analogical_thinking.directional_hypothesis_for`) and promote it
(`propositional_deduction.mint_logical_schema_from_analogy`), both
UNCHANGED, unedited existing functions.

A `DirectionalCorrespondence` is built by
`analogical_thinking.record_directional_correspondence(substrate, node_a,
node_b, vec_a, vec_b, witness)` (`domains/analogical_thinking.py:699-737`),
which needs:

- `node_a`, `node_b` — two REAL `Concept` graph nodes;
- `vec_a`, `vec_b` — `_concept_shape_vector(substrate, node)` output for
  each (`analogical_thinking.py:434-457`) — a MECHANICAL, pure function of
  an already-resolved Concept node, zero new capability;
- `witness` — `_pair_witness(substrate, vec_a, vec_b)` output
  (`analogical_thinking.py:460-507`) — the held `AntiUnifyWitness`/
  `FixedCount` Rust Terms over the two vectors, MECHANICAL, zero new
  capability.

**The entire chain from two resolved Concept nodes to a promoted,
inspectable `knowledge_logical` schema is already fully mechanical, unedited,
and load-bearing-tested** (`DIRECTIONAL_CORRESPONDENCE_RESULTS.md`,
`tests/test_directional_correspondence.py`, 11/11 green on `main` today).
The ONLY genuinely open question, exactly as the prior rung identified, is:
**can two Concept NAMES be extracted from a real sentence with an analogy
cue, and resolved to two real Concept nodes?**

## 2. Does an analogy-shaped construction already exist in the reading
   pipeline? — checked by grep on the RIGHT words, then confirmed live

`grep -niE '"like"|similar|comparative' seeds/reading_constructions.json`
(not the prior rung's `analog*`/`correspond*` grep, which was searching for
the WRONG surface vocabulary — English does not lexicalise analogy with the
morpheme "analog", it lexicalises it with "like"/"resemble"/"similar")
finds, already seeded, already wired into `_skeleton_from_words`, already
consumed by `read_clause` with **zero code in this rung touching them**:

```
local_id 6:  MarkerClass{cls:"LIKE", forms:["like","resembles","resemble"]}
local_id 46: ShapeSignature{name:"comparative_unlike",     predication:"contrast", signature:[["UNLIKE"]],        ground_template:{pred:"contrast",mode:"pair"}}
local_id 146:ShapeSignature{name:"comparative_unlike_cop",predication:"contrast", signature:[["COP"],["UNLIKE"]],ground_template:{pred:"contrast",mode:"pair"}}
local_id 47: ShapeSignature{name:"comparative_like",       predication:"similar", signature:[["LIKE"]],           ground_template:{pred:"similar",mode:"pair"}}
local_id 147:ShapeSignature{name:"comparative_like_cop",  predication:"similar", signature:[["COP"],["LIKE"]],   ground_template:{pred:"similar",mode:"pair"}}
```

**Confirmed live** (`WorldAdapter(seeds=()); load_all_seeds(a)`, a full
standing boot, no seed edited), against real sentences using real corpus
vocabulary (`mathematics` Mt: `generating_functions`, `function_definition`
— the SAME concept pair `DIRECTIONAL_CORRESPONDENCE_RESULTS.md` §4.1 already
demonstrated has real structural correspondence):

```
"Generating functions are like a function definition."
  -> construction: comparative_like_cop, speech_act: statement
  -> predications: [['similar', 'generating_functions', 'function_definition']]

"Generating functions resemble a function definition."
  -> construction: comparative_like, speech_act: statement
  -> predications: [['similar', 'generating_functions', 'function_definition']]

"Generating functions are unlike function definitions."
  -> construction: comparative_unlike_cop, speech_act: statement
  -> predications: [['contrast', 'generating_functions', 'function_definitions']]

"Is a generating function like a function definition?"
  -> construction: comparative_like_cop, speech_act: question
  -> predications: [['similar', 'generating_function', 'function_definition']]

"Generating functions are important."   (no comparative cue)
  -> construction: definitional, speech_act: statement
  -> predications: [['is_a', 'generating_functions', 'important']]
```

**`"X is like Y"` / `"X resembles Y"` already ground, via the UNMODIFIED
general reading pipeline, to exactly `["similar", subject, object]`** — the
`pred` name the construction seed already calls `"similar"`, byte-identical
to the word an analogy-shaped sentence adapter would need. `"X is unlike
Y"` grounds to `["contrast", ...]`, the honest opposite signal (a
dissimilarity assertion, correctly distinguishable from an analogy claim by
relation label alone). A question-shaped comparative correctly carries
`speech_act:"question"` (same gate precedent `SOLVER_NL_ADAPTER_RESULTS.md`
already established for `solve_reasoning_bridge`). **This directly refutes
the prior rung's "no analogy-shaped sentence parser exists anywhere in the
tree" finding** — one existed already, seeded, wired, and functional; the
prior rung's grep for `analog*`/`correspond*` simply never found it because
those are not the words English analogy sentences use.

**A known, honest limitation found live, not glossed over:** `"X is
similar to Y"` (the OTHER common analogy phrasing, using the adjective
"similar" + "to" rather than the `LIKE` marker class's own
`like`/`resembles`/`resemble` forms) does **not** trigger the comparative
construction — it falls through to the ordinary `definitional` construction
and mis-grounds as `is_a(X, "similar")`, silently dropping Y entirely. This
is a REAL parser gap (a second comparative surface form the seed's `LIKE`
marker class does not cover), sized and named in §5 as a follow-on, NOT
patched here — the adapter this rung builds must gate on `rel == "similar"`
(the correctly-grounded case) and will therefore correctly ignore this
particular mis-grounding rather than mistake it for a valid pair (subject
`generating_functions`, "object" `"similar"` is not a real Concept name and
will fail resolution honestly, see §4).

## 3. Concept-name resolution — does composable, mechanical reuse exist?

**Checked, not assumed.** `domains/neuroscience_tagging.py:138-144`
(`_find_concept_by_name`) is an EXISTING, unedited, already-shipped
mechanical helper: `for c in substrate.nodes("Concept"): if
attrs["name"]==name: return c` — a global scan across every `Concept` node
in the graph, regardless of which `Microtheory` holds it. This is the exact
shape needed (a bare name string -> a real Concept node), already reused
verbatim across ~15 call sites in that one file, following the SAME
"same pattern, own cache — no cross-import" house convention
`analogical_thinking.py`'s own module comment documents for
`_agent_node_id`/`_resolve_blob_edge`.

**A real hazard, checked live, that this convention's OWN precedent (return
the first match) does not handle:** `Concept` is a heavily-overloaded node
type (CAN belief-network propositions AND domain-vocabulary corpus terms
share one type tag — confirmed already by `ENTITY_RESOLUTION_RESULTS.md`
§1). On a full `load_all_seeds()` boot:

```
total Concept nodes: 10777, distinct names: 10157, duplicated names: 507
e.g. 'agent'(x3), 'patient', 'theme', 'instrument', 'source', 'goal', 'manner', ...
generating_functions -> 1 (unique)
function_definition  -> 1 (unique)
```

A naive first-match lookup would silently pick an arbitrary one of several
same-named Concepts for 507 real names in the standing corpus — the SAME
failure mode `ENTITY_RESOLUTION_RESULTS.md` §3/§4 already found and fixed
for `SmEntity<->Microtheory` resolution (the real "Peaseblossom" surname
shared by 4 residents) via an explicit ambiguity REFUSAL, not a silent
guess. Live-confirmed real sentence that would hit this: **"The agent is
like the patient."** grounds cleanly (`['similar','agent','patient']`,
`agent` has 3 real Concept-node matches in the standing corpus) — a
genuinely reachable ambiguity case, not a hypothetical.

**Design decision, and why it stays Python, not a Rule (checked against
CLAUDE.md's own axis, not glossed over):** `ENTITY_RESOLUTION_RESULTS.md`
pushed ITS OWN ambiguity guard into a graph Rule
(`seeds/entity_concept_correspondence.json`) because that rung was building
a STANDING, reusable, graph-persisted correspondence
(`SmEntity -denotes-> Microtheory`) that other future queries should be able
to read back without re-deriving it — a genuine case of "shape is
acquisition," a fact the graph should hold. This adapter's own name
resolution is different in kind: it is a ONE-SHOT lookup local to a single
adapter invocation translating one sentence's two surface tokens into two
node references, the SAME mechanical shape `reasoning_can_bridge.
_find_concept_by_name`, `neuroscience_tagging._find_concept_by_name`,
`propositional_deduction._schema_by_name`, and `analogical_thinking.
_find_mt` ALL already are — unedited, accepted, standing Python helpers
performing an EXACT-match graph query, not an agent decision about what to
believe or do. The ambiguity check (`len(hits) != 1 -> decline`) is the
SAME category of shape-gate the two prior NL-adapter rungs already used in
Python (`_is_property_pred`, the `speech_act=="question"` gate) — an
adapter refusing to proceed on unsuitable/underdetermined input, not a
decision over the agent's own beliefs. No Rule is added for this reason;
this is registered explicitly so the choice is checkable, not silent.

## 4. Live, end-to-end confirmation — BEFORE finalising the ranking,
   mirroring `SOLVER_NL_ADAPTER_PREREG.md` §3's own discipline

Run against a real `WorldAdapter` boot (`load_all_seeds`), zero seed edits,
zero code changes, using ONLY existing, unedited functions
(`reading_collapse.read_clause`, a local copy of the `_find_concept_by_name`
scan, `analogical_thinking._concept_shape_vector`/`_pair_witness`/
`record_directional_correspondence`/`directional_hypothesis_for`,
`solver_dispatch.mint_solve_analogical_promote_goal`,
`solver_dispatch.solve_analogical_promote`):

```
"Generating functions are like a function definition."
  -> predications: [['similar', 'generating_functions', 'function_definition']]
  -> node_a = Concept#2075 (generating_functions, 1 match), node_b = Concept#2009 (function_definition, 1 match)
  -> vec_a/vec_b via _concept_shape_vector (mechanical)
  -> witness = _pair_witness(vec_a, vec_b): fixed_count=82, shared=1 axis
  -> record_directional_correspondence -> DirectionalCorrespondence#24361
  -> directional_hypothesis_for -> {direction:'a_source', source_concept:'generating_functions',
       target_concept:'function_definition', confidence:{richness_a:3, richness_b:2, ...}}
  -> mint_solve_analogical_promote_goal(adapter, corr) -> Goal minted
  -> solve_analogical_promote(adapter, goal) [UNCHANGED resolver]
  -> goal.status == 'resolved'
  -> goal.answer == 'logical_analogical_generating_functions_function_definition'
```

Re-run twice, byte-identical (deterministic): `richness_a=3, richness_b=2`
both times.

**Honest resolver-side wall, found live** (not merely asserted possible):
two real, GLOBALLY-UNIQUE concept names with TIED richness —
`"myelination"` (richness 7) and `"temporal_difference_learning_formal"`
(richness 7, both real `neural_networks`/`machine_learning` Mt vocabulary,
`neuroscience_tagging.py`'s own `NEUROSCI_LINKS` table) —

```
"Myelination is like temporal difference learning formal."
  -> predications: [['similar', 'myelination', 'temporal_difference_learning_formal']]
  -> node_a (1 match), node_b (1 match) -- both unambiguous
  -> directional_hypothesis_for -> {direction: 'symmetric', richness_a:7, richness_b:7}
  -> solve_analogical_promote -> status:'walled', direction_verdict:'symmetric',
     note: "correspondence direction is 'symmetric' -- not resolved (only
     a_source/b_source are promotable); an undirected correspondence names
     no antecedent, nothing fabricated"
  -> gap_key: 'solve_analogical_promote:corr=#...' filed (Rung 2's
     note_solve_exhausted_gap, unchanged, fires correctly)
```

This is the SAME resolver-side honest-wall shape
`SOLVER_NL_ADAPTER_RESULTS.md` §4.2 demonstrated for `solve_reasoning_
bridge` — reached here with ZERO changes to `solve_analogical_promote`
itself, confirming the resolver's own existing wall path composes for free
with a text-driven `corr_node`.

**Honest adapter-side declines, confirmed live, mint nothing:**

```
"Generating functions are unlike function definitions."      -> rel="contrast", not "similar" -> decline
"Is a generating function like a function definition?"        -> speech_act=="question" -> decline
"Generating functions are important."                         -> rel="is_a", no comparative cue -> decline
"The agent is like the patient."                               -> 'agent' has 3 Concept matches -> decline (ambiguous)
"Generating functions are like a completely_unknown_bogus_concept_xyz." -> object name resolves to 0 Concepts -> decline
""  /  "   "                                                    -> empty statement -> decline
```

## 5. Ranking, revised with real evidence — `solve_analogical_promote` is
   NOT "moderate cost, real unbuilt parsing work." It is cheap, once the
   right vocabulary is grepped for.

| resolver (direction) | prerequisite | reuse found? |
|---|---|---|
| `solve_reasoning_bridge` (`deduction_to_can`) | two bare strings | total (built, `main@dae5fbe`) |
| **`solve_analogical_promote`** | one comparative-cue sentence -> two Concept-node refs | **total — comparative construction ALREADY SEEDED (§2); concept-name lookup ALREADY AN ESTABLISHED PYTHON IDIOM (§3); the correspondence-recording half was already known mechanical (`SOLVER_NL_ADAPTER_RESULTS.md`'s own finding, unchanged)** |
| `solve_decompose` | staged candidate list | none independent — inherits CAN/deduction cost |
| `solve_can_relax`/`solve_can_exact`/`solve_can_bp` | full CAN belief network | none — genuinely new causal-extraction-from-prose capability |

The one genuinely NEW piece of work this adapter needs beyond pure
composition is a ~10-line local `_find_concepts_by_name` scan (copying the
already-precedented idiom, per §3) plus the ambiguity-count gate — smaller
than `solve_reasoning_bridge`'s own adapter, which additionally needed a
speech-act gate AND a property-predication gate. **This was mis-ranked by
the prior rung not because the underlying facility was actually expensive,
but because the discovery grep used the wrong search terms** — exactly the
class of correction `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` names for
`Sort`/`SetMap`, and precisely what this task asked to re-check.

## 6. What will be built

`mint_solve_analogical_promote_goal_from_text(adapter, statement)` in
`domains/solver_dispatch.py`, immediately after the existing `mint_solve_
analogical_promote_goal` it composes with (mirroring where `mint_solve_
reasoning_bridge_goal_from_text` was placed relative to its own hand-built
counterpart):

1. Decline on empty/whitespace statement.
2. `whole = rc.read_clause(adapter, statement, write=False, learn=False)`.
3. Decline on `speech_act == "question"` (identical gate precedent).
4. Decline on no predication, or leading predication relation != `"similar"`
   (excludes `"contrast"`/`"is_a"`/any transitive-event relation — the ONE
   relation label this adapter's downstream machinery, `_pair_witness`, is
   correctly interpretable for: undirected structural similarity, never a
   dissimilarity or an unrelated property).
5. Resolve `subject`/`object` via a local `_find_concepts_by_name` scan
   (the §3 idiom); decline unless BOTH resolve to EXACTLY ONE Concept node
   each (covers "not found" and "ambiguous" in one check).
6. Decline if the two resolved nodes are identical (`node_a == node_b`,
   mirroring `_compute_analogy`'s own `if sn == tn: return None` guard,
   `analogical_thinking.py:1000` — "same concept; not an analogy").
7. Compute `vec_a`/`vec_b` (`_concept_shape_vector`, unedited) and `witness`
   (`_pair_witness`, unedited).
8. `record_directional_correspondence` (unedited) -> `corr_node`; decline if
   it returns `None` (defensive — matches that function's own documented
   honest no-op).
9. Return `mint_solve_analogical_promote_goal(adapter, corr_node)` — the
   UNCHANGED existing entry point, dispatching through the UNCHANGED
   `qd_bind_resolver` -> `solve_analogical_promote` exactly as every other
   caller.

**Not touched**: `solve_analogical_promote`'s own internals, `analogical_
thinking.py` (zero edits — every function it calls is read-only reuse),
`propositional_deduction.mint_logical_schema_from_analogy`, `seeds/
directional_correspondence.json`, `seeds/reading_constructions.json`. Pure
addition, mirroring the diff shape `SOLVER_NL_ADAPTER_RESULTS.md` §6
reported for its own rung.

**Named, NOT built here (a real, separate follow-on):** the `"X is similar
to Y"` (adjective+"to") comparative surface form does not ground correctly
today (§2) — a second `MarkerClass`/construction pair for that phrasing is a
genuinely new reading-pipeline addition (closer to a `seeds/reading_
constructions.json` edit than a thin adapter), out of this rung's scope per
the task's own instruction to build only what composes with EXISTING
machinery.

## 7. GO/NO-GO leaning

**GO**, with the scope precisely bounded: this adapter handles ONLY the
`LIKE`-marker-class comparative surface forms already seeded
(`like`/`resembles`/`resemble`, both copular and verbal), a single leading
predication, exact concept-name match, and an explicit ambiguity refusal —
the SAME honest, narrow-boundary shape both prior NL-adapter rungs shipped
(`solve_reasoning_bridge`'s exact-attr-match boundary;
`solve_reasoning_bridge`'s single-predication scope). The broader "similar
to" phrasing and any semantic (non-exact-name) concept matching are named,
sized follow-ons, not silently assumed solved.

## 8. Regression plan

`tests/test_solver_dispatch_migrated.py`, `tests/test_solve_gap_awareness_
migrated.py`, `tests/test_problem_shape_migrated.py`, `tests/test_solver_
math_boundary.py`, `tests/test_solver_nl_adapter.py`, `tests/test_
directional_correspondence.py`, plus a new `tests/test_solver_analogy_
adapter.py` for this rung's own live demonstrations — all green, fresh
(not from `results/failure_baseline.json`), before declaring GO final. An
adjacent sweep (`tests/test_blob_edge_analogy_extension.py`, `tests/test_
analogical_relative_ranking.py`, `tests/test_reasoning_facility_bridge.py`)
run for extra confidence, matching both predecessor rungs' own practice.
