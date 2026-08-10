"""BigvilleRecognitionWorld -- bigville R33 (block 324000): authority is recognition,
not a fact; the usurper is possible.

A body dying is a world-fact the engine enforces (any agent can strike). A ROLE /
AUTHORITY is a human-frame: "X rules" is true for Y iff Y recognizes X. The usurper
can murder the mayor and claim rule -- the substrate does not forbid it; what its
decree reaches is exactly the agents who recognize it, and nothing else.

A WORLD ADAPTER. No strike/recognize/authority/tribute DECISION in Python -- rc_*
are seed rules; recognition is an Argmax collapse in the seed. The adapter only
stages the world events (a strike, a claim, a decree) and reads.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402

_CHOICES = [("recognize", 1.0), ("reject", -1.0)]


class BigvilleRecognitionWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_recognition"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        for label, sign in _CHOICES:
            self.eng.add_node("RecogChoice", {"label": label, "recog_sign": sign})
        self._people = {}
        self._claim = None

    def _settle(self):
        for _ in range(5):
            self.eng.force_all_dirty()
            self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_person(self, name, *, coin=20.0, fear_weight=0.5, opportunism=0.3,
                   loyalty_prior=0.5, role="", alive=1):
        p = self.eng.add_node("Person", {"name": name, "coin": float(coin),
                                         "fear_weight": float(fear_weight),
                                         "opportunism": float(opportunism),
                                         "loyalty_prior": float(loyalty_prior),
                                         "role": role, "alive": float(alive),
                                         "shown_force": 0.0, "strike_armed": 0.0,
                                         "recog_choice": ""})
        self.eng.add_edge_unchecked(self._town, "has_resident", p)
        self._people[name] = p
        return p

    def murder(self, striker, target):
        """A world event: one agent strikes another dead. The engine does not forbid it."""
        self.eng.add_edge_unchecked(self._people[striker], "strikes", self._people[target])
        self.eng.set_attr(self._people[striker], "strike_armed", 1.0)
        self._settle()

    def claim_rule(self, claimant):
        """The claimant declares themselves ruler. Minting a claim is not forbidden; each
        agent then collapses on whether to recognize it."""
        self._claim = self.eng.add_node("Claim", {"role": "ruler", "authority": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_claim", self._claim)
        self.eng.add_edge_unchecked(self._claim, "by", self._people[claimant])
        self._settle()
        return self._claim

    def decree_tribute(self, amount):
        """A decree under the claim. It takes tribute only from those who recognize it."""
        dec = self.eng.add_node("Decree", {"amount": float(amount)})
        self.eng.add_edge_unchecked(self._town, "has_decree", dec)
        self.eng.add_edge_unchecked(dec, "under_claim", self._claim)
        self._settle()
        return dec

    # ------------------------------------------------- glass-box read-offs
    def is_alive(self, name):
        return float(self.eng.node(self._people[name])["attrs"].get("alive", 0.0)) == 1.0

    def authority(self):
        return int(self.eng.node(self._claim)["attrs"].get("authority", 0.0))

    def recognizers(self):
        return sorted(n for n, p in self._people.items()
                      if self._claim in self.eng.neighbours(p, "recognizes"))

    def coin_of(self, name):
        return float(self.eng.node(self._people[name])["attrs"]["coin"])

    def tributaries(self):
        dec = None
        for d in self.eng.neighbours(self._town, "has_decree"):
            dec = d
        if dec is None:
            return []
        return sorted(n for n, p in self._people.items()
                      if dec in self.eng.neighbours(p, "tributed"))
