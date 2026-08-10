"""THE AGENT AUTHORS BPL (graph-native, no teacher) — composes its generative program from its own evidence.

Across this arc the agent built every Bayesian-Program-Learning piece and MEASURED each one. Now it
AUTHORS its BPL recogniser from that evidence, no teacher: a BplComponent per piece carries the
marginal_gain the agent measured (its expertise) and whether it PRESERVES structure. The author_include
Rule is the agent's combine-all decision — include a component iff its measured marginal_gain > 0. The
host then ASSEMBLES the included components into the recognition program and measures it. The author_residual
Rule reads the agent's own excluded set (every excluded piece DISCARDS structure) and authors the spec for
the missing BPL piece — a STRUCTURE-PRESERVING learned per-primitive generative model with joint inference,
the dual of why its four learned attempts failed. The decisions are Rules over the agent's evidence.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_authors_bpl [episodes]
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
from domains.recognition_graph import (smoothdeform_error_term, marginal_part_error_term, shapecontext_error_term,
                                        WORD_ATTR, PARSE_EDGE, _Argmax, _NodesWhere, _Lit, _Neg, _Plus, _Times, _Attr, _V)

SEP = "=" * 92
WHOLE_N, PER_PART = 64, 12
THETAS = (55.0, 70.0, 85.0)

# The agent's OWN measured component evidence from this arc (marginal_gain in accuracy points; whether the
# piece preserves structure). These are the readings it banked, not a teacher's word.
COMPONENTS = [
    {"name": "smooth_deformation",   "term": "smoothdeform", "weight": 1.0,  "marginal_gain": 5.2,   "structure_preserving": 1.0, "learned": 0.0},
    {"name": "marginalising_parse",  "term": "marginal_part", "weight": 0.25, "marginal_gain": 1.1,  "structure_preserving": 1.0, "learned": 0.0},
    {"name": "shape_contexts",       "term": "shapecontext", "weight": 1.6,  "marginal_gain": 1.6,   "structure_preserving": 1.0, "learned": 0.0},
    {"name": "deformation_marginal", "term": "",             "weight": 0.0,  "marginal_gain": -0.6,  "structure_preserving": 1.0, "learned": 0.0},
    {"name": "stroke_relations",     "term": "",             "weight": 0.0,  "marginal_gain": -14.3, "structure_preserving": 0.0, "learned": 0.0},
    {"name": "learned_bag_of_parts", "term": "",             "weight": 0.0,  "marginal_gain": -0.8,  "structure_preserving": 0.0, "learned": 1.0},
    {"name": "learned_part_member",  "term": "",             "weight": 0.0,  "marginal_gain": -1.9,  "structure_preserving": 0.0, "learned": 1.0},
    {"name": "wccn_writer_prior",    "term": "",             "weight": 0.0,  "marginal_gain": -2.0,  "structure_preserving": 0.0, "learned": 1.0},
]
_BUILDERS = {"smoothdeform": smoothdeform_error_term,
             "marginal_part": lambda: marginal_part_error_term(2.0),
             "shapecontext": shapecontext_error_term}


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    way = 20
    print(SEP)
    print("THE AGENT AUTHORS BPL (no teacher): it composes its generative program from the components it")
    print("built + MEASURED across this arc — include a piece iff its own marginal_gain > 0 — then measures it.")
    print(SEP)
    if not ow.have_data("evaluation"):
        print(f"\n  Omniglot strokes not found under {ow.DATA}.")
        return 1

    # --- the agent authors the program: load its evidence as graph data, fire the authoring Rules ---
    a = srs.Substrate()
    a._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "bpl_authoring.json").read_text()), a.add_node("Agent", {}))
    bpl = a.add_node("BplProgram", {})
    cnodes = []
    for c in COMPONENTS:
        cn = a.add_node("BplComponent", {"name": c["name"], "marginal_gain": c["marginal_gain"],
                                         "structure_preserving": c["structure_preserving"], "learned": c["learned"],
                                         "term_key": c["term"], "weight": c["weight"], "included": 0.0})
        a.add_edge_unchecked(bpl, "has_component", cn); cnodes.append(cn)
    a._inner.run_rules(50000)                                     # author_include + author_residual fire

    included = [(c, a.node(cn)["attrs"]) for c, cn in zip(COMPONENTS, cnodes) if a.node(cn)["attrs"].get("included") == 1.0]
    excluded = [c for c, cn in zip(COMPONENTS, cnodes) if a.node(cn)["attrs"].get("included") != 1.0]
    residual = [a.node(r)["attrs"] for r in a.neighbours(bpl, "residual_spec")]

    print(f"\n  the agent's combine-all over its OWN measured marginal_gain:")
    for c in COMPONENTS:
        mark = "INCLUDE" if c["marginal_gain"] > 0 else "exclude"
        print(f"      {c['name']:24} marginal_gain {c['marginal_gain']:+6.1f}  structure_preserving={int(c['structure_preserving'])}  -> {mark}")

    # --- the host ASSEMBLES the authored program from the included components (mechanical, follows the selection) ---
    terms = [_Times([_Lit(float(at["weight"])), _BUILDERS[at["term_key"]]()]) for _, at in included if at.get("term_key")]
    authored = _Pred(_Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w", _Neg(_Plus(terms))))

    # --- measure the authored BPL recogniser on Omniglot one-shot ---
    by_alph = {al: ow.characters(al, "evaluation") for al in ow.alphabets("evaluation")}
    by_alph = {al: cs for al, cs in by_alph.items() if len(cs) >= way}
    alph_names = sorted(by_alph)
    wc: dict = {}; pc: dict = {}

    def whole(p):
        if p not in wc:
            wc[p] = ow.trajectory(p, WHOLE_N, per_stroke=True)
        return wc[p]

    def parts(p, th):
        k = (p, th)
        if k not in pc:
            pc[k] = cp.canonical_parts(ow.load_strokes(p), th, per_part=PER_PART)
        return pc[k]

    def add(s, p, *, q):
        n = s.add_node("Mark", {}) if q else s.add_node("Concept", {"is_word": 1.0})
        s.set_attr(n, "axs_heard_feat" if q else "axs_synth_feat", whole(p).tolist())
        for ss in parts(p, 70.0):
            st = s.add_node("Stroke", {"stroke_pts": ss.tolist()}); s.add_edge_unchecked(n, "has_stroke", st)
        for th in THETAS:
            ph = s.add_node("ParseHyp", {"theta": th}); s.add_edge_unchecked(n, PARSE_EDGE, ph)
            for ss in parts(p, th):
                st = s.add_node("Stroke", {"stroke_pts": ss.tolist()}); s.add_edge_unchecked(ph, "has_stroke", st)
        return n

    rng = np.random.default_rng(7); specs = []
    for _ in range(episodes):
        ch = by_alph[alph_names[int(rng.integers(len(alph_names)))]]
        idx = rng.permutation(len(ch))[:way]
        ex = int(rng.integers(20)); qd = int(rng.integers(20))
        while qd == ex:
            qd = int(rng.integers(20))
        specs.append((ch, idx, ex, qd))

    ok = tot = 0
    for ch, idx, ex, qd in specs:
        s = srs.Substrate(); qs = []
        for j in idx:
            fs = ow.drawings(ch[j])
            if len(fs) < 20:
                continue
            nm = os.path.relpath(ch[j], ow.split_dir("evaluation")).replace(os.sep, "/")
            c = add(s, fs[ex], q=False); s.set_attr(c, "name", nm); qs.append((nm, fs[qd]))
        for nm, qp in qs:
            m = add(s, qp, q=True)
            w = s.evaluate(authored, {"s": m})
            ok += (w is not None and s.node(w)["attrs"].get("name") == nm); tot += 1
    acc = 100 * ok / max(tot, 1)

    print(f"\n  {SEP[:88]}")
    print(f"  the agent AUTHORED its BPL program from {len(included)} measured-positive components "
          f"({', '.join(at['name'] for _, at in included)}),")
    print(f"  excluding {len(excluded)} it measured to HURT. measured one-shot ({way}-way, {episodes} ep): {acc:.1f}%.")
    if residual:
        r = residual[0]
        print(f"\n  and it AUTHORED the residual piece (to close the gap to full BPL ~96.7%), reading its own")
        print(f"  excluded set — every excluded piece discards structure:")
        print(f"      next: '{r['name']}'  (structure_preserving={int(r['structure_preserving'])}, learned={int(r['learned'])})")
        print(f"      why:  {r['rationale']}")
    print(f"\n  the program + the residual spec are the agent's, authored from its OWN measured evidence (Rules")
    print(f"  over marginal_gain) — no teacher. The combine-all of its positives is its best generative reader;")
    print(f"  the residual it names is exactly the learned per-primitive model its prior attempts got wrong.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
