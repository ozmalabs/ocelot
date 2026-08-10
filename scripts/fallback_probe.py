"""FALLBACK VOCABULARY probe — one process per arm.

Deliberately a near-clone of `scripts/redundancy_observability.py` (the audit's
Arm 4 runner) so the two are directly comparable: same ablation mechanism (an
in-process manifest filter — nothing on disk is touched), same 3-seed probe
pipeline, same 16x16 retina, same 40 steps, same ignition schedule. Only the
RNG differs (62002 from this rung's own block, vs the audit's 59002) and the
readout is extended with the fallback tallies.

Usage:  python scripts/fallback_probe.py [TARGET_SEED] OUT.json
        TARGET_SEED = "" means BASELINE (no ablation).

PROTOCOL §10.1 rule 3: a non-pytest entrypoint MUST call `engine_preamble()`
itself, or the absolute `site-packages/*.pth` resolves the CANONICAL tree's
engine and this worktree's Rust change evaporates silently. That bit this rung
once already, during the instrument's own smoke test.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

# The audit's own probe RNG, moved to this rung's block (62000-62999).
PROBE_SEED = 62002


def _filter_install(target: str) -> None:
    """Withhold every rule of `target` at install time.

    The redundancy audit's manifest filter verbatim in behaviour: mechanical
    dict surgery on the manifest before `load_seed_manifest` parses it, so an
    ablated rule never occupies a RuleIdx and NOTHING under `seeds/` is
    modified. Restoration is therefore exact rather than best-effort.
    """
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


def probe(target: str, count_totals: bool) -> dict:
    _filter_install(target)

    import domains.seed_registry  # noqa: F401
    import substrate_rs
    from domains.fallback_readout import engine_tallies
    from domains.lateral_world import add_lateral_retina, channels, gains, set_lat_params
    from domains.wave_world import WaveWorld
    from substrate.boot_core import boot_core, load_seeds_into

    substrate_rs._native.Substrate.fallback_count_totals(bool(count_totals))

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

    # Reset AFTER boot/wiring so the tally covers the WORKLOAD, not the
    # one-off seed installation. Boot-time reads are a different population and
    # pooling them would put a constant offset under every arm.
    s._inner.fallback_trace_reset()

    for i in range(40):
        w.step(ignite_k=1 if i % 5 == 0 else 0)

    tallies = engine_tallies(s)

    def _flat(a):
        import numpy as np
        return [round(float(x), 9) for x in np.asarray(a).ravel()]

    # The audit's readout, kept verbatim so the degraded/not-degraded verdict
    # is decided exactly as Arm 4 decided it. Note the audit's own recorded
    # bug: channels() takes anat["bipolars"] and gains() takes anat["hcells"];
    # passing the whole anat dict silently returns an empty readout.
    readout = {"nodes": s.node_count(), "edges": s.edge_count()}
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

    return {"readout": readout, "tallies": tallies, "target": target,
            "count_totals": bool(count_totals)}


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    out = sys.argv[2]
    count_totals = os.environ.get("FALLBACK_COUNT_TOTALS", "0") == "1"
    try:
        d = probe(target, count_totals)
        d["crashed"] = False
    except BaseException as e:  # PanicException is NOT an Exception subclass
        import traceback
        d = {"crashed": True, "target": target, "exc": repr(e)[:400],
             "traceback": traceback.format_exc()[:4000]}
    d["engine"] = provenance_line()
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(d, f, indent=1, sort_keys=True)
    print(f"[fallback_probe] target={target or 'BASELINE'} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
