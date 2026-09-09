# LLM sparsify — fidelity vs compute of the recovered graph — PREREG

**Block**: 310000

**Task**: The user — *"what is the computational cost difference?"* (of the
recovered Qwen3-0.6B graph, block 309000). Rather than assert, measure it: the
faithful graph costs ~1× the model; this rung sweeps sparsifications of that
graph and measures the fidelity-vs-compute tradeoff — how much compute can be
cut before the outcomes diverge.

## 1. The honest starting point (already measured)

The faithful recovered graph does the SAME dense arithmetic as the model:
- ~2·N·T FLOPs/token (N ≈ 596M params). Measured wall-clock (block 309000,
  CPU fp32, 5-token prompt): torch 192 ms vs numpy 208 ms — **~1× (±8%)**.
- Faithful recovery has NO cost advantage, and that is expected: 100%
  agreement requires the identical computation. The cost question is what the
  explicit graph now lets us CUT.

## 2. What is swept (real arithmetic skipped)

`domains/llm_structure_recovery.SparseConfig` — each knob actually skips ops,
and a FLOP counter reports the real reduction:
- **FFN top-k neuron gating** — keep only the top fraction of FFN hidden
  neurons per token (by |silu(gate)·up|); skip the rest of down_proj.
- **layer skipping** — drop whole layer blocks (residual passes through),
  chosen by smallest per-layer residual delta (the block-307 finding).
- **attention head pruning** — keep fewer heads per layer.

Agreement is measured against the FULL recovered graph (itself 100% vs torch),
isolating the sparsification effect. HELD-OUT prompt battery (block 309000's).

## 3. Falsifiable claims

1. **Sparsity-off is bit-exact** (default==today for the recovered forward).
2. **Each knob really cuts FLOPs** (the counter drops below 1.0).
3. **Fidelity-vs-compute is a measurable curve**: agreement degrades as
   compute is cut, and there is (or is not) a regime with meaningful FLOP
   savings at ~100% agreement. The registered expectation (from the task-1
   probe) is that naive pruning of a faithful DENSE small model degrades
   next-token FAST — i.e. large savings are NOT available from brute pruning;
   reported honestly whichever way it falls.

## 4. What the answer will mean

- If big FLOP cuts hold agreement → the recovered graph is cheaply
  sparsifiable and the cost advantage is realisable by pruning.
- If agreement breaks quickly (expected) → the dense computation is genuinely
  dense; the ~8.5-OoM savings measured in earlier rungs (block 302/305:
  coherence read ~48 FLOPs, kNN retrieval) come from the SPARSE-STRUCTURE
  operations the graph EXPOSES, NOT from brute-pruning a faithful dense
  forward. This is the honest resolution of "what is the cost difference":
  faithful copy ≈ 1×; the OoM wins live in the sparse-structure ops, and
  turning the dense graph into those is a real (not free) transformation.

## 5. Anti-faking / bounds

- Sparsification SKIPS arithmetic (real FLOP cut), not a simulated mask over a
  full compute; the counter reflects only the ops performed.
- Agreement on HELD-OUT prompts; degradation reported, not hidden.
- **default == today**: sparsity-off bit-exact; substrate `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched; models + venv under `/applications`, NOT committed.
- Bounds: one small model, next-token / greedy-argmax agreement, theoretical
  FLOP counting (not kernel-level timing); the head-pruning FLOP counter does
  not credit the projection matmuls (they still run), so head pruning shows ~1×
  FLOPs — reported as such.
