# Recursive self-improvement, tranche 18: results (2026-10-10)

Follows the [tranche 17 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE17_RESULTS_20261010.md). That tranche grounded 367 jargon words through the genus of their held definition. Its precision (~77%) was a manual reading only. This tranche makes genus reading measurable, compares the agent's own reader against the bespoke one, and fixes the reader against an exact benchmark.

## Summary

| Item | Result |
|---|---|
| **Exact genus benchmark** | **Built.** `evaluation/genus_reader_benchmark.py` scores 3,242 held words that have WordNet noun senses and a held definition. A pick is correct iff a genus sense is in the word's own hypernym closure. Splits: dev/test by hash, and quoted WordNet gloss vs free text. The definitions are frozen in `evaluation/fixtures/genus_benchmark_definitions.json`. |
| Benchmark validity | **Quoted glosses: valid. Free text: a loose lower bound.** WordNet usually lacks the technical sense a free-text definition is about (for example "thread: execution context"). A 40-miss sample showed about 22 of 40 free-text "misses" were correct gloss heads. |
| **Head reader v2** | Gloss **test** precision **0.637 → 0.673** (+3.6 pts), coverage 0.971 → 0.939. On free text (lower bound) it is unchanged: 0.145 → 0.148. |
| The agent's own reader | `reading_collapse.read_clause_order_n` gives a genus for 83% of words, with gloss test precision 0.652. **It is not better** than the head reader. Where the two disagree, the head reader is usually the right one. |
| Corroboration | When the two readers **agree**, precision is higher: gloss test 0.725 vs 0.506; manual identity domain 85% vs 70%. **Not adopted as a gate** (see §4). |
| Identity domain (manual) | 8 of the 367 tranche-17 picks change: 6 better, 1 still wrong, 1 worse. Plausible picks rise from 77.9% to about 79.0%. 196 words remain identity-only. |
| NLTK | `reading_collapse._clean_head` now looks compounds up in the sense table instead of NLTK (verified equal on compounds). |
| Regression | §5 |

## 1. The benchmark

The scoring rules:
- **Hit:** a genus noun sense is in the hypernym closure of the word's own noun senses, and it passes the steering aperture's specificity test (`extent*1000 <= 50*words`).
- **General:** a genus sense is in the closure but is too broad to pass that test (`person.n.01` for "secretary"). This is correct but never decides a match.
- **Miss:** a genus was picked and none of its senses is in the closure.
- **None:** no genus was picked.

Two headline figures, both per pick:
- **Precision:** (hit + general) / picked.
- **Specific precision:** hit / picked.

Extents are read from the current `seeds/lexical_qualia.json`, so specific precision shifts slightly when the index changes. The dev/test split uses sha256(word) mod 2. Readers were tuned on dev only.

`evaluation/genus_reader_compare.py` writes `evaluation/results/genus_reader_compare.json`. The tranche-17 reader is loaded verbatim from commit `f7c016b1`, so the baseline is pinned.

| Reader | gloss dev P | gloss test P / Ps / cov | free test P / cov |
|---|---|---|---|
| t17 head reader | 0.626 | 0.637 / 0.529 / 0.971 | 0.145 / 0.966 |
| **t18 head reader** | 0.687 | **0.673 / 0.561 / 0.939** | 0.148 / 0.964 |
| agent reader (`read_clause_order_n`) | 0.645 | 0.652 / 0.471 / 0.834 | 0.147 / 0.849 |
| agent, falling back to t18 | 0.642 | 0.660 / 0.493 / 0.987 | 0.150 / 0.990 |

## 2. Reader fixes (`domains/lexical_qualia._genus_of_segment` / `definition_genus`)

Each fix is kept only if it helped on the gloss dev split and did not regress the identity domain:
- A held "X of Y" compound is a single head: "a body of water" → `body_of_water`.
- Parenthesised asides are removed rather than cut at.
- A relativizer ends the head noun phrase after any noun reading: "a criminal who takes" → criminal.
- A postnominal participle ends the head noun phrase, but only when it is followed by a determiner, a preposition or nothing: "an officer holding a rank" → officer. A prenominal participle stays inside the noun phrase: "retired footballer", "wiring diagram", "Double-ended queue". The first, unconditional version of this cut broke 9 identity words.
- The quoted gloss's bookkeeping ("synonyms: …", "e.g. …", "+N other senses") is dropped.
- A verb-form head candidate with no noun sense is skipped ("a hollow device made of" → device). An unheld noun head stops the search, so "reference encoder" gives no genus rather than "reference".
- "X is surname of:" pages are treated as disambiguation stubs.

Tried and reverted:
- **An any-noun-reading fallback for heads.** Coverage went up but precision went down on dev.
- **Ignoring Wiktionary "name" readings when choosing the primary POS.** Gloss dev went 0.687 → 0.705, but in free text it made proper names count as heads ("Gibson", "French", "Latin"). That added 5 new wrong picks in the identity domain.

## 3. Identity domain (manual)

`manual_audit` uses the tranche-17 labels in `evaluation/fixtures/genus_manual_audit_t17.json` (81 wrong out of 367, labelled before this tranche). An unchanged pick keeps its label. The 8 changed picks I judged by hand:

| Word | t17 → t18 | My judgement |
|---|---|---|
| ambisonics | order → format | fixed |
| comitative | agent → entity | fixed |
| datacenter | housing → facility | fixed |
| teleosemantics | function → content | fixed |
| decorrelation | blocks → none | wrong pick removed |
| rea | nation → nation_of_islam | better |
| aboutness | referent → component | still wrong |
| tcmalloc | caches → thread | worse |

The result is about 77 wrong out of 366 picks, so **about 79% plausible** (up from 77.9%). The gain on quoted glosses mostly does not carry over to free-text jargon definitions.

## 4. Corroboration: measured, not adopted

When the head reader and the agent's reader return the same genus, precision is higher:
- **Gloss test:** 0.725 when they agree vs 0.506 when they disagree.
- **Identity domain (manual labels):** 192 agreeing picks at 84.9%, against 175 at about 70%.

Gating `lexical:definition` qualia on agreement would remove about 50 wrong genera, but at the cost of about 120 correct ones. A gate also cannot be expressed in the aperture: the aperture filters the shared quale's dimension, and that dimension is the genus *sense*. Doing it would need a tentative edge type that `ReachableFrom(has_quale)` does not follow. This is left as a decision. `definition_genus_by_reading` is kept so the measurement can be reproduced.

## 5. Regression and envelope

- **Regression:** the same 344 files, compared against `pf_t17.failed`. **0 new failures, 0 fixed.** The failure set is identical (204), with the same 6 timeouts (`test_autonomous_cycle`, `test_residual_promote`, 4× `test_recount_*`). The divergence fixture was restored after the run.
- **Tests:** `tests/test_lexical_qualia_migrated.py` 22 pass (8 new: 6 reader cases, the benchmark gate against the pinned tranche-17 reader, and the NLTK-free `_clean_head`). `tests/test_nl_steering_migrated.py` 12 pass.
- **Envelope:** peak 185.6 MiB (cap 200 MiB), ingress 18.2 ms. All resource assertions are True.
- **Index:** `seeds/lexical_qualia.json` v1.2.0. Two generator runs are byte-identical. Grounding: sense 4,434, closed_class 77, definition 366, function 36, identity 196.

## Next

- Give the identity domain a gold set that does not depend on my reading (for example, teacher confirmation of each genus), because the free-text benchmark cannot separate readers.
- Decide on the corroboration gate (§4).
- Index consumers: `concept_signature` reading `has_quale`. The blast radius is mapped: the closed `lexical` family needs a declared `lexical:quale` dimension, `test_reframing_proposer` boots a full agent, and `relational:has_quale` is already emitted where `out_edges` exists.
