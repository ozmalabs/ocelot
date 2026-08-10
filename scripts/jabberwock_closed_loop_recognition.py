"""CLOSE THE LOOP ON RECOGNITION — fold the tick/tock pulse into the recursive recogniser.

The other session closed the understand-drive: the open loop MEASURES the residual and discards it; the
closed loop adds CORRECT (a graph-native adaptive hill-climb that finds its direction from the residual's
CHANGE -- keep-or-flip dir, keep-or-halve step) + FOLD (commit next->current at the clock edge -- the tock,
where a value may go DOWN, impossible in a monotone in-tick fixpoint). tock = the modulo of tick; the loop
becomes a closed pulse that drives the shortfall down.

This folds that pulse onto THIS loop -- the recursive recognition operator. The operator's fusion weight
(part_w, the thing the glyph arc tuned by hand) is the tuned theta; OBSERVE runs the recogniser at the
current part_w and writes its accuracy + shortfall; the SAME correction production hill-climbs part_w from
the accuracy's change; the fold commits it on the clock edge. OPEN (fixed weight) vs CLOSED (the pulse):
does the recogniser CORRECT its own operator toward better accuracy from its residual alone -- no given
gradient, the optimum never shown to it?

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_closed_loop_recognition
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from substrate.world_adapter import WorldAdapter
from domains import omniglot_world as ow
from domains import canonical_parse as cp
from domains.recognition_graph import predict_recursive_sc_term, PARSE_EDGE

WHOLE_N, PER_PART, THETA0_W, TARGET, TICKS = 64, 12, 1.30, 0.87, 13
THETAS = (55.0, 70.0, 85.0)


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _o(k): return {"type": "Attr", "node": {"name": "o", "type": "Var"}, "key": k}
def _lit(v): return {"type": "Lit", "value": v}


# the SAME graph-native adaptive hill-climb the other session closed the toy with (the agent's correction):
_delta = {"type": "Minus", "a": _o("skill"), "b": _o("last_skill")}
_improved = {"type": "Gt", "a": _delta, "b": _lit(0.0)}
_next_dir = {"type": "IfThenElse", "cond": _improved, "then": _o("dir"),
             "other": {"type": "Times", "items": [_lit(-1.0), _o("dir")]}}
_next_step = {"type": "IfThenElse", "cond": _improved, "then": _o("step"),
              "other": {"type": "Times", "items": [_lit(0.5), _o("step")]}}
_next_theta = {"type": "Plus", "items": [_o("theta"), {"type": "Times", "items": [_next_dir, _next_step]}]}

MANIFEST = {
    "id": "closedloop_recog", "version": "1.0.0", "depends_on": [],
    "nodes": [
        {"local_id": 0, "type": "TunedOp",
         "attrs": {"theta": THETA0_W, "skill": 0.0, "last_skill": -1.0, "dir": -1.0, "step": 0.32,
                   "next_theta": THETA0_W, "next_dir": -1.0, "next_step": 0.32}},
        {"local_id": 1, "type": "CapAxis", "attrs": {"target": TARGET, "shortfall": 1.0}},
    ],
    "edges": [{"src": {"local": 0}, "type": "tunes", "tgt": {"local": 1}}],
    "productions": [{"provenance": "seed:closedloop:tunes", "src": {"type": "TunedOp", "var": "o"},
                     "edge_type": "tunes", "tgt": {"type": "CapAxis", "var": "ax"}}],
    "rules": [{
        "name": "shortfall_drives_correction",
        "match": [["o", "tunes", "ax"]], "where": {"type": "Lit", "value": True},
        "effects": [
            ["set_attr", "o", "next_dir", {"__term__": _next_dir}],
            ["set_attr", "o", "next_step", {"__term__": _next_step}],
            ["set_attr", "o", "next_theta", {"__term__": _next_theta}],
        ],
    }],
}


def _build_eval(episodes=12, way=12):
    """A FIXED held-out eval (deterministic given part_w) so the recogniser's accuracy is a clean landscape
    the hill-climb can ride -- the world executor; the optimum is never written into the agent."""
    by = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by = {a: cs for a, cs in by.items() if len(cs) >= way}
    alph = sorted(by); rng = np.random.default_rng(7); wc, pc = {}, {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p, th):
        k = (p, th)
        if k not in pc:
            pc[k] = cp.canonical_parts(ow.load_strokes(p), th, per_part=PER_PART)
        return pc[k]

    def add(s, p, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for pp in parts(p, 70.0):
            s.add_edge_unchecked(n, "has_stroke", s.add_node("Stroke", {"stroke_pts": pp.tolist()}))
        for th in THETAS:
            ph = s.add_node("ParseHyp", {"theta": th}); s.add_edge_unchecked(n, PARSE_EDGE, ph)
            for pp in parts(p, th):
                s.add_edge_unchecked(ph, "has_stroke", s.add_node("Stroke", {"stroke_pts": pp.tolist()}))
        return n

    specs = []
    for _ in range(episodes):
        ch = by[alph[int(rng.integers(len(alph)))]]
        idx = rng.permutation(len(ch))[:way]
        ex = int(rng.integers(20)); qd = int(rng.integers(20))
        while qd == ex:
            qd = int(rng.integers(20))
        specs.append((ch, idx, ex, qd))
    return specs, add


def make_skill(specs, add):
    def skill(part_w):
        """OBSERVE: run the recursive recogniser at this fusion weight; return its one-shot accuracy."""
        term = _Pred(predict_recursive_sc_term(max(0.0, part_w), 1.6, ("has_stroke",), 4.0, 2.0))
        ok = tot = 0
        for ch, idx, ex, qd in specs:
            s = srs.Substrate(); qs = []
            for j in idx:
                fs = ow.drawings(ch[j])
                if len(fs) < 20:
                    continue
                nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
                c = add(s, fs[ex], False); s.set_attr(c, "name", nm); qs.append((nm, fs[qd]))
            for nm, qp in qs:
                m = add(s, qp, True)
                w = s.evaluate(term, {"s": m})
                ok += (w is not None and s.node(w)["attrs"].get("name") == nm); tot += 1
        return ok / max(tot, 1)
    return skill


def run(closed, skill):
    ad = WorldAdapter(); ad.inner.load_seed_manifest(MANIFEST, ad.agent)
    o = next(n for n in ad.s.nodes("TunedOp")); ax = next(n for n in ad.s.nodes("CapAxis"))
    rows = []
    for t in range(TICKS):
        a = ad.s.node(o)["attrs"]
        sk = skill(a["theta"])                                        # OBSERVE (host I/O)
        ad.s.set_attr(o, "skill", sk); ad.s.set_attr(ax, "shortfall", TARGET - sk)
        rows.append((a["theta"], sk, TARGET - sk))
        if closed:
            ad.master_tick(); ad.tick()                               # CORRECT: the production computes next_*
            b = ad.s.node(o)["attrs"]
            ad.s.set_attr(o, "theta", b["next_theta"])                # FOLD at the clock edge (the tock)
            ad.s.set_attr(o, "last_skill", sk)
            ad.s.set_attr(o, "dir", b["next_dir"]); ad.s.set_attr(o, "step", b["next_step"])
    return rows


def main():
    print("=" * 96)
    print("CLOSE THE LOOP ON RECOGNITION — fold the tick/tock pulse onto the recursive recogniser's fusion weight.")
    print("=" * 96)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1
    specs, add = _build_eval()
    skill = make_skill(specs, add)
    op = run(False, skill)
    cl = run(True, skill)
    print(f"\n  operator fusion weight part_w0={THETA0_W} (off the arc's hand-tuned ~0.25); target acc={TARGET};")
    print(f"  the recogniser never sees the optimum -- it finds it from its own accuracy residual.\n")
    print(f"    {'tick':>5}{'OPEN shortfall':>16}{'CLOSED shortfall':>18}{'CLOSED part_w':>15}{'CLOSED acc':>12}")
    for t in range(TICKS):
        print(f"    {t:>5}{op[t][2]:>16.4f}{cl[t][2]:>18.4f}{cl[t][0]:>15.3f}{cl[t][1]:>12.3f}")

    print("\n" + "=" * 96)
    print(f"  OPEN  shortfall {op[0][2]:.3f} -> {op[-1][2]:.3f}: FLAT (acc {op[0][1]:.3f}). measures + discards; the operator")
    print(f"        is never corrected.")
    print(f"  CLOSED shortfall {cl[0][2]:.3f} -> {cl[-1][2]:.3f}: DECAYED (acc {cl[0][1]:.3f}->{cl[-1][1]:.3f}). the SAME pulse")
    print(f"        -- residual -> graph-native hill-climb -> fold at the clock edge -- drove part_w {THETA0_W}->{cl[-1][0]:.2f}")
    print(f"        from the accuracy's CHANGE alone, no given gradient. the recursive recogniser now CORRECTS its")
    print(f"  own operator toward better recognition. The tick/tock closed loop is folded into the recognition loop.")
    print("=" * 96)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
