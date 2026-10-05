"""Mary's Room stage 4.5: colour properties, looking episodes and their link.

Seeds (graph rules, built by tools/build_{colour_property,looking_episode,
look_property_link}_seed.py) on top of surface_segmentation +
surface_persistence:
  colour_property     per PersistentSurface: lattice mean linear catch, frame
                      anchor (max), ONE ColourProperty at first sight; rung 1
                      (L1-derived rounding bound) and rung 2 (L3b leave-one-out)
                      PropertyChecks.
  looking_episode     one LookingEpisode per exposure; SurfaceLook per matched
                      surface (mean RetinalPercept); FieldLook for a ganzfeld.
  look_property_link  look -presents_property|presents_unrecognised-> property.
Adapter: domains/perceived_surface_world.py (mechanical). Driven synchronously
(submit_photons_2d -> run_cognitive_tasks(1) -> run_rules -> prune).

Scene: spectral_scene.standard_mondrian (24x16) at 1000 td, deterministic
(cumulative) quantisation.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from domains import spectral_scene as ss
from domains.perceived_surface_world import (STAGE45_TYPES, PerceivedSurfaceWorld)

TD = 1000.0
NA, NE = ss.STANDARD_N_AZ, ss.STANDARD_N_EL
STD = ss.standard_mondrian()
GT = STD.label_map()
CH = ("L", "M", "S")
SEED45_TYPES = {"ColourPropertyParams", "ColourState", "LookingEpisodeParams",
                "LookingState", "Observer"}
GREY_WHITE = (ss.BACKGROUND_ID, ss.STANDARD_WHITE_ID)  # neutral 5, white


# ----------------------------------------------------------------- helpers

def _clean(rows):
    return [{k: v for k, v in r.items() if k != "_nid"} for r in rows]


def _sid_grid(w):
    return np.array([c.get("cur_sid") for c in w.cells()]).reshape(w.n_el, w.n_az)


def _sid_of_patch(sid_grid, gt, pid):
    vals = set(sid_grid[gt == pid].ravel().tolist())
    assert len(vals) == 1, (pid, vals)
    return vals.pop()


def _snapshot(w):
    e = w.eye._epoch
    return {
        "epoch": e,
        "sid": _sid_grid(w),
        "checks": _clean(w.checks(e)),
        "looks": _clean(w.surface_looks(e)),
        "properties": _clean(w.colour_properties()),
        "frames": _clean(w.frames()),
        "counts": w.counts(),
        "percepts": w.eye.percepts_2d(),
    }


def _run(exposures, **kw):
    w = PerceivedSurfaceWorld(NA, NE, stage45=True, **kw)
    try:
        assert all(s["rules_skipped"] == [] for s in w.load_summaries)
        snaps = []
        for p in exposures:
            w.expose(p)
            snaps.append(_snapshot(w))
        extra = {"episodes": _clean(w.episodes()), "field_looks": _clean(w.field_looks()),
                 "timings": list(w.timings)}
    finally:
        w.stop()
    return snaps, extra


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items()
                if k not in ("service_wall_micros", "wall_micros")}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def _export_without(w, drop_types) -> str:
    d = _strip(w.s.graph_to_dict())
    drop = {n["id"] for n in d["nodes"] if n["type"] in drop_types}
    keep = [n for n in d["nodes"] if n["id"] not in drop]
    rank = {n["id"]: i for i, n in enumerate(keep)}
    nodes = [{"id": rank[n["id"]], "type": n["type"], "attrs": n["attrs"]} for n in keep]
    edges = sorted(
        ({"src": rank[e["src"]], "tgt": rank[e["tgt"]], "type": e["type"],
          "attrs": e["attrs"]}
         for e in d["edges"] if e["src"] not in drop and e["tgt"] not in drop),
        key=lambda e: (e["src"], e["type"], e["tgt"]))
    return json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, default=repr)


def _derived_bound(c, pa, p, a):
    """TEST ORACLE of the seed's rung-1 envelope (same derivation)."""
    return (0.5 * (c + pa + p + a) + (0.25 if min(c, pa) < 1 else 0.0)
            + (0.25 if min(p, a) < 1 else 0.0))


def _lattice_catch(percepts, gt, pid):
    """TEST ORACLE: Round(mean member caught_quanta) per channel for a patch
    (numpy round = half-even, like the engine's Round)."""
    idx = np.flatnonzero(gt.ravel() == pid)
    return [float(np.round(np.mean([percepts[i]["receptors"][r]["caught_quanta"]
                                    for i in idx])))
            for r in ("l", "m", "s")]


def _props_by_sid(snap):
    return {p["sid"]: p for p in snap["properties"]}


def _report(title, rows):
    print(f"\n{title}")
    for r in rows:
        print("  " + r)


# ----------------------------------------------------------------- fixtures

@pytest.fixture(scope="module")
def e_e_d65():
    return _run([ss.render(STD, "E", TD), ss.render(STD, "E", TD),
                 ss.render(STD, "D65", TD)])


@pytest.fixture(scope="module")
def e_a():
    return _run([ss.render(STD, "E", TD), ss.render(STD, "A", TD)])


# ------------------------------------------------- 1. flags off byte-identity

@pytest.mark.parametrize("pooled", [False, True])
def test_flags_off_byte_identity_of_eye_and_seeds_1_2(pooled):
    base = PerceivedSurfaceWorld(NA, NE)                       # seeds 1-2 only, ON
    off = PerceivedSurfaceWorld(NA, NE, stage45=True, colour=False,
                                pooled=pooled, looking=False)  # + seeds 3-5, OFF
    try:
        assert all(s["rules_skipped"] == [] for s in off.load_summaries)
        for p in (ss.render(STD, "E", TD), ss.render(STD, "A", TD),
                  ss.diffuse(NA, NE, "E", TD)):
            base.expose(p)
            off.expose(p)
        assert all(off.counts()[t] == 0 for t in STAGE45_TYPES)
        assert off.counts()["presents_property"] == 0
        assert off.counts()["presents_unrecognised"] == 0
        assert off.s.node_count() == base.s.node_count() + len(SEED45_TYPES)
        assert off.s.edge_count() == base.s.edge_count() + 5
        assert off.eye.percepts_2d() == base.eye.percepts_2d()
        assert off.persistent_surfaces() == base.persistent_surfaces()
        assert (_export_without(off, SEED45_TYPES)
                == _export_without(base, set()))
    finally:
        base.stop()
        off.stop()


# ------------------------------------------------- 2. static E -> E

def test_static_mondrian_e_to_e_every_surface_holds_residual_zero(e_e_d65):
    snaps, extra = e_e_d65
    e1, e2 = snaps[0], snaps[1]
    n = len(e1["properties"])
    assert n == 10                         # 11 patches, isoluminant pair merged
    assert [c["status"] for c in e1["checks"]] == ["minted"] * n
    # ps_catch == oracle lattice catch for every non-merged patch
    for pid in sorted(set(GT.ravel().tolist()) - set(ss.ISOLUMINANT_PAIR)):
        sid = _sid_of_patch(e1["sid"], GT, pid)
        prop = _props_by_sid(e1)[sid]
        assert [prop["p" + ch] for ch in CH] == _lattice_catch(e1["percepts"], GT, pid)
    # anchor = per-channel max over surfaces
    f1 = e1["frames"][0]
    for ch in CH:
        assert f1["a" + ch] == max(p["p" + ch] for p in e1["properties"])
    assert len(e2["checks"]) == n
    for c in e2["checks"]:
        assert c["status"] == "holds" and c["resid_max"] == 0.0, c
        assert c["pooled_status"] == "holds_pooled"
    assert e2["properties"] == e1["properties"]       # never re-minted
    assert e2["counts"]["presents_property"] == 2 * n
    assert e2["counts"]["presents_unrecognised"] == 0
    assert [ep["status"] for ep in extra["episodes"]] == ["observed"] * 3
    _report("timing per exposure (s), E,E,D65", [", ".join(f"{t:.3f}" for t in extra["timings"])])


# ------------------------------------------------- 3. E -> D65 and E -> A

def _patch_names(snap):
    out = {}
    for pid in sorted(set(GT.ravel().tolist())):
        out.setdefault(_sid_of_patch(snap["sid"], GT, pid), []).append(
            f"{pid}:{STD.reflectance_of(pid)}")
    return out


def _check_table(label, snap, ref_props):
    names = _patch_names(snap)
    rows = []
    for c in snap["checks"]:
        if c["status"] == "minted":
            rows.append(f"sid {c['sid']:2d} {'/'.join(names.get(c['sid'], [])):34s} "
                        f"minted at this epoch (new sid; no check)")
            continue
        p = ref_props[c["sid"]]
        rel = max(c["resid_" + ch] / max(c["bound_" + ch], 1e-12) for ch in CH)
        rows.append(
            f"sid {c['sid']:2d} {'/'.join(names.get(c['sid'], [])):34s} "
            f"rung1={c['status']:8s} max resid/bound={rel:8.2f}  "
            f"rung2={c['pooled_status']:14s} "
            f"g=({', '.join(f'{c['g' + ch]:.3f}' for ch in CH)}) "
            f"p/pa=({', '.join(f'{p['p' + ch] / p['pa' + ch]:.3f}' for ch in CH)})")
    _report(label, rows)


def _assert_illuminant_epoch(snap, ref_props):
    for c in snap["checks"]:
        if c["status"] == "minted":
            continue
        assert c["status"] in ("holds", "refused")
        p = ref_props[c["sid"]]
        bounds = [_derived_bound(c["c" + ch], p["pa" + ch], p["p" + ch], c["a" + ch])
                  for ch in CH]
        resids = [abs(c["c" + ch] * p["pa" + ch] - p["p" + ch] * c["a" + ch]) for ch in CH]
        assert [c["bound_" + ch] for ch in CH] == pytest.approx(bounds)
        assert [c["resid_" + ch] for ch in CH] == pytest.approx(resids)
        assert (c["status"] == "holds") == all(r <= b for r, b in zip(resids, bounds))
        assert c["pooled_status"] in ("holds_pooled", "refused_pooled")
    # refusals are PropertyCheck nodes; properties unchanged; links follow rung 1
    assert {p["sid"]: p for p in snap["properties"] if p["sid"] in ref_props} == ref_props
    status = {c["sid"]: c["status"] for c in snap["checks"]}
    for look in snap["looks"]:
        want = "unrecognised" if status[look["sid"]] == "refused" else "property"
        assert look["link"] == want
        assert look["edges"] == {"presents_property": int(want == "property"),
                                 "presents_unrecognised": int(want == "unrecognised")}


def test_illuminant_change_rung1_and_rung2_reported(e_e_d65, e_a):
    snaps_d, _ = e_e_d65
    snaps_a, _ = e_a
    ref_d = _props_by_sid(snaps_d[0])
    ref_a = _props_by_sid(snaps_a[0])
    _assert_illuminant_epoch(snaps_d[2], ref_d)
    _assert_illuminant_epoch(snaps_a[1], ref_a)
    assert any(c["status"] == "refused" for c in snaps_a[1]["checks"])  # written
    for label, snap, ref in (("E -> D65", snaps_d[2], ref_d), ("E -> A", snaps_a[1], ref_a)):
        _check_table(f"{label}: per surface rung 1 (L1 bound) / rung 2 (L3b LOO)",
                     snap, ref)
        n = {s: sum(1 for c in snap["checks"] if c.get(k) == s)
             for k, s in (("status", "holds"), ("status", "refused"),
                          ("pooled_status", "holds_pooled"),
                          ("pooled_status", "refused_pooled"))}
        _report(f"{label} totals", [str(n)])


# ------------------------------------------------- 4. adaptation dissociation

def _look_of_patch(snap, pid):
    sid = _sid_of_patch(snap["sid"], GT, pid)
    return sid, next(l for l in snap["looks"] if l["sid"] == sid)


def test_adaptation_look_shifts_while_property_holds_superposed_field():
    """Exposures 2..21 = the scene PLUS a uniform 610 nm field (the scene stays
    visible, so the luminance-edge identity survives); exposure 22 = the scene
    alone. The grey/white surfaces LOOK greener (rg drops) while their
    PropertyCheck HOLDS with residual 0 against the epoch-1 property: catches
    are linear, adaptation lives in the activation only."""
    scene = ss.render(STD, "E", TD)
    field = ss.adapting_field(STD, 610.0, 2000)
    snaps, extra = _run([scene] + [scene + field] * 20 + [scene])
    first, last = snaps[0], snaps[-1]
    assert np.array_equal(first["sid"], last["sid"])
    rows = []
    for pid in GREY_WHITE:
        sid, l1 = _look_of_patch(first, pid)
        _, l22 = _look_of_patch(last, pid)
        chk = next(c for c in last["checks"] if c["sid"] == sid)
        assert l22["rg"] < l1["rg"], (pid, l1["rg"], l22["rg"])
        assert chk["status"] == "holds" and chk["resid_max"] == 0.0
        assert l22["link"] == "property"
        rows.append(f"patch {pid} sid {sid}: rg {l1['rg']:+.4f} -> {l22['rg']:+.4f}, "
                    f"by {l1['by']:+.4f} -> {l22['by']:+.4f}, check {chk['status']} "
                    f"resid {chk['resid_max']}")
    assert last["properties"] == first["properties"]
    during = [c["status"] for s in snaps[1:-1] for c in s["checks"]]
    rows.append(f"during adaptation (scene+field, epochs 2..21): "
                f"{during.count('holds')} holds / {during.count('refused')} refused")
    _report("adaptation, superposed 610 nm field", rows)
    _report("timing (s) first/last", [f"{extra['timings'][0]:.3f} {extra['timings'][-1]:.3f}"])


def test_adaptation_pure_field_look_shifts_no_green_property_minted():
    """The brief's literal schedule: exposures 2..21 = a pure 610 nm field
    (ganzfeld: no boundary, so stage 4.4 identity does not survive it --
    declared limitation; the scene re-births new sids at exposure 22). The
    grey/white surfaces' look shifts negative in rg, and the property minted
    for the re-born surface equals the epoch-1 property: no green property."""
    scene = ss.render(STD, "E", TD)
    field = ss.adapting_field(STD, 610.0, 2000)
    snaps, extra = _run([scene] + [field] * 20 + [scene])
    first, last = snaps[0], snaps[-1]
    assert len(extra["field_looks"]) == 20
    assert all(s["looks"] == [] and s["checks"] == [] for s in snaps[1:-1])
    p1, p22 = _props_by_sid(first), _props_by_sid(last)
    rows = []
    for pid in GREY_WHITE:
        s1, l1 = _look_of_patch(first, pid)
        s22, l22 = _look_of_patch(last, pid)
        assert s22 != s1                               # identity lost (4.4 limit 3)
        assert l22["rg"] < l1["rg"]
        keys = [k + ch for k in ("p", "pa") for ch in CH]
        assert [p22[s22][k] for k in keys] == [p1[s1][k] for k in keys]
        assert p22[s22]["minted_epoch"] == last["epoch"]
        rows.append(f"patch {pid}: sid {s1}->{s22} rg {l1['rg']:+.4f} -> {l22['rg']:+.4f}; "
                    f"property p={[p22[s22]['p' + ch] for ch in CH]} unchanged")
    _report("adaptation, pure 610 nm field (literal schedule)", rows)


# ------------------------------------------------- 5. eyelid ganzfeld

def test_eyelid_ganzfeld_episode_and_field_look_only():
    snaps, extra = _run([ss.diffuse(NA, NE, "E", TD, filter="eyelid")])
    c = snaps[0]["counts"]
    assert c["LookingEpisode"] == 1 and c["FieldLook"] == 1
    assert c["SurfaceLook"] == 0 and c["ColourProperty"] == 0
    assert c["PropertyCheck"] == 0 and c["FrameStats"] == 0
    assert c["presents_property"] == c["presents_unrecognised"] == 0
    fl = extra["field_looks"][0]
    pc = snaps[0]["percepts"]
    assert fl["rg"] == pytest.approx(np.mean([p["red_green"] for p in pc]))
    assert fl["by"] == pytest.approx(np.mean([p["blue_yellow"] for p in pc]))
    assert fl["n_cells"] == NA * NE
    _report("eyelid FieldLook", [f"rg {fl['rg']:+.4f} by {fl['by']:+.4f} "
                                 f"intensity {fl['intensity']:.4f}"])


# ------------------------------------------------- 6. swap falsifier

def test_swap_patches_property_follows_position_and_is_refused():
    swapped = ss.swap_patches(STD, 2, 3)
    snaps, _ = _run([ss.render(STD, "E", TD), ss.render(swapped, "E", TD)])
    before, after = snaps
    assert np.array_equal(before["sid"], after["sid"])          # identity = position
    status = {c["sid"]: c for c in after["checks"]}
    swapped_sids = {_sid_of_patch(before["sid"], GT, pid) for pid in (2, 3)}
    for sid in swapped_sids:
        assert status[sid]["status"] == "refused", status[sid]
    for sid, c in status.items():
        if sid not in swapped_sids:
            assert c["status"] == "holds"
    assert after["properties"] == before["properties"]
    for look in after["looks"]:
        assert look["link"] == ("unrecognised" if look["sid"] in swapped_sids else "property")
    _report("swap(2,3) under E", [
        f"sid {s}: {status[s]['status']} resid_max {status[s]['resid_max']:.0f} "
        f"margin {status[s]['margin']:.0f}" for s in sorted(swapped_sids)])


# ------------------------------------------------- 7. determinism

def test_determinism(e_e_d65):
    snaps, extra = e_e_d65
    again, extra2 = _run([ss.render(STD, "E", TD), ss.render(STD, "E", TD),
                          ss.render(STD, "D65", TD)])
    for a, b in zip(snaps, again):
        for k in ("epoch", "checks", "looks", "properties", "frames", "counts"):
            assert a[k] == b[k], k
        assert np.array_equal(a["sid"], b["sid"])
    assert extra["episodes"] == extra2["episodes"]
