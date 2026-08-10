"""BigvilleDurativeTownWorld -- the MASTER TICK IS FAST; decisions fire on
SURPRISE, not on a clock and not on an enumerated event list (block 283000).

The global clock is a lie. The coarse town tick made a whole walk happen "in one
tick" -> residents teleported (the play world's hop-by-hop movement was only a viz
hack over a coarse decision-tick). Here the HOP is the master tick: one fast tick
advances each walker ONE step, and it is CHEAP because almost nothing decides on
most ticks.

The trigger for a decision is SURPRISE -- observation != the resident's held
prediction -- the SAME held-prediction residual perception runs on (held surface =
prediction; new frame = order-0 residual). NOT an enumerated "settlement event"
list: an ARRIVAL you predicted needs no re-decision; an ENCOUNTER with someone you
were walking to MEET is unsurprising and fires nothing; a rival appearing UNBIDDEN
on your route is high surprise -> the collapse fires. It is residual all the way:
surprise gates WHETHER to decide; the decision core's own residual (282000-a) gates
HOW DEEP. Between surprises, a resident just CONTINUES its durative action (walk,
converse) -- the habitual fast path, no decision.

REAL here: the fast hop clock, hop movement, the held social prediction + surprise
(prediction residual), decision sparsity (O(surprise), not O(residents x ticks)),
no teleport, and a conversation that unfolds ALONG a shared route. SCAFFOLD (fires
AT the surprise points, gated + built elsewhere): the utterance CONTENT is the
speech faculty (278000); the conduct CHOICE is the supergraph collapse (282000).
The adapter is mechanical -- advance, observe, compare-to-prediction, record.
"""
from __future__ import annotations


def _step_toward(pos, goal):
    """One Manhattan hop from pos toward goal (x first, then y). No teleport."""
    x, y = pos
    gx, gy = goal
    if x != gx:
        return (x + (1 if gx > x else -1), y)
    if y != gy:
        return (x, y + (1 if gy > y else -1))
    return (x, y)


def _adjacent(a, b, r=1):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) <= r


# an adjacency-pair scaffold: once a conversation is open it CONTINUES as a durative
# action (habitual, no per-turn decision). Content is the speech faculty's job.
_TURNS = ["greeting", "greeting_back", "share", "ack", "share", "ack"]


class BigvilleDurativeTownWorld:
    """Residents with durative walk actions on a grid; decisions fire on SURPRISE.

    residents: list of dict(name, pos=(x,y), goal=(x,y), expect=[names]).
      `expect` = who this resident PREDICTS it will meet (its held social
      prediction). Meeting someone in `expect` is UNSURPRISING -> no decision;
      meeting someone NOT in `expect` is surprise -> a decision.
    """

    def __init__(self, residents, *, range_r=1):
        self.range_r = range_r
        self.pos = {r["name"]: tuple(r["pos"]) for r in residents}
        self.goal = {r["name"]: tuple(r.get("goal", r["pos"])) for r in residents}
        self.names = [r["name"] for r in residents]
        self.action = {n: ("walk" if self.pos[n] != self.goal[n] else "idle")
                       for n in self.names}
        # the HELD SOCIAL PREDICTION: who each resident currently expects near it.
        self.expect = {r["name"]: set(r.get("expect", [])) for r in residents}
        self._near = {n: set() for n in self.names}   # who is actually near now
        self._conv = {}                    # frozenset{a,b} -> turn index (durative)
        self.tick_no = 0
        self.pos_log = []
        self.decisions = []                # SURPRISE events (the sparse decisions)
        self.utterances = []               # [(tick, speaker, partner, act, moving)]
        self.max_hop = 0

    # ---------------------------------------------------------------- one fast tick
    def fast_tick(self):
        self.tick_no += 1
        # (1) ADVANCE durative actions one hop (mechanical; no teleport).
        for n in self.names:
            if self.action[n] == "walk" and self.pos[n] != self.goal[n]:
                nxt = _step_toward(self.pos[n], self.goal[n])
                self.max_hop = max(self.max_hop,
                                   abs(nxt[0] - self.pos[n][0]) + abs(nxt[1] - self.pos[n][1]))
                self.pos[n] = nxt
                if self.pos[n] == self.goal[n]:
                    self.action[n] = "idle"
        self.pos_log.append((self.tick_no, dict(self.pos)))

        # (2) OBSERVE the social scene, per resident.
        near = {n: set() for n in self.names}
        for i, a in enumerate(self.names):
            for b in self.names[i + 1:]:
                if _adjacent(self.pos[a], self.pos[b], self.range_r):
                    near[a].add(b); near[b].add(a)

        # (2b) A conversation opens on any new ENCOUNTER (predicted OR not) -- it is
        # a DURATIVE action, not a decision. Meeting a friend you set out to meet
        # still leads to a (habitual) chat; it just isn't a surprise.
        for i, a in enumerate(self.names):
            for b in self.names[i + 1:]:
                pair = frozenset((a, b))
                if b in near[a] and b not in self._near[a]:
                    self._conv.setdefault(pair, 0)

        # (3) SURPRISE = observation != held prediction. Only the SURPRISED decide
        # (this is where the 282000 conduct collapse would fire). A PREDICTED
        # meeting fires NOTHING here; an UNPREDICTED other (or an expected one
        # vanishing) is the residual that buys a decision.
        for n in self.names:
            surprise = near[n] - self.expect[n]        # someone UNPREDICTED nearby
            vanished = (self._near[n] - near[n]) & self.expect[n]  # expected, now gone
            if surprise or vanished:
                self.decisions.append({"tick": self.tick_no, "who": n,
                                       "surprise": sorted(surprise),
                                       "vanished": sorted(vanished)})
                self.expect[n] = set(near[n])          # prediction updates to match
            self._near[n] = near[n]

        # (4) open conversations CONTINUE as durative actions (habitual, NO decision
        # per turn) -- one utterance per tick until exhausted or out of range.
        for pair, ti in list(self._conv.items()):
            a, b = tuple(pair)
            if not _adjacent(self.pos[a], self.pos[b], self.range_r):
                self._conv.pop(pair, None); continue
            if ti >= len(_TURNS):
                continue
            speaker = a if ti % 2 == 0 else b
            partner = b if speaker == a else a
            moving = self.action[speaker] == "walk"
            self.utterances.append((self.tick_no, speaker, partner, _TURNS[ti], moving))
            self._conv[pair] = ti + 1

    def run(self, n_ticks):
        for _ in range(n_ticks):
            self.fast_tick()

    # ------------------------------------------------------------------- read-off
    def decision_count(self):
        return len(self.decisions)

    def utterances_while_moving(self):
        """Utterances spoken by a resident still WALKING -- proof a conversation
        unfolded ALONG a route, not at a standstill."""
        return [u for u in self.utterances if u[4]]

    def conversation_between(self, a, b):
        return [u for u in self.utterances if {u[1], u[2]} == {a, b}]
