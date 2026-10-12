# Preregistration: durable shape-recall quality pilot

**Question.** After restart and page-out, does the current long-term memory adapter retrieve records under positive scale/offset changes that preserve ordinal rank, and what distinct information does that representation merge?

**Frozen fixture.** Generate all six strict ordinal permutations over the adapter's three projected category features (new_signs, utts, round). Store three replicates in each of two positive magnitude classes per rank shape: 36 durable records in six clusters. Use 12 queries (six rank shapes × low/high magnitude). Each query carries an expected rank label and magnitude label fixed by the generator. Values and labels are generated before any retrieval runs.

**Arms.** Each query is evaluated in a fresh reader process against the durable store using (1) shape recall by the current LongTermMemory adapter and (2) exact-key lookup as a mechanism control. The writer forces all six clusters cold and verifies all records have been evicted before readers start. Readers report restored index counts, paged records, recall result, and bind/recall time.

**Metrics and checks.** Shape-candidate rank-label precision/recall, magnitude-label precision, exact-key correctness, indexed record count, clusters evicted, nodes resident after shuffle, and separate bind/recall timings. Pass criteria: shape recall returns the six records in the matching rank cluster on every query; all six share the requested rank label; the two magnitude labels are equally represented (0.5 precision); exact-key lookup returns the keyed record; every reader indexes all 36 records; all writer clusters are cold before reader launch.

**Interpretation boundary.** Rank-label success is an aligned synthetic positive control, not semantic learning. The magnitude label is intentionally independent information that the rank-only feature projection cannot encode. Report both so high rank-shape accuracy is not confused with general retrieval quality. This pilot does not establish task utility, natural-task prevalence, retention policy quality, or broad memory efficacy.

## Transparent harness amendment before scored rerun

The first invocation completed record writing and cluster eviction but failed on the first child read. Two harness assumptions were incorrect: the adapter's shuffle result is a metadata dictionary (the evicted cluster list is its evicted_clusters field), and the Rust Substrate.nodes() API returns node IDs whose attrs must be read with Substrate.node(). The runner now reads both APIs according to their actual contracts. No retrieval verdict was scored and no fixture, metric, or criterion changed. The input lock is amended before the scored rerun.
