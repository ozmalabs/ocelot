"""Confirmatory test for docs/research/engine_substrate/SD_LOOP_GEN_REARM_AND_TIE_PARITY_PREREG.md
(block 372000, start commit dca17cfa).

G1  sd_redecode left gen_checked and gen_explained stale across a codebook-epoch re-arm.
    Fix: sd_redecode also clears both to 0 (seeds/shape_decode_loop.json v1.19.0).
G2  ClosestShape was invisible to the argmin_tie census and refusal coercion. The Rust side is
    covered by the closest_shape_tests module in runners/dsl/src/shape_decode.rs (not here).

H-1  A re-armed observation ends in the same state as a fresh observation with the same
     signature, decoded once against the final codebook. Three streams:
       (a) the block 370000 affect growth stream (23 frames, test_affect_frame_v02 arm B);
       (b) the det1 view grid (A2 shears and the three integer rotations over the 7 pentominoes),
           then an epoch bump from an unrelated part;
       (c) the block 371000 tromino scenario.
H-2  In stream (b), every re-armed view observation has gen_checked == 1 at the end.
H-0  Source check of the seed: the two resets are present and the version is 1.19.0.

The pre-fix control reruns the three streams with the two resets removed from sd_redecode in
memory (monkeypatched seed_loader.manifest_for). It records counts and asserts nothing about them.

Measurements go to results/sd_gen_rearm_tie_parity.json.
"""
from __future__ import annotations

import copy
import importlib
import json
import os
import subprocess
import time

import pytest

pytest.importorskip("substrate_rs")

from substrate import seed_loader  # noqa: E402
from tests import test_affect_frame_v02 as v02  # noqa: E402
from tests import test_sd_rearm_closest_shape_migrated as tromino  # noqa: E402

det1 = importlib.import_module("scripts.det1_measure")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "results", "sd_gen_rearm_tie_parity.json")
SEED_PATH = os.path.join(ROOT, "seeds", "shape_decode_loop.json")
START_COMMIT = "dca17cfa1973b21bcd67d9dc56dd4cf083b1b347"

GEN_RESETS = (["set_attr", "obs", "gen_checked", 0], ["set_attr", "obs", "gen_explained", 0])
DIM_RESET = ["set_attr", "obs", "dim_explained", 0]
# sd_redecode's status guard: the statuses a codebook-epoch bump re-arms.
REDECODE_STATUSES = ("minted", "recognized", "recognized_transformed", "recognized_duplicate")
# Transform attributes compared between a re-armed and a fresh observation (source excluded:
# it names the observation key, which differs by construction).
TKEYS = ("base", "dims", "deltas", "transforms", "dim", "delta", "generator", "k",
         "generators", "ks")
VIEWS = {**det1.SHEARS, "rot90": det1.XF_DS["rot90"], "rot180": det1.XF_DS["rot180"],
         "rot270": det1.XF_DS["rot270"]}


# ---------------------------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------------------------

def _record(section, payload):
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    data = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as fh:
            data = json.load(fh)
    data[section] = payload
    with open(OUT_PATH, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True, default=str)


@pytest.fixture(scope="module", autouse=True)
def _header():
    from domains.engine_provenance import provenance_line
    head = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    if os.path.exists(OUT_PATH):
        os.remove(OUT_PATH)
    _record("header", {"start_commit": START_COMMIT, "head_at_run": head,
                       "engine": provenance_line(), "started_unix": time.time()})
    yield


def _plain(x):
    if isinstance(x, (list, tuple)):
        return [_plain(i) for i in x]
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    return x


def _tkey(sub, t):
    a = sub.node(t)["attrs"]
    return json.dumps({k: _plain(a.get(k)) for k in TKEYS if a.get(k) is not None},
                      sort_keys=True, default=str)


def _state(sub, nb, nid):
    """End state of one observation. `nb(nid, edge)` returns its neighbours on that edge."""
    a = sub.node(nid)["attrs"]
    trs = list(nb(nid, "has_transform"))
    return {"status": _plain(a.get("status")), "covered_by": _plain(a.get("covered_by")),
            "gen_explained": _plain(a.get("gen_explained")), "n_transform": len(trs),
            "transforms": sorted(_tkey(sub, t) for t in trs),
            "gen_checked": _plain(a.get("gen_checked")),
            "transform_explained": _plain(a.get("transform_explained")),
            "dim_explained": _plain(a.get("dim_explained"))}


def _core(st):
    return (st["status"], st["covered_by"], st["gen_explained"], st["n_transform"],
            tuple(st["transforms"]))


def _fresh_obs(sub, add_edge, run, ag, sig, dim_types, i):
    """A new Observation with the given signature, pending, wired `ag observed obs`.
    No follows or appraisal edges. It is decoded once against the codebook as it stands."""
    attrs = {"signature": sig, "key": ["fresh", i], "status": "pending"}
    if dim_types is not None:
        attrs["dim_types"] = list(dim_types)
    obs = sub.add_node("Observation", attrs)
    add_edge(ag, "observed", obs)
    run()
    return obs


def _compare(rows):
    bad = []
    for r in rows:
        if _core(r["re"]) != _core(r["fresh"]):
            bad.append({"label": r["label"], "re": _plain(r["re"]), "fresh": _plain(r["fresh"])})
    return {"n_total": len(rows), "n_agree": len(rows) - len(bad), "disagree": bad}


# ---------------------------------------------------------------------------------------------
# streams
# ---------------------------------------------------------------------------------------------

def _stream_affect():
    """(a) affect growth stream. Mirrors test_affect_frame_v02._arm_b, but keeps the graph open
    so that fresh observations can be decoded against the same codebook."""
    eye, inner = v02._boot([v02.SEED_FRAME])
    try:
        sub = eye.substrate
        events = []
        for ev in v02.ALL_EVENTS:
            hub = v02._new_hub(eye, inner)
            ap = v02.M._appraise(eye, inner, hub, **v02.inputs(*ev))
            inner.run_rules()
            events.append((ev, list(inner.neighbours(ap, "has_affect_frame"))))
        frames = [(ev, fid) for ev, fids in events for fid in fids]
        re_states = [_state(sub, inner.neighbours, fid) for _, fid in frames]
        ax_before = len(sub.nodes("CapabilityAxis"))
        rows = []
        for i, ((ev, fid), re) in enumerate(zip(frames, re_states)):
            a = sub.node(fid)["attrs"]
            dt = a.get("dim_types")
            obs = _fresh_obs(sub, inner.add_edge_unchecked, inner.run_rules, eye._agent,
                             _plain(a.get("signature")), _plain(dt) if dt is not None else None, i)
            rows.append({"label": f"{ev}/{a.get('aff_tag')}", "re": re,
                         "fresh": _state(sub, inner.neighbours, obs)})
        out = _compare(rows)
        out["capability_axes_minted_by_fresh_pass"] = len(sub.nodes("CapabilityAxis")) - ax_before
        out["n_frames_re_armed_arm"] = len(frames)
        return out
    finally:
        eye.stop()


def _stream_det1():
    """(b) det1 view grid, one graph, one epoch bump from an unrelated part."""
    s, ag, native = det1._boot(det1.OBJ, True, True)
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    views = []
    for src, xf, view in det1._views(VIEWS):
        goal = det1.sig(view)
        o = s.add_node("Observation", {"signature": goal, "key": [f"view:{src}:{xf}"],
                                       "status": "decoded", "residual": goal,
                                       "decoded_epoch": ep, "dim_types": det1.DT})
        s.add_edge(ag, "observed", o)
        views.append((f"{src}/{xf}", view, o))
    native.run_rules()
    pre_status = {label: s.node(o)["attrs"].get("status") for label, _, o in views}
    s.add_node("ShapeSignature", {"name": "zz_unrelated", "signature": [["zz_q", 1]]})
    s.set_attr(ag, "codebook_epoch", ep + 1.0)
    native.run_rules()
    re_states = {label: _state(s, s.neighbours, o) for label, _, o in views}
    rearmed = [label for label, _, _ in views if pre_status[label] in REDECODE_STATUSES]
    rows = []
    for i, (label, view, o) in enumerate(views):
        obs = _fresh_obs(s, s.add_edge, native.run_rules, ag, det1.sig(view), det1.DT, i)
        rows.append({"label": label, "re": re_states[label],
                     "fresh": _state(s, s.neighbours, obs)})
    out = _compare(rows)
    out["n_rearmed"] = len(rearmed)
    out["pre_bump_status"] = pre_status
    out["rearmed_gen_checked"] = {label: re_states[label]["gen_checked"] for label in rearmed}
    out["rearmed_gen_checked_not_1"] = [label for label in rearmed
                                        if re_states[label]["gen_checked"] != 1]
    return out


def _stream_tromino():
    """(c) the block 371000 tromino scenario, then one fresh observation."""
    s, ag, native = tromino._boot()
    tromino._add_part(s, "part_tromino", tromino.TROMINO, "json", dim_types=tromino.DIM_TYPES)
    obs = tromino._observe_decoded(s, ag, signature=tromino.ROTATED_K1_TROMINO,
                                   key="probe_rotate", residual=tromino.ROTATED_K1_TROMINO,
                                   decoded_epoch=tromino._epoch(s, ag),
                                   dim_types=tromino.DIM_TYPES)
    native.run_rules()
    s.add_node("ShapeSignature", {"name": "zz_unrelated", "signature": [["zz_q", 1]]})
    s.set_attr(ag, "codebook_epoch", tromino._epoch(s, ag) + 1)
    native.run_rules()
    re = _state(s, s.neighbours, obs)
    fresh = _fresh_obs(s, s.add_edge, native.run_rules, ag, tromino.ROTATED_K1_TROMINO,
                       tromino.DIM_TYPES, 0)
    return _compare([{"label": "rotated_k1_tromino", "re": re,
                      "fresh": _state(s, s.neighbours, fresh)}])


_RUNS = {}


def _run_streams():
    if "fixed" not in _RUNS:
        _RUNS["fixed"] = {"a": _stream_affect(), "b": _stream_det1(), "c": _stream_tromino()}
    return _RUNS["fixed"]


# ---------------------------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------------------------

def test_H0_seed_resets_gen_flags_and_version():
    with open(SEED_PATH, encoding="utf-8") as fh:
        seed = json.load(fh)
    rule = next(r for r in seed["rules"] if r["name"] == "sd_redecode")
    fx = rule["effects"]
    _record("H-0", {"version": seed["version"], "sd_redecode_effects": fx})
    assert seed["version"] == "1.19.0", seed["version"]
    for eff in GEN_RESETS:
        assert fx.count(eff) == 1, eff
    assert fx.index(GEN_RESETS[0]) > fx.index(DIM_RESET), "gen resets must follow the dim reset"
    assert "block 372000" in rule["comment"]


def test_H1_stream_a_affect_rearm_equals_fresh():
    res = _run_streams()["a"]
    _record("H-1a", res)
    assert res["n_total"] == 23, res["n_total"]
    assert res["n_agree"] == res["n_total"], res["disagree"][:5]


def test_H1_stream_b_det1_rearm_equals_fresh():
    res = _run_streams()["b"]
    _record("H-1b", res)
    assert res["n_total"] == 5 * len(det1.OBJ), res["n_total"]
    assert res["n_agree"] == res["n_total"], res["disagree"][:5]


def test_H1_stream_c_tromino_rearm_equals_fresh():
    res = _run_streams()["c"]
    _record("H-1c", res)
    assert res["n_total"] == 1
    assert res["n_agree"] == res["n_total"], res["disagree"]


def test_H2_stream_b_rearmed_views_gen_checked():
    res = _run_streams()["b"]
    _record("H-2", {"n_rearmed": res["n_rearmed"],
                    "rearmed_gen_checked": res["rearmed_gen_checked"],
                    "not_1": res["rearmed_gen_checked_not_1"]})
    assert res["n_rearmed"] > 0
    assert res["rearmed_gen_checked_not_1"] == [], res["rearmed_gen_checked_not_1"]


def test_control_prefix_disagreement_record_only(monkeypatch):
    """Record only. The same three streams with sd_redecode's two resets removed in memory."""
    orig = seed_loader.manifest_for

    def prefix(sid):
        m = orig(sid)
        if sid != "shape_decode_loop":
            return m
        m = copy.deepcopy(m)
        removed = 0
        for r in m["rules"]:
            if r.get("name") == "sd_redecode":
                before = len(r["effects"])
                r["effects"] = [e for e in r["effects"] if e not in GEN_RESETS]
                removed += before - len(r["effects"])
        assert removed == 2, removed
        return m

    monkeypatch.setattr(seed_loader, "manifest_for", prefix)
    pre = {"a": _stream_affect(), "b": _stream_det1(), "c": _stream_tromino()}
    _record("control-prefix", {k: {kk: vv for kk, vv in v.items() if kk != "pre_bump_status"}
                               for k, v in pre.items()})
