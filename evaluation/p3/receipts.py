"""Evaluator-owned append-only P3 denial, result, and rollback seals."""
from __future__ import annotations
import fcntl, os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from evaluation.p0a.canonical import canonical_bytes, object_hash, parse_canonical, sign, verify_signature
from .protocol import P3ProtocolError, is_digest

_BINDING_KEYS = {"p0_go_digest", "p1_go_digest", "p2_go_digest", "native_export_digest", "candidate_digest", "pre_snapshot_digest"}

@dataclass
class P3ReceiptLog:
    root: Path; signer: Any; previous: str|None=field(init=False,default=None); sequence:int=field(init=False,default=0)
    def __post_init__(self):
        self.root=Path(self.root); self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        if self.root.is_symlink() or not self.root.is_dir(): raise P3ProtocolError("receipt root")
        self.reload()
    @property
    def public_key(self): return self.signer.public_key() if hasattr(self.signer,"public_key") else self.signer
    def _validate_payload(self, kind: str, payload: dict[str, Any]) -> None:
        if kind == "containment":
            required={"schema","lock_digest","worker_image_digest","seccomp_digest","status","attempts","probe_digest","mounts"}
            attempts={"direct_control_plane_mutation","transitive_control_plane_mutation","host_io","replay_order","rollback_restore"}
            if (set(payload) != required or payload.get("schema") != "P3WorkerContainmentEvidenceV1"
                    or payload.get("status") != "contained" or set(payload.get("attempts", {})) != attempts
                    or set(payload["attempts"].values()) != {"blocked"}
                    or any(not is_digest(payload.get(field)) for field in ("lock_digest", "worker_image_digest", "seccomp_digest", "probe_digest"))
                    or not isinstance(payload.get("mounts"), dict) or set(payload["mounts"]) != {"agent", "input"}):
                raise P3ProtocolError("containment evidence")
        elif kind == "terminal":
            required={"lock_digest","proposal_digest","outcome","reason","control_digests","snapshot_digest","release_bindings","terminal_evidence"}
            evidence={"schema","lock_digest","run_id","task_digest","sequence","reason","evidence_digest"}
            terminal=payload.get("terminal_evidence")
            if (set(payload) != required or not isinstance(terminal, dict) or set(terminal) != evidence
                    or terminal.get("schema") != "P3EnvelopeTerminalEvidenceV1" or terminal.get("lock_digest") != payload.get("lock_digest")
                    or not isinstance(terminal.get("run_id"), str) or not is_digest(terminal.get("task_digest"))
                    or type(terminal.get("sequence")) is not int or not isinstance(terminal.get("reason"), str)
                    or terminal.get("evidence_digest") != object_hash(terminal, "evidence_digest")):
                raise P3ProtocolError("terminal envelope evidence")

    def reload(self):
        previous=None; sequence=0
        for number,path in enumerate(sorted(self.root.glob("*.json")),1):
            try: body=parse_canonical(path.read_bytes())
            except Exception as exc: raise P3ProtocolError("receipt canonical") from exc
            needed={"schema","sequence","previous_hash","kind","payload","receipt_hash","signature"}
            if set(body)!=needed or body["schema"]!="P3ReceiptV1" or body["sequence"]!=number or body["previous_hash"]!=previous: raise P3ProtocolError("receipt chain")
            if body["kind"] not in {"denial","pair","containment","terminal","result","rollback","impasse"} or not isinstance(body["payload"],dict): raise P3ProtocolError("receipt payload")
            self._validate_payload(body["kind"], body["payload"])
            if body["receipt_hash"]!=object_hash(body,"receipt_hash","signature"): raise P3ProtocolError("receipt hash")
            try: verify_signature(body,self.public_key,"receipt_hash")
            except Exception as exc: raise P3ProtocolError("receipt signature") from exc
            previous=body["receipt_hash"]; sequence=number
        self.previous,self.sequence=previous,sequence
    def append(self,kind:str,payload:dict[str,Any])->dict[str,Any]:
        if kind not in {"denial","pair","containment","terminal","result","rollback","impasse"} or not isinstance(payload,dict): raise P3ProtocolError("receipt payload")
        self._validate_payload(kind, payload)
        fd=os.open(self.root/".append.lock",os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX); self.reload(); body={"schema":"P3ReceiptV1","sequence":self.sequence+1,"previous_hash":self.previous,"kind":kind,"payload":payload}; body["receipt_hash"]=object_hash(body); body["signature"]=sign(body,self.signer,"receipt_hash"); target=self.root/f"{body['sequence']:06d}.json"; out=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o400)
            try: os.write(out,canonical_bytes(body)); os.fsync(out)
            finally: os.close(out)
            self.previous,self.sequence=body["receipt_hash"],body["sequence"]; return body
        finally: fcntl.flock(fd,fcntl.LOCK_UN); os.close(fd)

def receipt_payload(*,lock_digest:str|None,proposal_digest:str|None,outcome:str,reason:str,control_digests:dict[str,str],snapshot_digest:str|None=None,release_bindings:dict[str,str]|None=None)->dict[str,Any]:
    if lock_digest is not None and not is_digest(lock_digest): raise P3ProtocolError("lock digest")
    if proposal_digest is not None and not is_digest(proposal_digest): raise P3ProtocolError("proposal digest")
    if any(not is_digest(v) for v in control_digests.values()): raise P3ProtocolError("control digest")
    if release_bindings is not None and (set(release_bindings)!=_BINDING_KEYS or any(not is_digest(v) for v in release_bindings.values())): raise P3ProtocolError("release bindings")
    return {"lock_digest":lock_digest,"proposal_digest":proposal_digest,"outcome":outcome,"reason":reason,"control_digests":dict(control_digests),"snapshot_digest":snapshot_digest,"release_bindings":None if release_bindings is None else dict(release_bindings)}
