"""BigvillePriceWorld -- production-economy R3 (block 302000): EMERGENT scarcity
prices. A shop's price is not hand-set; it adjusts from local supply/demand
imbalance (the decentralized Gintis/Sugarscape mechanism in posted-price form):
selling OUT (unmet demand) raises it; a GLUT lowers it. Scarce fish -> higher
fish price, automatically.

A WORLD ADAPTER on BigvilleTradeWorld. No pricing decision in Python -- the price
moves via the seed rules reading unmet-demand / glut. The adapter only sets the
adjustment rates and reads the price back.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                   # noqa: E402
from worlds.bigville_trade_world import BigvilleTradeWorld       # noqa: E402


class BigvillePriceWorld(BigvilleTradeWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.eng.load_seed_manifest(manifest_for("bigville_prices"), None)

    def add_shop(self, trade, cell, *, input_kind, output_kind, recipe_in=1.0,
                 recipe_out=1.0, price=3.0, is_open=1, min_price=1.0,
                 price_step=0.5, glut_threshold=8.0):
        shop = super().add_shop(trade, cell, input_kind=input_kind,
                                output_kind=output_kind, recipe_in=recipe_in,
                                recipe_out=recipe_out, price=price, is_open=is_open)
        # emergent-price state + the town link (for the epoch gate).
        self.eng.set_attr(shop, "unmet", 0.0)
        self.eng.set_attr(shop, "min_price", float(min_price))
        self.eng.set_attr(shop, "price_step", float(price_step))
        self.eng.set_attr(shop, "glut_threshold", float(glut_threshold))
        self.eng.set_attr(shop, "price_epoch", 0.0)
        self.eng.add_edge_unchecked(shop, "in_town", self._rtown)
        return shop

    # ------------------------------------------------- glass-box read-offs
    def price(self, trade):
        return float(self.eng.node(self._shops[trade]["nid"])["attrs"]["price"])
