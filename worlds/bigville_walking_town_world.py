"""BigvilleWalkingTownWorld -- the SELF-DRIVING town: the hop clock (283000) meets
the graph-native surprise gate (284000). Residents WALK (one hop per master tick);
proximity EMERGES from positions (no hand-fed co-presence); the surprise gate fires
on the unpredicted; and only surprised residents run their Bond-directed supergraph
conduct collapse (282000). Block 285000 -- the whole loop, self-driving.

Per master tick (mechanical adapter I/O only):
  * advance each walker ONE hop toward its goal (no teleport);
  * derive co-presence from positions (within range) -> `sees` edges;
  * run the surprise gate + directed provision (rules) -> `m.surprised`;
  * dispatch ONLY surprised residents to the conduct collapse (a mechanical routing
    on the rule-computed flag); enact + record.
Everything decided is a rule (surprise, provision, the collapse); the adapter moves
bodies, mints observation, and reads results.
"""
from __future__ import annotations

from worlds.bigville_surprise_town_world import BigvilleSurpriseTownWorld


def _step_toward(pos, goal):
    x, y = pos
    gx, gy = goal
    if x != gx:
        return (x + (1 if gx > x else -1), y)
    if y != gy:
        return (x, y + (1 if gy > y else -1))
    return (x, y)


class BigvilleWalkingTownWorld(BigvilleSurpriseTownWorld):
    """residents: [dict(name, pos=(x,y), goal=(x,y), predicts=[...], w_supergraph=,
    conduct_k=)]. bonds as in the surprise town. Proximity range `range_r`."""

    def __init__(self, residents, bonds=None, *, range_r=1):
        super().__init__(residents, bonds)
        self.range_r = range_r
        self.pos = {r["name"]: tuple(r["pos"]) for r in residents}
        self.goal = {r["name"]: tuple(r.get("goal", r["pos"])) for r in residents}
        self.pos_log = []
        self.max_hop = 0

    def _copresence(self):
        cop = {n: [] for n in self.names}
        for i, a in enumerate(self.names):
            for b in self.names[i + 1:]:
                pa, pb = self.pos[a], self.pos[b]
                if abs(pa[0] - pb[0]) + abs(pa[1] - pb[1]) <= self.range_r:
                    cop[a].append(b); cop[b].append(a)
        return cop

    def step(self):
        """One master tick: advance hops, derive co-presence, run the surprise-gated
        conduct loop. Returns the per-resident outcomes (surprised/chosen/target)."""
        for n in self.names:                       # (1) advance one hop -- no teleport
            if self.pos[n] != self.goal[n]:
                nxt = _step_toward(self.pos[n], self.goal[n])
                self.max_hop = max(self.max_hop,
                                   abs(nxt[0] - self.pos[n][0]) + abs(nxt[1] - self.pos[n][1]))
                self.pos[n] = nxt
        self.pos_log.append((self.tick_no + 1, dict(self.pos)))
        return self.tick(self._copresence())       # (2-4) sees -> surprise -> collapse

    def run(self, n_ticks):
        return [self.step() for _ in range(n_ticks)]

    def health(self, nm):
        return float(self.s.node(self._person[nm])["attrs"]["health"])
