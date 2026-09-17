"""Evaluator-owned finite P3 release closure and tracked staging index."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Mapping

from evaluation.p0a.canonical import canonical_bytes, object_hash, parse_canonical
from .lock import ARTIFACT_NAMES, P3ReleaseLockV1
from .protocol import P3ProtocolError, is_digest

# OCI objects have no host file path; every other lock artifact must be an ordinary
# file below the evaluator-owned closure root.  The index commits both cases.
_IMAGE_ARTIFACTS=frozenset({"broker_image","policy_authority_image","receipt_writer_image","native_worker","native_evaluator_image"})


def _file_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file(): raise P3ProtocolError("P3 staged artifact unavailable")
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        digest=hashlib.sha256()
        while block:=os.read(fd,65536): digest.update(block)
    finally: os.close(fd)
    return "sha256:"+digest.hexdigest()


def write_staging_index(*, root: Path, lock: P3ReleaseLockV1, artifacts: Mapping[str, Path | str]) -> Path:
    """Write a canonical, lock-bound, finite closure index without fetching anything."""
    root=Path(root)
    if root.is_symlink() or not root.is_dir(): raise P3ProtocolError("P3 closure root")
    root=root.resolve(strict=True)
    if set(artifacts)!=set(ARTIFACT_NAMES): raise P3ProtocolError("P3 closure completeness")
    entries=[]
    for name in ARTIFACT_NAMES:
        expected=lock.artifacts[name]; artifact=artifacts[name]
        if name in _IMAGE_ARTIFACTS:
            if artifact!=expected or not is_digest(artifact): raise P3ProtocolError("P3 closure image")
            entries.append({"name":name,"digest":expected,"kind":"image","path":None}); continue
        if not isinstance(artifact,Path): raise P3ProtocolError("P3 staged artifact")
        path=artifact
        if path.is_symlink() or not path.is_file(): raise P3ProtocolError("P3 staged artifact")
        path=path.resolve(strict=True)
        if root not in path.parents or _file_digest(path)!=expected: raise P3ProtocolError("P3 staged artifact digest")
        entries.append({"name":name,"digest":expected,"kind":"file","path":str(path.relative_to(root))})
    index={"schema":"P3ArtifactStagingIndexV1","lock_digest":lock.digest,"entries":entries}
    index["index_digest"]=object_hash(index)
    target=root/"p3-artifact-staging-index.json"
    if target.exists() or target.is_symlink(): raise P3ProtocolError("P3 staging index exists")
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    try: os.write(fd,canonical_bytes(index)); os.fsync(fd)
    finally: os.close(fd)
    return target


def validate_staging_index(path: Path, *, root: Path, lock: P3ReleaseLockV1) -> dict[str, Any]:
    root=Path(root)
    if root.is_symlink() or not root.is_dir(): raise P3ProtocolError("P3 closure root")
    root=root.resolve(strict=True)
    try:
        raw=Path(path).read_bytes(); index=parse_canonical(raw)
    except Exception as exc: raise P3ProtocolError("P3 staging index") from exc
    if canonical_bytes(index)!=raw or not isinstance(index,dict) or set(index)!={"schema","lock_digest","entries","index_digest"} or index.get("schema")!="P3ArtifactStagingIndexV1" or index.get("lock_digest")!=lock.digest or index.get("index_digest")!=object_hash(index,"index_digest") or not isinstance(index.get("entries"),list) or len(index["entries"])!=len(ARTIFACT_NAMES): raise P3ProtocolError("P3 staging index")
    seen=set()
    for entry in index["entries"]:
        if not isinstance(entry,dict) or set(entry)!={"name","digest","kind","path"} or entry["name"] not in ARTIFACT_NAMES or entry["name"] in seen or entry["digest"]!=lock.artifacts[entry["name"]]: raise P3ProtocolError("P3 staging index entry")
        seen.add(entry["name"])
        if entry["name"] in _IMAGE_ARTIFACTS:
            if entry["kind"]!="image" or entry["path"] is not None: raise P3ProtocolError("P3 staging image")
        else:
            if entry["kind"]!="file" or not isinstance(entry["path"],str): raise P3ProtocolError("P3 staging file")
            candidate=(root/entry["path"])
            if candidate.is_symlink() or root not in candidate.resolve(strict=True).parents or _file_digest(candidate)!=entry["digest"]: raise P3ProtocolError("P3 staging digest")
    if seen!=set(ARTIFACT_NAMES): raise P3ProtocolError("P3 staging completeness")
    return index
