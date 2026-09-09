"""LLM structure recovery — Qwen3-0.6B as an explicit dataflow graph — tests.

See docs/research/psychology_affect/LLM_STRUCTURE_RECOVERY_PREREG.md and
scripts/llm_structure_recovery_measure.py.

The module needs numpy (present in the substrate env) but NOT torch — torch is
only the reference oracle. So: the graph-structure logic is tested
unconditionally; the reference-agreement tests are gated on torch + the model
and skip gracefully. When run with the external venv python they all execute.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

from domains import llm_structure_recovery as lsr  # noqa: E402

MODEL = "/applications/data/model_graph_work/Qwen3-0.6B"
_HAVE_MODEL = os.path.isfile(os.path.join(MODEL, "model.safetensors"))


def _have_torch():
    try:
        import torch  # noqa: F401
        return True
    except Exception:
        return False


_HAVE_REF = _have_torch() and _HAVE_MODEL
_need_model = pytest.mark.skipif(not _HAVE_MODEL, reason="Qwen3-0.6B absent")
_need_ref = pytest.mark.skipif(not _HAVE_REF, reason="torch/model absent")


# ---- graph structure (needs the model weights for config, but no torch) ----

@_need_model
def test_graph_is_explicit_dag():
    npm = lsr.NumpyQwen3(MODEL)
    g, out = lsr.build_graph(npm, [1, 2, 3, 4])
    # every node references only EARLIER nodes -> a valid topological DAG
    for node in g.nodes:
        for i in node.inputs:
            assert i < node.id
    # expected op kinds present
    ops = {n.op for n in g.nodes}
    for k in ("embed", "rmsnorm", "matmul_t", "gqa_attention", "swiglu",
              "add", "unembed_last"):
        assert k in ops, k
    # node count scales with layers (per-layer block + embed/norm/unembed)
    assert len(g.nodes) > npm.n_layers * 10


@_need_model
def test_graph_eval_equals_direct_numpy():
    npm = lsr.NumpyQwen3(MODEL)
    ids = [464, 6722, 315, 9822, 374]        # arbitrary token ids
    direct = npm.forward_logits(ids)
    g, out = lsr.build_graph(npm, ids)
    graph = g.evaluate(out)
    assert np.max(np.abs(direct - graph)) == 0.0   # bit-exact


@_need_model
def test_forward_path_uses_no_torch():
    """The recovered forward must not import torch. Assert torch is not loaded
    as a side effect of a forward pass."""
    import sys as _s
    had = "torch" in _s.modules
    npm = lsr.NumpyQwen3(MODEL)
    npm.forward_logits([1, 2, 3])
    if not had:
        assert "torch" not in _s.modules, "forward path pulled in torch"


# ---- sparsification (block 310000) -------------------------------------

@_need_model
def test_sparsity_off_bit_exact():
    npm = lsr.NumpyQwen3(MODEL)
    ids = [464, 6722, 315, 9822, 374]
    full = npm.forward_logits(ids)
    off = npm.forward_logits(ids, sparse=lsr.SparseConfig())
    assert np.max(np.abs(full - off)) == 0.0
    assert lsr.SparseConfig().off is True


@_need_model
def test_ffn_gating_cuts_flops():
    npm = lsr.NumpyQwen3(MODEL)
    ids = [464, 6722, 315, 9822, 374]
    fc_full = {}
    npm.forward_logits(ids, sparse=lsr.SparseConfig(), flop_counter=fc_full)
    fc_k = {}
    npm.forward_logits(ids, sparse=lsr.SparseConfig(ffn_keep_frac=0.25),
                       flop_counter=fc_k)
    assert fc_k["flops"] < fc_full["flops"]


@_need_model
def test_layer_deltas_shape():
    npm = lsr.NumpyQwen3(MODEL)
    d = npm.layer_deltas([464, 6722, 315, 9822, 374])
    assert len(d) == npm.n_layers
    assert all(x >= 0 for x in d)


# ---- reference agreement (skip without torch) --------------------------

@_need_ref
def test_matches_reference_next_token():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    npm = lsr.NumpyQwen3(MODEL)
    tok = AutoTokenizer.from_pretrained(MODEL)
    ref = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32).eval()
    for p in ("The capital of Germany is", "A cat is a kind of"):
        ids = tok(p, return_tensors="pt")["input_ids"][0].tolist()
        with torch.no_grad():
            rt = int(ref(torch.tensor([ids])).logits[0, -1].argmax())
        g, out = lsr.build_graph(npm, ids)
        gt = int(g.evaluate(out).argmax())
        assert rt == gt, (p, rt, gt)


# ---- default == today ---------------------------------------------------

def test_default_equals_today_so_unchanged():
    import hashlib
    so = "runners/dsl/python/substrate_rs/_native.abi3.so"
    if not os.path.exists(so):
        return
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == "7efe75eba05b006cafd15dbb4b7da246", md5
