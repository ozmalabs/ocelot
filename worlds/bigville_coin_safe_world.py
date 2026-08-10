"""BigvilleCoinSafeWorld -- bigville R47 (block 351000): COINS ARE PHYSICAL.

Coin is not an abstract balance -- it is physical coin stored in a physical SAFE, and access
is gated by a physical KEY you must HOLD. No key, no access; the coin is secure. Composes with
the Clerk-Treasurer (the treasury's coin lives in a safe the clerk holds the key to) and with
theft (steal the key -> gain access).

A WORLD ADAPTER. No open/withdraw/deposit DECISION in Python -- cs_* are seed rules. The
adapter mints safes/keys/agents, hands out keys, arms access, and reads.
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


class BigvilleCoinSafeWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_coin_safe"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._safes = {}
        self._keys = {}
        self._agents = {}
        self._accessing = {}      # agent -> current safe

    def _run(self):
        for _ in range(3):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_safe(self, name, *, stored_coin=0.0, open=False, keys_required=1):
        """A safe that opens once `keys_required` DISTINCT key-holders authorize it. 1 = ordinary
        single-key safe; 2 = a DUAL-KEY safe (two-person integrity -- neither holder opens it alone)."""
        s = self.eng.add_node("Safe", {"name": name, "stored_coin": float(stored_coin),
                                       "open": 1.0 if open else 0.0, "keys_required": float(keys_required)})
        self.eng.add_edge_unchecked(self._town, "has_safe", s)
        self._safes[name] = s
        return s

    def add_key(self, name, *, opens):
        """A physical key that opens a specific safe."""
        k = self.eng.add_node("Key", {"name": name})
        self.eng.add_edge_unchecked(k, "opens", self._safes[opens])
        self._keys[name] = k
        return k

    def add_agent(self, name, *, coin=0.0):
        a = self.eng.add_node("Agent", {"name": name, "coin": float(coin), "amount": 0.0,
                                        "open_armed": 0.0, "lock_armed": 0.0, "withdraw_armed": 0.0,
                                        "deposit_armed": 0.0, "access_denied": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def give_key(self, agent, key):
        """Hand a key to an agent (their inventory). Ownership is a separate frame (see theft)."""
        self.eng.add_edge_unchecked(self._agents[agent], "holds", self._keys[key])

    def _access(self, agent, safe):
        a = self._agents[agent]
        tgt = self._safes[safe]
        if self._accessing.get(agent) is not tgt:
            if self._accessing.get(agent) is not None:
                self.eng.remove_edge_unchecked(a, "accessing", self._accessing[agent])
            self.eng.add_edge_unchecked(a, "accessing", tgt)
            self._accessing[agent] = tgt
        self.eng.set_attr(a, "access_denied", 0.0)

    def try_open(self, agent, safe):
        self._access(agent, safe)
        self.eng.set_attr(self._agents[agent], "open_armed", 1.0)
        self._run()

    def lock(self, agent, safe):
        """Close the safe and clear the standing authorizations -- reopening requires the
        key-holders to authorize again. Mechanical reset (the OPEN decision is the threshold rule)."""
        s = self._safes[safe]
        for a in list(self.eng.in_neighbours(s, "authorizes")):
            self.eng.remove_edge_unchecked(a, "authorizes", s)
        self.eng.set_attr(s, "open", 0.0)
        self._run()

    def withdraw(self, agent, safe, amount):
        self._access(agent, safe)
        self.eng.set_attr(self._agents[agent], "amount", float(amount))
        self.eng.set_attr(self._agents[agent], "withdraw_armed", 1.0)
        self._run()

    def deposit(self, agent, safe, amount):
        self._access(agent, safe)
        self.eng.set_attr(self._agents[agent], "amount", float(amount))
        self.eng.set_attr(self._agents[agent], "deposit_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def safe_coin(self, safe): return round(float(self.eng.node(self._safes[safe])["attrs"]["stored_coin"]), 4)
    def is_open(self, safe): return float(self.eng.node(self._safes[safe])["attrs"]["open"]) == 1.0
    def coin(self, agent): return round(float(self.eng.node(self._agents[agent])["attrs"]["coin"]), 4)
    def was_denied(self, agent): return float(self.eng.node(self._agents[agent])["attrs"]["access_denied"]) == 1.0
    def authorizers(self, safe): return len(self.eng.in_neighbours(self._safes[safe], "authorizes"))
