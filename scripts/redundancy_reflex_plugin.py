"""ARM 5 -- layer dissociation: reflex firing census + reflex/higher-layer ablation.

Separate from `redundancy_ablate_plugin` on purpose: that file is being imported
by a running sweep, and editing an instrument mid-measurement changes it between
configs. This one is standalone.

Environment:
    REDUNDANCY_ABLATE_SEED      seed id to ablate (higher layer, Direction 1)
    REDUNDANCY_ABLATE_RULES     comma-separated rule names, or "*"
    REDUNDANCY_ABLATE_REFLEXES  comma-separated Reflex names to withhold, or "*"
                                (Direction 2 -- ablate the lower layer)
    REDUNDANCY_OUT              output json

Records, per run, every `Reflex` node's graph-resident `fire_count` summed over
every substrate built during the session. `fire_count` is the dead-arm
instrument: a reflex with baseline 0 survives every ablation trivially and is
excluded from the dissociation claim (PREREG Arm 5).
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

TARGET = os.environ.get("REDUNDANCY_ABLATE_SEED", "")
_RAW = os.environ.get("REDUNDANCY_ABLATE_RULES", "")
_RX = os.environ.get("REDUNDANCY_ABLATE_REFLEXES", "")
DROP_ALL = _RAW.strip() == "*"
DROP = set() if DROP_ALL else {r for r in _RAW.split(",") if r}
RX_ALL = _RX.strip() == "*"
RX_DROP = set() if RX_ALL else {r for r in _RX.split(",") if r}
HAS_RX = bool(_RX.strip())
OUT = os.environ.get("REDUNDANCY_OUT", "")

APPLIED: collections.Counter = collections.Counter()
_SUBSTRATES: list = []


def _filter(sid: str, manifest):
    if not isinstance(manifest, dict):
        return manifest
    out = manifest
    if TARGET and sid == TARGET and manifest.get("rules"):
        rules = manifest["rules"]
        kept = [] if DROP_ALL else [r for r in rules if r.get("name") not in DROP]
        out = dict(out)
        out["rules"] = kept
        APPLIED["rules:" + sid] += len(rules) - len(kept)
    if HAS_RX and manifest.get("reflexes"):
        rx = manifest["reflexes"]
        kept = [] if RX_ALL else [r for r in rx if r.get("name") not in RX_DROP]
        if len(kept) != len(rx):
            out = dict(out)
            out["reflexes"] = kept
            APPLIED["reflexes:" + sid] += len(rx) - len(kept)
    return out


def _install_hooks() -> None:
    import substrate.boot_core as bc
    import substrate.seed_loader as sl
    import substrate_rs as srs

    _mf = sl.manifest_for

    def manifest_for(sid, *a, **k):
        return _filter(str(sid), _mf(sid, *a, **k))

    sl.manifest_for = manifest_for
    bc.manifest_for = manifest_for

    try:
        import substrate.boot_all as ba
        _rs = ba._read_seeds

        def _read_seeds(d, *a, **k):
            got = dict(_rs(d, *a, **k))
            for sid in list(got):
                got[sid] = _filter(sid, got[sid])
            return got

        ba._read_seeds = _read_seeds
    except Exception:
        pass

    _init = srs.Substrate.__init__

    def __init__(self, *a, **k):
        _init(self, *a, **k)
        _SUBSTRATES.append(self)

    srs.Substrate.__init__ = __init__


class Plugin:
    def __init__(self) -> None:
        self.results = collections.defaultdict(lambda: collections.defaultdict(int))
        self.errors: list = []

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.results[os.path.basename(str(report.fspath))][report.outcome] += 1
        elif report.outcome == "failed":
            self.results[os.path.basename(str(report.fspath))]["error"] += 1
            self.errors.append({"nodeid": report.nodeid, "repr": str(report.longrepr)[:3000]})

    def pytest_sessionfinish(self, session, exitstatus):
        fire = collections.Counter()
        seen = collections.Counter()
        for s in _SUBSTRATES:
            try:
                for n in s.nodes("Reflex"):
                    a = s.node(n)["attrs"]
                    nm = a.get("name")
                    if not nm:
                        continue
                    seen[nm] += 1
                    fire[nm] += int(a.get("fire_count", 0) or 0)
            except Exception:
                continue
        rec = {"seed": TARGET, "rules_dropped": "*" if DROP_ALL else sorted(DROP),
               "reflexes_dropped": ("*" if RX_ALL else sorted(RX_DROP)) if HAS_RX else None,
               "n_dropped_installs": dict(APPLIED), "exitstatus": int(exitstatus),
               "per_file": {k: dict(v) for k, v in self.results.items()},
               "passed": sum(v.get("passed", 0) for v in self.results.values()),
               "failed": sum(v.get("failed", 0) for v in self.results.values()),
               "reflex_fire_count": dict(fire), "reflex_nodes_seen": dict(seen),
               "errors": self.errors[:30], "engine": ep.provenance_line()}
        if OUT:
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT, "w") as fh:
                json.dump(rec, fh, indent=1, sort_keys=True)


_install_hooks()


def pytest_configure(config):
    config.pluginmanager.register(Plugin(), "redundancy_reflex")
