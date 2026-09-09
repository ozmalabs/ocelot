# LLM structure recovery — Qwen3-0.6B as a graph — PREREG

**Block**: 309000

**Task**: The user — *"if we can take Qwen3-0.6B and recover the actual
structure to the point where the same prompts give the same outcomes, we can
prove that the structure is recoverable and make an LLM into a graph-cognition
seed, which is huge."*

This registers that proof: recover Qwen3-0.6B's structure into an EXPLICIT
computation GRAPH whose own evaluation gives the SAME OUTCOMES as the model on
held-out prompts.

## 1. What would actually prove it (and what would be a cheat)

- **Cheat (memorisation)**: store prompt→output pairs and replay. Proves
  nothing. Explicitly excluded — there is NO lookup table.
- **Cheat (torch)**: call the model and claim recovery. The forward path must
  NOT use torch/transformers — those appear ONLY as the reference ORACLE to
  check against.
- **The real proof (faithful reimplementation)**: reconstruct the forward pass
  as an explicit dataflow GRAPH — every op (embed, RMSNorm, GQA attention with
  QK-norm + RoPE, SwiGLU MLP, residual stream, final norm, unembed) — computed
  in pure numpy FROM THE RAW WEIGHTS, and verify its next-token prediction
  MATCHES the reference model on HELD-OUT prompts. Only the WEIGHTS are copied;
  the COMPUTATION is the graph's own. Agreement on held-out prompts = the
  structure genuinely transferred.

## 2. Method

`domains/llm_structure_recovery.py`:
- `NumpyQwen3` — the forward pass in pure numpy, reading `model.safetensors`
  directly (via `domains.model_reader`). float32. No torch.
- `DataflowGraph` — the forward recorded as an explicit op-DAG (`GraphNode`:
  id, op, inputs, attrs; edges = data dependencies), evaluated by a small
  pure-numpy op-table interpreter. This is the LLM expressed LITERALLY as a
  graph (~369 nodes for the 28-layer 0.6B), glass-box and inspectable.

Reference oracle: `transformers` `AutoModelForCausalLM` in fp32 (external venv,
block 307-308) — used ONLY to produce the ground-truth logits to compare.

## 3. Falsifiable claims

1. **Faithful forward**: the numpy `NumpyQwen3` forward's full logit vector
   matches the reference model (correlation ≈ 1.0, same argmax) on the gate
   prompts. (Confirmed: corr 1.0000 on 3 prompts.)
2. **Graph == direct**: the `DataflowGraph` evaluation is BIT-EXACT to the
   direct numpy forward (max|diff| = 0) — the graph representation loses
   nothing.
3. **Held-out agreement**: on a HELD-OUT prompt battery (distinct from the gate
   prompts, never inspected during construction), the recovered graph's
   next-token prediction matches the reference model at (near) 100%, with
   top-5 overlap ≈ 1.0 and logit correlation ≈ 1.0. This is the transfer test:
   same outcomes on unseen inputs = structure recovered.

Reported with measured outcomes; any mismatch reported, not hidden.

## 4. Anti-faking bars

- **No torch in the recovered graph**: the entire forward path is numpy from
  the raw weights; torch is only the oracle. (A grep-style audit: the graph
  eval imports no torch.)
- **No lookup table**: the graph computes logits from weights per prompt; there
  is no stored prompt→answer map.
- **Held-out prompts**: agreement measured on prompts NOT used while building —
  guards against accidental special-casing (though since only weights are
  copied, not fitted, the main risk is arch error, which held-out agreement
  also catches).
- **default == today**: a NEW module + script + docs; the substrate `.so` md5
  stays `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched. Model weights + venv under `/applications`, NOT committed.

## 5. What this proves — and its honest scope

- **Proves**: an LLM's structure is fully recoverable into an explicit,
  inspectable, editable dataflow GRAPH that reproduces its outcomes exactly.
  The knowledge AND the computation are now graph-native artifacts, not opaque
  weights — a graph-cognition SEED.
- **Does NOT (yet) claim**: that this runs on the CAN substrate's own field
  dynamics. It is a faithful numeric reimplementation as a dataflow-graph
  interpreter (pure numpy, substrate-side, glass-box) — the FOUNDATION for
  wiring the recovered ops into substrate primitives, not that wiring itself.
  Stated plainly so the claim is not overread.
- **Scope**: one small model (0.6B), next-token prediction, greedy argmax
  agreement. A demonstration of recoverability, not a production graph engine.
