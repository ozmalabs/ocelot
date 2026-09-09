# LLM coactivation shape — does the conditional graph close the gap? — RESULTS

**Block**: 313000. Pre-reg: `LLM_COACTIVATION_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (`fit_coactivation_graph`,
`coactivation_retrieve`); measure: `scripts/llm_coactivation_measure.py`.

Built the coactivation graph over the FFN memory dictionary and tested
query-conditional retrieval against it. **Verdict: HONEST NEGATIVE for the
deployable path — coactivation seed-and-expand does NOT close the order-2 →
oracle gap — WITH a mechanism positive: given a good seed, the graph DOES add
query-conditional information. The bottleneck is the SEED (a cheap accurate
query→memory index), not the graph.**

## Measured (Qwen3-0.6B, 20 train / 10 held-out, agreement vs full graph)

**Main — retrieval at matched target fraction:**

| target | coactivation (gate-key seed + graph) | order-2 static | order-1 | oracle |
|---|---|---|---|---|
| 0.60 | 3 | 4 | 4 | 8 |
| 0.50 | 1 | 2 | 1 | 8 |
| 0.40 | 0 | 1 | 0 | 5 |

**Diagnostic — good (true-activation) seed 0.15 → target 0.5:**
- true-seed + GRAPH expand: **3/10**
- true-seed + naive top-up: **2/10**

### Claim 2 — coactivation closes the gap: FAILS
Coactivation seed-and-expand (seeded by the cheap gate-key) does NOT beat the
static order-2 mask (3 vs 4, 1 vs 2, 0 vs 1) and is FAR below the per-query
oracle (which holds 8/10 even at target 0.5). Reported as a failure. The
oracle gap is huge and stable: the RIGHT neurons are per-query-selectable by
true activation, but no cheap ensemble descriptor here recovers them.

### Claim 3 — the graph carries conditional info given a good seed: HOLDS
With a good (true-activation) seed, graph expansion (3/10) beats naive top-up
(2/10). So the coactivation graph DOES carry query-conditional shape — the
co-firing partners of the right seed neurons are the right neurons to add. The
graph is not the problem.

## Diagnosis — the bottleneck is the SEED, not the graph

The two results together localise the failure precisely:
- A weak seed (gate-key, the order-1 signal already shown poor in block 311)
  cannot be rescued by graph expansion — you expand from the wrong starting
  memories.
- But given a good seed, the graph helps.

So the missing piece is a **cheap, accurate query→memory index** — a way to
pick the right SEED memories for a held-out query without computing the full
activation. The coactivation graph is a valid conditional-shape structure; it
just needs a good entry point. This refines the arc's open question exactly:
the true shape is per-query-conditional (oracle proves it recoverable), the
coactivation graph captures the conditional co-firing structure (diagnostic
proves it), and what remains open is the cheap seed — the query→memory
retrieval key — which a single gate-key direction does not provide (block 311's
finding, now confirmed as the binding constraint).

## Verdict on the framing

The user's "true shape over multiple queries" holds as a structural claim —
the coactivation graph is a real query-conditional shape and adds information
given a good seed. But turning it into a CHEAP shape-native FFN is blocked on
the seed: a good query→memory index is the un-recovered piece. This is the
honest state — the shape is there and graph-shaped; cheap conditional access to
it is the open problem, and it is NOT the graph, it is the entry key.

## Anti-faking / method
- Graph FIT on train corpus, retrieval EVALUATED on DISJOINT held-out (not
  per-query memorisation). Oracle is an explicit per-query upper bound.
- Every fraction reported, including the negative main result.
- **default == today**: `order2_shape=None` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), small batteries, uncalibrated fracs; tests ONE
  conditional-retrieval design (gate-key seed + co-firing expansion). The
  negative bounds THIS design, not every coactivation-based selector.
- Named next: a learned/derived cheap query→memory index for the seed (e.g.
  the joint gate+up key from block 311, or a low-rank router), then re-test the
  graph expansion on top of it.
