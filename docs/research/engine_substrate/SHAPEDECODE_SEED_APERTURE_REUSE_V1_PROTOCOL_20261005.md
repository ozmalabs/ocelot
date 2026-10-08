# ShapeDecode seed aperture reuse census v1 — protocol

## Question

Across checked-in seed JSON, where are name-scoped ShapeDecode Terms used, and which are nested in operators that repeatedly evaluate a value or predicate over candidate nodes?

## Method

Parse every `seeds/*.json` file and recursively walk the decoded JSON tree. Count each object whose `type` is `ShapeDecode` and which declares `codebook_scope`. Record seed path, JSON pointer, codebook type, and the operator context. Classify a call as repeated under `MaxOver.value`, `Argmax.value`, or `Filter.predicate` only when it is nested under that exact repeatedly evaluated field. All other scoped calls are `other`; no inference about call frequency is made. Record SHA256 for every scanned seed. The independent analyzer recomputes the census from the present seed files and compares rows and source digests.

## Limits

This is a static census of checked-in seed JSON only. It does not count Python-built Terms, tell whether a seed is loaded or a rule fires, estimate calls per task, characterize runtime codebook populations, or establish cache benefit. The category indicates a syntactic repeated-evaluation context, not observed runtime repetition.
