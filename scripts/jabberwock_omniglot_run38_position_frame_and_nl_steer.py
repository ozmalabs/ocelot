"""RUN 38 — the position-preserving contrastive frame, and the NL front-door that authors it.

Two results, one script, both reproducible on the Latin one-shot + a booted agent.

A) THE POSITION-PRESERVING FRAME (host realization of the authored shape).
   The held-open contrastive verdict (`domains/contrastive_verdict.contrastive_pick`, the
   jabberwock's own run-37 gap-A authoring) re-judges the top-2 on WHERE they differ. Its
   committed frame recenters each glyph on its own ink CENTROID, so it fixes SHAPE-difference
   pairs (A/O closure, G/Q terminal) but is blind to POSITION-difference pairs (F/L: same
   crossbar stroke, different height). `_normalize_glyph_shared` is the position-preserving
   twin — a shared bbox frame feeding the SAME held `MinOver(PointSetDist)` Term (no new Rust).
   It fixes F/L (the pair the centroid frame cannot) at the cost of A/O — because WHICH
   property separates a pair is PAIR-RELATIVE. The parameter-free robust combiner is
   frame-AGREEMENT (override the global pick only when both frames independently agree).

   Gate (contrastive fires only when the global top-2 are within `--gap`, i.e. the collapse
   is genuinely open): SC+TPS 75.2% -> frame-agreement 77.2% on the 26-way Latin one-shot.

B) THE NATURAL-LANGUAGE FRONT DOOR (`conversation_action._act_author_concern`).
   A plain English steer through `converse()` — "compare where the two letters differ and
   judge the trial on that region" — parses as an instruction and reaches the agent's OWN
   `induce_concern`/`ground_concern` loop, teacher-free (donkey=0). It grounds through the
   SAME `judge` composer head that authored contrastive_verdict's gap-A concern: the run-37
   provenance, re-derived live from language.

Run:
  OMNIGLOT_DIR=data/omniglot PYTHONPATH=. python \
    scripts/jabberwock_omniglot_run38_position_frame_and_nl_steer.py [--gap 0.03] [--skip-eval]
"""
import argparse
import glob
import os

import numpy as np

os.environ.setdefault("OMNIGLOT_DIR", "data/omniglot")

L = lambda nn: chr(64 + int(nn))
PAIRS = [("06", "12"), ("01", "15"), ("20", "12"), ("07", "17"), ("06", "16"), ("24", "11")]


def _eval(gap: float, n_points: int = 48):
    from substrate_rs import _native
    from domains import omniglot_world as ow, contrastive_verdict as cv
    from collections import Counter
    native = _native.Substrate()

    def ptset(ss):
        P = np.vstack(ss)
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        if d[-1] < 1e-9:
            return None
        u = np.linspace(0, d[-1], n_points)
        R = np.c_[np.interp(u, d, P[:, 0]), np.interp(u, d, P[:, 1])]
        R = R - R.mean(0)
        return R / (np.abs(R).max() + 1e-9)

    def sctps(a, b):
        return float(native.evaluate({"type": "Plus", "items": [
            {"type": "ShapeContextDist", "a": {"type": "Lit", "value": a.tolist()},
             "b": {"type": "Lit", "value": b.tolist()}},
            {"type": "TpsDeformDist", "a": {"type": "Lit", "value": a.tolist()},
             "b": {"type": "Lit", "value": b.tolist()}}]}, {}) or 0)

    glyphs = {}
    for cdir in sorted(glob.glob(f"{os.environ['OMNIGLOT_DIR']}/strokes_background/Latin/character*")):
        ch = cdir.split("character")[-1]
        for f in glob.glob(f"{cdir}/*.txt"):
            d = os.path.basename(f).split("_")[1].split(".")[0]
            try:
                ss, _ = ow.load_strokes_t(f)
            except Exception:
                continue
            ss = [s[:, :2].astype(float) for s in ss if s.shape[0] >= 8]
            if not ss:
                continue
            R = ptset(ss)
            if R is not None:
                glyphs.setdefault(d, {})[ch] = (R, ss)

    sup = max(glyphs, key=lambda d: len(glyphs[d]))
    sc = list(glyphs[sup]); sR = np.array([glyphs[sup][c][0] for c in sc])
    sStr = [glyphs[sup][c][1] for c in sc]
    Q = [(d, c) for d in glyphs if d != sup for c in glyphs[d] if c in sc]

    rows = []
    for d, c in Q:
        R, qstr = glyphs[d][c]; ti = sc.index(c)
        D = np.array([sctps(R, sR[j]) for j in range(len(sc))]); order = np.argsort(D)
        t1, t2 = int(order[0]), int(order[1]); g = float(D[t2] - D[t1])
        wc = cv.contrastive_pick(native, qstr, sStr[t1], sStr[t2], t1, t2)["winner"]
        ws = cv.contrastive_pick(native, qstr, sStr[t1], sStr[t2], t1, t2,
                                 normalize=cv._normalize_glyph_shared)["winner"]
        rows.append((ti, t1, wc, ws, g))

    def score(pick):
        ok = 0; err = Counter()
        for ti, t1, wc, ws, g in rows:
            p = pick(ti, t1, wc, ws, g); ok += p == ti
            if p != ti:
                err[(sc[ti], sc[p])] += 1
        return ok / len(rows), err

    verdicts = {
        "SC+TPS alone":     lambda ti, t1, wc, ws, g: t1,
        "centroid frame":   lambda ti, t1, wc, ws, g: wc if g < gap else t1,
        "shared frame":     lambda ti, t1, wc, ws, g: ws if g < gap else t1,
        "frame-agreement":  lambda ti, t1, wc, ws, g: (wc if wc == ws else t1) if g < gap else t1,
    }
    print(f"\n(A) POSITION-PRESERVING CONTRASTIVE FRAME — Latin one-shot, {len(sc)}-way, "
          f"n={len(rows)}, gate<{gap}\n")
    print(f"    {'verdict':<18}{'acc':>7}   " + "  ".join(f"{L(a)}{L(b)}" for a, b in PAIRS))
    for name, pick in verdicts.items():
        acc, err = score(pick)
        print(f"    {name:<18}{acc:>7.1%}   " + "   ".join(f"{err.get(pr, 0):>2}" for pr in PAIRS))
    print("\n    F/L is fixed only by the shared (position) frame; A/O only by the centroid")
    print("    (shape) frame — the discriminating property is PAIR-RELATIVE. frame-agreement is")
    print("    the parameter-free robust combiner. Per-pair frame-learning on background")
    print("    alphabets is the named next lever (a raw cross-frame magnitude compare is not")
    print("    valid — the frames carry different coordinate scales).")


def _front_door():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import comprehend_text as ct
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    except Exception:
        pass
    steers = [
        "Hold both candidates open when two come out close, and decide where they actually differ.",
        "Compare where the two letters differ and judge the trial on that region.",
    ]
    print("\n(B) NATURAL-LANGUAGE FRONT DOOR — converse() -> the agent's own self-authoring\n")
    for s in steers:
        comp = ct.comprehend_text(a, s)
        reply = a.converse(s)
        print(f"    steer : {s}")
        print(f"    parse : kind={comp.kind} predicate={(comp.dispatch or {}).get('predicate')!r}")
        print(f"    agent : {reply}\n")
    print(f"    teacher-free: donkey (LLM calls) = {donkey['n']}")
    print("    'compare ... judge the trial on that region' grounds through the SAME `judge`")
    print("    composer head that authored contrastive_verdict's run-37 gap-A concern.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=float, default=0.03, help="hold-open gate: contrast only when top-2 within this")
    ap.add_argument("--skip-eval", action="store_true", help="skip the Omniglot eval, run only the NL front-door demo")
    args = ap.parse_args()
    if not args.skip_eval:
        _eval(args.gap)
    _front_door()


if __name__ == "__main__":
    main()
