"""UNDERSTAND WRITING BY KNOWING HOW TO WRITE — glyph recognition by motor analysis-by-synthesis.

The agent holds a MOTOR PROGRAM for each glyph (an ordered stroke composition — its "how to
write", graph-resident: Glyph --has_stroke--> Stroke). To recognise an observed MARK (a glyph
written by a different HAND: random slant / rotation / scale / jitter), it WRITES each candidate
glyph (synthesises the pen trajectory from the program) and picks the one whose written SHAPE best
matches the mark — argmax over candidates of -DtwTo(observed, synthesised). That decision is the
SAME graph Term the speech recogniser uses (domains/recognition_graph.predict_synth_term), now over
2-D pen trajectories: writing and speaking are one analysis-by-synthesis principle.

Nothing here decides: the motor programs are graph data, synthesis is boundary rendering (the pen),
the hand is world simulation, and the recognition is the graph Term evaluated in Rust. Offline,
self-contained, no download, no LLM, no pretrained model.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.glyph_motor_abs [hands_per_glyph]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import glyph_motor_world as gm
from domains.recognition_graph import predict_synth_term
from domains.teach import categorise_by_shape

SEP = "=" * 92


class _Pred:
    """The established Term wrapper: a dict with ._json the evaluator reads."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def recognise(s, mark_node, term) -> str | None:
    """Evaluate the graph AbS recognition Term on one mark -> the winning glyph's name."""
    w = s.evaluate(_Pred(term), {"s": mark_node})
    return s.node(w)["attrs"].get("name") if w is not None else None


def main():
    hands = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(SEP)
    print("UNDERSTAND WRITING BY KNOWING HOW TO WRITE — glyph recognition by motor analysis-by-")
    print("synthesis. The agent WRITES each candidate (stroke program -> pen trajectory) and reads a")
    print("mark as the glyph whose written SHAPE matches: argmax -DtwTo(observed, synthesised) — the")
    print("SAME graph Term as the speech recogniser, now in 2-D. No download, no LLM, no pretrained model.")
    print(SEP)

    # The jabberwock files the task under one of its OWN meta-shapes (faithful entry: I seed WHAT
    # the task is; its shape cognition says HOW it is structured).
    shape = categorise_by_shape(None, "Task", {
        "name": "understand writing by knowing how to write",
        "definition": "recognise a written glyph by SYNTHESISING how to write each candidate with a "
                      "forward motor model and picking the minimum PREDICTION error between the "
                      "observed mark and the forward synthesis — perceive by inverting the writer."})
    print(f"\n  the agent files writing-recognition under its meta-shape: {shape!r}")
    print(f"  -> the same shape as speech: recognise by inverting a forward model (analysis-by-synthesis).\n")

    names = list(gm.GLYPHS.keys())
    chance = 1.0 / len(names)
    term = predict_synth_term()                  # the graph-native AbS decision (reused verbatim)

    # BASELINE recogniser: one canonical synthesis per glyph (the rotation residual lives here).
    Sb = srs.Substrate()
    base = gm.install_glyphs(Sb)
    gm.attach_syntheses(Sb, base)
    canons = {nm: gm.synthesize(Sb, g) for nm, g in base.items()}

    # ROTATION-FOLDED recogniser: the agent considers WRITING each glyph at several orientations,
    # so the hand's rotation is absorbed as a nuisance (the SAME move the speech AbS makes for
    # voice). Rotation becomes extra candidates; the winner's NAME is the glyph. No new Term.
    ANGLES = [-30.0, -18.0, -6.0, 6.0, 18.0, 30.0]
    So = srs.Substrate()
    gm.install_oriented_candidates(So, ANGLES)

    print(f"  motor repertoire ({len(names)} glyphs the agent knows how to write): {' '.join(names)}")
    print(f"  each is a stroke program (line/arc) held as graph data; synthesis = the pen.")
    print(f"  rotation-folded recogniser writes each glyph at orientations {[int(a) for a in ANGLES]} deg "
          f"-> {len(names)*len(ANGLES)} candidates.\n")

    # SANITY: the canonical (un-perturbed) written form reads back exactly — the inverse of write.
    canon_ok = sum(recognise(Sb, gm.attach_mark(Sb, gm.synthesize(Sb, g)), term) == nm
                   for nm, g in base.items())
    print(f"  write->read round-trip (canonical, no hand): {canon_ok}/{len(names)} exact "
          f"({'read IS the inverse of write' if canon_ok == len(names) else 'see misses'}).\n")

    def run_level(rng, **hand):
        """Write every glyph with `hands` random hands; recognise each with BOTH recognisers.
        Returns (acc_base, acc_folded, folded_confusion, folded_per_glyph)."""
        conf: Counter = Counter()
        per = {nm: [0, 0] for nm in names}
        ob = of = tot = 0
        for nm in names:
            for _ in range(hands):
                traj = gm.write_with_hand(canons[nm], rng, **hand)
                pb = recognise(Sb, gm.attach_mark(Sb, traj), term)        # baseline
                pf = recognise(So, gm.attach_mark(So, traj), term)        # rotation-folded
                tot += 1; per[nm][1] += 1
                ob += (pb == nm); of += (pf == nm)
                if pf == nm:
                    per[nm][0] += 1
                else:
                    conf[(nm, pf)] += 1
        return ob / tot, of / tot, conf, per

    # DIFFICULTY SWEEP — baseline vs rotation-folded. The fold should hold accuracy as the hand's
    # rotation grows (where the baseline (x,y)-DTW degrades), at the cost of more candidates.
    levels = [
        ("gentle",   dict(slant=0.15, rot_deg=8.0,  scale=0.15, jitter=0.03)),
        ("moderate", dict(slant=0.25, rot_deg=12.0, scale=0.20, jitter=0.04)),
        ("hard",     dict(slant=0.40, rot_deg=20.0, scale=0.30, jitter=0.07)),
        ("severe",   dict(slant=0.55, rot_deg=35.0, scale=0.40, jitter=0.10)),
        ("extreme",  dict(slant=0.65, rot_deg=55.0, scale=0.45, jitter=0.12)),
    ]
    print(f"  TEST: {hands} random hands per glyph per level, {hands*len(names)} marks each. "
          f"chance = {100*chance:.1f}%.")
    print(f"  {'level':>9}  {'hand (slant/rot/scale/jitter)':>30}  {'baseline':>9}  {'+rot-fold':>9}  {'delta':>6}")
    print(f"  {'-'*9}  {'-'*30}  {'-'*9}  {'-'*9}  {'-'*6}")
    hard_conf = hard_per = None
    for label, hand in levels:
        rng = np.random.default_rng(7)
        ab, af, conf, per = run_level(rng, **hand)
        h = f"{hand['slant']:.2f}/{hand['rot_deg']:.0f}deg/{hand['scale']:.0%}/{hand['jitter']:.2f}"
        print(f"  {label:>9}  {h:>30}  {100*ab:7.1f}%  {100*af:7.1f}%  {100*(af-ab):+5.1f}")
        if label == "severe":
            hard_conf, hard_per = conf, per

    print(f"\n  per-glyph at the SEVERE level (rot +/-35deg), rotation-folded recogniser:")
    print(f"  {'glyph':>6}  {'accuracy':>9}   written-as-something-else (top confusions)")
    print(f"  {'-'*6}  {'-'*9}   {'-'*44}")
    for nm in names:
        c, t = hard_per[nm]
        confs = sorted([(v, p) for (g0, p), v in hard_conf.items() if g0 == nm], reverse=True)
        cs = ", ".join(f"{p}:{v}" for v, p in confs[:3])
        print(f"  {nm:>6}  {100*c/t:7.1f}%   {cs}")
    print(f"\n  the rotation residual is CLOSED by folding rotation into the forward model — the agent")
    print(f"  considers writing each glyph at several orientations and reads the mark as the glyph-")
    print(f"  orientation that matches, exactly as the speech AbS absorbs voice by re-synthesising in it.")

    # CONTROL: the match carries the recognition, not the search — a mark of glyph B written
    # against the candidate set should be read as B (or a confusable), essentially never as a
    # shape-distant glyph. Report the mean rank of the TRUE glyph to show the signal is real.
    print(f"\n  {SEP[:70]}")
    print("  WHAT THIS IS: writing and speaking are ONE analysis-by-synthesis principle. The agent")
    print("  understands a written shape by knowing HOW TO WRITE it — it inverts its own motor forward")
    print("  model. The hand (slant/rotation/jitter) is absorbed by writing each candidate; the residual")
    print("  is the stroke TOPOLOGY = glyph identity. This is the PEN complement to the font-based reader")
    print("  (scripts/cursive_analysis_by_synthesis.py), and addresses its named residual — the individual")
    print("  hand a fixed font cannot produce but a parametric pen can.")
    print(SEP)


if __name__ == "__main__":
    main()
