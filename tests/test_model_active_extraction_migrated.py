"""Model active extraction — graph pulls apart a generative LM — tests.

See docs/research/psychology_affect/MODEL_ACTIVE_EXTRACTION_PREREG.md and
scripts/model_active_extraction_measure.py.

Static-weight + probe-parsing tests run unconditionally (the parsing/loop
mechanics need no model). Tests that read the GGUF weights skip if the model
blob is absent; tests that RUN the model skip if ollama is unavailable.
"""

import sys

import pytest

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

import substrate_rs as sr  # noqa: E402
from domains import model_active_extraction as mae  # noqa: E402

_HAVE_BLOB = mae.resolve_gguf_blob("gemma3:4b") is not None
_HAVE_OLLAMA = mae.ollama_available("gemma3:4b")
_need_blob = pytest.mark.skipif(not _HAVE_BLOB, reason="gemma3:4b GGUF absent")
_need_ollama = pytest.mark.skipif(not _HAVE_OLLAMA, reason="ollama/model absent")


# ---- probe parsing (unconditional — pure string logic) -----------------

def test_parse_target_strips_prompt_and_markdown():
    prompt = "Complete with one word. A dog is a kind of:"
    assert mae._parse_target(prompt + " **mammal**", prompt) == "mammal"
    assert mae._parse_target(prompt + " animal", prompt) == "animal"


def test_parse_target_skips_stopwords():
    # a completion that leads with stopwords should reach the content word
    assert mae._parse_target("the a of kitchen", "") == "kitchen"


def test_relation_templates_have_edge_types():
    for rel, (tmpl, edge_type) in mae.RELATION_TEMPLATES.items():
        assert "{s}" in tmpl
        assert edge_type and edge_type.islower()


# ---- graph-driven targeting (unconditional — uses a stub prober) -------

def test_active_loop_targets_sparsest(monkeypatch):
    """The active loop must probe the SPARSEST nodes first. Stub the model so
    the test needs no ollama — the ORDERING is the graph's own logic."""
    probed_order = []

    def fake_probe(subject, relation, **kw):
        probed_order.append(subject)
        return (mae.RELATION_TEMPLATES[relation][1], subject + "_x")

    monkeypatch.setattr(mae, "probe_relation", fake_probe)
    s = sr.Substrate()
    inner = s._inner
    nm = {w: inner.add_node("Concept", {"name": w, "state": 0.0,
                                        "external_field": 0.0,
                                        "identity_field": 0.0})
          for w in ("rich", "poor1", "poor2")}
    # 'rich' already has edges -> should be probed LAST under targeting
    inner.add_edge_unchecked(nm["rich"], "is_a", nm["poor1"])
    inner.add_edge_unchecked(nm["rich"], "at_location", nm["poor2"])
    mae.active_extract(s, nm, budget=3, targeted=True, relations=["IsA"])
    # first probed node must be a sparse one, not 'rich'
    assert probed_order[0] != "rich"


def test_active_loop_mints_edges(monkeypatch):
    def fake_probe(subject, relation, **kw):
        return (mae.RELATION_TEMPLATES[relation][1], "target_" + subject)

    monkeypatch.setattr(mae, "probe_relation", fake_probe)
    s = sr.Substrate()
    inner = s._inner
    nm = {"a": inner.add_node("Concept", {"name": "a", "state": 0.0,
                                          "external_field": 0.0,
                                          "identity_field": 0.0})}
    rep = mae.active_extract(s, nm, budget=2, targeted=True,
                             relations=["IsA", "UsedFor"])
    assert rep["edges_added"] == 2
    assert rep["probes"] == 2
    # the minted target node exists in the map now
    assert any(k.startswith("target_") for k in nm)


# ---- static weight reads (skip if blob absent) -------------------------

@_need_blob
def test_ffn_concepts_coherent():
    lm = mae.load_model("gemma3:4b", work_vocab=8000)
    idx, align, promoted = mae.ffn_concepts(lm, ["dog", "cat", "animal", "pet"],
                                            layer=20, top=8)
    # the animal-aligned neuron should promote animal-ish tokens
    joined = " ".join(t.lower() for t in promoted)
    assert any(w in joined for w in ("animal", "dog", "bird", "pet", "mice",
                                     "cat", "horse"))


@_need_blob
def test_embedding_distills_to_graph():
    lm = mae.load_model("gemma3:4b", work_vocab=8000)
    dg = mae.distill_embedding_graph(lm, k=8, quant=0.05)
    # the graph must not retain the dense matrix (anti-faking, inherited 304000)
    import numpy as np
    for v in vars(dg).values():
        assert not (isinstance(v, np.ndarray) and v.ndim == 2)


# ---- running the model (skip if ollama absent) -------------------------

@_need_ollama
def test_probe_relation_returns_typed_edge():
    res = mae.probe_relation("knife", "AtLocation", model_tag="gemma3:4b")
    assert res is not None
    edge_type, tgt = res
    assert edge_type == "at_location"
    assert isinstance(tgt, str) and tgt


# ---- default == today ---------------------------------------------------

def test_default_equals_today_so_unchanged():
    import hashlib
    import os
    so = "runners/dsl/python/substrate_rs/_native.abi3.so"
    if not os.path.exists(so):
        return
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == "7efe75eba05b006cafd15dbb4b7da246", md5
