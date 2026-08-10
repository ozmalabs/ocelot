"""Transcoding seed — migrated twin (no CuriousAgent).

Loads ``video`` + ``transcoding`` manifests into a bare
``substrate_rs.Substrate`` (no CuriousAgent), walks through a tiny
transcoding plan: source VideoStream → Ladder → three LadderRung
outputs realised by TranscodeJob nodes. All graph-resident, all
admitted by the seed's grammar, no agent.

This file is the migrated twin of ``test_transcoding_seed.py``.
The original was already CuriousAgent-free; this twin confirms the
full coverage with explicit migration labelling.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")

from substrate.seed_loader import manifest_for


def _load(sub, *ids):
    """Apply the named seeds in order. Bare-substrate version of
    load_seeds — no agent, no Seed bookkeeping, just walk the
    manifests."""
    for seed_id in ids:
        sub.load_seed_manifest(manifest_for(seed_id))


def test_video_seed_installs_codec_grammar():
    sub = srs.Substrate()
    _load(sub, "video")
    # The video seed adds productions: container→stream,
    # stream→frame, etc. They're now in the Rust grammar.
    grammar = sub.grammar_to_json()
    edge_types = {p["edge_type"] for p in grammar["productions"]}
    assert "has_stream" in edge_types
    assert "has_frame" in edge_types


def test_transcoding_seed_installs_ladder_and_productions():
    sub = srs.Substrate()
    _load(sub, "video", "transcoding")
    # Three LadderRung nodes from the default ladder.
    rungs = list(sub.nodes("LadderRung"))
    assert len(rungs) == 3
    rung_attrs = [sub.node(r)["attrs"] for r in rungs]
    names = {r["name"] for r in rung_attrs}
    assert names == {"high", "medium", "low"}
    # The 1080p rung has bitrate 5000 kbps.
    high = next(r for r in rung_attrs if r["name"] == "high")
    assert high["height"] == 1080 and high["bitrate_kbps"] == 5000
    # Transcoding productions are admitted.
    grammar = sub.grammar_to_json()
    edge_types = {p["edge_type"] for p in grammar["productions"]}
    assert edge_types >= {"has_input", "has_rung", "produces",
                            "realised_by", "input", "output"}


def test_build_an_actual_transcoding_plan():
    """Use the loaded transcoding ontology to express a real plan:
    one source VideoStream feeding a Ladder whose three rungs each
    produce an output stream via TranscodeJob nodes.

    Every edge is grammar-admitted (the seed's productions
    authorise them); no add_edge_unchecked, no agent, just the
    bare substrate executing the schema."""
    sub = srs.Substrate()
    _load(sub, "video", "transcoding")

    # Source: one VideoStream (the master).
    source = sub.add_node("VideoStream", {"codec": "h264",
                                            "width": 1920,
                                            "height": 1080})
    # The ABR ladder.
    ladder = sub.add_node("Ladder", {"profile": "hls_3tier"})
    sub.add_edge(ladder, "has_input", source)

    # For each default rung, wire it under the ladder, mint a
    # TranscodeJob, and an output VideoStream the job produces.
    rungs = list(sub.nodes("LadderRung"))
    for rung in rungs:
        sub.add_edge(ladder, "has_rung", rung)
        rung_attrs = sub.node(rung)["attrs"]
        output = sub.add_node("VideoStream", {
            "codec": "h264",
            "width": rung_attrs["width"],
            "height": rung_attrs["height"],
            "bitrate_kbps": rung_attrs["bitrate_kbps"],
        })
        job = sub.add_node("TranscodeJob", {"kind": "transrate"})
        sub.add_edge(job, "input", source)
        sub.add_edge(job, "output", output)
        sub.add_edge(rung, "produces", output)
        sub.add_edge(rung, "realised_by", job)

    # Reading the plan back: ladder has 3 rungs, each producing one
    # output, each output realised by a job whose input is the source.
    assert len(list(sub.neighbours(ladder, "has_rung"))) == 3
    for rung in sub.neighbours(ladder, "has_rung"):
        outputs = list(sub.neighbours(rung, "produces"))
        assert len(outputs) == 1
        jobs = list(sub.neighbours(rung, "realised_by"))
        assert len(jobs) == 1
        job_inputs = list(sub.neighbours(jobs[0], "input"))
        assert job_inputs == [source]
