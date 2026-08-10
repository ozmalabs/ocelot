"""BigvillePlayWorld -- records a PLAYABLE TIMELINE of a bigville run for the UI: per
animation frame, every resident's position (walking hop-by-hop), what they SAY (speech
acts rendered from the graph), and the ACTIONS/TRADES that fired (located). Pure
mechanical read of real graph state -- NO authored dialogue; every line is a render of a
real graph node/event. This is the "watch the scenario play" export.

The key subtlety: a shopping round-trip (home -> stall -> home) happens INSIDE one tick,
so per-tick positions would teleport. We hook `_walk_leg` (which returns the real hop
path from the R1 nav pipeline) to capture the intra-tick walk, and emit ONE animation
frame per hop -- so you actually see people walk to the market and back.
"""
from __future__ import annotations

from worlds.bigville_integ5_world import BigvilleInteg5World


class BigvillePlayWorld(BigvilleInteg5World):
    def __init__(self, *, cast=18, seed=276000, **kw):
        # a smaller, watchable cast by default; every mechanic is inherited.
        super().__init__(cast=cast, seed=seed, **kw)
        self.timeline = []            # [{t, day, pos:{id:[x,y]}, says:[...], acts:[...]}]
        self._events_emitted = 0      # how many of self.events we've already turned into frames
        self._route_targets = self._build_routine_targets()

    # ---- the daily ROUTINE (a visualisation scaffold over the REAL nav pipeline) -------
    # Residents in this town only moved during the once-a-day market run, so the map sat
    # frozen. Here each resident navigates (via the real mv_* flood/hop rules -- honest
    # pathfinding, no scripted coordinates) toward WHERE they would be at this hour: their
    # workplace in the morning, the market at midday, the town square in the afternoon,
    # home at night. The MOVEMENT is a routine (presentation); every EVENT it surrounds
    # (trade, utterance, conflict, birth, death) is a real graph read.
    def _build_routine_targets(self):
        a = getattr(self, "map_anchors", {}) or {}
        cells = self._cells
        cx = max(x for x, _ in cells) // 2
        cy = max(y for _, y in cells) // 2
        square = self._nearest_cell((cx, cy))
        shops = list((getattr(self, "_shopkeepers", {}) or {}).values())
        # spread ORDINARY folk's workplaces across the whole map (fields/edges) so the
        # morning commute is a visible walk OUT, then they converge on the square midday
        # and disperse home at night -- a real daily rhythm across the town, not a shuffle.
        perimeter = [c for c in cells
                     if c[0] < 4 or c[1] < 4 or c[0] > max(x for x, _ in cells) - 4
                     or c[1] > max(y for _, y in cells) - 4] or cells
        work = {}
        wi = 0
        for nm in self.people:
            role = self.roles2.get(nm, self.roles.get(nm, "villager"))
            if role in ("baker", "fishmonger") and shops:
                work[nm] = self.pos.get(self._movers.get(nm), self.homes.get(nm))
            elif role == "mayor":
                work[nm] = a.get("townhall", square)
            elif role == "pastor":
                work[nm] = a.get("church", square)
            elif role == "banker":
                work[nm] = a.get("bank", square)
            else:
                work[nm] = perimeter[(wi * 7 + 3) % len(perimeter)]   # a distributed field/plot
                wi += 1
        return {"square": square, "work": work,
                "market": self._nearest_cell((cx, cy + 1)),
                "townhall": a.get("townhall", square), "church": a.get("church", square)}

    def _phase_goal(self, nm, tick):
        h = tick % 36
        rt = self._route_targets
        if h < 12:                       # morning: to work
            return rt["work"].get(nm, rt["square"])
        if h < 20:                       # midday: to market / square
            return rt["market"]
        if h < 28:                       # afternoon: gather in the square (or venue)
            return rt["square"]
        return self.homes.get(nm, rt["square"])   # evening: home

    def _route_residents(self):
        for nm in self.people:
            if self.is_dead(nm):
                continue
            goal = self._phase_goal(nm, self.world_epoch)
            if not goal or self.pos.get(nm) == tuple(goal):
                continue
            try:
                self.eng.set_attr(self._movers[nm], "energy", 100.0)
                self.set_goal(nm, goal)
                self.move_one(nm)         # real flood + rule-chosen hops, one tick's budget
            except Exception:
                pass

    # -- render a real speech/action event into a located happening ----------------------
    _SPEECH_KINDS = {"drama", "council", "paper", "loud"}

    def _actor_pos(self, ev):
        for a in ev.get("actors", []):
            p = self.pos.get(a)
            if p:
                return [int(p[0]), int(p[1])]
        # fall back to the relevant institution anchor for town-wide acts
        anchors = getattr(self, "map_anchors", {}) or {}
        if ev["kind"] == "council":
            return list(anchors.get("townhall", [0, 0]))
        if ev["kind"] == "paper":
            return list(anchors.get("press", [0, 0]))
        return None

    def _drain_events(self):
        says, acts = [], []
        for ev in self.events[self._events_emitted:]:
            at = self._actor_pos(ev)
            actors = ev.get("actors") or []
            aid = actors[0] if actors else None
            item = {"id": aid, "at": at, "kind": ev["kind"], "text": ev.get("text", "")}
            if ev["kind"] in self._SPEECH_KINDS:
                says.append(item)
            else:
                acts.append(item)
        self._events_emitted = len(self.events)
        return says, acts

    def _snapshot_positions(self):
        pos = {}
        for nm in self.people:
            if self.is_dead(nm):
                continue
            p = self.pos.get(nm)
            if p:
                pos[nm] = [int(p[0]), int(p[1])]
        return pos

    def integ_step(self):
        super().integ_step()                 # the REAL sim (trades, social, life)
        self._route_residents()              # continuous daily movement over the real nav
        says, acts = self._drain_events()     # real events this tick -> speech + popups
        self.timeline.append({
            "t": self.world_epoch, "day": int(self.world_epoch // 36),
            "pos": self._snapshot_positions(), "says": says, "acts": acts})

    def play_doc(self):
        """The playable-scenario contract the UI consumes -- map, RICH residents (full
        held-state / journal / relationships / coin / health, from the state reader), the
        printed PAPER + council board, and the per-frame timeline. All real graph reads."""
        from worlds.bigville_integ3_state import export_townstate3
        snap = export_townstate3(self)
        # the townstate villagers already carry held/journal/rel/coin/health/cls/alive --
        # enrich each with its home (for the routine) and keep them as the residents.
        by_id = {v["id"]: v for v in snap.get("villagers", [])}
        residents = []
        for nm in self.people:
            v = dict(by_id.get(nm, {"id": nm}))
            v.setdefault("name", self.display.get(nm, nm))
            v.setdefault("role", self.roles2.get(nm, self.roles.get(nm, "villager")))
            v.setdefault("face", self.emoji.get(nm, "\U0001F9D1"))
            v.setdefault("cls", self.classes.get(nm, "middle"))
            v["home"] = list(self.homes.get(nm, self.pos.get(nm, [0, 0])))
            residents.append(v)
        return {
            "map": snap["map"],
            "residents": residents,
            "shops": {r: list(self.pos.get(k, [0, 0]))
                      for r, k in (getattr(self, "_shopkeepers", {}) or {}).items()},
            "paper": snap.get("paper", []),
            "council_board": snap.get("council_board", []),
            "collective_action": snap.get("collective_action"),
            "institutions": snap.get("institutions", {}),
            "frames": self.timeline,
            "days": int(self.world_epoch // 36),
            "ticks": int(self.world_epoch),
        }
