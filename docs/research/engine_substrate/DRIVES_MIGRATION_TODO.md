# Drives Migration TODO

The agent's cognitive drives are being migrated from Python orchestration
to graph-resident Rewrite Rules. The surprise drive is fully complete
(Phase 17b.* — 14 sub-phases, see [[ozma-surprise-drive-fully-graph-resident]]
in memory). This document tracks remaining work + patterns to follow.

## Completed (reference template)

✅ **Surprise drive** — Phase 17b.1 through 17b.3c.11.
   `surprise_investigate` Reflex dispatches a 7-rule cascade:
   construct → execute → top_cause → intervention_mint →
   intervention_sync → cause_selection → hypothesis_mint.
   `dispatch_mode="rule_only"`; no Python in the path.
   Counter migration: EventBaseRate / ActionCount /
   OutcomeCount / ActionEffectCount as graph nodes; all four
   Python counter dicts deleted. Salience formula as 33-node
   graph subgraph. New DSL primitives: `EvalSubgraph`, `Argmax`,
   `Argmin`. ISA #103, #104 (Argmax/Argmin) added to inventory.

## Remaining drives (descending difficulty)

### Insight drive (biggest)

`agent.insight(layer)` — periodic generalization pass with 3 layers:
- Layer 1 (frequent, ~200 ticks): `_promote_to_type_level` +
  `_discover_categories` + `_discover_action_affinities` +
  `_resolve_hypotheses` + `_reground_predicates`
- Layer 2 (less frequent, ~1000): cross-pattern synthesis + pruning
- Layer 3 (rare, ~5000): strategic / long-horizon synthesis

Currently called via Python `insight()` API (mostly from tests).
**Migration approach**: identify each sub-method's data + decision
logic, build per-phase rule cascades (multi-firing for promotions,
single-fire for synthesis). The `tick_insight_promotions` attr
write already exists; preserve that as a rule effect.

Reference template: [[ozma-rule-dispatch-patterns]] +
the surprise drive's 14-phase decomposition.

Estimated: 3–5 sessions.

### Impasse drive (boundary case)

`auto_resolve_impasse` reflex → `resolve_one_impasse` callable.
**Note**: this calls into the agent's `set_self_teacher` chain
(LLM / dictionary / wiki) — a genuine I/O boundary that
arguably belongs as a world-adapter channel (per
[[ozma-runner-agent-world-separation]]) rather than as a rule.

**Migration approach options**:
- (a) Keep as Python callable — accept it's the agent/world boundary
- (b) Wrap teacher invocation as a `channel_write` to a "teacher"
  output channel, with results coming back via the runtime_events
  input channel. The agent's reflexes consume responses.

Approach (b) matches the long-term ISA but needs the world-channel
infrastructure (§7), which isn't built yet.

Estimated: 1 session for (a), or wait for §7 channels.

### Locomotion / motor drive (substantial)

Continuous-control motor planning. Per
[[ozma-continuous-motor-core]] memory:
- `motor_value` Term-tree is already graph-resident
- Per-control dθ/dspeed forward model has fast EMA + single-prim credit
- Python remains for sampling + waypoint generation

**Migration approach**: identify Python orchestrators (waypoint
selection, motor sampling), convert to rules. The forward model EMA
follows the same shape as the emotion EMA (Phase 17b.1).

Estimated: 2–3 sessions.

### DMN / self-introspection (largely done)

`auto_self_insight` reflex → already uses dispatches_to rules
(M-C-C: Monitor / Compare / Author Control Goal). Per
[[ozma-mcc-self-introspection]]. The `self_insight` response was
already retired (the response key still exists in the registry
but isn't wired to any reflex).

**Remaining**: audit + verify no Python state leaks; possibly
delete the dead `insight_layer_1/2/3` callable entries from
the response registry once `insight()` itself is migrated.

Estimated: 1 session, mostly cleanup.

## Adjacent mechanical migrations

These are bounded Python-state cleanups that follow the
`_intervention_stat_nodes` / `_law_nodes` template (commit
`4297161`):

- `_concept_nodes` dict → walk `agent.knows_concept` (with name
  filter). Heavily used; multiple call sites; ~1 session.
- `_subroutine_nodes` dict → walk `agent.authored_subroutine`
  (with name filter). Medium use; ~½ session.
- `_emotion_nodes` dict → walk `agent.has_emotion` (with name
  filter). Medium use; ~½ session.
- `_pattern_nodes` / `_pair_stat_nodes` / `_regime_stat_nodes` /
  `_attribute_nodes` / etc. — various typed indices. Each
  ~½ to ~1 session.

Pattern: add `_find_X(...)` graph-walk helper, replace dict reads,
delete the dict field + writes.

## Adjacent broader work

- **30 new core Terms in Rust runner** (matches ISA §3.1.2 spec
  #70–#99). Mechanical implementation, follows the existing
  variant template. ~2 sessions.
- **World I/O channels (§7)** implemented in Rust runner. Needed
  for the bare-metal vision + the impasse-as-channel design above.
  ~1–2 sessions.
- **Conformance suite drafted (§9)**. Golden agent + synthetic
  world + expected post-state. Requires the world I/O work first.
  ~2 sessions.

## How to resume

1. Read [[ozma-surprise-drive-fully-graph-resident]] + linked
   memories for context.
2. Pick a drive from the list above (recommended start order:
   insight → locomotion → impasse — biggest leverage first).
3. Apply the 5 rule-dispatch patterns from
   [[ozma-rule-dispatch-patterns]]:
     1. Per-N-instance arithmetic (EMA shape)
     2. Construction + dispatch_mode (transitional)
     3. Multi-firing fan-out per element
     4. Shared subgraph + EvalSubgraph
     5. Counter migration (Python dict → graph nodes)
4. Validate with 116+/116 sweep after each commit.
