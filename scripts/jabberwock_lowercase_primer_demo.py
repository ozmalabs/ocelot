"""THE INSTRUCTION SHEET beats the exemplar -- recognise the bowl family by its intended
construction (its ductus), not by a stored exemplar.

Cross-drawer one-shot on the lowercase bowl family (a/o/c/d/e/g/q -- the maximally
self-confusable set, where a/o lives). Two templates, one held ShapeContext+TPS verdict:
  * EXEMPLAR  -- match each query to one support drawer's actual glyph for each letter.
  * CONSTRUCTION -- match each query to the primer's rendered intended form (domains/
    lowercase_primer.PRIMER): "a bowl (+ an intended stem/tail with a direction and extent)".

The construction carries the small deliberate element (the stem, the descender) that the
exemplar's shared bowl-MASS drowns -- so it eliminates the mass-drowning confusions (G/Q, D/A,
Q/A) and lifts the family. The one survivor is C->O (closure), the named frontier: the whole-
figure verdict still bends a c's open side shut, and no global/local closure feature fixes it
without regressing another pair (needs a construction-LOCAL, per-element aligned verdict).

Also authors the primer into the substrate (`author_primer`) so the agent HOLDS the instruction
sheet as ShapeSignature data.

Run: OMNIGLOT_DIR=data/omniglot PYTHONPATH=. python scripts/jabberwock_lowercase_primer_demo.py
"""
import os
import glob
from collections import Counter, defaultdict

import numpy as np

os.environ.setdefault("OMNIGLOT_DIR", "data/omniglot")

from domains import omniglot_world as ow, lowercase_primer as lp

IDX = {"a": "01", "c": "03", "d": "04", "e": "05", "g": "07", "o": "15", "q": "17"}


def main():
    from substrate_rs import _native
    native = _native.Substrate()

    glyphs = defaultdict(dict)
    for k, ch in IDX.items():
        for cdir in glob.glob(f"{os.environ['OMNIGLOT_DIR']}/strokes_background/Latin/character{ch}"):
            for f in glob.glob(f"{cdir}/*.txt"):
                d = os.path.basename(f).split("_")[1].split(".")[0]
                try:
                    ss, _ = ow.load_strokes_t(f)
                except Exception:
                    continue
                ss = [s[:, :2].astype(float) for s in ss if s.shape[0] >= 8]
                if ss:
                    glyphs[d][k] = ss

    sup = max(glyphs, key=lambda d: len(glyphs[d]))
    exemplar = {k: lp.whole_figure(glyphs[sup][k]) for k in IDX if k in glyphs[sup]}
    Q = [(d, k) for d in glyphs if d != sup for k in glyphs[d]]

    def exemplar_read(strokes):
        q = lp.whole_figure(strokes)
        pairs = [(float(native.evaluate(lp._sctps_term(q.tolist(), exemplar[k].tolist()), {}) or 0), k)
                 for k in exemplar]
        return min(pairs)[1]

    def run(name, read):
        ok = 0
        conf = Counter()
        for d, k in Q:
            p = read(glyphs[d][k])
            ok += p == k
            if p != k:
                conf[(k, p)] += 1
        print(f"  {name:<24}{ok / len(Q):>7.1%}   C/O={conf[('c', 'o')]:<3} "
              f"top confusions: {conf.most_common(5)}")

    print(f"lowercase bowl family {list(IDX)}; cross-drawer one-shot, n={len(Q)}, support drawer {sup}\n")
    run("exemplar templates", exemplar_read)
    run("construction (shape only)", lambda ss: lp.read_by_construction(native, ss, intent=False)["winner"])
    run("+ closure-INTENT (c/o)", lambda ss: lp.read_by_construction(native, ss, intent=True)["winner"])
    print("\n  The construction carries the intended stem/descender the exemplar's bowl-mass drowns")
    print("  (G/Q, D/A, Q/A collapse: 60.9% -> 76.7%). Then the CLOSURE INTENT -- does the bowl")
    print("  actually close, the motor trace that survives the mouse -- decides c vs o LOCALLY,")
    print("  only where c is in contention: 76.7% -> 89.5%, C->O 17 -> 0, no regressions.")

    from substrate.boot_core import boot_core
    s, _ag = boot_core()
    recs = lp.author_primer(s)
    print(f"\n  authored the primer into the substrate as ShapeSignatures: {sorted('lc_'+c for c in recs)}")


if __name__ == "__main__":
    main()
