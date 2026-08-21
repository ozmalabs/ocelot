"""pytest plugin: argmin_tie census with per-site attribution, per run."""
import sys, json, os
sys.path.insert(0, 'runners/dsl/python')

def pytest_sessionstart(session):
    from substrate_rs import _native
    _native.argmin_tie_enable("count")
    _native.argmin_tie_reset()

def pytest_sessionfinish(session, exitstatus):
    from substrate_rs import _native
    out = {"stats": _native.argmin_tie_stats(),
           "sites": [dict(r) if isinstance(r, dict) else str(r)
                     for r in _native.argmin_tie_sites()]}
    path = os.environ.get("TIE_OUT", "/tmp/tie_out.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print("\n=== argmin_tie ===", json.dumps(out["stats"], sort_keys=True))
