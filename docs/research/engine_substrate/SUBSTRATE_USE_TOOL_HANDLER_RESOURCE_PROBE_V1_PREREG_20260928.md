# UseTool handler resource and repeatability probe v1

## Question

Which symbolic-perception handlers return repeatable values from the current local resource snapshot in fresh processes, and which depend on missing/downloaded corpora or other external resource acquisition?

## Scope and protocol

- Freeze the repository source plus the four available local slab pairs (`conceptnet_en`, `wikt_antonym_en`, `wikt_figsense_en`, `wikt_pos_en`) by SHA-256 before workers start.
- Run three independent worker processes. Each invokes all 15 `HANDLERS` on one fixed representative input twice in the same order. A worker begins with empty Python handler caches.
- Replace NLTK corpus downloads and ConceptNet slab construction with recording failures; block socket connections. No network/resource acquisition is permitted.
- Preserve successful values, exception type/message, attempted acquisition calls, and local resource identities. The measure is handler repeatability in this checkout, not semantic accuracy or production frequency.
- Analyzer gates: all three workers have identical source/resource locks; every handler is represented in every worker; successful repeated values agree; acquisition attempts and failures are reported, never counted as successful semantic results.

## Fixed cases

`wn_antonym(hot,cold)`, `wikt_antonym(hot,cold)`, `cn_antonym(hot,cold)`, `derive_opposes(deafening,silence)`, `wn_animate(dog)`, `wn_verb_agentive(whisper)`, `text_valence(wonderful terrible)`, `wikt_metonymic(crown,monarch)`, `cn_contiguity(crown,monarch)`, `shape_cross_domain(crown,monarch)`, `wikt_idiomatic(kick the bucket)`, `is_extreme(million)`, `is_minimizer(barely)`, `is_intensifier_spike(fantastic)`, `text_severe(catastrophic)`.

## Limits

One input per handler cannot establish lexical accuracy, complete purity, or behavior across resource versions. Replacing acquisition functions intentionally tests the offline boundary; it does not simulate a successful download or corpus update. Any local slab may still be stale relative to its upstream source.
