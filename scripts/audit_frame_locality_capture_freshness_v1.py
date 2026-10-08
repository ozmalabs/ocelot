"""Check whether historical live-task captures can be repeated unchanged.

The audit never rewrites a lock or launches a worker. A stale result remains
valid evidence about its captured source, but must not be presented as a
current-source run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCKS = (
    "evaluation/substrate_capability/live_self_report_task_boundary_v2_1_lock_20260927.json",
    "evaluation/substrate_capability/live_task_request_cost_capture_v1_lock_20260927.json",
)
MANIFEST = "runners/dsl/python/substrate_rs/_native.build.json"
EXTENSION = "runners/dsl/python/substrate_rs/_native.abi3.so"


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_commit() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def inspect_lock(relative: str, commit: str, manifest_hash: str, extension_hash: str) -> dict:
    path = ROOT / relative
    envelope = json.loads(path.read_text(encoding="utf-8"))
    locked = envelope.get("locked_inputs", envelope)
    closure = locked.get("source_closure_sha256", {})
    changed, missing = [], []
    for source, expected in closure.items():
        actual = sha256(ROOT / source)
        if actual is None:
            missing.append(source)
        elif actual != expected:
            changed.append(source)
    named = locked.get("source_sha256", {})
    named_changed = []
    for source, expected in named.items():
        actual = sha256(ROOT / source)
        if actual is None or actual != expected:
            named_changed.append(source)
    checks = {
        "commit_matches": locked.get("commit") == commit,
        "source_closure_matches": not changed and not missing,
        "named_sources_match": not named_changed,
        "native_build_manifest_matches": locked.get("native_build_manifest_sha256") == manifest_hash,
        "native_extension_matches": locked.get("native_extension_sha256") == extension_hash,
    }
    return {
        "lock": relative,
        "lock_sha256": sha256(path),
        "locked_commit": locked.get("commit"),
        "source_closure_file_count": len(closure),
        "changed_source_count": len(changed),
        "changed_sources": changed,
        "missing_source_count": len(missing),
        "missing_sources": missing,
        "named_source_count": len(named),
        "changed_named_source_count": len(named_changed),
        "changed_named_sources": named_changed,
        "checks": checks,
        "ready_for_same_lock_rerun": all(checks.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="evaluation/substrate_capability/frame_locality_capture_freshness_v1_20261003.json")
    parser.add_argument("--locks", nargs="*", default=list(DEFAULT_LOCKS))
    args = parser.parse_args()
    commit = current_commit()
    manifest_hash, extension_hash = sha256(ROOT / MANIFEST), sha256(ROOT / EXTENSION)
    rows = [inspect_lock(lock, commit, manifest_hash, extension_hash) for lock in args.locks]
    report = {
        "schema_version": 1,
        "audit_kind": "historical_frame_locality_capture_freshness",
        "claim_boundary": "Checks source/native freshness only; does not validate historical capture semantics or measure frame locality.",
        "current": {"commit": commit, "native_build_manifest": {"path": MANIFEST, "sha256": manifest_hash},
                    "native_extension": {"path": EXTENSION, "sha256": extension_hash}},
        "runner": {"path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
                   "sha256": sha256(Path(__file__).resolve())},
        "summary": {"lock_count": len(rows), "same_lock_rerun_ready": sum(r["ready_for_same_lock_rerun"] for r in rows),
                    "stale_lock_count": sum(not r["ready_for_same_lock_rerun"] for r in rows)},
        "locks": rows,
    }
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    for row in rows:
        print(f"{row['lock']}: changed {row['changed_source_count']}/{row['source_closure_file_count']}; "
              f"native manifest match={row['checks']['native_build_manifest_matches']}; "
              f"same-lock rerun ready={row['ready_for_same_lock_rerun']}")
    print(f"wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
