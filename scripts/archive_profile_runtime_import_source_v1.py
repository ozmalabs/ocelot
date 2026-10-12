#!/usr/bin/env python3
"""Archive the exact source/seed/native inputs for profile import observation v1."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
LOCK = ROOT / "evaluation/substrate_capability/profile_runtime_import_observation_v1_lock_20260928.json"
ARCHIVE = ROOT / "evaluation/substrate_capability/source_bundles/profile_runtime_import_observation_v1_20260928.tar.zst"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    if ARCHIVE.exists():
        raise SystemExit(f"refusing to overwrite {ARCHIVE}")
    lock = json.loads(LOCK.read_text())
    expected = {**lock["python_source_sha256"], **lock["seed_manifest_sha256"],
                **lock["direct_source_sha256"]}
    for rel, digest in expected.items():
        if sha(ROOT / rel) != digest:
            raise SystemExit(f"locked source changed before archive: {rel}")
    from domains.engine_provenance import rust_source_fingerprint, rust_source_hashes
    rust_hashes = rust_source_hashes(str(ROOT))
    if rust_source_fingerprint(str(ROOT)) != lock["native_rust_source_fingerprint"]:
        raise SystemExit("Rust source fingerprint differs from captured lock")
    expected_native = "runners/dsl/python/substrate_rs/_native.abi3.so"
    if sha(ROOT / expected_native) != lock["native_extension_sha256"]:
        raise SystemExit("native extension differs from captured lock")
    expected_manifest = "runners/dsl/python/substrate_rs/_native.build.json"
    if sha(ROOT / expected_manifest) != lock["native_build_manifest_sha256"]:
        raise SystemExit("native build manifest differs from captured lock")
    paths = sorted(set(expected) | set(rust_hashes) | {expected_native, expected_manifest})
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", prefix="profile-source-", suffix=".list") as listing:
        listing.write("\n".join(paths) + "\n")
        listing.flush()
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["tar", "--zstd", "-cf", str(ARCHIVE), "-C", str(ROOT), "-T", listing.name], check=True)
    for rel, digest in expected.items():
        if sha(ROOT / rel) != digest:
            raise SystemExit(f"locked source changed during archive: {rel}")
    if rust_source_fingerprint(str(ROOT)) != lock["native_rust_source_fingerprint"]:
        raise SystemExit("Rust source changed during archive")
    if sha(ROOT / expected_native) != lock["native_extension_sha256"]:
        raise SystemExit("native extension changed during archive")
    subprocess.run(["zstd", "-t", str(ARCHIVE)], check=True)
    print(json.dumps({"archive": str(ARCHIVE.relative_to(ROOT)), "sha256": sha(ARCHIVE),
                      "size_bytes": ARCHIVE.stat().st_size, "file_count": len(paths)}, indent=2))


if __name__ == "__main__":
    main()
