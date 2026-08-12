"""Upload follow-up questions route to current_attachment + GraphEye vision."""
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
    return a


def _answer_attachment_goals(agent):
    out = []
    for g in agent.inner.neighbours(agent.agent, "has_goal"):
        if not agent.inner.has_node(g):
            continue
        if agent.s.node(g)["attrs"].get("kind") == "answer_attachment":
            out.append(g)
    return out


def _self_concerns(agent, *, kind=None, content=None):
    out = []
    for sc in agent.inner.neighbours(agent.agent, "has_self_concern"):
        if not agent.inner.has_node(sc):
            continue
        at = agent.s.node(sc)["attrs"]
        if kind is not None and at.get("kind") != kind:
            continue
        if content is not None and at.get("content") != content:
            continue
        out.append(at)
    return out


def _make_gray_png(path: str, size: int = 32) -> None:
    from PIL import Image
    arr = np.full((size, size, 3), 128, dtype=np.uint8)
    Image.fromarray(arr).save(path, format="PNG")


def test_upload_image_detects_text_presence(agent):
    import domains.file_ingest as fi
    import tempfile
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    arr = np.full((200, 500, 3), 245, dtype=np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:  # noqa: BLE001
        font = None
    draw.text((30, 80), "Hello upload OCR probe 123", fill=(10, 10, 10), font=font)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img.save(f.name, format="PNG")
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="text_probe.png")
        doc = out["document_id"]
        da = agent.s.node(doc)["attrs"]
        assert da.get("contains_text") == 1.0
        assert int(da.get("glyph_like_components") or 0) >= 4
        reply = agent.converse("What is in the image?", speech_act="question")
    finally:
        os.unlink(path)

    assert reply and "text-like" in reply.lower()
    assert "decoded" in reply.lower() or "accurately" in reply.lower()


def test_web_default_upload_question_routes(agent):
    import domains.file_ingest as fi
    import tempfile
    import numpy as np
    from PIL import Image

    arr = np.zeros((200, 300, 3), dtype=np.uint8)
    arr[50:150, 100:200] = [180, 60, 40]
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        Image.fromarray(arr).save(f.name)
        path = f.name
    try:
        fi.ingest_file(agent, path, filename="web_default.png")
        q = "I've uploaded web_default.png. What can you tell me about it?"
        reply = agent.converse(q, speech_act="question")
    finally:
        os.unlink(path)

    assert reply and "don't hold that" not in reply.lower()
    assert "through my eye" in reply.lower() or "shape" in reply.lower()


def test_photo_like_upload_uses_foveated_camera(agent):
    import domains.file_ingest as fi
    import numpy as np
    from PIL import Image

    h, w = 480, 640
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        arr[y, :] = [70 + y // 6, 80 + y // 6, 95 + y // 6]
    arr[120:360, 180:480] = [210, 45, 45]
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        Image.fromarray(arr).save(f.name, format="PNG")
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="photo_like.png")
        doc = out["document_id"]
        da = agent.s.node(doc)["attrs"]
        assert da.get("vision_modality") == "camera"
        assert int(da.get("vision_fixation_count") or 0) >= 2
        assert int(da.get("vision_native_width") or 0) == w
        assert float(da.get("vision_shape_count") or 0) > 0
        reply = agent.converse("What is in the image?", speech_act="question")
    finally:
        os.unlink(path)

    assert reply and "fixation" in reply.lower()
    assert "don't hold that" not in reply.lower()


def test_image_upload_question_uses_grapheye_vision(agent):
    import domains.file_ingest as fi

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_gray_png(f.name)
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="gray_square.png", caption="gray square")
        doc = out["document_id"]
        assert agent.s.node(doc)["attrs"].get("vision_summary")
        assert list(agent.inner.neighbours(doc, "has_shape"))
        reply = agent.converse("What is in the image?", speech_act="question")
    finally:
        os.unlink(path)

    assert reply and "don't hold that" not in reply.lower()
    low = reply.lower()
    assert "through my eye" in low or "shape" in low
    goals = _answer_attachment_goals(agent)
    assert goals, "attachment question must mint Goal{answer_attachment}"
    assert agent.s.node(goals[-1])["attrs"].get("outcome") == "resolved"

    ins = [m for m in agent.s.nodes("Message")
           if agent.s.node(m)["attrs"].get("from") == "interlocutor"
           and "what is in the image" in (agent.s.node(m)["attrs"].get("text") or "").lower()]
    assert ins
    mid = max(ins, key=lambda n: n.value)
    assert agent.s.node(mid)["attrs"].get("attachment_pending") == 1.0
    assert not _self_concerns(agent, kind="reply_fix", content="upload_vision_wiring")


def test_describe_uploaded_image_instruction(agent):
    import domains.file_ingest as fi

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_gray_png(f.name, size=16)
        path = f.name
    try:
        fi.ingest_file(agent, path, filename="tiny.png")
        reply = agent.converse("Describe the image", speech_act="question")
    finally:
        os.unlink(path)

    assert reply and "don't hold that" not in reply.lower()
    assert "through my eye" in reply.lower() or "shape" in reply.lower()


def test_missing_upload_vision_files_gap_then_fixes(agent, monkeypatch):
    """Without GraphEye at ingest, the agent files upload_vision_wiring gap."""
    import domains.file_ingest as fi

    monkeypatch.setattr(
        WorldAdapter, "perceive_upload_image", lambda self, arr, doc_id, **kw: [])

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_gray_png(f.name)
        path = f.name
    try:
        out = fi.ingest_file(agent, path, filename="no_vision.png")
        doc = out["document_id"]
        agent.inner.set_attr(doc, "vision_shape_count", 0.0)
        agent.converse("What is in the image?", speech_act="question")
        agent.comprehend()
    finally:
        os.unlink(path)

    gaps = _self_concerns(agent, kind="reply_fix", content="upload_vision_wiring")
    assert gaps, "image upload without vision_summary must file reply_fix gap"

    # Restore vision path and verify a fresh upload gets shape recognition.
    monkeypatch.undo()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_gray_png(f.name)
        path = f.name
    try:
        fi.ingest_file(agent, path, filename="with_vision.png")
        reply = agent.converse("What is in the image?", speech_act="question")
    finally:
        os.unlink(path)

    assert reply and "through my eye" in reply.lower()


def test_upload_honest_floor_files_reply_fix_gap(agent, monkeypatch):
    """When attachment routing is absent, honest floor on an upload question files a gap."""
    import domains.file_ingest as fi
    from substrate.seed_loader import manifest_for

    for rule_name in ("route_question_to_attachment", "reply_attachment_from_vision",
                      "reply_attachment_from_document"):
        for i, r in enumerate(agent.inner.export_rules()):
            if r.get("active") and r.get("name") == rule_name:
                agent.inner.remove_rule(i)
                break

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_gray_png(f.name)
        path = f.name
    try:
        fi.ingest_file(agent, path, filename="gap_probe.png")
        reply = agent.converse("What is in the image?", speech_act="question")
    finally:
        os.unlink(path)

    assert reply and "don't hold that" in reply.lower()
    agent.comprehend()
    gaps = _self_concerns(agent, kind="reply_fix", content="upload_attachment_reply")
    assert gaps, "honest floor on upload question must file reply_fix gap"

    agent.inner.load_seed_manifest(manifest_for("conversation_attachment_route"), agent.agent)
    agent.inner.load_seed_manifest(manifest_for("conversation_attachment_reply"), agent.agent)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        _make_gray_png(f.name)
        path = f.name
    try:
        fi.ingest_file(agent, path, filename="fixed.png")
        reply2 = agent.converse("What is in the image?", speech_act="question")
    finally:
        os.unlink(path)

    assert reply2 and "don't hold that" not in reply2.lower()
    assert "through my eye" in reply2.lower() or "shape" in reply2.lower()
