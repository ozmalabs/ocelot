"""A pytest plugin that reports the ARGMIN TIE counters PER TEST FILE.

Used as `-p argmin_tie_report` with `PYTHONPATH=scripts`, so it touches no
shared file (PROTOCOL §11.4: own your files).

It only READS the engine's counters and writes a JSON sidecar. The mode itself
is set by `OZMA_ARGMIN_UNIQUE` in the environment, which the Rust module reads
once per process -- so the plugin cannot change what it measures.

`ties` and `empties` are reported separately at every level: a tie-refusal null
and an empty-source null are the SAME `Value::None` downstream, and this rung's
whole point is that the two must never be conflated.
"""
import json
import os
import pathlib

_native = None


def _stats():
    global _native
    if _native is None:
        import substrate_rs
        _native = substrate_rs._native
    return _native.argmin_tie_stats()


class TieReport:
    def __init__(self):
        self.per_file = {}
        self.per_test = {}
        self.outcomes = {}
        self._last = None

    def pytest_sessionstart(self, session):
        s = _stats()
        self.mode = s["mode"]
        self._last = s

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        self.outcomes[report.nodeid] = report.outcome
        s = _stats()
        f = report.nodeid.split("::")[0]
        prev = self._last or {"firings": 0, "ties": 0, "empties": 0,
                              "refusals": 0, "unique_term_firings": 0}
        d = self.per_file.setdefault(
            f, {"firings": 0, "ties": 0, "empties": 0, "refusals": 0,
                "unique_term_firings": 0})
        dt = {k: s[k] - prev[k] for k in d}
        for k in d:
            d[k] += dt[k]
        if dt["ties"] or dt["refusals"]:
            self.per_test[report.nodeid] = dt
        self._last = s

    def pytest_sessionfinish(self, session, exitstatus):
        s = _stats()
        sites = _native.argmin_tie_sites()
        out = {
            "mode": os.environ.get("OZMA_ARGMIN_UNIQUE", "off"),
            "engine_mode_seen_by_rust": s["mode"],
            "loadavg": list(os.getloadavg()),
            "totals": s,
            "per_file": self.per_file,
            "per_test": self.per_test,
            "outcomes": self.outcomes,
            "sites": sites,
            "exitstatus": int(exitstatus),
        }
        dest = pathlib.Path(
            os.environ.get("ARGMIN_TIE_OUT", "results/argmin_tie_report.json"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(out, indent=2))
        tr = session.config.pluginmanager.get_plugin("terminalreporter")
        if tr is not None:
            tr.write_line(
                f"[argmin_tie] mode={out['mode']} firings={s['firings']} "
                f"ties={s['ties']} empties={s['empties']} "
                f"refusals={s['refusals']} -> {dest}")


def pytest_configure(config):
    config.pluginmanager.register(TieReport(), "argmin_tie_report_instance")
