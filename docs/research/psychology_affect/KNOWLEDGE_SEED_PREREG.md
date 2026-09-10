# Knowledge extraction as a CAN graph seed — PRE-REG

**Block**: 327000. Build target: `domains/llm_knowledge_seed.py`; measure:
`scripts/llm_knowledge_seed_measure.py`. Substrate BP / grammar are PROTECTED
(`can_native_bp.py`, `seeds/can_native_reimplementation.json`), read-only —
built TO.

## Motivation

Blocks 318–326 asked whether the LLM's MECHANISM can be re-expressed on the CAN
substrate (aperture-covariance of modes/transports). This block opens a
different direction: extract the LLM's CONTENT — what it knows — as native CAN
graph seeds the substrate can use for its OWN cognition. Three tiers, increasing
difficulty: KNOWLEDGE (relational facts), CONCEPTS, PROCESSES. This block is
tier 1, KNOWLEDGE, and establishes the extract → seed → substrate-query →
held-out-entailment pipeline the harder tiers reuse.

## Claims (falsifiable)

**Claim 1 — knowledge is extractable and seedable.** Relational facts (is-a
links) elicited from the LLM build a native CAN Microtheory (Concept nodes +
typed edges, the same grammar as the reimplementation seed). (Infrastructure.)

**Claim 2 — the seed answers held-out ENTAILMENT by substrate ops alone.** For
transitive-closure pairs at distance ≥ 2 that were NOT elicited, the substrate's
own graph traversal answers correctly (positives reachable, negatives not), with
NO LLM at query time. Prediction: substrate-transitive accuracy well above
chance. FALSIFIED IF it is at chance (the seed cannot derive entailment).

**Claim 3 — it DERIVES, not stores (anti-lookup).** The result must beat two
controls: (a) a DIRECT-EDGE baseline that answers only from stored edges must
FAIL the ≥ 2-hop entailments (they are not stored) — showing traversal adds real
inference; (b) a SHUFFLED-GRAPH control (edge targets permuted) must COLLAPSE
entailment — showing the relational STRUCTURE, not the node set, carries it.
FALSIFIED IF direct-edge already matches transitive (it is a lookup table) or
shuffle does not collapse (the structure is irrelevant).

## Method

- ELICIT (model venv, offline): constrained next-token is-a elicitation over a
  multi-level taxonomy; the LLM is the elicitation ORACLE only. Drop self-loops
  (a self-edge is not a relational fact). The extracted edges are whatever the
  LLM actually asserts — noisy 0.6B knowledge included.
- SPLIT: elicitation edges (seed) vs held-out ENTAILMENT = the transitive
  closure of the EXTRACTED graph at distance ≥ 2 (not directly elicited) +
  random non-reachable negatives.
- SEED (substrate, tree python3): `build_knowledge_mt` — Concept node per
  entity, directed `causal_influence` edge per relation.
- QUERY (substrate only): `query_transitive` (BFS traversal) vs `query_direct`
  (stored-edge lookup) vs shuffled-graph. Entailment accuracy = (positives
  answered yes + negatives answered no) / total.

## Anti-faking

- Held-out entailments are the transitive closure at distance ≥ 2 — DERIVED, not
  elicited; disjoint from the seed edges.
- Query time is PURE SUBSTRATE — no LLM in the loop (the LLM only elicited the
  adjacent edges, offline).
- Two controls (direct-edge lookup, shuffled-graph) distinguish real graph
  inference from a lookup table in a graph costume.
- The seed is built from what the LLM ACTUALLY asserts (noisy), and the
  entailment ground truth is the closure of THAT extracted graph — not an
  idealised taxonomy.
- **default == today**: `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`;
  protected CAN internals + seed grammar untouched (read-only, built-to);
  models + venv under `/applications`, NOT committed.
