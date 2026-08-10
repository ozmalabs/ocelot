"""BigvilleWillWorld -- bigville R54 (block 365000): a will is a note; PEOPLE make it a will.

A note is just writing. It becomes a WILL only because people TREAT it as one -- someone attests
it as the deceased's testamentary wishes and names who is to carry them out (the executor). Until
a person does that, it is inert writing and the estate passes intestate. And even attested, the
estate is not auto-distributed: the executor DECIDES whether to honour it.

A WORLD ADAPTER. No attest-as-decision/honour/withhold logic in Python -- the will-recognition is
a person's act (an admissible world event), and the decide/honour/withhold/intestate are wl_*/cy_*
seed rules. The adapter writes notes, has a person attest one as the will, records deaths, reads.
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


class BigvilleWillWorld:
    def __init__(self, *, funeral_fee=5.0):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_cemetery"), None)     # funeral settles first
        self.eng.load_seed_manifest(manifest_for("bigville_will"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_noticeboard"), None)  # a will is a Note
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._church = self.eng.add_node("Church", {"name": "Church", "funeral_fee": float(funeral_fee),
                                                    "coin": 0.0, "pious_gift_rate": 10.0})
        self.eng.add_edge_unchecked(self._town, "has_church", self._church)
        self._cem = self.eng.add_node("Cemetery", {"name": "the churchyard", "graves": 0.0})
        self.eng.add_edge_unchecked(self._church, "has_cemetery", self._cem)
        for label, sign in (("honour", 1.0), ("withhold", -1.0)):
            self.eng.add_node("HonorStance", {"label": label, "sign": sign})
        for label, sign in (("bequeath", 1.0), ("keep", -1.0)):      # the pious-bequest decision codebook
            self.eng.add_node("PietyStance", {"label": label, "sign": sign})
        self._agents = {}
        self._notes = {}

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_resident(self, name, *, estate=0.0, coin=0.0, alive=1, honesty=0.9, greed=0.1, piety=0.0):
        a = self.eng.add_node("Agent", {"name": name, "estate": float(estate), "coin": float(coin),
                                        "alive": float(alive), "buried": 0.0, "unburied": 0.0,
                                        "honesty": float(honesty), "greed": float(greed),
                                        "piety": float(piety), "will_choice": ""})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def appoint_doctor_undertaker(self, name):
        a = self._agents.get(name) or self.add_resident(name)
        self.eng.add_edge_unchecked(self._town, "has_undertaker", a)
        self.eng.add_edge_unchecked(self._town, "has_doctor", a)
        return a

    def write_note(self, author, content):
        """Write a plain NOTE (held by the author) -- ordinary writing, nothing special.
        It is not a will; only people can make it one (attest_as_will)."""
        n = self.eng.add_node("Note", {"content": content, "author": author, "is_will": 0.0, "withheld": 0.0})
        self.eng.add_edge_unchecked(self._agents[author], "holds", n)
        self._notes[author] = n
        return n

    def bequeath(self, author, to, amount):
        """A wish written into the author's note (`amount` to `to`). Still just writing until attested."""
        b = self.eng.add_node("Bequest", {"amount": float(amount), "paid": 0.0, "paid_amount": 0.0})
        self.eng.add_edge_unchecked(self._notes[author], "bequeaths", b)
        self.eng.add_edge_unchecked(b, "to", self._agents[to])
        return b

    def attest_as_will(self, attester, testator, *, executor):
        """PEOPLE make a note a will: a person attests that `testator`'s note is his last will and
        names the EXECUTOR to carry it out. THIS human act -- not any property of the writing -- is
        what makes the note a will (willed_by / executor edges). A different note attested by a
        different person would be a rival will (contested -- composes with recognition)."""
        n = self._notes[testator]
        self.eng.add_edge_unchecked(n, "willed_by", self._agents[testator])
        self.eng.add_edge_unchecked(n, "executor", self._agents[executor])
        self.eng.add_edge_unchecked(self._agents[attester], "attests_will", n)
        self.eng.set_attr(n, "is_will", 1.0)

    def give_note(self, frm, to, author):
        n = self._notes[author]
        self.eng.remove_edge_unchecked(self._agents[frm], "holds", n)
        self.eng.add_edge_unchecked(self._agents[to], "holds", n)

    def set_next_of_kin(self, testator, heir):
        self.eng.add_edge_unchecked(self._agents[testator], "next_of_kin", self._agents[heir])

    def die(self, name):
        self.eng.set_attr(self._agents[name], "alive", 0.0); self._run()

    # ------------------------------------------------- glass-box read-offs
    def coin(self, name): return round(float(self.eng.node(self._agents[name])["attrs"]["coin"]), 4)
    def estate(self, name): return round(float(self.eng.node(self._agents[name])["attrs"]["estate"]), 4)
    def is_buried(self, name): return float(self.eng.node(self._agents[name])["attrs"]["buried"]) == 1.0
    def executor_choice(self, name): return self.eng.node(self._agents[name])["attrs"].get("will_choice", "")
    def pious_choice(self, name): return self.eng.node(self._agents[name])["attrs"].get("pious_choice", "")
    def church_coin(self): return round(float(self.eng.node(self._church)["attrs"]["coin"]), 4)
