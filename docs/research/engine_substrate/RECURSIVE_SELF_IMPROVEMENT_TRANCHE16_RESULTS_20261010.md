# Recursive self-improvement, tranche 16: results (2026-10-10)

Follows the [tranche 15 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE15_RESULTS_20261009.md), whose open item was memory: the lexical qualia index plus in-process WordNet pushed the conversation seed profile from 150 MB to 322 MB.

## Summary

| Item | Result |
|---|---|
| **Persisted WordNet sense table** | **Done.** `domain_data/wordnet_senses.sqlite` (18.8 MB, deterministic) holds NLTK's own lemma index, synsets, hypernyms, morphology exceptions and suffix rules. `domains/wordnet_table.synsets(word)` reproduces NLTK's `wn.synsets(word)` exactly, verified on all 5,109 held words plus inflected forms, with 0 mismatches. |
| Runtime grounding without NLTK | **Done.** A word heard for the first time is grounded from the table, so no corpus load and no boot warm-up are needed. The index generator reads the same table, so boot and runtime qualia come from one source. |
| Slimmer Quale nodes | `Quale{name, dimension, extent}`. `lemma`, `pos` and `depth` were dropped, since the table holds them. The seed shrank from 4.5 MB to 3.75 MB. |
| **Memory** | Conversation profile peak **322 → 167 MB** (HEAD without the index: 150 MB). Ingress was 18 ms (limit 50). The index is still **17 MB over** the 150 MB `absolute_rss_bounded` envelope; see §3. |
| Regression | **0 new failures** across 344 files, compared with tranche 15. |

## 1. The sense table

Generator: `scripts/gen_wordnet_sense_table.py`. Two builds are byte-identical. It writes the file and then verifies it against NLTK, and exits non-zero on any mismatch.

| Table | Rows | Contents |
|---|---|---|
| `synset(id, name, pos, depth)` | 117,659 | |
| `hyper(child, parent)` | 97,666 | hypernyms and instance hypernyms |
| `lemma(form, pos, sid, rank)` | 227,277 | NLTK's `_lemma_pos_offset_map`, verbatim and in NLTK's order |
| `exc(pos, form, base, ord)` | 6,048 | the morphology exception lists |
| `subst(pos, ord, old, new)` | | the morphy suffix rules |

`domains/wordnet_table.py` reimplements NLTK 3.10's `_morphy` over these tables:
1. If the form is in the exception list, use the listed bases; otherwise apply one pass of the suffix rules.
2. Keep the original form first, then the forms the lemma table holds for that POS.

It queries sqlite read-only on disk.

Tests:
- `test_sense_table_reproduces_wordnet_synsets_exactly` (inflections, a function word, an unknown token, a hypernym);
- `test_runtime_grounding_does_not_load_the_wordnet_corpus`: the lexical qualia path never calls NLTK.

## 2. Index changes

- `scripts/gen_lexical_qualia_index.py` now reads `domains/wordnet_table`. Duplicate synsets per word are collapsed, so there are 27,046 word links instead of 27,057.
- `domains/lexical_qualia`:
  - `ground_word` mints senses and hypernym chains from the table;
  - `install_word_links` no longer warms WordNet;
  - the parsed manifest is not retained after install.
- Counts are unchanged: 20,571 qualia, 16,750 DAG edges, 5,109 held words, 598 identity-only.

## 3. Memory

Conversation seed profile, as measured by `evaluation/phase7_daemon_ingress_envelope` (no shadow read):

| Tree | RSS peak | Ingress |
|---|---|---|
| HEAD before tranche 15 (no index) | 150 MB | 17 ms |
| Tranche 15 (index + NLTK warmed at boot) | 322 MB | 20 ms |
| **Tranche 16** (index, sense table) | **167 MB** | **18 ms** |

**Where the remaining 17 MB goes.** It is the native cost of 20,571 Quale nodes and 16,750 edges, about 1 KB per node in the substrate. Two things were ruled out:
- renaming the identity attribute, so the boot content index skips Quale nodes, made no difference (191 vs 187 MB in a separate probe);
- WordNet itself is no longer resident.

**Options to close it, each with a cost:**
- **(a) Activate qualia lazily.** The graph would hold a held word's `has_quale` links only once it is used in a turn or concern, with the full index persisted on disk. This weakens "every held word links to a quale at all times" into "every held word has qualia in the persisted index, linked on use".
- **(b) Revise the envelope**, to account for an index the user has directed should be native.
- **(c) Reduce the substrate's per-node cost** (engine work).

This tranche does not pick between them.

## 4. Regression

Scope: the same 344 files as tranche 15, compared against the tranche-15 failure set (`pf_t15.failed`).

- **0 new failures.**
- **2 fixed**, the two tranche-15 fixes now on the committed tree: the daemon ingress envelope and the pronoun premise.
- 204 failures in total, all pre-existing (the tranche-15 baseline already accounted for them against HEAD).
- `test_autonomous_cycle` timed out, as in every run.
- The run rewrote `tests/fixtures/comprehension_divergence/divergence.json` (latency values only), and it was restored.

## Next

- Decide how to close the 17 MB (§3).
- Ground the 598 identity-only held words through the teacher and definition path.
- More consumers of the index: topic routing and analogy candidates (`concept_signature` reading `has_quale`).
