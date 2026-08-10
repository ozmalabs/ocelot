"""Record WHICH seeds each vision-bench test file actually installs.

Mechanical instrumentation only -- a pytest plugin that wraps the three seed
install paths (`seed_loader.manifest_for`, `boot_all._read_seeds`,
`boot_core.load_seeds_into`) and writes the union per test FILE.

This is a STRUCTURAL fact about the harness (knowable by reading the source),
not an experimental result: it is what the redundancy audit's selection rule is
defined over. Run BEFORE the pre-registration; see VISION_REDUNDANCY_PREREG.md.
"""
from __future__ import annotations

import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

SEEN: dict[str, set[str]] = collections.defaultdict(set)
_CURRENT = {"file": "<none>"}


def _install_hooks() -> None:
    import substrate.boot_core as bc
    import substrate.seed_loader as sl

    _mf = sl.manifest_for

    def manifest_for(sid, *a, **k):
        SEEN[_CURRENT["file"]].add(str(sid))
        return _mf(sid, *a, **k)

    sl.manifest_for = manifest_for
    bc.manifest_for = manifest_for
    try:
        import substrate.boot_all as ba
        _rs = ba._read_seeds

        def _read_seeds(d, *a, **k):
            got = _rs(d, *a, **k)
            for sid in got:
                SEEN[_CURRENT["file"]].add(str(sid))
            return got

        ba._read_seeds = _read_seeds
    except Exception:
        pass


class Plugin:
    def pytest_runtest_setup(self, item):
        _CURRENT["file"] = os.path.basename(str(item.fspath))

    def pytest_sessionfinish(self, session, exitstatus):
        out = {k: sorted(v) for k, v in SEEN.items()}
        with open(os.path.join(ROOT, "results", "redundancy_seed_map.json"), "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)


def main() -> int:
    import pytest

    _install_hooks()
    files = [ln.strip() for ln in open(
        os.path.join(ROOT, "scripts", "rung7_vision_bench.sh")) if ln.strip().startswith("tests/")]
    files = [f.rstrip(" \\") for f in files]
    return pytest.main(["-q", "-W", "ignore", "-p", "no:randomly", *files],
                       plugins=[Plugin()])


if __name__ == "__main__":
    raise SystemExit(main())
