"""ARM 4 -- OBSERVABILITY: when an ablation degrades the output, does the graph
RECORD that a fallback occurred, or is the degradation SILENT?

A silent fallback is a silent-failure generator: the system did the right thing
and left no evidence. This arm counts them.

Method: one FIXED probe world (the wave/lateral/on-off pipeline that 11 of the
15 seed-loading bench files build on), run identically under baseline and under
each whole-seed ablation. Three things are read off the resulting graph:

  functional readout   node/edge counts + the probe's own channel + gain
                       vectors. A DEGRADATION is a readout that differs from
                       baseline.
  marker inventory     nodes whose TYPE or whose attribute KEY/VALUE matches
                       the problem-marking vocabulary ENUMERATED FROM THE
                       CODEBASE (not invented here): Unknown / GroundingGap /
                       GapSpec / GapRouteCue / SelfConcern, and
                       unresolved|gap|refus|ambig|residual|stale|fallback|
                       missing|degrad|absent|unknown.
  verdict              SELF-EVIDENT iff the marker inventory differs from
                       baseline; SILENT iff the readout degraded and the marker
                       inventory did not.

Probe RNG seed 59002, from the allocated block 59000-59999.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

MARKER_TYPES = {"Unknown", "GroundingGap", "GapSpec", "GapRouteCue", "SelfConcern"}
# Keys carrying documentation, never runtime state.
DOC_KEYS = {"comment", "description", "doc", "docstring", "note", "provenance",
            "rationale", "why", "source"}
MARKER_RE = re.compile(
    r"unresolved|gap|refus|ambig|residual|stale|fallback|missing|degrad|absent|unknown",
    re.I)
PROBE_SEED = 59002

TARGETS = json.load(open(os.path.join(ROOT, "scripts", "_redundancy_targets.json"))) \
    if os.path.exists(os.path.join(ROOT, "scripts", "_redundancy_targets.json")) else None


def _filter_install(target: str):
    """Withhold every rule of `target` at install time -- the same manifest
    filter the main sweep uses, nothing touched on disk."""
    import substrate.boot_core as bc
    import substrate.seed_loader as sl
    _mf = getattr(sl, "_orig_manifest_for", None) or sl.manifest_for
    sl._orig_manifest_for = _mf

    def manifest_for(sid, *a, **k):
        m = _mf(sid, *a, **k)
        if target and str(sid) == target and isinstance(m, dict) and m.get("rules"):
            m = dict(m)
            m["rules"] = []
        return m

    sl.manifest_for = manifest_for
    bc.manifest_for = manifest_for


def probe(target: str) -> dict:
    """Build the fixed probe world with `target`'s rules withheld; read it off."""
    _filter_install(target)
    import domains.seed_registry  # noqa: F401
    from domains.lateral_world import add_lateral_retina, channels, gains, set_lat_params
    from domains.wave_world import WaveWorld
    from substrate.boot_core import boot_core, load_seeds_into

    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral", "vision_onoff"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)
    w = WaveWorld(s, h=16, w=16, seed=PROBE_SEED)
    anat = add_lateral_retina(w)
    set_lat_params(w, lateral=1.0, learn_gain=1.0, radius2=1.0,
                   lat_eta=2e-3, lat_gmax=2.0, frozen=0.0)
    for i in range(40):
        w.step(ignite_k=1 if i % 5 == 0 else 0)

    types = collections.Counter()
    markers = collections.Counter()
    for n in s.nodes():
        node = s.node(n)
        t = node["type"]
        types[t] += 1
        if t in MARKER_TYPES or MARKER_RE.search(t or ""):
            markers["type:" + t] += 1
        for k, v in (node.get("attrs") or {}).items():
            if not isinstance(k, str) or k in DOC_KEYS:
                continue  # documentation prose is not a runtime marker
            if MARKER_RE.search(k):
                markers["attr:" + k] += 1
            # A VALUE counts only when the whole value IS a status token (one
            # word). Without this the seeds' long explanatory `comment` strings
            # match the vocabulary and every run looks self-evident -- a false
            # positive that would have inverted this arm's result.
            if isinstance(v, str) and " " not in v.strip() and MARKER_RE.search(v):
                markers[f"val:{k}={v.strip()}"] += 1

    def _flat(a):
        import numpy as np
        return [round(float(x), 9) for x in np.asarray(a).ravel()]

    readout = {"nodes": s.node_count(), "edges": s.edge_count(),
               "types": dict(types)}
    # `channels` takes the BIPOLAR map and `gains` the HCELL map -- passing the
    # whole `anat` dict silently yields an empty readout (it iterates the two
    # top-level keys). That dead reader was caught by the smoke test before any
    # verdict was taken off it; PROTOCOL §1, positive-control the instrument.
    try:
        on, off = channels(w, anat["bipolars"])
        readout["channels_on"] = _flat(on)
        readout["channels_off"] = _flat(off)
    except BaseException as e:
        readout["channels_error"] = repr(e)[:400]
    try:
        readout["gains"] = _flat(gains(w, anat["hcells"]))
    except BaseException as e:
        readout["gains_error"] = repr(e)[:400]
    return {"readout": readout, "markers": dict(markers)}


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    out = sys.argv[2]
    try:
        rec = probe(target)
        rec["crashed"] = False
    except BaseException as e:
        rec = {"crashed": True, "exc": repr(e)[:600],
               "traceback": traceback.format_exc()[-6000:]}
    rec["target"] = target
    rec["engine"] = ep.provenance_line()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
