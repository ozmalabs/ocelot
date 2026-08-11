# `CuriousAgent` + worlds → cortex harness: teardown map

The last and largest piece of the Python-substrate migration (see
`SUBSTRATE_RS_MIGRATION.md`). It is NOT a delete — it is a **re-architecture
that is already partly underway**. CLAUDE.md states the end state: "The Python
`CuriousAgent` class and its 13K+ lines of construction / orchestration are
being deleted"; the replacement is the **cortex harness** (`CortexScheduler` +
cortices running on a `substrate_rs.Substrate`, as `scripts/develop.py` already
does for speech).

## Scope

- **`domains/curious_agent.py`** — 15,142 lines. Holds a Python `mind_substrate`
  (Python `Substrate` + `ConsistencyChecker` + `Grammar`), the curiosity drives,
  action selection, save/load, and world handles. Imports the full Python engine.
- **13 worlds** (`*_world.py`): audio, chat, collision, doom, harvest, hle,
  lever, meta_chess, multi_game, number, physics, structure, walker. Each exposes
  `<world>_handle(world, agent) -> {reset, legal_actions, apply_action,
  interpret_acts_on}`. Built on per-world TypedGraphs.
- **56 tests** instantiate `CuriousAgent`; **10 scripts** do too (the
  experiments: doom/harvest/meta_chess/multi_game/chat/probe_*/render_factorial/
  wiki_teacher_demo/bench_recogniser).
- These ~66 consumers are the bulk of the **68 remaining migration sites**.

## What's already done (lean on it)

- **Cortex harness** exists and is the replacement: `CortexScheduler`
  (independent-clock dispatch) + `SpeechCortex`/`IntentCortex`/`MotorCortex`/
  `DevelopmentCortex`/`CodeWritingCortex`/`auditory_cortex`. `develop.py` runs
  the speech agent entirely on it — NO `CuriousAgent`.
- **Native save/load**: `_native.Substrate` has `graph_to_dict` /
  `graph_from_dict` / `load_seed_manifest`. The agent's JSON round-trip is
  already a Rust capability.
- **Native rule engine + search**: `add_rule` / `apply_rule_once` / `run_rules`
  / `tick` / `Substrate.search` (this migration). The drives compile to these.
- **Surprise drive is FULLY graph-resident** — the reference template. See
  `DRIVES_MIGRATION_TODO.md`: a 7-rule cascade dispatched by a Reflex, all four
  Python counter dicts deleted, salience as a 33-node subgraph. 14 sub-phases.

## The crux

The cortices replace **specialized faculties** (speech, motor, intent,
development, code-authoring). They do NOT yet replace the **general
curiosity-driven action loop** — the `action_*_estimate` drives (novelty,
boredom, frontier, regret, opportunity, failure, ticks, population, …) + action
selection that make the agent "alive" on an arbitrary world. That loop is the
heart of the project and is the thing that must go native before `CuriousAgent`
can be deleted. `DRIVES_MIGRATION_TODO.md` is the live plan for exactly this.

## Five workstreams

### A. Drives → graph-resident Rewrite Rules (the hard core)
Tracked by `DRIVES_MIGRATION_TODO.md`. Surprise ✅. Remaining (its estimates):
- **Insight drive** (biggest, ~3–5 sessions): the periodic generalization pass
  (`_promote_to_type_level`, `_discover_categories`, `_discover_action_affinities`,
  `_resolve_hypotheses`, `_reground_predicates`) → per-phase rule cascades.
- **Locomotion / motor** (~2–3): waypoint/sampling orchestrators → rules; the
  `motor_value` Term is already graph-resident.
- **Impasse** (~1): the teacher-invocation boundary — keep as a Python channel
  or wrap as a world-channel write (needs §7 world-I/O channels).
- **DMN / self-introspection** (~1, cleanup): already mostly dispatched rules.
- **Python-state index dicts** → graph-walk helpers (`_concept_nodes`,
  `_subroutine_nodes`, `_emotion_nodes`, `_pattern_nodes`, …): ~½–1 each.
- Adjacent: ~30 new core Terms in Rust (~2), world-I/O channels (~1–2),
  conformance suite (~2).
This workstream is the gating one — everything else waits on the loop being native.

### B. Seeding → seed files
`curious_agent` has ~18 `install_/seed_` methods that build the agent's boot
graph (concepts, rules, reflexes, frames, microtheories). These move to versioned
**seed JSON** (`seeds/*.json` + the `Seed`/`SeedRegistry` loader, which already
exists) so a cortex-harness agent loads its capability set by seed id (CLAUDE.md
"seeds are modular"). Much of the 15K lines is this seeding, not loop logic.

### C. Save/load → already native
`graph_to_dict`/`from_dict`/`load_seed_manifest` exist; the `CuriousAgent.save`/
`load` JSON path retires once construction is a seed-load.

### D. Worlds → native handles or archive
- **Decide per world.** Most are dormant experiments (collision, doom, harvest,
  lever, meta_chess, multi_game, physics — no tests). Candidate to **archive**.
- The few with tests (walker, structure, number, chat, audio, hle, cross) port
  their handle to drive a cortex-harness agent on a `substrate_rs.Substrate`
  (the world builds its state with `add_node`/`add_edge`, ticks the substrate).
- A world handle is small (~50–100 lines); the cost is the agent loop it drives
  (workstream A), not the handle itself.

### E. Tests + scripts → migrate or retire
- **56 tests**, by what they exercise:
  - drives/behavior (insight, discovery, goals, frontier_seeking,
    predictive_and_boredom, action_*, meta_curiosity_and_t3, epistemic_state,
    temporal_discovery, reflexes, master_thread, meta_cognitive, …) → re-test at
    the **cortex-harness** level as each drive goes native; retire the Python
    versions.
  - math/reasoning (groups, rings, relations, theorems_as_terms, word_grounding,
    core_vocabulary) → could move onto the native engine independently (some
    overlap with the reasoning floors already migrated).
  - speech/teacher (agent_speech, conversation, intent, psychology, dict/wiki/
    grammar_teacher) → cortex harness (speech stack is already native).
  - worlds (walker/structure/number/chat/audio/cross/hle) → follow workstream D.
  - renderers/tools/persistence/concurrency/seeds → port or retire individually.
- **10 scripts**: repoint to the cortex harness (like `develop.py`) or archive
  the dormant experiments.

## Ordering

1. **A first** — it gates everything. Follow `DRIVES_MIGRATION_TODO.md`
   (insight → locomotion → impasse → DMN), using the surprise-drive template and
   the now-available native rule engine. Each drive: build the rule cascade,
   delete the Python orchestrator + its state dicts, validate.
2. **B in parallel** — extract seed data to JSON as drives clear (construction is
   separable from the loop).
3. **D + E** — once the loop is native, port the live worlds' handles + migrate
   their tests; archive the dormant worlds/scripts.
4. **Delete** `curious_agent.py` and the Python `substrate/` package when the
   last consumer is off them.

## Honest size

This is **many sessions** (the drives alone are ~10–15 per the TODO's estimates,
plus worlds/tests/seeding). It is the project's core re-architecture, not a
mechanical sweep — and unlike the reasoning floors, there is no one-shot recipe.
The reasoning-floor migration (done) cleared the easy 25%; this is the hard 75%,
and it is already scaffolded by the surprise-drive template + `DRIVES_MIGRATION_TODO.md`.
