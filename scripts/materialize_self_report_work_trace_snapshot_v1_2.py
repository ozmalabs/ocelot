#!/usr/bin/env python3
"""Create an immutable, manifest-checked source snapshot for live capture v1.2."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = Path("/tmp/ocelot_self_report_work_trace_v1_2")
BUNDLE = Path("/tmp/ocelot_self_report_work_trace_v1_2_source.tar.zst")
sys.path.insert(0, str(ROOT))
import substrate_live_self_report_work_trace_v1_2 as capture  # noqa: E402


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_file(rel: str) -> None:
    source = ROOT / rel
    target = DEST / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> None:
    if DEST.exists() or BUNDLE.exists():
        raise SystemExit(f"refusing to overwrite {DEST} or {BUNDLE}")

    before = capture.lock_inputs()
    closure_before = capture.source_closure()
    time.sleep(0.2)
    after = capture.lock_inputs()
    closure_after = capture.source_closure()
    if before != after or closure_before != closure_after:
        raise SystemExit("live source changed during the required double-read; no snapshot created")

    DEST.mkdir(parents=True)
    # Runtime Python source trees and their exact native extension/build record.
    for rel in ("domains", "substrate", "runners/dsl/python"):
        shutil.copytree(ROOT / rel, DEST / rel,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Rust inputs used by engine_provenance's source fingerprint.
    shutil.copytree(ROOT / "runners/dsl/src", DEST / "runners/dsl/src")
    copy_file("runners/dsl/Cargo.toml")
    # Exactly the top-level and generated seed manifests loaded by boot_all.
    (DEST / "seeds/generated").mkdir(parents=True)
    for rel in closure_before:
        if rel.startswith("seeds/"):
            copy_file(rel)
    # The capture scripts and complete preregistration/amendment chain.
    for rel in capture.SOURCES:
        copy_file(rel)
    # Runtime output and git identity remain linked to the canonical repository;
    # measured code, native binary, and task manifests are copied above.
    for name in (".git", "evaluation"):
        (DEST / name).symlink_to(ROOT / name, target_is_directory=True)

    copied_closure = {}
    for rel in closure_before:
        copied_closure[rel] = file_sha(DEST / rel)
    if copied_closure != closure_before:
        raise SystemExit("copied runtime/seed closure differs from stable source manifest")
    copied_sources = {rel: file_sha(DEST / rel) for rel in capture.SOURCES}
    expected_sources = before["source_sha256"]
    if copied_sources != expected_sources:
        raise SystemExit("copied protocol/runner/source files differ from source lock")
    native_rel = Path(capture._native.__file__).resolve().relative_to(ROOT)
    if file_sha(DEST / native_rel) != before["native_extension_sha256"]:
        raise SystemExit("copied native extension differs from source lock")
    manifest_rel = "runners/dsl/python/substrate_rs/_native.build.json"
    if file_sha(DEST / manifest_rel) != before["native_build_manifest_sha256"]:
        raise SystemExit("copied native build record differs from source lock")
    from domains.engine_provenance import rust_source_fingerprint
    if rust_source_fingerprint(str(DEST)) != before["rust_source_fingerprint"]:
        raise SystemExit("copied Rust source fingerprint differs from source lock")

    # A compact replay bundle is kept alongside the lock and raw output.
    subprocess.run(["tar", "--zstd", "-cf", str(BUNDLE), "-C", "/tmp", DEST.name], check=True)
    bundle_sha = file_sha(BUNDLE)
    output = {
        "snapshot": str(DEST),
        "bundle": str(BUNDLE),
        "bundle_sha256": bundle_sha,
        "stable_source_lock": before,
        "closure_file_count": len(closure_before),
        "copied_source_count": len(copied_sources),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
