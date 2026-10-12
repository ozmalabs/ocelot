# Recursive self-improvement, tranche 17: results (2026-10-10)

Follows the [tranche 16 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE16_RESULTS_20261010.md). Before this tranche, at the user's direction, the project RSS cap was raised from 150 MiB to 200 MiB (commit `029d6e21`). That change covered the four envelope constants, the malloc_trim threshold and three tests. The conversation profile peak of 181 MiB is now inside the cap (`absolute_rss_bounded` is True).

## Summary

| Item | Result |
|---|---|
| **Definitional grounding** | **Done.** Before this tranche, 598 held words had only their identity quale. Of these, 367 are now grounded through the genus of their held definition, and 36 through the closed-class role the function-word faculty gives them. **195 stay identity-only**, nearly all names and disambiguation stubs. |
| Coverage invariant at runtime | **Done.** A Concept minted at runtime by a path that does not know about the index (for example `teach_microtheory`, dictionary ingest or `learn_word`) gets its qualia the first time a turn mentions it. |
| Steering | `conversation_steering` v2.1.0: the aperture also resolves `lexical:definition`. "Work on the orchestrator gap" now names a "kubernetes" concern. Against the tranche-16 index the same turn found no concern. |
| Genus precision | **About 77% plausible** by my own manual reading (about 85 of 367 picks judged wrong or doubtful); see §2. |
| Memory / latency | Peak 184.6 MiB (+3.7 MiB), inside the 200 MiB cap. Ingress 18.6 ms (limit 50). |
| Regression | **0 new failures** across 344 files. The failure set is identical to tranche 16 (204), with the same 6 timeouts. |

## 1. What a word's qualia are

`domains/lexical_qualia.qualia_plan(word, definition)` is the single precedence rule. The offline index generator and runtime grounding both apply it:

1. `closed_class`: a ClosedClass role from `domain_data/reading_constructions.json`. Unchanged.
2. `lexical:sense`: WordNet senses from the sense table. Unchanged.
3. `closed_class` (new fallback): for a word with no sense, the role from its own definition's POS tag ("(pronoun) ..."), or else from `function_word_reference.classify`. Example: she, him, although, whom map to pronoun or conjunction.
4. `lexical:definition` (new): `Quale{name:"definition:<w>", genus}`. Its `has_quale` parents are the genus's WordNet noun senses, in the same way a synset's parents are its hypernyms. Examples: kubernetes→orchestrator, microservice→service, mutex→lock, qubit→bit.
5. `lexical:identity`: kept only when none of the above applies.

The genus reader is `definition_genus`. It is mechanical and works at the I/O boundary:
- It reads at most 3 definition segments, splitting on `. : ;` and dashes.
- It reads a copula gloss "X is a Y" from Y.
- It skips a segment that predicates something else of the word.
- It drops held "Substrate analogue: …" self-model commentary.
- It treats an empty head ("a type of Y") as Y.
- It cuts at the first preposition, conjunction, relativizer or verb after a noun.
- The head is the rightmost token whose primary reading is a noun (POS from the held Wiktionary faculty), or an out-of-vocabulary token, and it must be at least 3 letters. The longest WordNet noun compound ending at the head wins.

A disambiguation stub ("may refer to", "is the name of") names no genus. The genus is stored on the quale, so every pick can be audited in `seeds/lexical_qualia.json`.

Index v1.1.0:
- 20,784 qualia;
- 18,676 DAG edges;
- 5,109 held words, by grounding: sense 4,434, closed_class 77, definition 367, function 36, identity 195.

Only the 403 formerly identity-only words changed; no word that had a sense or role changed. Two generator runs produce byte-identical output.

## 2. Genus precision (honest)

I read all 367 picks by hand. This is my judgement, not an external gold standard. About 85 are wrong or doubtful. The error classes:

- **A citation segment read as the gloss:**
  - "Priest. Some contradictions …" gives dialetheism→priest;
  - "Victor Turner. …" gives liminality→turner.
- **A clause gloss whose rightmost noun is not its genus:**
  - "Children produce 'goed' …" gives overregularization→children;
  - "Tricking user into …" gives phishing→user;
  - "Affordance for reaching. Distance …" gives reachability→distance.
- **A biography or surname page heading** ("Notable people with the surname") gives cerris→people.
- **Data mismatch:** chucky's held definition describes someone else.

Wrong genera matter because the steering aperture resolves the genus senses, so a wrong genus can create a spurious shared quale. The extent cap (≤5% of held words) limits this only for general senses. The aperture is agent-editable data, so `lexical:definition` can be withdrawn from `resolves` if spurious matches show up.

## 3. Runtime coverage

The mention-grounding loop in `substrate/world_adapter.py` calls `lexical_qualia.ensure_qualia` on each held referent. It is a no-op when the referent already has qualia. Before this, a Concept minted by `teach_microtheory` and similar paths had no `has_quale` edge, which broke the "every held word links to a quale" invariant outside boot. `ground_word` (an unheld word) now uses the same plan, but without a definition. "zorblat" still stays unheld.

## 4. Tests

There are 6 new tests in `tests/test_lexical_qualia_migrated.py` (14 in total, all passing):
- the kubernetes definition quale, its genus and its closure, and microservice meeting service;
- "she" maps to `closed_class:pronoun`, and a "may refer to" stub stays identity;
- the seed stats match the graph;
- a runtime-minted Concept gains a genus quale on first mention;
- steering through a definition (counterfactual: it fails on the v1.0.0 index);
- the aperture generator is idempotent.

## 5. Regression

- Scope: the same 344 files, compared against `pf_t16.failed`.
- 0 new failures and 0 fixed; 204 failures, all pre-existing.
- Timeouts: `test_autonomous_cycle`, `test_residual_promote` and the 4 `test_recount_*` files, the same as tranche 16.
- The divergence fixture was rewritten by the run and has been restored.

## Next

- Raise genus precision on the error classes above. For example, read the definition through the agent's own `reading_collapse.read_clause_order_n` once its compound lookup uses the sense table instead of NLTK. Alternatively, have a teacher confirm doubtful genera.
- Ground the 195 remaining names through their pages ("X is a surname", "a village in …"), where a genus exists.
- More index consumers: `concept_signature` reading `has_quale`, topic routing, analogy candidates.
