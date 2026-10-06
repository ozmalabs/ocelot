"""Mary's Room stage 4 fixes: the 'not built' items of the stage-4 prereg.

Every new behaviour sits behind its OWN new flag (default 0.0):
  1. RE-ACQUISITION   surface_persistence 1.1.0, SurfacePersistenceParams.reacquire
  2. SATURATION       colour_property 1.1.0 (description only): shown, not refused
  3. RECALL           new seed colour_recall, ColourRecallParams.enabled
  4. CONCEPT LINK     new seed colour_concept_link, ColourConceptParams.enabled
  5. MOTION SEGMENTS  surface_segmentation 1.1.0,
                      SurfaceSegmentationParams.motion_segments
plus the BYTE-IDENTITY proof: with the new flags at 0 every graph export equals
a world built from the seeds f25aae47's generators produce.

Adapter: domains/perceived_surface_world.py (mechanical). Driven synchronously
(submit_photons_2d -> run_cognitive_tasks(1) -> run_rules -> prune).
Scene: spectral_scene.standard_mondrian (24x16), deterministic quantisation.
Measurements are printed (-s) and are reports, not pass conditions, unless an
assertion says otherwise.
"""
from __future__ import annotations

import importlib
import json
import math
import os
import subprocess

import numpy as np
import pytest

from domains import spectral_forward as sf
from domains import spectral_scene as ss
from domains.perceived_surface_world import PerceivedSurfaceWorld

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TD = 1000.0
NA, NE = ss.STANDARD_N_AZ, ss.STANDARD_N_EL
STD = ss.standard_mondrian()
GT = STD.label_map()
CH = ("L", "M", "S")
BASE_COMMIT = "f25aae47"
OLD_SEEDS = ("surface_segmentation", "surface_persistence", "colour_property",
             "looking_episode", "look_property_link")
NEW_SEEDS = ("colour_recall", "colour_concept_link")
NEW_FLAG_ATTRS = {"SurfacePersistenceParams": {"reacquire"},
                  "SurfaceSegmentationParams": {"motion_segments"}}
NEW_SEED_TYPES = {"ColourRecallParams", "ColourConceptParams", "ColourConcept"}
COLOUR_KEYS = {"caught_quanta", "red_green", "blue_yellow", "intensity",
               "activation", "rg", "by", "cL", "cM", "cS", "pL", "pM", "pS",
               "paL", "paM", "paS", "aL", "aM", "aS"}
COLOUR_EDGES = {"l_receptor", "m_receptor", "s_receptor", "has_retinal_percept",
                "look_of", "has_colour_property"}


# ----------------------------------------------------------------- helpers

def _report(title, rows):
    print(f"\n{title}")
    for r in rows:
        print("  " + r)


def _grid(w, key="cur_sid"):
    return np.array([c.get(key) for c in w.cells()]).reshape(w.n_el, w.n_az)


def _sid_of(grid, gt, pid):
    vals = set(grid[gt == pid].ravel().tolist())
    assert len(vals) == 1, (pid, vals)
    return vals.pop()


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items()
                if k not in ("service_wall_micros", "wall_micros")}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def _export(w, drop_types=(), strip_attrs=None) -> str:
    """Whole-graph export; nodes of `drop_types` (and their edges) removed and
    ids re-ranked; the attrs in strip_attrs[type] removed."""
    strip_attrs = strip_attrs or {}
    d = _strip(w.s.graph_to_dict())
    drop = {n["id"] for n in d["nodes"] if n["type"] in drop_types}
    keep = [n for n in d["nodes"] if n["id"] not in drop]
    rank = {n["id"]: i for i, n in enumerate(keep)}
    nodes = [{"id": rank[n["id"]], "type": n["type"],
              "attrs": {k: v for k, v in n["attrs"].items()
                        if k not in strip_attrs.get(n["type"], ())}} for n in keep]
    edges = sorted(
        ({"src": rank[e["src"]], "tgt": rank[e["tgt"]], "type": e["type"],
          "attrs": e["attrs"]}
         for e in d["edges"] if e["src"] not in drop and e["tgt"] not in drop),
        key=lambda e: (e["src"], e["type"], e["tgt"]))
    return json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, default=repr)


def _clean(rows):
    return [{k: v for k, v in r.items() if k != "_nid"} for r in rows]


def _records(w) -> dict:
    """Battery-style raw records of one exposure (the observables)."""
    e = w.eye._epoch
    return {"epoch": e, "cells": w.cells(), "segments": _clean(w.segments(epoch=e)),
            "surfaces": w.persistent_surfaces(), "state": w.state(),
            "properties": _clean(w.colour_properties()), "frames": _clean(w.frames()),
            "checks": _clean(w.checks(e)), "looks": _clean(w.surface_looks(e)),
            "field_looks": _clean(w.field_looks()), "episodes": _clean(w.episodes()),
            "counts": w.counts(), "percepts": w.eye.percepts_2d()}


def _strip_records(rec):
    rec = json.loads(json.dumps(rec, sort_keys=True, default=repr))
    for k, keys in NEW_FLAG_ATTRS.items():
        for a in rec["state"].get(k, []):
            for key in keys:
                a.pop(key, None)
    return rec


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def _exec_generator(src: str, name: str) -> dict:
    """Run a generator's source WITHOUT its __main__ write; return MANIFEST."""
    ns = {"__name__": f"gen_{name}",
          "__file__": os.path.join(ROOT, "tools", f"build_{name}_seed.py")}
    exec(compile(src, ns["__file__"], "exec"), ns)
    return ns["MANIFEST"]


def _dump(manifest) -> str:
    return json.dumps(manifest, indent=1) + "\n"


def _rule_attr_keys_and_edges(rule) -> tuple[set, set]:
    keys, edges = set(), set()

    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "Attr":
                keys.add(x["key"])
            if x.get("type") in ("Neighbours", "InNeighbours"):
                edges.add(x["edge_type"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(rule["where"])
    walk(rule["effects"])
    for m in rule["match"]:
        edges.add(m[1])
    return keys, edges


def _seed(name) -> dict:
    with open(os.path.join(ROOT, "seeds", f"{name}.json")) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def old_manifests():
    """The seeds f25aae47's generators produce (and f25aae47 committed)."""
    out = {}
    for name in OLD_SEEDS:
        src = _git("show", f"{BASE_COMMIT}:tools/build_{name}_seed.py")
        m = _exec_generator(src, name)
        assert _dump(m) == _git("show", f"{BASE_COMMIT}:seeds/{name}.json"), name
        out[name] = json.loads(json.dumps(m))
    return out


# ------------------------------------------------- 0. generators / manifests

@pytest.mark.parametrize("name", OLD_SEEDS + NEW_SEEDS)
def test_generators_deterministic_and_seeds_regenerated(name):
    path = os.path.join(ROOT, "tools", f"build_{name}_seed.py")
    with open(path) as f:
        src = f.read()
    a, b = _exec_generator(src, name), _exec_generator(src, name)
    assert _dump(a) == _dump(b)
    with open(os.path.join(ROOT, "seeds", f"{name}.json")) as f:
        assert f.read() == _dump(a), f"seeds/{name}.json is stale"


def test_versions_flags_and_manifests():
    want = {"surface_segmentation": "1.1.0", "surface_persistence": "1.1.0",
            "colour_property": "1.1.0", "looking_episode": "1.0.0",
            "look_property_link": "1.0.0", "colour_recall": "1.0.0",
            "colour_concept_link": "1.0.0"}
    for name, v in want.items():
        m = _seed(name)
        assert m["version"] == v, name
        assert m["latency_class"] == "hard_realtime"
    params = {n["type"]: n["attrs"] for name in want for n in _seed(name)["nodes"]
              if n["type"].endswith("Params")}
    assert params["SurfaceSegmentationParams"] == {"enabled": 0.0, "motion_segments": 0.0}
    assert params["SurfacePersistenceParams"] == {"enabled": 0.0, "reacquire": 0.0}
    assert params["ColourRecallParams"] == {"enabled": 0.0}
    assert params["ColourConceptParams"] == {"enabled": 0.0}
    assert _seed("colour_recall")["depends_on"] == ["colour_property"]
    assert _seed("colour_concept_link")["depends_on"] == ["colour_property"]
    assert "SATURATION DOES NOT AFFECT" in _seed("colour_property")["description"]


@pytest.mark.parametrize("seed,prefixes", [
    ("surface_persistence", ("ps_keep_last", "ps_reacq_key", "ps_reacq_mark")),
    ("surface_segmentation", ("seg_motion_",)),
])
def test_new_identity_rules_are_colour_free(seed, prefixes):
    """Static audit: the re-acquisition and motion rules read no catch, no
    percept value and no colour edge (identity stays colour-free)."""
    rules = [r for r in _seed(seed)["rules"] if r["name"].startswith(prefixes)]
    assert rules
    for r in rules:
        keys, edges = _rule_attr_keys_and_edges(r)
        assert not (keys & COLOUR_KEYS), (r["name"], keys & COLOUR_KEYS)
        assert not (edges & COLOUR_EDGES), (r["name"], edges & COLOUR_EDGES)


# ------------------------------------------------- 1. byte identity vs f25aae47

def _identity_schedule():
    ganz = ss.diffuse(NA, NE, "E", TD)
    eyelid = ss.diffuse(NA, NE, "E", TD, filter="eyelid")
    scene = ss.render(STD, "E", TD)
    return [scene, ss.render(STD, "D65", TD), ss.render(STD, "A", TD), ganz,
            eyelid, scene, ss.render(ss.swap_patches(STD, 2, 3), "E", TD),
            ss.render(ss.translate_patch(STD, 10, 1, 0), "E", TD),
            scene + ss.adapting_field(STD, 610.0, 2000), scene]


def test_flags_off_byte_identical_to_f25aae47(old_manifests):
    """f25aae47-style runs (its generators' seeds) vs today's seeds with the new
    flags at their defaults: identical raw records and identical whole-graph
    exports after EVERY exposure. The only stripped difference is the presence
    of the new flag attrs (value 0.0) on the two param nodes; for the world that
    also loads the two new seeds (flags off), their own param/concept nodes are
    dropped before comparing."""
    old = PerceivedSurfaceWorld(NA, NE, stage45=True, manifests=old_manifests)
    new = PerceivedSurfaceWorld(NA, NE, stage45=True)
    new7 = PerceivedSurfaceWorld(NA, NE, stage45=True, recall=False, concepts=False)
    old44 = PerceivedSurfaceWorld(NA, NE, manifests=old_manifests)
    new44 = PerceivedSurfaceWorld(NA, NE)
    worlds = (old, new, new7, old44, new44)
    try:
        for w in worlds:
            assert all(s["rules_skipped"] == [] for s in w.load_summaries)
        assert [s["id"] for s in new7.load_summaries][-2:] == list(NEW_SEEDS)
        n = 0
        for packets in _identity_schedule():
            for w in worlds:
                w.expose(packets)
            ref = _export(old)
            assert _export(new, strip_attrs=NEW_FLAG_ATTRS) == ref
            assert _export(new7, NEW_SEED_TYPES, NEW_FLAG_ATTRS) == _export(old, ())
            assert _export(new44, strip_attrs=NEW_FLAG_ATTRS) == _export(old44)
            r_old = json.dumps(_strip_records(_records(old)), sort_keys=True)
            assert json.dumps(_strip_records(_records(new)), sort_keys=True) == r_old
            assert json.dumps(_strip_records(_records(new7)), sort_keys=True) == r_old
            n += 1
        # non-vacuous: the schedule exercised every stage-4 node type
        c = old.counts()
        assert all(c[t] > 0 for t in ("ColourProperty", "PropertyCheck",
                                      "SurfaceLook", "FieldLook",
                                      "presents_property", "presents_unrecognised"))
        assert new.s.nodes("Recollection") == [] and new7.s.nodes("Recollection") == []
        assert all("concept_status" not in p for p in new7.colour_properties())
        assert all("reacquired_count" not in p for p in new.persistent_surfaces())
        assert all("seg_mgrp" not in c and "last_sid" not in c for c in new.cells())
        _report("byte identity vs f25aae47 generators",
                [f"{n} exposures x 5 worlds: exports and raw records identical; "
                 f"final counts {c}"])
    finally:
        for w in worlds:
            w.stop()


# ------------------------------------------------- 2. re-acquisition

def _run_grids(exposures, **kw):
    w = PerceivedSurfaceWorld(NA, NE, **kw)
    try:
        assert all(s["rules_skipped"] == [] for s in w.load_summaries)
        out = []
        for p in exposures:
            w.expose(p)
            out.append({"epoch": w.eye._epoch, "sid": _grid(w),
                        "surfaces": w.persistent_surfaces(),
                        "segments": _clean(w.segments(epoch=w.eye._epoch)),
                        "properties": _clean(w.colour_properties()) if kw.get("stage45") else [],
                        "checks": _clean(w.checks(w.eye._epoch)) if kw.get("stage45") else []})
    finally:
        w.stop()
    return out


def test_reacquire_scene_ganzfeld_ganzfeld_scene_same_sids():
    ganz = ss.diffuse(NA, NE, "E", TD)
    sched = [ss.render(STD, "E", TD), ganz, ganz, ss.render(STD, "E", TD)]
    on = _run_grids(sched, reacquire=True)
    off = _run_grids(sched)
    first, g1, g2, last = on
    assert (g1["sid"] == -1).all() and (g2["sid"] == -1).all()
    assert all(p["status"] == "coasting" and p["coast"] == 2 for p in g2["surfaces"])
    assert np.array_equal(first["sid"], last["sid"])
    assert len(last["surfaces"]) == len(first["surfaces"])
    assert all(p["status"] == "tracked" and p["coast"] == 0
               and p["reacquired_count"] == 1 for p in last["surfaces"])
    assert all(s["decision"] == "continue" and s["reacquired"] == 1.0
               for s in last["segments"])
    # flag off: the v1.0.0 behaviour (every surface re-born)
    assert len(off[-1]["surfaces"]) == 2 * len(off[0]["surfaces"])
    assert not (set(off[-1]["sid"].ravel()) & set(off[0]["sid"].ravel()))
    _report("re-acquisition: scene, ganzfeld, ganzfeld, scene",
            [f"reacquire on : {len(last['surfaces'])} surfaces, all sids kept, "
             f"reacquired_count=1 each",
             f"reacquire off: {len(off[-1]['surfaces'])} surfaces (all re-born)"])


def test_reacquire_scene_eyelid_swapped_scene_sids_follow_position():
    eyelid = ss.diffuse(NA, NE, "E", TD, filter="eyelid")
    swapped = ss.swap_patches(STD, 2, 3)
    on = _run_grids([ss.render(STD, "E", TD), eyelid, ss.render(swapped, "E", TD)],
                    reacquire=True, stage45=True)
    first, lid, after = on
    assert (lid["sid"] == -1).all()
    assert np.array_equal(first["sid"], after["sid"])
    swapped_sids = {_sid_of(first["sid"], GT, pid) for pid in (2, 3)}
    status = {c["sid"]: c["status"] for c in after["checks"]}
    for sid, st in status.items():
        assert st == ("refused" if sid in swapped_sids else "holds"), (sid, st)
    assert after["properties"] == first["properties"]     # not re-minted
    _report("re-acquisition: scene, eyelid, swap(2,3)",
            [f"sids follow position; swapped sids {sorted(swapped_sids)} rung1 refused; "
             f"others hold ({len(status) - 2})"])


def test_reacquire_new_patch_where_no_surface_was_births():
    without10 = ss.Mondrian(NA, NE, tuple(r for r in STD.rects if r[0] != 10),
                            STD.background)
    ganz = ss.diffuse(NA, NE, "E", TD)
    on = _run_grids([ss.render(without10, "E", TD), ganz, ss.render(STD, "E", TD)],
                    reacquire=True)
    first, _g, last = on
    gt0 = without10.label_map()
    for pid in set(GT.ravel().tolist()) - {10}:
        assert _sid_of(last["sid"], GT, pid) == _sid_of(first["sid"], gt0, pid), pid
    new = _sid_of(last["sid"], GT, 10)
    assert new not in set(first["sid"].ravel().tolist())
    p = next(s for s in last["surfaces"] if s["sid"] == new)
    assert p["born_epoch"] == last["epoch"] and "reacquired_count" not in p
    seg = next(s for s in last["segments"] if s["sid"] == new)
    assert seg["decision"] == "birth"
    _report("re-acquisition: new patch 10 after a ganzfeld",
            [f"patch 10 born sid {new} ({seg['birth_reason']}); all other patches "
             f"re-acquired their sids"])


def test_reacquire_survives_pure_adapting_field_properties_hold():
    """The stage-4 'pure 610 nm field' limitation, with reacquire on: identity
    survives 20 boundaryless field exposures; nothing is re-minted; the E->E
    check at the end holds with residual 0."""
    scene = ss.render(STD, "E", TD)
    field = ss.adapting_field(STD, 610.0, 2000)
    on = _run_grids([scene] + [field] * 20 + [scene], reacquire=True, stage45=True)
    first, last = on[0], on[-1]
    assert np.array_equal(first["sid"], last["sid"])
    assert last["properties"] == first["properties"]
    assert all(c["status"] == "holds" and c["resid_max"] == 0.0 for c in last["checks"])
    assert all(p["reacquired_count"] == 1 and p["status"] == "tracked"
               for p in last["surfaces"])
    _report("re-acquisition: scene + 20 x pure 610 nm field + scene",
            [f"{len(last['surfaces'])} surfaces re-acquired; "
             f"{len(last['properties'])} properties (none re-minted); checks hold"])


def test_reacquire_determinism():
    ganz = ss.diffuse(NA, NE, "E", TD)
    sched = [ss.render(STD, "E", TD), ganz, ss.render(STD, "D65", TD)]
    a = _run_grids(sched, reacquire=True)
    b = _run_grids(sched, reacquire=True)
    for x, y in zip(a, b):
        assert np.array_equal(x["sid"], y["sid"])
        assert x["surfaces"] == y["surfaces"] and x["segments"] == y["segments"]


# ------------------------------------------------- 3. saturation

def _packet_catch_oracle(packets, receptor):
    """TEST ORACLE: caught = sum count * exp(-z^2/2) per cell (dark 0 for
    cones) -- linear in the photons by construction."""
    c, bw, _half, _dark = sf.EYE_RECEPTORS[receptor]
    out = np.zeros(NA * NE)
    for p in packets:
        out[p["row"] * NA + p["col"]] += p["count"] * math.exp(
            -0.5 * ((p["wavelength_nm"] - c) / bw) ** 2)
    return out


def _quantisation_bound(receptor):
    """|caught - expected| per cell under cumulative rounding: each bin's count
    is off by < 1 quantum, so the catch is off by < sum_l exp(-z^2/2)."""
    c, bw, _h, _d = sf.EYE_RECEPTORS[receptor]
    return float(np.sum(np.exp(-0.5 * ((sf.grid(1) - c) / bw) ** 2)))


@pytest.fixture(scope="module")
def saturation_runs():
    out = {}
    for td in (1e3, 1e5):
        packets = ss.render(STD, "E", td)
        w = PerceivedSurfaceWorld(NA, NE, stage45=True)
        try:
            w.expose(packets)
            rec1 = {"percepts": w.eye.percepts_2d(), "looks": _clean(w.surface_looks(1)),
                    "props": _clean(w.colour_properties()), "sid": _grid(w)}
            w.expose(packets)
            rec2 = {"checks": _clean(w.checks(2)), "percepts": w.eye.percepts_2d(),
                    "props": _clean(w.colour_properties())}
        finally:
            w.stop()
        out[td] = (packets, rec1, rec2)
    return out


def test_saturation_catches_linear_checks_hold_looks_compress(saturation_runs):
    rows = []
    act_max = {}
    for td, (packets, r1, r2) in saturation_runs.items():
        acts = np.array([[p["receptors"][k]["activation"] for k in "lms"]
                         for p in r1["percepts"]])
        act_max[td] = (float(acts.min()), float(acts.max()))
        exp_c = ss.expected_catches(STD, "E", td)
        for k, ch in zip("lms", CH):
            eng = np.array([p["receptors"][k]["caught_quanta"] for p in r1["percepts"]])
            orc = _packet_catch_oracle(packets, k)
            # (a) the catch is the photon-linear sum, whatever the activation
            assert np.allclose(eng, orc, rtol=1e-12, atol=1e-9), (td, k)
            # (b) and agrees with the continuous expected catch to quantisation
            assert np.all(np.abs(eng - exp_c[k].ravel()) <= _quantisation_bound(k)), (td, k)
            # (c) every property = the lattice of the linear catches
            for prop in r1["props"]:
                m = (r1["sid"] == prop["sid"]).ravel()
                assert prop["p" + ch] == float(np.round(orc[m].mean())), (td, ch, prop["sid"])
        # (d) E -> E: every rung-1 check holds with residual 0, rung 2 holds
        assert len(r2["checks"]) == len(r1["props"])
        assert all(c["status"] == "holds" and c["resid_max"] == 0.0
                   and c["pooled_status"] == "holds_pooled" for c in r2["checks"])
        assert r2["props"] == r1["props"]
        rg = [l["rg"] for l in r1["looks"]]
        by = [l["by"] for l in r1["looks"]]
        rows.append(f"{td:>8.0f} td: activation {acts.min():.3f}..{acts.max():.3f}; "
                    f"look rg range {max(rg) - min(rg):.4f}, by range {max(by) - min(by):.4f}; "
                    f"E->E checks {len(r2['checks'])}/{len(r2['checks'])} hold resid 0")
    lo, hi = saturation_runs[1e3][1], saturation_runs[1e5][1]
    # saturation is real at 1e5 td: every cone activation above the 1e3 maximum
    assert act_max[1e5][0] > act_max[1e3][1]
    # looks compress: the across-surface spread of rg and by shrinks
    for key in ("rg", "by"):
        spread = {td: max(l[key] for l in r["looks"]) - min(l[key] for l in r["looks"])
                  for td, r in ((1e3, lo), (1e5, hi))}
        assert spread[1e5] < spread[1e3], key
    # descriptor p/pa: same surfaces, different lattice grain
    dmax = max(abs(a["p" + ch] / a["pa" + ch] - b["p" + ch] / b["pa" + ch])
               for a, b in zip(lo["props"], hi["props"]) for ch in CH)
    rows.append(f"max |p/pa(1e5) - p/pa(1e3)| over surfaces/channels = {dmax:.5f} "
                f"(1e3-td lattice grain)")
    _report("saturation: property path vs looks", rows)


# ------------------------------------------------- 4. recall

def test_recall_property_without_looking():
    w = PerceivedSurfaceWorld(NA, NE, stage45=True, recall=True)
    try:
        assert all(s["rules_skipped"] == [] for s in w.load_summaries)
        w.expose(ss.render(STD, "E", TD))
        w.expose(ss.diffuse(NA, NE, "E", TD, filter="eyelid"))   # eyes closed
        sid3 = _sid_of(_grid(w, "prev_sid"), GT, 3)
        props = {p["sid"]: p for p in _clean(w.colour_properties())}
        before = w.counts()
        n_nodes, types_before = w.s.node_count(), {
            n["type"] for n in w.s.graph_to_dict()["nodes"]}
        cue = w.recall(sid3)
        cue_missing = w.recall(10 ** 6)
        after = w.counts()
        assert after == before                     # no look, no property, no check
        assert w.s.node_count() == n_nodes + 4     # 2 cues + 2 recollections
        new_types = {n["type"] for n in w.s.graph_to_dict()["nodes"]} - types_before
        assert new_types == {"RecallCue", "Recollection"}
        recs = w.recollections()
        hit = next(r for r in recs if r["sid"] == sid3)
        miss = next(r for r in recs if r["sid"] == 10 ** 6)
        assert hit["status"] == "recalled" and hit["epoch_requested"] == w.eye._epoch
        assert hit["provenance_kind"] == "recalled"
        assert hit["observation_status"] == "not_observed"
        assert hit["recalls"] == [props[sid3]]
        assert w.edges_of(cue, "answered_by") == [hit["_nid"]]
        assert (miss["status"], miss["reason"]) == ("no_property", "no_surface")
        assert miss["recalls"] == []
        assert w.edges_of(cue_missing, "answered_by") == [miss["_nid"]]
        _report("recall (after an eyelid exposure: no SurfaceLook possible)",
                [f"sid {sid3}: {hit['status']} -> ColourProperty p="
                 f"{[props[sid3]['p' + ch] for ch in CH]} minted epoch {hit['minted_epoch']}",
                 f"sid 10^6: {miss['status']} ({miss['reason']}); counts unchanged {after}"])
    finally:
        w.stop()


def test_recall_surface_without_property_and_flag_off():
    w = PerceivedSurfaceWorld(NA, NE, stage45=True, colour=False, recall=True)
    off = PerceivedSurfaceWorld(NA, NE, stage45=True, recall=False)
    try:
        for x in (w, off):
            x.expose(ss.render(STD, "E", TD))
        sid = _sid_of(_grid(w), GT, 3)
        w.recall(sid)
        rec = w.recollections()
        assert [(r["status"], r["reason"]) for r in rec] == [("no_property", "no_property")]
        off.recall(sid)
        assert off.s.nodes("Recollection") == []
        assert w.counts()["SurfaceLook"] == off.counts()["SurfaceLook"]
    finally:
        w.stop()
        off.stop()


# ------------------------------------------------- 5. concept link

def _theory():
    return importlib.import_module("scripts.marys_room_broad_theory")


def test_concept_prototypes_from_frozen_anchors():
    th = _theory()
    with open(os.path.join(ROOT, "results", "marys_room_broad_armA.json")) as f:
        anchors = json.load(f)["anchors"]
    concepts = {n["attrs"]["name"]: n["attrs"] for n in _seed("colour_concept_link")["nodes"]
                if n["type"] == "ColourConcept"}
    assert set(concepts) == set(th.HUE4)
    white = sf.lms_from_spd(sf.illuminant("E", 1))
    for name, c in concepts.items():
        a = anchors[name]
        lms = np.array(a.get("lms_per_unit_energy", a.get("lms")))
        Ln, Mn, Sn = lms / white
        rg, by = Ln - Mn, Sn - 0.5 * (Ln + Mn)
        assert math.hypot(c["proto_rg"], c["proto_by"]) == pytest.approx(1.0, abs=1e-12)
        assert c["proto_rg"] == pytest.approx(rg / math.hypot(rg, by), abs=1e-12)
        assert c["proto_by"] == pytest.approx(by / math.hypot(rg, by), abs=1e-12)
    _report("ColourConcept prototypes (white-normalised CIE 2-deg anchors)",
            [f"{n:10s} ({c['proto_rg']:+.4f}, {c['proto_by']:+.4f}) "
             f"{c['proto_angle_deg']:+.2f} deg" for n, c in concepts.items()])


def _concept_run(td, layout_seed=None):
    scene = ss.standard_mondrian(seed=layout_seed)
    w = PerceivedSurfaceWorld(NA, NE, stage45=True, concepts=True)
    try:
        assert all(s["rules_skipped"] == [] for s in w.load_summaries)
        w.expose(ss.render(scene, "E", td))
        links = _clean(w.concept_links())
        concepts = _clean(w.colour_concepts())
        sid = _grid(w)
    finally:
        w.stop()
    return scene, links, concepts, sid


def _oracle_angles(prop, concepts):
    r = {ch: prop["p" + ch] / prop["pa" + ch] for ch in CH}
    d = (r["L"] - r["M"], r["S"] - 0.5 * (r["L"] + r["M"]))
    out = {}
    for c in concepts:
        u = (c["proto_rg"], c["proto_by"])
        out[c["name"]] = math.atan2(abs(d[0] * u[1] - d[1] * u[0]), d[0] * u[0] + d[1] * u[1])
    return d, out


@pytest.mark.parametrize("td", [100.0, 1000.0])
def test_concept_link_e_mondrian_accuracy_reported(td):
    th = _theory()
    scene, links, concepts, sid = _concept_run(td)
    gt = scene.label_map()
    by_sid = {p["sid"]: p for p in links}
    rows, n_ok, n_scored = [], 0, 0
    for p in links:
        d, ang = _oracle_angles(p, concepts)
        st = p["concept_status"]
        assert st in ("categorised", "achromatic", "tied", "no_anchor")
        if st == "categorised":
            best = min(ang, key=ang.get)
            srt = sorted(ang.values())
            assert p["categorised_as"] == [best] == [p["concept"]]
            assert p["concept_angle_deg"] == pytest.approx(math.degrees(srt[0]), abs=1e-9)
            assert p["concept_margin_deg"] == pytest.approx(
                math.degrees(srt[1] - srt[0]), abs=1e-9)
        else:
            assert p["categorised_as"] == []
        if st == "achromatic":
            assert d == (0.0, 0.0)
    rows.append(f"{'patch':>5s} {'reflectance':22s} {'truth hue4':11s} {'purity':>6s} "
                f"{'concept':11s} {'angle':>6s} {'margin':>6s}")
    for pid in [ss.BACKGROUND_ID] + scene.patch_ids():
        s = _sid_of(sid, gt, pid)
        shared = len(set(gt[sid == s].ravel().tolist())) > 1
        p = by_sid[s]
        spd = sf.illuminant("E", 1) * ss.reflectance_spd(scene.reflectance_of(pid))
        tr = th.truth_for(spd, "E")
        concept = p.get("concept") or p["concept_status"]
        scored = tr["hue4"] != "achromatic" and not shared
        if scored:
            n_scored += 1
            n_ok += int(concept == tr["hue4"])
        note = "merged surface: excluded" if shared else (
            "achromatic: excluded" if tr["hue4"] == "achromatic" else
            ("ok" if concept == tr["hue4"] else "WRONG"))
        rows.append(f"{pid:5d} {str(scene.reflectance_of(pid)):22s} {tr['hue4']:11s} "
                    f"{tr['excitation_purity']:6.3f} {concept:11s} "
                    f"{p.get('concept_angle_deg', float('nan')):6.1f} "
                    f"{p.get('concept_margin_deg', float('nan')):6.1f}  {note}")
    rows.append(f"accuracy {n_ok}/{n_scored} = {n_ok / max(n_scored, 1):.3f} "
                f"(chromatic, single-patch surfaces)")
    _report(f"concept link, standard Mondrian under E at {td:.0f} td "
            f"(Mary's research concept vs dominant-wavelength hue4 truth)", rows)


def test_concept_link_determinism():
    a = _concept_run(TD)[1]
    b = _concept_run(TD)[1]
    assert a == b


# ------------------------------------------------- 6. common-fate motion

def _new_onsets(w, seen):
    out = []
    for nid in w.s.nodes("RetinalOnsetEvent"):
        if nid in seen:
            continue
        seen.add(nid)
        a = w.s.node(nid)["attrs"]
        out.append((int(a["column_index"]), int(a["row_index"]), int(a["epoch"])))
    return out


def _mgrp_oracle(w, onsets, polys):
    """TEST ORACLE of seg_mgrp from the onset events and polygon spans only."""
    epoch = w.eye._epoch
    fired = {(c, r) for c, r, e in onsets if e == epoch}
    out = np.full((w.n_el, w.n_az), -1.0)
    n_cells = w.n_az * w.n_el
    for r in range(w.n_el):
        for c in range(w.n_az):
            inside = [p for p in polys if p["col_min"] <= c <= p["col_max"]
                      and p["row_min"] <= r <= p["row_max"]]
            if (c, r) in fired and len(inside) == 1:
                p = inside[0]
                out[r, c] = ((p["row_min"] * w.n_az + p["col_min"]) * n_cells
                             + p["row_max"] * w.n_az + p["col_max"])
    return out


def _motion_run(pid, n_static, motion):
    w = PerceivedSurfaceWorld(NA, NE, motion_segments=motion)
    seen, rec = set(), []
    try:
        assert all(s["rules_skipped"] == [] for s in w.load_summaries)
        scenes = [STD] * n_static + [ss.translate_patch(STD, pid, k, 0) for k in range(1, 5)]
        for k, sc in enumerate(scenes):
            w.expose(ss.render(sc, "E", TD))
            ep = w.eye._epoch
            onsets = _new_onsets(w, seen)
            polys = w.polygons(ep)
            gt = sc.label_map()
            g = _grid(w)
            r = {"step": k - n_static + 1, "epoch": ep, "n_onsets": len(onsets),
                 "onset_cols": sorted({c for c, _r, _e in onsets}),
                 "polys": polys, "label": _grid(w, "seg_label"), "sid": g,
                 "sid_pid": sorted(set(g[gt == pid].ravel().tolist())),
                 "sid_6": sorted(set(g[gt == 6].ravel().tolist())),
                 "motion_segs": _clean(w.motion_segments_current()),
                 "segments": _clean(w.segments(epoch=ep)),
                 "surfaces": w.persistent_surfaces()}
            if motion:
                r["mgrp"] = _grid(w, "seg_mgrp")
                assert np.array_equal(r["mgrp"], _mgrp_oracle(w, onsets, polys))
            rec.append(r)
    finally:
        w.stop()
    return rec


def _motion_rows(rec):
    return [f"step {r['step']:+d} ep {r['epoch']:2d}: onsets {r['n_onsets']:3d} "
            f"cols {r['onset_cols'][:6]}{'...' if len(r['onset_cols']) > 6 else ''}; "
            f"polygons {[(p['col_min'], p['col_max'], p['row_min'], p['row_max'], round(p['coherence'], 3)) for p in r['polys']]}; "
            f"motion segs {[(s['n_cells'], s.get('sid'), s.get('decision'), s.get('birth_reason')) for s in r['motion_segs']]}; "
            f"patch sids {r['sid_pid']} patch-6 sids {r['sid_6']}" for r in rec]


@pytest.fixture(scope="module")
def motion7():
    return {"lum": _motion_run(7, 1, False), "mot": _motion_run(7, 1, True),
            "mot_pre": _motion_run(7, 8, True)}


def test_motion_isoluminant_patch7_reported(motion7):
    lum, mot, pre = motion7["lum"], motion7["mot"], motion7["mot_pre"]
    a, b = ss.ISOLUMINANT_PAIR
    # where the motion route produced no motion group, the partition and the
    # identities are exactly the luminance-only ones
    for x, y in zip(lum, mot):
        if not (y["mgrp"] >= 0).any():
            assert np.array_equal(x["label"], y["label"])
            assert np.array_equal(x["sid"], y["sid"])
            assert x["surfaces"] == y["surfaces"]
    ec = ss.expected_catches(STD, "E", TD)
    catch = {pid: {k: float(ec[k][GT == pid].mean()) for k in ("rod", "lm")}
             for pid in (ss.BACKGROUND_ID, a, b)}
    merged0 = _sid_of(lum[0]["sid"], GT, a) == _sid_of(lum[0]["sid"], GT, b)
    sep = [r["sid_pid"] != r["sid_6"] for r in lum[1:]]
    _report("motion arm: isoluminant patch 7 moved +1 col x 4 over the static "
            "standard Mondrian, 1000 td",
            [f"expected catch (mean): bg {catch[0]}, patch 6 {catch[a]}, patch 7 {catch[b]} "
             f"-- L+M isoluminant, rod NOT (onset path is rod-only)",
             f"static exposure: pair merged = {merged0}",
             "LUMINANCE-ONLY persistence:", *["  " + s for s in _motion_rows(lum)],
             f"  separate identity for 7 at steps 1-4: {sep}",
             "MOTION ROUTE (literal schedule, 1 static exposure):",
             *["  " + s for s in _motion_rows(mot)],
             "MOTION ROUTE (8 static pre-adapting exposures, then the moves):",
             *["  " + s for s in _motion_rows(pre[7:])]])


def test_motion_route_determinism(motion7):
    again = _motion_run(7, 1, True)
    for x, y in zip(motion7["mot"], again):
        for k in ("epoch", "n_onsets", "polys", "motion_segs", "segments", "surfaces"):
            assert x[k] == y[k], k
        for k in ("label", "sid", "mgrp"):
            assert np.array_equal(x[k], y[k]), k


def test_motion_route_positive_control_dark_patch():
    """Route-liveness control (not the falsifier): the dark patch 10 (darker
    than the background on the rod) moved after pre-adaptation. Its vacated
    cells brighten, the rod onsets form a coherent component, and the route
    offers that cell set to persistence."""
    rec = _motion_run(10, 8, True)
    moves = rec[8:]
    live = [r for r in moves if r["motion_segs"]]
    assert live, "no motion segment in the control"
    for r in live:
        for s in r["motion_segs"]:
            assert s["decision"] in ("continue", "birth")
    _report("motion route control: dark patch 10, 8 static exposures then +1 col x 4",
            _motion_rows(moves))
