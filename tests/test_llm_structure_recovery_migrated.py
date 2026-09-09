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


# ---- shape substitution (block 311000) ---------------------------------

@_need_model
def test_shape_retrieve_off_bit_exact():
    npm = lsr.NumpyQwen3(MODEL)
    ids = [464, 6722, 315, 9822, 374]
    full = npm.forward_logits(ids)
    off = npm.forward_logits(ids, sparse=lsr.SparseConfig(ffn_retrieve_frac=1.0))
    assert np.max(np.abs(full - off)) == 0.0


@_need_model
def test_shape_retrieve_cuts_updown_flops():
    npm = lsr.NumpyQwen3(MODEL)
    ids = [464, 6722, 315, 9822, 374]
    fc_full = {}
    npm.forward_logits(ids, sparse=lsr.SparseConfig(), flop_counter=fc_full)
    fc_r = {}
    npm.forward_logits(ids, sparse=lsr.SparseConfig(ffn_retrieve_frac=0.1),
                       flop_counter=fc_r)
    assert fc_r["flops"] < fc_full["flops"]


@_need_model
def test_exact_topk_beats_shape_retrieve_at_same_frac():
    """The oracle activation-selector preserves the outcome at least as well as
    the gate-key geometry selector at the same fraction — the measured shape
    gap (the up-projection carries shape the single key misses)."""
    npm = lsr.NumpyQwen3(MODEL)
    prompts = [[464, 6722, 315, 9822, 374], [32, 5562, 374, 264, 3169, 315],
               [791, 14329, 315, 4106, 374]]
    full = [int(npm.forward_logits(p).argmax()) for p in prompts]
    frac = 0.5
    et = sum(int(npm.forward_logits(p, sparse=lsr.SparseConfig(ffn_keep_frac=frac)).argmax()) == f
             for p, f in zip(prompts, full))
    sr = sum(int(npm.forward_logits(p, sparse=lsr.SparseConfig(ffn_retrieve_frac=frac)).argmax()) == f
             for p, f in zip(prompts, full))
    assert et >= sr   # oracle selection is at least as good as gate-key


# ---- order-2 multi-query shape (block 312000) --------------------------

@_need_model
def test_order2_shape_none_bit_exact():
    npm = lsr.NumpyQwen3(MODEL)
    ids = [464, 6722, 315, 9822, 374]
    full = npm.forward_logits(ids)
    off = npm.forward_logits(ids, sparse=lsr.SparseConfig(order2_shape=None))
    assert np.max(np.abs(full - off)) == 0.0


@_need_model
def test_fit_order2_shape_returns_per_layer_sets():
    npm = lsr.NumpyQwen3(MODEL)
    corpus = [[464, 6722, 315, 9822, 374], [32, 5562, 374, 264, 3169, 315]]
    shape = lsr.fit_order2_shape(npm, corpus, frac=0.5)
    assert set(shape) == set(range(npm.n_layers))
    for L, sel in shape.items():
        # ~half the FFN neurons kept, and they are valid indices
        assert 0 < len(sel) <= npm._t("model.layers.%d.mlp.gate_proj.weight" % L).shape[0]


@_need_model
def test_order2_at_least_order1_aggressive_heldout():
    """In the aggressive regime (frac 0.5), the corpus-fitted order-2 keep-set
    selects at least as well as the single-query order-1 gate-key on held-out
    prompts — the true shape is more visible over multiple queries."""
    npm = lsr.NumpyQwen3(MODEL)
    train = [[464, 6722, 315, 9822, 374], [791, 14329, 315, 4106, 374],
             [32, 5562, 374, 264, 3169, 315], [791, 7160, 38268, 304, 279]]
    heldout = [[464, 6722, 315, 9603, 374], [32, 8415, 374, 264, 3169, 315]]
    full = [int(npm.forward_logits(p).argmax()) for p in heldout]
    shape = lsr.fit_order2_shape(npm, train, frac=0.5)
    o2 = sum(int(npm.forward_logits(p, sparse=lsr.SparseConfig(order2_shape=shape)).argmax()) == f
             for p, f in zip(heldout, full))
    o1 = sum(int(npm.forward_logits(p, sparse=lsr.SparseConfig(ffn_retrieve_frac=0.5)).argmax()) == f
             for p, f in zip(heldout, full))
    assert o2 >= o1


# ---- coactivation graph (block 313000) ---------------------------------

@_need_model
def test_fit_coactivation_graph_structure():
    npm = lsr.NumpyQwen3(MODEL)
    corpus = [[464, 6722, 315, 9822, 374], [791, 14329, 315, 4106, 374],
              [32, 5562, 374, 264, 3169, 315]]
    G = lsr.fit_coactivation_graph(npm, corpus, per_query_frac=0.1, pool_frac=0.5)
    # per-layer co-firing dicts, frequency arrays, and candidate pools present
    assert set(G.cofire) == set(range(npm.n_layers))
    assert set(G.freq) == set(range(npm.n_layers))
    for L in range(npm.n_layers):
        assert isinstance(G.cofire[L], dict)
        assert len(G.active_pool[L]) >= 1


@_need_model
def test_coactivation_retrieve_returns_valid_sets():
    npm = lsr.NumpyQwen3(MODEL)
    corpus = [[464, 6722, 315, 9822, 374], [791, 14329, 315, 4106, 374],
              [32, 5562, 374, 264, 3169, 315]]
    G = lsr.fit_coactivation_graph(npm, corpus, per_query_frac=0.1, pool_frac=0.5)
    shp = lsr.coactivation_retrieve(npm, G, [464, 6722, 315, 9603, 374],
                                    seed_frac=0.2, target_frac=0.5)
    assert set(shp) == set(range(npm.n_layers))
    for L in range(npm.n_layers):
        ff = npm._t("model.layers.%d.mlp.gate_proj.weight" % L).shape[0]
        sel = shp[L]
        assert 0 < len(sel) <= ff
        assert sel.min() >= 0 and sel.max() < ff
        # roughly the target fraction (>= since it fills toward target_k)
        assert len(sel) >= int(round(ff * 0.2))


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
