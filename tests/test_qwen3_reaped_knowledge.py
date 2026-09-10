"""Block 332000 — the reaped qwen3 knowledge seed is well-formed, every edge
carries source+trust, and it reloads into a substrate Microtheory whose
traversal derives multi-hop entailment (no LLM at query).
"""
from __future__ import annotations

import json
import os

import pytest

SEED = "seeds/generated/qwen3_reaped_knowledge.json"
CAN_SEED = "seeds/can_native_reimplementation.json"


def test_reaped_seed_wellformed_and_tagged():
    d = json.load(open(SEED))
    assert d["source"] == "qwen3"
    assert d["relation"] == "isa"
    assert 0.0 < d["trust"] < 0.9            # calibrated, below an attested source
    assert d["edges"]
    for e in d["edges"]:
        assert e["source"] == "qwen3"        # provenance on every edge
        assert "trust" in e                  # per-edge trust
        assert e["subject"] != e["object"]   # self-loops dropped
    # calibration recorded: substrate derived the held-out entailment, shuffle broke it
    cal = d["calibration"]
    assert cal["held_out_transitive_acc"] >= 0.9
    assert cal["shuffled_control_acc"] < 0.75


def _have_substrate():
    try:
        import substrate_rs  # noqa: F401
        return os.path.isfile(CAN_SEED)
    except Exception:
        return False


_need = pytest.mark.skipif(
    not _have_substrate(),
    reason="substrate_rs / can seed absent (run with PYTHONPATH=runners/dsl/python)")


@_need
def test_reaped_seed_reloads_and_derives_entailment():
    from substrate_rs import _native
    from domains import llm_knowledge_seed as ks
    d = json.load(open(SEED))
    triples = [(e["subject"], e["object"]) for e in d["edges"]]
    s = _native.Substrate()
    mt, n2n = ks.build_knowledge_mt(s, [CAN_SEED], triples, relation="isa")
    # a direct edge that IS stored:
    assert ks.query_direct(s, n2n, "poodle", "dog") is True
    # a >=2-hop entailment the substrate DERIVES (poodle -> dog -> ... -> animal),
    # which is NOT a stored edge:
    assert ks.query_direct(s, n2n, "poodle", "animal") is False
    assert ks.query_transitive(s, n2n, "poodle", "animal")[0] is True
