"""BigvilleInteg5World -- bigville R10e (block 276000): SCALE TO 50.

The ONLY change from R10d (BigvilleInteg4World) is the cast size and the register: a
50-resident town (the 30-register plus 20 ordinary townsfolk drawn from the SAME
generative model at archetype offset 0 -- grand-mean residents + individual noise;
population = distribution over seeds). Every mechanic -- the shopping loop, the social
rungs, conservation, the perf batching -- is inherited UNCHANGED. This rung exists to
MEASURE two things at a population where dynamics are genuine rather than anecdotal:

  1. GENUINE DYNAMICS: does cast=50 exhibit qualitatively different / richer macro
     behaviour than cast=16 (cascades, coalition structure, the mobilisable minority
     being MORE than one person -- the 3.5% quorum stops rounding to 1)?
  2. COST vs HEADCOUNT: the SCALE x TIMING frontier -- ms/tick vs population, post the
     phase-batching that made per-tick cost scale with the GRAPH not the POPULATION.

A WORLD ADAPTER: it changes a cast parameter and a register (world setup), no agent
decision. NO new Rust; own engine.
"""
from __future__ import annotations

import json
import os

from worlds.bigville_integ4_world import BigvilleInteg4World

_REGISTER_50 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "seeds", "bigville_townspeople_50.json")


class BigvilleInteg5World(BigvilleInteg4World):
    def __init__(self, *, cast=50, seed=276000, **kw):
        super().__init__(cast=cast, seed=seed, **kw)

    def _load_register(self):
        """Read the 50-resident register (integ2's `_load_register` reads a MODULE-level
        global, so a class-attr override would be ignored -- override the method)."""
        try:
            return json.load(open(_REGISTER_50)).get("inhabitants", [])
        except Exception:
            return super()._load_register()
