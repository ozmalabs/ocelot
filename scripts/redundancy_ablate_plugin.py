"""Seed-rule ablation as a MANIFEST FILTER (PROTOCOL §0 — graph data, not a code path).

A pytest plugin. Reads two environment variables:

    REDUNDANCY_ABLATE_SEED   the seed id to ablate
    REDUNDANCY_ABLATE_RULES  comma-separated rule names to withhold,
                             or the literal "*" for every rule in that seed

and withholds exactly those rules from that seed's manifest at INSTALL time.
Nothing on disk is touched, so concurrent runs cannot interfere and the
restoration check is exact (`git status` over `seeds/` stays clean).

This is the same kind of mechanism `substrate.boot_all.load_all_seeds(skip=...)`
already is: it changes WHICH GRAPH DATA IS INSTALLED. It contains no conditional
over graph state and makes no decision on the agent's behalf.

Also carries the Arm-1 rule-firing census: with REDUNDANCY_CENSUS=1 the plugin
accumulates the engine's own `rule_costs_report()` progress counter across every
substrate built during the run, and writes the totals at session end.
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
DROP_ALL = _RAW.strip() == "*"
DROP: set[str] = set() if DROP_ALL else {r for r in _RAW.split(",") if r}
CENSUS = os.environ.get("REDUNDANCY_CENSUS", "") == "1"
OUT = os.environ.get("REDUNDANCY_OUT", "")

# Ablations actually performed, so a config that names a seed nobody installs is
# visible as such rather than silently passing as "no effect".
APPLIED: collections.Counter = collections.Counter()
CENSUS_PROGRESS: collections.Counter = collections.Counter()
CENSUS_COUNT: collections.Counter = collections.Counter()
_SUBSTRATES: list = []


def _filter(sid: str, manifest):
    """Withhold the named rules from `sid`'s manifest. Mechanical dict surgery."""
    if not TARGET or sid != TARGET or not isinstance(manifest, dict):
        return manifest
    rules = manifest.get("rules")
    if not rules:
        return manifest
    out = dict(manifest)
    if DROP_ALL:
        kept = []
    else:
        kept = [r for r in rules if r.get("name") not in DROP]
    APPLIED[sid] += len(rules) - len(kept)
    out["rules"] = kept
    return out


def _install_hooks() -> None:
    import substrate.boot_core as bc
    import substrate.seed_loader as sl

    _mf = sl.manifest_for

    def manifest_for(sid, *a, **k):
        return _filter(str(sid), _mf(sid, *a, **k))

    sl.manifest_for = manifest_for
    bc.manifest_for = manifest_for

    try:
        import substrate.boot_all as ba
        _rs = ba._read_seeds

        def _read_seeds(d, *a, **k):
            got = _rs(d, *a, **k)
            if TARGET in got:
                got = dict(got)
                got[TARGET] = _filter(TARGET, got[TARGET])
            return got

        ba._read_seeds = _read_seeds
    except Exception:
        pass

    if CENSUS:
        import substrate_rs as srs
        _init = srs.Substrate.__init__

        def __init__(self, *a, **k):
            _init(self, *a, **k)
            _SUBSTRATES.append(self)

        srs.Substrate.__init__ = __init__


def _harvest_census() -> None:
    # `except BaseException`, deliberately: a substrate whose Rust mutex was
    # poisoned by an earlier panic raises `pyo3_runtime.PanicException`, which
    # does NOT inherit from Exception. Catching only Exception lost the whole
    # census at the last hook after all 200 tests had already passed.
    for s in _SUBSTRATES:
        try:
            for name, _micros, cnt, prog in s._inner.rule_costs():
                CENSUS_PROGRESS[name] += int(prog)
                CENSUS_COUNT[name] += int(cnt)
        except BaseException:
            CENSUS_PROGRESS["__unreadable_substrate__"] += 0
            CENSUS_COUNT["__unreadable_substrate__"] += 1
            continue


class Plugin:
    def __init__(self) -> None:
        self.results: dict[str, dict[str, int]] = collections.defaultdict(
            lambda: collections.defaultdict(int))
        self.errors: list = []

    def pytest_runtest_logreport(self, report):
        if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
            return
        f = os.path.basename(str(report.fspath))
        if report.when == "call":
            self.results[f][report.outcome] += 1
        elif report.outcome == "failed":
            self.results[f]["error"] += 1
            self.errors.append({"file": f, "nodeid": report.nodeid,
                                "phase": "setup", "repr": str(report.longrepr)[:4000]})

    def pytest_collectreport(self, report):
        if report.outcome == "failed":
            self.errors.append({"file": os.path.basename(str(report.fspath)),
                                "nodeid": report.nodeid, "phase": "collect",
                                "repr": str(report.longrepr)[:4000]})

    def pytest_sessionfinish(self, session, exitstatus):
        if CENSUS:
            _harvest_census()
        rec = {
            "seed": TARGET,
            "rules_dropped": "*" if DROP_ALL else sorted(DROP),
            "n_dropped_installs": dict(APPLIED),
            "exitstatus": int(exitstatus),
            "per_file": {k: dict(v) for k, v in self.results.items()},
            "passed": sum(v.get("passed", 0) for v in self.results.values()),
            "failed": sum(v.get("failed", 0) for v in self.results.values()),
            "errors": self.errors[:40],
            "engine": ep.provenance_line(),
        }
        if CENSUS:
            rec["census_progress"] = dict(CENSUS_PROGRESS)
            rec["census_count"] = dict(CENSUS_COUNT)
        if OUT:
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT, "w") as fh:
                json.dump(rec, fh, indent=1, sort_keys=True)


_install_hooks()


def pytest_configure(config):
    config.pluginmanager.register(Plugin(), "redundancy_ablate")
