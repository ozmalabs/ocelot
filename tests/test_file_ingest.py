"""File upload ingest — mechanical I/O into the graph."""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def test_ingest_plain_text_file(agent):
    import domains.file_ingest as fi

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("The moon is mostly silicate rock and regolith dust.")
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="moon_notes.txt", caption="notes")
    finally:
        os.unlink(path)

    assert out["kind"] == "text"
    assert out["n_mentions"] >= 5
    mid = out["message_id"]
    assert agent.s.node(mid)["attrs"].get("text") == "notes"
    doc = out["document_id"]
    assert "silicate" in agent.s.node(doc)["attrs"].get("text", "").lower()
    assert list(agent.inner.neighbours(doc, "has_mention"))
    assert doc in list(agent.inner.neighbours(mid, "has_attachment"))


def test_classify_upload_kinds():
    import domains.file_ingest as fi

    assert fi.classify_upload("text/plain", "readme.md") == "text"
    assert fi.classify_upload("image/png", "scan.png") == "image"
    assert fi.classify_upload("application/pdf", "paper.pdf") == "pdf"
    assert fi.classify_upload("audio/wav", "clip.wav") == "audio"
    assert fi.classify_upload("application/octet-stream", "data.bin") == "binary"
