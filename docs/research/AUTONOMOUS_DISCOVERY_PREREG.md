# Autonomous graph-native discovery preregistration

## Claim and scope
This demonstration tests a teacher-free, two-segment, graph-native discovery of one arity-three structural relation. It does **not** claim migration of arbitrary legacy `Concept` attribute/edge records. Semantic input is explicitly reified as `SemanticRelation` graph facts.

## Fixed boundary and policy
The host may only boot/load named seeds, submit raw entity/concept/semantic-relation/observer facts and one `DiscoveryRequest`, run native rules to quiescence, then submit one held-out `OperationRequest` and run native rules again. It may not create `ThoughtSegment`, residual/evidence/witness/candidate/observation/axis nodes; make mint or terminal decisions; choose a per-segment schedule; or provide held-out training evidence. No answerer, LLM, network, or tool callback is allowed.

The fixed graph-resident policy is `max_segments=2`, `mint_after_quanta=2`, `selection=min_traversal_order`, `integer_native=1`, with one requested start concept. The graph, not Python, selects the trajectory. The fixture assigns unique traversal ranks.

## Structural positive
Both training concepts contain exactly the five-tuple `(dimension="rel:binding", relation_head="bind", arg1_role="ITEM", arg2_role="SLOT", quantum=1)`; the setpoint contains none. The held-out operation preserves its four semantic fields while using independent opaque request/display values. The fixture declares one complete bijection for every nonsemantic graph-visible value: concept/setpoint IDs and labels, relation names/IDs, training and held-out request IDs, entity IDs, display values, and the precovered basis key. Only semantic tuple fields, graph topology, and traversal policy are outside that bijection. Canonical signatures are sorted five-tuples and recurrence identity is `ToJsonString(canonical_signature)`. A positive new-axis outcome passes only if the shape-decode ladder reaches exactly one novelty-minted `CapabilityAxis`; exact recognition, transform recognition, dimension inference, precoverage, or any residual cardinality other than one invalidates that positive claim.

## Fixed cases and expected outcomes
No substitution, alternate fixture, relabeling scheme, policy value, or target-axis assertion may be changed after observing any result. Deviations must be reported separately; preregistered outcomes are never overwritten.

| Case | Fixed manipulation | Expected settled result |
|---|---|---|
| `discovered_axis_positive` | `train_a -> train_b`, same binding tuple at both, empty setpoint | 2 evidence, 1 candidate persistence 2, 1 offer, 1 newly minted axis; after held-out submission exactly one `licensed_by` and one `reachable_via` edge |
| `no_residual_no_mint` | setpoint has the exact tuple | 0 evidence/candidates/offers/new axes and no held-out admissibility |
| `label_scramble_structural_transfer` | declared complete bijection over concept/setpoint IDs and labels, relation IDs/names, request IDs, entity IDs, display values, held-out request fields, and other opaque key-like values; preserve only semantic relation fields, topology, and traversal policy | positive counts and held-out licensing invariant under the structural graph projection |
| `label_scramble_no_transfer` | positive-like held-out labels but `arg2_role=GROUP` | no `licensed_by`, `reachable_via`, or `admissible` |
| `relation_head_mismatch_no_transfer` | matching roles, `relation_head=place` | no `licensed_by`, `reachable_via`, or `admissible` |
| `precovered_no_new_axis` | preinstall exact covering `ShapeSignature` | one offer resolves recognized (or documented existing-basis transform), zero episode/candidate new-axis edges, no held-out route through a new axis |
| `same_predicate_different_structure_no_aggregation` | two residual tuple encodings share `bind` but differ in role/quantum | 2 recurrence keys, persistence 1 each, 0 offers/new axes |
| `idempotence_and_seed_reload` | positive fixture, rerun rules and reload seed | filtered graph/counts unchanged; exactly one each of `ad_*`, `mrl_*`, and `mrs_*` rules |

## Falsifiers and audits
Before boot, the loaded manifest closure is scanned for target axis identifiers, expected target key/display string, held-out entity IDs, and a positive-covering `ShapeSignature`. The precovered control is the only allowed exception and records it as such. Tests monkeypatch legacy trajectory/residual/semantic-controller paths and install raising ask/LLM/network/tool callbacks. The adapter instruments every public mutation after seed loading: it permits only fixed raw fixture facts, then only the held-out `OperationRequest`, while prohibited derived node types and every post-submission mint/status mutation raise and are recorded. Audit telemetry is live (not reconstructed): it must show one raw discovery submission, zero prohibited adapter writes, and zero callback invocations on a normal run; dedicated controls invoke each raising external stub and each prohibited-write path to prove the counters and failure boundary. The fixture's complete declared opaque-label domain is checked as a bijection, and the ordinary and scrambled runs must have identical structural graph projections after labels/identifiers are erased.

## Required artifacts
For every case, the runner writes `results/autonomous_discovery/<case>/seed_manifest.json`, `initial_graph.json`, `settled_graph.json`, `rerun_graph.json`, `adapter_audit.json`, `rule_inventory.json`, and `assertions.json`. This preregistration contains no observed results; results are recorded only in generated artifacts after execution.
