"""Extract the BETWEEN-LAYER change — a transformer's actual FUNCTION.

The user: *"the extraction should possibly focus on the between-layer change"*
and *"get torch/transformers"*. The static embedding geometry (blocks 304-306)
is what the model KNOWS; the between-layer transformation of the residual
stream is what the model DOES. This module extracts that, with REAL forward
passes (torch + transformers, GPU), not a weights-only approximation.

See docs/research/psychology_affect/BETWEEN_LAYER_EXTRACTION_PREREG.md.

WHAT IT MEASURES:
  * forward_trace(prompt) — the residual stream h_L at every layer + the
    per-layer DELTA magnitude ||h_{L+1} - h_L|| (the change each layer writes).
  * logit_lens(...) — each layer's residual projected through the unembed:
    the token distribution AS IT IS BEING BUILT across depth (nostalgebraist's
    logit lens). Watching the answer token climb to the top across layers IS
    the between-layer function made visible.
  * layer_writes(prompt, concept) — the projection of each layer's delta onto
    a concept direction: WHICH layers write a given concept.

EXTERNAL TOOLING BOUNDARY: torch/transformers are an EXTERNAL venv
(/applications/data/model_graph_work/venv), NOT linked into the substrate. This
module imports them LAZILY, so importing it (or the rest of `domains`) does not
require torch — the substrate import surface is unchanged. The substrate `.so`
is untouched.
"""

from __future__ import annotations

from dataclasses import dataclass


def _torch():
    import torch  # lazy — only when actually running a model
    return torch


def have_torch() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except Exception:
        return False


@dataclass
class TracedModel:
    model: object
    tok: object
    device: str
    n_layers: int
    unembed: object          # (vocab, dim) output projection (lm_head / tied)


def load_traced(model_dir: str, *, device: str = "cuda",
                dtype: str = "float16") -> TracedModel:
    """Load a HF causal LM with hidden-state output enabled."""
    torch = _torch()
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_dir)
    dt = getattr(torch, dtype)
    dev = device if torch.cuda.is_available() and device == "cuda" else "cpu"
    model = AutoModelForCausalLM.from_pretrained(
        model_dir, dtype=dt, output_hidden_states=True).to(dev).eval()
    nl = model.config.num_hidden_layers if hasattr(model.config, "num_hidden_layers") \
        else model.config.get_text_config().num_hidden_layers
    # output embedding (unembed) — tied or separate
    W = model.get_output_embeddings().weight.detach()
    return TracedModel(model=model, tok=tok, device=dev, n_layers=nl, unembed=W)


def forward_trace(tm: TracedModel, prompt: str):
    """Run one forward pass. Returns {'hidden': [h_L ...], 'deltas': [||Δ||...],
    'ids': token_ids, 'tokens': token_strings} — deltas at the LAST token
    position (the position that predicts the next token)."""
    torch = _torch()
    enc = tm.tok(prompt, return_tensors="pt").to(tm.device)
    with torch.no_grad():
        out = tm.model(**enc)
    hs = out.hidden_states                       # tuple len n_layers+1
    last = -1
    deltas = [float((hs[i + 1][0, last] - hs[i][0, last]).norm())
              for i in range(len(hs) - 1)]
    ids = enc["input_ids"][0].tolist()
    return {"hidden": hs, "deltas": deltas, "ids": ids,
            "tokens": tm.tok.convert_ids_to_tokens(ids)}


def logit_lens(tm: TracedModel, hidden, *, position: int = -1, top: int = 5):
    """Project each layer's residual (at `position`) through the unembed and
    return the per-layer top-token strings + the full rank of every vocab item
    is not returned (only the top). This is the token distribution AS BUILT
    across depth. Returns [(layer_index, [top_tokens])]."""
    torch = _torch()
    W = tm.unembed                                # (vocab, dim)
    out = []
    for L, h in enumerate(hidden):
        v = h[0, position].to(W.dtype)
        logits = torch.matmul(W, v)               # (vocab,)
        topk = torch.topk(logits, top).indices.tolist()
        out.append((L, tm.tok.convert_ids_to_tokens(topk)))
    return out


def answer_rank_by_layer(tm: TracedModel, hidden, answer_token_id: int,
                         *, position: int = -1):
    """Rank of `answer_token_id` in each layer's logit-lens distribution
    (0 = top). Shows WHERE across depth the answer becomes the prediction —
    the between-layer function localised. Returns [rank per layer]."""
    torch = _torch()
    W = tm.unembed
    ranks = []
    for h in hidden:
        v = h[0, position].to(W.dtype)
        logits = torch.matmul(W, v)
        order = torch.argsort(logits, descending=True)
        rank = int((order == answer_token_id).nonzero()[0, 0])
        ranks.append(rank)
    return ranks


def layer_writes(tm: TracedModel, prompt: str, concept_vec, *, position: int = -1):
    """Projection of each layer's DELTA (h_{L+1}-h_L) onto a unit `concept_vec`
    (a residual-space direction) — how much each layer WRITES that concept.
    Returns [projection per layer]."""
    torch = _torch()
    tr = forward_trace(tm, prompt)
    hs = tr["hidden"]
    c = concept_vec / (concept_vec.norm() + 1e-9)
    proj = []
    for i in range(len(hs) - 1):
        d = (hs[i + 1][0, position] - hs[i][0, position]).to(c.dtype)
        proj.append(float(torch.dot(d, c)))
    return proj


# --- pure-python logit-lens math (no torch) — for unit-testing the logic -----

def _rank_in(scores, target_index):
    """Rank of target_index in a descending sort of `scores` (0 = top).
    Pure-python mirror of answer_rank_by_layer's ranking, for tests."""
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    return order.index(target_index)
