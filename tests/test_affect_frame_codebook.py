"""Confirmatory test for docs/research/psychology_affect/AFFECT_FRAME_CODEBOOK_PREREG.md
(block 369000, start commit 2e674bd9).

Does representing affect as integer log-level frames (seeds/affect_frame.json), decoded by the
unchanged shape_decode_loop against a held codebook, give emotion recognition, valence and
arousal direction, with the old contract unchanged?

Measurement only. Events are authored with the unchanged scripts/core_emotions_measure.py helpers;
the Rust engine computes every frame, decode and read-off. The direction comparisons are an
OFFLINE ideal observer over the published values. One test per gate (G-0..G-5), plus two
record-only exploratory tests (X-1, X-2). Measurements go to results/affect_frame_codebook.json.
"""
from __future__ import annotations

import importlib
import json
import math
import os
import subprocess
import time

import pytest

pytest.importorskip("substrate_rs")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "results", "affect_frame_codebook.json")
SEED_PATH = os.path.join(ROOT, "seeds", "affect_frame_canonical.json")
START_COMMIT = "2e674bd99454403d4a01d90e195ba328e1345723"
# VISION_PROTOCOL §12.3: G-0's no-change claim is about THIS RUNG's own commits, so it is
# pinned to the rung's range (prereg commit .. result commit), never to the mutable tree. The
# live-tree form failed the day it landed, when an unrelated merge brought engine changes.
RESULT_COMMIT = "ddea502fb3b394ecb41314a934ea1bf49feb2553"
SEED_ID = "affect_frame"
SEED_ID_CANON = "affect_frame_canonical"
LOW, T_PRESENT = 50, 256
SURPRISE_R = [150, 200, 400, 800, 1600]

M = importlib.import_module("scripts.core_emotions_measure")

_cache = {}


def sgn(x):
    return (x > 0) - (x < 0)


# ---------------------------------------------------------------------------------------------
# §3 event families (world data), copied from tests/test_affect_direction_judgement.py (368000)
# ---------------------------------------------------------------------------------------------

def inputs(kind, k):
    if kind == "gain":
        return dict(appraised=1, valued_goal=1, goal_blocked=0, step_prev=k, step=k + 1)
    if kind == "loss":
        return dict(appraised=1, attachment=1, regroundable=0, attach_k_prev=k, attach_k_now=k + 1)
    if kind == "neutral":
        return dict(appraised=1)
    if kind == "threat":
        return dict(appraised=1, threat=1, threat_half_life=1, threat_last_refresh=0,
                    threat_now_epoch=k)
    if kind == "surprise":
        return dict(appraised=0, residual=k)
    if kind == "mixed":
        return dict(appraised=1, valued_goal=1, goal_blocked=0, step_prev=1, step=4,
                    threat=1, threat_half_life=1, threat_last_refresh=0, threat_now_epoch=3)
    raise ValueError(kind)


def oracle(kind, k):
    """Block 368000 oracle: predicted (valence, arousal, emotion, n_fired). Unchanged contract."""
    if kind == "gain":
        return (1, (1024 >> k) - (1024 >> (k + 1)), 7, 1)
    if kind == "loss":
        return (-1, LOW, 8, 1)
    if kind == "neutral":
        return (0, LOW, 0, 0)
    if kind == "threat":
        p = 1024 >> k
        return (-1, p, 3 if p >= T_PRESENT else 2, 1)
    if kind == "surprise":
        return (0, k, 1, 1)
    if kind == "mixed":
        return (1, 128, 2, 2)
    raise ValueError(kind)


def truth_value(kind, k):
    if kind == "gain":
        return (1024 >> k) - (1024 >> (k + 1))
    if kind == "loss":
        return (1024 >> (k + 1)) - (1024 >> k)
    return 0


def intensity(kind, k):
    if kind == "threat":
        return 1024 >> k
    if kind == "surprise":
        return k
    return abs(truth_value(kind, k))


V_LEVELS = [("loss", k) for k in range(5)] + [("neutral", 0)] + [("gain", k) for k in range(5)]
A_FAMILIES = {"threat": list(range(5)), "surprise": SURPRISE_R,
              "gain": list(range(5)), "loss": list(range(5))}
ALL_EVENTS = (V_LEVELS + [("threat", k) for k in range(5)]
              + [("surprise", r) for r in SURPRISE_R] + [("mixed", 0)])


# ---------------------------------------------------------------------------------------------
# §4 analytic oracle (prereg Appendix A, transcribed; pure arithmetic)
# ---------------------------------------------------------------------------------------------

def lq(x):  # LogQuantum base 2, delta 1, raw: round(log2 x); x <= 0 -> round(log2 1e-9)
    return math.floor((math.log(x) if x > 0 else math.log(1e-9)) / math.log(2) + 0.5)


def frame_app(t, vp=0, lp=0, wc=0, tp=0, r=0):
    """(tag, val_sign, val_level or None, ar_level)."""
    return {"joy": (t, 1, lq(vp), lq(vp)), "sadness": (t, -1, lq(abs(vp)), lq(LOW)),
            "curiosity": (t, 1, lq(lp), lq(lp)), "fulfilment": (t, 1, lq(abs(wc)), lq(abs(wc))),
            "fear": (t, -1, None, lq(tp)), "anxiety": (t, -1, None, lq(tp)),
            "surprise": (t, 0, None, lq(r)), "anger": (t, -1, None, lq(800)),
            "frustration": (t, -1, None, lq(800)), "disgust": (t, -1, None, lq(400)),
            "boredom": (t, -1, None, lq(LOW)), "none": (t, 0, None, lq(LOW))}[t]


CB_APP = {t: frame_app(t, **kw) for t, kw in {
    "surprise": dict(r=500), "fear": dict(tp=1024 >> 3), "anxiety": dict(tp=1024),
    "anger": {}, "frustration": {}, "disgust": {}, "joy": dict(vp=512 - 64),
    "sadness": dict(vp=64 - 512), "curiosity": dict(lp=180), "boredom": {},
    "fulfilment": dict(wc=(1024 * 300) >> 10), "none": {}}.items()}


def ev_frames_app(kind, k):
    if kind == "gain":
        return [frame_app("joy", vp=(1024 >> k) - (1024 >> (k + 1)))]
    if kind == "loss":
        return [frame_app("sadness", vp=(1024 >> (k + 1)) - (1024 >> k))]
    if kind == "neutral":
        return [frame_app("none")]
    if kind == "threat":
        p = 1024 >> k
        return [frame_app("anxiety" if p >= 256 else "fear", tp=p)]
    if kind == "surprise":
        return [frame_app("surprise", r=k)]
    return [frame_app("joy", vp=448), frame_app("fear", tp=128)]           # mixed


def decode_app(frame):
    """(status, base, {predicate suffix: observed - held})."""
    t, s, lvl, alvl = frame
    held = CB_APP[t]
    d = {}
    if lvl is not None and lvl != held[2]:
        d["val_level"] = lvl - held[2]
    if alvl != held[3]:
        d["ar_level"] = alvl - held[3]
    return ("recognized" if not d else "recognized_transformed", "affect:" + t, d)


# ---------------------------------------------------------------------------------------------
# harness: the unchanged core_emotions_measure helpers, plus the affect_frame seed
# ---------------------------------------------------------------------------------------------

def _boot():
    from domains.reflective_faculty import _ensure_shape_decode_loop
    from substrate.seed_loader import manifest_for
    eye, inner = M._eye()
    _ensure_shape_decode_loop(eye.substrate, inner, eye._agent)
    inner.load_seed_manifest(manifest_for(SEED_ID), eye._agent)
    inner.load_seed_manifest(manifest_for(SEED_ID_CANON), eye._agent)
    return eye, inner


def _new_hub(eye, inner):
    hub, _ = M._hub(eye, inner)
    inner.add_edge_unchecked(eye._agent, "has_emotion_hub", hub)
    return hub


def _read(eye, ap):
    a = M._attrs(eye, ap)
    return (int(a["valence"]), int(a["arousal"]), int(a["emotion"]), int(a["n_fired"]))


def _dirs(eye, ap):
    a = M._attrs(eye, ap)
    vd, ad = a.get("val_direction"), a.get("ar_direction")
    return (None if vd is None else int(vd), None if ad is None else int(ad))


def _plain(x):
    if isinstance(x, (list, tuple)):
        return [_plain(i) for i in x]
    return x


def _frames(eye, inner, ap):
    out = []
    for f in inner.neighbours(ap, "has_affect_frame"):
        a = eye.substrate.node(f)["attrs"]
        trs = []
        for t in inner.neighbours(f, "has_transform"):
            ta = eye.substrate.node(t)["attrs"]
            trs.append(dict(base=ta.get("base"),
                            transforms=_plain(ta.get("transforms")) or []))
        sig = [[str(p), v] for p, v in _plain(a["signature"])]
        out.append(dict(id=f, status=a.get("status"), tag=a.get("aff_tag"),
                        val_sign=a.get("val_sign"), val_level=a.get("val_level"),
                        ar_level=a.get("ar_level"), sig=sig, covered_by=a.get("covered_by"),
                        transforms=trs))
    return out


def _frame_tuple(fr):
    vl = fr["val_level"]
    return (fr["tag"], int(fr["val_sign"]), None if vl is None else int(vl),
            int(fr["ar_level"]))


def _key(ev):
    return f"{ev[0]}:{ev[1]}"


def _isolated():
    eye, inner = _boot()
    axes_before = len(eye.substrate.nodes("CapabilityAxis"))
    out = {}
    try:
        for ev in ALL_EVENTS:
            hub = _new_hub(eye, inner)
            ap = M._appraise(eye, inner, hub, **inputs(*ev))
            inner.run_rules()
            out[ev] = dict(read=_read(eye, ap), frames=_frames(eye, inner, ap))
        axes_after = len(eye.substrate.nodes("CapabilityAxis"))
        n_obs = len(eye.substrate.nodes("Observation"))
    finally:
        eye.stop()
    return out, axes_before, axes_after, n_obs


def _trials(pairs):
    """Each ordered pair on a FRESH hub: event 1, run_rules, event 2 (+ follows edge), run_rules."""
    eye, inner = _boot()
    out = []
    try:
        for e1, e2 in pairs:
            hub = _new_hub(eye, inner)
            ap1 = M._appraise(eye, inner, hub, **inputs(*e1))
            inner.run_rules()
            ap2 = M._appraise(eye, inner, hub, **inputs(*e2))
            inner.add_edge_unchecked(ap2, "follows", ap1)
            inner.run_rules()
            out.append((e1, e2, _read(eye, ap1), _read(eye, ap2), _dirs(eye, ap2)))
    finally:
        eye.stop()
    return out


def _run():
    if _cache:
        return _cache
    t0 = time.time()
    iso, axes_before, axes_after, n_obs = _isolated()
    v_trials = _trials([(a, b) for a in V_LEVELS for b in V_LEVELS])
    a_trials = {f: _trials([((f, a), (f, b)) for a in ks for b in ks])
                for f, ks in A_FAMILIES.items()}
    _cache.update(iso=iso, axes_before=axes_before, axes_after=axes_after, n_obs=n_obs,
                  v_trials=v_trials, a_trials=a_trials, wall_s=time.time() - t0)
    return _cache


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
    if _cache:
        _record("timing", {"wall_s": _cache["wall_s"]})


# ---------------------------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------------------------

def test_G0_default_preserved():
    diff = subprocess.run(["git", "-C", ROOT, "diff", "--stat", START_COMMIT, RESULT_COMMIT, "--",
                           "seeds/core_emotions.json", "scripts/build_core_emotions_seed.py",
                           "runners/"], capture_output=True, text=True)
    _record("G-0", {"rc": diff.returncode, "diff_stat": diff.stdout})
    assert diff.returncode == 0
    assert diff.stdout.strip() == ""


def _seed_codebook():
    with open(SEED_PATH) as fh:
        seed = json.load(fh)
    out = {}
    for n in seed["nodes"]:
        tag = n["attrs"]["name"].split(":", 1)[1]
        sig = n["attrs"]["signature"]
        if isinstance(sig, str):
            sig = json.loads(sig)
        vals = {p.split(":")[-1]: v for p, v in sig}
        preds = [p.split(":")[-1] for p, _ in sig]
        out[tag] = dict(sig_preds=preds, tuple=(tag, int(vals["val_sign"]),
                                                int(vals["val_level"]) if "val_level" in vals else None,
                                                int(vals["ar_level"])))
    return out


def test_G1_codebook_and_frames():
    res = _run()
    cb = _seed_codebook()
    cb_bad = {}
    for tag, want in CB_APP.items():
        got = cb.get(tag)
        if got is None or got["tuple"] != want:
            cb_bad[tag] = {"seed": None if got is None else got["tuple"], "oracle": want}
    frame_bad = {}
    n_frames = 0
    for ev in ALL_EVENTS:
        want = sorted(ev_frames_app(*ev))
        frames = res["iso"][ev]["frames"]
        n_frames += len(frames)
        got = sorted(_frame_tuple(fr) for fr in frames)
        preds_ok = all(
            [p for p, _ in fr["sig"]] == [f"aff:{fr['tag']}:{x}" for x in
                                          (["val_sign", "val_level", "ar_level"]
                                           if fr["val_level"] is not None
                                           else ["val_sign", "ar_level"])]
            for fr in frames)
        if got != want or not preds_ok:
            frame_bad[_key(ev)] = {"got": got, "want": want, "preds_ok": preds_ok}
    n_codebook = len(cb)
    _record("G-1", {"n_codebook": n_codebook, "codebook_mismatch": cb_bad,
                    "n_frames": n_frames, "frame_mismatch": frame_bad})
    assert n_codebook == 12
    assert not cb_bad, f"codebook differs from prereg section 4: {cb_bad}"
    assert n_frames == 23
    assert not frame_bad, f"frames differ from prereg section 4: {frame_bad}"


def test_G2_recognition():
    res = _run()
    bad = []
    n_checked = 0
    for ev in ALL_EVENTS:
        frames = res["iso"][ev]["frames"]
        for want in ev_frames_app(*ev):
            status_w, base_w, deltas_w = decode_app(want)
            fr = [x for x in frames if x["tag"] == want[0]]
            n_checked += 1
            if len(fr) != 1:
                bad.append({"ev": _key(ev), "tag": want[0], "problem": "frame missing"})
                continue
            fr = fr[0]
            if fr["status"] != status_w:
                bad.append({"ev": _key(ev), "tag": want[0], "status": fr["status"],
                            "want": status_w})
            if fr["covered_by"] != base_w:
                bad.append({"ev": _key(ev), "tag": want[0], "covered_by": fr["covered_by"],
                            "want": base_w})
            if status_w == "recognized":
                if fr["transforms"]:
                    bad.append({"ev": _key(ev), "tag": want[0], "problem": "unexpected transform"})
            else:
                if len(fr["transforms"]) != 1:
                    bad.append({"ev": _key(ev), "tag": want[0],
                                "problem": f"{len(fr['transforms'])} transforms"})
                    continue
                tr = fr["transforms"][0]
                deltas = {}
                for t in tr["transforms"] or []:
                    deltas[str(t.get("pred", "")).split(":")[-1]] = int(t["delta"])
                if tr["base"] != base_w or deltas != deltas_w:
                    bad.append({"ev": _key(ev), "tag": want[0], "transform_base": tr["base"],
                                "deltas": deltas, "want_base": base_w, "want_deltas": deltas_w})
    axes_new = res["axes_after"] - res["axes_before"]
    _record("G-2", {"n_checked": n_checked, "n_mismatch": len(bad), "mismatch": bad,
                    "capability_axes_before": res["axes_before"],
                    "capability_axes_after": res["axes_after"], "new_axes": axes_new})
    assert n_checked == 23
    assert axes_new == 0
    assert not bad, f"recognition differs from prereg section 4: {bad}"


def test_G3_valence_direction():
    rows = []
    for e1, e2, r1, r2, d2 in _run()["v_trials"]:
        truth = sgn(truth_value(*e2) - truth_value(*e1))
        rows.append((e1, e2, truth, d2[0]))
    ok = sum(1 for _, _, t, j in rows if j == t)
    within = [r for r in rows if r[0] != r[1] and r[0][0] == r[1][0] and r[0][0] in ("gain", "loss")]
    ok_w = sum(1 for _, _, t, j in within if j == t)
    _record("G-3", {"n_trials": len(rows), "correct": ok, "within_n": len(within),
                    "within_correct": ok_w})
    assert len(rows) == 121
    assert ok == 121
    assert (ok_w, len(within)) == (40, 40)


def test_G4_arousal_direction():
    counts = {}
    for fam, trials in _run()["a_trials"].items():
        ok = sum(1 for e1, e2, _, _, d2 in trials
                 if d2[1] == sgn(intensity(*e2) - intensity(*e1)))
        counts[fam] = (ok, len(trials))
    _record("G-4", {"counts": counts})
    assert counts == {"threat": (25, 25), "surprise": (25, 25), "gain": (25, 25),
                      "loss": (5, 25)}


def test_G5_old_contract_unchanged():
    res = _run()
    iso = res["iso"]
    bad = {_key(ev): {"measured": iso[ev]["read"], "oracle": oracle(*ev)} for ev in ALL_EVENTS
           if tuple(iso[ev]["read"]) != tuple(oracle(*ev))}
    trials = res["v_trials"] + [t for ts in res["a_trials"].values() for t in ts]
    diffs = [(_key(e1), _key(e2)) for e1, e2, r1, r2, _ in trials
             if r1 != iso[e1]["read"] or r2 != iso[e2]["read"]]
    _record("G-5", {"n_events": len(ALL_EVENTS), "event_mismatch": bad,
                    "n_trials": len(trials), "trial_differs": diffs[:50],
                    "n_trial_differs": len(diffs)})
    assert len(trials) == 221
    assert not bad, f"isolated read-off differs from block 368000 oracle: {bad}"
    assert not diffs, f"read-off not context-free: {diffs[:10]}"


def test_X1_mixed_event():
    """Record only. One trial, mixed then gain k=0: the mixed side has two frames."""
    eye, inner = _boot()
    rec = {}
    try:
        hub = _new_hub(eye, inner)
        ap1 = M._appraise(eye, inner, hub, **inputs("mixed", 0))
        inner.run_rules()
        ap2 = M._appraise(eye, inner, hub, **inputs("gain", 0))
        inner.add_edge_unchecked(ap2, "follows", ap1)
        inner.run_rules()
        rec["mixed_frames"] = [(fr["tag"], fr["status"]) for fr in _frames(eye, inner, ap1)]
        rec["gain0_frames"] = [(fr["tag"], fr["status"]) for fr in _frames(eye, inner, ap2)]
        rec["dirs_ap2"] = _dirs(eye, ap2)
        rec["val_direction_present"] = M._attrs(eye, ap2).get("val_direction") is not None
    finally:
        eye.stop()
    _record("X-1", rec)


def test_X2_cost():
    """Record only: wall time of the whole measurement and Observation nodes decoded."""
    res = _run()
    _record("X-2", {"wall_s": res["wall_s"], "observation_nodes_after_isolated_run": res["n_obs"]})
