# Persistent learner retention contract

**Scope:** P25.01 specification. This contract defines identity, information accounting, and evaluator boundaries for retention experiments. It establishes no retention benefit and does not implement runtime deletion, consolidation, or a new memory policy.

## Persistent learner lifecycle

Each stream constructs one native learner before acquisition and carries that same learner instance, native substrate, agent root, owner identity, and shared budget through the complete ordered lifecycle:

`acquire → pre-delay test → offline treatment and independent interference → delayed test`.

The pre-delay test is observational and cannot replace or clone the learner. Offline work may update that learner only through the registered native interfaces. The delayed test is delivered to the same learner. Restart checks serialize and restore the same logical learner state and capacity ledger; they may not instantiate a fresh learner and replay evaluator-held target records into it. The implementation must record stable learner identity and checkpoint lineage at every boundary so a restart cannot masquerade as continuity.

## What counts as learner memory

The memory ledger accounts for every dynamically retained byte that can contribute to recovering an acquired or tested effect, including:

- raw episodes, observations, action/outcome receipts, counterexamples, and source-target maps;
- hypotheses, dimensions, learned rules, definitions, exceptions, and provenance needed to interpret them;
- chunks, summaries, compressed payloads, decoder programs or metadata, indices, references, and reconstruction witnesses;
- cached predictions, embeddings, task-specific state, pending work, and durable checkpoint data;
- copies in graph attributes, Python objects, native storage, files, caches, or any other learner-accessible location.

Each dynamic representation is charged once per independently stored copy. Canonical serialized payload bytes, key/index/reference overhead, container and decoder metadata, and retained provenance are included. Fixed executable/runtime overhead is measured and reported separately, because it does not scale with acquired content; any dynamically added rule, vocabulary, table, or per-stream state is charged as content. The ledger reports charged bytes, capacity, rejected writes, evictions, retrieval/decode work, and storage-location inventory. A representation not inventoried and charged is not available to the learner.

Reconstruction is information access. If an evicted representation can be rebuilt from a retained summary, witness, cache, checkpoint, world object, or host-side copy, all such retained information and the read/rebuild work are charged. Compression is a valid representation only when its encoded bytes, decoder, metadata, exceptions, and provenance are charged and the reconstruction is verified. Reporting compressed size alone does not establish consolidation or lower total memory.

## Equal retention and protection rules

All arms use identical admission, capacity, accounting, protection, eviction, checkpoint, and retrieval semantics. Target-task receipts are ordinary learned content and receive no target-specific protection. Protection, if later justified for a general safety or audit class, is declared before allocation, applies identically across arms and content instances, and may preserve provenance/status only; it must not preserve an uncharged answer-bearing payload or bypass capacity. An over-capacity write is rejected or causes the same registered eviction behavior in each arm.

The external evaluator may retain immutable world history and sealed labels for scoring and audit. This history is not agent memory: it is inaccessible to the learner, treatment code, task selector, checkpoint restoration, and answer path. Only actual authorized world receipts explicitly delivered to the learner become learner-accessible evidence, and then their full representation is charged. The evaluator records the boundary and verifies that hidden history cannot be queried or copied into learner state.

## Required audit record

For every boundary, record the learner identity and checkpoint lineage, memory capacity and charged use by representation class and storage location, protection class, evictions/rejections, retrieval and rebuild costs, native work and shared-budget debits, and hashes of the learner-visible state. Record external world history separately. A failed identity, uncharged recoverable copy, selective target protection, or evaluator-history leak invalidates the stream structurally; do not reinterpret it as a retention score.

P25.01 is specification-only. Later P25 tasks must implement and test these rules before any held-out allocation. The planned P25 comparison is sleep/consolidation, replay-only, matched-work awake, and no-offline under common memory semantics; this contract does not presuppose a treatment benefit.
