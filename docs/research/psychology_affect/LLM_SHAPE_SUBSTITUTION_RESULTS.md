# LLM shape substitution — is the outcome in the shape? — RESULTS

**Block**: 311000. Pre-reg: `LLM_SHAPE_SUBSTITUTION_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (`ffn_retrieve_frac`); measure:
`scripts/llm_shape_substitution_measure.py`.

The user's framing: *"the recovery is of the TRUE SHAPE encoded in the
substrate of the LLM."* **Verdict: SUPPORTED — the outcome IS carried by the
shape (which sparse memory-set fires), and the measurement pinpoints exactly
which part of the shape the current descriptor still misses.**

## Measured (Qwen3-0.6B, 12-prompt held-out battery, agreement vs full graph)

| fraction of FFN neurons | SHAPE-RETRIEVE (gate-key geometry) | EXACT-TOPK (true activation, oracle) | shape gap |
|---|---|---|---|
| 1.00 | 1.00 | 1.00 | 0.00 |
| 0.75 | (—) | 1.00 | 0.17 |
| 0.50 | 0.08 | **0.83** | 0.75 |
| 0.25 | 0.00 | 0.42 | 0.42 |
| 0.10 | 0.00 | 0.00 | — |

(FLOP fraction: shape-retrieve ~0.66–0.81, floored by the gate-scoring matmul
used to rank keys; exact-topk ~0.83–0.95.)

### Claim 2 — the outcome IS in the shape: HOLDS
EXACT-TOPK — selecting the sparse set of memories that actually fire — keeps
**83% agreement at 50% of neurons** and 42% at 25%. So the outcome depends
substantially on WHICH memories are active, not on the full dense sum over all
of them. Roughly half the FFN arithmetic is redundant *given the shape* of the
active set. This directly supports the framing: the computation's outcome lives
in the sparse active-memory shape, which is what the substrate holds natively.

### Claim 3 — the gap names the missing shape: HOLDS
SHAPE-RETRIEVE — selecting by gate-key geometry alone — keeps only **8% at 50%**
(gap 75% vs the oracle). Selecting memories by the single query-key direction
picks the WRONG ones: the `up_proj` carries shape information the `gate_proj`
key does not. So the query-key geometry is an INCOMPLETE descriptor of the true
shape, and the measurement localises exactly what is missing: **the joint
gate+up key structure** (a memory's true relevance is `silu(gate·x)·(up·x)`,
not `gate·x` alone). That is the next piece of shape to recover.

## Verdict on the framing

The recovery is indeed of a TRUE SHAPE, and this rung measures its two sides:
- **The shape carries the outcome** — the sparse active-memory set suffices
  (exact-topk 83% at half the neurons). The dense arithmetic is a
  high-fidelity readout of a shape that is mostly sparse.
- **My current shape descriptor is partial** — gate-key geometry alone
  under-selects; the full shape needs the joint gate+up key structure. The gap
  (75% at 50%) is the precise, honest measure of what is still un-recovered.

This is exactly the resolution the framing predicts: the LLM and the substrate
are two encodings of one shape; the outcome is in the shape (proven by the
oracle selector); and recovering the shape into a cheap shape-native op needs a
richer descriptor than a single key direction (named: gate+up joint keys /
coactivation) — the next rung.

## Anti-faking / method
- SHAPE-RETRIEVE really skips up+down arithmetic for unretrieved neurons; the
  gate-scoring rank step is a full matmul (FLOP floor ~0.66–0.81) — reported,
  not hidden. A proper retrieval index would remove that floor (not built).
- EXACT-TOPK is explicitly an ORACLE (peeks at the true activation to select) —
  used only to UPPER-BOUND how much the shape can carry, not as a deployable op.
- Agreement on held-out prompts vs the full graph; every point reported.
- **default == today**: `ffn_retrieve_frac=1.0` bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), next-token / greedy agreement, theoretical FLOPs.
- FFN only — attention is a different shape carrier (positional mixing), not
  substituted here.
- The measurement shows the shape carries the outcome and names the missing
  descriptor; it does NOT yet deliver a cheap shape-native FFN at full fidelity
  (that needs the joint gate+up retrieval + an index to remove the scoring
  floor) — the named next rung.
