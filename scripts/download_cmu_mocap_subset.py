#!/usr/bin/env python3
"""Download and verify the small CMU motion-topology evidence subset."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cmu_mocap"
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.json"
SUBJECT_BASE = "http://mocap.cs.cmu.edu/subjects"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download(url: str, target: Path, expected: str) -> str:
    if target.exists() and _sha256(target) == expected:
        return "held"
    RAW.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=RAW, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        with urlopen(url) as response:
            for block in iter(lambda: response.read(1024 * 1024), b""):
                temporary.write(block)
    actual = _sha256(temporary_path)
    if actual != expected:
        temporary_path.unlink(missing_ok=True)
        raise ValueError(f"checksum mismatch for {url}: {actual} != {expected}")
    temporary_path.replace(target)
    return "downloaded"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    statuses: dict[str, str] = {}
    for row in manifest["clips"]:
        subject = int(row["subject"])
        trial = int(row["trial"])
        for filename, checksum in (
            (f"{subject}.asf", row["asf_sha256"]),
            (f"{subject}_{trial:02d}.amc", row["amc_sha256"]),
        ):
            statuses[filename] = _download(
                f"{SUBJECT_BASE}/{subject}/{filename}",
                RAW / filename,
                checksum,
            )
    print(json.dumps(statuses, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
