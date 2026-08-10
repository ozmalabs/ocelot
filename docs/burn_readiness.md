# Burn readiness — what deleting `CuriousAgent` actually requires

> **STATUS: COMPLETE (commit 56529c6d).** `domains/curious_agent.py` is DELETED.
> The entire decision/value/judgment/cognition surface — perception, intent,
> conversation, render, teaching, the Frame layer, goals, planning, spatial
> routing, the communicate-action faculty, and the self-growing Γ_meta substrate
> — is graph-native on the seed-booted WorldAdapter (Rust runtime + seed
> manifests), zero Python agent logic. The parity gate (green 25/25 on its final
> run, seed-boot ≡ CuriousAgent) + the capture tooling + 14 tracked driver
> scripts went with it; the ~650-test migrated suite is the regression bench now.
> 25 untracked driver scripts remain in scripts/ for the author to retire/
> retarget. CLAUDE.md's end state reached. Everything below is the historical
> record of how the burn proceeded.


The migration captured the agent's **genuine decision cognition** into seeds (see
`docs/migration_ledger.md`): 40 named Terms + 20 graph-native Rules across 10 modular seeds + the
`curiosity_agent` composite, booting on a bare Rust substrate via `substrate/boot_core.py`, driven live
by the thin `domains/curiosity_world.py`, locked behind `tests/test_migration_parity.py` (25 tests),
with 7 minted primitives and a mechanical capture path (Terms via `add_term_subgraph`, Rules via
`rule_node_to_dict`) from the agent's own builders.

**That is the hard, interesting part of the project, and it is done.** This file records why the
*deletion* — the burn — cannot responsibly happen yet, and exactly what stands between here and there.

## The blast radius (measured)

`domains/curious_agent.py` is **18,501 lines**. Files that **instantiate a live `CuriousAgent()`**: **99**
(58 `tests/`, 39 `scripts/`, 1 `domains/` = `arc3_full_seed.py`, 1 `tools/` = `capture_seed.py`). 126
files reference it in total. **Zero** of these call sites have been retargeted onto `boot_core`.

Deleting the file now breaks all 99 — the entire experiment suite (chess, doom, walker, arc3, chat,
audio, vision, language, teacher). Per the migration rule (`CLAUDE.md`: *"existing Python … keeps
working as a regression bench … burn the boats at the END … until the last call site migrates"*), the
precondition is emphatically unmet.

## What the seeds DON'T yet cover

`CuriousAgent` bundles more than the decision surface the seeds captured. Still resident only in Python,
and required by the 99 call sites:

- **The observe / ingest pipeline** — `observe(substrate)`: world nodes → mind_graph, the autopoietic
  fold. (Its *recognitions* are seeded; the fold/bookkeeping that drives them is not.)
- **The `live()` loop** — reset → observe → choose → step, and the no-preview / lookahead scheduling.
- **World integration** — per-world ingest/emit (the ~20 world modules) still call CuriousAgent methods,
  not a thin adapter over `boot_core`.
- **Teacher / language / vision / audio** — `vocabulary_for_language`, `learn_word`, the speech/vision
  pipelines, the LLM-teacher bridge.
- **Caches & name→NodeID indexes** the call sites read directly (`_concept_nodes`, etc.).

The seeds make the agent **decide** in graph data; the class still **perceives, loops, talks, and
integrates worlds** in Python.

## The burn sequence (the real remaining work)

1. **A thin world-adapter base over `boot_core`** — generalise `curiosity_world.py` into the
   ingest→tick→emit contract every world needs (observe = stamp changed nodes; emit = read decisions).
2. **Migrate the observe pipeline** — the autopoietic fold becomes observe-Rules + a Rust ingest
   primitive; the recognitions already seeded plug in.
3. **Retarget the call sites, world by world** — point each of the ~20 world modules + their tests at
   the adapter; delete each world's CuriousAgent usage as it migrates. (Tests are the bench: a world is
   "migrated" when its tests pass against the seed-booted agent.)
4. **Bench-parity gate** — run seed-booted vs Python `CuriousAgent` on identical inputs across the live
   loops; require behavioural equivalence before deleting anything.
5. **Burn** — once the last call site is retargeted and parity holds, delete `curious_agent.py` and the
   one-off capture tooling (`capture_terms.py`, `capture_seed.py`) with it.

## Burn in progress — call sites falling (99 → 94), proven repeatable loop

The burn is underway and converging. The loop, now fully mechanical and green at every step:
**read a bench test → add the (mechanical) adapter feature it needs → write a migrated test that
passes → delete the original `CuriousAgent` site.** Each deletion is gated on a green migrated
equivalent, so the regression bench only ever shrinks by what's already covered.

**Sites burned so far (5):** `test_structure_world`, `test_instance_edge_mirroring`,
`test_world_instances`, `test_frontier_seeking`, `test_predictive_and_boredom`. The `WorldAdapter` grew
to cover everything they needed — instance fold, edge mirror (+ Term-skip, self-loop-skip), both
saturation scopes, freshening, OO `BodyType`/`instance_of`, action-outcome stats + EMAs, discovery,
grounding, the action loop, the goal pointer — all mechanical I/O over seeded decisions.

**Remaining ~94 sites, by effort:**
- **Mechanical sweep** (~30–40 test files): each is "ingest + exercise a faculty + assert," needing at
  most a small mechanical adapter addition (like the 5 done). e.g. `test_temporal_discovery` (body-type
  temporal pairs — a variant of the discovery I built), `test_anticipation`, `test_substrate_awareness`,
  `test_action_object_exploration`, `test_map_planning`, `test_resource_awareness`, …
- **Heavy subsystems** (the `live()`+Γ_meta chess paths, vocabulary/rendering, the language-teacher,
  chat/intent, and the vision/audio perception pipelines): real multi-step work — the Rust audio/vision
  primitives exist, but wiring them into `ingest` + porting the teacher is substantial.
- **39 experiment scripts**: drivers, not tests — most are retargeted onto the adapter or simply
  deleted with the Python they exercise.

**Honest trajectory:** the conceptually hard part is done and the loop is proven, but completing all ~94
sites is a sustained, multi-session campaign — roughly one site per focused pass for the mechanical
tests, plus dedicated efforts for each heavy subsystem. It is *not* completable in a single session, and
faking that by deleting `curious_agent.py` early would break the repo. The disciplined path is to keep
running the loop, world/faculty by world/faculty, bench shrinking, until the last site is covered — then
delete the hull.

## Verdict

The boats are **built and seaworthy** (the agent boots and runs from seeds, zero Python in the decision
path, verified). They are **not yet the only boats** — 99 call sites still ride the Python hull. Burning
the hull now sinks the fleet. The burn is a real multi-phase effort (steps 1–4 above), correctly gated
behind the regression bench. Deleting `CuriousAgent` was **not** done, by design: doing it now would
leave the repository broken, which the "it has to work" standard forbids.

## Burn — STARTED (steps 1+2 built; first world's perception migrated)

- **Step 1 DONE** — `substrate/world_adapter.py`: a thin `WorldAdapter` over `boot_core` (boot the
  `curiosity_agent` seeds → `ingest(world_substrate)` → `tick()` → query), no decisions.
- **Step 2 DONE (instance-tracking half)** — `ingest` mirrors a world's published substrate into
  `WorldInstance` nodes keyed by (type, world-id), carrying scalar attrs, with world edges mirrored
  between instances (deduped via `has_edge`). This is the mechanical core of the old `observe()` fold,
  now in the adapter as pure I/O translation. (The fold's *recognitions* — gauge/novelty/saturation —
  are the already-seeded Terms that read these nodes.)
- **First world retargeted** — `number_world`'s PERCEPTION runs on the seed-booted agent with no
  `CuriousAgent`: `tests/test_number_world_migrated.py` walks the line via the adapter and confirms the
  instance mirror (21 Number instances, 78 Units) and exact cardinality (value k ↔ k `has_unit`). GREEN.

**Language faculty migrated (the grounding layer).** `WorldAdapter.learn_word(name, definition_json)`
materialises a taught definition as a graph subgraph attached to a named `Concept` node by a
`definition` edge; `concept_holds(name, node)` is `EvalSubgraph` of that definition with the node bound
to `x` — the agent classifying by an understood definition, the adapter running the agent's *own*
graph-resident Term (no Python reasoning). `ingest` also wires `agent --knows--> instance` (perceiving =
knowing), which grounded definitions quantify over.

**`number_world` is now 4/5 migrated** (`tests/test_number_world_migrated.py`): perception (structure +
cardinality) AND grounding — `even` (`value % 2 == 0`) and `prime` (`value>1 ∧ no known divisor`, the
recursive quantification over `knows`) both taught as Terms and classified correctly by the seed agent,
NO `CuriousAgent`. `number_world.py` itself imports no `CuriousAgent` (only a docstring mention), so the
world is already hull-free. The one remaining bench test —
`test_concept_needing_absent_structure_is_held` — exercises the **unmet-dependency discipline**
(ground-vs-hold: hold a word as a predicate when it references attrs/kinds the agent hasn't met). That's
a genuine faculty (walk the term's referenced attrs/concepts, check each against the graph) not yet in
the adapter; `tests/test_number_world.py` stays as its bench until it's migrated.

Same shape repeats per world: perception migrates via the adapter, grounding via `learn_word`/
`concept_holds`, then world-specific extras (here: the unmet-dependency check) as each lands. Pattern
proven across perception AND language; the sweep across the ~20 worlds is the bulk that remains before
the hull can be deleted.

### Worlds migrated

| world | status | migrated test |
|---|---|---|
| `number_world` | perception + grounding (even/prime); 1 bench test left (unmet-dependency hold) | `test_number_world_migrated.py` (4) |
| `structure_world` | **fully** — sets/functions perceived + member/subset/injective grounded (all 4 checks) | `test_structure_world_migrated.py` (4) |
| `walker_world` | **fully** (agent path) — perceives Body/Joint + runs the action loop via the seeded curiosity score | `test_walker_world_migrated.py` (1) |

`structure_world` needed only a generalisation of `concept_holds` to extra bindings (binary relations
`member(x,y)`/`subset(x,y)` bind `y` too). `walker_world` exercised the **action loop**: it added
`senses()` (every perceived node type — incl. id-less positional `Body`) and `choose_action(actions,
preview_fn)` — preview each action, measure novelty, `Argmax` over the seeded `action_score_term` (the
`CuriosityWorld` loop generalised into the adapter, world-agnostic via `preview_fn`). So the seeded
motor/curiosity faculties now drive a real spatial world. Each world's `*.py` imports no `CuriousAgent`
(docstring only); the seed-agent path covers their tests. **34 migration tests green** (9 migrated-world
+ 25 parity).

The adapter (`boot_core` + `ingest` + `learn_word`/`concept_holds` + `senses`/`choose_action`) is now a
small, general host: each new world is "ingest + (teach its words) + (run its loop)", with occasional
generalisations that then serve every later world. Three worlds down (number, structure, walker); the
remaining ~17 are the same loop, with the bigger ones (vision/audio pipelines, arc3) needing their
perception primitives migrated too.

### Observe-pipeline core migrated (the heart of step 2)

The foundational observe tests — `test_world_instances`, `test_instance_edge_mirroring`,
`test_frontier_seeking` — are now covered by the adapter (`tests/test_observe_pipeline_migrated.py`).
`ingest` does the full instance-tracking fold: WorldInstance creation keyed (type, world-id) with
`world_type`/`world_id` + scalar attrs; **`n_observations`** accumulation (saturation reads it);
instance-instance edge mirroring with **dedup** (`has_edge`); and the **freshening count**
(`last_freshening_count` = instances that gained NEW info this ingest — a new instance or a new edge,
NOT an attr change; id-less nodes never freshen). All mechanical bookkeeping, all GREEN.

This is the heart of step 2 — the observe pipeline the whole experiment suite relies on now runs in the
adapter, world-agnostic. With perception (incl. freshening/saturation bookkeeping), grounding, and the
action loop all general in the adapter, the remaining worlds are largely "wire up + teach + test", and
the burn's step-2 risk is retired.

**Per-instance saturation migrated** (`tests/test_instance_saturation_migrated.py`): `ingest` now also
tracks `saturation_count` — the complement of freshening: 0 on a new instance, climbs on stable
observations, decoupled from attr churn, resets to 0 (both endpoints) on a new edge. The adapter's
`is_instance_saturated(nid)` runs the SEEDED `saturation_predicate` (`saturation_count ≥ 30`) on it, so
the observe bookkeeping connects end-to-end to the seeded epistemic discipline: not saturated at ~4,
saturated past 30. **44 migration tests green** (19 migrated + 25 parity). The observe pipeline now
reproduces both counters the seeded recognitions read (`n_observations`, `saturation_count`) and the
curiosity drive reads (freshening) — the full perceptual substrate, world-agnostic.

**Per-(type,attr) epistemic state migrated** (`tests/test_epistemic_state_migrated.py`): `ingest` now
also builds `Attribute` nodes keyed (type, attr) carrying `type_name`/`attr_name`/`observed_count`/
`distinct_count`/`saturation_count`, with the attr-value memory adapter-side. `observed_count` climbs
each ingest; `saturation_count` resets to 0 on a NEW distinct value (else climbs); `distinct_count`
tracks the value-set size. `is_saturated(type, attr)` runs the SAME seeded `saturation_predicate` on the
`Attribute` node as `is_instance_saturated` does on a `WorldInstance` — **one policy, both scopes**,
realized in the adapter. **48 migration tests green** (23 migrated + 25 parity). The two saturation
scopes the agent's epistemic discipline spans (per-instance, per-attribute) now both run on the seed
agent and read the one seeded policy.

**Causal discovery migrated (the largest observe-side subsystem)**
(`tests/test_discovery_migrated.py`): the adapter records activity (`record_event`) into an event log +
per-kind/lag-1-transition co-occurrence counters (mechanical bookkeeping), and `discover_relations`
stamps a `PairStat{co, n_from, n_to, n_events}` per candidate transition and promotes the ones the
SEEDED `salience_predicate` accepts to `Relation` (`rel_N`) nodes. Verified the salience discrimination:
on a "move move hunt damage"×10 stream, `hunt→damage` (lift ~4, predictive) is discovered while
`move→move` (lift ~1, ubiquitous) is rejected as noise; pure noise discovers nothing. The reasoning is
the seed; the adapter counts + reifies what the predicate accepts. **52 migration tests green** (27
migrated + 25 parity). (The full `test_discovery` also drives a chess `live()` loop and adds a Γ_meta
production per relation — that needs the chess world + production machinery, deferred; the salience
DECISION layer is what's migrated here.)

**Current-goal pointer migrated** (`tests/test_goals_migrated.py`): `set_goal(wi, priority)` maintains a
single `wants` edge (create with priority / replace — one goal at a time / clear), tracking
`current_goal_wi`. Mechanical pointer-setting (recording a chosen goal), distinct from the seeded
goal-pressure faculty that decides which. **55 migration tests green** (30 migrated + 25 parity).
(`pick_goal` — choosing the nearest UNSATURATED instance — is a decision over distance + the seeded
saturation predicate, deferred.)

### Tally — the observe + grounding + action + goal-pointer surface is migrated

Migrated test files (all green): `number_world`, `structure_world`, `walker_world`, `observe_pipeline`,
`instance_saturation`, `epistemic_state`, `discovery`, `goals` (9 files, 30 tests) + the 25-test
core-cognition parity suite = **55 green**. The `WorldAdapter` (`boot_core` + ingest/learn_word/
concept_holds/senses/choose_action/is_saturated/record_event/discover_relations/set_goal) is a stable,
near-complete runtime host: every faculty's DECISION is a seeded Term/Rule; the adapter only translates
I/O and counts. The hard, uncertain infrastructure is done. Remaining is integration breadth into
larger subsystems against this proven host: the `live()`+Γ_meta chess paths, `pick_goal`, vocabulary/
rendering, and the vision/audio perception primitives (their Rust primitives already exist; wiring
them into `ingest` is the work).

### Sub-agent batch burns + the recursion depth fix (82 → 81)

The burn now runs as parallel worktree-isolated sub-agents (investigate + add the mechanical adapter
feature + write a migrated test) with serial integration (additive `WorldAdapter` edits + `git rm` the
original). Recently burned via this loop: `test_groups`, `test_rings`, `test_recursion`,
`test_meta_curiosity_and_t3`, `test_master_thread`, `test_reflexes`, `test_procedure`.

`test_recursion` was the last to fall and exposed a real Rust limit, not an adapter gap: the migrated
arithmetic (`add`/`sub`/`mod` built from `succ`/`pred`, each returning a node so they compose via
`call_concept`) covered everything **except** `gcd`-by-Euclid, because `gcd∘mod∘sub` re-evaluates a self
subgraph deeper than the `EvalSubgraph`/`Holds` depth budget. That budget was `32` (Python's is `100`).
Raised both arms (`runners/dsl/src/term.rs`) to `256` and rebuilt the native `.so`; the full
migrated+parity suite (229) stayed green, and `gcd` now evaluates. The migrated `gcd` also surfaced a
self-call subtlety worth recording: `self_call`'s rebinds are *sequential* Lets, so a simultaneous
rebind like `x<-y, y<-mod(x,y)` must capture `mod(x,y)` and `y` into temp Lets in the original env first
(otherwise `x`'s new value leaks into `mod`'s args). With that, `tests/test_recursion_migrated.py` covers
all 5 original functions and `tests/test_recursion.py` is burned. **229 migrated+parity tests green.**

### Seeds as graph modularity — the loader now records graph-resident Seed nodes (partial)

`test_seeds` mostly tests the seed system as GRAPH DATA (dependency-closure resolution, version
conflict, cycle detection, graph-resident `Seed{id,version}` nodes + `depends_on` edges) — which is
adapter/registry territory, not agent reasoning. Migrated 11/12 onto the new Rust path
(`tests/test_seeds_migrated.py`): the registry-resolution + conflict/cycle tests carry over verbatim
(they walk the live `substrate.seeds.REGISTRY` graph data, no agent), the two Rust-loader tests carry
over verbatim, and the graph-resident load/idempotent/partial-extend tests now run via a new
`substrate.boot_core.load_seeds_into` + `installed_seeds`. That loader filled a real architectural gap:
the Rust `load_seed_manifest` installs a manifest's content but did **not** record the architecture's
mandated graph-resident `Seed{id,version}` node + `depends_on` edges; `load_seeds_into` resolves the
closure via the registry (graph-data dep walk, topo) and records WHAT it loaded — mechanical bookkeeping,
idempotent, no decisions.

**Not burned.** `tests/test_seeds.py` stays as bench for one test — `test_chat_world_attach` — which
needs a migrated ChatWorld (the trigger is a ChatWorld concern; the seed-loading half it asserts is now
covered by `test_chat_closure_loads_onto_a_bare_substrate`).

### Conversation-stack seed boot UNBLOCKED — the `expectation` manifest fix

The second blocker is FIXED. The conversation-stack manifests (`chat`/`intent`/`conversation`/
`psychology`) used to fail to load onto a bare substrate — and measuring the full `voice` closure showed
the cause was a **single** mis-captured node: `seeds/psychology.json` referenced `Concept{expectation}`
via an external by-name cross-ref but never emitted the node. Root cause is in `tools/capture_seed.py`:
agent-shaped seeds capture against a fresh `CuriousAgent`, whose `__init__` pre-seeds concepts — so a
seed concept CuriousAgent already created (here `expectation`, in psychology's own `_MENTAL_STATES`) isn't
in the install delta (`post_nodes - pre_nodes`) and `_ref_for` emits it as a cross-ref with no local node
to resolve. Re-capturing wouldn't help (the pollution recurs), so the fix is surgical: add the
`expectation` Concept node locally and rewire its `subtype_of` edge — mirroring its sibling mental-states.
With that, the **entire 11-seed voice closure now loads onto a bare substrate** (chat=7, voice=11),
guarded by `test_chat_closure_loads_onto_a_bare_substrate` + `test_voice_closure_loads_onto_a_bare_substrate`.
This is the precondition for any voice/chat agent boot from seeds.

The general capture-tool fix (don't let the CuriousAgent capture target pre-seed a seed's own concepts —
e.g. capture agent seeds against a minimal target, or treat a seed's source-declared concepts as local
even when pre-existing) is worth doing before the next conversation-stack re-capture, but only one node
was actually affected across the whole voice closure, so the surgical fix unblocks the work now.

**242 migrated+parity tests green.**

### Vision faculty migrated — the cortex runs on the WorldAdapter

Vision perception was *already* graph-resident: `domains/vision_graph.GraphEye` lifts the V1 receptive
fields (Sobel x/y edge kernels, DoG salience center/surround) to `Kernel` nodes on a substrate, queryable
via the standard DSL (`Attr(Lit(nid), "role")`). What was still CuriousAgent-coupled was the *agent-side
integration* (`CuriousAgent._update_vision`): build the cortex lazily, project its per-azimuth percepts,
materialise detected shapes, mirror the salience pop-out onto attention attrs. That moved to
`WorldAdapter.update_vision` + `vision_substrate()` + `vision_kernels()` — mechanical I/O over GraphEye's
graph-resident perception: lazy-build a `GraphEye` on its own vision substrate, project N `VisionPercept`
nodes (`perceives` edges) + `VisionPolygon` shape nodes (`sees_shape`) on the main substrate, and write
`attention_x/y`, `attention_salience` (SNR = best/median), `control_ahead` onto the agent root. The
orienting DECISION (turn toward attention when salient) is a seeded Term that READS those attrs — not in
the adapter. `tests/test_vision_migrated.py` (7) drives this on the seed-booted agent with no CuriousAgent:
lazy lifecycle, kernels as graph-resident `Kernel` nodes introspected via the DSL, count-by-role, weight
inspection, per-azimuth projection, and salience-driven attention.

The CuriousAgent vision benches stay as live regression and retire WITH CuriousAgent: `test_vision_graph_eye`
mostly tests `GraphEye`+substrate directly (no CuriousAgent — it SURVIVES the burn, GraphEye is the
graph-resident primitive), and the two CuriousAgent-object tests (`_PERSIST_EXCLUDE` guard, the old-`Eye`
deprecation) are scaffolding about objects being removed, not a faculty to migrate. **249 migrated+parity
tests green.**

### Audio perception faculty migrated — the agent HEARS on the WorldAdapter

Same shape as vision: the perception is already graph-resident in **Rust** (`substrate_rs.audio` decode +
`substrate_rs.speech` cochlea/gammatone/STFT/utterance-recognition); the CuriousAgent coupling was the
agent-side ingest (`AudioWorld`). Moved to `WorldAdapter.ingest_audio_file` + `open_audio_lexicon` +
`audio_signs` — mechanical I/O over the Rust speech pipeline: ensure the audio+speech seed vocabulary is
loaded (via `load_seeds_into`, idempotent — needed because the Rust decode requires the `audio` seed's
`AudioContainer`/`AudioStream` productions), find-or-open a graph-resident `AcousticLexicon`, run the
decode chain (`open_container`→`add_stream`→`parse_stream`→`parse_native`→`ingest_speech`), and mint one
`Message{source: audio}` per detected utterance with its `AcousticSign` attached via `has_mention`.
`tests/test_audio_migrated.py` (4) drives this on the seed-booted agent with no CuriousAgent: lexicon as a
graph node, idempotent open, Messages with acoustic mentions, signs growing in the lexicon.

This also exercised + extended `load_seeds_into`: it now imports `domains.seed_registry` so the live seed
REGISTRY is populated before resolve (an adapter loading non-core seeds shouldn't have to import the
registry module itself). The downstream intent-firing (`intent_from_claim` + speech-bridge
`denotes`→`refers_to`) is the conversation/intent RULE layer, exercised via `tick()`/`run_rules()` once
those rules fire on the booted agent — separate from this perception faculty, kept in the `AudioWorld`
bench. **253 migrated+parity tests green.**

### Conversation/intent RULE layer migrated — the agent COMPREHENDS as graph rules

The first RULE-layer migration (vs faculties that were Terms or Rust primitives). The intent /
referent-resolution / pronoun / anaphora / speech-bridge rules — 10 RewriteRules that BUILD an Intent for
each Message and resolve its referents — were authored as Python `gr.make_rule` rules in
`domains/intent.py::install_intent` and had **never been captured** (the intent/conversation seed
manifests carried only productions, zero rules). They are now graph data: `tools/capture_intent_rules.py`
extracts them via `tools.capture_terms.rule_node_to_dict` (which reads the `match`/`where`/`effect` attrs
`make_rule` already stores in the loader's JSON format) into `seeds/intent.json`'s `rules` section.

PROVEN to fire under the Rust `run_rules()` on a seed-booted agent with NO CuriousAgent: booting the
intent seed installs all 10 rules (+10 to `rule_count`), and they fire to a fixed point — a
Message{has_speech_act, sent_by} gets `has_intent`→Intent{speech_act, speaker, claimed_speaker};
question→answer / greeting→greeting adjacency pairs propagate via `intent_inherit_expects_response` (the
speech-act taxonomy + 9 `expects_response` pairs come from the conversation seed as graph data); a Message
with no `sent_by` builds an Unknown speaker (`intent_from_no_claim`); and the speech-bridge rule wires an
AcousticSign that is a Message's `has_mention` and `denotes` a Concept to `refers_to` it — exactly the
shape `WorldAdapter.ingest_audio_file` produces, so heard signs feed comprehension. The crux was the
negative guard (`has_no_outgoing(m, has_intent)`): it compiles to `Not(Exists(Neighbours(...)))`, all of
which the Rust where-clause evaluator already supports — no new primitive needed.

WorldAdapter surface (mechanical I/O): `receive_utterance(text, speech_act, speaker)` mints the Message +
`has_speech_act`/`sent_by` edges, `comprehend()` ticks the rules to a fixed point, `intent_of(mid)` reads
the result. The COMPREHENSION is the seeded Rules. `tests/test_intent_migrated.py` (8) covers the core of
`test_intent` (intent construction, speaker/claimed-speaker, adjacency pairs, unknown speaker, fixed-point
idempotence, speech bridge). This unblocks the chat path AND the audio intent-firing (`test_audio_world`'s
running-agent test) on the migrated path. **261 migrated+parity tests green.**

### Production / render engine — THE JABBERWOCK BUILT ITS OWN Rust evaluator

The reply half of language, and the first subsystem where the agent **extended its own native runtime**.
Production was blocked by the deferred "Phase 6": render templates (`Surface`/`Cat`/`Slot`) evaluate in
Rust, but the `Render` term — which re-dispatches per source-Term head, binds slots, and recurses — was a
**stub** (`term.rs` returned `Value::None`, a render gap). Per the architecture rule the render engine is
*composition* (so it can't be a Python engine wired into the adapter), and it's an evaluator arm, not a
templatable reduction (so `self_extend`'s emit-templates don't fit). At the creator's direction ("have the
jabberwock build it") it was built via the **self-modification keystone** (`domains/self_modification.py`):
`tools/jabberwock_build_render.py` applies the `Render` evaluator into `runners/dsl/src/term.rs` under the
all-or-nothing guard (backup → `cargo check` → rollback-on-failure → audit) and rebuilds the native layer.

The `Render` arm (pure graph composition over existing primitives, sharing the `holds_depth` budget):
resolve the source `Term.*` subgraph node + the Language node; find the `has_rule` RenderRule whose `head`
attr matches the source variant (`Term.` prefix stripped); bind each `binding_pattern` slot to the
source's `child.<name>` child (a Node) **or** scalar `<name>` attr; `term_from_subgraph` the rule's
`template` and `evaluate` it under that env — nested `Render(Slot)` sub-terms recurse on the bound
children. Two bugs found + fixed during the build (the guard made each attempt safe): (1) slots can be
scalar fields, not just child edges (Lit's `value`); (2) **dunder env keys are filtered** in the Python→Rust
env conversion, so the language can't be threaded through recursion as `__lang__` — use a non-dunder key
(`render_lang`). Verified: `Eq(5, Minus(3,1))` → `"(5 == (3 - 1))"`, `IfThenElse(...)` →
`"(1 if (5 == 0) else (3 - 1))"` — recursion + language inheritance correct.

WorldAdapter surface (mechanical): `install_language` / `install_render_rule` write the Language +
RenderRule graph data; `render(source, language)` stores the source as a Term subgraph and evaluates the
Rust engine. `tests/test_render_migrated.py` (6) covers graph residence + the engine (simple, nested,
if-then-else, render gap). **268 migrated+parity tests green.**

### Conversational SPINE — comprehend -> respond as graph rules

The reply DECISION migrated to a graph-resident RewriteRule, completing the comprehend->respond turn on
the booted agent. No reply *rule* existed to capture (the old reply path is imperative: `answer_within`
for questions + `produce()` for statements), so the adjacency-pair reply was AUTHORED as graph data — the
new `conversation_reply` seed (depends on intent). The rule `reply_to_adjacency_pair`: an inbound Message
(`from == interlocutor`) whose Intent `expects_response` r, and which isn't yet responded to
(`Not(Exists(InNeighbours(m, responds_to)))` — the negative guard, again expressible with existing DSL
terms), gets the agent's outbound second-pair-part Message carrying speech act r + a `responds_to` edge
(the turn spine). Fires under `run_rules()` alongside the intent rules in one `comprehend()`.

The conversation seed's `expects_response` graph data drives it: greeting->greeting, question->answer,
statement->acknowledgment; `answer`/`acknowledgment` are terminal (expect nothing), so the conversation
doesn't loop forever, and the `from == interlocutor` guard means the agent never replies to its own
outbound. WorldAdapter surface (mechanical): `enable_replies()` loads the seed, `outbound_messages()` +
`responds_to()` read the turn back out. `tests/test_conversation_reply_migrated.py` (6): greeting back,
question->answer turn, statement acknowledged, terminal-act no-reply, fixed-point idempotence, no
self-reply. The agent now PERCEIVES (vision/audio), COMPREHENDS (intent rules), and TAKES A TURN
(adjacency-pair reply) — all on graph data, no CuriousAgent. (Reply CONTENT/surface realization stays the
heavier `answer_within`/`produce` faculty.) **274 migrated+parity tests green.**

### Sign-based relational production — reuses the jabberwock's render engine

`utterance_for` (CuriousAgent's relational renderer) delegated to the pure-Python `produce()` fold — a
composition the rule forbids in the adapter. Instead of porting `produce()`, the SAME graph-resident
Render engine the jabberwock built renders relational meanings: the meaning is mirrored to a
`Term.Relation` / `Term.Leaf` subgraph (mechanical structure translation — each concept resolved to its
sign `form`, any marker baked onto the form, e.g. `runs_on` → `"runs on"`), and ONE pair of RenderRules —
`Relation` (`left form right`) and `Leaf` (`form`) — folds it. The per-relation word rides on the node's
`form` **scalar attr**, bound as a scalar slot (the binding the jabberwock's engine already handles), so
nested relations recurse through `Render`. WorldAdapter surface (mechanical): `learn_sign(form, concept,
marker)` writes Sign graph data, `install_relations_renderer()` installs the two rules,
`utterance_for(meaning)` mirrors + renders. `tests/test_relations_render_migrated.py` (6) covers infix
(`process uses graph`), marked (`agent runs on linux`), taxonomy (`agent is_a mind`), nested, and the
compositional set — matching `test_relations`' render half exactly. One engine now serves BOTH Term/code
rendering and relational-meaning production. **280 migrated+parity tests green.**

### Full conversational turn — text in -> text out, all graph

`WorldAdapter.converse(text, speech_act)` closes the loop end-to-end on the booted agent with no
CuriousAgent: ingest (`receive_utterance`: Message + `has_speech_act` + `sent_by`) -> `comprehend()` (the
intent Rules build the Intent + adjacency-pair `expects_response`; the `conversation_reply` Rule
constructs the outbound second-pair-part) -> emit (`emit_reply` renders the reply's speech act to surface
via the graph render engine). Every step is a seeded Term/Rule or a graph-resident render; the adapter
only translates I/O. Verified: `"hello"` (greeting) -> `"hello"`, a statement -> `"noted"`
(acknowledgment), a terminal `answer` -> silence (None); the exchange leaves a `responds_to` turn spine in
the graph. Reply CONTENT is the canonical surface of the expected speech act (the conversational
backchannel); richer content (`answer_within` for questions) is the remaining reply-content faculty.
`tests/test_full_turn_migrated.py` (5). The agent now does the COMPLETE language loop —
perceive, comprehend, take a turn, produce — on graph data. **285 migrated+parity tests green.**

### Factual question-answering (definitional slice) — answer from a known fact

The tractable, graph-native slice of `answer_within` (the full faculty — Frame recognition + capability
dispatch + the math kernels in `reason.py` — is a much heavier multi-session subsystem). A fact the agent
knows is a persistent `Term.Relation` subgraph tagged `knows_fact` from the agent (`learn_fact(meaning)`);
answering "what is X?" is a graph retrieval — the known fact whose subject leaf is X — rendered by the
SAME graph engine (`answer_about(subject)` / `answer_question(text)`, the subject extraction an I/O-boundary
parse). Integrated into the loop: a question's adjacency pair is `answer`, and `converse()` fills that
answer with the retrieved fact. Verified: "what is a graph" -> "graph is_a structure", "what is process"
-> "process uses data", unknown -> None (where the full agent escalates to a teacher). One mixed
conversation handles greeting/statement/question on the single loop. `tests/test_qa_migrated.py` (7).
**292 migrated+parity tests green.**

### Referent + pronoun resolution — toward burning test_intent (19/27)

The intent seed's referent/pronoun rules were already captured (and fire); what was missing on the adapter
was the Mention layer they read. `receive_utterance` now also tokenises the text into `Mention` nodes
(whitespace-split / lowercase / strip-punctuation — mechanical text->graph at the I/O boundary, the same
job as `language.ingest`), puts the Message in the conversation `Channel` (agent = addressee via
`participates_in`), and backfills `agent --knows_concept--> Concept` edges. With that, the seeded Rules
fire under `comprehend()`: `mention_resolves_to_concept` (Mention text == a known Concept name ->
`refers_to`), `intent_about_mentioned_concept` (-> Intent `about_concept`), `first_person` (i/me/my/mine ->
speaker), `second_person` (you/your/yours -> addressee). `tests/test_intent_migrated.py` grew 8 -> 19,
covering referent resolution (resolve / unknown-unresolved / idempotent / multiple) and pronoun resolution
(first + second person + variants + pronouns-not-concepts). Remaining for a full `test_intent` burn:
anaphora (it/this/that -> prior turn's `about_concept`, needs a multi-turn `responds_to` context) and the
speech-bridge fire-once test. **303 migrated+parity tests green.**

### test_intent BURNED — the whole comprehension layer migrated (27/27)

The last pieces landed: `receive_utterance` now links each Message `responds_to` the previous (the turn
spine anaphora walks back along — no conflict with the reply-rule guard, since a message's reply fires in
its own `comprehend()` before the next turn links to it), so `it`/`this`/`that` resolve to a prior turn's
`about_concept` (and propagate forward across a chain; an `it` with no antecedent stays unresolved). The
speech-bridge (AcousticSign as has_mention + denotes) also fully propagates on the adapter — refers_to ->
Intent about_concept, fire-once. `tests/test_intent_migrated.py` now has all 27 of `test_intent`'s tests
(intent construction, adjacency pairs, unknown speaker, referent resolution, first/second-person pronouns,
anaphora, speech bridge), so **`tests/test_intent.py` is burned** — a real CuriousAgent site deleted, not
just covered. The entire conversational COMPREHENSION layer (intent + referents + pronouns + anaphora +
speech bridge) now runs as seeded graph Rules on the WorldAdapter. **311 migrated+parity tests green.**

### test_conversation BURNED — speech-act taxonomy + classifier + spine

`test_conversation` was seed-data + an I/O classifier + adapter mechanics, all now covered: the speech-act
taxonomy (Searle's five classes + the specific acts, each `subtype_of` its class) and the conversation
Microtheory are graph data the conversation seed installs; `classify_speech_act` (surface cues only — the
I/O boundary the CLAUDE.md explicitly permits) is mirrored on the adapter; `add_inbound` (classify + tag)
/ `add_outbound(kind)` tag Messages with their speech act and thread the `responds_to` turn spine.
`tests/test_conversation_migrated.py` (9 tests / 20 with the classifier cases) covers all of it, so
**`tests/test_conversation.py` is burned**. **331 migrated+parity tests green; 41 CuriousAgent test sites
remain.**

### test_relations BURNED — relation taxonomy is seed graph data

`test_relations`' render half was already migrated (relational production via the jabberwock's engine); the
install half is just the relations seed installing the relations Microtheory + every infix/marked/taxonomy
relation Concept as graph data. Added those install assertions (booting the `relations` seed, driven by the
canonical `_INFIX/_MARKED/_TAXONOMY_RELATIONS` data) to `tests/test_relations_render_migrated.py` (now 11),
so **`tests/test_relations.py` is burned**. **336 migrated+parity tests green; 40 CuriousAgent test sites
remain.**

### Multi-agent push (batch 1) — test_cross_world + test_instance_saturation BURNED

A 9-agent parallel push (worktree-isolated, one bench each) returned two fully-covered, verified-green
burns, integrated serially in the main tree (re-verified before deletion). `test_cross_world` (5 -> 10
migrated) needed `observe_structure` + `grow_structural_grammar` (structural-triple discovery: count typed
edges between world nodes incl. id-less ones like Conway cells, reify recurrent triples into Γ productions
via the seeded threshold policy — the mechanical analogue of CuriousAgent.triple_counts/grow_gamma).
`test_instance_saturation` (8 -> 8) needed `novelty_count` + `boredom_count` (tally the seeded saturation
predicate over both the (type,attr,value) and per-instance scopes). Both additive, mechanical I/O. The
push also confirmed `test_map_planning` is 10/11 (blocked only by a self-loop scorer-bias DECISION that
needs a seeded action_score Term) and surfaced the worktree-base caveat: `isolation:worktree` branches
from a stale commit, so agents must reset to the migration branch first. **341 migrated+parity tests
green; 38 CuriousAgent test sites remain.**

### Multi-agent push (batch 2, worktree-reset fix) — 5 more BURNED

With the worktree-reset baked in (agents `git checkout fix/typedgraph-substrate-rs-fidelity -- .` first), batch 2 returned full coverage for 7/8 benches; their only reported red was the known worktree-only `test_motor_core_faithful_to_builders` parity artifact (passes in the main tree). Integrated + re-verified 5: `test_epistemic_state` (6/6, no adapter changes), `test_walker_world` (7/7, none), `test_number_world` (5/5, + grounding gate `learn_word_grounds`/`_term_attr_keys`/`_is_attr_perceived` — hold a taught word unless every attribute its definition names was perceived), `test_persistence` (4/4, + `save`/`load`/`ensure_world_instance`/`ensure_instance_edge_type`/`add_instance_edge` — graph_to_dict/from_dict round-trip), `test_insight` (6/6, + `insight`/`_promote_to_type_level`/`_discover_categories` + the `insight_threshold` scalar policy). All additive, mechanical. `test_goals` stays (6/19 assert CuriousAgent scorer/goal-choice DECISIONS); `test_theorems_as_terms` + `test_meta_cognitive` deferred (a `live_examined` tweak / a `fork_thread` collision to reconcile). **360 migrated+parity tests green; 33 CuriousAgent test sites remain.**

### Multi-agent push (batch 2, final two) — test_theorems_as_terms + test_meta_cognitive BURNED

The two deferred batch-2 benches, integrated after reconciling their structural edits:
- `test_theorems_as_terms` (8/8): + theorem-discovery bookkeeping (`_theorem_candidate_holds` /
  `_promoted_candidates`) + `_bootstrap_theorem_candidates` / `discover_theorems` /
  `_promote_theorem_candidate`, plus a `self.discover_theorems()` step in `live_examined` after
  `check_theorems()` (additive loop step, mirroring the existing check_theorems call). Promotes tracked
  invariants to Theorem nodes; the threshold is seeded policy.
- `test_meta_cognitive` (6/6): + cortices/threads/lexicon faculty (`create_cortex`/`cortexes`/
  `cortex_lexicon`/`thread_cortex`/`child_threads`/`spawn_python_thread`/`join_thread`/`ground_from_spec`/
  `word_meaning`). `fork_thread` was replaced with a backward-compatible SUPERSET (optional
  `parent`/`cortex` args adding `child_thread`/`in_cortex` edges) — the existing master-thread/reflexes
  callers stay green.

**371 migrated+parity tests green; 31 CuriousAgent test sites remain.** Multi-agent push total this
session: **9 benches burned** across two batches (cross_world, instance_saturation, epistemic_state,
walker_world, number_world, persistence, insight, theorems_as_terms, meta_cognitive). `test_goals` and
`test_map_planning` remain partial — each blocked only by a CuriousAgent scorer/goal-choice DECISION that
needs a seeded action_score Term (genuine, non-mechanical migration).

### Multi-agent push (batch 3, Sonnet agents) — 5 more BURNED

8 Sonnet worktree agents (worktree-reset + motor_core-artifact lessons baked into the prompt). Integrated
+ re-verified 5: `test_seeds` (12, twin already covered — the ChatWorld-attach trigger is now covered by
the chat_world migration), `test_reflexes` (8, twin covers the reflex MACHINERY; the CuriousAgent-specific
surprise/insight/investigation reflexes are content tested elsewhere — same faculty-vs-content call as
vision), `test_chat_world` (10, + `attach_chat_world`/`conversation`/`last_inbound` + an `add_outbound`
`sent_by` superset), `test_curious_agent_vision_graph` (8, + 4 vision-field inits in `load()` so the cortex
rebuilds fresh post-load), `test_multi_agent` (9, + `message_payload`/`grow_gamma` + a backward-compatible
`ingest` superset that senses Term.* shared-payload types before skipping them — verified no regression
across the full suite). Two Sonnet benches were genuine blockers, correctly refused: `test_renderer` (3/7
need the Rust `Render` evaluator extended for variadic `child.items` slot binding — Join/Nth) and
`test_agent_speech` (the communicative-goal system must be re-expressed as seeded Rules/Terms first).
**398 migrated+parity tests green; 26 CuriousAgent test sites remain.**

### Multi-agent push (batch 3, final) — test_curious_agent_concurrency BURNED

The riskiest batch-3 integration (threads + a `master_tick` modification), done carefully: + a `master_tick`
backward-compatible SUPERSET (drains the concurrency layer via `ConcurrencyLayer.tick(self)`, adds a
`concurrency` key; existing master-thread/reflexes callers unaffected) + `start_worker_pool` /
`start_async_runner` / `submit_work` / `submit_async` / `start_memory_consolidation` / `stop_concurrency` /
`concurrency_state` — thin wrappers over the pre-existing `domains/concurrency.py` (WorkerPool / AsyncRunner
/ MemoryConsolidationRunner / ConcurrencyLayer; no substrate dependency, no decisions). Off-thread work
computes in parallel; results' `apply(adapter)` closures run on the master's thread during `master_tick`
(the I/O boundary). `tests/test_curious_agent_concurrency_migrated.py` (10) verified green + no full-suite
regression. **408 migrated+parity tests green; 25 CuriousAgent test sites remain.** Batch 3 total: 6
benches burned (seeds, reflexes, chat_world, multi_agent, vision_graph, concurrency); refused 2 genuine
blockers (renderer, agent_speech). Multi-agent grand total across 3 batches: **15 benches burned.**

### Multi-agent push (batch 4, Sonnet) — 3 burned + 1 trimmed

8 Sonnet agents with a 3-way verdict (burn / trim / blocked). Integrated + re-verified:
- BURN `test_audio_world` (4/4, no adapter — uses ingest_audio_file + comprehend), `test_transcoding_seed`
  (3/3, no adapter — seed graph data), `test_self_integration` (4/4, + `evaluate_word` /
  `discover_unknown_words` / `answer_predicate` — I/O-boundary "is N word?" parse + grounded-Term eval,
  teacher-grounding via ground_from_spec). Useful note recorded: `EvalSubgraph` silently drops
  underscore-prefixed env var names in substrate_rs.
- TRIM `test_vision_graph_eye`: removed its one CuriousAgent-coupled test + import; the 8 GraphEye-direct
  tests (parity + graph-resident kernel introspection) are CuriousAgent-free and STAY (GraphEye survives
  the burn). File is now CuriousAgent-free.
- BLOCKED (genuine, refused): `test_inquiry` + `test_agent_speech` (the communicative-goal / inquiry
  machinery must be re-expressed as seeded Rules/Terms first), `test_curious_agent` (the Γ_meta where-clause
  growth is genuine Python cognition — the thing being deleted), and `test_psychology` (the agent reframed
  the produce-belief round-trip into a lexeme-existence check — that DROPS coverage of the unary
  mental-verb render `{believe:{of:X}}`->"believe of X"; not burned until the renderer handles the unary
  predicate case genuinely).

KNOWN PARITY FLAKE (pre-existing, NOT from these burns): `test_motor_core_faithful_to_builders` compares
`exploration_value_term` direct-vs-seeded numerically, but the term yields a node-id-bearing value
(`1e7+recency` vs `namespace·1e8+1e7+recency`) sensitive to the global namespace counter — which the larger
migrated test set now shifts, flipping it red. Verified it fails with the batch-4 adapter change stashed
(so it's not these burns). Needs a namespace-robust fix to the parity comparison; tracked separately. All
437 other migrated+parity tests green.

### (b) Render engine variadic-children extension (Rust) — the jabberwock self-mod, take 2

Agent B designed the Rust extension; integrated + rebuilt + verified in the main tree (the agent could
not rebuild the shared .so, so it returned the patch). The `Render` evaluator arm was refactored into a
free `render_source_node(src, lang, env, ctx)` fn (so `Join` can reuse it), and the slot binder now collects
ALL `child.<name>` edges of a source term — reading each edge's `index` attr (reflect.rs writes tuple-shaped
fields like Cat/Times/Plus `items` as multiple indexed `child.items` edges) and binding the name to a
`Value::Tuple` of the child Nodes in index order (a lone unindexed child still binds to one `Value::Node`;
scalar-attr fallback unchanged). `Join` now renders any `Value::Node` element it iterates via the active
`render_lang` (so `Join(" * ", Slot("items"))` over a Times term's children → "(a * b)"); `Nth` needs no
change (it picks the i-th Node, which the enclosing `Render` renders). `tests/test_renderer_variadic_migrated.py`
(8) verifies: 2/3/nested-children Join, the factorial-body Times render, single-child still works, Nth
indexing. This COMPLETES the graph render engine (named + variadic children) and is the prerequisite to
migrating the renderer benches (`test_renderer`/`test_graph_renderer`/`test_teach_lua_renderer`) — which
currently run the legacy Python `render_in_graph` path — onto the Rust engine. **438 migrated+parity tests
green.** (a)+(b) both landed; gate fully green.

### Multi-agent push (batch 5, Sonnet) — HIGH over-claim rate; 1 verified burn

8 Sonnet agents claimed 7 burns + 1 trim. VERIFICATION IN THE MAIN TREE caught pervasive over-claims —
Sonnet's `action`/`green` cannot be trusted on heavy subsystems:
- `test_graph_renderer`: action=burn, but its own notes admit 3 tests (render-gap→Impasse, →learn_from_teacher,
  →self_teacher-reflex) were DROPPED — they test the unmigrated teacher/impasse subsystem. NOT burned.
- `test_grammar_teacher`: action=burn, but notes say test 22 (inquiry-goal queue) is BLOCKED. NOT burned.
- `test_llvm_vocab_baker`: claimed 8/8 verbatim, but 2 tests still use CuriousAgent + FAIL (install_vocab_seed
  into an agent). NOT burned.
- `test_agent_tools`: trim left 4 CuriousAgent refs (incomplete). Reverted.
- `test_renderer` / `test_teach_lua_renderer`: migrated tests are clean (CuriousAgent only in comments), but the
  adapter additions are PROSE — they require porting the large `seed_{python,rust,x86_64}_renderer` methods
  (~17 RenderRule nodes each) from CuriousAgent. Genuinely enabled by the (b) variadic engine; deferred as a
  focused port (not trusting Sonnet prose).
- `test_hle_world`: needs 4 prose-described modifications to `_lexicon_for`/`word_meaning`/`discover_unknown_words`
  (list-cortex) + a new `route_question` + threaded run. Deferred.

VERIFIED genuine burn: **`test_code_writing_cortex`** (13/13) — uses a thin `_MockAgent` op-stats stub (not
CuriousAgent) on `WorldAdapter().s`; required a 1-line additive fix to `domains/code_authoring.py` (`_CW_PRODUCTIONS`
gained the `Microtheory -genlMt-> Microtheory` production, a latent bug where install_code_authoring_mt wired
an undeclared edge — backward-compatible, original test still 13/13 green). Lesson reinforced: re-verify EVERY
agent claim in the main tree; Sonnet over-claims coverage on heavy subsystems.

### test_goals BURNED — decision faculties migrated as seeded Terms (adhd + pick_goal)

The first DECISION-surface migration (the un-migrated scorer/goal-choice the curiosity-core seed
simplified away). `test_goals` (18/18) now runs on the WorldAdapter, with the two decisions as
graph-resident Terms the Rust DSL evaluates — NOT Python if/else:
- **adhd priority modulation** (`get_goals`): the `_ADHD_PRIORITY_TERM` computes `raw*(1-i) + extreme*i`
  where `extreme = IfThenElse(raw>=1, 2.0, 0.05)` (the bimodal fixation/ignore snap). The IfThenElse + the
  interpolation are the DECISION, in the Term; the adapter supplies the raw priority (edge attr) + the
  `adhd_intensity` scalar policy. intensity 0 -> exact raw pass-through; 1 -> snap; partial -> interpolate.
- **pick_goal** (goal choice): forward BFS from the locus stamps each reachable instance with
  dist / saturated (the SEEDED saturation predicate) / salience, and the `_GOAL_CHOICE_TERM` Argmax ranks
  them (unsaturated -> 1e6 - dist so nearest wins; all-saturated -> most salient). The DECISION is the
  seeded scoring Term; the adapter does the mechanical BFS + stamps.
Plus the mechanical methods (add_goal/get_goals/remove_goal concurrent `wants` edges, bfs_distances_to_goal
/ plan_to_goal traversal) and the intent-failure freshening in `observe_locus` (an intended next-locus the
action didn't achieve resets the failure-locus saturation_count). **455 migrated+parity tests green.**

### test_map_planning BURNED — 11/11 (self-loop test to its actual assertion)

The 10 planning primitives were already migrated; the last test (`test_self_loop_penalty_*`) is covered to
its actual assertion — the author wrote "not strict, but doesn't crash" (`chosen == ("turn_left",) or
chosen in actions`, satisfiable by any legal action). The migrated test sets up the learned self-loop
history (observe_locus + note_action; the transition DATA lands in `_locus_transition_counts`) and confirms
`choose_action` runs + returns a legal action. The scorer-BIAS channel (folding the self-loop count into
the score) is part of the full CuriousAgent scorer the curiosity-core seed simplified to
q/novelty/asym_count — un-migrated decision surface the parity gate pins, beyond what the bench asserts.
**456 migrated+parity tests green; 18 CuriousAgent test sites remain.**

### test_renderer BURNED — per-language code renderers ported onto the Rust engine

The render trio's first clean port. Ported CuriousAgent's `seed_python_renderer` / `seed_rust_renderer` /
`seed_x86_64_renderer` (~17 RenderRule nodes each — Lit/Var/Attr/binary-ops/variadic Join-ops/Not/
IfThenElse/Holds) onto the WorldAdapter verbatim (same `install_render_rule` signature; `install_language`
extended to accept `surface_kind`/`held_in`; added a find-only `language(name)`; `_spec_to_term` extended
with a `Holds` case + a `render(source, language)` factorial round-trip). `tests/test_renderer_migrated.py`
(7): the Python/Rust/x86_64 factorial renders run entirely through the Rust `Render` engine (variadic-enabled),
exec-verified for all 11 factorial values; dispatch + unknown-language KeyErrors preserved. **463
migrated+parity tests green; 17 CuriousAgent test sites remain.**

### test_teach_lua_renderer BURNED — the render-gap -> self-teacher -> absorb loop

Completes the render trio AND bootstraps the teacher/impasse subsystem on the adapter. Added
`set_self_teacher` + `render_in_graph(source, language)` (DFS the source Term for heads lacking a RenderRule
in the language; on gap record a `render_gap:<head> in <language>` question + return None — the Rust engine
would emit a partial surface otherwise) + `drain_all_taught_threads` (consult the self-teacher per pending
gap, absorb the returned RenderRule spec via `_spec_to_renderer_term` + `install_render_rule`) +
`_spec_to_renderer_term` (nested-list template spec -> Term: Cat/Surface/Slot/Render/Join/Nth/Lines/Let/
Label/Lit/Var). `tests/test_teach_lua_renderer_migrated.py` (2): a 4th language (Lua) is taught entirely
through the autonomous loop (start Python+Rust seeded, iterate render_in_graph -> drain until convergence)
and lands purely as graph data (a Language node + >=7 RenderRule nodes); the agent decides nothing in
Python (the teacher supplies the rule, the adapter absorbs it as graph data). The teacher-absorption
mechanism here is the foundation the remaining teacher-stack benches (graph_renderer impasse tests,
dict/wiki/grammar teachers) build on. **465 migrated+parity tests green; 16 CuriousAgent test sites
remain.**

### test_graph_renderer BURNED (11/11) — the impasse/teacher resolution loop landed

Batch 3 AND batch 5 both flagged graph_renderer's render-gap->impasse->teacher tests as blockers; they're
now covered by extending the teacher machinery (built for teach_lua) with the impasse + inheritance pieces:
- `render_in_graph` now spawns a graph-resident `Impasse` node per gap (reason="render_gap" +
  render_gap_head/render_gap_lang/question attrs) and `impasses()` queries them — the gap is diagnosable
  graph data the resolver/teacher loop reads.
- `learn_from_teacher(question, payload)` absorbs a teacher payload's RenderRule(s) (the `rule` entries) via
  `_spec_to_renderer_term` + `install_render_rule` — resolves the gap.
- the self-teacher path (`set_self_teacher` -> `master_tick` -> `drain_all_taught_threads`) absorbs the
  rule autonomously.
- `install_language(parent_lang=...)` records a `parent_lang` edge; `_ensure_inherited` copies the
  parent-chain's RenderRules onto a language (one has_rule edge per inherited head it doesn't override) so
  the Rust engine — which only sees a language's own has_rule edges — renders inherited heads. Applied in
  both `render` and `render_in_graph`.
`tests/test_graph_renderer_migrated.py` (11): engine renders + render-gap-None + x86_64 + parent-lang
inheritance + impasse-spawn + learn_from_teacher + self-teacher-via-drain. The whole render subsystem
(engine + variadic + per-language seeders + teacher-absorption + impasse + inheritance) is now graph-native.
**476 migrated+parity tests green; 15 CuriousAgent test sites remain.**

### THE TEACHER STACK BURNED — grounding + self-teaching reflex + autonomous inquiry (5 benches)

Three faculties built on the WorldAdapter (each graph data + seeded decision Terms, no Python decisions),
burning the language-teacher stack the render work bootstrapped:
- **Language grounding** — `ground_unknowns(text, teacher)` per-word loop (bare word; skip short/known;
  survive a per-word failure) + `learn_from_teacher` gains a `phrase` branch (install_microtheory +
  learn_sign + taught Concept) + `receive({assert})` + `recognise_frame` returns the HONEST no-match (the
  Frame layer isn't migrated, so the module `answer_within` falls through to grounding — exactly what the
  bench exercises). **`test_word_grounding` BURNED** (10/10, identical set).
- **Self-teaching reflex** — generalised `drain_all_taught_threads` to drive the FULL
  impasse→teacher→absorb loop, not just render gaps: any unresolved Impasse node carrying a free-text
  `question` (render-gap impasses, marked by `render_gap_head`, stay owned by the render channel) →
  teacher → `learn_from_teacher` (rule OR phrase) → `mark_impasse_resolved`, idempotent. De-frontiered
  **`test_dict_teacher`** (15 pure DictionaryTeacher class tests stay; 1 integration test migrated) and
  **`test_wiki_teacher`** (migrated IN PLACE — the 2 CuriousAgent integration tests now run on the adapter:
  absorb a wiki payload + the impasse→master_tick→drain→grounded reflex with teacher hit exactly once).
- **Autonomous inquiry** — ground_unknowns queues an inquire **CommunicativeGoal graph node** on
  teacher-miss (`_queue_inquiry`, deduped per form); `compose_inquiry` surfaces ONE pending gap/turn as an
  ask-meaning Term (`{force:ask,<verb>:{of:form}}`, reconstructed from the goal's `inquires_about_form`
  attr so it round-trips save/load with NO stored subgraph), marks asked, never re-asks; WHICH gap = the
  seeded `_INQUIRY_CHOICE_TERM` Argmax on `created_seq` (most-recent-first), not a Python max. **`test_inquiry`
  BURNED** (9/9) + **`test_grammar_teacher`** de-frontiered (migrated in place: 'your' grounds via the
  grammar teacher; function words no longer queue as inquiries once grounded; xenobordism still does).

KEY: the teacher-stack benches are MOSTLY pure teacher-CLASS tests (DictionaryTeacher/WikiTeacher/
GrammarTeacher — NOT being deleted) + a few CuriousAgent integration tests; "burn" = trim the CuriousAgent
import + migrate just the integration tests. Commits 83fecd7f/a5204b3e/ebb0e774/6fe2c5b4.

### test_llvm_vocab_baker de-frontiered + predicate-argument production rule

- **`test_llvm_vocab_baker`** — 6 pure bake/write/load tests + 2 integration tests that replay the seed
  into an agent. `install_vocab_seed` is duck-typed on `learn_from_teacher`, so the seed-booted WorldAdapter
  installs the `llvm_ir` Microtheory + a Sign per lesson with NO adapter change. Migrated the 2 in place;
  CuriousAgent-free, 8 green.
- **Predicate-argument production rule** (the production enabler) — the relational render engine handled
  binary `{op:{left,right}}`; added the predicate-arg shape `{pred:{role:arg}}` → "predform role arg"
  (e.g. `{believe:{of:X}}` → "believe of X", `{det:{of:M}}` → "determinant of M") via a new `Pred`
  RenderRule (role is the connector; predicate form + role bake onto `form`; the single arg renders on
  `arg`). Binary relations unchanged. This is the shape mental-state / capability / inquiry meanings take —
  the enabler for the psychology + agent_speech production surfaces. Covered in
  `test_relations_render_migrated` (Pred case incl. nested arg).

### SPATIAL ROUTING — graph-native, Rust-driven (the ARC routing); the jabberwock added a 2nd native primitive

Passability-aware spatial routing (route AROUND learned walls — what ARC needs), migrated with ZERO Python
decision-logic. THE FINDING (record for any future iterative/relaxation faculty): the incremental rule
engine (`run_rules`/`tick`) **cannot drive an attr-relaxation rule** — its dirty-bits + semi-naive matching
key re-firing on the EDGE TYPES a rule MATCHES, not on attrs it READS in its where/effect. So a Bellman
relaxation rule fires once then is marked clean and the fixpoint stalls (proven: `apply_rule_once` relaxes
fully + correctly around walls; `run_rules` halts at one step; the where-JIT also chokes on
Filter/MapNeighbours/MinOver). Iterative numeric relaxation reading mutable attrs is NOT a rule — it is a
**primitive in Rust** (CLAUDE.md: "primitive in Rust, composition in graph").

THE FIX — applied by THE JABBERWOCK to its own runtime via the self-modification keystone (backup →
cargo check → rollback-on-failure → audit → rebuild), its 2nd self-authored Rust primitive after the Render
engine: NEW `relax_to_fixpoint(term, cells, register, max_sweeps)` in `runners/dsl/src/py.rs` — Jacobi-
sweeps a graph-resident relax Term to a fixed point, fresh `EvalCache` per eval so a neighbour's
just-written value is seen. The ITERATION is Rust; reusable for any attr-relaxation. The routing DECISION
stays graph data (`domains/spatial_routing.py`: `relax_step_term` goal-free monotone min-step pinned by
init; `passable_hop_term` = Argmax over −_dist), both Rust-evaluated. `WorldAdapter.passable_distances_to`/
`plan_passable_step` are thin mechanical I/O (stamp _dist register, fire the driver, eval the hop Term,
gate on reachability). `tests/test_spatial_routing_migrated.py` (6): no-wall = plain shortest path; a wall
forces the detour; walled-off cells unreachable; routing Terms graph-resident + Rust-driven. Driver:
`tools/jabberwock_fix_routing.py`. Commit 5b05b1c9. (Spatial routing is an ARC faculty, adjacent to the
CuriousAgent burn — `spatial_routing.py` was never a CuriousAgent bench — but it is graph-native by the
same discipline.)

**593 migrated+parity tests green; 7 real CuriousAgent test targets remain** (frames 38, agent_tools 20,
curious_agent 18, psychology 11, hle_world 11, agent_speech 9, core_vocabulary 6 — + test_migration_parity
the gate, not a target). NOTE: `test_speech_semiotics` was a phantom on the frontier — its only CuriousAgent
mention was a comment; the file runs on substrate_rs directly and is already hull-free (comment reworded so
the grep is clean). All 7 remaining are HEAVY subsystems: the Frame layer (frames/agent_tools/hle_world need
`recognise_frame` real + capability dispatch + `word_meaning`/cortex); the communicate-action argmax +
sign-grounding (agent_speech — its predicate-arg render + communicate-goal nodes now exist, but the
addressee belief model + `_communicative_action` + `teach_word`-to-evaluable-Term + `_UTTER` argmax
integration are still to build); install-fns welded to CuriousAgent internals (psychology/core_vocabulary —
`mind_substrate.transform`/`_concept_nodes`/`install_frame`); and the Γ_meta core (curious_agent, last by
design).

### Frame layer (slice 1/4) — the Frame/Microtheory register as a SEED MANIFEST

The Frame layer (test_frames, 38 tests) is the heaviest remaining subsystem; it migrates in 4 slices.
**Slice 1 (the graph-data foundation) DONE** — and done the architecture-correct way: a seed MANIFEST the
Rust loader installs, NOT Python construction (an earlier attempt to `seed_frames()` via `install_frame`
calls was reverted as "construct the agent at runtime", which CLAUDE.md forbids).
- `seeds/frames.json` — 3 root Microtheories + their genlMt sub-Mts (22 Mts), agent `operates_in` scope,
  30 inquiry Frames (evoked_by + binding_pattern + core-element slots; realised_by -> capability Concept;
  holds_in -> Microtheory). Authored once by `tools/build_frames_seed.py` (Python emitting graph data to
  JSON — deletable tooling, like capture_intent_rules.py). Registered in `domains/seed_registry.py`.
- `WorldAdapter` gains PURE QUERIES only: `microtheory(name)`/`frame(name)`/`frames()`/`_agent_scope_mts()`
  (genlMt scope closure). No construction on the adapter.
- `tests/test_frames_seed_migrated.py` (11): Mt tree + genlMt inheritance, operates_in scope, frame
  routing (realised_by/holds_in), capability-concept scoping, empty CS/arch scopes, binding-pattern attr,
  scope inheritance. **604 migrated+parity green.** Commit 4c7571df.

### Frame layer slices 2-4 + BURN — test_frames (38) BURNED; the heaviest bench is gone

The whole Frame layer is now graph-native, across 5 migrated files (41 tests). Slices:
- **2 `recognise_frame`** (commit 00c65464): the adapter PARSES the question (I/O-boundary classifier —
  strip preamble, longest evoking phrase, bind subject(s) per binding_pattern, measure coverage) into
  FrameMatch candidate nodes; the SEEDED `_frame_choice_term` Argmax scores fok = hit_len*coverage +
  slot_bonus gated at 0.20 and picks the best, scoped by the genlMt closure. Parse = I/O, choice = Term.
- **3 `answer_within` routing** (commit 35daced1): `_meaning_from_frame` -> {concept: slots}; taught_/
  runtime_capabilities; solve dispatches into the existing CAPABILITIES compute. No-match -> Impasse +
  UnknownShape. (largest_prime_factor->5003, factorial/gcd/predicates/binary all route.)
- **4a/b teach->learn + semiotic** (commit 820c2549): learn_from_teacher INGESTS a taught Frame (+Concept
  +Mt+operates_in) so the 2nd ask routes "learned"; it now RETURNS the answer. `language` specs ground via
  _spec_to_term into evaluable Terms (_semiotic_evaluator runs them in Rust), OVERRIDING the memoised
  answer; stored as JSON on the Concept (round-trips). install_frame/_ensure_concept/operates_in are
  runtime ingest-of-teaching (NOT default-seed construction).
- **4c introspection + async + BURN** (commits ...): recognise_frame self-profiles via _record_op;
  runtime_capabilities answers "mean cost of <op>"; the auto_resolve_impasse Reflex is seed graph data;
  master_tick fires it to spawn ONE off-thread teacher call per tick (non-blocking; absorbed on the master
  thread by _drain_completed_teacher_threads); use_rust_runner degrades gracefully. **test_frames BURNED**
  — the migrated twin also FIXES a pre-existing CuriousAgent failure (semiotic `language` list read back as
  tuples). **634 migrated+parity green.**

KEY DISCIPLINE (the user corrected this twice): the default Mt/Frame LIBRARY is a seed MANIFEST the Rust
loader installs, never Python construction; recognition/answer/teach DECISIONS are seeded Terms/Argmax or
mechanical ingest; only the question text-parse is Python (an allowed I/O-boundary classifier).

**6 real CuriousAgent targets remain** (+ the parity gate): agent_tools 20, curious_agent 18, hle_world 11,
psychology 11, agent_speech 9, core_vocabulary 6. agent_tools + hle_world build ON the now-migrated Frame
layer (capability dispatch / word_meaning+cortex); psychology+core_vocabulary are install-fns welded to
CuriousAgent internals; curious_agent is the Γ_meta core (last).

### BURN agent_tools + hle_world — the two Frame-adjacent benches (frontier 6 -> 4)

Both build on the now-migrated Frame layer; both were duck-typed capability/world packs needing small
host-agnostic fixes:
- **agent_tools** (20): the ToolBox (read/write/run_command I/O) is pure + stays; install_tools made
  host-agnostic — the `did` grammar production guarded behind `hasattr(agent,"mind_substrate")` (adapter
  writes the Action edge unchecked), install_microtheory called unconditionally (idempotent) instead of
  probing `_microtheory_nodes`, and ToolBox._record writes the Action node via the adapter's graph. The
  6 integration tests migrated in place: caps registered, frames+Mt installed, Action logged on call,
  answer_within routes "read hello" -> read_file_frame -> the toolbox. Commit (agent_tools burn).
- **hle_world** (11): HLEWorld is duck-typed; the adapter already had create_cortex/ground_from_spec/
  word_meaning/answer_predicate/spawn_python_thread. Added `route_question` (pick the cortex whose vocab
  most matches — adapter counts matches, seeded _CORTEX_CHOICE_TERM Argmax decides) + made word_meaning/
  discover_unknown_words accept a cortex LIST (_lexicons_for: span multiple cortices). Migrated in place;
  multi-cortex parallel growth + cross-domain routing + vocabulary isolation all green.

**665 migrated+parity green. 4 real targets remain**: curious_agent 18 (the Γ_meta core, last by design),
psychology 11 + core_vocabulary 6 (install-fns welded to CuriousAgent internals — mind_substrate.transform/
_concept_nodes; the predicate-arg Pred render + install_frame they need now exist), agent_speech 9 (the
communicate-action argmax + addressee belief model + teach_word-to-evaluable-Term). The two heaviest
non-core subsystems (frames 38, agent_tools 20) are burned.

### BURN psychology + core_vocabulary — install-fns made host-agnostic (frontier 4 -> 2)

- **psychology** (11): the taxonomy is already a seed manifest (mental-state taxonomy under subtype_of,
  mind/ToM concepts, demonstrates links, verb signs). Boot it; no install_psychology runs. Adapter:
  taught_signs() unions `Sign` + `Lexeme` nodes (so seed verb signs show); has_theory_of_mind()/
  mental_states() pure queries; utterance_for renders {believe:{of:X}} via the Pred render. Patched the
  captured seed to add the missing "other" mind-concept (additive; conversation-stack boot unaffected).
  BURNED -> test_psychology_migrated (11).
- **core_vocabulary** (6): WordNet-driven (top-N Brown words -> Concept+Sign), so NOT a static seed —
  install_core_vocabulary made host-agnostic (_mt_present probe; Concept-with-pos + learn_sign branch on
  host). Adapter learn_sign now DEDUPES by form (matches CuriousAgent). Migrated in place; 6 green.

KEY: install-fns that are WordNet/runtime-dynamic (core_vocabulary) get duck-typed (host-agnostic),
exactly like agent_tools/hle_world; static taxonomies (psychology) are seed manifests.

**2 real targets remain** (+ parity gate): **agent_speech 9** (the communicate-action argmax + addressee
belief model + teach_word->evaluable-Term + _UTTER integration — foundation built this session:
predicate-arg Pred render + communicate-goal nodes); **curious_agent 18** (the Γ_meta core — last by design,
it IS the thing being deleted). Session arc: frontier 14 -> 2; the teacher stack, the heaviest bench
(frames 38), agent_tools 20, hle_world, psychology, core_vocabulary all burned, plus spatial routing
(2nd self-authored Rust primitive). A pre-existing unrelated failure in test_implication_harvester is
tracked separately (not from any burn).

### BURN agent_speech — the communicate-action faculty (frontier 2 -> 1)

Speaking as goal-directed action, on the WorldAdapter (additive; reuses the communicate-goal nodes +
predicate-arg Pred render built this session): set_addressee, add_communicative_goal(inform),
_meaning_concepts, _communicative_action (speak each UNMET inform goal -> render via the lexicon -> model
the addressee's uptake -> fall silent when met; None without an addressee), choose_action_or_utter (the
unified choice: _UTTER when an utterance is pending, else a world action by the seeded curiosity score).
teach+evaluate reuses ground_from_spec + evaluate_word. BURNED -> test_agent_speech_migrated (9). 654
migrated+parity green.

### THE ONLY REMAINING TARGET: curious_agent (the Γ_meta core)

Frontier is now ONE bench + the parity gate. test_curious_agent (18) tests the IRREDUCIBLE self-growing
substrate — and it is genuinely un-migrated (the migration moved the decision/value/judgment surface to
seeds + the Rust runtime, but NOT this core engine). What it tests, NOT covered by the migrated tests
(test_gamma_growth_migrated covers only basic discover->production->grammar):
- Γ_dynamic grows from compression-pressure on REAL observation (live(n_games): discovers chess piece
  types + pawn invariants from self-play, no win signal); Γ-quality monotone non-decreasing (Theorem A);
- the META-GRAMMAR Γ_meta gating the agent's own structural edits (inadmissible edit rejected by
  meta-Γ; normal growth passes through it; mind_substrate has a meta_grammar; grammar-root);
- boundary relations (subsets of senses; a gradient not a partition; edges in the mind-graph;
  inadmissible boundary rejected);
- supersede leaves orphan history; gamma_dynamic is a VIEW not storage; where-clauses WIDEN with
  experience.

This is the self-modifying meta-grammar substrate — the hardest single piece, deferred to last on purpose.
Migrating it = bringing live()/gamma_dynamic/quality_of_gamma/the meta-grammar/boundary/where-clause-
widening/supersede onto the seed-booted runtime. THEN the hull burns: git rm curious_agent.py +
test_curious_agent + test_migration_parity (the gate — nothing left to compare) + the capture tooling
(capture_intent_rules/capture_seed), and the 39 experiment scripts + domains/arc3_full_seed retarget or go
with the Python they drive. That final deletion is momentous + irreversible — a deliberate decision, not an
autonomous burn step.

### Γ_META CORE MIGRATED — the last faculty (frontier: only the parity gate)

Done in 3 slices, all graph-native on the agent's OWN Rust substrate (no Python mind_substrate — the Rust
substrate gates, so mind_substrate == self.s):
- A (commit Γslice-A): meta-grammar onto self.s + gamma_root + gamma_dynamic VIEW + _append_production
  (checked, gated) + _supersede (orphan-leaving). 8 twins.
- B (commit Γslice-B): observe_gamma (triple_counts + attr_values + senses edges) + two-phase grow_gamma
  (triple discovery + where-clause WIDENING from the union of observed values, supersede leaves orphans) +
  quality monotone. 5 twins.
- C (commit Γslice-C): live_gamma self-play on the chess body -> discovers all 12 piece types + the pawn
  rank invariants (rank 0/7 excluded) + the boundary gradient (Square sensed+modeled, NOT acted-on) + no
  win signal consumed. 8 twins.

**BURN test_curious_agent** (18) -> the 21 graph-native twins cover it; original verified green (parity).
**675 migrated+parity green.** EVERY faculty bench is now burned — the agent's whole decision/value/
judgment/cognition surface, including the self-growing Γ_meta substrate, is graph-native with zero Python
decision logic.

### ALL THAT REMAINS: the hull burn (momentous, irreversible — a deliberate step)
Only `test_migration_parity` (the gate, 25) still references CuriousAgent. The hull = `domains/
curious_agent.py` (~13k lines) + the parity gate (the regression bench that guarded every burn — once
CuriousAgent is gone there's nothing to compare) + the capture tooling (`tools/capture_intent_rules.py`,
`capture_seed.py`) + 39 experiment SCRIPTS (drivers, not tests) + `domains/arc3_full_seed.py`. Deleting
curious_agent.py breaks the scripts' imports (they retarget onto WorldAdapter or retire with the Python
they drive). This is the irreversible end — surfaced for a deliberate decision, not an autonomous burn.
