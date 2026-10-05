"""Mary's Room stage 4.3 + 4.4: perceived, persistent, colour-free surfaces.

Seeds (graph rules, built by tools/build_surface_{segmentation,persistence}_seed.py):
  surface_segmentation  luminance Y = L+M caught quanta; adjacent cells are the
                        same surface iff |dY| <= Sqrt(Y_a + Y_b); min-label flood;
                        one SurfaceSegment per component after a completion guard.
  surface_persistence   PersistentSurface identity by cell overlap
                        (track_comps 2*ov >= min(count)), ambiguity refused.
Adapter: domains/perceived_surface_world.py (mechanical). The eye is driven
synchronously: submit_photons_2d -> run_cognitive_tasks(1) -> run_rules, then
prune_settled_tasks.

Scene: spectral_scene.standard_mondrian (24x16) at 1000 td, deterministic
(cumulative) quantisation unless stated.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from domains import spectral_scene as ss
from domains.perceived_surface_world import PerceivedSurfaceWorld

TD = 1000.0
NA, NE = ss.STANDARD_N_AZ, ss.STANDARD_N_EL
SEED_TYPES = {"SurfaceSegmentationParams", "SegmentationState",
              "SurfacePersistenceParams", "PersistenceState", "SurfaceCounter"}
NEW_TYPES = {"SurfaceSegment", "PersistentSurface"}
NEW_CELL_KEYS = {"seg_epoch", "seg_label", "seg_Y", "seg_has_edge", "seg_joined",
                 "ps_epoch", "prev_sid", "cur_sid"}


# ----------------------------------------------------------------- helpers

def _snapshot(w: PerceivedSurfaceWorld) -> dict:
    epoch = w.eye._epoch
    cells = w.cells()
    segs = [{k: v for k, v in s.items() if k != "_nid"}
            for s in w.segments(epoch=epoch)]
    return {
        "epoch": epoch,
        "label": np.array([c.get("seg_label") for c in cells]).reshape(w.n_el, w.n_az),
        "Y": np.array([c.get("seg_Y") for c in cells]).reshape(w.n_el, w.n_az),
        "cur_sid": np.array([c.get("cur_sid") for c in cells]).reshape(w.n_el, w.n_az),
        "segments": segs,
        "surfaces": w.persistent_surfaces(),
        "state": w.state(),
    }


def _run(exposures, n_az=NA, n_el=NE):
    w = PerceivedSurfaceWorld(n_az, n_el)
    snaps = []
    try:
        for packets in exposures:
            w.expose(packets)
            snaps.append(_snapshot(w))
        timings = list(w.timings)
        integrity = _segment_integrity(w)
    finally:
        w.stop()
    return snaps, timings, integrity


def _segment_integrity(w):
    """For the CURRENT segments: in_segment member count == n_cells."""
    out = []
    for s in w.segments(current_only=True):
        members = w.s.in_neighbours(s["_nid"], "in_segment")
        out.append((s["root"], len(members), s["n_cells"]))
    return out


def _oracle_components(Y: np.ndarray) -> np.ndarray:
    """TEST ORACLE: 4-connected components of the same-surface relation
    |dY| <= sqrt(Ya+Yb), labelled by min flat index."""
    n_el, n_az = Y.shape
    lab = np.arange(n_el * n_az).reshape(n_el, n_az)
    changed = True
    while changed:
        changed = False
        for r in range(n_el):
            for c in range(n_az):
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < n_el and 0 <= cc < n_az:
                        a, b = Y[r, c], Y[rr, cc]
                        if abs(a - b) <= np.sqrt(a + b) and lab[rr, cc] < lab[r, c]:
                            lab[r, c] = lab[rr, cc]
                            changed = True
    return lab


def _iou_table(gt: np.ndarray, label: np.ndarray) -> dict:
    out = {}
    for pid in sorted(set(gt.ravel().tolist())):
        g = gt == pid
        best, best_root = 0.0, None
        for root in set(label[g].ravel().tolist()):
            s = label == root
            iou = (g & s).sum() / (g | s).sum()
            if iou > best:
                best, best_root = iou, root
        out[pid] = (float(best), best_root)
    return out


def _sid_of_patch(snap, gt, pid):
    vals = set(snap["cur_sid"][gt == pid].ravel().tolist())
    assert len(vals) == 1, (pid, vals)
    return vals.pop()


def _surface(snap, sid):
    return next(p for p in snap["surfaces"] if p["sid"] == sid)


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items()
                if k not in ("service_wall_micros", "wall_micros")}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def _export_without_seed_nodes(w) -> str:
    """Whole-graph export with the seeds' own param/state nodes (and their
    edges) removed and node ids re-ranked, so it is comparable to an eye that
    never loaded the seeds."""
    d = _strip(w.s.graph_to_dict())
    drop = {n["id"] for n in d["nodes"] if n["type"] in SEED_TYPES}
    keep = [n for n in d["nodes"] if n["id"] not in drop]
    rank = {n["id"]: i for i, n in enumerate(keep)}
    nodes = [{"id": rank[n["id"]], "type": n["type"], "attrs": n["attrs"]} for n in keep]
    edges = sorted(
        ({"src": rank[e["src"]], "tgt": rank[e["tgt"]], "type": e["type"],
          "attrs": e["attrs"]}
         for e in d["edges"] if e["src"] not in drop and e["tgt"] not in drop),
        key=lambda e: (e["src"], e["type"], e["tgt"]))
    return json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, default=repr)


def _report(title, rows):
    print(f"\n{title}")
    for r in rows:
        print("  " + r)


STD = ss.standard_mondrian()
GT = STD.label_map()


# ----------------------------------------------------------------- fixtures

@pytest.fixture(scope="module")
def illum_run():
    """E, E, D65, A on the static standard Mondrian."""
    exposures = [ss.render(STD, "E", TD), ss.render(STD, "E", TD),
                 ss.render(STD, "D65", TD), ss.render(STD, "A", TD)]
    return _run(exposures)


# ------------------------------------------------- 0. adjacency precondition

def test_adjacency_edges_join_cells_symmetrically_4_neighbour():
    w = PerceivedSurfaceWorld(6, 4, load_seeds=False)
    try:
        d = w.s.graph_to_dict()
        types = {n["id"]: n["type"] for n in d["nodes"]}
        idx = {n["id"]: n["attrs"].get("cell_index") for n in d["nodes"]}
        adj = {(idx[e["src"]], idx[e["tgt"]]) for e in d["edges"]
               if e["type"] == "adjacent_receptor"}
        assert all(types[e["src"]] == types[e["tgt"]] == "RetinalColumn"
                   for e in d["edges"] if e["type"] == "adjacent_receptor")
        assert all((b, a) in adj for a, b in adj)
        expect = set()
        for r in range(4):
            for c in range(6):
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    if 0 <= r + dr < 4 and 0 <= c + dc < 6:
                        expect.add((r * 6 + c, (r + dr) * 6 + c + dc))
        assert adj == expect
    finally:
        w.stop()


# ----------------------------------------------------------------- 1. off

def test_flags_off_no_new_nodes_and_eye_byte_identical():
    bare = PerceivedSurfaceWorld(NA, NE, load_seeds=False)
    off = PerceivedSurfaceWorld(NA, NE, segmentation=False, persistence=False)
    try:
        assert all(s["rules_skipped"] == [] for s in off.load_summaries)
        for packets in (ss.render(STD, "E", TD), ss.render(STD, "A", TD)):
            bare.expose(packets)
            off.expose(packets)
        for t in NEW_TYPES:
            assert off.s.nodes(t) == []
        assert all(not (NEW_CELL_KEYS & set(c)) for c in off.cells())
        assert off.s.node_count() == bare.s.node_count() + len(SEED_TYPES)
        assert off.s.edge_count() == bare.s.edge_count() + len(SEED_TYPES)
        assert off.eye.percepts_2d() == bare.eye.percepts_2d()
        assert off.eye.carve_polygons_2d() == bare.eye.carve_polygons_2d()
        assert _export_without_seed_nodes(off) == _export_without_seed_nodes(bare)
        # seed state untouched
        st = off.state()
        assert st["SegmentationState"] == [{"done_epoch": -1, "final_epoch": -1}]
        assert st["PersistenceState"] == [{"ready_epoch": -1}]
        assert st["SurfaceCounter"] == [{"next_sid": 0}]
    finally:
        bare.stop()
        off.stop()


def test_persistence_alone_does_nothing_without_segmentation():
    w = PerceivedSurfaceWorld(NA, NE, segmentation=False, persistence=True)
    try:
        w.expose(ss.render(STD, "E", TD))
        assert w.s.nodes("SurfaceSegment") == []
        assert w.s.nodes("PersistentSurface") == []
        assert all(not (NEW_CELL_KEYS & set(c)) for c in w.cells())
    finally:
        w.stop()


# ------------------------------------------------- 2. segmentation vs truth

def test_segmentation_recovers_patches_isoluminant_pair_merges(illum_run):
    snaps, timings, _ = illum_run
    e = snaps[0]
    label = e["label"]
    # (a) the graph partition IS the declared criterion's connected components
    #     (proves flood fixpoint before mint: one segment per final component)
    assert np.array_equal(label, _oracle_components(e["Y"]))
    roots = sorted(set(label.ravel().tolist()))
    assert sorted(s["root"] for s in e["segments"]) == roots
    for s in e["segments"]:
        assert s["n_cells"] == int((label == s["root"]).sum())
        assert s["has_boundary"] == 1.0
        assert s["current"] == 1.0
    # (b) ground truth: every patch exact except the declared isoluminant pair
    iou = _iou_table(GT, label)
    a, b = ss.ISOLUMINANT_PAIR
    pair_union = (GT == a) | (GT == b)
    pair_roots = set(label[pair_union].ravel().tolist())
    assert len(pair_roots) == 1, "isoluminant pair predicted to MERGE"
    assert np.array_equal(label == pair_roots.pop(), pair_union)
    for pid, (v, _root) in iou.items():
        if pid in ss.ISOLUMINANT_PAIR:
            assert v == pytest.approx(0.5)
        else:
            assert v == 1.0, (pid, v)
    assert len(e["segments"]) == len(iou) - 1
    _report("per-patch IoU, E 1000 td (patch: IoU, root)",
            [f"{pid:2d} {STD.reflectance_of(pid)!s:22s} IoU={v:.3f} root={r}"
             for pid, (v, r) in iou.items()])
    # D65 keeps the merge; A splits the pair (no longer isoluminant)
    for snap, merged in ((snaps[2], True), (snaps[3], False)):
        lab = snap["label"]
        assert np.array_equal(lab, _oracle_components(snap["Y"]))
        assert (len(set(lab[pair_union].ravel().tolist())) == 1) == merged
        for pid in set(GT.ravel().tolist()) - set(ss.ISOLUMINANT_PAIR):
            assert _iou_table(GT, lab)[pid][0] == 1.0
    _report("timing per exposure (s), E,E,D65,A", [", ".join(f"{t:.3f}" for t in timings)])


def test_segment_membership_edges_match_counts(illum_run):
    _, _, integrity = illum_run
    assert integrity and all(n == m for _r, n, m in integrity)


# ----------------------------------------------------------------- 3. ganzfeld

def test_ganzfeld_one_boundaryless_component_not_a_surface():
    ganz = ss.diffuse(NA, NE, "E", TD)
    snaps, timings, _ = _run([ganz, ss.render(STD, "E", TD), ganz])
    g = snaps[0]
    assert len(g["segments"]) == 1
    assert g["segments"][0]["n_cells"] == NA * NE
    assert g["segments"][0]["has_boundary"] == 0.0
    assert "decision" not in g["segments"][0]
    assert g["surfaces"] == []
    assert (g["cur_sid"] == -1).all()
    # a Mondrian then births surfaces; a second ganzfeld births none, all coast
    m, g2 = snaps[1], snaps[2]
    n = len(m["surfaces"])
    assert n == len(m["segments"]) > 0
    assert len(g2["surfaces"]) == n
    assert all(p["coast"] == 1 and p["status"] == "coasting" for p in g2["surfaces"])
    assert (g2["cur_sid"] == -1).all()
    _report("timing per exposure (s), ganz,E,ganz", [", ".join(f"{t:.3f}" for t in timings)])


# ----------------------------------------------------------------- 4. persistence

def test_same_scene_twice_same_sids(illum_run):
    snaps, _, _ = illum_run
    e1, e2 = snaps[0], snaps[1]
    assert (e1["cur_sid"] >= 0).all()
    assert np.array_equal(e1["cur_sid"], e2["cur_sid"])
    assert len(e2["surfaces"]) == len(e1["surfaces"])
    assert all(s["decision"] == "continue" for s in e2["segments"])
    assert all(p["status"] == "tracked" and p["last_epoch"] == e2["epoch"]
               for p in e2["surfaces"])


def test_illuminant_change_keeps_identity_except_declared_pair_split(illum_run):
    snaps, _, _ = illum_run
    e, d65, a_ill = snaps[1], snaps[2], snaps[3]
    # E -> D65: every cell keeps its sid (identity colour-free; the pair stays merged)
    assert np.array_equal(e["cur_sid"], d65["cur_sid"])
    assert not np.array_equal(e["Y"], d65["Y"])  # non-vacuous: the catches changed
    # D65 -> A: all patches keep their sid except the isoluminant pair, which
    # SPLITS under A; both halves claim the merged surface with equal overlap,
    # so the match is REFUSED: both born new, the merged surface coasts 'split'.
    pair = set(ss.ISOLUMINANT_PAIR)
    for pid in set(GT.ravel().tolist()) - pair:
        assert _sid_of_patch(a_ill, GT, pid) == _sid_of_patch(d65, GT, pid), pid
    old = _sid_of_patch(d65, GT, ss.ISOLUMINANT_PAIR[0])
    assert old == _sid_of_patch(d65, GT, ss.ISOLUMINANT_PAIR[1])
    new = [_sid_of_patch(a_ill, GT, pid) for pid in ss.ISOLUMINANT_PAIR]
    assert len(set(new)) == 2 and old not in new
    assert all(_surface(a_ill, s)["born_epoch"] == a_ill["epoch"] for s in new)
    merged = _surface(a_ill, old)
    assert (merged["status"], merged["claims"], merged["coast"]) == ("split", 2, 1)
    pair_segs = [s for s in a_ill["segments"] if s["sid"] in new]
    assert [s["birth_reason"] for s in pair_segs] == ["refused_ambiguous"] * 2
    _report("illuminant schedule E,E,D65,A: sid per patch",
            [f"{pid:2d} " + " ".join(f"{_sid_of_patch(s, GT, pid):3d}" for s in snaps)
             for pid in sorted(set(GT.ravel().tolist()))])


def test_swap_patches_sids_follow_position():
    swapped = ss.swap_patches(STD, 2, 3)
    snaps, timings, _ = _run([ss.render(STD, "E", TD), ss.render(swapped, "E", TD)])
    before, after = snaps
    assert np.array_equal(before["cur_sid"], after["cur_sid"])
    for pid in (2, 3):  # non-vacuous: the content at those positions changed
        assert not np.allclose(before["Y"][GT == pid], after["Y"][GT == pid])
    assert np.allclose(before["Y"][GT == 2], after["Y"][GT == 3])
    _report("timing per exposure (s), swap", [", ".join(f"{t:.3f}" for t in timings)])


def test_translate_one_cell_keeps_sid():
    moved = ss.translate_patch(STD, 10, 1, 0)
    snaps, _, _ = _run([ss.render(STD, "E", TD), ss.render(moved, "E", TD)])
    before, after = snaps
    gt2 = moved.label_map()
    sid10 = _sid_of_patch(before, GT, 10)
    assert _sid_of_patch(after, gt2, 10) == sid10
    for pid in set(GT.ravel().tolist()) - {10}:
        assert _sid_of_patch(after, gt2, pid) == _sid_of_patch(before, GT, pid)
    assert len(after["surfaces"]) == len(before["surfaces"])
    assert _surface(after, sid10)["status"] == "tracked"


def test_translate_beyond_width_births_new_and_old_coasts():
    w = STD.rect(10)[4]
    moved = ss.translate_patch(STD, 10, w + 1, 0)
    gt2 = moved.label_map()
    assert not ((GT == 10) & (gt2 == 10)).any()   # no overlap at all
    snaps, _, _ = _run([ss.render(STD, "E", TD), ss.render(moved, "E", TD)])
    before, after = snaps
    old = _sid_of_patch(before, GT, 10)
    new = _sid_of_patch(after, gt2, 10)
    assert new != old
    assert _surface(after, new)["born_epoch"] == after["epoch"]
    o = _surface(after, old)
    assert (o["status"], o["coast"]) == ("coasting", 1)
    for pid in set(GT.ravel().tolist()) - {10}:
        assert _sid_of_patch(after, gt2, pid) == _sid_of_patch(before, GT, pid)


# ----------------------------------------------------------------- 5. same colour twice

def test_same_reflectance_two_locations_two_sids():
    scene = ss.Mondrian(12, 6, ((1, "red", 1, 1, 3, 3), (2, "red", 7, 1, 3, 3)))
    gt = scene.label_map()
    snaps, _, _ = _run([ss.render(scene, "E", TD)] * 2, n_az=12, n_el=6)
    for snap in snaps:
        assert np.allclose(snap["Y"][gt == 1], snap["Y"][gt == 2])   # same colour
        s1, s2 = _sid_of_patch(snap, gt, 1), _sid_of_patch(snap, gt, 2)
        assert s1 != s2 and s1 >= 0 and s2 >= 0
        assert len(snap["segments"]) == 3
    assert np.array_equal(snaps[0]["cur_sid"], snaps[1]["cur_sid"])


# ----------------------------------------------------------------- 6. determinism

def test_determinism(illum_run):
    snaps, _, _ = illum_run
    exposures = [ss.render(STD, "E", TD), ss.render(STD, "E", TD),
                 ss.render(STD, "D65", TD), ss.render(STD, "A", TD)]
    again, _, _ = _run(exposures)
    for a, b in zip(snaps, again):
        assert a["epoch"] == b["epoch"]
        assert np.array_equal(a["label"], b["label"])
        assert np.array_equal(a["cur_sid"], b["cur_sid"])
        assert a["segments"] == b["segments"]
        assert a["surfaces"] == b["surfaces"]
        assert a["state"] == b["state"]


def test_poisson_shot_noise_segmentation_reported():
    """Shot-noise grain under real Poisson catches (seeded). Reported, with the
    one structural assertion that the graph partition equals the criterion's
    components (the IoU is a measurement, not a pass condition)."""
    snaps, _, _ = _run([ss.render(STD, "E", TD, method="poisson", seed=4300)])
    lab = snaps[0]["label"]
    assert np.array_equal(lab, _oracle_components(snaps[0]["Y"]))
    iou = _iou_table(GT, lab)
    _report(f"Poisson E 1000 td: {len(snaps[0]['segments'])} segments; per-patch IoU",
            [f"{pid:2d} IoU={v:.3f}" for pid, (v, _r) in iou.items()])
