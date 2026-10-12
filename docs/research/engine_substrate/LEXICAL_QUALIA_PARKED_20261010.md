# Lexical qualia index: parked (2026-10-10)

**Status: parked** at commit `5bd47e1e`, at the user's direction: "this should be documented and parked, and refocus on recursive self improvement". Nothing here is half-built. The index is live and steering uses it; the work stopped at the points listed under "Open decisions" and "Resume points". This file is the single entry point to resume from.

## What exists (all committed, tested, in production boot)

| Piece | Where | Tranche |
|---|---|---|
| Native, persisted qualia index: `Quale{name, dimension, extent}` nodes, one edge type `has_quale` (word → quale → broader quale), and a `QualiaIndex` node. A word's closure is `ReachableFrom(word, "has_quale")`. | `seeds/lexical_qualia.json` (v1.2.0), generator `scripts/gen_lexical_qualia_index.py` (deterministic), install pass in `substrate/boot_all.py` | 15 |
| Every held single-word Concept links to at least one quale. Grounding, in precedence order: closed-class role → WordNet senses → function-word role → genus of its held definition → identity. One rule serves both boot and runtime: `domains/lexical_qualia.qualia_plan`. | `domains/lexical_qualia.py` | 15, 17 |
| Runtime grounding: an unheld word gets a Concept with qualia if it has a sense or role (`ground_word`). A held Concept minted without qualia gets them on first mention (`ensure_qualia`). | `substrate/world_adapter.py` (mention backfill) | 15, 17 |
| Persisted WordNet sense table: an exact reimplementation of NLTK's `synsets`/morphy, so NLTK is never loaded at runtime. | `domain_data/wordnet_senses.sqlite`, `domains/wordnet_table.py`, `scripts/gen_wordnet_sense_table.py` | 16, 18 |
| Steering matches a turn to a filed concern by shared qualia inside an agent-editable `QualiaAperture` (resolves `lexical:sense`, `lexical:definition`, `lexical:identity`; `max_extent_per_mille` 50). | `seeds/conversation_steering.json` v2.1.0, generators `scripts/gen_steer_qualia_match.py` and `scripts/gen_steer_aperture_definition.py` | 15, 17 |
| Exact genus benchmark (WordNet hypernym closure, dev/test, gloss vs free text) and a reader comparison, including the agent's own `read_clause_order_n`. | `evaluation/genus_reader_benchmark.py`, `evaluation/genus_reader_compare.py`, `evaluation/fixtures/genus_*`, `evaluation/results/genus_reader_compare.json` | 18 |

Index counts:
- 5,109 held words, grounded as: sense 4,434, closed_class 77, definition 366, function 36, identity 196;
- 20,785 qualia;
- 18,647 DAG edges.

Cost: conversation-profile RSS peak 185.6 MiB against the project cap of 200 MiB (raised from 150 MiB in `029d6e21`). Ingress latency 18 ms; full boot is about 2 s slower than without the index.

## Measured state (honest)

- **Genus precision.** On held-out quoted WordNet glosses, precision is 0.673 at 0.939 coverage. On the jargon domain the index actually uses, manual reading gives about 79% plausible. Those labels are my own, in `evaluation/fixtures/genus_manual_audit_t17.json`. The free-text benchmark is only a loose lower bound (0.15), because WordNet lacks the technical senses.
- **Corroboration.** Where the head reader and the agent's reader agree, precision is 0.73 vs 0.51 on glosses and 85% vs 70% on jargon. It is measured but not used.
- **Remaining identity-only words (196).** These are mostly proper names and disambiguation stubs.
- **Consumers.** The index is read only by steering. `concept_signature`, topic routing and analogy do not read it.

## Invariants guarded by tests (keep green while parked)

- `tests/test_lexical_qualia_migrated.py` (22 tests): every held word has qualia; the index is native and its closure is reachable; definitional grounding; the runtime invariant; steering by definition; the benchmark gate against the pinned tranche-17 reader; no NLTK on the runtime path.
- `tests/test_nl_steering_migrated.py` (12 tests).
- The RSS envelope tests: `tests/test_phase7_production_envelope.py`, `tests/test_phase7_daemon_ingress_envelope.py`, `tests/test_native_cycle_measurement.py`.

## Open decisions (need the user)

1. **Corroboration gate.** Should a definitional genus link only when both readers agree? That would remove about 50 wrong genera but also about 120 correct ones. It needs a tentative edge type that `ReachableFrom(has_quale)` does not follow, because the aperture can only filter by the shared quale's dimension.
2. **RSS envelope.** 200 MiB was set "for now". Lazy activation of word links remains the alternative (tranche-16 results §3).

## Resume points (in suggested order)

1. **A gold set for jargon genera** that does not depend on the agent's own reading. Teacher confirmation per genus is the obvious source. Without it, readers cannot be compared on the domain that matters.
2. **`concept_signature` reading `has_quale`** (unify computed and native qualia). The blast radius is already mapped:
   - the closed `lexical` family needs a declared `lexical:quale` QualiaDimension (`domains/qualia_schema._check_coord`);
   - `test_reframing_proposer` boots a full agent, so its analogies could change;
   - `relational:has_quale` is already emitted where `out_edges` exists;
   - the Observer `resolves` gate covers only field axes.
3. Ground the 196 names from their pages where a genus exists ("X is a surname", "a village in …").
4. More consumers: topic routing, analogy candidates.

## Results documents

[T15](RECURSIVE_SELF_IMPROVEMENT_TRANCHE15_RESULTS_20261009.md) · [T16](RECURSIVE_SELF_IMPROVEMENT_TRANCHE16_RESULTS_20261010.md) · [T17](RECURSIVE_SELF_IMPROVEMENT_TRANCHE17_RESULTS_20261010.md) · [T18](RECURSIVE_SELF_IMPROVEMENT_TRANCHE18_RESULTS_20261010.md)
