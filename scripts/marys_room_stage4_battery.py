"""Mary's Room stage 4 -- the preregistered confirmatory battery (B1-B7, P1-P6).

Preregistration: docs/experiments/marys-room-stage4-prereg.md (commit f25aae47).
This script is NEW analysis code; it builds worlds ONLY through the frozen
adapter domains/perceived_surface_world.py and the frozen scene generator
domains/spectral_scene.py.  Ground-truth label maps / expected catches are used
for REPORTING and for the declared mechanical choices below only; they are
never given to the eye.

Every mechanical choice the prereg leaves open is fixed in RULES (printed and
stored before any exposure is run).  No choice depends on any outcome.

Run (from the repo root):
    PYTHONPATH=. .venv/bin/python scripts/marys_room_stage4_battery.py
    PYTHONPATH=. .venv/bin/python scripts/marys_room_stage4_battery.py --smoke
      (--smoke: crash test only -- one development-layout sequence per arm at
       1000 td, written to /tmp, no verdicts printed)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG_COMMIT = "f25aae47"
EXPECTED_ENGINE = "b6a41e3bbba6"

APPARATUS = [
    "docs/experiments/marys-room-stage4-prereg.md",
    "domains/photon_eye.py",
    "domains/spectral_scene.py",
    "domains/perceived_surface_world.py",
    "seeds/surface_segmentation.json",
    "seeds/surface_persistence.json",
    "seeds/colour_property.json",
    "seeds/looking_episode.json",
    "seeds/look_property_link.json",
    "tools/build_surface_segmentation_seed.py",
    "tools/build_surface_persistence_seed.py",
    "tools/build_colour_property_seed.py",
    "tools/build_looking_episode_seed.py",
    "tools/build_look_property_link_seed.py",
    # frozen files of the earlier (broad) study
    "domains/spectral_forward.py",
    "scripts/marys_room_broad.py",
    "scripts/marys_room_broad_theory.py",
    "scripts/marys_room_broad_audit.py",
    "scripts/marys_room_broad_boundary.py",
    "scripts/marys_room_broad_review_fixes.py",
    "results/marys_room_broad.json",
    "results/marys_room_broad_armA.json",
    "results/marys_room_broad_audit.json",
    "results/marys_room_broad_boundary.json",
    "results/marys_room_broad_freeze.json",
    "results/marys_room_broad_review_fixes.json",
    "results/marys_room_broad_stimuli.json",
    "results/marys_room_broad_per_stimulus.csv",
    # Rust source
    "runners/dsl/src",
]
ENGINE_FILES = ["runners/dsl/python/substrate_rs/_native.abi3.so",
                "runners/dsl/python/substrate_rs/_native.build.json"]

TDS = (100.0, 1000.0)
HELD_OUT = tuple(range(1, 9))
DEV = None
LAYOUTS = (DEV,) + HELD_OUT
WILSON_Z = 1.959963984540054
B1_ILLS = ("E", "D65", "A", "E")
B1_LABELS = ("E1", "D65", "A", "E_return")
B2_N_ADAPT, B2_WL, B2_QUANTA = 20, 610.0, 2000
B3_ILLS, B3_TDS = ("E", "D65", "A"), (1000.0, 1.0e4)
B5_STEPS = [(1, 0)] * 4 + [(6, 0)]
B7_LAYOUTS, B7_SEEDS = (1, 2), (7001, 7002, 7003, 7004, 7005)

RULES = {
    "R0_worlds": "PerceivedSurfaceWorld(24, 16, stage45=True) with adapter defaults "
                 "segmentation=persistence=colour=pooled=looking=True; the param nodes are "
                 "read back after build and asserted enabled==1 (and pooled==1). One fresh "
                 "world per sequence (per layout x td x arm; B3: per illuminant x td; B7: per "
                 "layout x td x Poisson seed).",
    "R1_surface_unit": "A 'surface' for per-surface reporting is a declared ground-truth patch "
                       "(ids 0=background neutral 5, 1..10) of the scene shown at that exposure "
                       "(label_map, reporting only). Its sid(s) = the set of graph cur_sid over "
                       "its cells.",
    "R2_neutral_white": "B2 'neutral' = background patch 0 (neutral 5; held-out layouts permute "
                        "only chromatic reflectances, so it is the only neutral); 'white' = patch 1.",
    "R3_exempt": "P1 exception set (per B1 sequence): a patch is criterion-boundary iff at some "
                 "exposure of the sequence some 4-adjacent cell pair (a in the patch, b in a "
                 "different patch) satisfies |Y_a - Y_b| <= sqrt(Y_a + Y_b), Y = the graph's own "
                 "seg_Y readout (the segmentation seed's join criterion).",
    "R4_silent_rebind": "A silent re-bind = a SurfaceSegment with decision 'continue' at "
                        "exposure t whose sid covers a different SET of ground-truth patches at "
                        "t than at t-1. A refused split/merge = the affected cells' segment is a "
                        "'birth' (birth_reason recorded).",
    "R5_P1_B1": "P1(B1) supported iff every non-exempt patch has one constant sid across all "
                "4 exposures AND there is no silent re-bind in any held-out B1 sequence "
                "(both tds). Exempt patches may keep or change sid.",
    "R6_hue": "Hue angle = degrees(atan2(by, rg)) of the SurfaceLook of the patch's sid; "
              "change = |wrapped difference| in [0, 180] vs exposure 1. A patch enters the hue "
              "statistics at exposure t only if at both exposure 1 and t it is covered by "
              "exactly one sid, that sid covers no other patch, and the sid has a SurfaceLook.",
    "R7_anchor": "Anchor surface of a check frame = the sid(s) whose lattice catch (cL,cM,cS) "
                 "equals the frame anchor (aL,aM,aS) on all three channels (catch of a sid "
                 "minted at that epoch = its ColourProperty p). A frame with no such sid, or "
                 "whose anchor sid was minted at that epoch, counts as rung 1 NOT holding on "
                 "the anchor in that frame.",
    "R8_P3_frames": "P3 frames/conditions are the B1 non-reference exposures (D65, A, E_return) "
                    "of held-out layouts. Non-anchor rung-1 fractions exclude anchor sids and "
                    "minted checks. The td comparison pools D65 + A frames (illuminant-change "
                    "frames) at each td; the A vs D65 comparison is made at each td. "
                    "'Rung 2 >= rung 1 in every condition': condition = (layout, td, exposure); "
                    "count holds vs holds_pooled over non-minted checks.",
    "R9_compare": "Fraction comparisons are made on point estimates; Wilson 95% intervals "
                  "(z=1.95996) are reported alongside. Comparison clauses evaluated at each td "
                  "separately: true at every td -> supported, at some -> partially, at none -> "
                  "not supported.",
    "R10_universal": "Universal clauses ('every', 'all'): all instances -> supported; at least "
                     "one but not all -> partially; none -> not supported. A prediction with "
                     "several clauses is supported iff all clauses are supported, not supported "
                     "iff all are not supported, otherwise partially.",
    "R11_B3": "B3: one fresh world and ONE exposure per (illuminant in E,D65,A) x (td in 1000, "
              "1e4): diffuse(24,16, ill, td, filter='eyelid'), cumulative quantisation.",
    "R12_B4_pair": "B4 pair: among declared patches 1..10 whose reflectance is chromatic "
                   "(name not starting with white/neutral/black -- i.e. excludes patch 1), the "
                   "pair with the largest |L+M| difference of spectral_scene.patch_report(scene, "
                   "'E', td)['lm']; ties -> lexicographically smallest (a, b).",
    "R13_B5_patch": "B5 moved patch: the lowest-id declared patch whose rect, translated by every "
                    "cumulative offset of the schedule (+1..+4 then +10 columns), stays on the "
                    "24-column sheet and never overlaps another declared patch's rect (geometry "
                    "only; identical in every layout). Schedule = spectral_scene.motion steps "
                    "[(1,0)]*4 + [(6,0)]; exposure 0 unmoved.",
    "R14_B5_verdict": "P1(B5) per sequence: the moved patch has one sid at exposures 0..4 equal "
                      "to its exposure-0 sid; at the jump (exposure 5) it has one sid never "
                      "seen before in the sequence, whose PersistentSurface born_epoch equals "
                      "that epoch, and the previous sid has status 'coasting' with coast >= 1.",
    "R15_B6_room": "B6 room Mondrian: STANDARD_LAYOUT geometry; slot i (rect order 1..10) gets "
                   "ColorChecker neutral number 19 + ((i-1) mod 6) (19 white 9.5 ... 24 black 2); "
                   "background neutral 5. Slots 4 and 10 therefore carry neutral 5 = background "
                   "(not segmentable from it). Interleaving: the two eyelid ganzfelds split the "
                   "6 room exposures into three equal runs: M M G M M G M M. Ganzfeld = "
                   "diffuse(24,16,'E', td, filter='eyelid'). Release: 3 x render("
                   "standard_mondrian(seed=k), 'E', td). All at the arm's scene_td.",
    "R16_B6_verdict": "P5 clauses per sequence: (a) node types and edge types with count > 0 "
                      "after release are a subset of those with count > 0 after the room; (b) "
                      "every chromatic patch of the release scene is covered at release "
                      "exposure 1 by one sid that has a ColourProperty minted at a release "
                      "epoch (evaluated per patch, universal); (c) SurfaceLook count and "
                      "presents_property edge count both increase during release.",
    "R17_B7": "B7: spectral_scene.illuminant_change(scene, [E,D65,A,E], td, method='poisson', "
              "seed=s) (per-exposure seed offset +index, per-cell SeedSequence). Segment count "
              "= number of SurfaceSegment nodes of that epoch. Clause 1: in every (layout, td, "
              "exposure) cell, median over the 5 seeds > deterministic B1 count of the same "
              "cell. Clause 2: at each td, rung-1 refusal fraction refused/(holds+refused) "
              "over non-minted checks of exposures 2-4 pooled over k=1,2 and seeds >= the same "
              "fraction for deterministic B1 on k=1,2.",
    "R18_determinism": "After the full battery, B1 and B3 are re-run in fresh worlds; the sha256 "
                       "of their raw records (timings excluded) must equal the first run's.",
    "R19_dev": "The development layout (seed=None) is run in every layout arm and summarised "
               "separately; it never enters a verdict.",
}


# ------------------------------------------------------------------ git checks
def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def git_checks() -> dict:
    head = git("rev-parse", "HEAD").stdout.strip()
    missing = [p for p in APPARATUS if not os.path.exists(os.path.join(ROOT, p))]
    d = git("diff", "--quiet", PREREG_COMMIT, "--", *APPARATUS)
    names = git("diff", "--name-only", PREREG_COMMIT, "--", *APPARATUS).stdout.split()
    status = git("status", "--porcelain").stdout.splitlines()
    eng = {}
    for p in ENGINE_FILES:
        fp = os.path.join(ROOT, p)
        eng[p] = hashlib.sha256(open(fp, "rb").read()).hexdigest() if os.path.exists(fp) else None
    out = {"head": head, "prereg_commit": PREREG_COMMIT,
           "apparatus_files": APPARATUS, "apparatus_missing": missing,
           "apparatus_diff_quiet_exit": d.returncode, "apparatus_diff_names": names,
           "git_status_porcelain": status, "engine_file_sha256": eng}
    if d.returncode != 0 or missing:
        print(json.dumps(out, indent=1))
        raise SystemExit("ABORT: apparatus differs from prereg commit " + PREREG_COMMIT)
    return out


# ------------------------------------------------------------------ stats
def wilson(k: int, n: int, z: float = WILSON_Z):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - h), min(1.0, c + h)]


def frac(k, n):
    return {"k": int(k), "n": int(n), "value": (k / n) if n else None, "wilson95": wilson(k, n)}


def median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else 0.5 * (xs[m - 1] + xs[m])


def universal(flags) -> str:
    flags = list(flags)
    if flags and all(flags):
        return "supported"
    if any(flags):
        return "partially"
    return "not supported"


def combine(verdicts) -> str:
    v = list(verdicts)
    if all(x == "supported" for x in v):
        return "supported"
    if all(x == "not supported" for x in v):
        return "not supported"
    return "partially"


def hue_deg(look) -> float:
    return math.degrees(math.atan2(look["by"], look["rg"]))


def dhue(a, b) -> float:
    d = abs(a - b) % 360.0
    return 360.0 - d if d > 180.0 else d


# ------------------------------------------------------------------ world I/O
def clean(row: dict) -> dict:
    return {k: v for k, v in row.items() if k != "_nid"}


def as_int(v):
    return None if v is None else int(v)


def graph_type_counts(w) -> dict:
    d = w.s.graph_to_dict()
    return {"nodes": dict(Counter(n["type"] for n in d["nodes"])),
            "edges": dict(Counter(e["type"] for e in d["edges"]))}


class Runner:
    def __init__(self, PSW, n_az, n_el):
        self.PSW, self.n_az, self.n_el = PSW, n_az, n_el
        self.build_s: list[float] = []

    def new_world(self):
        t0 = time.perf_counter()
        w = self.PSW(self.n_az, self.n_el, stage45=True)
        self.build_s.append(time.perf_counter() - t0)
        assert all(s["rules_skipped"] == [] for s in w.load_summaries), w.load_summaries
        flags = {}
        for t, keys in (("SurfaceSegmentationParams", ("enabled",)),
                        ("SurfacePersistenceParams", ("enabled",)),
                        ("ColourPropertyParams", ("enabled", "pooled")),
                        ("LookingEpisodeParams", ("enabled",))):
            nids = w.s.nodes(t)
            assert len(nids) == 1, t
            a = dict(w.s.node(nids[0])["attrs"])
            for k in keys:
                assert a[k] == 1.0, (t, k, a)
                flags[f"{t}.{k}"] = a[k]
        return w, flags

    def snapshot(self, w, gt, keep_Y: bool, types: bool = False) -> dict:
        e = int(w.eye._epoch)
        cells = w.cells()
        sid = [as_int(c.get("cur_sid")) for c in cells]
        snap = {
            "epoch": e,
            "sid_grid": sid,
            "Y_grid": [c.get("seg_Y") for c in cells] if keep_Y else None,
            "segments": [clean(s) for s in w.segments(epoch=e)],
            "surfaces": w.persistent_surfaces(),
            "checks": [clean(c) for c in w.checks(e)],
            "looks": [clean(l) for l in w.surface_looks(e)],
            "field_looks": [clean(f) for f in w.field_looks() if f.get("epoch") == e],
            "episodes_this_epoch": sum(1 for x in w.episodes() if x.get("epoch") == e),
            "frames": [clean(f) for f in w.frames() if f.get("epoch") == e],
            "properties": [clean(p) for p in w.colour_properties()],
            "counts": w.counts(),
            "patch_sids": patch_sids(gt, sid, self.n_az),
        }
        if types:
            snap["graph_types"] = graph_type_counts(w)
        return snap

    def run(self, exposures, gts, keep_Y=False, types_at=()) -> dict:
        w, flags = self.new_world()
        snaps, timings = [], []
        try:
            for i, (pk, gt) in enumerate(zip(exposures, gts)):
                timings.append(w.expose(pk))
                snaps.append(self.snapshot(w, gt, keep_Y, types=(i in types_at)))
        finally:
            w.stop()
        return {"flags": flags, "snaps": snaps, "timings": timings}


def patch_sids(gt, sid, n_az) -> dict:
    """{patch_id: sorted list of sids over its cells} (gt is None -> {})."""
    if gt is None:
        return {}
    out: dict = {}
    for r, row in enumerate(gt):
        for c, pid in enumerate(row):
            out.setdefault(int(pid), set()).add(sid[r * n_az + c])
    return {str(k): sorted(v, key=lambda x: (x is None, x)) for k, v in sorted(out.items())}


def composition(snap) -> dict:
    """{sid: frozenset of patch ids covered}."""
    comp: dict = {}
    for p, sids in snap["patch_sids"].items():
        for s in sids:
            comp.setdefault(s, set()).add(int(p))
    return {s: frozenset(v) for s, v in comp.items()}


def single(snap, pid):
    s = snap["patch_sids"].get(str(pid), [])
    return s[0] if len(s) == 1 and s[0] is not None and s[0] >= 0 else None


def look_of(snap, sid):
    for l in snap["looks"]:
        if l["sid"] == sid:
            return l
    return None


def check_of(snap, sid):
    for c in snap["checks"]:
        if c["sid"] == sid:
            return c
    return None


def is_chromatic(name) -> bool:
    n = str(name).lower()
    return not (n.startswith("white") or n.startswith("neutral") or n.startswith("black"))


def anchor_info(snap) -> dict:
    """R7: anchor sid(s) of a check frame and their rung-1 status."""
    if not snap["frames"]:
        return {"anchor_sids": [], "frame": None}
    f = snap["frames"][0]
    a = (f["aL"], f["aM"], f["aS"])
    props = {p["sid"]: p for p in snap["properties"]}
    anchors = []
    for c in snap["checks"]:
        if c["status"] == "minted":
            p = props.get(c["sid"])
            cat = (p["pL"], p["pM"], p["pS"]) if p else None
        else:
            cat = (c["cL"], c["cM"], c["cS"])
        if cat == a:
            anchors.append({"sid": c["sid"], "status": c["status"],
                            "pooled_status": c.get("pooled_status")})
    return {"anchor_sids": anchors, "frame": {"aL": a[0], "aM": a[1], "aS": a[2]}}


def adjacent_pairs(gt):
    n_el, n_az = len(gt), len(gt[0])
    for r in range(n_el):
        for c in range(n_az):
            for dr, dc in ((1, 0), (0, 1)):
                rr, cc = r + dr, c + dc
                if rr < n_el and cc < n_az and gt[r][c] != gt[rr][cc]:
                    yield r * n_az + c, rr * n_az + cc, int(gt[r][c]), int(gt[rr][cc])


# ------------------------------------------------------------------ arms
class Battery:
    def __init__(self, ss, sf, runner, smoke=False):
        self.ss, self.sf, self.R = ss, sf, runner
        self.smoke = smoke
        self.na, self.ne = ss.STANDARD_N_AZ, ss.STANDARD_N_EL
        self.layouts = (DEV,) if smoke else LAYOUTS
        self.tds = (1000.0,) if smoke else TDS

    def scene(self, k):
        return self.ss.standard_mondrian(seed=k)

    def gt(self, scene):
        return scene.label_map().tolist()

    # B1 ---------------------------------------------------------------
    def b1(self, layouts=None, method="cumulative", seeds=(None,)):
        recs = []
        for k in (layouts or self.layouts):
            sc = self.scene(k)
            g = self.gt(sc)
            for td in self.tds:
                for sd in seeds:
                    if method == "poisson":
                        ex = self.ss.illuminant_change(sc, list(B1_ILLS), td,
                                                       method="poisson", seed=sd)
                    else:
                        ex = [self.ss.render(sc, ill, td) for ill in B1_ILLS]
                    r = self.R.run(ex, [g] * 4, keep_Y=(method != "poisson"))
                    r.update({"layout": k, "td": td, "method": method, "poisson_seed": sd,
                              "reflectances": {str(p): str(sc.reflectance_of(p))
                                               for p in [0] + sc.patch_ids()}})
                    recs.append(r)
                    print(f"  B1[{method}] k={k} td={td:g} seed={sd} "
                          f"{sum(r['timings']):.1f}s", flush=True)
        return recs

    # B2 ---------------------------------------------------------------
    def b2(self):
        recs = []
        for k in self.layouts:
            sc = self.scene(k)
            g = self.gt(sc)
            field = self.ss.adapting_field(sc, B2_WL, B2_QUANTA)
            for td in self.tds:
                scene = self.ss.render(sc, "E", td)
                ex = [scene] + [scene + field] * B2_N_ADAPT + [scene]
                r = self.R.run(ex, [g] * len(ex))
                # keep only what B2 records in full; drop middle snapshots' bulky parts
                for s in r["snaps"][1:-1]:
                    s.pop("properties", None)
                r.update({"layout": k, "td": td})
                recs.append(r)
                print(f"  B2 k={k} td={td:g} {sum(r['timings']):.1f}s", flush=True)
        return recs

    # B3 ---------------------------------------------------------------
    def b3(self):
        recs = []
        tds = (1000.0,) if self.smoke else B3_TDS
        ills = ("E",) if self.smoke else B3_ILLS
        for td in tds:
            for ill in ills:
                ex = [self.ss.diffuse(self.na, self.ne, ill, td, filter="eyelid")]
                r = self.R.run(ex, [None])
                r.update({"illuminant": ill, "td": td})
                recs.append(r)
                print(f"  B3 {ill} td={td:g} {sum(r['timings']):.1f}s", flush=True)
        return recs

    # B4 ---------------------------------------------------------------
    def b4_pair(self, sc, td):
        rep = {row["patch_id"]: row for row in self.ss.patch_report(sc, "E", td)}
        cand = [p for p in sc.patch_ids() if is_chromatic(sc.reflectance_of(p))]
        best = None
        for i, a in enumerate(cand):
            for b in cand[i + 1:]:
                d = abs(rep[a]["lm"] - rep[b]["lm"])
                key = (-d, a, b)
                if best is None or key < best[0]:
                    best = (key, a, b, d)
        return best[1], best[2], best[3]

    def b4(self):
        recs = []
        for k in self.layouts:
            sc = self.scene(k)
            g = self.gt(sc)
            for td in self.tds:
                a, b, d = self.b4_pair(sc, td)
                sw = self.ss.swap_patches(sc, a, b)
                ex = [self.ss.render(sc, "E", td), self.ss.render(sw, "E", td)]
                r = self.R.run(ex, [g, self.gt(sw)], keep_Y=True)
                r.update({"layout": k, "td": td, "pair": [a, b], "lm_diff": d,
                          "pair_reflectances": [str(sc.reflectance_of(a)),
                                                str(sc.reflectance_of(b))]})
                recs.append(r)
                print(f"  B4 k={k} td={td:g} pair=({a},{b}) {sum(r['timings']):.1f}s",
                      flush=True)
        return recs

    # B5 ---------------------------------------------------------------
    def b5_patch(self, sc):
        offs, cum = [], 0
        for dc, _dr in B5_STEPS:
            cum += dc
            offs.append(cum)
        for pid in sorted(sc.patch_ids()):
            _p, _r, c0, r0, w, h = sc.rect(pid)
            ok = True
            for o in offs:
                nc0 = c0 + o
                if nc0 + w > sc.n_az:
                    ok = False
                    break
                for q in sc.patch_ids():
                    if q == pid:
                        continue
                    _q, _rq, qc, qr, qw, qh = sc.rect(q)
                    if nc0 < qc + qw and qc < nc0 + w and r0 < qr + qh and qr < r0 + h:
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return pid
        raise RuntimeError("no patch satisfies R13")

    def b5(self):
        recs = []
        for k in self.layouts:
            sc = self.scene(k)
            pid = self.b5_patch(sc)
            scenes, cur = [sc], sc
            for dc, dr in B5_STEPS:
                cur = self.ss.translate_patch(cur, pid, dc, dr)
                scenes.append(cur)
            for td in self.tds:
                ex = self.ss.motion(sc, pid, B5_STEPS, "E", td)
                r = self.R.run(ex, [self.gt(s) for s in scenes])
                r.update({"layout": k, "td": td, "moved_patch": pid,
                          "moved_reflectance": str(sc.reflectance_of(pid)),
                          "rects": [list(s.rect(pid)[2:]) for s in scenes]})
                recs.append(r)
                print(f"  B5 k={k} td={td:g} patch={pid} {sum(r['timings']):.1f}s",
                      flush=True)
        return recs

    # B6 ---------------------------------------------------------------
    def room_scene(self):
        names = self.sf.reflectance_names()
        rects = []
        for i, r in enumerate(self.ss.STANDARD_LAYOUT):
            rects.append((r[0], names[18 + (i % 6)]) + tuple(r[2:]))
        return self.ss.Mondrian(self.na, self.ne, tuple(rects), self.ss.DEFAULT_BACKGROUND)

    def b6(self):
        recs = []
        room = self.room_scene()
        g_room = self.gt(room)
        for k in self.layouts:
            rel = self.scene(k)
            g_rel = self.gt(rel)
            for td in self.tds:
                M = self.ss.render(room, "E", td)
                G = self.ss.diffuse(self.na, self.ne, "E", td, filter="eyelid")
                R = self.ss.render(rel, "E", td)
                order = ["M", "M", "G", "M", "M", "G", "M", "M", "R", "R", "R"]
                ex = [{"M": M, "G": G, "R": R}[o] for o in order]
                gts = [{"M": g_room, "G": None, "R": g_rel}[o] for o in order]
                r = self.R.run(ex, gts, types_at=(7, 10))
                r.update({"layout": k, "td": td, "order": order,
                          "room_reflectances": {str(p): str(room.reflectance_of(p))
                                                for p in [0] + room.patch_ids()},
                          "release_reflectances": {str(p): str(rel.reflectance_of(p))
                                                   for p in [0] + rel.patch_ids()}})
                recs.append(r)
                print(f"  B6 k={k} td={td:g} {sum(r['timings']):.1f}s", flush=True)
        return recs

    # B7 ---------------------------------------------------------------
    def b7(self):
        lay = (1,) if self.smoke else B7_LAYOUTS
        seeds = B7_SEEDS[:1] if self.smoke else B7_SEEDS
        return self.b1(layouts=lay, method="poisson", seeds=seeds)


# ------------------------------------------------------------------ analysis
def an_b1(recs):
    per = []
    for r in recs:
        S = r["snaps"]
        # exempt (R3): needs the stored Y grid (deterministic B1 only)
        exempt = set()
        per_seq = {"layout": r["layout"], "td": r["td"], "poisson_seed": r.get("poisson_seed")}
        if S[0]["Y_grid"] is not None:
            gt = r["_gt"]
            for snap in S:
                Y = snap["Y_grid"]
                for a, b, pa, pb in adjacent_pairs(gt):
                    ya, yb = Y[a], Y[b]
                    if ya is None or yb is None:
                        continue
                    if abs(ya - yb) <= math.sqrt(ya + yb):
                        exempt.add(pa)
                        exempt.add(pb)
        pids = sorted(int(p) for p in S[0]["patch_sids"])
        sids = {p: [snap["patch_sids"][str(p)] for snap in S] for p in pids}
        stable = {p: all(len(x) == 1 and x == sids[p][0] for x in sids[p]) for p in pids}
        comps = [composition(s) for s in S]
        rebinds, births = [], []
        for t in range(1, len(S)):
            for seg in S[t]["segments"]:
                if seg.get("decision") == "continue":
                    sid = seg.get("sid")
                    before, after = comps[t - 1].get(sid), comps[t].get(sid)
                    if before is not None and after is not None and before != after:
                        rebinds.append({"t": t, "sid": sid, "before": sorted(before),
                                        "after": sorted(after)})
                elif seg.get("decision") == "birth":
                    births.append({"t": t, "sid": seg.get("sid"),
                                   "birth_reason": seg.get("birth_reason"),
                                   "patches": sorted(comps[t].get(seg.get("sid"), []))})
        # checks per exposure
        checks = []
        for t in range(1, len(S)):
            anc = anchor_info(S[t])
            anc_sids = {a["sid"] for a in anc["anchor_sids"]}
            for c in S[t]["checks"]:
                checks.append({"t": t, "label": B1_LABELS[t], "sid": c["sid"],
                               "status": c["status"], "pooled_status": c.get("pooled_status"),
                               "is_anchor": c["sid"] in anc_sids,
                               "patches": sorted(comps[t].get(c["sid"], []))})
            per_seq.setdefault("anchors", []).append({"t": t, "label": B1_LABELS[t], **anc})
        # hue (R6)
        hue = []
        for t in range(1, len(S)):
            for p in pids:
                s0, st = single(S[0], p), single(S[t], p)
                if s0 is None or st is None:
                    continue
                if comps[0][s0] != {p} or comps[t][st] != {p}:
                    continue
                l0, lt = look_of(S[0], s0), look_of(S[t], st)
                if l0 is None or lt is None:
                    continue
                hue.append({"t": t, "label": B1_LABELS[t], "patch": p,
                            "hue0": hue_deg(l0), "huet": hue_deg(lt),
                            "dhue": dhue(hue_deg(l0), hue_deg(lt)),
                            "rg0": l0["rg"], "by0": l0["by"], "rgt": lt["rg"], "byt": lt["by"]})
        segcount = [len(s["segments"]) for s in S]
        nonneg = [sum(1 for v in s["sid_grid"] if v is not None and v >= 0) for s in S]
        cont = [sum(1 for a, b in zip(S[0]["sid_grid"], s["sid_grid"])
                    if a is not None and a >= 0 and a == b) / len(s["sid_grid"]) for s in S]
        per_seq.update({"exempt_patches": sorted(exempt), "patch_sids": {str(p): sids[p] for p in pids},
                        "stable": {str(p): stable[p] for p in pids},
                        "nonexempt_unstable": [p for p in pids if not stable[p] and p not in exempt],
                        "silent_rebinds": rebinds, "births": births, "checks": checks,
                        "hue": hue, "segment_count": segcount,
                        "cells_with_sid": nonneg, "cell_sid_continuity_vs_t0": cont})
        per.append(per_seq)
    return per


def pool(per, layouts):
    return [p for p in per if p["layout"] in layouts]


def summarise_b1(per, layouts):
    P = pool(per, layouts)
    out = {"n_sequences": len(P)}
    tds = sorted({p["td"] for p in P})
    rung = {}
    for td in tds:
        for lab in B1_LABELS[1:]:
            ch = [c for p in P if p["td"] == td for c in p["checks"]
                  if c["label"] == lab and c["status"] != "minted"]
            na = [c for c in ch if not c["is_anchor"]]
            key = f"td{td:g}_{lab}"
            rung[key] = {
                "rung1_all": frac(sum(c["status"] == "holds" for c in ch), len(ch)),
                "rung2_all": frac(sum(c["pooled_status"] == "holds_pooled" for c in ch), len(ch)),
                "rung1_nonanchor": frac(sum(c["status"] == "holds" for c in na), len(na)),
                "rung2_nonanchor": frac(sum(c["pooled_status"] == "holds_pooled" for c in na), len(na)),
                "minted_checks_excluded": sum(1 for p in P if p["td"] == td for c in p["checks"]
                                              if c["label"] == lab and c["status"] == "minted"),
                "per_layout": {str(p["layout"]): {
                    "rung1_holds": sum(c["status"] == "holds" for c in p["checks"]
                                       if c["label"] == lab and c["status"] != "minted"),
                    "rung2_holds": sum(c["pooled_status"] == "holds_pooled" for c in p["checks"]
                                       if c["label"] == lab and c["status"] != "minted"),
                    "rung1_nonanchor_holds": sum(c["status"] == "holds" for c in p["checks"]
                                                 if c["label"] == lab and c["status"] != "minted"
                                                 and not c["is_anchor"]),
                    "n_nonanchor": sum(1 for c in p["checks"] if c["label"] == lab
                                       and c["status"] != "minted" and not c["is_anchor"]),
                    "n": sum(1 for c in p["checks"] if c["label"] == lab and c["status"] != "minted")}
                    for p in P if p["td"] == td},
            }
        # D65 + A pooled non-anchor (R8)
        na2 = [c for p in P if p["td"] == td for c in p["checks"]
               if c["label"] in ("D65", "A") and c["status"] != "minted" and not c["is_anchor"]]
        rung[f"td{td:g}_D65+A"] = {"rung1_nonanchor": frac(sum(c["status"] == "holds" for c in na2), len(na2))}
    out["rung"] = rung
    # anchors
    anc = []
    for p in P:
        for a in p["anchors"]:
            ok = any(x["status"] == "holds" for x in a["anchor_sids"])
            anc.append({"layout": p["layout"], "td": p["td"], "label": a["label"],
                        "anchor_sids": a["anchor_sids"], "rung1_holds_on_anchor": ok})
    out["anchor_frames"] = anc
    out["anchor_holds"] = frac(sum(a["rung1_holds_on_anchor"] for a in anc), len(anc))
    # identity
    out["nonexempt_unstable"] = [{"layout": p["layout"], "td": p["td"], "patches": p["nonexempt_unstable"]}
                                 for p in P if p["nonexempt_unstable"]]
    out["silent_rebinds"] = [{"layout": p["layout"], "td": p["td"], **e}
                             for p in P for e in p["silent_rebinds"]]
    out["births"] = [{"layout": p["layout"], "td": p["td"], **e} for p in P for e in p["births"]]
    out["exempt"] = {f"{p['layout']}|{p['td']:g}": p["exempt_patches"] for p in P}
    n_patch = sum(len(p["stable"]) for p in P)
    out["patches_stable"] = frac(sum(v for p in P for v in p["stable"].values()), n_patch)
    ne = [(p, q) for p in P for q, v in p["stable"].items() if int(q) not in p["exempt_patches"]]
    out["nonexempt_patches_stable"] = frac(sum(p["stable"][q] for p, q in ne), len(ne))
    # hue
    hue = {}
    for td in tds + ["all"]:
        for lab in B1_LABELS[1:]:
            xs = [h["dhue"] for p in P if td == "all" or p["td"] == td for h in p["hue"]
                  if h["label"] == lab]
            hue[f"td{td if td == 'all' else format(td, 'g')}_{lab}"] = {
                "n": len(xs), "median": median(xs),
                "min": min(xs) if xs else None, "max": max(xs) if xs else None}
    out["hue_change"] = hue
    # condition-level rung2 >= rung1
    cond = []
    for p in P:
        for lab in B1_LABELS[1:]:
            ch = [c for c in p["checks"] if c["label"] == lab and c["status"] != "minted"]
            r1 = sum(c["status"] == "holds" for c in ch)
            r2 = sum(c["pooled_status"] == "holds_pooled" for c in ch)
            cond.append({"layout": p["layout"], "td": p["td"], "label": lab,
                         "rung1": r1, "rung2": r2, "n": len(ch), "ok": r2 >= r1})
    out["rung2_ge_rung1_conditions"] = cond
    out["segment_count"] = {f"{p['layout']}|{p['td']:g}": p["segment_count"] for p in P}
    return out


def an_b2(recs):
    per = []
    for r in recs:
        S = r["snaps"]
        first, last = S[0], S[-1]
        rows = []
        for pid, role in ((0, "neutral"), (1, "white")):
            s1, s22 = single(first, pid), single(last, pid)
            l1 = look_of(first, s1) if s1 is not None else None
            l22 = look_of(last, s22) if s22 is not None else None
            c22 = check_of(last, s22) if s22 is not None else None
            rows.append({"patch": pid, "role": role, "sid1": s1, "sid22": s22,
                         "rg1": l1["rg"] if l1 else None, "by1": l1["by"] if l1 else None,
                         "rg22": l22["rg"] if l22 else None, "by22": l22["by"] if l22 else None,
                         "status22": c22["status"] if c22 else None,
                         "pooled_status22": c22.get("pooled_status") if c22 else None,
                         "resid_max22": c22.get("resid_max") if c22 else None,
                         "link22": l22.get("link") if l22 else None})
        during = Counter(c["status"] for s in S[1:-1] for c in s["checks"])
        per.append({"layout": r["layout"], "td": r["td"], "rows": rows,
                    "during_status": dict(during),
                    "sid_grid_same_1_22": first["sid_grid"] == last["sid_grid"]})
    return per


def an_b3(recs):
    out = []
    for r in recs:
        s = r["snaps"][0]
        c = s["counts"]
        out.append({"illuminant": r["illuminant"], "td": r["td"],
                    "LookingEpisode": c["LookingEpisode"], "FieldLook": c["FieldLook"],
                    "SurfaceLook": c["SurfaceLook"], "ColourProperty": c["ColourProperty"],
                    "PropertyCheck": c["PropertyCheck"], "FrameStats": c["FrameStats"],
                    "presents_property": c["presents_property"],
                    "presents_unrecognised": c["presents_unrecognised"],
                    "field_look": s["field_looks"][0] if s["field_looks"] else None})
    return out


def an_b4(recs):
    per = []
    for r in recs:
        b, a = r["snaps"]
        pids = sorted(int(p) for p in b["patch_sids"])
        follows = {p: a["patch_sids"][str(p)] == b["patch_sids"][str(p)] for p in pids}
        sw = sorted({s for p in r["pair"] for s in b["patch_sids"][str(p)]},
                    key=lambda x: (x is None, x))
        st = {c["sid"]: c for c in a["checks"]}
        swapped = [{"sid": s, "status": st[s]["status"] if s in st else None,
                    "pooled_status": st[s].get("pooled_status") if s in st else None,
                    "resid_max": st[s].get("resid_max") if s in st else None} for s in sw]
        others = [{"sid": s, "status": c["status"], "pooled_status": c.get("pooled_status")}
                  for s, c in sorted(st.items()) if s not in sw]
        per.append({"layout": r["layout"], "td": r["td"], "pair": r["pair"],
                    "pair_reflectances": r["pair_reflectances"], "lm_diff": r["lm_diff"],
                    "sids_follow_position": {str(p): v for p, v in follows.items()},
                    "all_follow": all(follows.values()),
                    "swapped": swapped, "others": others,
                    "others_holds": sum(o["status"] == "holds" for o in others),
                    "others_n": len(others)})
    return per


def an_b5(recs):
    per = []
    for r in recs:
        S = r["snaps"]
        pid = r["moved_patch"]
        sids = [S[t]["patch_sids"].get(str(pid)) for t in range(len(S))]
        s0 = single(S[0], pid)
        steps_ok = [single(S[t], pid) == s0 and s0 is not None for t in range(1, 5)]
        sj = single(S[5], pid)
        seen = set()
        for t in range(5):
            seen.update(x for x in S[t]["sid_grid"] if x is not None)
        surf = {p["sid"]: p for p in S[5]["surfaces"]}
        prev = single(S[4], pid)
        born_ok = (sj is not None and sj not in seen and sj in surf
                   and surf[sj]["born_epoch"] == S[5]["epoch"])
        coast_ok = (prev is not None and prev in surf and surf[prev]["status"] == "coasting"
                    and surf[prev]["coast"] >= 1)
        others = {}
        for q in sorted(int(p) for p in S[0]["patch_sids"]):
            if q == pid:
                continue
            others[str(q)] = all(S[t]["patch_sids"].get(str(q)) == S[0]["patch_sids"][str(q)]
                                 for t in range(len(S)))
        per.append({"layout": r["layout"], "td": r["td"], "moved_patch": pid,
                    "moved_reflectance": r["moved_reflectance"], "moved_sids": sids,
                    "steps_keep_sid": steps_ok, "jump_new_sid": sj, "jump_born_ok": born_ok,
                    "prev_sid": prev,
                    "prev_status_at_jump": surf.get(prev, {}).get("status") if prev is not None else None,
                    "prev_coast_at_jump": surf.get(prev, {}).get("coast") if prev is not None else None,
                    "jump_coast_ok": coast_ok,
                    "ok": all(steps_ok) and born_ok and coast_ok,
                    "others_constant": others,
                    "jump_segment": [s for s in S[5]["segments"] if s.get("sid") == sj]})
    return per


def an_b6(recs):
    per = []
    for r in recs:
        S = r["snaps"]
        room, rel = S[7]["graph_types"], S[10]["graph_types"]
        rn = {t for t, n in room["nodes"].items() if n > 0}
        re_ = {t for t, n in rel["nodes"].items() if n > 0}
        reE = {t for t, n in room["edges"].items() if n > 0}
        relE = {t for t, n in rel["edges"].items() if n > 0}
        new_nodes, new_edges = sorted(re_ - rn), sorted(relE - reE)
        rel_epochs = {S[t]["epoch"] for t in (8, 9, 10)}
        props = {p["sid"]: p for p in S[10]["properties"]}
        chrom = []
        for p, name in r["release_reflectances"].items():
            if int(p) == 0 or not is_chromatic(name):
                continue
            s = single(S[8], int(p))
            ok = s is not None and s in props and props[s]["minted_epoch"] in rel_epochs
            chrom.append({"patch": int(p), "reflectance": name, "sid": s,
                          "property_minted_epoch": props[s]["minted_epoch"] if s in props else None,
                          "new_property_in_release": ok})
        cr, cl = S[7]["counts"], S[10]["counts"]
        delta = {k: cl[k] - cr[k] for k in cr}
        new_props = [p for p in S[10]["properties"] if p["minted_epoch"] in rel_epochs]
        per.append({"layout": r["layout"], "td": r["td"],
                    "room_counts": cr, "release_counts": cl, "delta_counts": delta,
                    "room_types": room, "release_types": rel,
                    "room_node_types": sorted(rn), "release_node_types": sorted(re_),
                    "room_edge_types": sorted(reE), "release_edge_types": sorted(relE),
                    "new_node_types": new_nodes, "new_edge_types": new_edges,
                    "types_subset": not new_nodes and not new_edges,
                    "chromatic_patches": chrom,
                    "new_properties_in_release": len(new_props),
                    "new_properties_sids": [p["sid"] for p in new_props],
                    "release_checks": [{"t": t, "status": dict(Counter(c["status"] for c in S[t]["checks"]))}
                                       for t in (8, 9, 10)],
                    "adds_looks_and_presents": delta["SurfaceLook"] > 0 and delta["presents_property"] > 0})
    return per


# ------------------------------------------------------------------ verdicts
def verdicts(A, layouts=HELD_OUT, tds=(100.0, 1000.0), b1_key="heldout"):
    V = {}
    b1 = A["B1"][b1_key]
    # ---- P1
    c_b1 = ("supported" if not b1["nonexempt_unstable"] and not b1["silent_rebinds"]
            else "not supported")
    b4 = [p for p in A["B4"]["per_sequence"] if p["layout"] in layouts]
    c_b4 = universal(p["all_follow"] for p in b4)
    b5 = [p for p in A["B5"]["per_sequence"] if p["layout"] in layouts]
    c_b5 = universal(p["ok"] for p in b5)
    V["P1"] = {"verdict": combine([c_b1, c_b4, c_b5]),
               "clauses": {
                   "B1": {"verdict": c_b1,
                          "nonexempt_patches_stable": b1["nonexempt_patches_stable"],
                          "nonexempt_unstable": b1["nonexempt_unstable"],
                          "silent_rebinds": len(b1["silent_rebinds"]),
                          "all_patches_stable": b1["patches_stable"],
                          "births": Counter(b["birth_reason"] for b in b1["births"])},
                   "B4": {"verdict": c_b4, "sequences_all_follow": sum(p["all_follow"] for p in b4),
                          "n": len(b4)},
                   "B5": {"verdict": c_b5, "sequences_ok": sum(p["ok"] for p in b5), "n": len(b5),
                          "steps_ok": sum(all(p["steps_keep_sid"]) for p in b5),
                          "jump_born_ok": sum(p["jump_born_ok"] for p in b5),
                          "jump_coast_ok": sum(p["jump_coast_ok"] for p in b5)}}}
    # ---- P2
    hue_ok = []
    hue_nums = {}
    for td in tds:
        mA = b1["hue_change"][f"td{td:g}_A"]["median"]
        mD = b1["hue_change"][f"td{td:g}_D65"]["median"]
        ok = mA is not None and mD is not None and mA > mD > 0
        hue_ok.append(ok)
        hue_nums[f"td{td:g}"] = {"median_E_to_A": mA, "median_E_to_D65": mD, "ok": ok,
                                 "n_A": b1["hue_change"][f"td{td:g}_A"]["n"],
                                 "n_D65": b1["hue_change"][f"td{td:g}_D65"]["n"]}
    c_hue = universal(hue_ok)
    b2 = [p for p in A["B2"]["per_sequence"] if p["layout"] in layouts]
    rows = [r for p in b2 for r in p["rows"]]
    rg_ok = [r["rg1"] is not None and r["rg22"] is not None and r["rg22"] < r["rg1"] for r in rows]
    c_rg = universal(rg_ok)
    V["P2"] = {"verdict": combine([c_hue, c_rg]),
               "clauses": {"B1_hue": {"verdict": c_hue, **hue_nums},
                           "B2_rg_drop": {"verdict": c_rg, "k": sum(rg_ok), "n": len(rg_ok)}}}
    # ---- P3
    c_anchor = universal(a["rung1_holds_on_anchor"] for a in b1["anchor_frames"])
    f100 = b1["rung"][f"td{min(tds):g}_D65+A"]["rung1_nonanchor"]   # 100 td
    f1000 = b1["rung"][f"td{max(tds):g}_D65+A"]["rung1_nonanchor"]  # 1000 td
    cmp_td = f100["value"] is not None and f1000["value"] is not None and f100["value"] >= f1000["value"]
    cmp_ill = []
    ill_nums = {}
    for td in tds:
        fA = b1["rung"][f"td{td:g}_A"]["rung1_nonanchor"]
        fD = b1["rung"][f"td{td:g}_D65"]["rung1_nonanchor"]
        ok = fA["value"] is not None and fD["value"] is not None and fA["value"] <= fD["value"]
        cmp_ill.append(ok)
        ill_nums[f"td{td:g}"] = {"A": fA, "D65": fD, "ok": ok}
    c_nonanchor = universal([cmp_td] + cmp_ill)
    c_r2 = universal(c["ok"] for c in b1["rung2_ge_rung1_conditions"])
    b2_ok = [r["status22"] == "holds" and r["rg1"] is not None and r["rg22"] is not None
             and r["rg22"] < r["rg1"] for r in rows]
    c_b2 = universal(b2_ok)
    sw = [s for p in b4 for s in p["swapped"]]
    c_b4r = universal(s["status"] == "refused" for s in sw)
    V["P3"] = {"verdict": combine([c_anchor, c_nonanchor, c_r2, c_b2, c_b4r]),
               "clauses": {
                   "anchor_every_frame": {"verdict": c_anchor, **b1["anchor_holds"]},
                   "nonanchor_fractions": {"verdict": c_nonanchor,
                                           "td100_D65+A": f100, "td1000_D65+A": f1000,
                                           "td_ok": cmp_td, "A_vs_D65": ill_nums},
                   "rung2_ge_rung1_every_condition": {
                       "verdict": c_r2,
                       "k": sum(c["ok"] for c in b1["rung2_ge_rung1_conditions"]),
                       "n": len(b1["rung2_ge_rung1_conditions"]),
                       "failures": [c for c in b1["rung2_ge_rung1_conditions"] if not c["ok"]]},
                   "B2_hold_at_22_while_shifted": {
                       "verdict": c_b2, "k": sum(b2_ok), "n": len(b2_ok),
                       "status22": dict(Counter(r["status22"] for r in rows))},
                   "B4_swapped_refused": {"verdict": c_b4r,
                                          "k": sum(s["status"] == "refused" for s in sw),
                                          "n": len(sw),
                                          "statuses": dict(Counter(str(s["status"]) for s in sw))}}}
    # ---- P4
    b3 = A["B3"]["per_condition"]
    ok4 = [x["LookingEpisode"] == 1 and x["FieldLook"] == 1 and x["SurfaceLook"] == 0
           and x["ColourProperty"] == 0 and x["PropertyCheck"] == 0
           and x["presents_property"] == 0 and x["presents_unrecognised"] == 0 for x in b3]
    V["P4"] = {"verdict": universal(ok4), "k": sum(ok4), "n": len(ok4)}
    # ---- P5
    b6 = [p for p in A["B6"]["per_sequence"] if p["layout"] in layouts]
    ca = universal(p["types_subset"] for p in b6)
    chrom = [c for p in b6 for c in p["chromatic_patches"]]
    cb = universal(c["new_property_in_release"] for c in chrom)
    cc = universal(p["adds_looks_and_presents"] for p in b6)
    V["P5"] = {"verdict": combine([ca, cb, cc]),
               "clauses": {
                   "no_new_types": {"verdict": ca, "k": sum(p["types_subset"] for p in b6),
                                    "n": len(b6),
                                    "new_types": sorted({t for p in b6 for t in
                                                         p["new_node_types"] + p["new_edge_types"]})},
                   "new_ColourProperty_for_chromatic_surfaces": {
                       "verdict": cb, "k": sum(c["new_property_in_release"] for c in chrom),
                       "n": len(chrom)},
                   "new_SurfaceLook_and_presents_property": {
                       "verdict": cc, "k": sum(p["adds_looks_and_presents"] for p in b6),
                       "n": len(b6)}}}
    # ---- P6
    b7 = A["B7"]
    c1 = universal(c["ok"] for c in b7["segment_cells"])
    c2v = [b7["refusal"][f"td{td:g}"]["ok"] for td in tds]
    c2 = universal(c2v)
    V["P6"] = {"verdict": combine([c1, c2]),
               "clauses": {"median_segments_exceed_det": {
                               "verdict": c1, "k": sum(c["ok"] for c in b7["segment_cells"]),
                               "n": len(b7["segment_cells"])},
                           "rung1_refusal_ge_det": {"verdict": c2, **b7["refusal"]}}}
    return V


def an_b7(per7, per1):
    det = {(p["layout"], p["td"]): p for p in per1 if p["layout"] in B7_LAYOUTS}
    cells = []
    for (k, td), d in sorted(det.items()):
        for t in range(4):
            xs = [p["segment_count"][t] for p in per7 if p["layout"] == k and p["td"] == td]
            m = median(xs)
            cells.append({"layout": k, "td": td, "label": B1_LABELS[t], "poisson": xs,
                          "median": m, "deterministic": d["segment_count"][t],
                          "ok": m is not None and m > d["segment_count"][t]})
    ref = {}
    for td in sorted({p["td"] for p in per7}):
        pc = [c for p in per7 if p["td"] == td for c in p["checks"] if c["status"] != "minted"]
        dc = [c for (k, t2), p in det.items() if t2 == td for c in p["checks"]
              if c["status"] != "minted"]
        fp = frac(sum(c["status"] == "refused" for c in pc), len(pc))
        fd = frac(sum(c["status"] == "refused" for c in dc), len(dc))
        r2p = frac(sum(c["pooled_status"] == "refused_pooled" for c in pc), len(pc))
        r2d = frac(sum(c["pooled_status"] == "refused_pooled" for c in dc), len(dc))
        ref[f"td{td:g}"] = {"poisson_rung1_refused": fp, "det_rung1_refused": fd,
                            "poisson_rung2_refused": r2p, "det_rung2_refused": r2d,
                            "poisson_minted_checks_excluded": sum(
                                1 for p in per7 if p["td"] == td for c in p["checks"]
                                if c["status"] == "minted"),
                            "ok": fp["value"] is not None and fd["value"] is not None
                            and fp["value"] >= fd["value"]}
    cont = [{"layout": p["layout"], "td": p["td"], "seed": p["poisson_seed"],
             "segment_count": p["segment_count"],
             "cell_sid_continuity_vs_t0": p["cell_sid_continuity_vs_t0"],
             "rung1": dict(Counter(f"{c['label']}:{c['status']}" for c in p["checks"])),
             "rung2": dict(Counter(f"{c['label']}:{c['pooled_status']}" for c in p["checks"]))}
            for p in per7]
    return {"segment_cells": cells, "refusal": ref, "per_sequence": cont}


# ------------------------------------------------------------------ main
def strip_timings(obj):
    if isinstance(obj, dict):
        return {k: strip_timings(v) for k, v in obj.items()
                if k not in ("timings", "service_wall_micros", "wall_micros", "_gt")}
    if isinstance(obj, list):
        return [strip_timings(v) for v in obj]
    return obj


def payload_hash(obj) -> str:
    return hashlib.sha256(json.dumps(strip_timings(obj), sort_keys=True,
                                     default=repr).encode()).hexdigest()


def attach_gt(ss, recs):
    for r in recs:
        r["_gt"] = ss.standard_mondrian(seed=r["layout"]).label_map().tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--from-raw", default=None,
                    help="analysis-only re-entry from a raw checkpoint written by this script")
    args = ap.parse_args()
    t_start = time.time()

    print("RULES (fixed before any exposure):")
    for k, v in RULES.items():
        print(f"  {k}: {v}")
    gc = git_checks()
    print(f"git HEAD {gc['head']}; apparatus diff vs {PREREG_COMMIT}: clean "
          f"({len(APPARATUS)} paths)")

    sys.path.insert(0, ROOT)
    from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp
    engine_preamble()
    from domains import spectral_scene as ss          # noqa: E402
    from domains import spectral_forward as sf        # noqa: E402
    from domains.perceived_surface_world import PerceivedSurfaceWorld  # noqa: E402
    pl = provenance_line()
    print(pl)
    if EXPECTED_ENGINE not in pl:
        raise SystemExit(f"ABORT: engine is not {EXPECTED_ENGINE}")
    stamp = provenance_stamp()

    runner = Runner(PerceivedSurfaceWorld, ss.STANDARD_N_AZ, ss.STANDARD_N_EL)
    B = Battery(ss, sf, runner, smoke=args.smoke)
    # declared choices printed before running
    choices = {"B5_moved_patch": B.b5_patch(ss.standard_mondrian()),
               "B6_room_reflectances": {str(p): str(B.room_scene().reflectance_of(p))
                                        for p in [0] + B.room_scene().patch_ids()},
               "B6_order": ["M", "M", "G", "M", "M", "G", "M", "M", "R", "R", "R"],
               "B4_pairs": {f"{k}|{td:g}": list(B.b4_pair(ss.standard_mondrian(seed=k), td))
                            for k in B.layouts for td in B.tds}}
    print("DECLARED CHOICES (geometry / expected-catch only):", json.dumps(choices))
    n_exp = (len(B.layouts) * len(B.tds) * (4 + 22 + 2 + 6 + 11)
             + (1 if args.smoke else 6)
             + (1 if args.smoke else len(B7_LAYOUTS) * len(B7_SEEDS) * len(TDS)) * 4)
    n_rerun = len(B.layouts) * len(B.tds) * 4 + (1 if args.smoke else 6)
    print(f"ESTIMATE: {n_exp} exposures + {n_rerun} rerun exposures; at 0.9 s/exposure "
          f"~{(n_exp + n_rerun) * 0.9 / 60:.1f} min", flush=True)

    ckpt = ("/tmp/marys_room_stage4_smoke_raw.json" if args.smoke
            else "/tmp/marys_room_stage4_raw_checkpoint.json")
    if args.from_raw:
        # analysis-only re-entry (crash recovery): the SAME raw records, no new exposures
        with open(args.from_raw) as f:
            saved = json.load(f)
        raw, det, runner.build_s = saved["raw"], saved["determinism"], saved["build_s"]
        print(f"loaded raw checkpoint {args.from_raw} (sha {payload_hash(raw)})")
    else:
        raw = {}
        for arm, fn in (("B1", B.b1), ("B2", B.b2), ("B3", B.b3), ("B4", B.b4),
                        ("B5", B.b5), ("B6", B.b6), ("B7", B.b7)):
            print(f"[{arm}] running", flush=True)
            t0 = time.time()
            raw[arm] = fn()
            print(f"[{arm}] done {time.time() - t0:.1f}s", flush=True)

        # determinism
        print("[determinism] re-running B1 and B3", flush=True)
        h1 = {"B1": payload_hash(raw["B1"]), "B3": payload_hash(raw["B3"])}
        again = {"B1": B.b1(), "B3": B.b3()}
        h2 = {k: payload_hash(v) for k, v in again.items()}
        det = {"first": h1, "second": h2, "identical": h1 == h2}
        print("determinism:", det, flush=True)
        assert h1 == h2, "DETERMINISM FAILED"
        with open(ckpt, "w") as f:
            json.dump({"raw": raw, "determinism": det, "build_s": runner.build_s}, f,
                      default=repr)
        # analysis always runs on the JSON round-trip so a re-entry is identical
        with open(ckpt) as f:
            raw = json.load(f)["raw"]
        print(f"raw checkpoint {ckpt} (sha {payload_hash(raw)})", flush=True)

    # analysis
    attach_gt(ss, raw["B1"])
    for r in raw["B7"]:
        r["_gt"] = ss.standard_mondrian(seed=r["layout"]).label_map().tolist()
    per1 = an_b1(raw["B1"])
    per7 = an_b1(raw["B7"])
    A = {"B1": {"per_sequence": per1,
                "heldout": summarise_b1(per1, HELD_OUT),
                "development": summarise_b1(per1, (DEV,))},
         "B2": {"per_sequence": an_b2(raw["B2"])},
         "B3": {"per_condition": an_b3(raw["B3"])},
         "B4": {"per_sequence": an_b4(raw["B4"])},
         "B5": {"per_sequence": an_b5(raw["B5"])},
         "B6": {"per_sequence": an_b6(raw["B6"])},
         "B7": an_b7(per7, per1)}
    if args.smoke:
        # exercise the verdict code on development data only; result discarded, not printed
        verdicts(A, layouts=(DEV,), tds=B.tds, b1_key="development")
        V = None
    else:
        V = verdicts(A)

    runtime = time.time() - t_start
    all_t = [t for arm in raw.values() for r in arm for t in r["timings"]]
    perf = {"wall_s": runtime, "exposures": len(all_t),
            "exposure_s_mean": sum(all_t) / len(all_t), "exposure_s_max": max(all_t),
            "world_builds": len(runner.build_s),
            "world_build_s_mean": sum(runner.build_s) / len(runner.build_s)}
    for arm in raw.values():
        for r in arm:
            r.pop("_gt", None)
    payload = {"study": "marys-room-stage4-battery",
               "prereg": "docs/experiments/marys-room-stage4-prereg.md",
               "smoke": args.smoke, "git": gc, "engine_provenance": stamp,
               "provenance_line": pl, "rules": RULES, "declared_choices": choices,
               "determinism": det, "perf": perf,
               "raw_payload_sha256": payload_hash(raw),
               "analysis": A, "verdicts": V, "raw": raw}
    out_dir = "/tmp/marys_room_stage4_smoke" if args.smoke else os.path.join(ROOT, "results")
    os.makedirs(out_dir, exist_ok=True)
    jp = os.path.join(out_dir, "marys_room_stage4_battery.json")
    with open(jp, "w") as f:
        json.dump(payload, f, default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else repr(o))
    write_csv(os.path.join(out_dir, "marys_room_stage4_battery_summary.csv"), A, V)
    print(f"wrote {jp}; runtime {runtime / 60:.1f} min; {len(all_t)} exposures; "
          f"mean {perf['exposure_s_mean']:.3f} s/exposure")
    if args.smoke:
        print("SMOKE OK (verdicts not computed)")
        return
    print("\nVERDICTS")
    for p, v in V.items():
        print(f"  {p}: {v['verdict']}")
        print("     " + json.dumps({k: x for k, x in v.items() if k != "verdict"},
                                   default=lambda o: dict(o) if isinstance(o, Counter) else repr(o))[:2000])


def write_csv(path, A, V):
    rows = []

    def add(arm, quantity, scope, td, cond, f=None, value=None, extra=""):
        if f is not None:
            lo, hi = (f["wilson95"] or [None, None])
            rows.append([arm, quantity, scope, td, cond, f["k"], f["n"], f["value"], lo, hi, extra])
        else:
            rows.append([arm, quantity, scope, td, cond, "", "", value, "", "", extra])

    for scope in ("heldout", "development"):
        s = A["B1"][scope]
        for key, d in s["rung"].items():
            td, cond = key.split("_", 1)
            for q, f in d.items():
                if isinstance(f, dict) and "k" in f:
                    add("B1", q, scope, td[2:], cond, f)
        add("B1", "anchor_rung1_holds", scope, "all", "all_frames", s["anchor_holds"])
        add("B1", "patches_stable", scope, "all", "E,D65,A,E", s["patches_stable"])
        add("B1", "nonexempt_patches_stable", scope, "all", "E,D65,A,E", s["nonexempt_patches_stable"])
        add("B1", "silent_rebinds", scope, "all", "", value=len(s["silent_rebinds"]))
        for key, h in s["hue_change"].items():
            td, cond = key.split("_", 1)
            add("B1", "median_dhue_deg", scope, td[2:], cond, value=h["median"], extra=f"n={h['n']}")
    for p in A["B2"]["per_sequence"]:
        for r in p["rows"]:
            add("B2", f"{r['role']}_rg1->rg22", "heldout" if p["layout"] in HELD_OUT else "development",
                p["td"], f"layout={p['layout']}", value=f"{r['rg1']}->{r['rg22']}",
                extra=f"status22={r['status22']};pooled={r['pooled_status22']}")
    for x in A["B3"]["per_condition"]:
        add("B3", "counts", "n/a", x["td"], x["illuminant"],
            value=json.dumps({k: x[k] for k in ("LookingEpisode", "FieldLook", "SurfaceLook",
                                                "ColourProperty", "PropertyCheck",
                                                "presents_property", "presents_unrecognised")}))
    for p in A["B4"]["per_sequence"]:
        add("B4", "swap", "heldout" if p["layout"] in HELD_OUT else "development", p["td"],
            f"layout={p['layout']};pair={p['pair']}", value=p["all_follow"],
            extra=";".join(f"sid{s['sid']}={s['status']}" for s in p["swapped"])
            + f";others_holds={p['others_holds']}/{p['others_n']}")
    for p in A["B5"]["per_sequence"]:
        add("B5", "motion_ok", "heldout" if p["layout"] in HELD_OUT else "development", p["td"],
            f"layout={p['layout']};patch={p['moved_patch']}", value=p["ok"],
            extra=f"steps={p['steps_keep_sid']};born={p['jump_born_ok']};coast={p['jump_coast_ok']}")
    for p in A["B6"]["per_sequence"]:
        add("B6", "release", "heldout" if p["layout"] in HELD_OUT else "development", p["td"],
            f"layout={p['layout']}", value=p["types_subset"],
            extra=(f"new_props={p['new_properties_in_release']};"
                   f"chromatic_with_new_prop={sum(c['new_property_in_release'] for c in p['chromatic_patches'])}"
                   f"/{len(p['chromatic_patches'])};dSurfaceLook={p['delta_counts']['SurfaceLook']};"
                   f"dpresents_property={p['delta_counts']['presents_property']}"))
    for c in A["B7"]["segment_cells"]:
        add("B7", "segments_median_vs_det", "B7", c["td"], f"layout={c['layout']};{c['label']}",
            value=c["median"], extra=f"det={c['deterministic']};poisson={c['poisson']}")
    for td, d in A["B7"]["refusal"].items():
        for q in ("poisson_rung1_refused", "det_rung1_refused",
                  "poisson_rung2_refused", "det_rung2_refused"):
            add("B7", q, "B7", td[2:], "D65,A,E_return", d[q])
    if V:
        for p, v in V.items():
            add("verdict", p, "heldout", "", "", value=v["verdict"])
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arm", "quantity", "scope", "td", "condition", "k", "n", "value",
                    "wilson_lo", "wilson_hi", "extra"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
