# Knowledge extraction as a CAN graph seed — RESULTS

**Block**: 327000. Pre-reg: `KNOWLEDGE_SEED_PREREG.md`.
Build: `domains/llm_knowledge_seed.py`; measure:
`scripts/llm_knowledge_seed_measure.py`. Substrate: protected
`can_native_bp.py` / `seeds/can_native_reimplementation.json` (read-only,
built-to).

**POSITIVE. The LLM's relational knowledge, elicited offline and seeded into a
native CAN Microtheory, lets the substrate DERIVE held-out entailment it was
never told — transitive-closure facts at distance ≥ 2 — by its own graph
traversal, with NO LLM at query time. It passes both anti-faking controls
decisively: a direct-edge lookup cannot answer the multi-hop entailments, and a
shuffled graph collapses them. Knowledge is extractable as a working graph seed
for the substrate's own cognition.**

## Result (held-out entailment; NO LLM at query time; chance = 0.50)

18 is-a edges extracted from Qwen3-0.6B; held-out = 7 transitive-closure
positives at distance ≥ 2 (NOT elicited: poodle→animal, oak→plant, copper→
material, …) + 7 random non-reachable negatives.

| query mode | accuracy | positives (yes) | negatives (no) |
|---|---|---|---|
| **SUBSTRATE transitive** | **1.00** | 7/7 | 7/7 |
| direct-edge baseline | 0.50 | 0/7 | 7/7 |
| shuffled-graph control | 0.57 | 1/7 | 7/7 |

## Claim 1 — extractable and seedable: HOLDS

Constrained next-token is-a elicitation over a multi-level taxonomy yielded 18
non-self-loop edges (the 0.6B model's actual, noisy assertions), which build a
native CAN Microtheory (Concept node per entity, `causal_influence` edge per
is-a link) via `build_knowledge_mt` on the reimplementation grammar. No new node
or edge types minted.

## Claim 2 — answers held-out entailment by substrate ops: HOLDS

The substrate's own graph traversal (`query_transitive`, BFS over the seeded
edges) answers all 7 held-out ≥ 2-hop entailments correctly and rejects all 7
negatives — accuracy 1.00 — with NO LLM in the loop. The substrate derives what
the extracted edges ENTAIL, not just what was stored.

## Claim 3 — derives, not stores: HOLDS (both controls)

- **Direct-edge baseline: 0.50 (0/7 positives).** Lookup-only cannot answer a
  single ≥ 2-hop entailment — they are not stored edges. So the substrate
  traversal is adding REAL multi-hop inference, not retrieving stored answers.
- **Shuffled-graph control: 0.57 (1/7 positives).** Permuting the edge targets
  (same nodes, scrambled relations) collapses entailment to near-chance — so it
  is the RELATIONAL STRUCTURE, not the node set or a memorised list, that
  carries the inference. Not a lookup table in a graph costume.

## Verdict

Tier 1 of the extraction direction succeeds cleanly: an LLM's relational
knowledge can be lifted into a native CAN graph seed, and the substrate then
does its OWN cognition over it — deriving entailments the seed was never told,
by graph traversal, with the LLM entirely out of the query loop. This is the
"graph cognition seed" payoff for knowledge, and it establishes the
extract → seed → substrate-query → held-out-entailment pipeline that the harder
tiers (concepts, processes) will reuse.

## Anti-faking / method

- Held-out entailments are the transitive closure at distance ≥ 2 — derived, not
  elicited; disjoint from the seed edges.
- Query time is PURE SUBSTRATE; the LLM only elicited adjacent edges, offline.
- Two controls (direct-edge lookup 0.50, shuffled-graph 0.57) bound the result
  against a lookup table and against node-set-only effects.
- The seed is built from what the LLM ACTUALLY asserts (noisy), with self-loops
  dropped (a self-edge is not a fact); the entailment ground truth is the
  closure of THAT extracted graph.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals + seed grammar untouched; models + venv under
  `/applications`, NOT committed.

## Honest bounds and next tiers

- One small model (0.6B), is-a relation only, small held-out (7 + 7). The 0.6B
  model's noisy elicitation (chain-skips, self-loops) collapsed the taxonomy to
  18 edges and 7 reachable ≥ 2-hop positives — so the N is small; the
  load-bearing claims are the qualitative separation (transitive 1.00 vs direct
  0.50 vs shuffle 0.57), not a large-sample rate.
- The pipeline generalises to other relations (capital-of, part-of, opposite-of)
  and richer graphs; that is a scale-up, not a new mechanism.
- NEXT TIERS: CONCEPTS (extract a concept's identity so it composes in a NEW
  Microtheory it never co-occurred with — concept transfer) and PROCESSES
  (extract a procedure as graph dynamics — a rewrite/transport — and apply it to
  unseen inputs). Both reuse this block's extract → seed → substrate-query →
  held-out harness; the anti-faking bar rises from held-out ENTAILMENT to
  held-out TRANSFER and held-out APPLICATION respectively.
