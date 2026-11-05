"""Confirmatory test for docs/research/engine_substrate/SD_LOOP_REARM_AND_JSON_SIGNATURE_PREREG.md
(block 371000, start commit 1281a482).

Two defects in the sd loop, and their fix:

D1  A transformed observation that was re-armed by a codebook-epoch bump stayed `decoded`,
    because sd_recognize_transformed / sd_recognize_dim required "no has_transform edge yet".
    Fix: sd_rerecognize_transformed and sd_rerecognize_dim (seeds/shape_decode_loop.json v1.18.0).
D2  sd_recognize.covered_by and sd_mint_quantum.closest_held_shape scored JSON-string part
    signatures as one opaque value, so a JSON part could not be matched.
    Fix: the Rust Term ClosestShape, which reads a signature the way load_parts does.

One test per gate G-1..G-5 (prereg §3), plus a source check of the rule sites. The prog_construction
sites are not in this file (see the block 371000 report). Measurements go to
results/sd_rearm_closest_shape.json.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import time

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402
from tests import test_affect_frame_codebook as cb  # noqa: E402
from tests import test_affect_frame_v02 as v02  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "results", "sd_rearm_closest_shape.json")
SEED_PATH = os.path.join(ROOT, "seeds", "shape_decode_loop.json")
START_COMMIT = "1281a4829a042dc7eaedd1293f6648e10c33de0e"
NEW_RULES = ("sd_rerecognize_transformed", "sd_rerecognize_dim")

PART_A = [["probe_a", "X", 1], ["probe_b", "Y"]]
PART_B = [["probe_c", "Z", 2], ["probe_d", "W"]]
PARTIAL = [["probe_c", "Z", 2], ["zznew", "Q"]]

DIM_TYPES = ["pred", "coord:r", "coord:c", "val"]
TROMINO = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 1, 0, "red"]]
ROTATED_K1_TROMINO = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 1, 1, "red"]]


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


def _boot(skip_new_rules=False):
    """boot_core + the shape_decode_loop seed family, as test_dimension_inference_migrated does.

    With skip_new_rules, the shape_decode_loop manifest is loaded in memory with the two D1
    rules removed. That is the pre-fix rule set, used only for the record-only control."""
    from substrate.seed_loader import manifest_for
    s, ag = boot_core()
    native = rf._native_eval2(s)
    if not skip_new_rules:
        rf._ensure_shape_decode_loop(s, native, ag)
        return s, ag, native
    have = rf._installed_seed_ids(s)
    assert "shape_decode_loop" not in have, "boot_core already installed shape_decode_loop"
    for sid in rf._SHAPE_DECODE_LOOP_SEEDS:
        if sid in have:
            continue
        manifest = manifest_for(sid)
        if sid == "shape_decode_loop":
            manifest = copy.deepcopy(manifest)
            manifest["rules"] = [r for r in manifest["rules"] if r.get("name") not in NEW_RULES]
        native.load_seed_manifest(manifest, ag)
        s.add_node("Seed", {"id": sid, "version": "1.0.0"})
        have.add(sid)
    if s.node(ag)["attrs"].get("codebook_epoch") is None:
        s.set_attr(ag, "codebook_epoch", 0.0)
    return s, ag, native


def _add_part(s, name, signature, form, dim_types=None):
    """A codebook part. form 'json' stores the signature as a JSON string, as json.dumps would."""
    sig = json.dumps(signature) if form == "json" else signature
    attrs = {"name": name, "signature": sig, "kind": "faculty", "faculty": name}
    if dim_types is not None:
        attrs["dim_types"] = list(dim_types)
    return s.add_node("ShapeSignature", attrs)


def _observe_decoded(s, ag, *, signature, key, residual, decoded_epoch, dim_types=None):
    attrs = {"signature": signature, "key": [key], "status": "decoded", "residual": residual,
             "decoded_epoch": decoded_epoch}
    if dim_types is not None:
        attrs["dim_types"] = list(dim_types)
    obs = s.add_node("Observation", attrs)
    s.add_edge(ag, "observed", obs)
    return obs


def _epoch(s, ag):
    return s.node(ag)["attrs"].get("codebook_epoch") or 0.0


def _attrs(s, nid):
    return dict(s.node(nid)["attrs"])


# ---------------------------------------------------------------------------------------------
# G-1 / G-2: JSON-string parts through the two rule sites
# ---------------------------------------------------------------------------------------------

def _g1_covered_by(form):
    s, ag, native = _boot()
    _add_part(s, "zz_part_A", PART_A, form)
    _add_part(s, "zz_part_B", PART_B, form)
    obs = _observe_decoded(s, ag, signature=PART_B, key=["probe_g1"], residual=[],
                           decoded_epoch=_epoch(s, ag))
    native.run_rules()
    at = _attrs(s, obs)
    return {"covered_by": at.get("covered_by"), "status": at.get("status")}


def test_G1_covered_by_json_and_native():
    res = {"json": _g1_covered_by("json"), "native": _g1_covered_by("native")}
    _record("G-1", res)
    assert res["native"]["covered_by"] == "zz_part_B", res
    assert res["json"]["covered_by"] == "zz_part_B", res
    assert res["json"]["status"] == "recognized", res


def _g2_axis(form):
    s, ag, native = _boot()
    _add_part(s, "zz_part_A", PART_A, form)
    _add_part(s, "zz_part_B", PART_B, form)
    before = {n["id"] if isinstance(n, dict) else n for n in s.nodes("CapabilityAxis")}
    obs = _observe_decoded(s, ag, signature=PARTIAL, key=["probe_g2"],
                           residual=[["zznew", "Q"]], decoded_epoch=_epoch(s, ag))
    native.run_rules()
    new_axes = []
    for n in s.nodes("CapabilityAxis"):
        nid = n["id"] if isinstance(n, dict) else n
        if nid not in before:
            new_axes.append(_attrs(s, nid))
    return {"obs_status": _attrs(s, obs).get("status"), "n_new_axes": len(new_axes),
            "closest_held_shape": [a.get("closest_held_shape") for a in new_axes],
            "capability_keys": [a.get("capability_keys") for a in new_axes]}


def test_G2_closest_held_shape_json_and_native():
    res = {"json": _g2_axis("json"), "native": _g2_axis("native")}
    _record("G-2", res)
    for form in ("json", "native"):
        r = res[form]
        assert r["n_new_axes"] == 1, res
        assert r["closest_held_shape"] == ["zz_part_B"], res


# ---------------------------------------------------------------------------------------------
# G-3: block 369000's affect codebook with every signature stored as a JSON string
# ---------------------------------------------------------------------------------------------

def _affect_run(json_codebook):
    from domains.reflective_faculty import _ensure_shape_decode_loop
    from substrate.seed_loader import manifest_for
    eye, inner = cb.M._eye()
    _ensure_shape_decode_loop(eye.substrate, inner, eye._agent)
    inner.load_seed_manifest(manifest_for(cb.SEED_ID), eye._agent)
    canon = manifest_for(cb.SEED_ID_CANON)
    if json_codebook:
        canon = copy.deepcopy(canon)
        for node in canon["nodes"]:
            sig = node["attrs"].get("signature")
            if isinstance(sig, list):
                node["attrs"]["signature"] = json.dumps(sig)
    inner.load_seed_manifest(canon, eye._agent)
    axes_before = len(eye.substrate.nodes("CapabilityAxis"))
    out = {}
    try:
        for ev in cb.ALL_EVENTS:
            hub = cb._new_hub(eye, inner)
            ap = cb.M._appraise(eye, inner, hub, **cb.inputs(*ev))
            inner.run_rules()
            out[cb._key(ev)] = {"read": cb._read(eye, ap), "frames": cb._frames(eye, inner, ap)}
        axes_after = len(eye.substrate.nodes("CapabilityAxis"))
    finally:
        eye.stop()
    return out, axes_after - axes_before


def _frame_summary(frames):
    return [{"tag": f["tag"], "status": f["status"], "covered_by": f["covered_by"],
             "transforms": f["transforms"]} for f in frames]


def test_G3_affect_codebook_json_strings_match_native():
    native, native_mints = _affect_run(json_codebook=False)
    as_json, json_mints = _affect_run(json_codebook=True)
    diffs = []
    n_frames = 0
    wrong_cover = []
    for key in native:
        nf = _frame_summary(native[key]["frames"])
        jf = _frame_summary(as_json[key]["frames"])
        n_frames += len(jf)
        if native[key]["read"] != as_json[key]["read"]:
            diffs.append({"event": key, "native_read": native[key]["read"],
                          "json_read": as_json[key]["read"]})
        if nf != jf:
            diffs.append({"event": key, "native": nf, "json": jf})
        for f in jf:
            if f["covered_by"] != "affect:" + f["tag"]:
                wrong_cover.append({"event": key, "tag": f["tag"], "covered_by": f["covered_by"]})
    _record("G-3", {"n_events": len(native), "n_frames_json": n_frames,
                    "native_mints": native_mints, "json_mints": json_mints,
                    "diffs": diffs, "wrong_covered_by": wrong_cover,
                    "json_covered_by": sorted({f["covered_by"] for k in as_json
                                               for f in _frame_summary(as_json[k]["frames"])})})
    assert len(native) == 22
    assert n_frames == 23
    assert json_mints == 0 and native_mints == 0, (native_mints, json_mints)
    assert not diffs, f"JSON-string codebook differs from native: {diffs[:3]}"
    assert not wrong_cover, f"covered_by is not affect:<own tag>: {wrong_cover[:5]}"


# ---------------------------------------------------------------------------------------------
# G-4: block 370000 growth arm, D1 transform path
# ---------------------------------------------------------------------------------------------

def _growth_arm():
    eye, inner = v02._boot([v02.SEED_FRAME])
    try:
        ax_before = len(eye.substrate.nodes("CapabilityAxis"))
        events = []
        for ev in v02.ALL_EVENTS:
            hub = v02._new_hub(eye, inner)
            ap = v02.M._appraise(eye, inner, hub, **v02.inputs(*ev))
            inner.run_rules()
            events.append((ev, list(inner.neighbours(ap, "has_affect_frame"))))
        ax_after = len(eye.substrate.nodes("CapabilityAxis"))
        n_transform = len(list(eye.substrate.nodes("Transform")))
        frames = []
        for ev, fids in events:
            for fid in fids:
                fr = v02._frame_read(eye, inner, fid)
                fr["event"] = ev
                frames.append(fr)
    finally:
        eye.stop()
    return {"frames": frames, "n_transform": n_transform, "ax_delta": ax_after - ax_before}


def test_G4_growth_transform_path():
    arm = _growth_arm()
    counts = {}
    bad = []
    n_rt = 0
    for fr in arm["frames"]:
        counts[fr["status"]] = counts.get(fr["status"], 0) + 1
        want = v02.STATUS.get((fr["event"], fr["tag"]))
        if fr["status"] != want:
            bad.append({"event": fr["event"], "tag": fr["tag"], "status": fr["status"],
                        "want": want})
        if fr["status"] == "recognized_transformed":
            n_rt += 1
            if len(fr["transforms"]) != 1 or fr["transform_explained"] != 1:
                bad.append({"event": fr["event"], "problem": "has_transform count or explained",
                            "n_transforms": len(fr["transforms"]),
                            "transform_explained": fr["transform_explained"]})
                continue
            want_base, want_deltas = v02.DELTAS[(fr["event"][0], fr["event"][1])]
            tr = fr["transforms"][0]
            if tr["base"] != "affect:" + want_base or tr["deltas"] != want_deltas:
                bad.append({"event": fr["event"], "tag": fr["tag"], "base": tr["base"],
                            "deltas": tr["deltas"], "want_deltas": want_deltas})
    _record("G-4", {"status_counts": counts, "n_transform_nodes": arm["n_transform"],
                    "capability_axes_delta": arm["ax_delta"], "mismatch": bad,
                    "n_mismatch": len(bad)})
    full = {k: counts.get(k, 0) for k in ("recognized", "recognized_transformed", "decoded")}
    assert full == {"recognized": 8, "recognized_transformed": 15, "decoded": 0}, counts
    assert n_rt == 15
    assert arm["n_transform"] == 15, arm["n_transform"]
    assert not bad, f"frame statuses or transforms differ: {bad[:5]}"


# ---------------------------------------------------------------------------------------------
# G-5: dimension path, unrelated codebook growth re-arms the observation
# ---------------------------------------------------------------------------------------------

def _dimension_rearm(skip_new_rules):
    s, ag, native = _boot(skip_new_rules=skip_new_rules)
    _add_part(s, "part_tromino", TROMINO, "json", dim_types=DIM_TYPES)
    obs = _observe_decoded(s, ag, signature=ROTATED_K1_TROMINO, key="probe_rotate",
                           residual=ROTATED_K1_TROMINO, decoded_epoch=_epoch(s, ag),
                           dim_types=DIM_TYPES)
    native.run_rules()
    first = _attrs(s, obs).get("status")
    s.add_node("ShapeSignature", {"name": "zz_unrelated", "signature": [["zz_q", 1]]})
    s.set_attr(ag, "codebook_epoch", _epoch(s, ag) + 1)
    native.run_rules()
    at = _attrs(s, obs)
    transforms = list(s.neighbours(obs, "has_transform"))
    latent = list(s.neighbours(obs, "has_latent_dimension"))
    t_at = _attrs(s, transforms[0]) if transforms else {}
    return {"status_first_pass": first, "status_after_growth": at.get("status"),
            "n_transform": len(transforms), "n_latent_dimension": len(latent),
            "base": t_at.get("base"), "generator": t_at.get("generator"), "k": t_at.get("k"),
            "transform_explained": at.get("transform_explained"),
            "dim_explained": at.get("dim_explained"), "covered_by": at.get("covered_by")}


def test_G5_dimension_path_rearm():
    fixed = _dimension_rearm(skip_new_rules=False)
    _record("G-5", {"fixed": fixed})
    assert fixed["status_first_pass"] == "recognized_transformed", fixed
    assert fixed["status_after_growth"] == "recognized_transformed", fixed
    assert fixed["base"] == "part_tromino", fixed
    assert fixed["generator"] == "rotation90", fixed
    assert fixed["k"] == 1, fixed
    assert fixed["n_transform"] == 1, fixed
    assert fixed["n_latent_dimension"] == 1, fixed


def test_G5_control_pre_fix_rules_record_only():
    """Record only: the same scenario with the two D1 rules removed in memory. Prereg §3 says the
    pre-fix status is `decoded`. This test writes what it observed and asserts nothing about it."""
    pre = _dimension_rearm(skip_new_rules=True)
    _record("G-5-control-prefix", {"prefix": pre})


# ---------------------------------------------------------------------------------------------
# source check: the rule sites and the new rules are in the seed
# ---------------------------------------------------------------------------------------------

def test_source_rule_sites_use_closest_shape():
    with open(SEED_PATH, encoding="utf-8") as fh:
        seed = json.load(fh)
    rules = {r["name"]: r for r in seed["rules"]}
    sites = {
        "sd_recognize": rules["sd_recognize"]["effects"][1][3]["__term__"]["node"],
        "sd_mint_quantum": rules["sd_mint_quantum"]["effects"][0][3]["closest_held_shape"]
        ["__term__"]["node"],
    }
    for name, node in sites.items():
        assert node["type"] == "ClosestShape", (name, node)
        assert node["goal"] == {"type": "Attr", "node": {"type": "Var", "name": "obs"},
                                "key": "signature"}, name
        assert "Argmax" not in json.dumps(node) and "AntiUnify" not in json.dumps(node), name
    for name in NEW_RULES:
        assert name in rules, name
        assert rules[name]["match"] == [["ag", "observed", "obs"], ["obs", "has_transform", "t"]]
    assert seed["version"] == "1.18.0", seed["version"]
    _record("source", {"sites": sorted(sites), "new_rules": list(NEW_RULES),
                       "version": seed["version"]})
