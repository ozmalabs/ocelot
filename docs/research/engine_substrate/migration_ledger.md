# Migration ledger — Python faculty → graph data (the agent owns this)

The running record of `CuriousAgent` faculties migrated to graph data (Terms / Rules / Concepts), with
their parity status. This is the migration's OUTPUT — graph data, not Python, not tooling. When a
faculty's row is here and parity-green, its Python is deletable. Dissolving methods (caches /
graph-access wrappers / evaluator-callers) are recorded as DISSOLVE — they're deleted, not migrated;
their callers inline the graph access shown.

## Cluster: goals / policy  (4 methods → 1 Term + 1 build-Rule + 3 dissolve)

| Python faculty | graph-native form | status |
|---|---|---|
| `_get_top_level_goals()` | DISSOLVE → inline `Neighbours{agent_root, "has_goal"}` | — |
| `_goal_satisfaction(g)` | DISSOLVE → `EvalSubgraph(Pick(Neighbours{g, "satisfaction_term"}))` (its docstring: "Python is just the evaluator") | — |
| `_goal_active_weight(g)` | the genuine decision `weight = (1 − satisfaction) × priority`, as a Term (reads inlined) — see below | **parity GREEN** |
| `_create_goal(...)` | a construction Rule: a `goal_request` on the agent → `add_node Goal{label,priority,persistent}` + `has_goal` edge, request consumed (fire-once). Conditional parent/target/sat edges = variants. | **parity GREEN** |

`_goal_active_weight` migrated Term (verified: priority=2.0, satisfaction=0.25 → 1.5 == Python):

```json
{"type":"Times","items":[
  {"type":"Minus",
     "a":{"type":"Lit","value":1.0},
     "b":{"type":"EvalSubgraph","node":{"type":"Pick","source":
            {"type":"Neighbours","node":{"type":"Var","name":"g"},"edge_type":"satisfaction_term"}}}},
  {"type":"Attr","node":{"type":"Var","name":"g"},"key":"priority"}]}
```

This is the whole intellectual content of the four methods: the weight formula. The caches
(`_goal_weight_cache`, `_goal_term_cache`) vanish (the graph is the store), the satisfaction evaluator
is `EvalSubgraph`, the top-level lookup is `Neighbours`. The cluster collapses ~hundreds of lines +
3 caches → one weight Term + one goal-construction Rule.

`_create_goal` construction Rule (verified: `GoalReq{label:"visit_target", priority:3.0}` → a `Goal`
node + `agent --has_goal-->` it, label/priority carried through):

```json
{"name":"create_goal_from_request",
 "match":[["agent","is_a","Agent"],["agent","goal_request","req"]],
 "effects":[
   ["add_node","goal","Goal",{"label":{"__term__":{"type":"Attr","node":{"type":"Var","name":"req"},"key":"label"}},
                              "priority":{"__term__":{"type":"Attr","node":{"type":"Var","name":"req"},"key":"priority"}},
                              "persistent":false}],
   ["add_edge","agent","has_goal","goal"],
   ["del_edge","agent","goal_request","req"]]}
```

Graph-native modelling: the agent doesn't *call* `_create_goal(...)`; a goal-generating Rule posts a
`goal_request` (params as attrs), and this construction Rule builds the Goal and consumes the request.
That is how an invoked Python factory becomes an autonomous graph rewrite.

**Goal cluster: DONE** — 2 genuine pieces (weight Term + construction Rule) parity-green, 2 dissolve.

## Cluster: action scoring / selection  (the agent's decision core)

| Python faculty | graph-native form | status |
|---|---|---|
| `_action_score(...)` | the curiosity-score decision as a Term: `−q + |touched∩asym|·meta_w + novelty·novelty_w` (set-ops native) | **parity GREEN** |
| `choose_action(...)` | `Argmax{source: action-candidates, var_name: c, value: <score Term over c>}` — selection is a reduction | **parity GREEN** |
| `_lookahead(...)` depth=1 (default/greedy) | IS that `Argmax` (the score Term is the immediate score) | **parity GREEN** (via choose_action) |
| `_lookahead(...)` depth>1 (k-step plan) | `Argmax` over first-action candidates of `LookaheadValue{node, child_edge, score_key, depth}` (native bounded tree-fold: `value(n,d)=score(n)+(d>1∧children? max_child value(child,d-1):0)`); adapter expands the previewed game-tree | **parity GREEN** (backup matches `_lookahead` at d=1,2,3; choice flips greedy→planning) |
| `choose_action` guards (`len==1`, `¬preview_safe`, no productions) | dispatch → match conditions / rule variants, not the decision | — (control flow) |
| `_get_scalar_policy('meta_curiosity_weight'/'novelty_weight', …)` | DISSOLVE → the policy `Lit` reads inline as `Attr`/`Neighbours` | — |
| `quality_of_position`, `_novelty_count`, `senses`/`models_set`/`acts_on_set` | sub-faculties (own rows) feeding `q`, `novelty`, the asymmetry sets | pending |

`_action_score` migrated Term (verified: q=0.3, |touched∩asym|=2, meta_w=0.15, novelty=5,
novelty_w=0.02 → 0.1 == Python; and two more cases):

```json
{"type":"Plus","items":[
  {"type":"Neg","arg":{"type":"Var","name":"q"}},
  {"type":"Times","items":[
     {"type":"Count","source":{"type":"Intersect","a":{"type":"Var","name":"touched"},
                                                   "b":{"type":"Var","name":"asym"}}},
     {"type":"Var","name":"meta_w"}]},
  {"type":"Times","items":[{"type":"Var","name":"novelty"},{"type":"Var","name":"novelty_w"}]}]}
```

The 3-signal curiosity score (quality + boundary-asymmetry + novelty, policy-weighted) — the heart of
`choose_action` — is this one Term; selection is `Argmax` over actions of it. The set logic
(`sensed−acted | sensed−modeled`, `touched ∩ asymmetric`) is native (`Difference`/`Union`/`Intersect`/
`Count`); the weights are dissolved policy reads. `choose_action`'s body collapses to: compute the
score Term per action, `Argmax`.

Score sub-faculties:

| Python faculty | graph-native form | status |
|---|---|---|
| `quality_of_position(s)` | `admitted / max(total,1)` = `Div{Count{admitted edges}, Max{Count{all edges},1}}` (admissibility is the Γ primitive) | **parity GREEN** (ratio: 7/10→0.7, 0/0→0, 5/5→1, 3/4→0.75) |
| `senses` / `acts_on_set` / `models_set` | DISSOLVE → `_relation_set('senses'/'acts_on'/'models')` = a relation-set read (`Neighbours`/`MapSet`) | — |
| `is_instance_saturated(wi)` | DISSOLVE → `EvalSubgraph(saturation_predicate, {attr: wi})` — "one policy governs both scopes" (its docstring); the Python is just the evaluator | — |
| `_novelty_count(s)` — channel 2 (unsaturated instances) | `Count{Filter{NodesOfType(WorldInstance), wi, Not{saturation_predicate}}}` | **parity GREEN** |
| `_novelty_count(s)` — channel 1 (unseen (type,attr,value)) | `Count{FilterList{ScalarAttrTriples, t, Not{In{t, seen}}}}` — a node-attr occurrence is novel iff its `(type,attr,value)` triple isn't in the seen-memory (`v∉seen[(type,k)] ⟺ (type,k,v)∉seen_triples`); minted `ScalarAttrTriples{skip_prefix}` enumerator (ordered list, preserves per-node occurrences, excludes Float like Python) | **parity GREEN** |
| **`_novelty_count` (full)** | `Plus{channel-1 Count, channel-2 Count}` — both channels now native | **parity GREEN** (both) |

`quality_of_position` ratio Term: `{"type":"Div","a":{"type":"Var","name":"explained"},
"b":{"type":"Max","items":[{"type":"Var","name":"total"},{"type":"Lit","value":1}]}}`.

`choose_action` selection Term (verified: 5 candidates with attrs (q, asym_count, novelty), Argmax picks
idx 3 == Python argmax of `−q + asym_count·meta_w + novelty·novelty_w`):

```json
{"type":"Argmax",
 "source":{"type":"NodesOfType","node_type":"ActionCandidate"},
 "var_name":"c",
 "value":{"type":"Plus","items":[
   {"type":"Neg","arg":{"type":"Attr","node":{"type":"Var","name":"c"},"key":"q"}},
   {"type":"Times","items":[{"type":"Attr","node":{"type":"Var","name":"c"},"key":"asym_count"},{"type":"Lit","value":0.15}]},
   {"type":"Times","items":[{"type":"Attr","node":{"type":"Var","name":"c"},"key":"novelty"},{"type":"Lit","value":0.02}]}]}}
```

The world callables (`apply_action`, `interpret_acts_on`, `legal_actions`) stay in the world adapter —
they preview each action and stamp the candidate's score inputs (q / asym_count / novelty). That is
mechanical I/O translation (CLAUDE.md's permitted adapter role), NOT an agent decision. The agent's
decision is the `Argmax` + score Term; the set logic (`(sensed−acted)|(sensed−modeled)`, `touched∩…`)
is the asymmetry-count the adapter pre-stamps from the agent's relation sets. **The action-scoring /
selection cluster is the agent's whole act-choice, now graph data** — including k-step planning:
`choose_action`'s `lookahead_depth` policy drives `Argmax{first-actions, LookaheadValue{·, depth}}`, the
native bounded tree-fold that backs up `value = immediate + best-future` over the adapter-previewed
game-tree. Verified that the choice flips with depth (greedy picks the high-immediate action; depth≥2
flips to the action with the better continuation) — planning works, in graph data.

### New primitive minted this cluster: `NodesOfType{node_type}` (Layer B)

The unfiltered node-enumeration source — `nodes_of_type(T)` → frozenset of all nodes of a type.
`NodesWhere` was the equality-filtered special case; `NodesOfType` is the whole population, the
source every graph-wide aggregate (`Count`/`Filter`/`MapSet` over a type) was missing. Wired across
term.rs (enum + eval + copy + traversal) / jsonio.rs (name + emit + parse) / reflect.rs
(describe + reconstruct); cargo-check clean, release-rebuilt, `.so` installed. PARITY GREEN:
`Count{NodesOfType(WorldInstance)}`=7 (Cell/Agent excluded), and channel-2 unsaturated=3 == Python.

This is the sanctioned "new primitive → Rust" path (CLAUDE.md): the existing DSL genuinely could not
enumerate a whole type, so the primitive went into Rust and the agent composes it. `_novelty_count`'s
channel 1 was later closed by a second enumerator, `ScalarAttrTriples{skip_prefix}` — it emits every
scalar `(type, key, value)` triple across nodes as an ordered list (preserving per-node occurrences,
excluding Float exactly as Python's `isinstance(v,(int,str,bool))` does). Channel 1 then composes
entirely from existing pieces: `Count{FilterList{ScalarAttrTriples, t, Not{In{t, seen}}}}`, verified
GREEN (novelty 3 == Python; the Float attr excluded; `skip_prefix="Term."` drops Term-node attrs). So
`_novelty_count` is now **FULLY migrated**: `Plus{channel-1, channel-2}`, both channels native.

## Cluster: observe / perception  (the autopoietic fold)

`observe(substrate)` is ~200 lines, but most of it is the **autopoietic fold** — mechanical
graph-mutation that translates perceived world nodes into `mind_graph` state (mention counts,
per-instance saturation bookkeeping, net-shed accumulation, resource materialisation). Those are
**observe-Rules fired by the adapter's ingest** (each is an `add_node`/`set_attr`/counter effect, not a
decision). Embedded in the fold are a few genuine *recognitions* — and those are the migration targets:

| Python faculty (inside `observe`) | graph-native form | status |
|---|---|---|
| score-rose detection (`cur_score > last_score ∧ last≠−∞`) | a comparison: `And{Gt{cur, last}, Not{Eq{last, −inf}}}` → a `_last_score_rose` attr Rule | pending (trivial Gt-rule) |
| **gauge-type recognition** ("the type with the most sustained net shedding past a policy threshold") | `Argmax{Filter{NodesOfType(BodyType), bt, Gt{Attr{bt,"net_shed_to_floor"}, Lit(thr−1)}}, bt, Attr{bt,"net_shed_to_floor"}}` | **parity GREEN** |
| **`turns = max(0, gauge_full − shed)`** | `Max{Minus{Attr{root,"gauge_full"}, shed}, Lit 0}` | **parity GREEN** |
| net-shed accumulation, mention counts, saturation tick/reset | DISSOLVE → observe-Rules (counter/`set_attr` effects on `BodyType`/`Attribute`/`WorldInstance` nodes), fired by ingest | — |
| `is_saturated(t,a)` / `is_instance_saturated(wi)` | DISSOLVE → `EvalSubgraph(saturation_predicate)` (one policy, both scopes) | — |

`gauge-type` recognition Term (verified: 5 BodyTypes, picks `turnbar` net=11 == Python argmax over
net>thr−1):

```json
{"type":"Argmax",
 "source":{"type":"Filter","source":{"type":"NodesOfType","node_type":"BodyType"},"var_name":"bt",
   "predicate":{"type":"Gt","a":{"type":"Attr","node":{"type":"Var","name":"bt"},"key":"net_shed_to_floor"},"b":{"type":"Lit","value":5}}},
 "var_name":"bt","value":{"type":"Attr","node":{"type":"Var","name":"bt"},"key":"net_shed_to_floor"}}
```

Same `NodesOfType`+`Filter`+`Argmax` shape as `choose_action` — the new primitive is already paying off
across clusters (a recognition = a thresholded Argmax over a typed population; the act-choice = an
Argmax over previewed candidates). The autopoietic fold itself is the world-adapter's ingest +
observe-Rules; the *recognitions* are the small graph Terms above.

## Cluster: theorem-induction / relation discovery  (the agent's causal learning)

The headline: **the genuine causal-inference decisions are ALREADY graph Terms** — seeded with the DSL
constructors and installed via `_term_to_mind`, not Python logic. `discover_relations` itself is
counter-bookkeeping + reification glue around them ("the reasoning is in gamma; Python only updates
counts and reifies what the predicate accepts" — its own docstring). All three verified faithful so the
Python eval-wrappers (`_get_named_predicate` + `.evaluate(...)`) DISSOLVE:

| causal decision | graph Term (already seeded) | status |
|---|---|---|
| **salience / lift** ("a rare-but-predictive pair wins even at high-count noise") `co≥3 ∧ co·n_events/(n_from·n_to) ≥ 2` | `And{Gte{co,3}, Gte{Div{co·n_events, n_from·n_to}, 2.0}}` | **parity GREEN** (5 cases — lift 3.33 fires, 0.89 noise rejected) |
| **confound screening** ("B explained away by A: conditional lift ≤ 1.5 with evidence") | `And{Gte{n_cond,5}, Lte{Div{co_cond·n_ticks, n_cond·n_y}, 1.5}}` | **parity GREEN** (3 cases — cond_lift 1.0 screens, 9.0 keeps) |
| **interventional causation** ("do-contrast: P(Y\|do A) ≥ 2·P(Y\|do ¬A)") | `And{Gte{n_with,5}, Gte{Div{n_with,n_a}, Times{2, Div{n_y−n_with, n_ticks−n_a}}}}` | **parity GREEN** (3 cases — 0.80 vs 0.09 causal, 0.30 vs 0.20 not) |
| promotion gate (`count ≥ min_count`, top-K) + reification (`_promote_relation` + `add_edge`) | DISSOLVE → a construction Rule (`where count ≥ min_count` / `where salience_predicate`, effects `add_node Relation` + `add_edge`) like `create_goal_from_request` | — |
| counter maintenance (`_agent_world_counter`, PairStat/CondStat/InterventionStat updates) | DISSOLVE → observe-Rules (counter `set_attr` effects), fired by ingest | — |
| **`anti_unify` (recursive least-general-generalization)** | minted as native `AntiUnify{values}` Term — recursive LGG over nested Dicts/Tuples/Sets, WILD = `("·?·",)` sentinel | **parity GREEN** (10-case battery) |
| **`_fixed_count` (MDL specificity)** | minted as native `FixedCount{pattern}` Term — WILD→0, Dict/Tuple→Σ children, Set→cardinality, leaf→1 | **parity GREEN** (5 patterns + composed) |
| **`induce_rule` + keep-gate** (`induce_change_rules`) | `pattern = AntiUnify{insts}`, `fixed = FixedCount{pattern}`, `support = Count`; gate `And{Gte{FixedCount{AntiUnify}, min_fixed}, Gte{Count, min_support}}` | **parity GREEN** (3 instance-sets, fixed + gate both match) |
| **`covers` (rule-application test)** | minted as native `Covers{pattern, instance}` Term — dual of `AntiUnify`: WILD matches all, Dict keys-present-&-covered, Tuple same-len element-wise, Set ⊆ instance, scalar equal | **parity GREEN** (12 cases + induce→test loop) |
| `_wild_paths` (abstracted-path list readout) | recursive fold collecting WILD positions | pending (minor recursion readout) |
| change-history partition (group by `frm` / `kind` / reward) + `_reify_implied_rule` | DISSOLVE → grouping over change-instance nodes + a construction Rule (`ImpliedRule` node), like `create_goal_from_request` | — |
| win-rule modal-outcome fallback (`most_common(1)` target when AU abstracts it) | `Argmax` over outcome counts (the recurring selection shape) | pending (Argmax over a count-map) |

So the causal-learning cluster's *decisions* (lift, screening, intervention) are already graph data —
this whole sophisticated layer needs no migration, only confirmation (done) + deletion of its Python
eval-wrappers. The implied-rule LGG operator `anti_unify` — once the one genuine Python-cognition gap here — is now
the native `AntiUnify{values}` Term (minted this turn, the sanctioned "new primitive → Rust" path).
It performs the recursive least-general-generalization faithfully: empty → WILD; all-equal → that
value; all-Dict → over the intersected keys, each recursively generalized; all-Tuple of equal length →
element-wise; all-Set/FrozenSet → the intersection; otherwise → WILD; with the `("·?·",)` sentinel
round-tripping exactly (the `wild` Sym is interned at construction so the read-only evaluator never
interns). Verified against `domains/implied_rule.py::anti_unify` on a 10-case battery (all-equal,
dict-WILD, key-intersection, tuple-WILD, diff-len-WILD, frozenset-intersection, **nested dict+tuple
recursion**, mixed→WILD, single, empty) — all GREEN.

`induce_rule` is now fully composable from native primitives: `pattern = AntiUnify{insts}`,
`fixed = FixedCount{pattern}` (the MDL specificity, minted this turn), `support = Count`. The keep-gate
that `induce_change_rules` decides on — keep a rule iff specific enough AND supported enough — is the
Term `And{Gte{FixedCount{AntiUnify{insts}}, min_fixed}, Gte{Count, min_support}}`, verified GREEN on 3
instance-sets (win-rule-shared keeps at fixed=3; frm-varies rejected at fixed=1; all-differ rejected at
fixed=0). The **win-rule** is just the reward-grouping (`score_rose`/`aesthetic`/`intrinsic`) of this
same faculty — so the agent's "what does the score follow?" learning is graph-native at its core.

And the loop CLOSES: `covers` — the rule-application test — is now native `Covers{pattern, instance}`,
the dual of `AntiUnify`. The full **induce→test cycle runs in graph data**: `Covers{AntiUnify{insts},
fresh}` induces a rule from examples and tests it on a fresh scenario — verified GREEN (accepts a fresh
matching instance with extra keys, rejects a non-matching one). For a win-rule, `Covers{winrule_pattern,
current_state}` is exactly "does the condition the score follows now hold?" — which makes a held
`ImpliedRule` actionable for the planner. The induction faculty is native end-to-end: induce
(`AntiUnify`) + rank/gate (`FixedCount`) + test (`Covers`). What remains are `_wild_paths` (a minor
abstracted-path readout), the grouping + reification (Rules), and the modal-outcome fallback (`Argmax`).

## Reification: from verified-in-isolation to loadable graph data

The primitives are complete and the faculties verified, but verification used ad-hoc `add_rule` /
`evaluate` calls. For a migrated faculty to be the agent's actual boot path it must ship as a **seed
manifest** the Rust runtime loads. The seed loader (`load_seed_manifest`) handled `nodes`/`edges`/
`productions` but **not `rules`** — so the migrated decisions (which are RewriteRules) couldn't be
bundled. Closed that: `load_seed_manifest` now installs a `rules` section, reusing the same
`parse_rule_json` path as `add_rule` (rules match the live graph at tick time, so no local-id
resolution needed). Summary now reports `rules`.

**Proven end-to-end** (`decision_core` manifest): a seed carrying `create_goal_from_request` loads
(`{rules: 1}`), and on `run_rules` the Rust engine fires it — Goal node created (`label=visit_target`,
`priority=3.0`), `has_goal` edge wired, `goal_request` consumed. So a migrated faculty is now
**installable graph data that boots and runs in Rust**, not a Python-side test fixture. This is the
bridge toward deleting the Python clusters: capture each verified cluster into `seeds/<id>.json`
(nodes + edges + productions + **rules**), load it, confirm it ticks, then the Python is deletable.

### First captured seed: `seeds/decision_core.json`

The first migrated faculty shipped as a real seed file. `decision_core` bundles the goal-construction
Rule (`create_goal_from_request`) and is **registered in `seed_registry.py` with NO Python installer**
— it is migrated graph data, not captured from an `install_X`, which is exactly the end-state CLAUDE.md
describes (a seed is graph data the agent boots with). Verified the full path: `manifest_for(
"decision_core")` reads the file → `load_seed_manifest` installs it (`{rules: 1}`) on a fresh substrate
→ a runtime agent posts a `goal_request` → `run_rules` fires the seeded Rule in Rust → Goal created
(`label=explore_room`, `priority=2.5`), `has_goal` wired, request consumed. **GREEN.**

This is the first burned boat: the goal-construction faculty now exists as loadable graph data the Rust
runtime boots with — its `CuriousAgent._create_goal` Python is superseded. The decision Terms
(goal-weight, action-score, recognitions) attach to this seed as Term-subgraph nodes/edges in a
follow-on capture; the seed file is structured (empty `nodes`/`edges`) to receive them.

### Terms as first-class graph data: `add_term_subgraph` + named attachment

For a decision Term to ship in a seed it must be expressible as graph nodes/edges. Exposed
`add_term_subgraph(term_json) → root NodeID` (PyO3 over `reflect::term_to_subgraph`) — the inverse of
`EvalSubgraph`'s read: it materialises a Term as typed `Term.<Variant>` nodes + `child.<field>` edges.
Verified the **round-trip**: the `quality_of_position` Term materialises to 5 `Term.*` nodes
(Div/Max/Var/Lit) and `EvalSubgraph(root)` reads it back live — 0.7 and 0.75 across two envs == direct
`evaluate`. And the **named-attachment pattern** (how a decision Term actually lives in the graph):
the action-score Term attached to a `Policy` node by an `action_score_term` edge, read via
`EvalSubgraph(Pick(Neighbours{p, "action_score_term"}))` — exactly the shape `goal-weight` uses for
`satisfaction_term` — evaluates to 0.29 == direct. **GREEN.**

So the capture path is complete in both halves: **Rules** ship via the seed `rules` section (proven by
`decision_core`), and **Terms** ship as materialised `Term.*` subgraphs attached by named edges. A
faculty's full graph data — decision Terms + construction Rules — can now be captured into one seed,
loaded, and ticked, after which its Python cluster is deletable.

### First FULLY-reified faculty: the goal cluster in `decision_core.json`

The goal cluster's entire graph data now ships in one seed and boots end-to-end. `decision_core.json`
carries: 9 `Term.*` nodes + 9 edges encoding the **goal-weight Term** `(1−satisfaction)×priority`
(captured via `add_term_subgraph` → `graph_to_dict` → seed local-id format), attached to `agent_root`
by a `goal_weight_term` edge; plus the **`create_goal_from_request` Rule**. Verified the whole cluster
from one seed (`{nodes:9, edges:9, rules:1}`): a runtime `goal_request` → `run_rules` fires the Rule →
`Goal{label:reach_exit, priority:4.0}` created → the seeded goal-weight Term, read via
`EvalSubgraph(Pick(Neighbours{agent, "goal_weight_term"}))` on that goal (with a `satisfaction_term`
of 0.25), evaluates to **3.0 == (1−0.25)×4.0**. **GREEN.**

So `CuriousAgent._create_goal` AND `_goal_active_weight` are now fully superseded by graph data the Rust
runtime boots with — the goal cluster is the first faculty whose complete behaviour (construct + score)
runs from a seed with zero Python. Per the migration rule, the actual line-deletion of the superseded
Python waits for the seed-boot path to replace the `CuriousAgent` wholesale (burn the boats at the end,
keeping the Python regression bench intact until the last call site migrates) — but the goal cluster's
graph-native replacement is complete and proven.

### Action-scoring cluster reified into the same seed

`decision_core.json` now also carries the action-scoring cluster's decision Terms, captured the same
way (materialise → `graph_to_dict` → seed local-ids, attached to `agent_root` by named edges). The seed
holds **26 `Term.*` nodes + 26 edges + 1 Rule**, exposing three named decision Terms:

| named edge | Term | verified from seed |
|---|---|---|
| `goal_weight_term` | `(1−satisfaction)×priority` | 3.0 on (priority 4, sat 0.25) |
| `action_score_term` | `−q + asym_count·0.15 + novelty·0.02` | 0.29 on (q 0.2, asym 3, nov 2) |
| `quality_term` | `explained / max(total,1)` | 0.7 on (7, 10) |

All three load and evaluate from the seed — **GREEN**. `choose_action`'s `Argmax` and the k-step
`LookaheadValue` are adapter-invoked decisions that *compose* these seeded Terms at choice-time (read
`action_score_term`, score each previewed candidate, `Argmax`), so the scoring data lives in the seed
and the selection harness reads it. Two clusters' core decision data — goals + action-scoring — now
boot from one seed and evaluate with zero Python.

### Second seed: `learning_core.json` — the causal-inference faculty

The causal-learning cluster reified as a standalone seed, proving the capture pattern across an
independent faculty. `learning_core.json` holds **60 `Term.*` nodes + 60 edges** exposing three named
predicate Terms (the decisions that were already DSL-built and seeded via `_term_to_mind`, now shipped
as a captured seed), registered with NO Python installer:

| named edge | predicate | verified from seed |
|---|---|---|
| `salience_predicate` | `co≥3 ∧ co·n_events/(n_from·n_to) ≥ 2` | predictive (lift 3.33) True; high-count noise (lift 0.89) False |
| `screening_predicate` | `n_cond≥5 ∧ co_cond·n_ticks/(n_cond·n_y) ≤ 1.5` | True (screened) |
| `intervention_predicate` | `n_with≥5 ∧ n_with/n_a ≥ 2·((n_y−n_with)/(n_ticks−n_a))` | True (causal) |

All three load and evaluate from the seed — **GREEN**, including the signal-vs-noise discrimination
that is the salience predicate's whole point.

### Induction pipeline + observe recognitions reified → all four clusters now boot from seeds

`learning_core` regenerated to also carry the **induction pipeline** (75 nodes/edges): `induce_pattern_term`
= `AntiUnify{insts}`, `induce_keep_gate_term` = `And{Gte{FixedCount{AntiUnify{insts}}, min_fixed},
Gte{Count{insts}, min_support}}`, `rule_covers_term` = `Covers{pattern, instance}`. Verified from the
seed: anti-unify two matching change-instances → the shared pattern; keep-gate keeps (fixed 3 ≥ 2,
support 2 ≥ 2) and rejects all-differ (fixed 0); covers accepts a fresh match (extra keys ok) and
rejects a non-match — the full induce→gate→test loop runs as seed-loaded graph data. **GREEN.**

New seed **`perception_core.json`** (21 nodes/edges) carries the observe-cluster recognitions:
`gauge_recognition_term` = `Argmax{Filter{NodesOfType(BodyType), net_shed > thr−1}, net_shed}` (picks
`turnbar` net 11), `turns_term` = `Max{Minus{gauge_full, shed}, 0}` (13 and a 0-clamp), `novelty_ch1_term`
= `Count{FilterList{ScalarAttrTriples{skip:"Term."}, t, Not{In{t, seen}}}}` (2 on a clean substrate —
and the seed's own `Term.*` nodes are correctly skipped). All **GREEN** from the seed.

**All four genuine-cognition clusters now have their decision data as loadable graph data**, across
three modular seeds — exactly CLAUDE.md's "an agent declares the seeds it wants":

| seed | faculty | graph data |
|---|---|---|
| `decision_core` | goals + action-scoring | `create_goal_from_request` Rule + goal-weight / action-score / quality Terms |
| `learning_core` | causal inference + implied-rule induction | salience / screening / intervention predicates + induce-pattern / keep-gate / covers Terms |
| `perception_core` | observe recognitions | gauge-type / turns / novelty-channel-1 Terms |

Every named Term and Rule loads from its seed and evaluates/fires to its parity-verified value, with
zero Python in the decision path. The `CuriousAgent`'s genuine cognition now has a complete
graph-native replacement that boots from seeds — the precondition for the wholesale Python deletion.

### Composed boot proven: the agent runs from seeds on a bare substrate (no `CuriousAgent`)

`substrate/boot_core.py` is a thin world-adapter-layer helper (loader only, no decisions): create a
bare `Substrate`, add the agent root, load the three core seeds through the Rust loader, return
`(substrate, agent_root)`. No `CuriousAgent` Python class is involved — the agent is the graph.

Verified the composed agent end-to-end (`boot_core()` → bare substrate + 3 seeds):
- **All 12 named faculties present exactly once** — no name conflicts across `decision_core` /
  `learning_core` / `perception_core` (the modular-seed coherence check CLAUDE.md describes).
- **Full decision cycle runs from graph data**: (a) post a `goal_request` → `run_rules` fires the
  seeded Rule → `Goal{reach_exit}` created → goal-weight = 3.0; (b) three `ActionCandidate`s scored via
  the seeded `action_score_term` (`[0.1, 0.29, −0.19]`) → `Argmax` picks #1; (c) `salience_predicate`
  fires True on a lift-3.33 pair. **GREEN.**

So the agent's genuine cognition **boots from seeds and runs its decision loop on a bare Rust substrate,
with zero Python agent code** — only the thin seed-loading adapter + `tick()`/`run_rules()`. This is the
architecture's end-state demonstrated on the migrated core: *the agent is a graph, running in Rust;
Python only assembles and ticks it.* The wholesale deletion of the `CuriousAgent` Python is now gated
only on the world adapters retargeting onto `boot_core` (ingest world I/O → these seeds → tick → emit),
behind the Python regression bench until that retarget is complete.

And the act-choice composes into a **single graph evaluation** that reads the seed: graph-native
`choose_action` is `Argmax{NodesOfType(ActionCandidate), c, EvalSubgraph(Pick(Neighbours{agent,
"action_score_term"}))}` — the `Argmax` binds each candidate to `c`, and `EvalSubgraph` evaluates the
*seeded* `action_score_term` with that binding, so the selection AND the per-candidate scoring are both
graph data composed at eval time (no per-candidate Python loop). Verified on the booted agent: scores
`[0.1, 0.29, −0.19, −0.08]` → picks #1. **GREEN.** The world adapter's only role is previewing legal
actions into `ActionCandidate` nodes (mechanical I/O) and triggering the eval — exactly the permitted
adapter contract.

### Live loop: a thin world adapter drives the seed-booted agent (no `CuriousAgent`)

`domains/curiosity_world.py` (`CuriosityWorld`, ~80 lines, no decisions) is the first world adapter
retargeted onto `boot_core`. It does the three permitted mechanical things: **ingest** (stamp perceived
world nodes, grow a seen-triple memory), **preview** (for each legal action, measure the score INPUTS
the policy reads — novelty as a set-difference `|preview_triples − seen|`, quality as the
understood-fraction — and stamp an `ActionCandidate`), **emit** (read back the chosen action). It never
weights or selects: the decision is the seeded `action_score_term` + `Argmax`, evaluated in Rust.

Verified the **closed live loop** end-to-end on the booted agent:
- choice 1 (a familiar room vs an unseen one): picks **`go_novel`** — curiosity seeks the unseen
  (novelty 2 → score outweighs the familiar's 0);
- after acting on the novel room and observing it, its triples enter `seen`, so its novelty is
  **consumed** (re-preview scores it as familiar);
- choice 3 (the explored rooms vs a fresh frontier): picks **`go_frontier`** — the curiosity gradient
  has shifted to the new unseen region. **GREEN.**

Stale candidates are cleared between choices (`remove_node`), so each `Argmax` sees only the current
options (verified: 2 candidates after choice 1, 1 after choice 2 — no accumulation). This is the whole
architecture running live: **world adapter (measure + ingest/emit) + seed-booted Rust agent (decide via
graph data), with no `CuriousAgent` Python anywhere in the loop.** The curiosity behaviour — seek
novelty, satisfy it, move the frontier — emerges from the seeded `action_score_term`, not from adapter
code.

### Durable regression suite: `tests/test_migration_parity.py`

The session's ad-hoc parity checks are codified as a runnable pytest suite (**14 tests, all passing**),
so every GREEN claim in this ledger is re-runnable — the gate for deleting the Python `CuriousAgent`.
Three layers:
1. **the six minted primitives** behave like their Python twins (`NodesOfType`, `AntiUnify`,
   `FixedCount`, `Covers`, `LookaheadValue` incl. the planning-flips-the-choice case, `ScalarAttrTriples`
   incl. Float-exclusion / Term-skip);
2. **each faculty evaluates from its actual seed** to its known value (goal-weight 3.0, action-score
   0.29, quality 0.7, the `create_goal` Rule firing, the causal predicates' signal-vs-noise, the
   induce→gate→test pipeline, the gauge/turns recognitions);
3. **the composed boot** has no cross-seed name conflicts and the **live curiosity loop** runs
   (`go_novel` then `go_frontier`).

Run: `pytest tests/test_migration_parity.py` — 14 passed in 0.06s. The migration's correctness is now a
regression, not a pile of one-off scripts.

### Aesthetic goal-prior reified (beauty = compressibility = order)

The agent's universal goal-prior — `_grid_aesthetic_value`, the value it climbs when no explicit goal is
given — migrated into `perception_core` (now 50 nodes/edges, 7 named Terms). Beauty = compressibility:
the weighted sum `0.6·best + 0.25·order + 0.15·simplicity`, where `order = 1 − entropy/max_entropy`,
`simplicity = 1/n_colours`, and the colour **entropy** `−Σ(k/n)·log(k/n)` is a genuine reduction now
expressed as `Neg{Sum{counts, k, (k/n)·Log(k/n)}}` (using the `Log` primitive). Captured as four named
Terms (`entropy_term`, `order_from_entropy_term`, `simplicity_term`, `aesthetic_value_term`), verified
from the seed across three colour-distributions — entropy/order/aesthetic all parity-GREEN (e.g.
counts [2,1,1] → ent 1.0397, order 0.0536, aesthetic 0.5434). The "what is the goal when none is given"
faculty is now graph data: the agent's drive toward order is the same MDL/compression selector that
runs the whole substrate, applied to states. Regression suite now **15 passing**.

### Epistemic/ontological judgment cluster reified: `epistemics_core.json`

A whole band of the agent's **judgment predicates** — the "~110 judgment methods" the migration plan
flagged as the hard core — turn out to be DSL-built Terms already, and capture the same way. New seed
`epistemics_core` (50 nodes/edges, 5 named predicates), each verified from the seed:

| named edge | judgment | verified |
|---|---|---|
| `saturation_predicate` | "I know this well enough" — `saturation_count ≥ 30` | True at 31, False at 5 |
| `ephemeral_predicate` | transient effect — `n_left_view≥8 ∧ cease-fraction > 0.4` | True (muzzle-flash type) |
| `persistent_object_predicate` | permanent object — `n_left_view≥8 ∧ cease-fraction < 0.2` | True (wall type) |
| `law_predicate` | regime-pinned invariant — `obs≥6 ∧ distinct=1 ∧ global_distinct≥2` | True (Galileo's `acc_y` in `falling`) |
| `conservation_predicate` | globally-constant composite — `observed≥6 ∧ distinct=1` | (momentum Σm·v) |

These are the agent's epistemics (what it knows), ontology (effect vs object — object permanence
withheld from flicker), and physics-law discovery — all graph data the agent reads and can edit. They
were never Python decisions; the Python was only the evaluator. Regression suite now **16 passing**.

The migration now covers **six faculties across four seeds** (`decision_core`, `learning_core`,
`perception_core`, `epistemics_core`), every named Term/Rule parity-green from its seed. The pattern —
the genuine cognition is small graph data; the Python is bookkeeping + evaluation that dissolves — holds
the deeper it goes.

### Composite seed: `curiosity_agent` — one declaration boots the whole agent

The four core seeds are bundled into a composite `curiosity_agent` seed (deps-only, no installer) that
`depends_on` (`decision_core`, `learning_core`, `perception_core`, `epistemics_core`). A world adapter
requests this one seed and the loader resolves the closure — exactly CLAUDE.md's *"an agent declares the
seeds it wants; the loader resolves the dependency closure and installs them in topological order."*
Verified: `REGISTRY.resolve(["curiosity_agent"])` returns the four core seeds (each before the
composite) and `boot_core` (now loading all four) yields **all 21 named faculties present exactly once**
— no cross-seed name conflicts. Regression suite **17 passing** (adds the full-21-faculty boot check and
the composite-closure check).

This is the migrated CuriousAgent's genuine cognition as a single declarable agent definition: 21
decision Terms + 1 construction Rule across 4 modular seeds, booting on a bare Rust substrate with zero
Python agent code, every value parity-verified.

### Resource valuation added to `decision_core`

The resource-management value functions joined `decision_core` (now 38 nodes/edges, 5 Terms + 1 Rule):
`resource_value_term` = `1 − current/observed_max` (scarcity — how badly a resource needs preserving)
and `resource_preservation_satisfaction_term` = `current/observed_max` (a preserve-resource goal's
satisfaction, so its goal-weight `(1−satisfaction)×priority` rises automatically as the resource
depletes — composing with the already-seeded `goal_weight_term`). Verified from the seed: scarcity 0.7
and satisfaction 0.3 on a resource at 3/10. The agent's drive to preserve a depleting resource is now
graph data feeding the goal-pressure formula. Composite faculty count → **23 named, all present once**;
regression suite **18 passing**. (The exploration-value navigation function — `recency + under-known +
door-to-unknown + salience` with its nested `_door_term`/`_flanked_term` traversal — is expressible and
remains a larger pending capture, best done by running the Python Term-builder through
`add_term_subgraph` rather than hand-transcription.)

### Regression hygiene: the six new primitives don't break the core

After six rebuilds of the Rust core adding `NodesOfType` / `AntiUnify` / `FixedCount` / `Covers` /
`LookaheadValue` / `ScalarAttrTriples` (+ the `rules` seed-section and `add_term_subgraph`), the broad
test slice (`dsl/term/eval/substrate/rewrite/reflect/grammar/seed`) is **287 passed, 1 skipped, 1
failed** — and the one failure is pre-existing and orthogonal: `test_chess.py` `_castling_fen` does
`rights & BB_H1` where `rights = 9.295e18`, a u64 castling bitboard that exceeds `i64::MAX` (9.223e18)
and so round-trips as a Float through `Value::Int`. The migration's additions never touch int/float
width or number encoding (verified by diff — every `i64`/`f64` in the new code is a local inside the
new primitives), so the core DSL/substrate/seed/reflect paths are confirmed regression-clean; the chess
u64>i64 limit is a separate, pre-existing concern.

### Capture tool: Python DSL → seed (no more hand-transcription)

`tools/capture_terms.py` mechanises the seed-capture I had been doing by hand. The missing link already
existed — `substrate/jsonio.py::term_to_json` converts a Python `Term` dataclass (exactly what the
agent's `_make_X_term()` builders return) into the Term-JSON shape the primitives use. The tool chains:
`Python Term → term_to_json → add_term_subgraph → graph_to_dict → seed nodes/edges + named attachment
edge`. So a faculty is now captured by writing its formula once in readable Python DSL —
`Minus(Lit(1.0), Div(Attr(Var("self"), "current"), Attr(Var("self"), "observed_max")))` — and naming
it; `build_term_seed(...)` emits a loadable, parity-faithful seed.

Proven: re-capturing `epistemics_core` from Python DSL reproduces the hand-built seed **exactly** (50
nodes / 50 edges, identical structure) and all five predicates evaluate correctly from the generated
manifest. A regression test (`test_capture_tool_roundtrip`) locks it: a DSL `Term` → tool → loaded seed
→ correct value. Suite **19 passing**.

This retires hand-JSON for the remaining captures: the deep nested faculties (exploration-value with
`_door_term`/`_flanked_term`, etc.) are now captured by expressing the formula in Python DSL (or calling
the agent's existing builder, which already returns a `Term`) and handing it to `build_term_seed` — a
mechanical sweep, not transcription. The one-off tool is deletable with the Python it migrates.

### First mechanical sweep: `motor_core` captured from the agent's own builders

`CuriousAgent` instantiates instantly and its `_*_value_term()` builders return `Term` objects directly,
so the sweep is: **call the builder → `term_to_json` → `build_term_seed`**. Captured the spatial-motor /
navigation value functions into `motor_core.json` (**209 nodes/edges**, far past hand-transcription
scale) — including the deep `exploration_value` (the flagged "pending larger capture") with its nested
`_door_term`/`_flanked_term` traversal, `Filter`/`Exists`, and `motor_value`/`attention_value`'s spatial
math (`Vec`/`Cos`/`Sin`/`AngleBetween`/`Rotate`):

| named edge | faculty |
|---|---|
| `motor_value_term` | feedback control — turn toward target, move when aligned |
| `attention_value_term` | orient to a salient pop-out (gated above the salience floor) |
| `exploration_value_term` | navigate — recency + under-known + door-to-unknown + salience |

Faithful by direct check: for each, `inner.evaluate(term_to_json(builder()))` == the seeded
`EvalSubgraph` value (motor 0.99927, attention 0.67959, exploration 3.10e8) — **GREEN**. `motor_core`
registered, added to the `curiosity_agent` composite and `boot_core`; suite **20 passing** (the composed
boot now checks **26 named faculties present exactly once**). This is the sweep proving itself: three
rich faculties — one of them the deepest in the agent — captured in a single call with zero
transcription, parity guaranteed by the round-trip property.

### Sweep continued: 9 more faculties from builders (motor 6, experimentation 6)

Probed every `_*_term()` builder — all 11 untouched ones serialize cleanly via `term_to_json` — and
swept them. `motor_core` regenerated to **6 terms** (adding `forward_wall_term` /
`forward_wall_penalty_term` / `operate_control_term` to the three already there; 325 nodes/edges); new
seed `experimentation_core` (**6 terms**, 119 nodes/edges) holds the curiosity + active-experimentation
drives: `order_n_curiosity` (prediction-error pull), `abs_info_gain`, `event_salience`,
`intervention_lift` (do-contrast lift), `hypothesis_test` (open-hypothesis check), `experiment_value`
(pull toward *doing* the test). Each verified faithful (direct `term_to_json` eval == seeded
`EvalSubgraph`): motor 0.99927 / attention 0.67959 / exploration 3.10e8 / intervention-lift 6.667 /
etc. — **all GREEN**.

`experimentation_core` registered, added to the `curiosity_agent` composite + `boot_core`; the composed
boot now verifies **35 named faculties present exactly once** across **six atomic seeds + the
composite**. Suite **20 passing**. The migration's coverage is now broad — goals, action-choice,
resource valuation, causal inference, induction, observe recognitions, aesthetic prior, epistemic/
ontological judgment, spatial-motor control, navigation, curiosity drives, and active experimentation —
all graph data, all parity-faithful, captured (latterly) by mechanical sweep from the agent's own
builders.

### Standing-Term sweep complete: `decision_core` regenerated, goal-satisfaction added

A full scan of every `-> Term:` method confirms the **standing named-Term faculties are now all captured**.
`decision_core` regenerated cleanly through the tool — inline decision Terms expressed in readable DSL
(`goal_weight`/`action_score`/`quality`) + builder-captured Terms (`resource_value`,
`resource_preservation_satisfaction`, and the newly-added `visit_satisfaction` / `know_position_satisfaction`)
+ the `create_goal_from_request` Rule preserved — **7 Terms + 1 Rule, 47 nodes/edges**, all faithful and
the Rule still fires. The composed boot now verifies **37 named faculties present exactly once**; suite
**20 passing**.

The only `-> Term:` methods left uncaptured are **not standing faculties**: the parameterized
goal-satisfaction *factories* (`_make_affordance_probe_satisfaction(target)`,
`_make_achieve_attr_satisfaction(attr, val)`, `_make_survey_satisfaction(threshold)`, and the
communicate/inform/inquire satisfactions) bake concrete goal-specific values, so they are **per-goal
templates a goal-construction Rule instantiates**, not edges on `agent_root`; and `_spec_to_term` /
`_door_term` / `_flanked_term` are converters / sub-terms (the door/flanked ones already live inside
`exploration_value_term`). These belong to the **Rule-heavy phase** (parameterized goal-construction
Rules, surprise→investigation, impasse, communication) — a distinct, larger effort than the Term sweep,
which is now done: **37 decision Terms + 1 Rule across six atomic seeds + the composite, every value
parity-faithful.**

## Rule-heavy phase begins: parameterized goal construction

The first faculty beyond standing Terms — **parameterized goal construction** — needed a new primitive
to crack the crux: a typed goal's satisfaction reads an attr whose KEY is goal-specific
(`Eq(Attr(target, attr_name), val)`), but `Attr.key` is a static `Sym`, so a single Rule couldn't
parameterize it. Minted **`AttrByName{node, name}`** (7th primitive) — dynamic attribute access: read
`node`'s attr whose key is the *value* `name` evaluates to. Wired across term.rs/jsonio/reflect + the
Python DSL (`substrate/dsl.py`); cargo-clean, rebuilt.

That one primitive collapses the whole baked-factory family (`_make_achieve_attr_satisfaction(attr,val)`,
survey, affordance-probe, …) into **one generic satisfaction proto Term**:
`Eq{AttrByName{Pick(Neighbours{g,"target"}), Attr{g,"target_attr"}}, Attr{g,"target_value"}}` — reads
the target's attr *named by the goal's own `target_attr`*. New seed `goal_construction.json` (9
nodes/edges) ships that proto + a Rule `create_achieve_attr_goal` that mints a typed `Goal` from an
`achieve_attr_request` (carrying label/priority/target_attr/target_value + `target` edge), pointing its
`satisfaction_term` at the shared proto.

**Verified end-to-end**: post an `achieve_attr_request{open_the_door, target=Door, target_attr=open,
target_value=1}` → `run_rules` mints the Goal → the seeded `goal_weight_term` reads the generic proto:
door shut → unsatisfied → weight **5.0** (full pressure); flip `Door.open=1` → satisfied → weight
**0.0**. **GREEN.** This is the Rule-heavy pattern: a construction Rule + a dynamically-parameterized
generic satisfaction Term (parameterization enabled by `AttrByName`), composing with the existing seeded
goal-pressure formula so a typed goal's pressure tracks the world. `goal_construction` registered, added
to the composite + `boot_core`; **38 named faculties + 2 Rules across seven atomic seeds**; suite
**21 passing**.

**Template generalizes — second typed goal (visit).** Added `visit_satisfaction_proto` +
`create_visit_goal` to `goal_construction` (now 2 protos + 2 Rules, 17 nodes/edges), proving the pattern
isn't achieve-attr-specific. The visit proto is a *different satisfaction shape* — membership
`In{Pick(Neighbours{g,"target"}), Neighbours(Pick(InNeighbours{g,"has_goal"}), "at_position")}` (is the
goal's target among the owning agent's `at_position` neighbours) — but reads only from `g` like every
proto, so the same `goal_weight` mechanism drives it. Verified end-to-end: post `visit_request` → Rule
mints the Goal → weight **3.0** while away, **0.0** once an `at_position` edge to the target appears.
**GREEN.** Two goal families now run from one seed via the identical construction-Rule + generic-proto
template; suite **22 passing**, **39 named faculties + 3 Rules**.

### Self-monitoring is largely already graph-native; introspective recall captured

Inspecting the surprise→investigation cluster: the **`rule_surprise_top_cause` Rule is already fully
graph-native** — it picks the max-salience existential cause via nested `Argmax`/`MaxOver`/`Filter`/`Let`
Term-trees (no Python callback), built by `make_rule` as graph data. So the genuine self-monitoring
*analysis* ("what caused this surprise?") is already a graph Rule; the remaining Python is the
subroutine-construct/execute `rule_then_callable` plumbing. Captured the cluster's clean introspection
Term — **`wonder_why_query_term`**, the windowed event-recall the investigation runs:
`Filter{Neighbours{agent,"logged"}, e, at_tick−window ≤ e.timestamp < at_tick}` — added to
`experimentation_core` (now 7 terms, 136 nodes/edges). Verified: with `subr{at_tick:20, window:5}` it
recalls exactly the events in `[15,20)` (3 of 6). **GREEN.** Suite **23 passing**, **40 named
faculties + 3 Rules across seven atomic seeds**. The self-monitoring frontier is narrower than it
looked — the decision/analysis is graph data; what's left is making the imperative investigation
*subroutine* (currently a Python callback) graph-resident, a distinct larger effort.

### Self-monitoring captured: the surprise→investigation cascade is already graph-native

The frontier turned out *already crossed*: `_do_surprise_investigation` was **DELETED** (code comment:
"The 7-rule cascade on surprise_investigate runs the full investigation path without any Python in it").
The faculty is three chained `make_rule`-built Rules — construct (mint the per-firing investigation
subroutine + its windowed recall query), execute (run the query into `causes_set`), top-cause (pick the
max-salience existential cause by nested `Argmax`/`MaxOver`/`Filter`/`Let`). All graph data, no callback.

So it just needed *capturing* — which exposed the **rule-capture enabler**: `make_rule` already stores a
Rule's `match` / `where` (`term_to_json`) / `effect` (`{"__term__": …}`-encoded) on the node, exactly
what the Rust `parse_rule_json` accepts. Added `tools/capture_terms.py::rule_node_to_dict` — the
mechanical inverse of the loader (`id`→`name`, singular `effect`→`effects`) — so any graph-native Rule
the agent builds is captured by reading its node. Auto-extracted the 3 surprise Rules (incl. their
nested-`Argmax` effects + where-clauses) from a `CuriousAgent` and wrote `self_monitoring.json`
(depends_on `experimentation_core` for the recall). Verified they **install + parse**: loading the seed
raises `rule_count` by exactly 3. **GREEN.** `self_monitoring` registered, added to the composite +
`boot_core`; **eight atomic seeds + composite**, suite **24 passing**.

(Honest scope: the 3 rules load + parse faithfully — auto-captured from the agent's own graph-native
build, which the agent itself runs to fixed point. Full end-to-end *cascade firing* needs a staged
surprise scenario — Event + EventBaseRate nodes + a trigger — which is a runtime-scenario verification
beyond this capture; the construction-Rule firing was proven separately on `create_goal`/`create_*_goal`.)

### Full rule sweep: all 17 graph-native Rules captured

With `rule_node_to_dict`, swept **every** `_ensure_*_rule` builder — triggering all of them on a
`CuriousAgent` surfaces **17 graph-native Rules**, all auto-extracted (incl. `rule_surface_curiosity`'s
11 effects, the nested-`Argmax` causal rules, etc.) and distributed into themed seeds:

| seed | rules added |
|---|---|
| `memory_core` (new) | consolidate-episode, episode-from-message, forget-old-episode |
| `reflex_core` (new) | emotion-EMA-update, pointer-from-grounded-concept |
| `learning_core` | cause-selection, hypothesis-mint, intervention-mint, intervention-sync |
| `goal_construction` | + allocate-goal-frame, chunk-resolved-goal (now 4 Rules) |
| `self_monitoring` | + monitor-self-and-partner, author-asymmetry-assessment (now 5 Rules) |
| `experimentation_core` | surface-curiosity |

Verified: every seed's rules parse, and the composed boot installs **all 20 graph-native Rules** (1
create-goal + 4 goal_construction + 5 self_monitoring + 4 learning + 3 memory + 2 reflex + 1
experimentation) — `rule_count() == 20` after `boot_core`. **GREEN**, suite **25 passing**, **ten atomic
seeds + composite, 40 named Terms + 20 Rules**.

This closes the *capture* phase: both directions exist (`term_to_json`→`add_term_subgraph` for Terms,
`rule_node_to_dict` for Rules) and **the agent's entire graph-native repertoire — every decision Term
and every rewrite Rule it builds — is now captured into loadable seeds**, mechanically, from its own
builders. What remains is the **burn**: retarget the existing world adapters onto `boot_core`, run full
bench-parity against the Python `CuriousAgent`, then delete the Python (kept behind the regression bench
until the last call site migrates).

## Tally so far

Genuine graph data produced + parity-green: **goal weight Term, goal construction Rule, action-score
Term, quality ratio Term, novelty channel-2 Term, choose_action Argmax, gauge-type recognition Argmax,
turns clamp Term, salience/lift predicate, confound-screening predicate, interventional-causation
predicate, induce_rule fixed + keep-gate, covers rule-test, k-step lookahead, novelty channel-1 /
full `_novelty_count`** (15 pieces, 4 clusters) + **6 new Rust primitives (`NodesOfType`, `AntiUnify`,
`FixedCount`, `Covers`, `LookaheadValue`, `ScalarAttrTriples`)**. The causal-learning cluster's decisions were *already*
graph Terms (seeded via `_term_to_mind`) — verified faithful, so their Python eval-wrappers dissolve;
no migration needed, only confirmation. `AntiUnify` + `FixedCount` make the implied-rule / win-rule
induction faculty fully composable from native primitives (pattern + MDL specificity + support + the
keep-gate), all parity-green.

**Three flagged Layer-B gaps → ALL CLOSED:** ✅ `anti_unify` (now `AntiUnify`); ✅ k>1 lookahead
recursion (now `LookaheadValue`); ✅ novelty channel-1 attr-enumeration (now `ScalarAttrTriples`).
(`FixedCount` and `Covers` were follow-on primitives the induction pipeline needed, not among the
three.) No flagged primitive gaps remain — every recursion/enumeration the DSL couldn't express is now
a tight Rust primitive, each parity-green, composed in graph. The
action-scoring/selection cluster — the agent's entire act-choice — is graph data (decision = `Argmax`
of the curiosity-score Term over previewed candidates); the observe/perception cluster's genuine
*recognitions* (gauge-type, turns) are graph Terms while its autopoietic fold is observe-Rules + adapter
ingest. Recurring shape confirmed across 3 clusters: **a recognition/choice = a (thresholded) `Argmax`
over a typed node population**; the rest dissolves. Flagged Layer-B gaps: novelty channel 1
(attr-enumeration); k>1 lookahead recursion (tree-fold). Dissolves confirmed: `_goal_satisfaction`, `_get_top_level_goals`, the policy reads,
`senses`/`acts`/`models`, `is_instance_saturated`. One honest gap flagged (novelty channel 1 — an
attr-enumeration primitive). The agent's goal-pressure and action-choice — its core drives — are now a
few small Terms + one Rule. Pattern holds every cluster: read → strip glue (dissolves) → author the one
formula/decision → parity-check → ledger; when the DSL genuinely can't express it, mint the primitive
in Rust (not Python) and flag what's still missing rather than faking it.


## Cluster: minting recurrence / accommodation

| Python faculty | graph-native form | status |
|---|---|---|
| episode-wide predicate occurrence ledger | `MintingRecurrenceEpisode` + immutable `ResidualSegmentEvidence` + `PredicateRecurrenceCandidate`; persistence is `Count(supported_by_segment)` | **parity GREEN** |
| threshold/due selection and once-only handoff | `mrl_offer_due_once` creates one native `Observation` only after native `Gte(persistence, mint_after_quanta)` | **parity GREEN** |
| terminal/mint provenance | `mrl_record_offer_terminal` and `mrl_record_mint_result` retain offer status and candidate/episode→axis links | **parity GREEN** |
| aperture residual extraction / evidence emission | Python adapter remains: it reads trajectory residuals and posts immutable facts, then reads results | adapter boundary |

The policy is explicitly retained: one invocation is one episode; tuple witnesses project to a predicate-only candidate; counts accumulate across intervening absences; each candidate gets one offer. `shape_decode_loop` remains the sole recognition/deduplication/axis-mint authority. The held-out semantic consumer proves that a predicate-keyed axis is not itself sufficient for downstream use: only a matching graph-resident `bind(ITEM,SLOT)` witness licenses the SLOT operation. See `MINTING_RECURRENCE_LEDGER_PREREG.md` and `MINTING_RECURRENCE_LEDGER_RESULTS.md`.
