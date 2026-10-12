"""Authenticated-principal boundaries for CoW user sessions."""
from __future__ import annotations

import json
import os
import stat

import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

from domains import cow_sessions
from domains.cow_sessions import (
    CowSessionManager, _adapter_digest, _adapter_graph_digest,
)
from substrate.world_adapter import WorldAdapter


def test_users_get_private_whole_adapter_branches_and_owned_sessions_only():
    manager = CowSessionManager(WorldAdapter())
    a = manager.create_session("principal-a")
    b = manager.create_session("principal-b")
    a_session = manager.get_session("principal-a", a["id"])
    b_session = manager.get_session("principal-b", b["id"])

    node = a_session.adapter.s.add_node("UserPrivateFact", {"owner": "a"})
    assert a_session.adapter.s.has_node(node)
    assert not b_session.adapter.s.has_node(node)
    assert manager.list_sessions("principal-b") == [b]

    with pytest.raises(KeyError, match="session not found"):
        manager.get_session("principal-b", a["id"])


def test_real_conversation_turn_is_private_to_user_branch_and_baseline():
    manager = CowSessionManager(WorldAdapter())
    a = manager.create_session("principal-a")
    b = manager.create_session("principal-b")
    user_a = manager.get_session("principal-a", a["id"])
    user_b = manager.get_session("principal-b", b["id"])
    initial_updated_at = user_a.updated_at
    baseline_count = manager._baseline.s.node_count()
    sibling_count = user_b.adapter.s.node_count()

    manager.chat("principal-a", a["id"], "A private greeting")

    assert any(turn["text"] == "A private greeting"
               for turn in user_a.adapter.chat_transcript())
    assert not any(turn["text"] == "A private greeting"
                   for turn in user_b.adapter.chat_transcript())
    assert user_b.adapter.s.node_count() == sibling_count
    assert manager._baseline.s.node_count() == baseline_count
    assert user_a.updated_at > initial_updated_at
    assert manager.describe_session(user_a)["state"] == "active"


def test_fork_starts_at_source_state_and_clear_resets_only_selected_session():
    manager = CowSessionManager(WorldAdapter())
    root = manager.create_session("principal-a")
    source = manager.get_session("principal-a", root["id"])
    source.adapter.s.add_node("UserPrivateFact", {"owner": "source"})

    child = manager.fork_session("principal-a", source.id)
    child_session = manager.get_session("principal-a", child["id"])
    assert child["parent_id"] == source.id
    assert child_session.adapter.s.node_count() == source.adapter.s.node_count()

    manager.clear_session("principal-a", child["id"])
    cleared = manager.get_session("principal-a", child["id"])
    assert cleared.adapter.s.node_count() < source.adapter.s.node_count()
    assert source.adapter.s.node_count() > cleared.adapter.s.node_count()
    assert manager.get_session("principal-a", source.id).adapter.s.node_count() \
        == source.adapter.s.node_count()


def test_failed_session_clear_restores_parent_and_timestamp(monkeypatch):
    manager = CowSessionManager(WorldAdapter())
    info = manager.create_session("principal-a")
    target = manager.get_session("principal-a", info["id"])
    target.parent_id = "f" * 32
    previous_adapter = target.adapter
    previous_updated_at = target.updated_at
    monkeypatch.setattr(manager, "_persist_session",
                        lambda *_args: (_ for _ in ()).throw(OSError("commit failed")))

    with pytest.raises(OSError, match="commit failed"):
        manager.clear_session("principal-a", target.id)

    assert target.adapter is previous_adapter
    assert target.parent_id == "f" * 32
    assert target.updated_at == previous_updated_at


def test_real_turn_fork_continuation_and_clear_preserve_sibling_history():
    manager = CowSessionManager(WorldAdapter())
    root_info = manager.create_session("principal-a")
    manager.chat("principal-a", root_info["id"], "My name is Alice.")
    root = manager.get_session("principal-a", root_info["id"])

    child_info = manager.fork_session("principal-a", root.id)
    child = manager.get_session("principal-a", child_info["id"])
    manager.chat("principal-a", child.id, "What name did I share?")

    assert [turn["text"] for turn in root.adapter.chat_transcript()] == [
        "My name is Alice."]
    assert [turn["text"] for turn in child.adapter.chat_transcript()] == [
        "My name is Alice.", "What name did I share?"]

    manager.clear_session("principal-a", child.id)
    assert manager.get_session("principal-a", root.id).adapter.chat_transcript() \
        == root.adapter.chat_transcript()
    assert manager.get_session("principal-a", child.id).adapter.chat_transcript() == []


def test_sibling_and_nested_forks_diverge_without_mutating_ancestors():
    manager = CowSessionManager(WorldAdapter())
    root = manager.create_session("principal-a")
    left = manager.fork_session("principal-a", root["id"])
    right = manager.fork_session("principal-a", root["id"])
    left_session = manager.get_session("principal-a", left["id"])
    right_session = manager.get_session("principal-a", right["id"])
    left_node = left_session.adapter.s.add_node("BranchFact", {"branch": "left"})
    right_node = right_session.adapter.s.add_node("BranchFact", {"branch": "right"})

    grandchild = manager.fork_session("principal-a", left["id"])
    grandchild_session = manager.get_session("principal-a", grandchild["id"])
    grandchild_node = grandchild_session.adapter.s.add_node(
        "BranchFact", {"branch": "grandchild"})

    root_adapter = manager.get_session("principal-a", root["id"]).adapter

    def facts(adapter):
        return {adapter.s.node(node)["attrs"]["branch"]
                for node in adapter.s.nodes("BranchFact")}

    assert facts(root_adapter) == set()
    assert facts(left_session.adapter) == {"left"}
    assert facts(right_session.adapter) == {"right"}
    assert facts(grandchild_session.adapter) == {"left", "grandchild"}
    assert grandchild["parent_id"] == left["id"]


def test_explicit_user_clear_removes_only_that_principals_sessions():
    manager = CowSessionManager(WorldAdapter())
    a = manager.create_session("principal-a")
    b = manager.create_session("principal-b")

    manager.clear_user("principal-a")
    assert manager.list_sessions("principal-a") == []
    assert manager.list_sessions("principal-b") == [b]
    assert manager.ensure_default_session("principal-a")
    assert manager.list_sessions("principal-a")
    assert a["id"] != manager.ensure_default_session("principal-a")


def test_persisted_user_clear_commits_empty_namespace_and_removes_all_revisions(tmp_path):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    first = manager.create_session("principal-a")
    second = manager.create_session("principal-a")
    folder = manager._metadata_path("principal-a").parent
    assert list(folder.glob("*.save"))

    manager.clear_user("principal-a")
    assert not list(folder.glob("*.save"))
    assert not list(folder.glob("*.runtime.json"))
    resumed = CowSessionManager(baseline, storage_dir=tmp_path)
    assert resumed.list_sessions("principal-a") == []
    assert resumed.ensure_default_session("principal-a") not in {
        first["id"], second["id"]}


def test_failed_persisted_user_clear_preserves_old_checkpoint_and_registry(
        tmp_path, monkeypatch):
    manager = CowSessionManager(WorldAdapter(), storage_dir=tmp_path)
    info = manager.create_session("principal-a")
    folder = manager._metadata_path("principal-a").parent
    original = manager._persist_metadata
    monkeypatch.setattr(manager, "_persist_metadata",
                        lambda _principal: (_ for _ in ()).throw(OSError("commit failed")))

    with pytest.raises(OSError, match="commit failed"):
        manager.clear_user("principal-a")

    assert manager.list_sessions("principal-a")[0]["id"] == info["id"]
    assert list(folder.glob("*.save"))
    monkeypatch.setattr(manager, "_persist_metadata", original)
    resumed = CowSessionManager(WorldAdapter(), storage_dir=tmp_path)
    assert resumed.list_sessions("principal-a")[0]["id"] == info["id"]


def test_turn_state_rolls_back_when_checkpoint_commit_fails(monkeypatch):
    manager = CowSessionManager(WorldAdapter())
    info = manager.create_session("principal-a")
    session = manager.get_session("principal-a", info["id"])
    before = session.adapter.s.node_count()

    def partial_turn(_text, speaker):
        session.adapter.s.add_node("UncommittedTurn", {"speaker": speaker})
        return "reply"

    session.adapter.converse = partial_turn
    previous_updated_at = session.updated_at
    monkeypatch.setattr(manager, "_persist_session",
                        lambda *_args: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError, match="disk full"):
        manager.chat("principal-a", info["id"], "hello")
    assert session.adapter.s.node_count() == before
    assert session.adapter.s.nodes("UncommittedTurn") == []
    assert session.updated_at == previous_updated_at


def test_persisted_namespace_recovers_sessions_and_parent_lineage(tmp_path):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    root = manager.create_session("principal-a")
    root_session = manager.get_session("principal-a", root["id"])
    root_session.adapter._seen.add(("private", "marker", 7))
    manager.chat("principal-a", root["id"], "persist this")
    child = manager.fork_session("principal-a", root["id"])

    resumed = CowSessionManager(baseline, storage_dir=tmp_path)
    rows = resumed.list_sessions("principal-a")
    assert {row["id"] for row in rows} == {root["id"], child["id"]}
    assert next(row for row in rows if row["id"] == child["id"])["parent_id"] \
        == root["id"]
    recovered = resumed.get_session("principal-a", root["id"])
    assert ("private", "marker", 7) in recovered.adapter._seen


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission modes")
def test_persisted_namespace_directories_and_files_are_owner_only(tmp_path):
    storage = tmp_path / "ocelot-state"
    manager = CowSessionManager(WorldAdapter(), storage_dir=storage)
    info = manager.create_session("principal-a")
    folder = manager._metadata_path("principal-a").parent

    assert stat.S_IMODE(storage.stat().st_mode) == 0o700
    assert stat.S_IMODE((storage / "users").stat().st_mode) == 0o700
    assert stat.S_IMODE(folder.stat().st_mode) == 0o700
    for path in folder.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert (folder / f"{info['id']}.r1.save").is_file()


def test_failed_revision_commit_recovers_previous_checkpoint(tmp_path, monkeypatch):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    info = manager.create_session("principal-a")
    session = manager.get_session("principal-a", info["id"])
    session.adapter._seen.add(("private", "committed", 1))
    manager._persist_session("principal-a", session)
    committed_revision = session.revision

    session.adapter._seen.add(("private", "uncommitted", 2))
    monkeypatch.setattr(manager, "_persist_metadata",
                        lambda _principal: (_ for _ in ()).throw(OSError("simulated commit failure")))
    with pytest.raises(OSError, match="simulated commit failure"):
        manager._persist_session("principal-a", session)
    assert session.revision == committed_revision

    resumed = CowSessionManager(baseline, storage_dir=tmp_path)
    recovered = resumed.get_session("principal-a", info["id"])
    assert ("private", "committed", 1) in recovered.adapter._seen
    assert ("private", "uncommitted", 2) not in recovered.adapter._seen
    folder = resumed._metadata_path("principal-a").parent
    assert (folder / f"{info['id']}.r{committed_revision + 1}.save").exists() is False


def test_failed_revision_staging_removes_uncommitted_first_session_files(
        tmp_path, monkeypatch):
    manager = CowSessionManager(WorldAdapter(), storage_dir=tmp_path)

    def fail_directory_sync(_path):
        raise OSError("simulated directory sync failure")

    monkeypatch.setattr(cow_sessions, "_fsync_directory", fail_directory_sync)
    with pytest.raises(OSError, match="directory sync failure"):
        manager.create_session("principal-a")

    folder = manager._user_dir("principal-a")
    assert not list(folder.glob("*.save"))
    assert not list(folder.glob("*.runtime.json"))
    assert manager.list_sessions("principal-a") == []


def test_persistence_rejects_tampered_committed_checkpoint(tmp_path):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    info = manager.create_session("principal-a")
    folder = manager._metadata_path("principal-a").parent
    checkpoint = folder / f"{info['id']}.r1.save"
    checkpoint.write_bytes(checkpoint.read_bytes() + b" ")

    resumed = CowSessionManager(baseline, storage_dir=tmp_path)
    with pytest.raises(RuntimeError, match="digest mismatch"):
        resumed.list_sessions("principal-a")


def test_v2_metadata_migrates_graph_only_baseline_digest_to_v3(tmp_path):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    info = manager.create_session("principal-a")
    metadata_path = manager._metadata_path("principal-a")
    payload = json.loads(metadata_path.read_text())
    payload["schema"] = "ocelot_cow_sessions.v2"
    payload["baseline_digest"] = _adapter_graph_digest(manager._users["principal-a"])
    metadata_path.write_text(json.dumps(payload))

    resumed = CowSessionManager(baseline, storage_dir=tmp_path)
    rows = resumed.list_sessions("principal-a")

    assert rows[0]["id"] == info["id"]
    migrated = json.loads(metadata_path.read_text())
    assert migrated["schema"] == "ocelot_cow_sessions.v3"
    assert migrated["baseline_digest"] == _adapter_digest(resumed._users["principal-a"])


def test_v1_metadata_migrates_legacy_checkpoint_names_atomically(tmp_path):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    info = manager.create_session("principal-a")
    folder = manager._metadata_path("principal-a").parent
    metadata_path = manager._metadata_path("principal-a")
    payload = json.loads(metadata_path.read_text())
    payload["schema"] = "ocelot_cow_sessions.v1"
    payload.pop("baseline_digest")
    for row in payload["sessions"]:
        row.pop("revision")
        row.pop("graph_digest")
        row.pop("runtime_digest")
        session_id = row["id"]
        (folder / f"{session_id}.r1.save").rename(folder / f"{session_id}.save")
        (folder / f"{session_id}.r1.runtime.json").rename(
            folder / f"{session_id}.runtime.json")
    metadata_path.write_text(json.dumps(payload))

    resumed = CowSessionManager(baseline, storage_dir=tmp_path)
    rows = resumed.list_sessions("principal-a")

    assert rows[0]["id"] == info["id"]
    assert rows[0]["revision"] == 1
    assert json.loads(metadata_path.read_text())["schema"] == "ocelot_cow_sessions.v3"
    assert not (folder / f"{info['id']}.save").exists()
    assert (folder / f"{info['id']}.r1.save").exists()


def test_failed_recovery_does_not_cache_partial_principal_state(tmp_path):
    baseline = WorldAdapter()
    writer = CowSessionManager(baseline, storage_dir=tmp_path)
    info = writer.create_session("principal-a")
    checkpoint = (writer._metadata_path("principal-a").parent
                  / f"{info['id']}.r1.save")
    original = checkpoint.read_bytes()
    checkpoint.write_bytes(original + b"tamper")

    reader = CowSessionManager(baseline, storage_dir=tmp_path)
    with pytest.raises(RuntimeError, match="digest mismatch"):
        reader.list_sessions("principal-a")
    assert "principal-a" not in reader._users

    checkpoint.write_bytes(original)
    assert reader.list_sessions("principal-a")[0]["id"] == info["id"]


def test_persistence_rejects_changed_baseline(tmp_path):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    manager.create_session("principal-a")
    changed_baseline = WorldAdapter()
    changed_baseline.s.add_node("ChangedBaselineMarker", {"changed": True})

    resumed = CowSessionManager(changed_baseline, storage_dir=tmp_path)
    with pytest.raises(RuntimeError, match="baseline digest mismatch"):
        resumed.list_sessions("principal-a")


def test_persistence_rejects_changed_adapter_runtime_baseline(tmp_path):
    baseline = WorldAdapter()
    baseline._seen.add(("baseline", "runtime", 1))
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    manager.create_session("principal-a")

    changed_baseline = WorldAdapter()
    changed_baseline._seen.add(("baseline", "runtime", 2))
    resumed = CowSessionManager(changed_baseline, storage_dir=tmp_path)
    with pytest.raises(RuntimeError, match="baseline digest mismatch"):
        resumed.list_sessions("principal-a")


def test_adapter_runtime_digest_is_stable_for_unordered_container_order():
    first = WorldAdapter()
    first._seen = {("alpha", "k", 1), ("beta", "k", 2)}
    second = WorldAdapter()
    second._seen = {("beta", "k", 2), ("alpha", "k", 1)}

    assert _adapter_digest(first) == _adapter_digest(second)


def test_recovery_collects_uncommitted_checkpoint_files(tmp_path, monkeypatch):
    baseline = WorldAdapter()
    manager = CowSessionManager(baseline, storage_dir=tmp_path)
    info = manager.create_session("principal-a")
    session = manager.get_session("principal-a", info["id"])
    session.adapter._seen.add(("private", "orphan", 3))
    monkeypatch.setattr(manager, "_persist_metadata",
                        lambda _principal: (_ for _ in ()).throw(OSError("commit unavailable")))
    with pytest.raises(OSError):
        manager._persist_session("principal-a", session)
    folder = manager._metadata_path("principal-a").parent
    orphan = folder / f"{info['id']}.r2.save"
    assert orphan.is_file()

    recovered = CowSessionManager(baseline, storage_dir=tmp_path)
    recovered.list_sessions("principal-a")
    assert not orphan.exists()


def test_isolated_baseline_mode_builds_a_distinct_user_baseline():
    built = []

    def baseline_factory():
        adapter = WorldAdapter()
        adapter._seen.add(("baseline", str(len(built)), 1))
        built.append(adapter)
        return adapter

    manager = CowSessionManager(WorldAdapter(), baseline_mode="isolated",
                                baseline_factory=baseline_factory)
    a = manager.create_session("principal-a")
    b = manager.create_session("principal-b")
    a_adapter = manager.get_session("principal-a", a["id"]).adapter
    b_adapter = manager.get_session("principal-b", b["id"]).adapter
    assert len(built) == 2
    assert a_adapter._seen != b_adapter._seen


def test_isolated_baseline_mode_preserves_caller_supplied_seeded_baseline():
    baseline = WorldAdapter()
    marker = baseline.s.add_node("CallerSelectedSeed", {"name": "preserved"})
    manager = CowSessionManager(baseline, baseline_mode="isolated")
    session_info = manager.create_session("principal-a")
    user_adapter = manager.get_session("principal-a", session_info["id"]).adapter

    assert user_adapter.s.has_node(marker)
    assert user_adapter.s.node(marker)["attrs"]["name"] == "preserved"


def test_unsupported_conversation_only_mode_fails_instead_of_falling_back():
    with pytest.raises(ValueError, match="conversation_only isolation is not supported"):
        CowSessionManager(WorldAdapter(), isolation_mode="conversation_only")


def test_distinct_sessions_can_process_turns_concurrently():
    manager = CowSessionManager(WorldAdapter())
    a = manager.create_session("principal-a")
    b = manager.create_session("principal-b")
    rendezvous = Barrier(2, timeout=3)
    for principal, session_id in (("principal-a", a["id"]),
                                  ("principal-b", b["id"])):
        session = manager.get_session(principal, session_id)
        def fake_converse(text, speaker):
            rendezvous.wait()
            return f"{speaker}:{text}"
        session.adapter.converse = fake_converse

    with ThreadPoolExecutor(max_workers=2) as pool:
        one = pool.submit(manager.chat, "principal-a", a["id"], "one")
        two = pool.submit(manager.chat, "principal-b", b["id"], "two")
        assert one.result(timeout=5) == "principal-a:one"
        assert two.result(timeout=5) == "principal-b:two"


@pytest.mark.parametrize("lifecycle", ["fork", "clear"])
def test_session_lifecycle_waits_for_an_inflight_turn(lifecycle):
    manager = CowSessionManager(WorldAdapter())
    info = manager.create_session("principal-a")
    session = manager.get_session("principal-a", info["id"])
    turn_entered = Event()
    release_turn = Event()
    lifecycle_started = Event()

    def blocked_turn(_text, speaker):
        turn_entered.set()
        assert release_turn.wait(timeout=5)
        session.adapter.s.add_node("ConcurrentTurn", {"speaker": speaker})
        return "finished"

    session.adapter.converse = blocked_turn
    with ThreadPoolExecutor(max_workers=2) as pool:
        turn = pool.submit(manager.chat, "principal-a", session.id, "in flight")
        assert turn_entered.wait(timeout=5)

        def perform_lifecycle():
            lifecycle_started.set()
            if lifecycle == "fork":
                return manager.fork_session("principal-a", session.id)
            return manager.clear_session("principal-a", session.id)

        operation = pool.submit(perform_lifecycle)
        assert lifecycle_started.wait(timeout=5)
        release_turn.set()
        assert turn.result(timeout=5) == "finished"
        result = operation.result(timeout=5)

    if lifecycle == "fork":
        child = manager.get_session("principal-a", result["id"])
        assert child.adapter.s.nodes("ConcurrentTurn")
        assert session.adapter.s.nodes("ConcurrentTurn")
    else:
        assert result["revision"] == session.revision
        assert session.adapter.s.nodes("ConcurrentTurn") == []


def test_user_clear_blocks_new_session_creation_until_it_finishes():
    manager = CowSessionManager(WorldAdapter())
    existing_info = manager.create_session("principal-a")
    other_info = manager.create_session("principal-b")
    existing = manager.get_session("principal-a", existing_info["id"])
    other = manager.get_session("principal-b", other_info["id"])
    gate = manager._namespace_gate("principal-a")
    turn_entered = Event()
    release_turn = Event()
    clear_started = Event()
    create_started = Event()

    def blocked_turn(_text, speaker):
        turn_entered.set()
        assert release_turn.wait(timeout=5)
        existing.adapter.s.add_node("PreClearTurn", {"speaker": speaker})
        return "finished"

    existing.adapter.converse = blocked_turn
    other.adapter.converse = lambda _text, speaker: "other principal completed"
    with ThreadPoolExecutor(max_workers=4) as pool:
        turn = pool.submit(manager.chat, "principal-a", existing.id, "in flight")
        assert turn_entered.wait(timeout=5)

        def clear_namespace():
            clear_started.set()
            manager.clear_user("principal-a")

        clear = pool.submit(clear_namespace)
        assert clear_started.wait(timeout=5)
        with gate._condition:
            assert gate._condition.wait_for(
                lambda: gate._waiting_writers > 0, timeout=5)

        def create_after_clear():
            create_started.set()
            return manager.create_session("principal-a")

        create = pool.submit(create_after_clear)
        assert create_started.wait(timeout=5)
        assert not create.done()
        # The namespace gate is per principal: B is not held behind A's clear.
        assert manager.chat("principal-b", other.id, "independent") \
            == "other principal completed"
        release_turn.set()
        assert turn.result(timeout=5) == "finished"
        clear.result(timeout=5)
        new_session = create.result(timeout=5)

    assert [row["id"] for row in manager.list_sessions("principal-a")] == [
        new_session["id"]]
    assert new_session["id"] != existing.id
