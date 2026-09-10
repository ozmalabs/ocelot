"""Block 334000 — the reaped `qwen3` source's trust band is DERIVED + time-sliced.

Block 331 seeded qwen3 with a FLAT `self_published_calibrated` band, deferring
the temporal-timeline path because the `communication_concepts` installer (the
JSON->graph materializer for a source's `timeline` -> SourceEvent nodes) had been
removed with the python-core purge and the SourceEvent grammar looked absent.

Block 334 re-authors that installer as an ADDITIVE seed-builder (mechanical
JSON->graph install, no decision logic) and confirms the reader side
(source_provenance.context_for / _compose_trust / _source_events, and the
SourceEvent/has_event node+edge types) was already live. Installing the seed now
MATERIALIZES the qwen3 concept's calibration `timeline` as SourceEvent graph
nodes, so epistemic_status_for_source DERIVES a time-sliced band from the events
instead of the flat tag.

Honest calibration made structural: knowledge (is-a) EARNED (+1), process
(negate) CONTROL-FAILED (-1), concept (opposite) too weak to earn (neutral).
Net zero -> the calibrated self-published baseline, but now derived + auditable
+ time-sliced, and still strictly BELOW an attested reference (wikipedia).

Pure graph — NO model, NO network.
"""
from __future__ import annotations

import os

import pytest

SEED = "seeds/communication_concepts.json"


def _have_substrate():
    try:
        import substrate_rs  # noqa: F401
        return os.path.isfile(SEED)
    except Exception:
        return False


_need = pytest.mark.skipif(
    not _have_substrate(),
    reason="substrate_rs / seed absent (run with PYTHONPATH=runners/dsl/python)")


def _find_concept(s, name):
    for cid in s.nodes("Concept"):
        if s.node(cid)["attrs"].get("name") == name:
            return cid
    return None


def _fresh_world_with_seed():
    from substrate_rs import _native
    from domains.communication_concepts import install_communication_concepts_seed
    s = _native.Substrate()
    mt = install_communication_concepts_seed(s)
    assert mt is not None
    return s


@_need
def test_installer_materializes_qwen3_calibration_timeline():
    s = _fresh_world_with_seed()
    qid = _find_concept(s, "qwen3")
    assert qid is not None
    evs = list(s.neighbours(qid, "has_event"))
    ids = sorted(s.node(e)["attrs"].get("event_id") for e in evs)
    assert ids == [
        "qwen3_calibration_concept_opposite",
        "qwen3_calibration_knowledge_isa",
        "qwen3_calibration_process_negate",
    ]
    # every event is GROUNDED (built_from) in >=1 concept it grounds_in
    for e in evs:
        assert list(s.neighbours(e, "built_from"))


@_need
def test_qwen3_band_is_derived_time_sliced_not_flat():
    from domains import source_provenance as sp
    s = _fresh_world_with_seed()
    st = sp.epistemic_status_for_source(s, "qwen3")
    assert st is not None
    # DERIVED + time-sliced (temporal path), not the flat held band
    why = st.get("why") or ""
    assert "DERIVED" in why and "time-sliced" in why


@_need
def test_qwen3_composed_net_is_honest_and_below_attested():
    from domains import source_provenance as sp
    s = _fresh_world_with_seed()
    ctx = sp.context_for(s, "qwen3")
    assert ctx["temporal"] is True
    tr = ctx["trust"]
    # knowledge EARNED raises, process CONTROL-FAILED lowers, concept neutral
    assert tr["raising_events"] == ["qwen3_calibration_knowledge_isa"]
    assert tr["lowering_events"] == ["qwen3_calibration_process_negate"]
    # net zero -> calibrated self-published baseline
    assert tr["status"] == "self_published"
    assert abs(tr["weight"] - 0.5) < 1e-9
    # strictly below the attested reference
    w = sp.epistemic_status_for_source(s, "wikipedia")
    q = sp.epistemic_status_for_source(s, "qwen3")
    assert q["confidence"] < w["confidence"]


@_need
def test_qwen3_band_time_slices_before_calibration():
    """A cutoff BEFORE the 2026-09-04 calibration -> empty cone -> bare baseline;
    proving the band is DERIVED from dated events, not a flat constant."""
    from domains import source_provenance as sp
    s = _fresh_world_with_seed()
    early = sp.context_for(s, "qwen3", when="2020-01-01")
    assert early["in_cone_events"] == []
    assert early["trust"]["raising_events"] == []
    assert early["trust"]["lowering_events"] == []
