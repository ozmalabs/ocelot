# Shape-decode cache-key trace probe v1 preregistration (2026-09-26)

## Question

Does the native access trace expose `sd_cache_key` typed-population fingerprint work on each identical computed `DimInfer`, including the second call that can reuse an SD result within one rule firing?

## Design

Use fresh native substrates in a 2×2 paired design: one versus two identical computed `DimInfer` effect values, each with tracing disabled/enabled. Each substrate has one `CodebookPart` and one `DimensionGenerator` carrying marker attributes, plus one matched trigger edge. The rule writes each computed result to a separate attribute. The rule's changed write produces one progressing firing and a second closure firing with no further progress; `sd_ops` resets per firing and is retained across sibling effects. The independent workload controls are the authored effect count and exact terminal state/progress. The direct instrumentation oracle is `term_index_query` count per codebook type; source inspection confirms this marker is emitted once each time `sd_cache_key` fingerprints that type.

## Predictions

- For each trace-enabled arm, two effects produce twice the query-marker count of one effect, because both computed terms build a key in each firing.
- Node/type/attribute reads increase with the additional key fingerprint, while decoder miss-path scans add reads only when the result is not cached. These event classes currently share type/attribute event kinds, so this probe will not claim an exact miss count from those rows.
- Traced and untraced terminal states, progress, and statuses match; plain arms emit no access events; no trace rows overflow.

## Limits

The result measures instrumentation visibility and bounded cache reuse in one authored `DimInfer` case. It does not prove general trace completeness, quantify cache speedup, measure overhead, or cover direct evaluation outside a RuleUID. Cache hit/miss counts are inferred from source-controlled cache lifetime plus the paired workload shape, not emitted as explicit hit/miss events.
