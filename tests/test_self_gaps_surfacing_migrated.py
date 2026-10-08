"""The agent SURFACES ITS OWN GAPS over the chat interface — graph-native.

A gap is graph DATA: a `SelfConcern` node the gap-minting side files, linked
`agent -has_self_concern-> sc` with attrs {status, source, kind, content}. This
suite hand-mints a couple of SelfConcern nodes (the shared contract) so it is
independent of the parallel gap-minting agent, then checks that:

  (1) `reflect("self_gaps", None, a.inner)` reads those nodes and returns a state
      dict that includes their content;
  (2) "What gaps do you have?" is answered by LISTING the filed gap content
      (never the "I am Jabberwock." self-identity non-sequitur);
  (3) a full boot with loader anomalies reports its graph-filed boot-integrity
      gap instead of the formerly incorrect "no gaps" answer.

The reader (`reflective_faculty._run_self_gaps`) only READS graph nodes and
FORMATS them — no decision, no invented content. These tests exercise that read.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import reflective_faculty as rf


def _boot():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _mint_gap(a, source, kind, content, status="noted"):
    sc = a.s.add_node("SelfConcern",
                      {"status": status, "source": source, "kind": kind,
                       "content": content})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
    return sc


def test_reflect_self_gaps_reads_the_filed_concerns():
    a = _boot()
    _mint_gap(a, "implicit", "knowledge", "I do not know how to play chess")
    _mint_gap(a, "explicit_report", "capability", "I cannot see images")

    state = rf.reflect("self_gaps", None, a.inner)
    assert isinstance(state, dict)
    assert "unwired" not in state, "self_gaps must be a wired faculty"
    assert state.get("count") == 2

    # the state must carry the ACTUAL filed content (read off the graph, verbatim)
    contents = [c["content"] for c in state["concerns"]]
    assert "I do not know how to play chess" in contents
    assert "I cannot see images" in contents
    # the rendered `note` mentions the content too (what _surface_self_state shows)
    assert "chess" in state["note"] and "images" in state["note"]
    # grouped by the shared-contract source
    assert set(state["by_source"]) == {"implicit", "explicit_report"}


def test_reflect_self_gaps_reads_via_inner_and_wrapper_identically():
    a = _boot()
    _mint_gap(a, "conversation", "skill", "I struggle with long division")
    via_inner = rf.reflect("self_gaps", None, a.inner)
    via_wrapper = rf.reflect("self_gaps", None, a.s)
    assert via_inner["count"] == via_wrapper["count"] == 1
    assert via_inner["note"] == via_wrapper["note"]
    assert "long division" in via_inner["note"]


def test_converse_lists_filed_gaps_not_self_identity():
    a = _boot()
    _mint_gap(a, "implicit", "knowledge", "I do not know how to play chess")
    _mint_gap(a, "conversation", "skill", "I struggle with long division")

    reply = a.converse("What gaps do you have?", speech_act="question")
    assert isinstance(reply, str) and reply.strip()
    # the filed gap content is surfaced ...
    assert "chess" in reply
    assert "long division" in reply
    # ... and it is NOT the self-identity non-sequitur.
    assert reply.strip() != "I am Jabberwock."
    assert "Jabberwock" not in reply


def test_converse_surfaces_boot_integrity_gap_when_full_boot_is_incomplete(tmp_path):
    # Since tranche 11 the shipped full boot is complete (the 11 non-manifest
    # files moved to domain_data/), so the incomplete boot is constructed: a
    # second boot cycle over a seed dir holding one invalid manifest.
    import json as _json
    a = _boot()
    (tmp_path / "broken.json").write_text(_json.dumps({
        "id": "broken", "version": "1", "nodes": [{"type": "Concept", "attrs": {"name": "broken"}}],
        "edges": [], "productions": [], "rules": []}))
    load_all_seeds(a, seed_dir=tmp_path)
    a.inner.run_rules()
    reply = a.converse("What gaps do you have?", speech_act="question")
    assert isinstance(reply, str) and reply.strip()
    assert "boot integrity" in reply.lower()
    assert "no gaps" not in reply.lower()
    # Evidence-grounded answer, never the self-identity collapse.
    assert reply.strip() != "I am Jabberwock."
    assert "Jabberwock" not in reply


def test_reflect_self_gaps_empty_is_explicit_not_unwired():
    a = _boot()
    state = rf.reflect("self_gaps", None, a.inner)
    assert "unwired" not in state
    assert state.get("count") == 0
    assert state["concerns"] == []
    assert "no gaps" in state["note"].lower()
