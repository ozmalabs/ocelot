"""Newer models are more graph-like — metric + reader tests.

See docs/research/psychology_affect/NEWER_MODELS_MORE_GRAPHLIKE_PREREG.md and
scripts/newer_models_graphlike_measure.py.

Metric mechanics are tested on a SYNTHETIC matrix with a known cluster
structure (unconditional). Real-model reads (sharded HF + gemma GGUF) skip
gracefully when the model is absent.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

from domains import model_active_extraction as mae  # noqa: E402

WORK_DIR = "/applications/data/model_graph_work"
QWEN17 = os.path.join(WORK_DIR, "Qwen3-1.7B")
_HAVE_QWEN17 = os.path.isfile(os.path.join(QWEN17, "model.safetensors.index.json"))
_HAVE_GEMMA = mae.resolve_gguf_blob("gemma3:4b") is not None
_need_qwen = pytest.mark.skipif(not _HAVE_QWEN17, reason="Qwen3-1.7B absent")
_need_gemma = pytest.mark.skipif(not _HAVE_GEMMA, reason="gemma3:4b absent")


# ---- synthetic model for metric mechanics (unconditional) --------------

def _synthetic_lm(clustered=True, seed=0):
    """A LoadedModel-shaped stub with a KNOWN geometry: clustered rows have
    crisp reciprocal neighbourhoods (graph-like); scrambled rows do not."""
    rng = np.random.default_rng(seed)
    if clustered:
        centres = rng.normal(size=(10, 16))
        rows, names = [], {}
        for c in range(10):
            for i in range(8):
                rows.append(centres[c] + 0.02 * rng.normal(size=16))
                names["c%d_%d" % (c, i)] = len(rows) - 1
        W = np.array(rows, dtype=np.float32)
    else:
        W = rng.normal(size=(80, 16)).astype(np.float32)
        names = {"t%d" % i: i for i in range(80)}
    inv = {i: t for t, i in names.items()}
    work = list(range(W.shape[0]))
    M = W / (np.linalg.norm(W, axis=1, keepdims=True) + 1e-9)
    return mae.LoadedModel(blob="", vec_fn=lambda i: W[i], vocab=names, inv=inv,
                           shape=W.shape, marker="", work_ids=work, kind="hf",
                           src="", _M=M, _pos={t: j for j, t in enumerate(work)})


def test_structure_probes_detect_concentration():
    """A low-rank clustered geometry (few directions carry variance) must have
    a LOWER pr_over_d than a full-rank random one — the structure probe detects
    representational concentration, independent of any codec."""
    clustered = mae.structure_probes(_synthetic_lm(True), sample=80)
    scrambled = mae.structure_probes(_synthetic_lm(False), sample=80)
    assert clustered["pr_over_d"] < scrambled["pr_over_d"], (clustered, scrambled)
    assert 0.0 < clustered["erank_over_d"] <= 1.0


def test_knn_reciprocity_higher_for_clustered():
    clustered = mae.knn_reciprocity(_synthetic_lm(True), sample=80, k=7)
    scrambled = mae.knn_reciprocity(_synthetic_lm(False), sample=80, k=7)
    # a clustered (graph-like) geometry has more mutual neighbours
    assert clustered > scrambled, (clustered, scrambled)
    assert clustered > 0.5


def test_distill_survival_monotone_in_bits():
    lm = _synthetic_lm(True)
    surv = mae.distill_survival(lm, k=5, bits=(8, 4, 3))
    # more bits -> higher (or equal) recall
    assert surv[8] >= surv[4] - 1e-6 >= 0
    assert surv[8] > 0.5


def test_shard_map_single_file(tmp_path):
    # a dir with a single model.safetensors resolves every tensor to it
    import struct
    import json as _json
    hdr = {"a": {"dtype": "F32", "shape": [2, 2], "data_offsets": [0, 16]}}
    raw = _json.dumps(hdr).encode()
    p = tmp_path / "model.safetensors"
    with open(p, "wb") as f:
        f.write(struct.pack("<Q", len(raw)))
        f.write(raw)
        f.write(b"\x00" * 16)
    smap = mae._shard_map(str(tmp_path))
    assert smap["a"] == str(p)


# ---- real sharded HF read (skip if absent) -----------------------------

@_need_qwen
def test_qwen_sharded_embedding_reads():
    lm = mae.load_model(QWEN17, work_vocab=5000)
    assert lm.kind == "hf"
    assert lm.shape[0] > 100000 and lm.shape[1] == 2048


@_need_qwen
def test_qwen_ffn_concept_best_layer():
    lm = mae.load_model(QWEN17, work_vocab=8000)
    L, idx, align, promoted = mae.ffn_concepts_best_layer(
        lm, ["dog", "cat", "animal", "pet"])
    joined = " ".join(t.lower() for t in promoted)
    assert any(w in joined for w in ("animal", "dog", "cat", "pet", "bird")), \
        (L, align, promoted)


QWEN38 = os.path.join(WORK_DIR, "Qwen3.8-27B")
_HAVE_QWEN38 = os.path.isfile(os.path.join(QWEN38, "model.safetensors.index.json"))
_need_qwen38 = pytest.mark.skipif(not _HAVE_QWEN38, reason="Qwen3.8-27B absent")


@_need_qwen38
def test_qwen38_untied_and_prefixed_read():
    """Qwen3.8-27B is multimodal-wrapped (model.language_model.* prefix) and
    UNTIED (separate lm_head). The reader must find the prefixed embedding and
    load lm_head as the unembed projection."""
    lm = mae.load_model(QWEN38, work_vocab=5000)
    assert lm.kind == "hf"
    assert lm.shape[1] == 5120
    assert lm._ffn_prefix == "model.language_model.layers"
    # untied => _Mout (lm_head unembed rows) loaded for the promoted-token read
    assert getattr(lm, "_Mout", None) is not None


# ---- default == today ---------------------------------------------------

def test_default_equals_today_so_unchanged():
    import hashlib
    so = "runners/dsl/python/substrate_rs/_native.abi3.so"
    if not os.path.exists(so):
        return
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == "7efe75eba05b006cafd15dbb4b7da246", md5
