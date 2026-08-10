"""BigvilleEconScaleWorld -- the R4 (block 252000) SCALE instrument, economy ON.

Re-runs the 248000 scale probe with movement+ECONOMY on. It SUBCLASSES the proven
248000 counting instrument ``BigvilleScaleWorld`` (imported UNCHANGED) to reuse its
constant-density torus placement, and adds the realized EXCHANGE-op census -- the
economy analogue of 248's realized perception-op census. Two arms:

  * ``local``     (HEADLINE) -- LOCAL exchange: a buyer transacts only with a shop
                    AT / adjacent to its cell (the co-location join `be_exchange`
                    enforces). Constant shop+buyer density => realized exchange-ops
                    = N*k (LINEAR).
  * ``all_pairs`` (CONTROL / falsifier) -- a GLOBAL market clear: every buyer
                    compared against every shop = N_buyer * N_shop (QUADRATIC).
                    This is exactly what an accidental global price-solve would
                    produce -- the falsifier the local arm must sit CI-separated
                    below.

Pure counting; NO agent decisions (the exchange DECISION is the seed rule
`be_exchange`; here we only COUNT the interaction-ops it would realize, exactly as
248 counts perception pairs). Shops are placed at a constant density on the SAME
torus so the co-location neighbourhood never tiles the whole village -- the
N-scaling of the exchange interaction is isolated.
"""
from __future__ import annotations

import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from worlds.bigville_scale_world import BigvilleScaleWorld     # noqa: E402

SHOP_DENSITY = 0.5          # a shop for every ~two inhabitants (constant fraction of N)
EXCH_RANGE = 1              # Chebyshev radius for LOCAL co-located exchange


class BigvilleEconScaleWorld(BigvilleScaleWorld):
    """N inhabitants (all potential buyers) + ~SHOP_DENSITY*N shops on the 248
    constant-density torus. Counts realized EXCHANGE-ops per the arm.

    Shops are hosted at a constant fraction of INHABITANT cells (the market forms
    where people are), so a shop's host inhabitant is trivially co-located with it
    -- a guaranteed O(N) LOCAL signal (>= n_shops), constant per-capita, plus any
    additional buyers who happen within EXCH_RANGE. Constant density => LINEAR."""

    def __init__(self, n, arm="local", place_seed=252000, **kw):
        assert arm in ("local", "all_pairs")
        # reuse the 248 torus geometry; do NOT run the drama (this is a counting
        # instrument for the EXCHANGE interaction, like 248 for perception).
        super().__init__(n, arm="sparse", place_seed=place_seed, run_drama=False, **kw)
        self.econ_arm = arm
        # a constant fraction of inhabitants host a shop at their own cell (the
        # market forms where people cluster). n_shops scales with N -> constant
        # per-capita, and each shop is co-located with its host buyer.
        n_shops = max(1, int(round(SHOP_DENSITY * self.n)))
        self.shop_pos = [self.pos[i] for i in range(n_shops)]
        self.n_shops = len(self.shop_pos)
        self.econ_ops_log = []

    def econ_census(self):
        """Realized exchange-ops for this placement. ``local`` counts co-located
        buyer x shop pairs (a spatial bucket keeps the candidate set local, so the
        COUNT itself is not an accidental all-pairs sweep); ``all_pairs`` is the
        deliberate global market-clear N_buyer x N_shop."""
        if self.econ_arm == "all_pairs":
            return self.n * self.n_shops
        L = self.L
        R = EXCH_RANGE
        shop_buckets = {}
        for s in self.shop_pos:
            shop_buckets.setdefault(s, []).append(s)
        ops = 0
        for (bx, by) in self.pos:                 # every inhabitant is a buyer
            for ddx in range(-R, R + 1):
                for ddy in range(-R, R + 1):
                    cell = ((bx + ddx) % L, (by + ddy) % L)
                    ops += len(shop_buckets.get(cell, ()))
        return ops

    def run(self, T=12):
        for _ in range(T):
            self.econ_ops_log.append(self.econ_census())
        return self.econ_ops_log

    def mean_econ_ops(self):
        return float(np.mean(self.econ_ops_log)) if self.econ_ops_log else 0.0
