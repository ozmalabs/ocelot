"""Block 330000 — tests for the HF-forward shim (`domains/llm_hf_forward.py`)
and the HF-variant contextual-vector extractor. Gated on torch + the harvest
model being present (the model + venv live under /applications, not committed),
so these run only in the harvest environment.
"""
from __future__ import annotations

import os
import pytest

from domains import llm_hf_forward as hf
from domains import llm_process_seed as ps

MODEL = "/applications/data/model_graph_work/Qwen3.8-4B-Distill"


def _have():
    try:
        import torch  # noqa: F401
        return os.path.isdir(MODEL) and os.path.isfile(
            os.path.join(MODEL, "config.json"))
    except Exception:
        return False


_need = pytest.mark.skipif(not _have(),
                           reason="harvest model / torch absent (under /applications)")


def test_hfforward_class_present():
    # the shim imports without torch/model (torch is imported lazily in __init__)
    assert hasattr(hf, "HFForward")
    assert hasattr(ps, "statement_vectors_hf")


@_need
def test_hfforward_logits_and_hidden_states():
    import numpy as np
    m = hf.HFForward(MODEL, dtype="float32")
    tok = m.tokenizer
    ids = tok("The capital of France is", return_tensors="pt")["input_ids"][0].tolist()
    lg = m.forward_logits(ids)
    assert lg.ndim == 1 and lg.shape[0] > 1000            # vocab logits
    # a capable model puts the right token on top
    top = tok.decode([int(np.argmax(lg))]).strip().lower()
    assert "paris" in top
    hs = m.hidden_all_layers(ids)
    assert len(hs) >= 2
    d = hs[0].shape[0]
    assert all(h.shape == (d,) for h in hs)               # per-layer last-token [d]


@_need
def test_statement_vectors_hf_shape():
    import numpy as np
    m = hf.HFForward(MODEL, dtype="float32")
    vecs = ps.statement_vectors_hf(m, m.tokenizer,
                                   ["Water is wet", "Fire is hot"], layer=8)
    assert set(vecs.keys()) == {"Water is wet", "Fire is hot"}
    d = vecs["Water is wet"].shape[0]
    assert vecs["Fire is hot"].shape == (d,)
    assert np.isfinite(vecs["Water is wet"]).all()
