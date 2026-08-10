"""Does factoring out the shared per-session deformation raise one-shot accuracy? — REAL ink.

Real Omniglot cross-drawer one-shot (within one alphabet): a "drawer" is a person (one file
suffix `_NN` per person, the same person across every character) — one session, one apparatus,
one shared deformation. Support = one drawer's glyphs (one per character); query = another
drawer's; classify by a simple resample-and-normalise shape distance.

Two conditions, the honest full picture:
  * NO injected apparatus difference — real Omniglot drawers already share aspect (same
    alphabet, similar AMT equipment), so there is no per-session nuisance to remove and no lift.
    Synthetic-mechanism != benchmark-value, reported.
  * WITH a per-drawer apparatus deformation (simulating different mice/surfaces per person —
    the cross-device case the motor story is about): the nuisance costs real one-shot accuracy,
    and establishing each drawer's shared deformation (establish_deformation) + canonicalising
    every glyph recovers almost all of it. The shared latent is solved ONCE per session.

Data: OMNIGLOT_DIR=data/omniglot (see cascade_ink_demo.py).
Run: OMNIGLOT_DIR=data/omniglot PYTHONPATH=. python scripts/motor_deformation_oneshot_demo.py
"""
import os
import glob
import numpy as np

os.environ.setdefault("OMNIGLOT_DIR", "data/omniglot")
from domains.omniglot_world import load_strokes_t
from domains.motor_signature import establish_deformation, canonicalize

ALPHABET = "Latin"


def _load():
    """glyphs[drawer][char] = a single-stroke pen path (clean matching)."""
    glyphs = {}
    for cdir in sorted(glob.glob(f"{os.environ['OMNIGLOT_DIR']}/strokes_background/{ALPHABET}/character*")):
        ch = os.path.basename(cdir)
        for f in glob.glob(f"{cdir}/*.txt"):
            drawer = os.path.basename(f).split("_")[1].split(".")[0]
            try:
                ss, _ = load_strokes_t(f)
            except Exception:
                continue
            ss = [s for s in ss if s.shape[0] >= 30]
            if len(ss) != 1:                                  # single-stroke only
                continue
            glyphs.setdefault(drawer, {})[ch] = ss[0][:, :2].astype(float)
    return glyphs


def _norm(p, N=48):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    u = np.linspace(0, d[-1], N)
    q = np.c_[np.interp(u, d, p[:, 0]), np.interp(u, d, p[:, 1])]
    q = q - q.mean(0)
    return q / (np.sqrt((q ** 2).sum(1).mean()) + 1e-9)


def _rot(a):
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


def _run(glyphs, drawers, apparatus):
    # optionally apply a distinct per-drawer apparatus deformation to all of that drawer's glyphs
    gly = {}
    for i, d in enumerate(drawers):
        g = np.random.default_rng(i)
        if apparatus:
            A = g.uniform(0.3, 0.6)
            th = g.uniform(0, np.pi)
            M = _rot(th) @ np.diag([1 + A, 1 - A]) @ _rot(-th)
        else:
            M = np.eye(2)
        gly[d] = {c: (glyphs[d][c] - glyphs[d][c].mean(0)) @ M.T + glyphs[d][c].mean(0)
                  for c in glyphs[d]}
    defm = {d: establish_deformation(list(gly[d].values())) for d in drawers}

    raw = can = tot = 0
    for A in drawers:
        for B in drawers:
            if A == B:
                continue
            common = [c for c in gly[A] if c in gly[B]]
            if len(common) < 10:
                continue
            sr = {c: _norm(gly[A][c]) for c in common}
            sc = {c: _norm(canonicalize(gly[A][c], defm[A])) for c in common}
            for c in common:
                qr, qc = _norm(gly[B][c]), _norm(canonicalize(gly[B][c], defm[B]))
                tot += 1
                raw += min(common, key=lambda k: np.linalg.norm(qr - sr[k])) == c
                can += min(common, key=lambda k: np.linalg.norm(qc - sc[k])) == c
    return raw / tot, can / tot, tot


def main():
    glyphs = _load()
    drawers = [d for d in glyphs if len(glyphs[d]) >= 10]
    anis = np.array([establish_deformation(list(glyphs[d].values()))["anisotropy"] for d in drawers])
    r0, c0, tot = _run(glyphs, drawers, apparatus=False)
    r1, c1, _ = _run(glyphs, drawers, apparatus=True)

    print(f"{ALPHABET}: {len(drawers)} drawers, {tot} cross-drawer one-shot trials (simple matcher)\n")
    print(f"  per-drawer shared anisotropy: mean {anis.mean():.2f}, spread {anis.std():.2f} "
          f"— mostly the shared alphabet aspect, so it barely differs between drawers.\n")
    print(f"  NO apparatus difference:   raw {r0:.1%}   canon {c0:.1%}   ({(c0 - r0) * 100:+.1f} pts) "
          f"— nothing to remove.")
    print(f"  + per-drawer apparatus:    raw {r1:.1%}   canon {c1:.1%}   ({(c1 - r1) * 100:+.1f} pts) "
          f"— recovers {(c1 - r1) * 100:.0f} of the {(r0 - r1) * 100:.0f} pts the nuisance cost.")
    print(f"\n  -> factoring out the shared per-session deformation raises accuracy WHEN there is a")
    print(f"     per-session latent to remove (cross-device / different-mouse) — solved once per")
    print(f"     session, not per glyph. On a single-collection alphabet the drawers share kit, so")
    print(f"     there is little to gain; the mechanism pays off across apparatus, as measured.")


if __name__ == "__main__":
    main()
