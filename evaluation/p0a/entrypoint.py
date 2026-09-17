"""P0 evaluation launch path: evaluator-hosted authority plus fresh sandbox exec.

The legacy I/O guard below is defense in depth for compatibility only.  The
sandbox mount/namespace/descriptor policy in :mod:`sandbox` is the enforcement
boundary; this module deliberately has no fork, multiprocessing, or local
fallback launch path.
"""
from __future__ import annotations

import builtins
from contextlib import contextmanager
from dataclasses import dataclass
import io
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from typing import Iterator

from .agent_protocol import SCHEMA, decode_frame, session_nonce, validate_frame, write_frame
from .broker import ActionBroker, BrokerReply
from .canonical import ProtocolError, canonical_bytes, parse_canonical, sha256
from .graph_proposals import GraphProposalProjector, ObservedGraphActionOutcomeV1, observed_outcome
from .launch_failure import LaunchFailureRecord
from .legacy_io_guard import DirectIODenied, activated, active, deny_direct_io
from .provenance import NativeGraphExportAttestationVerifier, NativeGraphProvenanceVerifier
from .run_paths import LaunchAttemptPaths, RunPaths
from .runtime_failure import RuntimeFailureRecord
from .sandbox import (BwrapSandboxLauncher, SandboxPolicyUnavailable, SandboxSpec,
                      SandboxStartFailed, SandboxUnavailable)
from .supervisor import CgroupSupervisor

_AUDIT_IO_ROUTES = {"open": "builtins.open", "os.chmod": "os.chmod", "os.chown": "os.chown",
                    "os.lchown": "os.lchown", "os.remove": "os.remove", "os.rename": "os.rename",
                    "os.mkdir": "os.mkdir", "os.rmdir": "os.rmdir", "os.symlink": "os.symlink",
                    "os.link": "os.link", "os.truncate": "os.truncate", "os.utime": "os.utime"}


def _audit_direct_io(event: str, _args: tuple[object, ...]) -> None:
    route = _AUDIT_IO_ROUTES.get(event)
    if route is not None and active(): deny_direct_io(route)


sys.addaudithook(_audit_direct_io)


def _blocked(route: str):
    deny_direct_io(route)
    raise DirectIODenied(f"P0A_DIRECT_IO_DENIED:{route}")


@contextmanager
def intercept_legacy_process_io() -> Iterator[None]:
    """Compatibility defense in depth; not P0 isolation or custody evidence."""
    patches = {(socket, "socket"): (socket.socket, "socket"), (urllib.request, "urlopen"): (urllib.request.urlopen, "urllib.urlopen"),
               (subprocess, "Popen"): (subprocess.Popen, "subprocess.Popen"), (os, "system"): (os.system, "os.system"),
               (os, "execv"): (os.execv, "os.execv"), (os, "execve"): (os.execve, "os.execve"),
               (os, "read"): (os.read, "os.read"),
               (builtins, "open"): (builtins.open, "builtins.open"), (io, "open"): (io.open, "io.open")}
    originals = {target: value[0] for target, value in patches.items()}
    try:
        for (owner, name), (_original, route) in patches.items(): setattr(owner, name, lambda *a, _route=route, **k: _blocked(_route))
        yield
    finally:
        for (owner, name), original in originals.items(): setattr(owner, name, original)


def _context_hash(value: object) -> str:
    try: return sha256(value if isinstance(value, bytes) else canonical_bytes(value))
    except Exception: return sha256(b"unavailable-startup-context")


def _manifest_failure_reason(exc: Exception) -> str:
    message = str(exc)
    if "expired" in message: return "manifest_expired"
    if "unknown manifest key" in message or "signature" in message: return "manifest_unauthorized"
    if "enable no methods" in message: return "manifest_fixture_policy_violation"
    return "manifest_malformed"


class _HostProtocolServer:
    """Parent-only broker/projection endpoint over bounded worker stdio."""
    def __init__(self, process, *, broker, provenance, grant_resolver, run_id: str, runtime_record,
                 receipt_log, now_ms, supervisor: CgroupSupervisor, heartbeat_deadline_ms: int | None):
        self.process, self.broker, self.run_id = process, broker, run_id
        self.runtime_record, self.receipt_log, self.now_ms, self.supervisor = runtime_record, receipt_log, now_ms, supervisor
        self.heartbeat_deadline_ms = heartbeat_deadline_ms
        self.projector = GraphProposalProjector(broker, grant_resolver=grant_resolver, provenance_verifier=provenance)
        self.nonce = session_nonce(); self._terminal = False; self._lock = threading.Lock()
        self._thread: threading.Thread | None = None; self._watchdog: threading.Thread | None = None

    def _fail(self, code: str, error: Exception | str, *, kill_scope: bool = True) -> None:
        with self._lock:
            if self._terminal: return
            self._terminal = True
        try:
            self.runtime_record.record(run_id=self.run_id, verified_manifest_hash=self.broker.manifest.manifest_hash,
                                       last_valid_receipt_sequence=self.receipt_log.sequence,
                                       last_valid_receipt_hash=self.receipt_log.previous, reason_code=code, error=error)
        finally:
            if kill_scope:
                try: self.supervisor.stop(code)
                except Exception: pass

    def start(self) -> None:
        self.supervisor.heartbeat(self.now_ms())
        try:
            write_frame(self.process.process.stdin, {"schema": SCHEMA, "type": "hello", "run_id": self.run_id, "session_nonce": self.nonce})
        except Exception as exc:
            self._fail("sandbox_protocol_eof", exc); raise ProtocolError("sandbox protocol startup failed") from exc
        self._thread = threading.Thread(target=self._serve, name="p0-evaluator-protocol", daemon=True); self._thread.start()
        if self.heartbeat_deadline_ms is not None:
            self._watchdog = threading.Thread(target=self._watch, name="p0-evaluator-watchdog", daemon=True); self._watchdog.start()

    def _watch(self) -> None:
        assert self.heartbeat_deadline_ms is not None
        interval = max(0.001, min(self.heartbeat_deadline_ms / 4000, 0.25))
        while not self._terminal:
            time.sleep(interval)
            if self.supervisor.expire_if_stale(self.now_ms(), self.heartbeat_deadline_ms) != "running":
                # expire_if_stale owns the controller kill; do not invoke it a
                # second time while recording the terminal failure.
                self._fail("heartbeat_expired", "worker heartbeat deadline exceeded", kill_scope=False)
                return

    def _serve(self) -> None:
        try:
            while True:
                frame = validate_frame(decode_frame(self.process.process.stdout), run_id=self.run_id, nonce=self.nonce)
                if frame["type"] == "terminal":
                    self._terminal = True; return
                if frame["type"] == "heartbeat":
                    self.supervisor.heartbeat(self.now_ms()); continue
                if frame["type"] != "submit_native_graph_proposal": raise ProtocolError("agent protocol direction")
                # Never convert a worker-selected opaque identifier into a
                # proposal. The candidate itself is provenance-checked against
                # the evaluator-attested canonical native export.
                reply = self.projector.submit_native_proposal(frame["proposal"])
                # A receipt publication failure is terminal before a worker can
                # receive another capability result or send more work.
                terminal = self.runtime_record.read()
                if terminal is not None:
                    self._fail("receipt_append_failed", terminal["error"])
                    return
                outcome = observed_outcome(self.receipt_log.last_receipt, reply)
                write_frame(self.process.process.stdin, {"schema": SCHEMA, "type": "reply", "run_id": self.run_id, "session_nonce": self.nonce,
                                                         "correlation_id": frame["correlation_id"], "reply": reply.as_dict(), "outcome": outcome.as_dict()})
        except EOFError as exc:
            # A clean worker terminal is the only permitted EOF.
            if not self._terminal:
                exit_code = self.process.process.poll()
                self._fail("sandbox_worker_exit" if exit_code not in (None, 0) else "sandbox_protocol_eof", exc)
        except Exception as exc:
            self._fail("sandbox_protocol_violation", exc)

    def stop(self, reason: str = "sandbox_killed") -> None:
        self._fail(reason, reason)
        if self._thread: self._thread.join(timeout=2)
        if self._watchdog: self._watchdog.join(timeout=2)


class EvaluationActionClient:
    """Removed public in-parent client retained only as a fail-closed API stub."""
    def submit_native_graph_proposal(self, proposal: dict) -> BrokerReply:
        raise ProtocolError("P0 actions are available only to the isolated worker")
    def observed_outcome(self, reply: BrokerReply) -> ObservedGraphActionOutcomeV1:
        return ObservedGraphActionOutcomeV1(proposal_digest=None, phase=reply.phase, reason_code=None,
                                            request_hash=None, signed_receipt_hash=None,
                                            receipt_sequence=reply.receipt_sequence_or_null)


@dataclass(frozen=True)
class SandboxedEvaluationRun:
    """Host-side lifecycle view. It intentionally exposes no action capability."""
    manifest: object
    run_paths: RunPaths
    _server: _HostProtocolServer

    @property
    def terminal(self) -> bool: return self._server._terminal
    def stop(self, reason: str = "sandbox_killed") -> None: self._server.stop(reason)
    def wait(self, timeout: float | None = None) -> int | None: return self._server.process.process.wait(timeout=timeout)


def _agent_spec(value: object) -> SandboxSpec:
    if not isinstance(value, SandboxSpec): raise SandboxPolicyUnavailable("sandbox_policy_unavailable: staged agent specification")
    return value


@contextmanager
def evaluation_mode(*, manifest_verifier, manifest: dict, expected_digests: dict, grant_keys: dict,
                    receipt_log, native_graph_export: bytes, native_graph_export_attestation: dict | None = None,
                    native_export_attestation_keys: dict | None = None, supervisor=None, now_ms=None, reporter=None,
                    grant_resolver=None, launch_failure_record=None, runtime_failure_record=None,
                    allow_fixture_methods: bool = False, fixture_registry: bool = False,
                    agent_spec: SandboxSpec | None = None, sandbox_launcher: BwrapSandboxLauncher | None = None,
                    control_root: Path | None = None, heartbeat_deadline_ms: int | None = None):
    """Launch only a verified staged worker; unavailable isolation fails closed.

    The previous ``fork``/``Pipe`` P0 implementation has intentionally been
    removed. A call that omits a verified sandbox specification or launcher is
    a terminal launch denial, not a local compatibility execution.
    """
    clock = now_ms or (lambda: int(time.time() * 1000))
    contexts = {"manifest_candidate_hash": _context_hash(manifest), "expected_digests_hash": _context_hash(expected_digests),
                "native_graph_export_hash": _context_hash(native_graph_export), "receipt_log_configuration_hash": _context_hash({"manifest_hash": getattr(receipt_log, "manifest_hash", None), "broker_image_digest": getattr(receipt_log, "broker_image_digest", None), "input_digest": getattr(receipt_log, "input_digest", None)})}
    try:
        attempt = LaunchAttemptPaths.create(control_root or (Path(receipt_log.root) / "control-plane"))
        failure = launch_failure_record or LaunchFailureRecord.for_attempt_paths(attempt, receipt_log, now_ms=clock)
    except Exception as exc:
        raise ProtocolError("launch failure authority unavailable") from exc

    def launch_failure(reason: str, verified=None) -> None:
        observed = getattr(receipt_log, "manifest_hash", None)
        # A verified, bound receipt chain is permitted to receipt a denied start.
        if verified is not None and observed == verified.manifest_hash:
            try:
                receipt_log.sequence, receipt_log.previous = receipt_log.validate()
                receipt_log.append(run_id=verified.run_id, outcome="impasse", reason_code=reason); return
            except Exception: reason = "receipt_log_untrusted"
        failure.record(run_id=None if verified is None else verified.run_id,
                       verified_manifest_hash=None if verified is None else verified.manifest_hash,
                       observed_receipt_log_manifest_hash=observed if isinstance(observed, str) and observed.startswith("sha256:") else None,
                       reason_code=reason, context_hashes=contexts)

    try:
        verified = manifest_verifier.verify(manifest, expected_digests=expected_digests, allow_fixture_methods=allow_fixture_methods)
    except Exception as exc:
        launch_failure(_manifest_failure_reason(exc)); raise ProtocolError("evaluation manifest rejected") from exc
    if not verified.local_harness_only:
        launch_failure("unsupported_launcher_authority", verified); raise ProtocolError("this launcher only supports local P0-A approximation")
    if fixture_registry and not allow_fixture_methods:
        launch_failure("fixture_registry_policy_violation", verified); raise ProtocolError("fixture registry requires explicit fixture manifest mode")
    if receipt_log.manifest_hash != verified.manifest_hash:
        launch_failure("receipt_log_manifest_mismatch", verified); raise ProtocolError("receipt log manifest mismatch")
    try:
        paths = RunPaths.for_verified_run(control_root or (Path(receipt_log.root) / "control-plane"), run_id=verified.run_id, verified_manifest_hash=verified.manifest_hash)
        if Path(receipt_log.root) != paths.receipts_root:
            raise ProtocolError("receipt log is not evaluator-owned run path")
        runtime = runtime_failure_record or RuntimeFailureRecord.for_run_paths(paths, receipt_log, now_ms=clock)
        existing = runtime.read()
        if existing is not None: raise ProtocolError("terminal runtime failure")
        NativeGraphExportAttestationVerifier(native_export_attestation_keys or {}, now_ms=clock).verify(native_graph_export, native_graph_export_attestation, run_id=verified.run_id, agent_build_digest=verified.body["agent_build_digest"], control_plane_digest=verified.body["control_plane_digest"], input_snapshot_digest=verified.body["input_snapshot_digest"])
        provenance = NativeGraphProvenanceVerifier(native_graph_export, run_id=verified.run_id, input_snapshot_digest=verified.body["input_snapshot_digest"], now_ms=clock,
                                                   native_attestation_digest=sha256(canonical_bytes(native_graph_export_attestation)))
    except Exception as exc:
        launch_failure("invalid_native_graph_export" if not isinstance(exc, ProtocolError) or "terminal runtime failure" not in str(exc) else "run_terminal_runtime_failure", verified)
        raise ProtocolError("evaluation prelaunch rejected") from exc
    try:
        spec = _agent_spec(agent_spec)
        if sandbox_launcher is None: raise SandboxUnavailable("sandbox_unavailable: launcher absent")
        sandbox_launcher.preflight(spec)
    except SandboxPolicyUnavailable as exc:
        launch_failure("sandbox_policy_unavailable", verified); raise ProtocolError("sandbox isolation policy unavailable") from exc
    except SandboxUnavailable as exc:
        launch_failure("sandbox_unavailable", verified); raise ProtocolError("sandbox isolation unavailable") from exc
    scope = None
    try:
        if heartbeat_deadline_ms is not None and (not isinstance(heartbeat_deadline_ms, int) or heartbeat_deadline_ms <= 0):
            raise ValueError("heartbeat deadline invalid")
        # The evaluator creates a run-bound scope before any worker exec.  The
        # launcher can only invoke scope.spawn(), whose implementation must
        # atomically place the child in this killable scope.
        scope = sandbox_launcher.controller.create_scope(verified.run_id)
        if scope.run_id != verified.run_id:
            raise ValueError("scope run binding")
        if supervisor is None:
            supervisor = CgroupSupervisor(verified.run_id, scope)
        if not isinstance(supervisor, CgroupSupervisor) or supervisor.control.run_id != verified.run_id:
            raise ValueError("supervisor run binding")
        if supervisor.scope is not scope:
            raise ValueError("supervisor scope binding")
    except Exception as exc:
        if scope is not None:
            try: scope.kill("sandbox_start_failed")
            except Exception: pass
        launch_failure("supervisor_policy_unavailable", verified)
        raise ProtocolError("sandbox supervisor policy unavailable") from exc
    try:
        broker = ActionBroker(verified, grant_keys=grant_keys, receipt_log=receipt_log, now_ms=clock, control=None,
                              fixture_registry=fixture_registry, runtime_failure_record=runtime,
                              graph_binding_verifier=provenance.validates_binding)
        process = sandbox_launcher.start(spec, scope)
        server = _HostProtocolServer(process, broker=broker, provenance=provenance, grant_resolver=grant_resolver,
                                     run_id=verified.run_id, runtime_record=runtime, receipt_log=receipt_log, now_ms=clock,
                                     supervisor=supervisor, heartbeat_deadline_ms=heartbeat_deadline_ms)
        server.start()
    except SandboxStartFailed as exc:
        launch_failure("sandbox_start_failed", verified); raise ProtocolError("sandbox worker start failed") from exc
    except Exception as exc:
        # A controller scope can exist even when broker construction fails;
        # close that precreated scope rather than leaving evaluator resources
        # allocated after a denied start.
        if scope is not None:
            try: scope.kill("sandbox_start_failed")
            except Exception: pass
        launch_failure("sandbox_start_failed", verified); raise ProtocolError("sandbox worker start failed") from exc
    run = SandboxedEvaluationRun(verified, paths, server)
    try:
        # Host caller has status only; evaluated code is in the worker.
        with activated(reporter=reporter), intercept_legacy_process_io(): yield run
    finally:
        if process.process.poll() is None: server.stop("sandbox_killed")
        try: receipt_log.sequence, receipt_log.previous = receipt_log.validate()
        except Exception as exc:
            runtime.record(run_id=verified.run_id, verified_manifest_hash=verified.manifest_hash,
                           last_valid_receipt_sequence=receipt_log.sequence, last_valid_receipt_hash=receipt_log.previous,
                           reason_code="receipt_append_failed", error=exc)
