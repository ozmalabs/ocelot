#!/usr/bin/env python3
"""PER-AREA RESIDUAL SALIENCE ON THE EVENT STREAM — probe (block 164000).

Rung 4 of the photon-eye migration. Salience is the RESIDUAL of the async
onset-event stream after the dominant common-fate motion is explained — the
event-native re-expression of 157000 (egomotion ⟷ the dominant common-fate
velocity v_dom; a track's cancelled residual ⟷ a column's |v_run − v_dom|).

ARCHITECTURE (CLAUDE.md — the agent is Rust): no agent decision in Python. The
salience is computed by the Rust `retinal_residual_salience` kernel and minted by
the `retinal_mint_salience` graph rule (seeds/retinal_salience.json); this probe
only PACKS the onset-event stream into the kernel payload (mechanical I/O, the
peer of `settle_carve`) and READS the scores back. The headline numbers are gated
by tests/test_residual_salience_event_migrated.py.

Pre-registration: VISION_RESIDUAL_SALIENCE_EVENT_PREREG.md.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import substrate_rs as srs  # noqa: E402

STRIDE = 3


def _auc(fg, bg):
    if not fg or not bg:
        return None
    wins = sum(1.0 if a > b else (0.5 if a == b else 0.0) for a in fg for b in bg)
    return wins / (len(fg) * len(bg))


def _pack(n_az, events, max_gap=1.0, vel_tol=0.35):
    p = [float(n_az), float(max_gap), float(vel_tol), float(len(events))]
    for c, e in events:
        p.extend([float(c), float(e)])
    return p


def _kernel(s, payload):
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": "retinal_residual_salience",
        "payload": [float(v) for v in payload], "input_epoch": 1,
        "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    return list(s.node(t)["attrs"]["output"])


def main():
    from domains.engine_provenance import engine_preamble, provenance_stamp
    engine_preamble(strict=False)
    prov = provenance_stamp(strict=False)
    s = srs.Substrate()
    n_az = 16

    # HEADLINE: fast coherent background (cols 0..9, v=3) + slow independent
    # mover (cols 12..14, v=−1). Residual isolates the mover; raw ranks the
    # fast background above it.
    bg = [(c, c / 3.0) for c in range(0, 10)]
    mover = [(c, 100.0 - c) for c in range(12, 15)]
    out = _kernel(s, _pack(n_az, bg + mover))
    fired = [c for c in range(n_az) if out[c * STRIDE] == 1.0]
    raw = {c: out[c * STRIDE + 1] for c in fired}
    res = {c: out[c * STRIDE + 2] for c in fired}
    bg_c = list(range(0, 10)); mv_c = list(range(12, 15))
    order = sorted(res, key=lambda c: -res[c])
    primary = {
        "raw_auc_mover_vs_bg": _auc([raw[c] for c in mv_c], [raw[c] for c in bg_c]),
        "residual_auc_mover_vs_bg": _auc([res[c] for c in mv_c], [res[c] for c in bg_c]),
        "mover_rank_residual": min(order.index(c) for c in mv_c) + 1,
        "bg_residual_max": max(res[c] for c in bg_c),
        "mover_residual": res[mv_c[0]],
        "bg_raw": raw[bg_c[0]], "mover_raw": raw[mv_c[0]],
    }

    # SILENCE: fully coherent field → residual ~0 everywhere; raw not silent.
    coh = _kernel(s, _pack(n_az, [(c, float(c)) for c in range(n_az)]))
    cf = [c for c in range(n_az) if coh[c * STRIDE] == 1.0]
    silence = {
        "max_residual": max(coh[c * STRIDE + 2] for c in cf),
        "max_raw": max(coh[c * STRIDE + 1] for c in cf),
    }

    # NO-DOMINANT identity: isolated flashes → v_dom=0 → residual == raw.
    flr = _kernel(s, _pack(n_az, [(0, 5.0), (4, 9.0), (8, 2.0), (12, 7.0)]))
    ff = [c for c in range(n_az) if flr[c * STRIDE] == 1.0]
    no_dominant = {
        "residual_equals_raw": all(
            abs(flr[c * STRIDE + 1] - flr[c * STRIDE + 2]) < 1e-9 for c in ff),
    }

    result = {
        "block": 164000, "rung": "photon-eye/4 residual-salience-event",
        "engine_source_match": prov.get("source_match"),
        "primary": primary, "silence": silence, "no_dominant": no_dominant,
    }
    print(json.dumps(result, indent=2))
    outp = os.path.join(ROOT, "results", "residual_salience_event.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w") as fh:
        json.dump(result, fh, indent=2)
    print("wrote", outp)
    return result


if __name__ == "__main__":
    main()
