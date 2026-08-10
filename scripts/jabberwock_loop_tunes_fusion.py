"""WIRE THE LOOP ONTO A REAL SPEECH PARAM — the closed loop self-tunes a fusion weight from its OWN residual (no labels).

The agent's move (H): the self-tuning loop (jabberwock_finish_the_loop) is built+confirmed on a SYNTHETIC operator but
never wired to real speech. Wire it: let the graph-native adaptive hill-climb tune a real DECODE fusion weight w from a
LABEL-FREE residual (decode confidence), folding at the clock edge -- and check the weight it lands on matches/beats the
hand-fit (label-using) global best, with NO manual setpoint and NO access to the test labels.

Decode: two COMPLEMENTARY ACOUSTIC cues on the held-out clips (no frequency/selection confound) -- A = triphone-backoff
read (the ~17% win), B = monophone read. Fused distance fused_w(c) = zA(c) + w*zB(c) per clip (z = per-clip z-score so
w is meaningful). argmin = prediction. The loop's skill(w) = mean decode CONFIDENCE (top-1 softmax prob, fixed temp) --
a label-free signal it maximizes. accuracy(w) uses labels ONLY for the hand-fit baseline + final scoring; the loop never
sees it.

Pre-committed bar (the agent's): KEEP = loop's auto-w content acc matches-or-beats hand-fit global best, no setpoint,
beats frozen-w control; STOP = loop can't reach the fixed-weight baseline / fails to converge / gain within noise (|z|<1)
-> land. FAIRNESS = frozen-w control on the IDENTICAL decode path + same clips; loop tunes on confidence (its residual),
never on scored accuracy.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_loop_tunes_fusion
"""
from __future__ import annotations

import glob
import math
import os
import pickle
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from substrate.world_adapter import WorldAdapter
from scripts.phonebank import CACHE, _meta
from scripts.jabberwock_reads_oov_from_phones import phones, dtw, STOP
from scripts.jabberwock_realign_emission import build_units, realign_split, uniform_split, template

N_WAY = 100
SAMPLE = 60000
TICKS = 22


def mono_template(w, mono):
    ph = phones(w)
    if not ph:
        return None
    parts = []
    for p in ph:
        m = mono.get(p)
        if m is None:
            return None
        parts.append(m)
    return np.concatenate(parts, 0)


# ---- the graph-native adaptive hill-climb (verbatim structure from finish_the_loop) ----
def _o(k):
    return {"type": "Attr", "node": {"name": "o", "type": "Var"}, "key": k}


def _lit(v):
    return {"type": "Lit", "value": v}


_delta = {"type": "Minus", "a": _o("skill"), "b": _o("last_skill")}
_improved = {"type": "Gt", "a": _delta, "b": _lit(0.0)}
_next_dir = {"type": "IfThenElse", "cond": _improved, "then": _o("dir"),
             "other": {"type": "Times", "items": [_lit(-1.0), _o("dir")]}}
_next_step = {"type": "IfThenElse", "cond": _improved, "then": _o("step"),
              "other": {"type": "Times", "items": [_lit(0.5), _o("step")]}}
_next_theta = {"type": "Plus", "items": [_o("theta"), {"type": "Times", "items": [_next_dir, _next_step]}]}


def manifest(theta0, step0):
    return {
        "id": "loopfuse", "version": "1.0.0", "depends_on": [],
        "nodes": [
            {"local_id": 0, "type": "TunedOp",
             "attrs": {"theta": theta0, "skill": 0.0, "last_skill": -1.0, "dir": 1.0, "step": step0,
                       "next_theta": theta0, "next_dir": 1.0, "next_step": step0}},
            {"local_id": 1, "type": "CapAxis", "attrs": {"target": 1.0, "shortfall": 1.0}},
        ],
        "edges": [{"src": {"local": 0}, "type": "tunes", "tgt": {"local": 1}}],
        "productions": [{"provenance": "seed:loopfuse:tunes",
                         "src": {"type": "TunedOp", "var": "o"}, "edge_type": "tunes",
                         "tgt": {"type": "CapAxis", "var": "ax"}}],
        "rules": [{"name": "fusion_weight_correction",
                   "match": [["o", "tunes", "ax"]],
                   "where": {"type": "Lit", "value": True},
                   "effects": [["set_attr", "o", "next_dir", {"__term__": _next_dir}],
                               ["set_attr", "o", "next_step", {"__term__": _next_step}],
                               ["set_attr", "o", "next_theta", {"__term__": _next_theta}]]}],
    }


def main():
    print("=" * 100)
    print("WIRE THE LOOP ONTO A REAL SPEECH PARAM — loop self-tunes the acoustic fusion weight from confidence (no labels)")
    print("=" * 100)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    sample = [words[i] for i in rng.permutation(len(words))[:SAMPLE]]
    vocabcount = Counter(w for (w, _f, _p) in words)
    del words
    uni = [(ph, uniform_split(np.asarray(fr, np.float32), ph)) for (_w, fr, ph) in sample]
    _, _, _, mono0 = build_units(uni)
    re_pw = []
    for (_w, fr, ph) in sample:
        fr = np.asarray(fr, np.float32)
        subs = realign_split(fr, ph, mono0)
        re_pw.append((ph, subs if subs is not None else uniform_split(fr, ph)))
    units = build_units(re_pw)
    mono = units[3]
    print(f"  realigned units built ({len(units[0])} triphone medoids).", flush=True)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand = list(dict.fromkeys(list(targets) + distractors))
    cand = [w for w in cand if template(w, units) is not None and mono_template(w, mono) is not None][:N_WAY]
    tA = {w: template(w, units) for w in cand}
    tB = {w: mono_template(w, mono) for w in cand}
    clips = [(w, np.asarray(cf, np.float32)) for (w, cf) in clips]
    print(f"  {len(cand)}-way; {len(clips)} held-out clips; cue A=triphone-backoff, cue B=monophone\n", flush=True)

    # precompute per-clip z-scored cue distances (so the fusion weight is meaningful + reusable for any w)
    ZA, ZB, TRUE = [], [], []
    for (w, cf) in clips:
        dA = np.array([dtw(cf, tA[c]) for c in cand])
        dB = np.array([dtw(cf, tB[c]) for c in cand])
        za = (dA - dA.mean()) / (dA.std() + 1e-9)
        zb = (dB - dB.mean()) / (dB.std() + 1e-9)
        ZA.append(za); ZB.append(zb); TRUE.append(cand.index(w) if w in cand else -1)
    ZA = np.array(ZA); ZB = np.array(ZB); TRUE = np.array(TRUE)
    valid = TRUE >= 0
    TEMP = 1.0                                  # fixed softmax temperature (z-scored cues -> ~unit scale)

    def accuracy(w):
        fused = ZA + w * ZB                      # (clips, cand); lower = better
        pred = fused.argmin(1)
        return 100 * np.mean(pred[valid] == TRUE[valid])

    def confidence(w):                           # LABEL-FREE: mean top-1 softmax prob
        fused = ZA + w * ZB
        p = np.exp(-(fused - fused.min(1, keepdims=True)) / TEMP)
        p = p / p.sum(1, keepdims=True)
        return float(p.max(1)[valid].mean())

    # the accuracy + confidence landscapes (accuracy uses labels = REVEALED only for analysis/baseline)
    ws = np.round(np.arange(-1.0, 2.51, 0.25), 2)
    print(f"    {'w':>6}{'accuracy':>11}{'confidence':>13}")
    accs = {}
    for w in ws:
        a, cf = accuracy(w), confidence(w)
        accs[w] = a
        print(f"    {w:>6.2f}{a:>10.1f}%{cf:>13.4f}", flush=True)
    hand_w = max(ws, key=lambda w: accs[w]); hand_acc = accs[hand_w]
    conf_w = max(ws, key=lambda w: confidence(w))
    print(f"\n  hand-fit best (LABEL-using): w={hand_w} acc {hand_acc:.1f} | confidence-optimum (label-FREE): w={conf_w:.2f}", flush=True)

    # THE LOOP: graph-native hill-climb maximises confidence(w) (its own residual), folds at the clock edge.
    ad = WorldAdapter()
    ad.inner.load_seed_manifest(manifest(theta0=0.0, step0=0.5), ad.agent)
    o = next(n for n in ad.s.nodes("TunedOp"))
    traj = []
    for t in range(TICKS):
        a = ad.s.node(o)["attrs"]
        skill = confidence(a["theta"])           # OBSERVE: run the decode at current w, read its CONFIDENCE (no labels)
        ad.s.set_attr(o, "skill", skill)
        traj.append((a["theta"], skill))
        ad.master_tick(); ad.tick()              # CORRECT: the fold production computes next_*
        b = ad.s.node(o)["attrs"]
        ad.s.set_attr(o, "theta", b["next_theta"])   # FOLD at the clock edge
        ad.s.set_attr(o, "last_skill", skill)
        ad.s.set_attr(o, "dir", b["next_dir"]); ad.s.set_attr(o, "step", b["next_step"])
    w_loop = traj[-1][0]
    loop_acc = accuracy(w_loop)
    frozen_w = 0.0                               # control: pure-triphone, no fusion (a fixed weight, identical path)
    frozen_acc = accuracy(frozen_w)
    print(f"\n  LOOP converged w={w_loop:.3f} (from confidence alone, no labels, no setpoint); "
          f"trajectory w: {' '.join(f'{x:.2f}' for x,_ in traj[::3])}", flush=True)

    n = int(valid.sum())
    def z2(a1, a0):
        p1, p0 = a1 / 100, a0 / 100; p = (p1 + p0) / 2
        se = math.sqrt(2 * p * (1 - p) / n) if 0 < p < 1 else 1e-9
        return (p1 - p0) / se
    print("\n" + "=" * 100)
    print(f"  hand-fit best (labels)  w={hand_w}: {hand_acc:.1f}%   |   LOOP (no labels) w={w_loop:.2f}: {loop_acc:.1f}%   |   "
          f"frozen w=0: {frozen_acc:.1f}%")
    z_hand = z2(loop_acc, hand_acc); z_frozen = z2(loop_acc, frozen_acc)
    matches = loop_acc >= hand_acc - 1e-9 or abs(z_hand) < 1.0
    beats_frozen = loop_acc > frozen_acc
    if matches and beats_frozen and z_frozen >= 1.0:
        print(f"  KEEP — the loop SELF-TUNED a real speech param: from its OWN confidence (no labels, no setpoint) it found")
        print(f"  w={w_loop:.2f}, matching the hand-fit best ({loop_acc:.1f} vs {hand_acc:.1f}, |z|={abs(z_hand):.2f}) and beating frozen")
        print(f"  ({frozen_acc:.1f}, z={z_frozen:.2f}). The closed loop's residual closed at the clock edge on REAL speech. Pulse wired.")
    elif matches and not beats_frozen:
        print(f"  PARTIAL — the loop matched the hand-fit best ({loop_acc:.1f} vs {hand_acc:.1f}) but the fusion adds ~nothing over")
        print(f"  frozen triphone ({frozen_acc:.1f}): the loop correctly found w*~0 from confidence, but there was no real")
        print("  weight to win. Self-tuning works; this fusion has no headroom. Honest.")
    else:
        print(f"  STOP — the loop's label-free optimum did NOT track accuracy (loop {loop_acc:.1f} vs hand-fit {hand_acc:.1f}, "
              f"z={z_hand:.2f}); confidence != correctness here. Fall back to land. Honest (the agent's pre-commitment).")
    print("=" * 100)


if __name__ == "__main__":
    main()
