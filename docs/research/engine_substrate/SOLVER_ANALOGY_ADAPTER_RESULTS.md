# A real analogy-shaped sentence adapter for `solve_analogical_promote` — RESULTS

Prereg: `SOLVER_ANALOGY_ADAPTER_PREREG.md`, same worktree/branch, base
`main @ dae5fbe` ("Merge solver-nl-adapter: first NL adapter for the six
unwired solve_* resolvers, GO"), verified via `git log --oneline -1 main`
immediately before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/solver-analogy-adapter`, branch
`solver-analogy-adapter`, commits `d6ced53` (PREREG) + `c374a64`
(implementation + tests). `data/` was absent in the fresh worktree (not a
partial real directory); symlinked (`ln -sfn /home/matt/ozmadev/ocelot/data
data`) and confirmed `data/wiktionary/en.jsonl.gz` resolves to the real
492,560,156-byte file. `main`'s tip moved to `02ec251` while this rung was
in flight (a concurrent, unrelated Bigville session) — the branch point
`dae5fbe` remains a real, verified ancestor and this rung's own diff never
touches any file the concurrent session is landing.

**Headline finding: `SOLVER_NL_ADAPTER_RESULTS.md`'s "no analogy-shaped
sentence parser exists anywhere in the tree" claim was too pessimistic, and
the grep that produced it used the wrong vocabulary.** A `LIKE` MarkerClass
(`like`/`resembles`/`resemble`) plus `comparative_like`/`comparative_
like_cop` constructions were already seeded in `seeds/reading_
constructions.json`, already wired into the general reading pipeline, and
already ground "X is like Y"/"X resembles Y" to exactly `["similar",
subject, object]` — confirmed live, unmodified, before any code in this
rung was written. Composed with an already-precedented concept-by-name
lookup idiom (an existing pattern copied locally, not new capability), an
explicit, measured-necessary ambiguity-refusal gate, and the already-fully-
mechanical `DirectionalCorrespondence` machinery
(`_concept_shape_vector`/`_pair_witness`/`record_directional_
correspondence`, all UNEDITED), a real, narrow, honestly-bounded adapter was
built — GO — and live-demonstrated end to end on real corpus sentences,
including both the promotion success path and a genuine resolver-side
honest wall.

---

## 1. What the prior rung's ranking actually checked, and where it stopped short

`SOLVER_NL_ADAPTER_PREREG.md` §2 checked for an analogy-shaped-sentence
parser via `grep for analog*/correspond* constructions in seeds/reading_
constructions.json: none`. That grep is searching for the wrong surface
vocabulary: English does not express an analogy claim with the morpheme
"analog" (that word describes the CONCEPT of an analogy, not how one is
STATED in a sentence) — it says "X is LIKE Y", "X RESEMBLES Y", "X is
SIMILAR to Y". A grep restricted to `analog*`/`correspond*` will find every
occurrence of the WORD "analogy" and none of the actual comparative
constructions a real analogy-shaped sentence uses. This is a narrow,
specific, checkable claim, and it does not survive being checked against the
right words — precisely the shape of correction this task was assigned to
look for (mirroring `RULE_REFERENCE_LAYER_SIZING_RESULTS.md`'s own
`Sort`/`SetMap` reversal, cited by name in the task prompt).

## 2. What already existed, read directly, then confirmed live

`grep -niE '"like"|similar|comparative' seeds/reading_constructions.json`
finds, already seeded (`local_id` 6/46/146/47/147), unedited by this rung:

```
MarkerClass{cls:"LIKE", forms:["like","resembles","resemble"]}
ShapeSignature{name:"comparative_like",      predication:"similar", signature:[["LIKE"]],         ground_template:{pred:"similar",mode:"pair"}}
ShapeSignature{name:"comparative_like_cop",  predication:"similar", signature:[["COP"],["LIKE"]], ground_template:{pred:"similar",mode:"pair"}}
ShapeSignature{name:"comparative_unlike",    predication:"contrast",signature:[["UNLIKE"]],        ground_template:{pred:"contrast",mode:"pair"}}
ShapeSignature{name:"comparative_unlike_cop",predication:"contrast",signature:[["COP"],["UNLIKE"]],ground_template:{pred:"contrast",mode:"pair"}}
```

**Confirmed live** against a full `WorldAdapter(seeds=()); load_all_seeds(a)`
boot, real `mathematics` Mt vocabulary (`generating_functions`,
`function_definition` — the SAME pair `DIRECTIONAL_CORRESPONDENCE_
RESULTS.md` §4.1 already demonstrated has real structural correspondence),
zero seed edits, zero code written yet at the time of this check:

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

`"X is like Y"`/`"X resembles Y"` already ground to exactly `["similar",
subject, object]` via the completely unmodified general reading pipeline —
byte-identical to the relation label an analogy-adapter needs. `"X is
unlike Y"` grounds to `["contrast", ...]`, the correctly-distinguishable
opposite signal. A comparative question correctly carries
`speech_act:"question"`.

**A real, honest limitation found live, and NOT silently absorbed into the
adapter's scope:** `"X is similar to Y"` (the adjective-plus-"to" phrasing,
as opposed to the `LIKE` marker class's own `like`/`resembles`/`resemble`
forms) does **not** trigger the comparative construction — it falls through
to `definitional` and mis-grounds as `is_a(X, "similar")`, silently
dropping `Y`. This is a real, second comparative-surface-form gap in the
reading pipeline (a genuinely new `MarkerClass`/construction addition, not
a thin-adapter fix) — named in §6 as a follow-on, not attempted here. The
adapter built below gates on `rel == "similar"` specifically, so this
particular mis-grounding is correctly ignored rather than mistaken for a
valid pair (its "object" is the literal string `"similar"`, which fails
concept-name resolution honestly — see §4).

## 3. Concept-name resolution — the one genuinely new (but small) piece

`domains/neuroscience_tagging.py:138-144` (`_find_concept_by_name`, unedited
elsewhere) is an EXISTING, already-shipped, already-reused (~15 call sites
in that one file) mechanical global-scan-by-name helper — the exact shape
needed to turn a surface token into a Concept node reference, no new
capability.

**A real, measured hazard its own OWN "first match" precedent does not
handle, checked before building anything:** `Concept` is a heavily-
overloaded node type — CAN belief-network propositions (`worlds/
bigville_can_beliefs.py`) and domain-vocabulary corpus terms
(`mathematics`/`computer_architecture`/… Mts) share it, confirmed already by
`ENTITY_RESOLUTION_RESULTS.md` §1. On a full `load_all_seeds()` boot:

```
total Concept nodes: 10777, distinct names: 10157, duplicated names: 507
e.g. 'agent'(x3), 'patient', 'theme', 'instrument', 'source', 'goal', 'manner', ...
generating_functions -> 1 (unique)      function_definition -> 1 (unique)
```

**Live-confirmed reachable, not a hypothetical**: `"The agent is like the
patient."` grounds cleanly to `['similar','agent','patient']`, and `'agent'`
has 3 distinct real Concept-node matches in the standing corpus — a naive
first-match lookup would silently, non-deterministically pick one.

**Design decision, checked against CLAUDE.md's shape/rule axis rather than
defaulted to Python out of convenience:** `ENTITY_RESOLUTION_RESULTS.md`
pushed its own analogous ambiguity guard into a graph Rule
(`seeds/entity_concept_correspondence.json`) because that rung was building
a STANDING, reusable, graph-persisted correspondence
(`SmEntity -denotes-> Microtheory`) other future queries read back — a
genuine "shape is acquisition" case. This adapter's resolution is different
in kind: a ONE-SHOT lookup, local to a single adapter invocation, turning
one sentence's two surface tokens into two node references — the SAME
mechanical shape `reasoning_can_bridge._find_concept_by_name`,
`neuroscience_tagging._find_concept_by_name`, `propositional_deduction.
_schema_by_name`, and `analogical_thinking._find_mt` already are (all
unedited, all accepted, all exact-match graph queries, none of them agent
decisions about belief or action). The ambiguity check (`len(hits) != 1 ->
decline`) is the SAME category of adapter-side shape-gate both prior
NL-adapter rungs already used in Python (`_is_property_pred`, the
`speech_act=="question"` gate). No Rule was added for this reason; recorded
explicitly here (matching the PREREG's own registered reasoning) so the
choice is checkable, not silent.

## 4. What was built

`domains/solver_dispatch.py` (immediately after the existing `mint_solve_
analogical_promote_goal`, mirroring where the predecessor rung placed its
own text adapter relative to its hand-built counterpart):

```python
def _find_concepts_by_name(sub, name: str) -> list:
    return [c for c in sub.nodes("Concept") if sub.node(c)["attrs"].get("name") == name]


def mint_solve_analogical_promote_goal_from_text(adapter, statement: str):
    from domains import reading_collapse as rc
    from domains import analogical_thinking as at_mod
    if not statement or not str(statement).strip():
        return None
    sub, native, ag = _resolve(adapter)
    whole = rc.read_clause(adapter, statement, write=False, learn=False)
    if whole.get("speech_act") == "question":
        return None
    preds = whole.get("predications") or []
    if not preds or len(preds[0]) < 3:
        return None
    rel, subj, obj = preds[0][0], preds[0][1], preds[0][2]
    if rel != "similar":
        return None
    subj, obj = str(subj).strip(), str(obj).strip()
    if not subj or not obj:
        return None
    hits_a = _find_concepts_by_name(sub, subj)
    hits_b = _find_concepts_by_name(sub, obj)
    if len(hits_a) != 1 or len(hits_b) != 1:
        return None
    node_a, node_b = hits_a[0], hits_b[0]
    if node_a == node_b:
        return None
    vec_a = at_mod._concept_shape_vector(sub, node_a)
    vec_b = at_mod._concept_shape_vector(sub, node_b)
    witness = at_mod._pair_witness(sub, vec_a, vec_b)
    corr_node = at_mod.record_directional_correspondence(
        sub, node_a, node_b, vec_a, vec_b, witness)
    if corr_node is None:
        return None
    return mint_solve_analogical_promote_goal(adapter, corr_node)
```

Every function this new code CALLS is unedited reuse: `reading_collapse.
read_clause`, `analogical_thinking._concept_shape_vector`/`_pair_witness`/
`record_directional_correspondence`, and the pre-existing `mint_solve_
analogical_promote_goal`. The only genuinely NEW lines are the ~5-line
`_find_concepts_by_name` scan (copying an established idiom) and the
sequencing/gating logic around it — smaller than `solve_reasoning_bridge`'s
own adapter, which additionally needed a property-predication classifier.

`solve_analogical_promote`'s own internals, `analogical_thinking.py`
(zero edits), `propositional_deduction.mint_logical_schema_from_analogy`,
`seeds/directional_correspondence.json`, and `seeds/reading_
constructions.json` are all byte-unchanged — confirmed by diff (§7).

## 5. Live demonstration

### 5.1 Success — real sentence, real corpus concepts, verified by hand against the promoted schema

```
sentence: "Generating functions are like a function definition."
subj/obj resolve to Concept#2075 (generating_functions, unique) /
                      Concept#2009 (function_definition, unique)
witness: fixed_count=82, 1 shared axis
DirectionalCorrespondence#24361 recorded
directional_hypothesis_for -> {direction:'a_source', source_concept:'generating_functions',
    target_concept:'function_definition', confidence:{richness_a:3, richness_b:2, ...}}

goal = mint_solve_analogical_promote_goal_from_text(agent, sentence)
goal.attrs: {kind:'solve_analogical_promote', status:'pending'}
goal -targets_correspondence-> DirectionalCorrespondence#24361 (about_a=node_a, about_b=node_b)

after dispatch through the UNCHANGED qd_bind_resolver -> solve_analogical_promote:
  status: 'resolved'
  direction_verdict: 'a_source'
  answer/schema_name: 'logical_analogical_generating_functions_function_definition'
  resolve_with -> Resolver{name:'solve_analogical_promote'}   # the JOIN's own effect
```

**Correctness verified by hand against the promoted schema's own attrs**
(mirroring `DIRECTIONAL_CORRESPONDENCE_RESULTS.md` §4.3's own inspection
discipline, not merely trusting `status=="resolved"`):

```
schema (ShapeSignature) attrs:
  kind: 'knowledge_logical'
  coherence: 'elaborative'          # the two-tier evidentiary system, reused unedited
  provenance: 'analogical'
  signature:  [["holds", "generating_functions"]]
  supplies:   {"relation": "is_a", "attr": "function_definition"}
derived_from edge -> DirectionalCorrespondence#24361 : True
```

Re-run twice, byte-identical (deterministic): `richness_a=3, richness_b=2`
both times, direction `a_source` both times.

A second real surface form of the SAME `LIKE` marker class — `"Generating
functions resemble a function definition."` (verbal, not copular) — also
resolves cleanly (`test_verbal_form_resembles_also_grounds_the_same_way`),
confirming the adapter reads the construction's relation LABEL, not one
hardcoded surface string.

### 5.2 Honest wall (resolver-side) — real, unambiguous concepts, genuinely undetermined direction

Two real, GLOBALLY-UNIQUE concept names with a measured, live TIED
richness — `"myelination"` (richness 7) and
`"temporal_difference_learning_formal"` (richness 7, both real `neural_
networks`/`machine_learning` Mt vocabulary):

```
"Myelination is like temporal difference learning formal."
  -> predications: [['similar', 'myelination', 'temporal_difference_learning_formal']]
  -> both concept names unambiguous (1 match each)
  -> directional_hypothesis_for -> {direction: 'symmetric', richness_a: 7, richness_b: 7}
  -> solve_analogical_promote [UNCHANGED] -> status: 'walled'
     direction_verdict: 'symmetric'
     note: "correspondence direction is 'symmetric' -- not resolved (only
            a_source/b_source are promotable); an undirected correspondence
            names no antecedent, nothing fabricated"
     gap_key: 'solve_analogical_promote:corr=#...' filed (Rung 2's
            note_solve_exhausted_gap, unchanged, fires correctly)
```

This is the SAME resolver-side honest-wall shape `SOLVER_NL_ADAPTER_
RESULTS.md` §4.2 demonstrated for `solve_reasoning_bridge` — reached here
with **zero changes** to `solve_analogical_promote`, confirming the
resolver's own existing wall path composes for free with a text-driven
`corr_node`.

### 5.3 Honest decline (adapter-side) — unsuitable real input mints nothing

```
"Generating functions are unlike function definitions."                       -> rel="contrast" -> decline
"Is a generating function like a function definition?"                        -> speech_act=="question" -> decline
"Generating functions are important."                                         -> rel="is_a", no comparative cue -> decline
"The agent is like the patient."                                              -> 'agent' has 3 Concept matches -> decline (ambiguous)
"Generating functions are like a completely_unknown_bogus_concept_xyz."       -> object resolves to 0 Concepts -> decline
""  /  "   "  /  None                                                        -> empty/degenerate statement -> decline
```

Confirmed additionally that four declines together mint **zero** Goal nodes
(`test_decline_mints_no_goal_node_at_all` — `len(agent.s.nodes("Goal"))`
identical before/after), not merely that the return value is `None`, the
SAME "never mint garbage from unsuitable input" discipline both prior
NL-adapter rungs established.

## 6. The old direct-mint path is unaffected

`mint_solve_analogical_promote_goal(adapter, corr_node)` — the ORIGINAL,
hand-supplied-`corr_node` entry point — still dispatches byte-identically
(`test_old_direct_mint_path_unaffected`, two hand-built Concepts, a
hand-computed `DirectionalCorrespondence`): reaches `status in ('resolved',
'walled')`, never an exception, exactly as before. The new function is a
pure ADDITION alongside it, never a replacement.

## 7. Regression

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_solver_dispatch_migrated.py \
    tests/test_solve_gap_awareness_migrated.py \
    tests/test_problem_shape_migrated.py \
    tests/test_solver_math_boundary.py \
    tests/test_solver_nl_adapter.py \
    tests/test_directional_correspondence.py \
    tests/test_solver_analogy_adapter.py \
    -q -p no:randomly
80 passed in 180.08s
```

Extra sweep, the analogical-thinking facility's own adjacent suites, run
fresh for extra confidence (matching both predecessor rungs' own practice):

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_blob_edge_analogy_extension.py \
    tests/test_analogical_relative_ranking.py \
    tests/test_reasoning_facility_bridge.py \
    -q -p no:randomly
21 passed in 70.80s
```

**101/101 green across all ten suites, zero regressions, zero waivers.**

```
$ git diff --stat dae5fbe -- domains/solver_dispatch.py
 domains/solver_dispatch.py | 125 ++++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 124 insertions(+), 1 deletion(-)

$ git diff dae5fbe -- domains/solver_dispatch.py | grep '^-' | grep -v '^---'
-    "mint_solve_analogical_promote_goal",
```

The single removed line is the `__all__` entry replaced by the two-entry
version (`mint_solve_analogical_promote_goal`, `mint_solve_analogical_
promote_goal_from_text`) — every existing function's body is byte-unchanged.
No Rust touched; no `cargo build` needed. No seed file was modified — the
new Goal still dispatches through the UNCHANGED `qd_bind_resolver` JOIN and
the already-installed `solve_analogical_promote` Resolver
(`seeds/solver_dispatch.json`, untouched).

## 8. GO / NO-GO

**GO.** `solve_analogical_promote` is now reachable from real natural-
language text via `mint_solve_analogical_promote_goal_from_text` —
demonstrated live on real corpus concepts, both the success path
(correctness verified by hand against the promoted schema's own attrs and
`derived_from` edge) and both honest-refusal paths (a genuine resolver-side
wall on a real tied-richness pair; six adapter-side declines on unsuitable
real input). 101/101 regression tests green, fresh, across the task-named
suites plus an additional adjacent-facility sweep. The diff is purely
additive — `solve_analogical_promote`'s own internals, `analogical_
thinking.py`, and every seed file are untouched.

**The prior rung's "moderate cost, real unbuilt parsing work" ranking for
this resolver does not hold up.** The comparative construction was already
built and seeded; the concept-lookup idiom was already an established
Python pattern; the correspondence-recording half was already known
mechanical (the prior rung's own correct finding, unchanged here). The only
genuinely new code is a ~5-line name-scan helper plus sequencing — smaller
than the adapter the prior rung actually built for `solve_reasoning_
bridge`. **The mis-ranking traced to a grep on the wrong search terms
(`analog*`/`correspond*` instead of `like`/`similar`/`comparative`), not to
the underlying facility being genuinely expensive** — exactly the class of
correction this task was assigned to check for.

**Not merged, not pushed to `main`.** `main`'s tip was checked fresh
(`dae5fbe`) immediately before creating this worktree, and every commit
(`d6ced53`, `c374a64`) lives on the `solver-analogy-adapter` branch only.
This rung did not run any command that touched `main` at any point (`main`
has since advanced to `02ec251` via a concurrent, unrelated session — this
branch's own diff touches no file that session is landing). The
orchestrator performs the merge.

---

## 9. What this document does NOT establish

1. **"X is similar to Y" (adjective+"to" phrasing) is not covered.** Found
   live (§2): this surface form mis-grounds via the `definitional`
   construction today, dropping the object entirely. A second `MarkerClass`/
   construction pair for this phrasing is a genuinely new reading-pipeline
   addition (closer to a `seeds/reading_constructions.json` edit than a
   thin adapter) — sized as real, separate follow-on work, not attempted
   here, not silently assumed solved.
2. **Concept-name resolution is exact-match only, not semantic.** Mirrors
   the SAME honest boundary `SOLVER_NL_ADAPTER_RESULTS.md` §8 item 5 already
   named for `solve_reasoning_bridge`: a sentence naming a concept by a
   near-synonym, a paraphrase, or a definite description with no lexical
   overlap does not resolve — only a surface token that normalises
   byte-identically to an existing Concept's `name` succeeds.
3. **The ambiguity guard is a refusal, not a disambiguation.** A genuinely
   ambiguous concept name (507 real duplicates exist in the standing
   corpus) is correctly left unresolved, never guessed at via a
   ranking/salience heuristic — no such mechanism was built or was needed,
   mirroring `ENTITY_RESOLUTION_RESULTS.md`'s own no-over-merge discipline
   for a structurally analogous but distinct problem.
4. **Only a single leading predication is read**, mirroring `mint_solve_
   reasoning_bridge_goal_from_text`'s own scope: a compound sentence
   asserting more than one comparison is not handled beyond its first
   clause.
5. **Negation/polarity of the comparative itself is not modelled beyond
   the `similar`/`contrast` relation-label distinction the reading pipeline
   already makes.** "X is NOT like Y" was not checked live in this rung —
   whatever the general reader's own negation handling (or lack of it) does
   for a comparative clause is inherited as-is, not audited here.
6. **`DirectionalCorrespondence`'s own richness heuristic and cost profile
   are unchanged and were not re-investigated.** `DIRECTIONAL_
   CORRESPONDENCE_RESULTS.md` §7's own honest limitations (richness is a
   heuristic not a proof; per-write `run_rules()` cost at large-corpus
   scale) apply identically here — this rung is a new CALLER of that
   machinery, not a re-examination of it.
7. **Synthetic-proven mechanism ≠ benchmark value, per house standard**:
   every number above is a mechanism demonstration (does the adapter
   correctly reach a promoted schema / an honest wall / a clean decline on
   real sentences), not a coverage/accuracy claim over how often real,
   naturally-occurring analogy sentences in some corpus would successfully
   parse and resolve.

---

## 10. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/solver-analogy-adapter
git log --oneline -1 main   # dae5fbe at branch time; main has since advanced

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_solver_analogy_adapter.py -q -p no:randomly

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_solver_dispatch_migrated.py tests/test_solve_gap_awareness_migrated.py \
  tests/test_problem_shape_migrated.py tests/test_solver_math_boundary.py \
  tests/test_solver_nl_adapter.py tests/test_directional_correspondence.py \
  tests/test_solver_analogy_adapter.py -q -p no:randomly

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_blob_edge_analogy_extension.py tests/test_analogical_relative_ranking.py \
  tests/test_reasoning_facility_bridge.py -q -p no:randomly
```
