"""BigvilleLivingTownWorld -- the FULL FOLD-IN (block 289000): the 280-287 conduct
spine wired into the LIVE integ5/play town. The town keeps all its own mechanics
(produce / buy / trade / paper / council / life-death / routing); this adds
INTERPERSONAL CONDUCT -- residents help / give / greet / (rarely) harm each other,
driven by held Bonds, on the SURPRISE clock.

Architecture (the project's own split): the TOWN is the WORLD (it moves bodies and
provides observations = who is co-present, from real positions); a CONDUCT LAYER --
a BigvilleSurpriseTownWorld mirroring the residents as ConductState minds with held
Bonds -- is the AGENT GRAPH. Each town tick: read co-presence from the town's real
positions, drive the surprise-gated Bond-directed conduct collapse, and write the
resulting conduct back into the town's event feed (so the paper, narration, and the
player all surface it). ADDITIVE: the town's substrate + mechanics are untouched;
the conduct layer is a parallel agent graph, exactly like a world adapter feeding a
mind. NO agent decision in Python: provision, surprise, and the choice are seed
rules; this adapter reads positions and records outcomes.
"""
from __future__ import annotations

from worlds.bigville_play_world import BigvillePlayWorld
from worlds.bigville_surprise_town_world import BigvilleSurpriseTownWorld

_RANGE = 2                      # co-presence radius on the town grid
_VERB = {"harm": "strikes", "help": "helps", "transfer": "shares with"}
_KIND = {"harm": "violence", "help": "kindness", "transfer": "gift"}


class BigvilleLivingTownWorld(BigvillePlayWorld):
    def __init__(self, *, cast=12, seed=276000, conduct=True, **kw):
        super().__init__(cast=cast, seed=seed, **kw)
        self.conduct_enabled = bool(conduct)
        self.conduct_events = []           # conduct-only feed (for gating/inspection)
        self.minds = None
        if self.conduct_enabled:
            residents, bonds = self._derive_social()
            self.minds = BigvilleSurpriseTownWorld(
                residents, bonds, extra_seeds=("bigville_fast_bond",), fast_gain=0.1)
            self._mind_names = set(r["name"] for r in residents)

    # ---- derive the social graph from the town's real structure (deterministic) -----
    def _derive_social(self):
        """Held Bonds + predictions from the town's own classes/roles/order -- a
        deterministic social model (no randomness: reproducible). Friends are
        adjacent same-class residents (predict each other); a few deterministic
        feuds cross the grain (resentment, unpredicted -> they surprise)."""
        people = [nm for nm in self.people]
        cls = {nm: self.classes.get(nm, "middle") for nm in people}
        bonds, predicts = {}, {nm: [] for nm in people}
        # friendships: each resident befriends the next same-class resident.
        by_cls = {}
        for nm in people:
            by_cls.setdefault(cls[nm], []).append(nm)
        for group in by_cls.values():
            for i, a in enumerate(group):
                b = group[(i + 1) % len(group)] if len(group) > 1 else None
                if b and b != a:
                    aff = 2.5 + 0.5 * ((i) % 2)
                    bonds[(a, b)] = {"affection": aff}
                    bonds[(b, a)] = {"affection": aff}
                    predicts[a].append(b); predicts[b].append(a)
        # a few feuds: every 4th resident deeply resents a specific other, NOT
        # predicted -> a surprising, provoking encounter (rare directed violence).
        for i, a in enumerate(people):
            if i % 4 == 1 and len(people) > 3:
                foe = people[(i + len(people) // 2) % len(people)]
                if foe != a:
                    bonds[(a, foe)] = {"resentment": 5.0, "affection": -4.0}
                    # deliberately absent from predicts[a] -> it surprises.
        residents = [{"name": nm, "predicts": sorted(set(predicts[nm]))}
                     for nm in people]
        return residents, bonds

    # ---- the conduct pass, each town tick ------------------------------------------
    def _copresence(self):
        cop = {}
        for nm in self.people:
            if nm not in self._mind_names or self.is_dead(nm):
                continue
            p = self.pos.get(nm)
            if not p:
                continue
            near = []
            for o in self.people:
                if o == nm or o not in self._mind_names or self.is_dead(o):
                    continue
                q = self.pos.get(o)
                if q and abs(p[0] - q[0]) + abs(p[1] - q[1]) <= _RANGE:
                    near.append(o)
            cop[nm] = near
        return cop

    def _conduct_pass(self):
        cop = self._copresence()
        if not cop:
            return
        out = self.minds.tick(cop)
        for r in out:
            if not r.get("surprised") or not r.get("chosen"):
                continue
            act, actor, tgt = r["chosen"], r["resident"], r.get("target")
            if act == "rest" or tgt is None:
                continue
            text = "%s %s %s" % (actor, _VERB.get(act, act), tgt)
            ev = dict(tick=self.world_epoch, kind=_KIND.get(act, "conduct"),
                      actors=[actor], target=tgt, act=act, text=text)
            self.events.append(ev)          # into the town's feed (paper/player)
            self.conduct_events.append(ev)

    def integ_step(self):
        super().integ_step()                # the whole town: mechanics + routing
        if self.conduct_enabled:
            self._conduct_pass()            # + interpersonal conduct, surprise-gated

    def conduct_harm_events(self):
        return [e for e in self.conduct_events if e["act"] == "harm"]

    def close(self):
        try:
            if self.minds:
                self.minds.close()
        except Exception:
            pass
        try:
            super().close()
        except Exception:
            pass
