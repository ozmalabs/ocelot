# Recursive self-improvement, tranche 15: results (2026-10-09)

Follows the [tranche 14 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE14_RESULTS_20261009.md).

Direction from the user: every held word should link to one or more qualia. Qualia are native and persisted, and they are a conceptual index whose purpose is fuzzy matching. Steering should match by qualia, not by words, but that is one consumer, not the reason for the index.

## Summary

| Item | Result |
|---|---|
| **Lexical qualia index** (native, persisted) | **Done.** `seeds/lexical_qualia.json` holds 20,571 `Quale` nodes and a `has_quale` DAG (16,750 edges). At boot, 30,840 `has_quale` links connect all 5,109 held words to their qualia. **Every held word links to ≥ 1 quale.** |
| Words heard for the first time | **Become held words with qualia** when WordNet gives them a sense or the held ClosedClass data gives them a role. A token with neither ("zorblat") stays unheld, so the "what does X mean?" path is unchanged. |
| Filed concerns | **Carry qualia the same way turns do.** Their content is tokenised into Mentions, which the native intent rules resolve to held words. |
| **Steering by qualia** (`conversation_steering` v2.0.0) | **Done.** The concern a steer turn names is picked by shared qualia inside a held aperture. "Work on the ordering gap." promotes "alphabetise list"; the word "ordering" appears in no concern. |
| Resource cost | **Measured, and it breaks a stated envelope.** Conversation seed profile RSS went from 150 MB to 322 MB. That is about 100 MB for the index nodes and about 100 MB for WordNet, which is now warmed at boot so a turn never pays the cold load. Full boot time: 11.4 s → 13.2 s. See §5. |
| Regression | **0 failures attributable to this tranche** after 1 test-premise update, across 344 files (every file that boots or converses, plus the tranche-14 scope). |

## 1. The index

Generator: `scripts/gen_lexical_qualia_index.py`. It is deterministic (two runs are byte-identical) and writes one JSON object per line, so the file diffs cleanly (4.5 MB).

**`Quale{name, dimension, lemma, pos, depth, extent}` nodes, by dimension:**

| Dimension | Count | What it is |
|---|---|---|
| `lexical:sense` | 19,967 | A WordNet synset: each sense of a held word, plus every hypernym above it. |
| `closed_class` | 6 | A grammatical role from the held `ClosedClass` data in `domain_data/reading_constructions.json` (determiner, preposition, auxiliary, …). A function word's quale is its role. |
| `lexical:identity` | 598 | The word's own identity quale, used only for a held word with no sense and no role (names, jargon). It is the honest degenerate quale until the word is grounded; the count is the visible gap. |

**One edge type, `has_quale`:** word → sense quale → broader quale. A word's whole closure is the native `ReachableFrom(word, "has_quale")` Term.

**`extent`** is an exact count: the number of held words whose closure contains the quale. "entity" has extent 3,374; "alphabetize.v.01" has 1.

**How it loads:**
- The Quale nodes and the DAG are native seed data.
- The word → sense links are persisted in the same file (`word_qualia`). `domains/lexical_qualia.install_word_links` installs them at boot through the `Concept.name` index (`substrate/boot_all.py`, next to the grounding-reach pass). Cross-seed name refs would be resolved by a linear scan of every Concept, about 30k times.
- A full boot reports `{"installed": 30840, "words_linked": 5109}`, 0 failed seeds and 0 anomalies.

**Fuzzy, but exact at the grain.** Two different words match by the qualia their closures share; this is Quale node identity, not string similarity.
- "alphabetise" and "arrange" share `arrange.v.01`, with no letters in common.
- "tabulate" meets "arrange" at a *different* sense, `arrange.v.06`, so senses stay distinct.

## 2. New words and concerns

**New words.** `world_adapter._backfill_knows_concept_for_message` calls `lexical_qualia.ground_word` for a mention with no held Concept. That is the I/O boundary: WordNet is external data a graph rule cannot call.
- It mints the Concept and its `has_quale` links, reusing existing Quale nodes and minting missing senses with their hypernym chain.
- It increments `extent` by exactly 1 on every quale in the new word's closure.
- New words are persisted with the agent's own saved state; the seed is the boot prior.

**Concerns.** `world_adapter._tokenise_self_concerns` tokenises each SelfConcern's `content` once, the same way a turn is tokenised. The same native intent rules then resolve its words.

## 3. Steering by qualia

`seeds/conversation_steering.json` v2.0.0 is emitted by `scripts/gen_steer_qualia_match.py`, which is idempotent; `gen_steer_best_match.py` now reports that it has been superseded. All three steering rules (promote, retire, clarify) read the index natively.

**Target mentions** are every mention of the steer turn except those that are part of the steering construction itself: a referent with a `steer_*` route, or a gap noun.

**Aperture** (held, agent-editable data): `QualiaAperture{name:"steering", resolves:["lexical:sense","lexical:identity"], max_extent_per_mille:50}`. A shared quale counts only if:
- its dimension is resolved, so function words (closed-class qualia) never decide a match; and
- `extent × 1000 ≤ 50 × QualiaIndex.words`, so it is specific enough. Generic qualia such as "entity" or "change" do not count.

All of this is integer arithmetic.

**The pick** is lexicographic:
1. The most target mentions covered: a turn word covers a concern when their closures meet inside the aperture.
2. The fewest concern mentions left uncovered.
3. The oldest concern.

If nothing is covered, the turn lands on the "couldn't tell which gap" reply.

End-to-end check (shadow read on), with five noted concerns, one of them a divergence concern that quotes an earlier steer turn:

| Steer turn | Result |
|---|---|
| "Work on the alphabetise data gap." | promotes *alphabetise data* (the tranche-13 case) |
| "Work on the arranging gap." | promotes *tabulate list* ("arrange" covers both tabulate and alphabetise; fewest uncovered, then oldest) |
| "Work on the condense gap." | promotes *condense data*, not the quoting divergence concern, by the fewest-uncovered rule |
| "Work on the zorblat gap." | clarify reply |
| "Drop the summarise report gap." | retires *summarise report* |

Each turn took about 0.3 s.

**Tests** (`tests/test_lexical_qualia_migrated.py`, 6 tests):
- every held word has a quale;
- the closure is native `ReachableFrom`;
- a function word's quale is its role;
- new words become held, and "zorblat" does not;
- shared-sense fuzzy matching, with distinct senses kept apart and exact `extent`;
- "ordering" names "alphabetise list";
- the generators are idempotent.

All 12 `test_nl_steering_migrated.py` tests pass on v2.0.0, including the tranche-14 regression test.

## 4. Regression

**Scope.** 344 test files: every file that calls `converse` or `load_all_seeds`, plus the tranche-14 scope plus the new test file.

**Baseline.** The 91 files with failures were rerun with `substrate/boot_all.py`, `substrate/world_adapter.py` and `seeds/conversation_steering.json` restored to HEAD and `seeds/lexical_qualia.json` removed.

**Result.** 206 failures on the tranche-15 tree; 4 did not fail on the reverted tree:

| Test | Cause | Resolution |
|---|---|---|
| `test_pronoun_enrichment_migrated::test_unsafe_shadow_referent_stays_unresolved` | Its premise was "no Concept named saturn". "Saturn" is a WordNet word, so it is now held when heard and the pronoun resolves. | The premise now uses a token with no sense ("zorblat"). Passes. |
| `test_phase7_daemon_ingress_envelope::test_signal_only_daemon_ingress_uses_native_authority_without_external_io` | Ingress latency broke the 50 ms envelope: the first unheld word paid WordNet's cold load inside the turn. | WordNet is now warmed when the index is installed at boot (the existing `warm_wordnet` precedent). Ingress measured at 20 ms; passes. |
| 2 × `test_topic_span_migrated` (`deep_ingest_off…`, `topic_not_in_any_document…`) | The reverted rerun of this file did not finish (killed when the tree was restored), so it gave no comparison. | Both are pre-existing failures recorded in tranche 11. |

`test_autonomous_cycle` timed out on both trees, as before. The run rewrote `tests/fixtures/comprehension_divergence/divergence.json` (latency only), and it was restored.

## 5. Resource cost (open)

Conversation seed profile (`evaluation/phase7_daemon_ingress_envelope.load_conversation_seed_profile`, no shadow read):

| | RSS after profile |
|---|---|
| HEAD | 150 MB (just under the 150 MB `absolute_rss_bounded` limit) |
| index, no WordNet | 214 MB |
| index + WordNet warm (shipped) | **322 MB** |

**The index (≈ 100 MB).** A native load of the 20,571 Quale nodes and 16,750 edges alone costs about 60–80 MB, roughly 3 KB per node in the substrate. Parsing the manifest in Python costs the rest. I removed the cached table, but the arena isn't returned to the OS.

**WordNet (≈ 100 MB).** This is NLTK's in-memory WordNet. A default daemon already pays it, since shadow read is on by default and warms WordNet. A non-shadow profile now pays it too.

`absolute_rss_bounded` is reported by the envelope measurer but not asserted by its test, so the suite passes. It is still a stated product bound, and it is now exceeded. That is the first item for the next tranche.

## Next

1. **Bring the index back inside the envelope.**
   - Fewer attributes per Quale node.
   - Runtime grounding from a persisted compact sense table (stdlib sqlite in `domain_data/`) instead of in-process NLTK. That removes about 100 MB and the cold load.
   - Measure per-node substrate cost.
2. **Ground the 598 identity-only held words** (names, jargon) through the teacher and definition path, so their qualia become real senses.
3. **More consumers of the index:** topic routing and analogy candidates. `concept_signature` could read `has_quale` so the computed and native qualia are one thing.
