# Structural recovery of an LLM's FFN — statement

**Block**: 320000. This is a STATEMENT of what has been recovered, separate from
any cost claim. Build: `domains/llm_structure_recovery.py`.

## The claim

The feed-forward computation of Qwen3-0.6B is not an opaque 3072-neuron map. It
DECOMPOSES into explicit, recoverable STRUCTURE that reproduces the model's
outcomes on held-out prompts. Recover the structure first; optimising it (making
it cheap) is a separate, downstream axis that the recovered form makes obvious.

## What is recovered (per layer L)

1. **Modes** `modes[L]` — the FFN activation over a corpus is dramatically
   low-rank (block 318: participation ratio 5–24 out of ff=3072). Its structure
   is captured by ~k≈32 SVD modes (right singular vectors of the centred
   activation), an explicit `k × ff` matrix.

2. **Coefficient map** `Wc[L]` — an explicit `k × d` linear map from the layer's
   MLP input to the k mode COEFFICIENTS. The activation is reconstructed as
   `mean[L] + coeffs · modes[L]`. This is the right grain: predict k
   coefficients, not ff neuron activations (blocks 315–317 predicted the ff-dim
   activation and plateaued; block 318 fixed the grain).

3. **Per-position selector** — the active set is a per-TOKEN object (block 319:
   a single fixed set across a sequence caps at 2/1/0; per-position selection
   reaches the per-token oracle 9/6/4). The recovered selector picks each
   position's active set from its own predicted coefficients.

4. **Faithful numpy substrate** — the surrounding forward pass (embed, RMSNorm,
   GQA + QK-norm + RoPE attention, SwiGLU, residual, unembed) is computed from
   the raw weights in pure numpy (the recovered graph of the earlier arc), NOT
   by torch. torch appears only as the reference oracle.

Together `{modes[L], Wc[L], mean[L], per-position selector}` over the numpy
substrate reproduce the model's held-out next-token outcomes.

## Structure first, cost second

- The recovery is the point: the computation is expressible as explicit objects
  (modes, a coefficient map, a per-position selector) that give the same
  outcomes. That is what "the structure is recoverable" means.
- ONCE recovered, the structure tells you where the cheap wins are: predict k≈32
  coefficients (not 3072 activations) and compute only the selected neurons.
  Block 320's cheap inline path realises this and runs below the full FFN in
  counted FLOPs (see `STRUCTURAL_RECOVERY_RESULTS.md`) — but that cheapness is a
  CONSEQUENCE of the recovered structure, not the claim itself.

## Provenance / honesty

- Only the WEIGHTS were copied; the COMPUTATION (modes, coefficients, selection,
  substrate) is the recovered graph's own — not a torch call, not a
  prompt→output lookup.
- All quality claims are on DISJOINT held-out prompts; oracles are explicit
  upper bounds (peek at the true activation).
- `.so` md5 stays `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals
  untouched; models + venv under `/applications`, NOT committed.
