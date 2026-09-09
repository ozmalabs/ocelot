# LLM sparsify — fidelity vs compute of the recovered graph — RESULTS

**Block**: 310000. Pre-reg: `LLM_SPARSIFY_PREREG.md`.
Build: `domains/llm_structure_recovery.py` (SparseConfig + FLOP counter);
measure: `scripts/llm_sparsify_measure.py`.

The user: *"what is the computational cost difference?"* **Measured answer:
the faithful recovered graph is ~1× the model (no advantage), and naive
sparsification of it buys almost nothing before the outcomes break. The
orders-of-magnitude savings live in the SPARSE-STRUCTURE operations the graph
exposes, not in pruning a faithful dense forward.** This is an honest negative
that resolves the whole cost thesis precisely.

## The cost of the faithful copy (block 309000, restated)

Same dense arithmetic as the model: ~2·N·T FLOPs/token. Wall-clock CPU fp32,
5-token prompt: torch **192 ms** vs numpy **208 ms** = **~1× (±8%)**. Faithful
recovery has no cost advantage — 100% agreement demands the identical compute.

## Fidelity-vs-compute curve (held-out battery, agreement vs the full graph)

Full-graph matmul FLOPs (battery): 4.7×10⁹ per short prompt.

**[A] FFN top-k neuron gating**
| keep fraction | agreement | FLOP fraction |
|---|---|---|
| 1.00 | 1.00 | 1.00 |
| 0.90 | 1.00 | 0.98 |
| 0.75 | **1.00** | **0.95** |
| 0.50 | 0.83 | 0.91 |
| 0.25 | 0.42 | 0.86 |

**[B] layer skipping (smallest residual delta first)**
| layers skipped | agreement | FLOP fraction |
|---|---|---|
| 0 | 1.00 | 1.00 |
| 2 | **0.00** | 0.93 |
| 4 | 0.00 | 0.87 |
| 8 | 0.00 | 0.73 |

**[C] attention head pruning** — 16→1.00, 14→0.50, 12→0.25, 8→0.00
(FLOP fraction stays ~1.00: the head loop only skips the tiny per-head
attention, not the q/k/v/o projection matmuls — reported honestly).

**[D] combined (ffn 0.75 + skip 4 layers)** — agreement 0.00.

## Verdict — the cost difference, resolved honestly

1. **Faithful recovery = ~1× cost.** No free lunch; 100% agreement = identical
   dense computation.
2. **Naive sparsification of the faithful dense graph buys ~nothing**: the only
   loss-free cut is FFN keep-0.75 = **~5% FLOPs saved at 100% agreement**.
   Beyond that, agreement collapses — layer skipping breaks at the FIRST
   skipped layer (even "small-delta" layers are load-bearing for the final
   token), heads break by 14/16, FFN by keep-0.5.
3. **Therefore the orders-of-magnitude savings measured earlier are NOT from
   pruning a dense copy.** They come from the SPARSE-STRUCTURE operations the
   graph makes explicit and editable — the coherence read (~48 FLOPs) and kNN
   retrieval (block 302/305), which are ~8.5 OoM below a dense forward token.
   The dense transformer computation is genuinely dense; recovering it
   faithfully means paying for it, and the win is in REPLACING dense ops with
   sparse-structure ops, a real (non-free) transformation — not in shaving the
   dense graph.

This is the precise, honest resolution: **the graph-cognition seed's value is
that the computation is now explicit and editable, so you can substitute
sparse-structure operations where fidelity allows — not that the faithful copy
is itself cheaper.**

## Anti-faking / method
- Sparsification really skips arithmetic; the FLOP counter reflects only ops
  performed. Agreement measured on held-out prompts vs the full graph.
- Every knob's degradation reported, including the negatives (layer/head
  pruning break immediately) and the head-pruning FLOP-counter caveat.
- **default == today**: sparsity-off bit-exact; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.

## Honest bounds
- One small model (0.6B), next-token / greedy-argmax agreement, theoretical
  FLOP counting (not kernel-level timing).
- Simple, uncalibrated sparsification (per-token top-k, delta-ranked skipping,
  first-h heads) — proper structured pruning / distillation-aware methods do
  better, but the POINT stands: the faithful dense graph is not cheaply
  pruned, and the OoM wins are elsewhere.
- The head-pruning FLOP counter does not credit the projection matmuls (they
  still run), so head pruning shows ~1× FLOPs — a counter limitation, stated.
