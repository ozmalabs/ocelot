"""tests/test_seed_guard_migrated.py — gates the durable safety guard in domains/teach.py
(`OZMA_SEED_PERSIST_DISABLED` / `_persist_blocked`). Twice-bitten (runs 47/48): `teach()`
persists to `seeds/<category>.json` (the REAL boot seed dir) by default, and several
migrated test files called teach()-backed helpers without tmp isolation, mutating a real
file owned across sessions.

SAFETY: this suite never touches the actual production `seeds/` dir. Every "real dir"
scenario below monkeypatches `domains.teach.SEEDS` to a throwaway tmp path first, so the
guard's own comparison (`Path(seeds_dir).resolve() == SEEDS.resolve()`) is exercised
end-to-end against a stand-in, never the genuine directory. `test_guard_is_env_and_dir_
conditioned` calls `_persist_blocked` directly (a pure path comparison, no I/O) against the
REAL `teach_mod.SEEDS` constant, which is safe because that function never writes."""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import teach as teach_mod

ENV = teach_mod.OZMA_SEED_PERSIST_DISABLED_ENV


def _teach_agent(s):
    """`teach()` requires `agent.s` -- the established idiom (domains/stroke_codebook.py's
    `_teach_agent`) for calling it from a bare Substrate: a throwaway shim carrying just
    that attribute."""
    return type("_TeachAgent", (), {"s": s})()


def _boot_shim():
    s, _agent_node = boot_core()
    return _teach_agent(s), s


def test_guard_blocks_write_to_real_dir_when_env_set(tmp_path, monkeypatch):
    """(a) env set + seeds_dir resolves to the (patched, stand-in) real SEEDS dir -> no
    file created, but the live graph add still happens."""
    fake_real = tmp_path / "real_seeds"
    fake_real.mkdir()
    monkeypatch.setattr(teach_mod, "SEEDS", fake_real)
    monkeypatch.setenv(ENV, "1")

    tagent, s = _boot_shim()
    before = len(list(s.nodes("TaughtHint")))
    res = teach_mod.teach(tagent, "TaughtHint", {"topic": "guard_test_a", "answer": "x"},
                           category="guard_test_cat", seeds_dir=teach_mod.SEEDS)

    assert res["persisted"] is False
    assert res["saved"] is False
    assert not (fake_real / "guard_test_cat.json").exists()
    assert list(fake_real.iterdir()) == []          # no file of any name was created
    after = len(list(s.nodes("TaughtHint")))
    assert after == before + 1                       # in-graph add unaffected


def test_guard_leaves_explicit_tmp_dir_unaffected(tmp_path, monkeypatch):
    """(b) env set, but the caller passes an EXPLICIT seeds_dir that is NOT the (patched)
    real SEEDS dir -- the established test-isolation idiom (`teach(..., seeds_dir=tmp_path)`)
    must still write normally."""
    fake_real = tmp_path / "real_seeds"
    fake_real.mkdir()
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    monkeypatch.setattr(teach_mod, "SEEDS", fake_real)
    monkeypatch.setenv(ENV, "1")

    tagent, s = _boot_shim()
    res = teach_mod.teach(tagent, "TaughtHint", {"topic": "guard_test_b", "answer": "y"},
                           category="guard_test_cat", seeds_dir=isolated)

    assert res["persisted"] is True
    assert res["saved"] is True
    written = isolated / "guard_test_cat.json"
    assert written.exists()
    data = json.loads(written.read_text())
    assert any(n["attrs"].get("topic") == "guard_test_b" for n in data["nodes"])
    assert not (fake_real / "guard_test_cat.json").exists()   # real dir untouched


def test_guard_inactive_when_env_unset(tmp_path, monkeypatch):
    """(c) env UNSET -> default/real-dir teach() writes as before (byte-compat with the
    pre-guard behaviour)."""
    fake_real = tmp_path / "real_seeds"
    fake_real.mkdir()
    monkeypatch.setattr(teach_mod, "SEEDS", fake_real)
    monkeypatch.delenv(ENV, raising=False)

    tagent, s = _boot_shim()
    res = teach_mod.teach(tagent, "TaughtHint", {"topic": "guard_test_c", "answer": "z"},
                           category="guard_test_cat", seeds_dir=teach_mod.SEEDS)

    assert res["persisted"] is True
    assert res["saved"] is True
    written = fake_real / "guard_test_cat.json"
    assert written.exists()
    data = json.loads(written.read_text())
    assert any(n["attrs"].get("topic") == "guard_test_c" for n in data["nodes"])


def test_guard_is_env_and_dir_conditioned_not_a_blanket_disable(monkeypatch, tmp_path):
    """(d) source + behavioural audit: the guard must require BOTH the env var AND the
    target resolving to the real SEEDS dir -- never a blanket "env set => never persist"
    (which would also wrongly break every isolation fixture's explicit-tmp-dir write).

    `_persist_blocked` never performs I/O (pure path comparison), so it is safe to call
    directly against the REAL `teach_mod.SEEDS` constant here without patching it."""
    real = teach_mod.SEEDS
    other = tmp_path / "not_the_real_seeds_dir"
    other.mkdir()

    monkeypatch.delenv(ENV, raising=False)
    assert teach_mod._persist_blocked(real) is False   # env unset -> never blocks
    assert teach_mod._persist_blocked(other) is False

    monkeypatch.setenv(ENV, "1")
    assert teach_mod._persist_blocked(real) is True    # env set + real dir -> blocks
    assert teach_mod._persist_blocked(other) is False  # env set + other dir -> unaffected

    src = inspect.getsource(teach_mod._persist_blocked)
    assert ENV in inspect.getsource(teach_mod)
    assert "os.environ.get" in src and "SEEDS" in src and "resolve" in src
