"""LLVM vocabulary baker — front-load the teacher's payloads as a seed.

Covers the bake / write / load round-trip and confirms that replaying
the seed against the seed-booted WorldAdapter installs a Microtheory +
lexicon Sign for every entry (install_vocab_seed is duck-typed on
learn_from_teacher), so the vocabulary is front-loaded without per-word
teacher round-trips.
"""
from __future__ import annotations

import json

import pytest

from domains.llvm_vocab_baker import (
    bake_vocab, install_vocab_seed, load_vocab_seed, write_vocab_seed,
)
from domains import llvm_teacher


_REPO_ROOT = __file__.rsplit("/tests/", 1)[0]
_SEED_PATH = f"{_REPO_ROOT}/seeds/llvm_ir.json"


# ---------------------------------------------------------------------------
# bake
# ---------------------------------------------------------------------------

def test_bake_vocab_includes_every_canonical_entry():
    m = bake_vocab()
    assert m["id"] == "llvm_ir_vocabulary"
    assert m["entries_count"] == len(llvm_teacher._ENTRIES)
    baked_phrases = {l["phrase"] for l in m["lessons"]}
    canonical_phrases = {e.phrase for e in llvm_teacher._ENTRIES}
    assert baked_phrases == canonical_phrases


def test_bake_vocab_payloads_are_teacher_shape():
    m = bake_vocab()
    # Spot-check a representative entry — payload matches what the
    # teacher would have produced at runtime.
    add_lesson = next(l for l in m["lessons"] if l["phrase"] == "add")
    payload = add_lesson["payload"]
    assert "answer" in payload
    assert "learn" in payload
    entry = payload["learn"][0]
    assert entry["microtheory"] == "llvm_ir"
    assert entry["genl_mt"] == "compiler_ir"
    assert entry["binding_pattern"] == "function_of_two_subjects"
    assert entry["source"] == "llvm_langref"


def test_bake_vocab_payloads_round_trip_through_json():
    m = bake_vocab()
    s = json.dumps(m)
    restored = json.loads(s)
    assert restored["entries_count"] == m["entries_count"]
    assert restored["lessons"][0]["phrase"] == m["lessons"][0]["phrase"]


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------

def test_write_vocab_seed_produces_valid_json(tmp_path):
    p = write_vocab_seed(tmp_path / "out.json")
    assert p.exists()
    # Re-parse and validate.
    m = load_vocab_seed(p)
    assert m["id"] == "llvm_ir_vocabulary"
    assert m["entries_count"] == len(llvm_teacher._ENTRIES)


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------

def test_load_vocab_seed_reads_committed_seed():
    """The seed at seeds/llvm_ir.json (committed alongside this code)
    is loadable + has the expected structure."""
    m = load_vocab_seed(_SEED_PATH)
    assert m["id"] == "llvm_ir_vocabulary"
    assert m["entries_count"] >= 65  # Phase 1 lower bound
    assert isinstance(m["lessons"], list)
    assert all("phrase" in l and "payload" in l for l in m["lessons"])


def test_load_vocab_seed_rejects_missing_lessons_key(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"id": "bad", "version": "1.0.0"}')
    with pytest.raises(ValueError, match="missing 'lessons' key"):
        load_vocab_seed(bad)


# ---------------------------------------------------------------------------
# install — replay the seed into a real agent
# ---------------------------------------------------------------------------

def _agent_or_skip():
    """The seed-booted WorldAdapter — install_vocab_seed is duck-typed on
    `learn_from_teacher`, so the adapter replays the seed exactly as a full
    agent would (Microtheory + lexicon Signs per lesson)."""
    from substrate.world_adapter import WorldAdapter
    return WorldAdapter()


def test_install_vocab_seed_installs_frames_in_agent():
    """The agent ends up with one Frame per lesson — the same Frames
    the teacher would have built lazily, just front-loaded."""
    agent = _agent_or_skip()
    n = install_vocab_seed(agent, _SEED_PATH)
    assert n == load_vocab_seed(_SEED_PATH)["entries_count"]

    # Agent now has the `llvm_ir` Microtheory.
    assert "llvm_ir" in agent.microtheory_names(), \
        "llvm_ir Mt should be installed by the seed"

    # Sample of taught signs — phrases from canonical entries should
    # appear in the agent's lexicon.
    taught_forms = {s.get("form") for s in agent.taught_signs()}
    for sample in ("llvm ir", "add", "phi", "getelementptr"):
        assert sample in taught_forms, \
            f"expected taught sign for {sample!r}; missing"


def test_install_vocab_seed_is_idempotent():
    """Replaying the same seed twice shouldn't double-install — the
    agent's `learn_from_teacher` handles already-known concepts."""
    agent = _agent_or_skip()
    n1 = install_vocab_seed(agent, _SEED_PATH)
    n2 = install_vocab_seed(agent, _SEED_PATH)
    assert n1 == n2
    # Agent isn't broken — still answers from the Frame layer.
    forms = {s.get("form") for s in agent.taught_signs()}
    assert "llvm ir" in forms
