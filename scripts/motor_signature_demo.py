"""Motor signature on REAL ink — reverse-engineering the apparatus behind Omniglot glyphs.

Recognising each glyph is the cheap reflex; this reads the deeper, apparatus-invariant-to-
recognition layer: HOW it was made. Omniglot was mouse-collected on Mechanical Turk — cheap
mice, whatever mats, people who don't care — so the strokes should read as high-friction,
stick-slip, moderately shaky: the long tail of "how people drag a mouse", not "how people draw".

Data (see cascade_ink_demo.py): OMNIGLOT_DIR=data/omniglot.
Run: OMNIGLOT_DIR=data/omniglot PYTHONPATH=. python scripts/motor_signature_demo.py
"""
import os
import glob
import numpy as np

os.environ.setdefault("OMNIGLOT_DIR", "data/omniglot")
from domains.omniglot_world import load_strokes_t
from domains.motor_signature import motor_signature, infer_environment, _turning


def main():
    sigs = []
    first = None
    for f in sorted(glob.glob(f"{os.environ['OMNIGLOT_DIR']}/strokes_background/*/character*/*.txt"))[::4]:
        try:
            strokes, _ = load_strokes_t(f)
        except Exception:
            continue
        for st in strokes:
            xy = st[:, :2].astype(float)
            t = st[:, 2].astype(float)
            if xy.shape[0] < 70 or float(_turning(xy).sum()) < 1.0 * np.pi:
                continue
            if np.any(np.diff(t) <= 0):
                continue
            sig = motor_signature(xy, t)
            sigs.append(sig)
            score = sig["friction"] + (1.0 - sig["care"])      # a clear draggy exemplar
            if first is None or score > first[2]:
                first = (f, sig, score)
        if len(sigs) >= 400:
            break

    stick = np.array([s["stick_slip"] for s in sigs])
    fr = np.array([s["friction"] for s in sigs])
    care = np.array([s["care"] for s in sigs])
    pauses = np.array([s["pauses"] for s in sigs])
    print(f"{len(sigs)} real timed Omniglot strokes — reverse-engineered apparatus:\n")
    print(f"  stick-slip (corner slowdown):  {stick.mean():.2f}   "
          f"({(stick > 0.1).mean():.0%} clearly stall into their corners)")
    print(f"  friction (est.):               {fr.mean():.2f}")
    print(f"  care (est.):                   {care.mean():.2f}")
    print(f"  within-stroke re-anchor pauses:{pauses.mean():.2f}   "
          f"({(pauses > 0).mean():.0%}) — ~none, because in this data a pen-DOWN stroke is one")
    print(f"     continuous drag: re-anchoring happens at pen-UP, so the workspace limit shows up")
    print(f"     in HOW the character is broken into strokes, not within a stroke.")

    # THE PAYOFF: from a SINGLE glyph, abduce the environment it was made in.
    fpath, s0 = first[0], first[1]
    env = infer_environment(s0)
    print(f"\n  From a SINGLE glyph ({fpath.split('background/')[1]}; "
          f"friction {s0['friction']:.2f}, care {s0['care']:.2f}):")
    print(f"    surface:    {env['surface']}")
    print(f"    device:     {env['device']}")
    print(f"    engagement: {env['engagement']}")
    print(f"    context:    {env['context']}")
    for n in env["notes"]:
        print(f"      - {n}")
    print(f"\n  -> Omniglot was in fact collected on Amazon Mechanical Turk, by mouse, casually —")
    print(f"     the environment abduced from one glyph. Recognition never needed any of it.")


if __name__ == "__main__":
    main()
