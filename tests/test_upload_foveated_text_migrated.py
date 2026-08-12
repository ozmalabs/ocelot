"""Foveated upload text: reflexive identification + active full-read decision."""
from __future__ import annotations

import os
import sys
import tempfile

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

# OPTIONAL DEPENDENCY (red-test triage 2026-08-12): absent 'cv2' is a SKIP with a
# named reason, never a red. See tests/optional_deps.py.
from optional_deps import importorskip as _optional_importorskip  # noqa: E402
_optional_importorskip('cv2')



@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.wire_upload_text_read_faculty()
    return a


def _make_text_image(path: str, text: str, *, size=(400, 120)) -> None:
    from PIL import Image, ImageDraw, ImageFont
    arr = np.full((size[1], size[0], 3), 245, dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:  # noqa: BLE001
        font = None
    draw.text((20, 40), text, fill=(10, 10, 10), font=font)
    img.save(path, format="PNG")


def test_reflexive_foveated_text_identified_on_upload(agent):
    import domains.file_ingest as fi

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_text_image(f.name, "Hello reflexive text probe")
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="reflex_probe.png")
        doc = out["document_id"]
        da = agent.s.node(doc)["attrs"]
        assert da.get("foveated_text_identified") == 1.0
        assert int(da.get("foveated_glyph_count") or 0) >= 1
        regions = list(agent.inner.neighbours(doc, "has_text_region"))
        assert regions, "expected FoveatedTextRegion from reflexive rule"
    finally:
        os.unlink(path)


def test_active_decode_only_when_asked(agent):
    import domains.file_ingest as fi

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_text_image(f.name, "Decode me now please")
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="decode_probe.png")
        doc = out["document_id"]
        da = agent.s.node(doc)["attrs"]
        assert da.get("foveated_text_identified") == 1.0
        assert not da.get("decoded_text")

        agent.converse("What is in the image?", speech_act="question")
        da2 = agent.s.node(doc)["attrs"]
        assert not da2.get("decoded_text"), "presence question must not trigger full decode"

        reply = agent.converse("What does the text say in the image?", speech_act="question")
        da3 = agent.s.node(doc)["attrs"]
        assert da3.get("decoded_text") is not None
        assert reply and ("recover" in reply.lower() or "read" in reply.lower())
    finally:
        os.unlink(path)


def test_decode_goal_minted_by_graph(agent):
    import domains.file_ingest as fi

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_text_image(f.name, "Graph goal mint test")
        path = f.name
    try:
        fi.ingest_file(agent, path, filename="goal_probe.png")
        agent.converse("Read the text in the image", speech_act="question")
        kinds = []
        for g in agent.inner.neighbours(agent.agent, "has_goal"):
            kinds.append(agent.s.node(g)["attrs"].get("kind"))
        assert "decode_upload_text" in kinds
    finally:
        os.unlink(path)
