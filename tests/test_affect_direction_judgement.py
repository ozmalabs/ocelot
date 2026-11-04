"""Confirmatory test for docs/research/psychology_affect/AFFECT_DIRECTION_JUDGEMENT_PREREG.md
(block 368000, start commit 2c753aaa).

Can Ocelot's own appraisal read-off (seeds/core_emotions.json em_readoff) tell whether valence or
arousal went up, down or stayed the same between two events?

Measurement only. Events are authored with the UNCHANGED scripts/core_emotions_measure.py helpers
(_eye/_hub/_appraise/_attrs); the Rust rule engine computes every read-off. The direction
comparisons are an OFFLINE ideal observer over the published values; nothing is written back into
the graph. One test per gate (G-0..G-6). Measurements go to results/affect_direction_judgement.json.
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import time

import pytest

pytest.importorskip("substrate_rs")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "results", "affect_direction_judgement.json")
START_COMMIT = "2c753aaae0c038631267403d3cdcd30b598a60bb"
# §12.3 (VISION_PROTOCOL): G-6's claim is about THIS RUNG's own commits, so it is pinned to the
# rung's range (prereg commit .. result commit), never to the mutable working tree.
RESULT_COMMIT = "77ba15a77c36ffa3683a7d2a0e7be29a28a566f6"
LOW, T_PRESENT = 50, 256
SURPRISE_R = [150, 200, 400, 800, 1600]

M = importlib.import_module("scripts.core_emotions_measure")


def sgn(x):
    return (x > 0) - (x < 0)


# ---------------------------------------------------------------------------------------------
# §3 event families (world data) and the §4 oracle
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
    """Predicted (valence, arousal, emotion, n_fired)."""
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
# harness: the unchanged core_emotions_measure helpers
# ---------------------------------------------------------------------------------------------

def _read(eye, ap):
    a = M._attrs(eye, ap)
    return (int(a["valence"]), int(a["arousal"]), int(a["emotion"]), int(a["n_fired"]))


def _isolated_all():
    eye, inner = M._eye()
    out = {}
    try:
        for ev in ALL_EVENTS:
            hub, _ = M._hub(eye, inner)
            ap = M._appraise(eye, inner, hub, **inputs(*ev))
            inner.run_rules()
            out[ev] = _read(eye, ap)
    finally:
        eye.stop()
    return out


def _trials(pairs):
    """Each ordered pair on a FRESH hub: event 1, run_rules, event 2, run_rules, read both."""
    eye, inner = M._eye()
    out = []
    try:
        for e1, e2 in pairs:
            hub, _ = M._hub(eye, inner)
            ap1 = M._appraise(eye, inner, hub, **inputs(*e1))
            inner.run_rules()
            ap2 = M._appraise(eye, inner, hub, **inputs(*e2))
            inner.run_rules()
            out.append((e1, e2, _read(eye, ap1), _read(eye, ap2)))
    finally:
        eye.stop()
    return out


_cache = {}


def _run():
    if _cache:
        return _cache
    t0 = time.time()
    _cache["iso"] = _isolated_all()
    _cache["v_trials"] = _trials([(a, b) for a in V_LEVELS for b in V_LEVELS])
    _cache["a_trials"] = {f: _trials([((f, a), (f, b)) for a in ks for b in ks])
                          for f, ks in A_FAMILIES.items()}
    _cache["wall_s"] = time.time() - t0
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


def _key(ev):
    return f"{ev[0]}:{ev[1]}"


# ---------------------------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------------------------

def test_G0_harness_reproduces_the_oracle():
    iso = _run()["iso"]
    rows = {_key(ev): {"measured": iso[ev], "predicted": oracle(*ev)} for ev in ALL_EVENTS}
    bad = {k: v for k, v in rows.items() if tuple(v["measured"]) != tuple(v["predicted"])}
    _record("G-0", {"n_events": len(rows), "mismatches": bad, "rows": rows})
    assert len(rows) == 22
    assert not bad, f"read-off differs from the hand derivation: {bad}"


def test_G1_context_independence():
    res = _run()
    iso = res["iso"]
    trials = res["v_trials"] + [t for ts in res["a_trials"].values() for t in ts]
    diffs = [(_key(e1), _key(e2), r1, r2) for e1, e2, r1, r2 in trials
             if r1 != iso[e1] or r2 != iso[e2]]
    _record("G-1", {"n_trials": len(trials), "n_differ": len(diffs), "differ": diffs[:50]})
    assert len(trials) == 221
    assert not diffs


def _v_rows():
    rows = []
    for e1, e2, r1, r2 in _run()["v_trials"]:
        t1, t2 = truth_value(*e1), truth_value(*e2)
        cls = ("same" if e1 == e2 else
               "within" if e1[0] == e2[0] and e1[0] in ("gain", "loss") else "cross")
        rows.append({"e1": _key(e1), "e2": _key(e2), "cls": cls, "family": e1[0],
                     "truth": sgn(t2 - t1), "val_judged": sgn(r2[0] - r1[0]),
                     "resolvable": t1 == t2 or r1[:2] != r2[:2], "r1": r1, "r2": r2})
    return rows


def test_G2_valence_only_direction():
    rows = _v_rows()
    ok = lambda r: r["val_judged"] == r["truth"]
    counts = {c: (sum(ok(r) for r in rows if r["cls"] == c), sum(r["cls"] == c for r in rows))
              for c in ("within", "cross", "same")}
    total = (sum(ok(r) for r in rows), len(rows))
    _record("G-2", {"total": total, "by_class": counts,
                    "within_judged_histogram": {str(j): sum(r["val_judged"] == j for r in rows
                                                            if r["cls"] == "within")
                                                for j in (-1, 0, 1)}})
    assert total == (81, 121)
    assert counts["within"] == (0, 40)
    assert counts["cross"] == (70, 70)
    assert counts["same"] == (11, 11)


def test_G3_joint_information_bound():
    iso = _run()["iso"]
    rows = _v_rows()
    distinct_val = len({iso[ev][0] for ev in V_LEVELS})
    distinct_tuple = len({iso[ev][:2] for ev in V_LEVELS})
    unres = sorted((r["e1"], r["e2"]) for r in rows if not r["resolvable"])
    expect = sorted((_key(("loss", a)), _key(("loss", b)))
                    for a in range(5) for b in range(5) if a != b)
    _record("G-3", {"distinct_valence": distinct_val, "distinct_tuples": distinct_tuple,
                    "resolvable": sum(r["resolvable"] for r in rows), "n": len(rows),
                    "unresolvable": unres})
    assert distinct_val == 3
    assert distinct_tuple == 7
    assert sum(r["resolvable"] for r in rows) == 101
    assert unres == expect


def test_G4_arousal_direction():
    res = _run()["a_trials"]
    counts = {}
    for fam, trials in res.items():
        ok = sum(sgn(r2[1] - r1[1]) == sgn(intensity(*e2) - intensity(*e1))
                 for e1, e2, r1, r2 in trials)
        counts[fam] = (ok, len(trials))
    _record("G-4", {"counts": counts})
    assert counts == {"threat": (25, 25), "surprise": (25, 25), "gain": (25, 25),
                      "loss": (5, 25)}


def test_G5_mixed_event():
    got = _run()["iso"][("mixed", 0)]
    _record("G-5", {"measured": got, "predicted": oracle("mixed", 0)})
    assert got == (1, 128, 2, 2)


def test_G6_zero_mechanism_change():
    _run()
    diff = subprocess.run(["git", "-C", ROOT, "diff", "--stat", START_COMMIT, RESULT_COMMIT,
                           "--", "runners/", "seeds/"], capture_output=True, text=True)
    _record("G-6", {"rc": diff.returncode, "diff_stat": diff.stdout})
    assert diff.returncode == 0
    assert diff.stdout.strip() == ""
