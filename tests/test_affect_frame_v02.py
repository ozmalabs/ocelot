"""Confirmatory test for docs/research/psychology_affect/AFFECT_FRAME_V02_PREREG.md
(block 370000, start commit d1e7d6ab).

Does the affect frame v0.2 rule set (seeds/affect_frame.json v0.2.0 with
seeds/affect_frame_canonical.json) (a) give each emotion tag a ComponentDirection for mixed
events, (b) grow the affect codebook from experience through the sd loop, and (c) project the
latest appraisal's frames onto the canonical AffectiveState, with the old contract unchanged?

Measurement only. Events are authored with the unchanged scripts/core_emotions_measure.py helpers.
The Rust engine computes every frame, component, growth and projection. The expected values are
the prereg Appendix A oracle, transcribed as pure arithmetic. G-5 (the block 369000 test re-run)
is not in this file: it is tests/test_affect_frame_codebook.py, run in the same pytest
invocation. Measurements go to results/affect_frame_v02.json.
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
OUT_PATH = os.path.join(ROOT, "results", "affect_frame_v02.json")
START_COMMIT = "d1e7d6abaaddc2b2c654449427cd12b5e1018486"
# VISION_PROTOCOL §12.3: G-0 is pinned to this rung's own range, never the mutable tree.
RESULT_COMMIT = "d3000ad51ce56b319d0f385f45986e9c01990a3c"
LOW = 50

M = importlib.import_module("scripts.core_emotions_measure")

_cache = {}

SEED_FRAME = "affect_frame"
SEED_CANON = "affect_frame_canonical"
SEED_AFFECT = "affective_state_core"


def sgn(x):
    return (x > 0) - (x < 0)


# ---------------------------------------------------------------------------------------------
# event families (world data), copied from tests/test_affect_frame_codebook.py (369000)
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


V_LEVELS = [("loss", k) for k in range(5)] + [("neutral", 0)] + [("gain", k) for k in range(5)]
SURPRISE_R = [150, 200, 400, 800, 1600]
A_FAMILIES = {"threat": list(range(5)), "surprise": SURPRISE_R,
              "gain": list(range(5)), "loss": list(range(5))}
ALL_EVENTS = (V_LEVELS + [("threat", k) for k in range(5)]
              + [("surprise", r) for r in SURPRISE_R] + [("mixed", 0)])


# ---------------------------------------------------------------------------------------------
# prereg Appendix A oracle (pure arithmetic, transcribed)
# ---------------------------------------------------------------------------------------------

def lq(x):
    return math.floor((math.log(x) if x > 0 else math.log(1e-9)) / math.log(2) + 0.5)


def frame(t, vp=0, tp=0, r=0):
    """(tag, val_sign, val_level or None, ar_level)."""
    return {"joy": (t, 1, lq(vp), lq(vp)), "sadness": (t, -1, lq(abs(vp)), lq(LOW)),
            "fear": (t, -1, None, lq(tp)), "anxiety": (t, -1, None, lq(tp)),
            "surprise": (t, 0, None, lq(r)), "none": (t, 0, None, lq(LOW))}[t]


def ev_frames(kind, k):
    """Emission order for mixed is fear then joy (af_emit_fear precedes af_emit_joy)."""
    if kind == "gain":
        return [frame("joy", vp=(1024 >> k) - (1024 >> (k + 1)))]
    if kind == "loss":
        return [frame("sadness", vp=(1024 >> (k + 1)) - (1024 >> k))]
    if kind == "neutral":
        return [frame("none")]
    if kind == "threat":
        p = 1024 >> k
        return [frame("anxiety" if p >= 256 else "fear", tp=p)]
    if kind == "surprise":
        return [frame("surprise", r=k)]
    return [frame("fear", tp=128), frame("joy", vp=448)]


def K(f):
    return f[1] * (f[2] + 1) if f[2] is not None else f[1]


def comp_expected(e1, e2):
    """{tag: (val_direction, ar_direction)} for tags shared by the two appraisals."""
    fa = {f[0]: f for f in ev_frames(*e1)}
    fb = {f[0]: f for f in ev_frames(*e2)}
    return {t: (sgn(K(fb[t]) - K(fa[t])), sgn(fb[t][3] - fa[t][3])) for t in fa if t in fb}


# §4.1 trial sets (Appendix A `single` and `mixed`)
SINGLE_TRIALS = ([(a, b) for a in V_LEVELS for b in V_LEVELS]
                 + [((f, x), (f, y)) for f, ks in A_FAMILIES.items() for x in ks for y in ks])
_E = ALL_EVENTS
MIXED_TRIALS = ([(("mixed", 0), s) for s in _E[:-1]] + [(s, ("mixed", 0)) for s in _E[:-1]]
                + [(("mixed", 0), ("mixed", 0))])

# §4.2 growth: the held shape of each tag is the first frame of that tag in the stream.
GROWTH_NAMES = ["affect:sadness", "affect:none", "affect:joy", "affect:anxiety",
                "affect:fear", "affect:surprise"]
# §4.2 per-frame statuses, keyed by (event, tag)
STATUS = {
    (("loss", 0), "sadness"): "recognized",
    (("neutral", 0), "none"): "recognized",
    (("gain", 0), "joy"): "recognized",
    (("threat", 0), "anxiety"): "recognized",
    (("threat", 3), "fear"): "recognized",
    (("surprise", 150), "surprise"): "recognized",
    (("mixed", 0), "joy"): "recognized",
    (("mixed", 0), "fear"): "recognized",
}
DELTAS = {
    ("loss", 1): ("sadness", {"val_level": -1}),
    ("loss", 2): ("sadness", {"val_level": -2}),
    ("loss", 3): ("sadness", {"val_level": -3}),
    ("loss", 4): ("sadness", {"val_level": -4}),
    ("gain", 1): ("joy", {"val_level": -1, "ar_level": -1}),
    ("gain", 2): ("joy", {"val_level": -2, "ar_level": -2}),
    ("gain", 3): ("joy", {"val_level": -3, "ar_level": -3}),
    ("gain", 4): ("joy", {"val_level": -4, "ar_level": -4}),
    ("threat", 1): ("anxiety", {"ar_level": -1}),
    ("threat", 2): ("anxiety", {"ar_level": -2}),
    ("threat", 4): ("fear", {"ar_level": -1}),
    ("surprise", 200): ("surprise", {"ar_level": 1}),
    ("surprise", 400): ("surprise", {"ar_level": 2}),
    ("surprise", 800): ("surprise", {"ar_level": 3}),
    ("surprise", 1600): ("surprise", {"ar_level": 4}),
}
for _ev in [("loss", k) for k in range(1, 5)] + [("gain", k) for k in range(1, 5)] \
        + [("threat", 1), ("threat", 2), ("threat", 4)]:
    STATUS[(_ev, DELTAS[_ev][0])] = "decoded"
for _r in (200, 400, 800, 1600):
    STATUS[(("surprise", _r), "surprise")] = "recognized_transformed"
STATUS[(("threat", 0), "anxiety")] = "recognized"

# §4.3 projection K along E
K_SEQ = [-10, -9, -8, -7, -6, 0, 10, 9, 8, 7, 6, -1, -1, -1, -1, -1, 0, 0, 0, 0, 0, None]


# ---------------------------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------------------------

def _boot(seeds):
    from domains.reflective_faculty import _ensure_shape_decode_loop
    from substrate.seed_loader import manifest_for
    eye, inner = M._eye()
    _ensure_shape_decode_loop(eye.substrate, inner, eye._agent)
    for s in seeds:
        inner.load_seed_manifest(manifest_for(s), eye._agent)
    return eye, inner


def _new_hub(eye, inner):
    hub, _ = M._hub(eye, inner)
    inner.add_edge_unchecked(eye._agent, "has_emotion_hub", hub)
    return hub


def _plain(x):
    if isinstance(x, (list, tuple)):
        return [_plain(i) for i in x]
    return x


def _int_or_none(v):
    return None if v is None else int(v)


def _components(eye, inner, ap):
    out = []
    for cd in inner.neighbours(ap, "has_component_direction"):
        a = eye.substrate.node(cd)["attrs"]
        out.append((str(a["tag"]), _int_or_none(a.get("val_direction")),
                    _int_or_none(a.get("ar_direction"))))
    return out


def _dirs(eye, ap):
    a = M._attrs(eye, ap)
    return (_int_or_none(a.get("val_direction")), _int_or_none(a.get("ar_direction")))


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
        _record("timing", {"wall_s": {k: _cache[k] for k in ("wall_A", "wall_B", "wall_C")
                                      if k in _cache}})


# ---------------------------------------------------------------------------------------------
# arm A: components (single-frame and mixed trials), canonical codebook loaded
# ---------------------------------------------------------------------------------------------

def _arm_a_trials(pairs):
    eye, inner = _boot([SEED_FRAME, SEED_CANON])
    out = []
    try:
        for e1, e2 in pairs:
            hub = _new_hub(eye, inner)
            ap1 = M._appraise(eye, inner, hub, **inputs(*e1))
            inner.run_rules()
            ap2 = M._appraise(eye, inner, hub, **inputs(*e2))
            inner.add_edge_unchecked(ap2, "follows", ap1)
            inner.run_rules()
            out.append(dict(e1=e1, e2=e2, comps=_components(eye, inner, ap2),
                            af_dir=_dirs(eye, ap2)))
    finally:
        eye.stop()
    return out


def _arm_a():
    if "A" not in _cache:
        t0 = time.time()
        _cache["A"] = dict(single=_arm_a_trials(SINGLE_TRIALS),
                           mixed=_arm_a_trials(MIXED_TRIALS))
        _cache["wall_A"] = time.time() - t0
    return _cache["A"]


# ---------------------------------------------------------------------------------------------
# arm B: growth, one stream on one agent, canonical codebook NOT loaded
# ---------------------------------------------------------------------------------------------

def _frame_read(eye, inner, fid):
    a = eye.substrate.node(fid)["attrs"]
    trs = []
    for t in inner.neighbours(fid, "has_transform"):
        ta = eye.substrate.node(t)["attrs"]
        deltas = {}
        for d in _plain(ta.get("transforms")) or []:
            deltas[str(d.get("pred", "")).split(":")[-1]] = int(d["delta"])
        trs.append(dict(base=str(ta.get("base")), deltas=deltas))
    return dict(tag=str(a.get("aff_tag")), status=str(a.get("status")),
                transform_explained=_int_or_none(a.get("transform_explained")),
                transforms=trs)


def _arm_b():
    if "B" in _cache:
        return _cache["B"]
    t0 = time.time()
    eye, inner = _boot([SEED_FRAME])
    try:
        ax_before = len(eye.substrate.nodes("CapabilityAxis"))
        events = []
        for ev in ALL_EVENTS:
            hub = _new_hub(eye, inner)
            ap = M._appraise(eye, inner, hub, **inputs(*ev))
            inner.run_rules()
            events.append((ev, list(inner.neighbours(ap, "has_affect_frame"))))
        ax_after = len(eye.substrate.nodes("CapabilityAxis"))
        epoch = _int_or_none(eye.substrate.node(eye._agent)["attrs"].get("codebook_epoch"))
        grown = []
        for sid in sorted(eye.substrate.nodes("ShapeSignature"), key=lambda n: n.value):
            a = eye.substrate.node(sid)["attrs"]
            if str(a.get("kind")) != "affect":
                continue
            sig = [[str(p), float(v)] for p, v in _plain(a.get("signature"))]
            grown.append(dict(name=str(a.get("name")), signature=sig))
        frames = []
        for ev, fids in events:
            for fid in fids:
                fr = _frame_read(eye, inner, fid)
                fr["event"] = ev
                frames.append(fr)
    finally:
        eye.stop()
    _cache["B"] = dict(ax_before=ax_before, ax_after=ax_after, epoch=epoch, grown=grown,
                       frames=frames)
    _cache["wall_B"] = time.time() - t0
    return _cache["B"]


# ---------------------------------------------------------------------------------------------
# arm C: projection onto the canonical AffectiveState, one hub, E in order with follows
# ---------------------------------------------------------------------------------------------

AFF_KEYS = ("valence", "arousal", "baseline")


def _arm_c():
    if "C" in _cache:
        return _cache["C"]
    t0 = time.time()
    eye, inner = _boot([SEED_FRAME, SEED_CANON, SEED_AFFECT])
    rows = []
    try:
        hub = _new_hub(eye, inner)
        aff = inner.neighbours(eye._agent, "has_affective_state")[0]
        inner.add_edge_unchecked(hub, "has_affective_state", aff)
        seed_attrs = _plain(eye.substrate.node(aff)["attrs"])
        prev = None
        for ev in ALL_EVENTS:
            ap = M._appraise(eye, inner, hub, **inputs(*ev))
            if prev is not None:
                inner.add_edge_unchecked(ap, "follows", prev)
            inner.run_rules()
            a = eye.substrate.node(aff)["attrs"]
            rows.append(dict(event=ev,
                             frame_components=_plain(a.get("frame_components")),
                             frame_count=_int_or_none(a.get("frame_count")),
                             frame_key=a.get("frame_key"),
                             valence=a.get("valence"), arousal=a.get("arousal"),
                             baseline=a.get("baseline"),
                             attrs_now=_plain(a)))
            prev = ap
    finally:
        eye.stop()
    _cache["C"] = dict(rows=rows, seed_attrs=seed_attrs)
    _cache["wall_C"] = time.time() - t0
    return _cache["C"]


# ---------------------------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------------------------

def test_G0_isolation():
    import subprocess as sp
    diff = sp.run(["git", "-C", ROOT, "diff", "--stat", START_COMMIT, RESULT_COMMIT, "--",
                   "seeds/core_emotions.json", "scripts/build_core_emotions_seed.py",
                   "runners/"], capture_output=True, text=True)
    _record("G-0", {"rc": diff.returncode, "diff_stat": diff.stdout})
    assert diff.returncode == 0
    assert diff.stdout.strip() == ""


def test_G1_components_single_frame():
    a = _arm_a()
    rows = a["single"]
    n = len(rows)
    with_comp = 0
    none_comp = 0
    bad = []
    for r in rows:
        shared = (ev_frames(*r["e1"])[0][0] == ev_frames(*r["e2"])[0][0])
        if shared:
            if len(r["comps"]) == 1 and r["comps"][0][1:] == r["af_dir"] \
                    and r["comps"][0][0] == ev_frames(*r["e2"])[0][0]:
                with_comp += 1
            else:
                bad.append({"e1": r["e1"], "e2": r["e2"], "comps": r["comps"],
                            "af_dir": r["af_dir"]})
        else:
            if not r["comps"]:
                none_comp += 1
            else:
                bad.append({"e1": r["e1"], "e2": r["e2"], "comps": r["comps"],
                            "af_dir": r["af_dir"], "problem": "unexpected component"})
    _record("G-1", {"n_trials": n, "with_one_component_equal_af_direction": with_comp,
                    "none": none_comp, "mismatch": bad, "n_mismatch": len(bad)})
    assert n == 221
    assert with_comp == 139
    assert none_comp == 82
    assert not bad, f"single-frame components differ from prereg section 4.1: {bad[:10]}"


def test_G2_components_mixed():
    a = _arm_a()
    rows = a["mixed"]
    bad = []
    trials_with = 0
    total = 0
    af_set = []
    for r in rows:
        want = comp_expected(r["e1"], r["e2"])
        got = {t: (vd, ad) for t, vd, ad in r["comps"]}
        total += len(r["comps"])
        if r["comps"]:
            trials_with += 1
        if r["af_dir"] != (None, None):
            af_set.append({"e1": r["e1"], "e2": r["e2"], "af_dir": r["af_dir"]})
        if got != want or len(got) != len(r["comps"]):
            bad.append({"e1": r["e1"], "e2": r["e2"], "got": r["comps"], "want": want})
    _record("G-2", {"n_trials": len(rows), "trials_with_components": trials_with,
                    "components": total, "af_direction_set": af_set, "mismatch": bad,
                    "n_mismatch": len(bad)})
    assert len(rows) == 43
    assert trials_with == 15
    assert total == 16
    assert not af_set, f"af_direction set on a mixed trial: {af_set[:5]}"
    assert not bad, f"mixed components differ from prereg section 4.1: {bad[:10]}"


def test_G3_growth():
    b = _arm_b()
    grown_names = [g["name"] for g in b["grown"]]
    sig_bad = []
    want_sigs = {}
    for ev in ALL_EVENTS:
        for f in ev_frames(*ev):
            if f[0] not in want_sigs:
                sig = [[f"aff:{f[0]}:val_sign", float(f[1])]]
                if f[2] is not None:
                    sig.append([f"aff:{f[0]}:val_level", float(f[2])])
                sig.append([f"aff:{f[0]}:ar_level", float(f[3])])
                want_sigs[f[0]] = sig
    for g in b["grown"]:
        tag = g["name"].split(":", 1)[1]
        if g["signature"] != want_sigs.get(tag):
            sig_bad.append({"name": g["name"], "got": g["signature"],
                            "want": want_sigs.get(tag)})
    status_bad = []
    n_checked = 0
    counts = {}
    for fr in b["frames"]:
        key = (fr["event"], fr["tag"])
        want = STATUS.get(key)
        n_checked += 1
        counts[fr["status"]] = counts.get(fr["status"], 0) + 1
        if fr["status"] != want:
            status_bad.append({"event": fr["event"], "tag": fr["tag"],
                               "status": fr["status"], "want": want})
        if fr["status"] == "recognized":
            if fr["transforms"]:
                status_bad.append({"event": fr["event"], "tag": fr["tag"],
                                   "problem": "transform on a recognized frame"})
            continue
        if len(fr["transforms"]) != 1 or fr["transform_explained"] != 1:
            status_bad.append({"event": fr["event"], "tag": fr["tag"],
                               "problem": "transform_explained or has_transform count",
                               "transform_explained": fr["transform_explained"],
                               "n_transforms": len(fr["transforms"])})
            continue
        tr = fr["transforms"][0]
        dkey = (fr["event"][0], fr["event"][1])
        want_base, want_deltas = DELTAS[dkey]
        if tr["base"] != "affect:" + want_base or tr["deltas"] != want_deltas:
            status_bad.append({"event": fr["event"], "tag": fr["tag"], "base": tr["base"],
                               "deltas": tr["deltas"], "want_deltas": want_deltas})
    _record("G-3", {"grown_names": grown_names, "grown": b["grown"],
                    "signature_mismatch": sig_bad, "capability_axes_delta":
                    b["ax_after"] - b["ax_before"], "codebook_epoch": b["epoch"],
                    "n_frames": n_checked, "status_counts": counts,
                    "mismatch": status_bad, "n_mismatch": len(status_bad)})
    assert grown_names == GROWTH_NAMES
    assert not sig_bad, f"grown signatures differ from frame signatures: {sig_bad}"
    assert b["ax_after"] - b["ax_before"] == 6
    assert b["epoch"] == 6
    assert n_checked == 23
    assert counts == {"recognized": 8, "recognized_transformed": 4, "decoded": 11}, counts
    assert not status_bad, f"frame statuses or transforms differ from prereg section 4.2: {status_bad}"


def test_G4_projection():
    c = _arm_c()
    bad = []
    seed_attrs = c["seed_attrs"]
    for i, row in enumerate(c["rows"]):
        ev = row["event"]
        want_frames = sorted([[f[0], int(f[1]), _int_or_none(f[2]), int(f[3])]
                              for f in ev_frames(*ev)], key=lambda x: str(x))
        got_frames = row["frame_components"] or []
        got_n = sorted([[str(x[0]), int(x[1]), _int_or_none(x[2]), int(x[3])]
                        for x in got_frames], key=lambda x: str(x))
        problems = []
        if row["frame_count"] != len(ev_frames(*ev)):
            problems.append(("frame_count", row["frame_count"], len(ev_frames(*ev))))
        if got_n != want_frames:
            problems.append(("frame_components", got_frames, want_frames))
        want_key = K_SEQ[i]
        got_key = row["frame_key"]
        if (None if got_key is None else int(got_key)) != want_key:
            problems.append(("frame_key", got_key, want_key))
        if (row["valence"], row["arousal"], row["baseline"]) != (0.0, 0.0, 1.0):
            problems.append(("valence/arousal/baseline", row["valence"], row["arousal"],
                             row["baseline"]))
        now = row["attrs_now"]
        changed = {k: (seed_attrs.get(k), now.get(k)) for k in seed_attrs
                   if seed_attrs.get(k) != now.get(k)}
        if changed:
            problems.append(("old attrs changed", changed))
        if problems:
            bad.append({"i": i, "event": ev, "problems": problems})
    _record("G-4", {"n_events": len(c["rows"]), "mismatch": bad, "n_mismatch": len(bad),
                    "seed_attrs": seed_attrs,
                    "mixed_emitted_order": [r["frame_components"] for r in c["rows"]
                                             if r["event"] == ("mixed", 0)]})
    assert len(c["rows"]) == 22
    assert not bad, f"projection differs from prereg section 4.3: {bad}"
