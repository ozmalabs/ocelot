"""BigvilleChurchWorld -- bigville R30 (block 319000): the church's public
congregation + Mary's private counsel room.

The church already exists as a funded institution (bigville_fisc_church, 257000);
Mary the pastor is a main named character (cast100). This adds the non-denominational
public Service with an EMERGENT congregation (each resident's collapse over
{go,stay}), and the PRIVATE counsel room where what a resident confides to Mary is
confidential -- held privately, never public (the-room-where-it-happened occlusion).

A WORLD ADAPTER. No attend/counsel DECISION in Python -- ch_* are seed rules; the
attend decision is an Argmax collapse in the seed. The adapter mints the church/
Mary/room/residents, arms Sunday and counsel, ticks, and reads.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.seed_loader import manifest_for          # noqa: E402
from worlds.bigville_map_generator import BigvilleMapGenerator   # noqa: E402

_CHOICES = [("go", 1.0), ("stay", -1.0)]                # the attend/abstain collapse candidates


class BigvilleChurchWorld:
    def __init__(self, pastor_draw=0.8, *, seed=0):
        # MIGRATED (block 344000): the church, Mary, and her private counsel room are no longer
        # hand-minted -- they are GENERATED (a fixed-point of the town map). The behavioural ch_*
        # rules bind to the generated geography via the has_church / staffed_by / has_room edges the
        # generator emits. The adapter only sets the pastor's draw and adds residents + choices.
        self.gen = BigvilleMapGenerator(seed=seed).generate()
        self.eng = self.gen.eng
        self.eng.load_seed_manifest(manifest_for("bigville_church"), None)
        self._town = self.gen._town
        self.eng.set_attr(self._town, "sunday", 0.0)
        self._church = self.gen.role_place("church")            # town -has_church-> this place
        self._mary = self.gen.staff_node("Church")              # church -staffed_by-> Mary (pastor)
        self.eng.set_attr(self._mary, "draw", float(pastor_draw))
        self._room = self.gen.room_node("Church", "counsel")    # the private counsel room
        for label, sign in _CHOICES:
            self.eng.add_node("ChurchChoice", {"label": label, "attend_sign": sign})
        self._residents = {}

    # ------------------------------------------------------------------ ingest
    def add_resident(self, name, *, piety=0.5, worldly_pull=0.3, creed="none", distress=0.0):
        r = self.eng.add_node("Resident", {"name": name, "piety": float(piety),
                                           "worldly_pull": float(worldly_pull),
                                           "creed": creed, "distress": float(distress),
                                           "church_choice": "", "counsel_armed": 0.0,
                                           "counseled": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_resident", r)
        self._residents[name] = r
        return r

    def _run(self):
        self.eng.force_all_dirty()
        return self.eng.run_rules(1000000)

    def sunday(self):
        """Hold the Sunday service; each resident decides (collapses) whether to attend."""
        self.eng.set_attr(self._town, "sunday", 1.0)
        self._run()
        self.eng.set_attr(self._town, "sunday", 0.0)

    def seek_counsel(self, name, *, confides, distress=1.0):
        """A resident goes to Mary's private room to be counselled."""
        r = self._residents[name]
        self.eng.set_attr(r, "confides", confides)
        self.eng.set_attr(r, "distress", float(distress))
        self.eng.set_attr(r, "counsel_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def is_non_denominational(self):
        return float(self.eng.node(self._church)["attrs"].get("non_denominational", 0.0)) == 1.0

    def pastor_name(self):
        return self.eng.node(self._mary)["attrs"]["name"]

    def _open_service(self):
        for s in self.eng.neighbours(self._church, "has_service"):
            if float(self.eng.node(s)["attrs"].get("open", 0.0)) == 1.0:
                return s
        return None

    def congregation(self):
        """Who attended the current service (emergent, by name)."""
        s = self._open_service()
        if s is None:
            return []
        return sorted(n for n, r in self._residents.items()
                      if s in self.eng.neighbours(r, "attends"))

    def congregation_size(self):
        return len(self.congregation())

    def distress_of(self, name):
        return round(float(self.eng.node(self._residents[name])["attrs"].get("distress", 0.0)), 3)

    def private_disclosures(self):
        """What Mary holds in confidence -- visible to the OBSERVER only (the town cannot
        read it). Returns [(content, private, public)]."""
        out = []
        for disc in self.eng.neighbours(self._mary, "holds_private"):
            a = self.eng.node(disc)["attrs"]
            out.append((a.get("content"), float(a.get("private", 0.0)), float(a.get("public", 0.0))))
        return out
