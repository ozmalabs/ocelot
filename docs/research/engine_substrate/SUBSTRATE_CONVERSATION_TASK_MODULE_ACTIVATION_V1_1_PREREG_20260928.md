# Conversation task module-activation panel v1.1

Date: 2026-09-28  
Status: preregistered after v1 exposed an unlocked WordNet corpus/cache dependency.

## Change from v1

Keep the five tasks, fixed schedule, function-call instrumentation, per-task oracle, and two fresh processes per condition unchanged. Extend the source lock to include the WordNet corpus selected by `domains.wordnet_membership._find_corpus()` and the derived SQLite index selected by `_connection()`. The expected database must exist before locking and its schema/digest metadata must match the corpus digest. The same immutable warmed database is used by all workers; its path, byte count, SHA-256, corpus path/digest/SHA-256, and environment selector are checked before/after each worker and around the whole panel.

## V1 evidence disposition

The v1 capture and analyzer passed their declared gates, but a post-run code-path audit found `domains.wordnet_membership._find_corpus()` reads `${HOME}/nltk_data/corpora/wordnet.zip` and `_connection()` reads/writes a digest-keyed SQLite index under the system temporary directory. Neither input was in the v1 fingerprint. The scene-description call trace differs sharply across replicates: v1 scene worker 0 called `_iter_lines` 161,363 times while worker 1 did not, consistent with first-build versus existing-cache paths. V1 remains valid as an exploratory activation trace but not a source-stable resource comparison.

## Gates

All v1 source/replication/trace gates remain. Add:

1. Corpus SHA-256 and derived database SHA-256/size are stable across every worker and match the preregistered lock.
2. Database metadata is exactly `(schema=1, digest=<corpus digest>)` before each worker; no worker mutates the database.
3. No worker calls `_build_database`; if any does, preserve output and mark the cache-state gate failed rather than pooling costs.

The database is intentionally pre-existing and shared read-only so the experiment estimates steady-state task activation. It does not estimate cold cache construction cost.
