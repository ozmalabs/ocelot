"""Finite P3 worker/evaluator transport; no in-process execution callback exists here.

The worker receives one evaluator-signed next-task envelope through stdin and only
sees the immutable staged candidate through a read-only mount.  Its response is
bounded.  A separate evaluator executable owns verification, scoring, and the
signature over each canonical pair record.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, object_hash, verify_signature
from .lock import THRESHOLDS
from .protocol import P3ProtocolError, is_digest

MAX_FRAME_BYTES = 64 * 1024
_ATTEMPTS = ("direct_control_plane_mutation", "transitive_control_plane_mutation", "host_io", "replay_order", "rollback_restore")


class P3ExecutionFailure(P3ProtocolError):
    """Fixed failure classes only; container diagnostics are never released."""


@dataclass(frozen=True)
class P3PodmanSpec:
    image_digest: str
    worker_binary: Path
    agent_root: Path
    input_root: Path
    seccomp_profile: Path
    seccomp_digest: str
    work_root: Path
    staging_root: Path
    uid_gid: str = "65532:65532"
    podman_path: str = "podman"
    entrypoint: str = "/runtime/p3_worker"

    def validate(self) -> None:
        if not is_digest(self.image_digest) or self.uid_gid != "65532:65532":
            raise P3ExecutionFailure("p3 worker identity")
        if self.entrypoint not in {"/runtime/p3_worker", "/runtime/p3_probe"}:
            raise P3ExecutionFailure("p3 worker entrypoint")
        root = Path(self.staging_root)
        if root.is_symlink() or not root.is_dir():
            raise P3ExecutionFailure("p3 staging root")
        root = root.resolve(strict=True)
        resolved: dict[str, Path] = {}
        for label, raw in (("worker", self.worker_binary), ("agent", self.agent_root), ("input", self.input_root), ("seccomp", self.seccomp_profile), ("work", self.work_root)):
            path = Path(raw)
            if path.is_symlink() or not path.exists():
                raise P3ExecutionFailure(f"p3 {label} staging")
            path = path.resolve(strict=True)
            if path == root or root not in path.parents:
                raise P3ExecutionFailure(f"p3 {label} escapes staging")
            resolved[label] = path
        if not resolved["worker"].is_file() or not os.access(resolved["worker"], os.X_OK):
            raise P3ExecutionFailure("p3 worker binary")
        candidate = resolved["agent"] / "candidate.bin"
        if candidate.is_symlink() or not candidate.is_file():
            raise P3ExecutionFailure("p3 staged candidate")
        if set(path.name for path in resolved["agent"].iterdir()) != {resolved["worker"].name, "candidate.bin"}:
            raise P3ExecutionFailure("p3 agent closure")
        if (not resolved["agent"].is_dir() or not resolved["input"].is_dir()
                or not resolved["work"].is_dir() or not resolved["seccomp"].is_file()
                or resolved["worker"].parent != resolved["agent"] or resolved["agent"] == resolved["input"]):
            raise P3ExecutionFailure("p3 staging layout")
        actual = "sha256:" + hashlib.sha256(resolved["seccomp"].read_bytes()).hexdigest()
        if actual != self.seccomp_digest:
            raise P3ExecutionFailure("p3 seccomp digest")


class P3PodmanLauncher:
    """P2/P0-equivalent rootless, no-network, read-only local-only launch policy."""
    def executable(self, spec: P3PodmanSpec) -> str:
        candidate = shutil.which(spec.podman_path) if os.path.sep not in spec.podman_path else spec.podman_path
        if not candidate or not os.access(candidate, os.X_OK):
            raise P3ExecutionFailure("podman unavailable")
        return candidate

    def preflight(self, spec: P3PodmanSpec) -> None:
        spec.validate(); executable = self.executable(spec)
        try:
            rootless = subprocess.run([executable, "info", "--format", "{{.Host.Security.Rootless}}"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2, check=False, close_fds=True, env={"PATH": os.environ.get("PATH", "")})
            image = subprocess.run([executable, "image", "inspect", "--format", "{{.Id}}", spec.image_digest], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2, check=False, close_fds=True, env={"PATH": os.environ.get("PATH", "")})
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise P3ExecutionFailure("podman preflight") from exc
        if rootless.returncode or rootless.stdout.strip().lower() != b"true":
            raise P3ExecutionFailure("rootless Podman required")
        if image.returncode or image.stdout.strip().decode("ascii", "ignore") not in {spec.image_digest, spec.image_digest[7:]}:
            raise P3ExecutionFailure("digest-pinned local P3 image unavailable")

    def argv(self, spec: P3PodmanSpec) -> list[str]:
        spec.validate()
        # Keep P2/P0 hardening: no pulls/network/socket/mutable host mounts/caps,
        # fixed non-root identity, no privilege gain, seccomp, and bounded tmpfs I/O.
        return [spec.podman_path, "run", "--rm", "--interactive", "--pull=never", "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", f"--security-opt=seccomp={Path(spec.seccomp_profile).resolve(strict=True)}", f"--user={spec.uid_gid}", "--pids-limit=32", "--memory=4g", "--cpus=1", "--tmpfs=/work:rw,noexec,nosuid,nodev,size=64k", f"--volume={Path(spec.agent_root).resolve(strict=True)}:/agent:ro,nosuid,nodev,noexec", f"--volume={Path(spec.input_root).resolve(strict=True)}:/input:ro,nosuid,nodev,noexec", "--workdir=/work", "--env=HOME=/work", "--env=PATH=/agent", "--env=LANG=C.UTF-8", spec.image_digest, spec.entrypoint]

    def exchange(self, spec: P3PodmanSpec, request: bytes) -> tuple[bytes, int]:
        if len(request) > MAX_FRAME_BYTES:
            raise P3ExecutionFailure("p3 input frame bound")
        self.preflight(spec)
        try:
            process = subprocess.Popen(self.argv(spec), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, close_fds=True, env={"PATH": os.environ.get("PATH", "")}, start_new_session=True)
            try:
                stdout, _ = process.communicate(request, timeout=THRESHOLDS["wall_seconds"])
            except subprocess.TimeoutExpired as exc:
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.communicate(); raise P3ExecutionFailure("p3 worker timeout") from exc
        except OSError as exc:
            raise P3ExecutionFailure("p3 worker launch") from exc
        if len(stdout) > MAX_FRAME_BYTES or process.returncode != 0:
            raise P3ExecutionFailure("p3 worker execution")
        return stdout, process.returncode


def _tree_commitment(root: Path) -> str:
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise P3ExecutionFailure("p3 probe mount")
    entries=[]
    for path in sorted(root.rglob("*")):
        if path.is_symlink(): raise P3ExecutionFailure("p3 probe symlink")
        if path.is_dir(): entries.append({"path":str(path.relative_to(root)),"kind":"dir","digest":""})
        elif path.is_file(): entries.append({"path":str(path.relative_to(root)),"kind":"file","digest":"sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()})
        else: raise P3ExecutionFailure("p3 probe mount type")
    return object_hash({"entries":entries})


class P3WorkerClient:
    """Worker boundary with an evaluator-keyed, one-time release ledger."""
    def __init__(self, spec: P3PodmanSpec, *, task_release_keys: Mapping[str, Any] | None = None,
                 launcher: P3PodmanLauncher | None = None):
        self.spec, self.launcher = spec, launcher or P3PodmanLauncher()
        self.task_release_keys = dict(task_release_keys or {})
        self.release_ledger: Any = None

    def bind_task_release(self, *, lock_digest: str, run_id: str) -> None:
        from .study import TaskReleaseLedger
        if not self.task_release_keys: raise P3ExecutionFailure("P3 worker task authority unavailable")
        self.release_ledger = TaskReleaseLedger(self.task_release_keys, lock_digest, run_id)

    def execute_next(self, envelope: Mapping[str, Any], *, candidate_digest: str) -> dict[str, Any]:
        if not is_digest(candidate_digest) or self.release_ledger is None:
            raise P3ExecutionFailure("sealed P3 task")
        try:
            sealed = self.release_ledger.consume(envelope)
        except P3ProtocolError as exc:
            raise P3ExecutionFailure("P3 worker task envelope") from exc
        candidate=Path(self.spec.agent_root) / "candidate.bin"
        if candidate.is_symlink() or not candidate.is_file() or "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest() != candidate_digest:
            raise P3ExecutionFailure("P3 staged candidate binding")
        input_root=Path(self.spec.input_root)
        if input_root.is_symlink() or not input_root.is_dir(): raise P3ExecutionFailure("P3 sealed input")
        task=input_root / "next-task.json"
        entries=list(input_root.iterdir())
        if any(path.name != "next-task.json" or path.is_symlink() or not path.is_file() for path in entries): raise P3ExecutionFailure("P3 sealed input closure")
        if task.exists(): os.unlink(task)
        raw=canonical_bytes(sealed)
        fd=os.open(task, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o400)
        try: os.write(fd,raw); os.fsync(fd)
        finally: os.close(fd)
        request={"schema":"P3WorkerRequestV1", "sealed_task_digest":sealed["task_digest"]}
        stdout, _ = self.launcher.exchange(self.spec, canonical_bytes(request))
        try: output=json.loads(stdout)
        except (TypeError, ValueError, json.JSONDecodeError) as exc: raise P3ExecutionFailure("P3 worker response") from exc
        required={"schema","task_digest","candidate_digest","candidate_evidence","worker_output_digest"}
        if (not isinstance(output,dict) or set(output)!=required or output.get("schema")!="P3WorkerOutputV1"
                or output.get("task_digest")!=sealed["task_digest"] or output.get("candidate_digest")!=candidate_digest
                or not isinstance(output.get("candidate_evidence"),dict) or not is_digest(output.get("worker_output_digest"))):
            raise P3ExecutionFailure("P3 worker response")
        if output["worker_output_digest"] != object_hash({key:value for key,value in output.items() if key != "worker_output_digest"}):
            raise P3ExecutionFailure("P3 worker digest")
        if len(canonical_bytes(output)) > MAX_FRAME_BYTES: raise P3ExecutionFailure("P3 worker output bound")
        return output

    def adversarial_probe(self, *, lock_digest: str) -> dict[str, Any]:
        if not is_digest(lock_digest): raise P3ExecutionFailure("P3 containment lock")
        before={"agent":_tree_commitment(self.spec.agent_root),"input":_tree_commitment(self.spec.input_root)}
        probe=replace(self.spec, entrypoint="/runtime/p3_probe")
        request={"schema":"P3WorkerAdversarialProbeV1", "lock_digest":lock_digest, "attempts":list(_ATTEMPTS)}
        stdout, _ = self.launcher.exchange(probe, canonical_bytes(request))
        try: report=json.loads(stdout)
        except (TypeError, ValueError, json.JSONDecodeError) as exc: raise P3ExecutionFailure("P3 adversarial probe") from exc
        after={"agent":_tree_commitment(self.spec.agent_root),"input":_tree_commitment(self.spec.input_root)}
        expected={"schema":"P3WorkerAdversarialProbeReportV1","status":"contained","attempts":{name:"blocked" for name in _ATTEMPTS}}
        if not isinstance(report,dict) or report != expected or after != before:
            raise P3ExecutionFailure("P3 adversarial probe")
        return {"schema":"P3WorkerContainmentEvidenceV1","lock_digest":lock_digest,"worker_image_digest":self.spec.image_digest,
                "seccomp_digest":self.spec.seccomp_digest,"status":"contained","attempts":report["attempts"],
                "probe_digest":object_hash(report),"mounts":{key:{"before":before[key],"after":after[key]} for key in before}}


class P3EvaluatorClient:
    """Independent evaluator release ledger; it will not parse an unauthenticated task."""
    def __init__(self, binary: Path, *, public_key: Any, task_release_keys: Mapping[str, Any] | None = None):
        self.binary=Path(binary); self.public_key=public_key; self.task_release_keys=dict(task_release_keys or {}); self.release_ledger: Any = None
        if self.binary.is_symlink() or not self.binary.is_file() or not os.access(self.binary,os.X_OK): raise P3ExecutionFailure("P3 evaluator unavailable")
        self.binary=self.binary.resolve(strict=True)

    def bind_task_release(self, *, lock_digest: str, run_id: str) -> None:
        from .study import TaskReleaseLedger
        if not self.task_release_keys: raise P3ExecutionFailure("P3 evaluator task authority unavailable")
        self.release_ledger = TaskReleaseLedger(self.task_release_keys, lock_digest, run_id)

    def evaluate(self, *, lock_digest: str, envelope: Mapping[str, Any], worker_output: Mapping[str, Any], candidate_digest: str, pre_snapshot_digest: str) -> dict[str, Any]:
        if self.release_ledger is None: raise P3ExecutionFailure("P3 evaluator task authority unavailable")
        try:
            sealed = self.release_ledger.consume(envelope)
        except P3ProtocolError as exc:
            raise P3ExecutionFailure("P3 evaluator task envelope") from exc
        request={"schema":"P3EvaluatorRequestV1","lock_digest":lock_digest,"envelope":sealed,"worker_output":dict(worker_output),"candidate_digest":candidate_digest,"pre_snapshot_digest":pre_snapshot_digest}
        try:
            completed=subprocess.run([str(self.binary)],input=canonical_bytes(request),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=THRESHOLDS["wall_seconds"],check=False,close_fds=True,env={"PATH":""})
            if completed.returncode or len(completed.stdout)>MAX_FRAME_BYTES: raise ValueError("evaluator exit")
            evidence=json.loads(completed.stdout)
        except (OSError, ValueError, TypeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc: raise P3ExecutionFailure("P3 evaluator failure") from exc
        return validate_pair_evidence(evidence, public_key=self.public_key, lock_digest=lock_digest, envelope=sealed, candidate_digest=candidate_digest, pre_snapshot_digest=pre_snapshot_digest)


def validate_pair_evidence(value: Mapping[str, Any], *, public_key: Any, lock_digest: str, envelope: Mapping[str, Any], candidate_digest: str, pre_snapshot_digest: str) -> dict[str, Any]:
    required={"schema","key_id","lock_digest","task_digest","pair_id","sequence","candidate_digest","pre_snapshot_digest","post_snapshot_digest","arms","safety_ok","resource_ledger","retention_delta","transfer_delta","worker_output_digest","receipt_hashes","evidence_digest","signature"}
    if not isinstance(value,Mapping) or set(value)!=required or value.get("schema")!="P3PairEvidenceV1": raise P3ProtocolError("pair evidence schema")
    for field, expected in (("lock_digest",lock_digest),("task_digest",envelope.get("task_digest")),("pair_id",envelope.get("pair_id")),("sequence",envelope.get("sequence")),("candidate_digest",candidate_digest),("pre_snapshot_digest",pre_snapshot_digest)):
        if value.get(field)!=expected or (field not in {"pair_id", "sequence"} and not is_digest(value.get(field))): raise P3ProtocolError("pair evidence binding")
    if not is_digest(value.get("post_snapshot_digest")) or not is_digest(value.get("worker_output_digest")) or not isinstance(value.get("key_id"),str): raise P3ProtocolError("pair evidence digest")
    if not isinstance(value.get("arms"),dict) or set(value["arms"])!={"governed","frozen","reset_memory","no_consolidation"}: raise P3ProtocolError("pair evidence arms")
    if type(value.get("safety_ok")) is not bool or not isinstance(value.get("resource_ledger"),dict) or set(value["resource_ledger"])!=set(value["arms"]): raise P3ProtocolError("pair evidence scoring")
    if (type(value.get("retention_delta")) is not int or type(value.get("transfer_delta")) is not int
            or not -100000 <= value["retention_delta"] <= 100000 or not -100000 <= value["transfer_delta"] <= 100000): raise P3ProtocolError("pair evidence deltas")
    fields={"cpu_count","memory_bytes","wall_seconds","graph_transactions","network_bytes"}
    for arm, record in value["arms"].items():
        if not isinstance(record,dict) or set(record)!={"score","status"} or type(record["score"]) is not int or not 0<=record["score"]<=100000 or record["status"] not in {"ok","failure"}: raise P3ProtocolError("pair evidence arms")
        ledger=value["resource_ledger"][arm]
        if not isinstance(ledger,dict) or set(ledger)!=fields or any(type(ledger[k]) is not int or not 0<=ledger[k]<=THRESHOLDS[k] for k in fields): raise P3ProtocolError("pair evidence ledger")
    if not isinstance(value.get("receipt_hashes"),dict) or set(value["receipt_hashes"])!={"worker","evaluator"} or any(not is_digest(item) for item in value["receipt_hashes"].values()): raise P3ProtocolError("pair evidence receipts")
    expected=object_hash({key:item for key,item in value.items() if key not in {"evidence_digest","signature"}})
    if value.get("evidence_digest")!=expected: raise P3ProtocolError("pair evidence digest")
    try: verify_signature(dict(value),public_key,"evidence_digest")
    except Exception as exc: raise P3ProtocolError("pair evidence signature") from exc
    return dict(value)
