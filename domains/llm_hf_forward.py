"""Block 330000 — a thin HF-forward shim so the extraction arc (327/328/329)
runs against ANY transformers model, including hybrid architectures the numpy
`NumpyQwen3` reader does not support.

The extraction tiers only ever need two things from a model:
  * next-token logits (knowledge elicitation `elicit_isa`),
  * per-layer last-token hidden states (concept `word_vectors` / process
    `statement_vectors`).

For the dense Qwen3-0.6B those came from the pure-numpy `NumpyQwen3` (whose
forward path the mechanism arc 318-326 also uses). For a CURRENT model like
`empero-ai/Qwen3.8-4B-Distill` — a `qwen3_5` HYBRID (linear-attention/SSM +
sparse full-attention, MRoPE, vision tower, MTP head) — there is no numpy
reader (that is Plan B, deferred). But `transformers` runs it, and
`output_hidden_states=True` exposes exactly the per-layer residual-stream
activations the extractors want, REGARDLESS of how attention produced them.

This shim wraps an HF causal-LM and exposes the minimal surface the extractors
call, so `elicit_isa` / `word_vectors` / `statement_vectors` work unchanged:
  * `.forward_logits(token_ids) -> np.ndarray[vocab]`  (last position)
  * `._t(name)` -> the input-embedding matrix (for `word_vectors`'
    single-token embedding path)
  * `hidden_at(token_ids, layer) -> np.ndarray[d]`  (last-token hidden state at
    a layer — the `_ffn_io_all`-style contextual vector the concept/process
    extractors need)

torch/transformers/model are USED HERE (this is the harvest side, offline). This
module never enters a substrate query path and never touches the protected
files or the `.so`.
"""

from __future__ import annotations

import numpy as np


class HFForward:
    """Minimal HF-model wrapper exposing the extraction surface. Loads once;
    all methods are torch-no-grad numpy-out. `layer` indexes into
    `output_hidden_states` (0 = embeddings, 1..n = post-block)."""

    def __init__(self, model_dir, *, dtype="float32", device="cpu"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self._torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        td = {"float32": torch.float32, "bfloat16": torch.bfloat16,
              "float16": torch.float16}.get(dtype, torch.float32)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_dir, dtype=td, low_cpu_mem_usage=True)
        self.model.eval()
        self.device = device
        if device != "cpu":
            self.model.to(device)
        # input-embedding matrix as numpy (for the single-token embed path)
        self._embed = self.model.get_input_embeddings().weight.detach().to(
            torch.float32).cpu().numpy()

    # ---- surface the extractors call ------------------------------------
    def forward_logits(self, token_ids, sparse=None, flop_counter=None):
        """Last-position next-token logits [vocab] as numpy. `sparse`/`flop_
        counter` are accepted for signature-compatibility with NumpyQwen3 and
        ignored (this is the full HF forward)."""
        torch = self._torch
        ids = torch.tensor([list(token_ids)], dtype=torch.long, device=self.device)
        with torch.no_grad():
            out = self.model(input_ids=ids)
        return out.logits[0, -1].detach().to(torch.float32).cpu().numpy()

    def forward_logits_batch(self, batch_token_ids):
        """Last-real-position next-token logits for a BATCH of variable-length
        token-id sequences: returns np.ndarray [B, vocab]. Sequences are
        LEFT-padded to a common length so position -1 is the true final token of
        every row (correct for a causal LM), with an attention_mask zeroing the
        pads. One forward for the whole batch — this is the throughput lever.

        Block 335000: batched elicitation. Read is identical to B calls of
        forward_logits (same last-token logits), just amortized over one forward.
        """
        torch = self._torch
        seqs = [list(t) for t in batch_token_ids]
        if not seqs:
            return np.empty((0, 0), dtype=np.float32)
        pad_id = self.tokenizer.pad_token_id
        if pad_id is None:
            pad_id = self.tokenizer.eos_token_id or 0
        maxlen = max(len(s) for s in seqs)
        B = len(seqs)
        ids = torch.full((B, maxlen), int(pad_id), dtype=torch.long)
        mask = torch.zeros((B, maxlen), dtype=torch.long)
        for i, s in enumerate(seqs):
            L = len(s)
            ids[i, maxlen - L:] = torch.tensor(s, dtype=torch.long)  # LEFT pad
            mask[i, maxlen - L:] = 1
        if self.device != "cpu":
            ids = ids.to(self.device)
            mask = mask.to(self.device)
        with torch.no_grad():
            out = self.model(input_ids=ids, attention_mask=mask)
        # last position is the true final token for every row (left-padded)
        return out.logits[:, -1, :].detach().to(torch.float32).cpu().numpy()

    def hidden_at(self, token_ids, layer):
        """Last-token hidden state at `layer` [d] as numpy — the contextual
        vector the concept/process extractors use (analogous to
        `_ffn_io_all(...)[layer][-1]`)."""
        torch = self._torch
        ids = torch.tensor([list(token_ids)], dtype=torch.long, device=self.device)
        with torch.no_grad():
            out = self.model(input_ids=ids, output_hidden_states=True)
        return out.hidden_states[layer][0, -1].detach().to(torch.float32).cpu().numpy()

    def hidden_all_layers(self, token_ids):
        """Last-token hidden state at EVERY layer: list over layers of [d]."""
        torch = self._torch
        ids = torch.tensor([list(token_ids)], dtype=torch.long, device=self.device)
        with torch.no_grad():
            out = self.model(input_ids=ids, output_hidden_states=True)
        return [h[0, -1].detach().to(torch.float32).cpu().numpy()
                for h in out.hidden_states]

    def _t(self, name):
        """Compatibility shim for the numpy reader's tensor accessor — only the
        input-embedding matrix is needed by the extractors (`word_vectors`)."""
        if name in ("model.embed_tokens.weight", "embed_tokens", "lm_head.weight"):
            return self._embed
        raise KeyError("HFForward exposes only the embedding matrix, not %r" % name)

    @property
    def n_layers(self):
        return int(self.model.config.text_config.num_hidden_layers) \
            if hasattr(self.model.config, "text_config") \
            else int(self.model.config.num_hidden_layers)
