"""Pilot (seeds 0-4): locate the give-fold and check D-independence.
Disclosed pilot -- sets the prereg interval. NOT the confirmatory run."""
import json
import sys
import os

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.seizure_engine_lattice import Arch, run_one, classify, persists  # noqa


def fold_for_seed(arch, seed, D=3.0, alpha=0.5,
                  grid=(0.7, 0.6, 0.55, 0.5, 0.45, 0.4, 0.3)):
    """Finest give at which it still DIES, and coarsest at which it PERSISTS."""
    last_die, first_persist = None, None
    for gv in grid:
        r = run_one(arch, D=D, give=gv, alpha=alpha, seed=seed)
        p = persists(r, arch)
        if p and first_persist is None:
            first_persist = gv
        if not p:
            last_die = gv
    # fold ~ midpoint between the coarsest-persist and the die just above it
    return last_die, first_persist


def main():
    arch = Arch()
    print("=== give-fold across seeds (alpha=0.5, D=3) ===")
    folds = []
    for seed in range(5):
        die, persist = fold_for_seed(arch, seed)
        mid = None if persist is None or die is None else (die + persist) / 2
        folds.append(mid)
        print(f"seed {seed}: last_die give={die} first_persist give={persist} fold~{mid}")
    fv = [f for f in folds if f is not None]
    if fv:
        print(f"fold median={np.median(fv):.3f} range=[{min(fv):.3f},{max(fv):.3f}]")

    print("\n=== P2: give=1.0 never seizes across drive D (alpha=0.5, seed 0) ===")
    for D in (1, 3, 6, 12, 30, 60):
        r = run_one(arch, D=float(D), give=1.0, alpha=0.5, seed=0)
        print(f"D={D:3d}: persists={persists(r, arch)} final_active={r['n_active'][-60:].mean():.1f}")

    print("\n=== P6: fold vs drive D (does the fold move with D?) ===")
    for D in (2, 4, 8, 16):
        die, persist = fold_for_seed(arch, 0, D=float(D))
        mid = None if persist is None or die is None else (die + persist) / 2
        print(f"D={D:2d}: fold~{mid} (last_die={die} first_persist={persist})")

    print("\n=== good null: alpha=0 never seizes at any give (seed 0, D=3) ===")
    for gv in (1.0, 0.5, 0.2, 0.0):
        r = run_one(arch, D=3.0, give=gv, alpha=0.0, seed=0)
        print(f"give={gv}: persists={persists(r, arch)} peak_active={r['n_active'].max()}")


if __name__ == "__main__":
    main()
