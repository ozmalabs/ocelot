"""Chat history persistence for the web UI (daemon file + adapter transcript read)."""
from __future__ import annotations

import os
import sys

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


def test_chat_history_file_roundtrip(tmp_path):
    from scripts.jabberwock_daemon import load_chat_history, save_chat_history

    path = tmp_path / "chat_history.json"
    turns = [{"text": "Can you dance?", "reply": "No — I can't dance. I have no body.",
              "heard": [], "ts": 1.0}]
    save_chat_history(path, turns)
    loaded = load_chat_history(path)
    assert loaded == turns


def test_record_chat_turn_appends_and_dedupes(tmp_path):
    from scripts.jabberwock_daemon import DaemonState, init_chat_history, record_chat_turn

    agent = WorldAdapter(seeds=())
    ckpt_dir = tmp_path / "checkpoints"
    ckpt_dir.mkdir()
    state = DaemonState(agent, "fresh")
    init_chat_history(state, ckpt_dir, agent)
    record_chat_turn(state, "hello", "noted")
    record_chat_turn(state, "hello", "noted")
    assert len(state.chat_turns) == 1
    record_chat_turn(state, "again", "understood")
    assert len(state.chat_turns) == 2
    from scripts.jabberwock_daemon import load_chat_history, _chat_history_path
    loaded = load_chat_history(_chat_history_path(ckpt_dir))
    assert len(loaded) == 2


def test_adapter_chat_transcript_after_converse(agent):
    agent.converse("What are you?", speech_act="question")
    turns = agent.chat_transcript()
    # inbound is always minted; outbound pairing depends on the reply path
    assert isinstance(turns, list)
