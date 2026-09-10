"""Block 331000 — the reaped-LLM source `qwen3` is seeded as a CALIBRATED
generative source whose held epistemic weight sits BELOW an attested reference.

The extraction arc (327-329) reaps an LLM's content; block 331 registers the
model as a `source` the agent already knows how to weigh (`source_provenance`).
An LLM is a self-published synthetic source — a confident crowd-compression —
so it seeds a `generative_source` genre and a `qwen3` concept with a flat
`reliability` band strictly below Wikipedia's `consensus_tertiary`. Per-tier
trust (knowledge > concept > process, from the block-330 calibration) is carried
on the reaped EDGES (block 332), not smeared into this source-wide band.

These tests exercise the seed JSON shape + the in-tree `source_provenance`
reader for the FLAT band. The temporal-timeline elaboration (dated calibration
events composed via `context_for`) was deferred here for want of the
`communication_concepts` installer; block 334 re-authored that installer as an
additive seed-builder and the temporal path is now exercised in
tests/test_qwen3_temporal_source.py.
"""
from __future__ import annotations

import json
import os

import pytest

SEED = "seeds/communication_concepts.json"
CAN_SEED = "seeds/can_native_reimplementation.json"


def _concepts():
    d = json.load(open(SEED))
    arr = d.get("concepts") if isinstance(d, dict) else d
    return {c["name"]: c for c in arr if isinstance(c, dict) and "name" in c}


def test_seed_json_wellformed_and_qwen3_present():
    c = _concepts()
    assert "generative_source" in c
    assert "qwen3" in c
    # genre chain: qwen3 is-a generative_source is-a source
    assert "generative_source" in c["qwen3"]["built_from"]
    assert "source" in c["generative_source"]["built_from"]


def test_qwen3_carries_calibrated_below_consensus_reliability():
    c = _concepts()
    assert c["qwen3"]["reliability"] == "self_published_calibrated"
    assert c["generative_source"]["reliability"] == "self_published_calibrated"
    # NOT an attested/consensus band
    assert c["qwen3"]["reliability"] != c["wikipedia"]["reliability"]
    # the genre's conventions encode "fluency is not evidence / corroborate"
    conv = c["generative_source"]["conventions"]
    assert conv.get("fluency_is_not_evidence") is True
    assert conv.get("corroborate_before_assert") is True


def test_source_provenance_label_resolves_qwen3_and_llm():
    from domains import source_provenance as sp
    assert sp._source_concept_name("qwen3") == "qwen3"
    assert sp._source_concept_name("Qwen3.8-4B said") == "qwen3"
    assert sp._source_concept_name("an llm produced this") == "language_model"
    assert sp._source_concept_name("wikipedia") == "wikipedia"   # unbroken


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
def test_qwen3_epistemic_band_below_wikipedia():
    from substrate_rs import _native
    from substrate.seed_loader import engine_rules_only
    from domains import source_provenance as sp
    s = _native.Substrate()
    s.load_seed_manifest(engine_rules_only(json.load(open(CAN_SEED))))
    s.add_node("Concept", {"name": "wikipedia", "reliability": "consensus_tertiary"})
    s.add_node("Concept", {"name": "qwen3", "reliability": "self_published_calibrated"})
    w = sp.epistemic_status_for_source(s, "wikipedia")
    q = sp.epistemic_status_for_source(s, "qwen3")
    assert w is not None and q is not None
    # calibrated LLM sits strictly below an attested reference, above a conjecture
    assert q["confidence"] < w["confidence"]
    assert q["confidence"] > 0.1
    assert q["status"] == "self_published"
