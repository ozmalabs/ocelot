# Engine / substrate mechanics

## Decision and risk boundary

The engine's general commitment gate establishes a context-specific future
manifold as a time-indexed shape tube, then compares `wait`, `refine`, and
`commit` projections against the complete tube. Execution chooses the minimum
sufficient action/intervention that keeps the projected tube inside it; goals
only break equal-intervention ties. Width, information loss, and time bounds
are explicit fields, with changes treated as explicit transitions. Hard safety
vetoes and external approval remain separate, non-tradeable host boundaries.
The F-16 is one proving ground among many.

At each projected time slice the engine computes retained, lost, and escape
residual shapes itself. The time/width/information-loss triangle bounds those
residuals; complete cells and topology links are retained for audit. The gate
enforces this shape residual within each assessment, not persisted lineage
across assessments. Manifold momentum is nonphysical continuity when
longitudinal callers reuse an established manifold; identity or bounds changes
must be represented by those callers as explicit transitions.

The rule-engine internals underneath every capability doc in this
directory: the `run_rules` fixpoint itself, the Python-to-Rust migration
that made it canonical, and the project's own self-improvement/self-account
machinery. If `docs/features/dynamic-quantization.md` is "the loop that
learns," this doc is "the engine that runs the loop."

## The migration: Python agent → graph-native, agent-driven

`CLAUDE.md`'s own history is the primary record here (see its "Migration is
COMPLETE" and "Composer + driver migrated" sections) — this doc summarizes
rather than repeats it. In outline: the ~13K-line `CuriousAgent` Python
class (perception, intent, conversation, render, teaching, goals, planning,
spatial routing, and the self-growing Γ_meta substrate) was deleted outright
and replaced by seed-booted graph data (`substrate/boot_core.py` +
`substrate/world_adapter.py`) running on the Rust `substrate_rs` engine. The
regression gate for that migration — 598 `pytest -k migrated` tests as of
its completion — is why `-k migrated` is this tree's standing test
convention (`docs/CODE_MAP.md`'s testing section).

That migration is complete for the agent's core decision loop, but the
**legacy pure-Python `(G,Γ)` engine files under `substrate/*.py`**
(`graph.py`, `dsl.py`, `grammar.py`, `checker.py`, `learner.py`, ...) are
not fully retired tree-wide:
`docs/research/engine_substrate/SUBSTRATE_RS_MIGRATION.md` is a live
migration map, not a closed-out report, and named dozens of remaining
Python-substrate call sites (mostly
test/world-graph construction, which `CLAUDE.md` explicitly permits — see
its "What Python is allowed to do" boundary) at the time it was last
updated. Read that map, not this paragraph, for the current call-site
count if it matters to your work.

## Engine mechanics that don't fit under any one capability

A cluster of root-level `ENGINE_*`/`GENERIC_*`/`ROBUST_ORDER_N_WITNESS*`
documents (now `docs/research/engine_substrate/`) covers rule-matching
correctness issues that are properties of the engine, not of any one
domain: **determinism of `Argmax`/`Argmin` under ties**
(`ENGINE_ARGMAX_DETERMINISM_*`), **instrumenting what value a winning match actually
carried** (`ENGINE_WINNER_VALUE_*`), **incremental match** and **predicate
retraction** (can the engine update its match set without recomputing from
scratch when one fact changes — and can it *retract* a previously-derived
fact cleanly), the **empty-match-set proof** (a specific correctness
property: a rule whose match set is empty must behave identically to one
that was never installed), and **dirty-propagation precision** (does a
change's "this might now match differently" flag reach exactly the rules it
should, no more, no less). `GENERIC_ORDER_N_*` is the dimension-generic
version of the order-N discovery mechanism `docs/features/vision.md`'s
"physics from observation" section uses concretely — this is where it was
built as a property of *any* dimension rather than one hard-coded to space.

## Self-improvement and self-account machinery

The agent's standing self-repair loop, summarized in depth in `CLAUDE.md`
("THE AGENT FIXES ITSELF WHERE IT IS GRAPH-NATIVE," "THE AGENT FINDS ITS OWN
GAPS"): a knowledge gap self-heals via its own teacher-grounding chain; a
graph-native capability gap can be experimented on and adopted through the
`SelfConcern` → `StandingConcern` → experiment → adopt pipeline; a
Python-layer gap (something the agent's cognition cannot see because it
isn't graph data) can only be *found and filed*, honestly, never silently
patched by the agent itself.
`docs/research/engine_substrate/CURIOUS_AGENT_TEARDOWN.md` and
`DRIVES_MIGRATION_TODO.md` document specific pieces of this transition;
`docs/research/engine_substrate/METACOGNITIVE_LEARNING_RESULTS.md` covers
the agent treating its own learning plan as a revisable graph program;
`CAPABILITY_GRAPH.md` covers the agent's measured self-model of its own
competence (a graph with two flows computed over it by the agent's own rule
engine).

## Where the code lives

- Rust: `runners/dsl/src/graph.rs`, `graph_rules.rs`, `rewrite.rs` (the
  fixpoint), `term.rs`.
- Python boot layer: `substrate/boot_core.py`, `substrate/boot_all.py`,
  `substrate/seed_loader.py`, `substrate/world_adapter.py` — see
  `docs/CODE_MAP.md`'s `substrate/` section.
- Gates: `tests/test_argmin_unique_migrated.py`,
  `tests/test_term_eval_counter_migrated.py`,
  `tests/test_generic_order_n_migrated.py`, and the broader engine-tagged
  migrated suite.

## For the full history

`docs/research/engine_substrate/` holds the migration maps, the
engine-correctness prereg/results pairs, and the self-improvement design
documents listed above. See that folder's `INDEX.md`.
