"""Per-principal CoW namespaces and session lifecycle.

This manager is intentionally transport-neutral. Authentication belongs to
the HTTP boundary; every method takes the already-authenticated principal and
never trusts a user ID from a request body.
"""
from __future__ import annotations

import threading
import time
import uuid
import hashlib
import json
import os
from contextlib import ExitStack
from contextlib import contextmanager
from pathlib import Path
from dataclasses import dataclass, field
from threading import Condition, get_ident

from domains.world_adapter_cow import fork_world_adapter
from substrate.world_adapter import WorldAdapter

_RUNTIME_EXCLUDED = {
    "s", "inner", "_conversation_lock", "_storage_mmap", "_eye",
    "_upload_eye", "_vision_substrate", "_teacher_threads",
    "_discourse_store",
}


def _pack(value, node_id_type):
    if isinstance(value, node_id_type):
        return {"$node": int(value.value)}
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, list):
        return {"$list": [_pack(item, node_id_type) for item in value]}
    if isinstance(value, tuple):
        return {"$tuple": [_pack(item, node_id_type) for item in value]}
    if isinstance(value, set):
        items = [_pack(item, node_id_type) for item in value]
        return {"$set": sorted(items, key=_canonical_json)}
    if isinstance(value, frozenset):
        items = [_pack(item, node_id_type) for item in value]
        return {"$frozenset": sorted(items, key=_canonical_json)}
    if isinstance(value, dict):
        items = [[_pack(key, node_id_type), _pack(item, node_id_type)]
                 for key, item in value.items()]
        return {"$dict": sorted(items, key=lambda pair: _canonical_json(pair[0]))}
    raise TypeError(f"unsupported adapter runtime value: {type(value).__name__}")


def _canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"))


def _unpack(value, node_id_type):
    if not isinstance(value, dict):
        return value
    if "$node" in value:
        return node_id_type(int(value["$node"]))
    if "$list" in value:
        return [_unpack(item, node_id_type) for item in value["$list"]]
    if "$tuple" in value:
        return tuple(_unpack(item, node_id_type) for item in value["$tuple"])
    if "$set" in value:
        return set(_unpack(item, node_id_type) for item in value["$set"])
    if "$frozenset" in value:
        return frozenset(_unpack(item, node_id_type) for item in value["$frozenset"])
    if "$dict" in value:
        return {_unpack(key, node_id_type): _unpack(item, node_id_type)
                for key, item in value["$dict"]}
    raise ValueError("unknown adapter runtime state tag")


def _runtime_state(adapter: WorldAdapter) -> dict:
    node_id_type = type(adapter.agent)
    return {name: _pack(value, node_id_type)
            for name, value in vars(adapter).items()
            if name not in _RUNTIME_EXCLUDED}


def _restore_runtime_state(adapter: WorldAdapter, path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "ocelot_adapter_runtime.v1":
        raise ValueError("unsupported adapter runtime sidecar schema")
    node_id_type = type(adapter.agent)
    for name, packed in payload["state"].items():
        if name in _RUNTIME_EXCLUDED:
            raise ValueError("runtime sidecar attempts to replace a live handle")
        setattr(adapter, name, _unpack(packed, node_id_type))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _adapter_identity(adapter: WorldAdapter) -> dict:
    return {
        "graph": adapter.s.graph_to_dict(),
        "grammar": adapter.s.grammar_to_json(),
        "rules": adapter.inner.export_rules(),
    }


def _digest(value) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _adapter_graph_digest(adapter: WorldAdapter) -> str:
    return _digest(_adapter_identity(adapter))


def _adapter_digest(adapter: WorldAdapter) -> str:
    identity = _adapter_identity(adapter)
    identity["runtime"] = _runtime_state(adapter)
    return _digest(identity)


class _NamespaceGate:
    """Allow parallel per-session work but make user-wide clear exclusive."""

    def __init__(self):
        self._condition = Condition()
        self._readers = 0
        self._writer = False
        self._waiting_writers = 0
        self._reader_depth: dict[int, int] = {}

    @contextmanager
    def read(self):
        thread_id = get_ident()
        with self._condition:
            reentrant = self._reader_depth.get(thread_id, 0) > 0
            while self._writer or (self._waiting_writers and not reentrant):
                self._condition.wait()
            self._readers += 1
            self._reader_depth[thread_id] = self._reader_depth.get(thread_id, 0) + 1
        try:
            yield
        finally:
            with self._condition:
                self._readers -= 1
                depth = self._reader_depth[thread_id] - 1
                if depth:
                    self._reader_depth[thread_id] = depth
                else:
                    del self._reader_depth[thread_id]
                if self._readers == 0:
                    self._condition.notify_all()

    @contextmanager
    def write(self):
        with self._condition:
            self._waiting_writers += 1
            self._condition.notify_all()
            try:
                while self._writer or self._readers:
                    self._condition.wait()
                self._writer = True
            finally:
                self._waiting_writers -= 1
                self._condition.notify_all()
        try:
            yield
        finally:
            with self._condition:
                self._writer = False
                self._condition.notify_all()


@dataclass
class Session:
    id: str
    adapter: WorldAdapter
    parent_id: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    state: str = "active"
    revision: int = 0
    graph_digest: str | None = None
    runtime_digest: str | None = None
    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)


class CowSessionManager:
    """In-process user namespaces, each branched from a shared baseline.

    Session state is whole-adapter CoW. When ``storage_dir`` is configured,
    namespace metadata and each session checkpoint/runtime sidecar are saved
    for restart recovery.
    """

    def __init__(self, baseline: WorldAdapter, storage_dir: str | Path | None = None,
                 *, baseline_mode: str = "shared",
                 isolation_mode: str = "whole_adapter",
                 baseline_factory=None):
        if baseline_mode not in {"shared", "isolated"}:
            raise ValueError("baseline_mode must be 'shared' or 'isolated'")
        if isolation_mode != "whole_adapter":
            raise ValueError(
                "conversation_only isolation is not supported yet; "
                "select whole_adapter explicitly")
        # Pin an immutable, quiescent baseline now. User namespaces must not
        # inherit whichever graph revision happens to be live at first access.
        self._baseline = fork_world_adapter(baseline)
        self.baseline_mode = baseline_mode
        self.isolation_mode = isolation_mode
        # Preserve the caller's selected seed/profile by default. Deployments
        # can provide a factory when each principal needs independently
        # provisioned content or policy.
        self._baseline_factory = baseline_factory or (
            lambda: fork_world_adapter(self._baseline))
        self.storage_dir = Path(storage_dir).expanduser() if storage_dir else None
        if self.storage_dir is not None:
            self._private_directory(self.storage_dir)
        self._users: dict[str, WorldAdapter] = {}
        self._baseline_digests: dict[str, str] = {}
        self._sessions: dict[str, dict[str, Session]] = {}
        self._default_session: dict[str, str] = {}
        self._namespace_gates: dict[str, _NamespaceGate] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _principal(principal: str) -> str:
        value = str(principal or "").strip()
        if not value:
            raise ValueError("authenticated principal is required")
        return value

    def _ensure_user(self, principal: str) -> None:
        if principal not in self._users:
            user_baseline = (
                fork_world_adapter(self._baseline) if self.baseline_mode == "shared"
                else self._baseline_factory())
            self._users[principal] = user_baseline
            self._baseline_digests[principal] = _adapter_digest(user_baseline)
            self._sessions[principal] = {}
            try:
                self._load_user(principal)
            except Exception:
                # A failed recovery must not leave a partially initialized
                # principal that a later request could treat as a new user.
                self._users.pop(principal, None)
                self._baseline_digests.pop(principal, None)
                self._sessions.pop(principal, None)
                self._default_session.pop(principal, None)
                raise

    def _namespace_gate(self, principal: str) -> _NamespaceGate:
        with self._lock:
            return self._namespace_gates.setdefault(principal, _NamespaceGate())

    def _user_dir(self, principal: str) -> Path | None:
        if self.storage_dir is None:
            return None
        key = hashlib.sha256(principal.encode("utf-8")).hexdigest()
        users_dir = self.storage_dir / "users"
        self._private_directory(users_dir)
        path = users_dir / key
        self._private_directory(path)
        return path

    @staticmethod
    def _private_directory(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            path.chmod(0o700)
        except OSError:
            # Keep the service usable on filesystems that do not implement
            # POSIX modes; deployments must enforce equivalent ACLs there.
            pass

    def _metadata_path(self, principal: str) -> Path | None:
        folder = self._user_dir(principal)
        return folder / "sessions.json" if folder else None

    def _write_revision_files(self, folder: Path, session: Session,
                              revision: int) -> tuple[str, str]:
        """Write and sync one immutable checkpoint pair without publishing it."""
        graph_target = folder / f"{session.id}.r{revision}.save"
        runtime_target = folder / f"{session.id}.r{revision}.runtime.json"
        temporary = folder / f".{session.id}.{uuid.uuid4().hex}.save.tmp"
        runtime_temporary = folder / f".{session.id}.{uuid.uuid4().hex}.runtime.tmp"
        runtime_state = _runtime_state(session.adapter)
        graph_target = folder / f"{session.id}.r{revision}.save"
        try:
            session.adapter.save(str(temporary))
            os.chmod(temporary, 0o600)
            with temporary.open("rb") as stream:
                os.fsync(stream.fileno())
            runtime_payload = {
                "schema": "ocelot_adapter_runtime.v1",
                "state": runtime_state,
            }
            with runtime_temporary.open("w", encoding="utf-8") as stream:
                json.dump(runtime_payload, stream, ensure_ascii=False,
                          separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(runtime_temporary, 0o600)
            graph_digest = _sha256_file(temporary)
            runtime_digest = _sha256_file(runtime_temporary)
            os.replace(temporary, graph_target)
            os.replace(runtime_temporary, runtime_target)
            _fsync_directory(folder)
            return graph_digest, runtime_digest
        except Exception:
            # No metadata pointer can reference this revision yet. Remove any
            # half-published pair so a failed first session creation cannot
            # leave orphan checkpoints behind without a sessions.json index.
            graph_target.unlink(missing_ok=True)
            runtime_target.unlink(missing_ok=True)
            try:
                _fsync_directory(folder)
            except OSError:
                pass
            raise
        finally:
            temporary.unlink(missing_ok=True)
            runtime_temporary.unlink(missing_ok=True)

    def _persist_session(self, principal: str, session: Session) -> None:
        folder = self._user_dir(principal)
        if folder is None:
            return
        next_revision = session.revision + 1
        graph_digest, runtime_digest = self._write_revision_files(
            folder, session, next_revision)
        old_revision = session.revision
        old_graph_digest = session.graph_digest
        old_runtime_digest = session.runtime_digest
        session.revision = next_revision
        session.graph_digest = graph_digest
        session.runtime_digest = runtime_digest
        try:
            # This atomic metadata replacement commits the graph and sidecar as
            # one revision. Until it succeeds, recovery still selects the old
            # pair and ignores the new immutable files.
            self._persist_metadata(principal)
        except Exception:
            session.revision = old_revision
            session.graph_digest = old_graph_digest
            session.runtime_digest = old_runtime_digest
            raise
        if old_revision:
            (folder / f"{session.id}.r{old_revision}.save").unlink(missing_ok=True)
            (folder / f"{session.id}.r{old_revision}.runtime.json").unlink(missing_ok=True)
            _fsync_directory(folder)

    def _persist_metadata(self, principal: str) -> None:
        # Registry changes and metadata publication share this lock so an
        # older concurrent chat save cannot overwrite a newer session list.
        with self._lock:
            target = self._metadata_path(principal)
            if target is None:
                return
            payload = {
                "schema": "ocelot_cow_sessions.v3",
                "principal": principal,
                "baseline_mode": self.baseline_mode,
                "isolation_mode": self.isolation_mode,
                "baseline_digest": self._baseline_digests[principal],
                "default_session": self._default_session.get(principal),
                "sessions": [self._metadata_row(session) for session in
                             self._sessions[principal].values()],
            }
            temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
            with temporary.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
            _fsync_directory(target.parent)

    def _load_user(self, principal: str) -> None:
        metadata = self._metadata_path(principal)
        if metadata is None or not metadata.is_file():
            return
        try:
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            schema = payload.get("schema")
            if (schema not in {"ocelot_cow_sessions.v1", "ocelot_cow_sessions.v2",
                              "ocelot_cow_sessions.v3"}
                    or payload.get("principal") != principal
                    or payload.get("baseline_mode", "shared") != self.baseline_mode
                    or payload.get("isolation_mode", "whole_adapter")
                    != self.isolation_mode
                    or not isinstance(payload.get("sessions"), list)):
                raise ValueError("invalid session metadata schema")
            expected_baseline_digest = (
                _adapter_digest(self._users[principal]) if schema == "ocelot_cow_sessions.v3"
                else _adapter_graph_digest(self._users[principal]))
            if (schema in {"ocelot_cow_sessions.v2", "ocelot_cow_sessions.v3"}
                    and payload.get("baseline_digest") != expected_baseline_digest):
                raise ValueError("namespace baseline digest mismatch")
            loaded = {}
            folder = metadata.parent
            for row in payload["sessions"]:
                session_id = str(row["id"])
                if len(session_id) != 32 or any(
                        char not in "0123456789abcdef" for char in session_id):
                    raise ValueError("invalid persisted session ID")
                if schema in {"ocelot_cow_sessions.v2", "ocelot_cow_sessions.v3"}:
                    revision = int(row["revision"])
                    if revision < 1:
                        raise ValueError("invalid persisted session revision")
                    path = folder / f"{session_id}.r{revision}.save"
                    runtime_path = folder / f"{session_id}.r{revision}.runtime.json"
                else:
                    revision = 0
                    path = folder / f"{session_id}.save"
                    runtime_path = folder / f"{session_id}.runtime.json"
                if not path.is_file() or not runtime_path.is_file():
                    raise ValueError("committed session revision is missing")
                graph_digest = _sha256_file(path)
                runtime_digest = _sha256_file(runtime_path)
                if schema in {"ocelot_cow_sessions.v2", "ocelot_cow_sessions.v3"} and (
                        graph_digest != row.get("graph_digest")
                        or runtime_digest != row.get("runtime_digest")):
                    raise ValueError("committed session revision digest mismatch")
                adapter = WorldAdapter.load(str(path))
                _restore_runtime_state(adapter, runtime_path)
                state = str(row.get("state", "active"))
                if state != "active":
                    raise ValueError("unsupported persisted session lifecycle state")
                created_at = float(row.get("created_at") or time.time())
                loaded[session_id] = Session(
                    id=session_id, adapter=adapter,
                    parent_id=row.get("parent_id"),
                    created_at=created_at,
                    updated_at=float(row.get("updated_at") or created_at),
                    state=state, revision=revision,
                    graph_digest=graph_digest,
                    runtime_digest=runtime_digest)
            self._sessions[principal] = loaded
            default = payload.get("default_session")
            if default in loaded:
                self._default_session[principal] = default
            if schema == "ocelot_cow_sessions.v1":
                # Migrate the legacy flat checkpoint names by staging every
                # numbered revision first, then atomically publishing v3.
                # The v1 files remain intact until that metadata commit lands.
                for session in loaded.values():
                    (session.graph_digest, session.runtime_digest) = (
                        self._write_revision_files(folder, session, 1))
                    session.revision = 1
                self._persist_metadata(principal)
                for session in loaded.values():
                    (folder / f"{session.id}.save").unlink(missing_ok=True)
                    (folder / f"{session.id}.runtime.json").unlink(missing_ok=True)
                _fsync_directory(folder)
                schema = "ocelot_cow_sessions.v3"
            elif schema == "ocelot_cow_sessions.v2":
                # v2 stored graph-only baseline digests. Verify that legacy
                # identity, then upgrade the pointer to a runtime-inclusive v3
                # digest without rewriting its already checksummed revisions.
                self._persist_metadata(principal)
                schema = "ocelot_cow_sessions.v3"
            if schema == "ocelot_cow_sessions.v3":
                keep = set()
                for session in loaded.values():
                    keep.add(f"{session.id}.r{session.revision}.save")
                    keep.add(f"{session.id}.r{session.revision}.runtime.json")
                removed = False
                for pattern in ("*.r*.save", "*.r*.runtime.json", "*.save",
                                ".*.tmp", ".*.save.tmp", ".*.runtime.tmp"):
                    for candidate in folder.glob(pattern):
                        if candidate.name not in keep:
                            candidate.unlink(missing_ok=True)
                            removed = True
                if removed:
                    _fsync_directory(folder)
        except Exception as exc:
            raise RuntimeError(
                f"cannot recover persisted namespace {principal!r}: "
                f"{type(exc).__name__}: {exc}") from exc

    def create_session(self, principal: str) -> dict:
        principal = self._principal(principal)
        with self._namespace_gate(principal).read():
            with self._lock:
                self._ensure_user(principal)
                session_id = uuid.uuid4().hex
                session = Session(session_id, fork_world_adapter(self._users[principal]))
                self._sessions[principal][session_id] = session
                was_default = principal not in self._default_session
                self._default_session.setdefault(principal, session_id)
                try:
                    self._persist_session(principal, session)
                except Exception:
                    self._sessions[principal].pop(session_id, None)
                    if was_default:
                        self._default_session.pop(principal, None)
                    raise
                return self.describe_session(session)

    def _get_session(self, principal: str, session_id: str) -> Session:
        principal = self._principal(principal)
        try:
            return self._sessions[principal][str(session_id)]
        except KeyError as exc:
            # Do not disclose whether another principal owns the supplied ID.
            raise KeyError("session not found") from exc

    def ensure_default_session(self, principal: str) -> str:
        principal = self._principal(principal)
        with self._namespace_gate(principal).read():
            with self._lock:
                self._ensure_user(principal)
                current = self._default_session.get(principal)
                if current in self._sessions[principal]:
                    return current
                # RLock and the reentrant namespace read gate keep two
                # simultaneous first requests from creating orphan defaults.
                return self.create_session(principal)["id"]

    def fork_session(self, principal: str, session_id: str) -> dict:
        principal = self._principal(principal)
        with self._namespace_gate(principal).read():
            with self._lock:
                source = self._get_session(principal, session_id)
            with source.lock:
                child = Session(uuid.uuid4().hex,
                                fork_world_adapter(source.adapter),
                                parent_id=source.id)
                with child.lock:
                    with self._lock:
                        if self._sessions.get(principal, {}).get(source.id) is not source:
                            raise KeyError("session not found")
                        self._sessions[principal][child.id] = child
                        try:
                            self._persist_session(principal, child)
                        except Exception:
                            self._sessions[principal].pop(child.id, None)
                            raise
                    return self.describe_session(child)

    def clear_session(self, principal: str, session_id: str) -> dict:
        principal = self._principal(principal)
        with self._namespace_gate(principal).read():
            with self._lock:
                target = self._get_session(principal, session_id)
                baseline = self._users[principal]
            with target.lock:
                with self._lock:
                    if self._sessions.get(principal, {}).get(target.id) is not target:
                        raise KeyError("session not found")
                previous_adapter = target.adapter
                previous_parent = target.parent_id
                previous_updated_at = target.updated_at
                target.adapter = fork_world_adapter(baseline)
                target.parent_id = None
                target.updated_at = time.time()
                try:
                    self._persist_session(principal, target)
                except Exception:
                    target.adapter = previous_adapter
                    target.parent_id = previous_parent
                    target.updated_at = previous_updated_at
                    raise
                return self.describe_session(target)

    def clear_user(self, principal: str) -> None:
        principal = self._principal(principal)
        with self._namespace_gate(principal).write():
            with self._lock:
                self._ensure_user(principal)
                sessions = list(self._sessions[principal].values())
            with ExitStack() as locks:
                for session in sorted(sessions, key=lambda item: item.id):
                    locks.enter_context(session.lock)
                with self._lock:
                    previous_user = self._users[principal]
                    previous_digest = self._baseline_digests[principal]
                    previous_sessions = self._sessions[principal]
                    previous_default = self._default_session.get(principal)
                    replacement_user = (
                        fork_world_adapter(self._baseline)
                        if self.baseline_mode == "shared" else self._baseline_factory())
                    self._users[principal] = replacement_user
                    self._baseline_digests[principal] = _adapter_digest(replacement_user)
                    self._sessions[principal] = {}
                    self._default_session.pop(principal, None)
                    folder = self._user_dir(principal)
                    try:
                        # Publish the empty namespace before deleting old
                        # revision files. A crash after this pointer commit
                        # leaves harmless orphans, never dangling references.
                        self._persist_metadata(principal)
                    except Exception:
                        self._users[principal] = previous_user
                        self._baseline_digests[principal] = previous_digest
                        self._sessions[principal] = previous_sessions
                        if previous_default is not None:
                            self._default_session[principal] = previous_default
                        raise
                if folder is not None:
                    for pattern in ("*.save", "*.runtime.json", ".*.tmp",
                                    ".*.save.tmp", ".*.runtime.tmp"):
                        for path in folder.glob(pattern):
                            path.unlink(missing_ok=True)
                    _fsync_directory(folder)

    def list_sessions(self, principal: str) -> list[dict]:
        principal = self._principal(principal)
        with self._namespace_gate(principal).read():
            with self._lock:
                self._ensure_user(principal)
                return [self.describe_session(item) for item in
                        self._sessions[principal].values()]

    def get_session(self, principal: str, session_id: str) -> Session:
        principal = self._principal(principal)
        with self._namespace_gate(principal).read():
            with self._lock:
                self._ensure_user(principal)
                return self._get_session(principal, session_id)

    def chat(self, principal: str, session_id: str, text: str) -> str:
        principal = self._principal(principal)
        with self._namespace_gate(principal).read():
            with self._lock:
                self._ensure_user(principal)
                session = self._get_session(principal, session_id)
            with session.lock:
                with self._lock:
                    if self._sessions.get(principal, {}).get(session.id) is not session:
                        raise KeyError("session not found")
                previous = fork_world_adapter(session.adapter)
                previous_updated_at = session.updated_at
                try:
                    reply = session.adapter.converse(str(text), speaker=principal)
                    session.updated_at = time.time()
                    self._persist_session(principal, session)
                except Exception:
                    # A turn and its checkpoint pointer form one operation.
                    # If inference or durable commit fails, restore the
                    # pre-turn branch so retry cannot append an uncommitted turn.
                    session.adapter = previous
                    session.updated_at = previous_updated_at
                    raise
                return str(reply)

    @staticmethod
    def _describe(session: Session) -> dict:
        return {"id": session.id, "parent_id": session.parent_id,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "state": session.state,
                "revision": session.revision,
                "isolation": "whole_adapter", "storage": "cow"}

    def describe_session(self, session: Session) -> dict:
        """Return public session metadata without exposing its adapter."""
        description = self._describe(session)
        description["baseline_mode"] = self.baseline_mode
        return description

    @classmethod
    def _metadata_row(cls, session: Session) -> dict:
        row = cls._describe(session)
        row.update({"revision": session.revision,
                    "graph_digest": session.graph_digest,
                    "runtime_digest": session.runtime_digest})
        return row
