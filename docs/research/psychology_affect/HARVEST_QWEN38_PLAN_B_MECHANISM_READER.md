# Plan B (deferred) — a `qwen3_5` mechanism reader for Qwen3.8-27B

**Status:** SAVED, NOT STARTED. Plan A (extraction-only harvest into Jabberwock
as a trust-weighted source) proceeds first. This document scopes the larger,
separate effort Plan B would be, so it can be picked up later without
re-discovery.

## Why Plan B is a separate arc

The mechanism-recovery arc (blocks 318–326: mode-grain recovery, per-position
retrieval, structural recovery, native-graph aperture, transport chain) all runs
on `domains/llm_structure_recovery.py::NumpyQwen3` — a pure-numpy forward pass
built for the DENSE-ATTENTION Qwen3 (the 0.6B: GQA + QK-norm + RoPE + SwiGLU +
RMSNorm, `tie_word_embeddings`).

`Qwen3.8-27B` (`/applications/data/model_graph_work/Qwen3.8-27B`, 52 GB, 18
shards) is a DIFFERENT architecture — `model_type: qwen3_5`
(`Qwen3_5ForConditionalGeneration`), verified from its `config.json`:

- **Hybrid attention:** 64 layers, `layer_types` is mostly `linear_attention`
  (Mamba/SSM-style) with `full_attention` every 4th layer
  (`full_attention_interval: 4`). The numpy reader implements ONLY dense
  softmax attention — it has no linear-attention/SSM path.
- **Linear-attention params** the reader does not model: `linear_conv_kernel_dim
  4`, `linear_key_head_dim 128`, `linear_num_key_heads 16`,
  `linear_num_value_heads 48`, `linear_value_head_dim 128`,
  `mamba_ssm_dtype float32`, `output_gate_type swish`, `attn_output_gate true`.
- **MRoPE, not RoPE:** `rope_parameters.mrope_interleaved: true`,
  `mrope_section [11,11,10]`, `partial_rotary_factor 0.25`,
  `rope_theta 1e7`. The reader does full RoPE at θ=1e6.
- **Multimodal:** a `vision_config` (a ViT tower, `deepstack_visual_indexes`,
  image/video token ids). Irrelevant to text-mode mechanism recovery but present
  in the checkpoint and the forward graph.
- **Shapes:** `hidden_size 5120`, `intermediate_size 17408`, `head_dim 256`,
  `num_attention_heads 24`, `num_key_value_heads 4`, `vocab_size 248320`,
  `tie_word_embeddings false` (a separate `lm_head`), `mtp_num_hidden_layers 1`
  (a multi-token-prediction head).

None of these are supported by `NumpyQwen3`. So the mechanism arc cannot touch
the 27B until a `qwen3_5` reader exists.

## Hard constraints Plan B inherits

- **`.so` md5 frozen `7efe75eba05b006cafd15dbb4b7da246`; seed+python only, no
  Rust.** The new reader is pure numpy in `domains/` (a sibling of
  `NumpyQwen3`), never touching the protected files (`can_ops.rs`,
  `can_junction_tree.py`, `can_native_bp.py`, `model_reader.py`).
- **6 GB GPU vs 52 GB bf16 model.** A numpy forward pass runs on CPU and streams
  weights per-layer from the 18 safetensors shards (never all resident). Slow;
  size the batteries accordingly (the mechanism measures use ~40–70 prompts).
- Models/venv under `/applications` never committed.

## Scope — what a `qwen3_5` numpy reader must implement

1. **Shard-streaming weight access.** `model.safetensors.index.json` maps
   tensors → shard files; load per-layer tensors lazily (the 0.6B reader holds
   one file; the 27B must stream 18). A weight-name resolver + LRU over shards.

2. **Linear-attention (SSM) layer.** The load-bearing new primitive. Implement
   the qwen3_5 linear-attention block in numpy: the short causal conv
   (`linear_conv_kernel_dim 4`), the gated linear-attention / state-space recur
   over `linear_num_{key,value}_heads` with `linear_{key,value}_head_dim`, the
   `output_gate_type swish` output gate, `attn_output_gate`. Ground the exact
   recurrence against the `transformers` `qwen3_5` modelling source (read it,
   mirror it in numpy) — this is where the effort is, and where correctness must
   be gated hardest (per-layer hidden-state agreement vs the HF forward).

3. **Full-attention layer at the interval.** Reuse the dense GQA path (the 0.6B
   reader already has it) but with `head_dim 256`, `num_kv_heads 4`, and MRoPE.

4. **MRoPE with partial rotary.** `mrope_interleaved`, `mrope_section [11,11,10]`,
   `partial_rotary_factor 0.25` (only 25% of head dims rotated). Text-only mode
   collapses the three mrope sections to the text position, but the partial-
   rotary interleave must match exactly.

5. **SwiGLU MLP + RMSNorm** at the 27B shapes (already in the 0.6B reader; just
   re-parameterise). Separate `lm_head` (no tying). Ignore the MTP head and the
   vision tower for text mechanism recovery (document the omission).

6. **Correctness gate (non-negotiable, the anti-faking bar).** Before ANY
   mechanism measure: assert the numpy reader's next-token logits match the HF
   `transformers` forward (argmax agreement + top-k overlap) on a held-out prompt
   battery, per the block-307/308 oracle discipline. A reader that does not
   reproduce the reference is not a recovery of anything.

## Then: re-run the mechanism arc on the 27B

Once the reader passes the correctness gate, the existing measures apply almost
unchanged (they call `forward_logits` / `_ffn_io` / `_ffn_io_all`):

- **318 mode-grain:** effective-rank diagnostic + mode router at the 27B's
  `intermediate_size 17408` (participation-ratio prediction: still ≪ ff, likely
  a few dozen modes — a scaling check of the wrong-grain finding).
- **319 per-position retrieval, 320 structural recovery + cheap inline path.**
- **321–323 native-graph aperture** (within-layer incidence covariance): does the
  27B's cleaner representation lift covariance above the 0.6B's 0.88?
- **324–326 between-layer transport + multi-hop chain:** the transport aperture
  across the 27B's 64 layers — but NOTE the hybrid architecture changes the
  between-layer object (linear-attention layers carry a recurrent STATE, not just
  a residual-stream config), so the transport reading may differ qualitatively
  from the dense 0.6B. That is itself a finding worth the arc.

## Honest cost estimate

The linear-attention/SSM numpy implementation + shard streaming + MRoPE +
correctness gate is the bulk — comparable to the original `NumpyQwen3` build,
because it is a second architecture from scratch. Budget it as its own multi-block
arc (reader bring-up + correctness gate as one block; each mechanism re-run as
follow-ons), NOT a rider on the harvest. The payoff is scaling the native-graph
mechanism findings to a frontier-class hybrid model and testing whether the
transport aperture survives the linear-attention state — a real, open question.

## Decision record

Chosen now: **Plan A** (extraction-only harvest — knowledge/concepts/processes
into Jabberwock as a trust-weighted `qwen3` source via the HF forward path, no
numpy reader needed). Plan B deferred to this document. The two are independent:
A delivers the content-capability payoff for the entity; B scales the mechanism
arc and can be picked up whenever the reader effort is warranted.
