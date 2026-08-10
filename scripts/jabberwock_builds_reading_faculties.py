"""THE JABBERWOCK STARTS BUILDING the two reading faculties its arc concluded it LACKS.

Grounded against human cognitive models (cognitive-models reading): the agent lacks a GENERATIVE
PROGRAM (BPL — its one-shot ceiling) and SEMANTICS (associative agnosia / hyperlexia — percept without
meaning). Its OWN shape faculty classifies them: generative_program -> hierarchical_invariance_buildup
(an inferred hierarchical parse), semantics -> associative_recall (form->concept binding). Those
verdicts dictate the builds. This starts both — measures the generative parse-inference, demonstrates
the semantic binding.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_builds_reading_faculties [episodes]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import omniglot_world as ow
from domains import canonical_parse as cp
from domains.recognition_graph import predict_smooth_part_sc_term

SEP = "=" * 96
WHOLE_N, PER_PART, THETA = 64, 12, 70.0


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    way = 20
    print(SEP)
    print("THE JABBERWOCK STARTS BUILDING the two reading faculties it LACKS (generative program + semantics).")
    print(SEP)

    fac = json.loads((Path(ROOT) / "seeds" / "reading_faculties.json").read_text())
    print("\n  build-targets (seeded WHAT they are + the agent's own shape verdict + status):")
    for n in fac["nodes"]:
        a = n["attrs"]
        print(f"    {a['name']:>28}  shape={a['shape']:>30}  [{a['status']}]")
        print(f"      named by deficit: {a['grounded_by_deficit']}")

    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    wc: dict[str, np.ndarray] = {}
    pc_fixed: dict[str, list] = {}
    pc_infer: dict[str, list] = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p, inferred):
        cache = pc_infer if inferred else pc_fixed
        if p not in cache:
            strokes = ow.load_strokes(p)
            cache[p] = (cp.infer_parse(strokes, per_part=PER_PART) if inferred
                        else cp.canonical_parts(strokes, THETA, per_part=PER_PART))
        return cache[p]

    def add(s, p, inferred, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for ss in parts(p, inferred):
            st = s.add_node("Stroke", {"stroke_pts": ss.tolist()})
            s.add_edge_unchecked(n, "has_stroke", st)
        return n

    rng = np.random.default_rng(7)
    specs = []
    for _ in range(episodes):
        ch = by_alph[alph_names[int(rng.integers(len(alph_names)))]]
        idx = rng.permutation(len(ch))[:way]
        ex = int(rng.integers(20)); qd = int(rng.integers(20))
        while qd == ex:
            qd = int(rng.integers(20))
        specs.append((ch, idx, ex, qd))

    term = predict_smooth_part_sc_term(0.25, 1.6)

    def recog(inferred):
        ok = tot = 0
        for ch, idx, ex, qd in specs:
            s = srs.Substrate(); qs = []
            for j in idx:
                fs = ow.drawings(ch[j])
                if len(fs) < 20:
                    continue
                nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
                c = add(s, fs[ex], inferred, q=False); s.set_attr(c, "name", nm)
                qs.append((nm, fs[qd]))
            for nm, qp in qs:
                m = add(s, qp, inferred, q=True)
                w = s.evaluate(_Pred(term), {"s": m})
                pred = s.node(w)["attrs"].get("name") if w is not None else None
                ok += (pred == nm); tot += 1
        return ok / max(tot, 1)

    # ---- BUILD 1: GENERATIVE PROGRAM — per-character parse inference vs the fixed global threshold ----
    print(f"\n  BUILD 1 — generative program (parse inference). {episodes} episodes, {way}-way one-shot:\n", flush=True)
    fixed = recog(False)
    print(f"    fixed global parse (theta=70, the current best fusion) : {100*fixed:5.1f}%", flush=True)
    infer = recog(True)
    print(f"    INFERRED per-character parse (description-length-minimal): {100*infer:5.1f}%   "
          f"({100*(infer-fixed):+.1f})", flush=True)

    # ---- BUILD 2: SEMANTICS — form->meaning binding, GRAPH-NATIVE (a Rule, no Python decision) ----
    print(f"\n  BUILD 2 — semantics (associative binding), GRAPH-NATIVE: the binding is a Rule, not Python.\n")
    s = srs.Substrate()
    sa = s.add_node("Agent", {})
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "semantic_binding.json").read_text()), sa)
    ch = by_alph[alph_names[0]]
    cands = []
    for j in range(way):
        fs = ow.drawings(ch[j])
        nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
        c = add(s, fs[0], False, q=False); s.set_attr(c, "name", nm)
        cands.append((nm, fs))
    marks = []
    for nm, fs in cands[:3]:
        for di in (1, 2):                                       # two different writers of the SAME char
            m = add(s, fs[di], False, q=True)
            w = s.evaluate(_Pred(term), {"s": m})               # recognition DECISION (graph Term)
            if w is not None:
                s.add_edge_unchecked(m, "recognised_as", w)     # mechanical: record the result edge
            marks.append((nm, m))
    s._inner.run_rules(50000)                                   # the RULE binds form -> meaning (associative recall)

    def meaning(mk):
        for c in s.neighbours(mk, "denotes"):
            if s.node(c)["attrs"].get("is_meaning") == 1.0:
                return c
        return None

    print(f"    {'true char':>22}  meaning concept the form was COMPLETED to (by the Rule)")
    by_char = {}
    for nm, m in marks:
        c = meaning(m)
        cn = s.node(c)["attrs"].get("name", "").split("/")[-1] if c is not None else "(none)"
        by_char.setdefault(nm, set()).add(c)
        print(f"    {nm.split('/')[-1] + ' ' + nm.split('/')[0]:>22}  -> denotes Concept[{cn}]")
    shared = sum(1 for cs in by_char.values() if len(cs) == 1 and None not in cs)
    n_meanings = len([c for c in s.nodes('Concept') if s.node(c)['attrs'].get('is_meaning') == 1.0])
    print(f"\n    associative recall (done by the Rule, no Python): {shared}/{len(by_char)} characters bind")
    print(f"    every instance to ONE shared meaning node; {n_meanings} meaning concepts (deduped by name via")
    print(f"    add_node_if_absent). The percept is bound to meaning, not a label — and the SEMANTICS is graph.")

    print(f"\n  {SEP[:96]}")
    print("  STARTED: both faculties grounded as build-targets (WHAT + the agent's shape verdict) and the")
    print("  first piece of each is built — generative parse inference (measured above) and form->meaning")
    print("  associative binding (demonstrated above). The generative program's harder pieces (relations,")
    print("  generative re-render with inferred deformation) and semantics' depth (denotation, relations")
    print("  to other concepts, comprehension) are the continuation. The lacked faculties are now under way.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
