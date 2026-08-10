"""Self-concern API titles and detail for the concerns tab."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import jabberwock_daemon as jbd


def test_concern_title_conversation_request():
    title = jbd._concern_title(
        {"source": "conversation", "predicate": "fix", "content": "grammar"},
        "Fix your grammar.")
    assert title == "fix grammar"


def test_concern_title_knowledge_gap():
    title = jbd._concern_title(
        {"source": "implicit", "kind": "knowledge", "content": "moon"},
        None)
    assert title == "Knowledge gap: moon"


def test_concern_detail_prefers_message():
    detail = jbd._concern_detail(
        {"content": "grammar"},
        "Fix your grammar.")
    assert detail == "Fix your grammar."
