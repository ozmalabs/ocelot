# Live operation-scope manifest v1 preregistration

Date: 2026-10-03  
Status: protocol frozen before manifest generation.

## Question

What candidate read/write resource scopes and rule-to-rule dependencies are
recoverable from the source-hashed Term inventory and the request-time native
definitions of rules observed in the live frame capture?

## Inputs and population

Use the source-locked v1.1 request-time rule exports and traces for all three
workers and both prompts. Include every distinct RuleUID with at least one
concrete access-trace row in either request. Use the current 237-variant Term
source crosswalk. Do not use protocol-owned task node membership to include,
exclude, or group rules. Preserve each rule's request membership and weighted
trace counts.

## Scope extraction rules

- Match triples declare reads of their literal typed edge resource.
- `Attr` declares its literal attribute key; `AttrByName` is a dynamic-key
  read. `TypeOf` is a conservative dynamic type read.
- `Neighbours`, `InNeighbours`, `MapNeighbours`, `SlideNeighbours`, and
  `Edges` declare the literal edge type when exported, otherwise an
  all-edge-type/local-adjacency read.
- `NodesOfType` declares a whole-population read keyed by its literal type
  where present. `NodesWhere` declares a typed population plus attribute read;
  index use is runtime-dependent. `ScalarAttrTriples` is a global population
  read.
- Source inventory wildcard and dynamic-helper classifications remain
  explicit broad or implicit graph reads. External dependencies are retained
  separately. Generic child-walk syntax is not counted as a graph read unless
  its children contain graph-reading Terms.
- `add_edge`/`del_edge` write the literal edge type; `add_node` /
  `add_node_if_absent` write the literal node population and authored
  attributes; `set_attr` / `set_attr_if_different` write the literal key.
  `del_node` is a broad graph write because it removes incident edges and its
  type is not necessarily statically known. Rule-store mutation is recorded
  separately. Any unrecognized effect is preserved and marked unresolved.
- Build a finite-resource directed dependency edge from writer rule to reader
  rule for each shared resource. Separately compute a conservative graph in
  which broad reads connect to all writers and broad writes connect to all
  readers. Keep self-edges and report the chosen convention.

## Gates

1. Input capture, source inventory, and all upstream checks match their stored
   hashes; the three worker exports agree on each definition.
2. Every request-observed UID resolves to a same-request export. The manifest
   covers all distinct request-traced UIDs and all Term variants in their
   exported syntax map to the current source inventory.
3. Typed match edges and all recognized effect resources are extracted. Any
   unsupported effect shape or dynamic resource remains present in an explicit
   unresolved/broad list; do not silently omit it.
4. The weighted access count in the manifest reconciles with the source/trace
   crosswalk's 1,650,456 total.
5. Retain the full per-rule manifest, resource-to-reader/writer maps,
   dependency edges, graph summaries, and all gate outcomes.

## Interpretation boundary

This is a syntactic candidate operation-scope graph. It does not prove that
every Term executed, capture failed matcher attempts, resolve every implicit
helper dependency, estimate finite inference domains, or define a factor
graph. The broad graph is conservative by construction; the finite-resource
graph may omit unknown dependencies. Neither graph establishes a task frame,
partition correctness, or speedup. The two-prompt fixture is not a prevalence
sample.

## Artifacts

- Runner: `scripts/analyze_live_operation_scope_manifest_v1.py`
- Source lock: `evaluation/substrate_capability/live_operation_scope_manifest_v1_lock_20261003.json`
- Machine-readable manifest and analysis: `evaluation/reports/live_operation_scope_manifest_v1_20261003.json`
- Results: `docs/research/engine_substrate/SUBSTRATE_LIVE_OPERATION_SCOPE_MANIFEST_V1_RESULTS_20261003.md`
