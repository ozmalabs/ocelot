from __future__ import annotations

from evaluation.p0a.canonical import canonical_bytes
from evaluation.p2.runtime import validate_runtime_closure


def test_runtime_manifest_binds_worker_and_explicit_loader(tmp_path):
    worker_digest = "sha256:" + "b" * 64
    manifest = {"schema": "P2NativeRuntimeClosureV1", "binary_digest": worker_digest,
                "interpreter": "/lib64/ld-linux-x86-64.so.2", "files": [
                    {"path": "/lib64/ld-linux-x86-64.so.2", "digest": "sha256:" + "a" * 64,
                     "elf_class": 2, "elf_machine": 62},
                    {"path": "/lib/libc.so.6", "digest": "sha256:" + "c" * 64,
                     "elf_class": 2, "elf_machine": 62},
                ], "support_files": [{"path": "/etc/ld.so.cache", "digest": "sha256:" + "d" * 64}]}
    target = tmp_path / "closure.json"; target.write_bytes(canonical_bytes(manifest))
    assert validate_runtime_closure(target, worker_digest=worker_digest)["interpreter"] == manifest["interpreter"]
