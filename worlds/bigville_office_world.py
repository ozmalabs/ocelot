"""BigvilleOfficeWorld -- bigville R48 (block 358000): jobs/roles are AGENT-CREATED, advertised,
applied-for, appointed, delegated -- never hardcoded, never magically filled.

A role is a concept an authority conceives in response to NEED (council by decree; owner
directly for an overloaded establishment). The opening must be MADE KNOWN -- advertised by a
posted note, spread by word of mouth through `knows` ties, or the creator directly ASKS a
person. Those who learn of it DECIDE whether to apply; the delegator selects among the
APPLICANTS. The holder's authority is delegated; a holder who dies/leaves vacates and the
opening is re-advertised for a successor.

A WORLD ADAPTER. No create/advertise-hearing/apply/select/appoint DECISION in Python --
of_*/rc_* are seed rules. The adapter mints the bodies/residents/decrees, posts notices,
makes direct asks, wires `knows` ties, and reads.
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


class BigvilleOfficeWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_office"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_noticeboard"), None)   # advertising medium
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._square = self.eng.add_node("Square", {"name": "town square"})
        self.eng.add_edge_unchecked(self._town, "has_square", self._square)
        self._board = self.eng.add_node("Noticeboard", {"name": "the noticeboard"})
        self.eng.add_edge_unchecked(self._square, "has_board", self._board)
        for label, sign in (("apply", 1.0), ("pass", -1.0)):   # the apply/pass collapse codebook
            self.eng.add_node("ApplyStance", {"label": label, "sign": sign})
        self._council = None
        self._nodes = {}
        self._job_notes = {}

    def _run(self):
        for _ in range(8):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ the delegating bodies
    def add_council(self, *, w_competence=1.0, w_loyalty=1.0):
        c = self.eng.add_node("Council", {"name": "Council", "authority": 0.0,
                                          "w_competence": float(w_competence), "w_loyalty": float(w_loyalty)})
        self.eng.add_edge_unchecked(self._town, "has_council", c)
        self._council = c
        return c

    def recognize_council(self, name):
        self.eng.add_edge_unchecked(self._resident(name), "recognizes", self._council)

    def unrecognize_council(self, name):
        self.eng.remove_edge_unchecked(self._nodes[name], "recognizes", self._council)
        self._run()

    def add_owner(self, name, *, authority=5.0, w_competence=1.0, w_loyalty=1.0):
        o = self.eng.add_node("Agent", {"name": name, "authority": float(authority), "alive": 1.0,
                                        "w_competence": float(w_competence), "w_loyalty": float(w_loyalty)})
        self._nodes[name] = o
        return o

    def add_establishment(self, owner, name, *, workload, capacity, needed_role):
        e = self.eng.add_node("Establishment", {"name": name, "workload": float(workload),
                                                "capacity": float(capacity), "needed_role": needed_role})
        self.eng.add_edge_unchecked(self._nodes[owner], "owns", e)
        self._nodes[name] = e
        return e

    def set_workload(self, estab, workload):
        self.eng.set_attr(self._nodes[estab], "workload", float(workload)); self._run()

    # ------------------------------------------------------------------ residents (potential applicants)
    def _resident(self, name):
        if name not in self._nodes:
            # a bare resident is CONTENT by default (reservation > want_work) -- they won't apply
            # unless made a real job-seeker via add_resident
            self._nodes[name] = self.eng.add_node("Agent", {"name": name, "alive": 1.0, "left": 0.0,
                                                            "competence": 0.5, "loyalty": 0.5,
                                                            "want_work": 0.0, "reservation": 0.5,
                                                            "apply_choice": ""})
            self.eng.add_edge_unchecked(self._town, "has_resident", self._nodes[name])
        return self._nodes[name]

    def add_resident(self, name, *, competence=0.5, loyalty=0.5, want_work=0.0, reservation=0.3, alive=1):
        a = self._resident(name)
        for k, v in (("competence", competence), ("loyalty", loyalty), ("want_work", want_work),
                     ("reservation", reservation), ("alive", float(alive)), ("left", 0.0),
                     ("apply_choice", "")):
            self.eng.set_attr(a, k, v if isinstance(v, str) else float(v))
        return a

    def knows(self, a, b):
        """A social tie for WORD OF MOUTH (a can tell b of an opening)."""
        self.eng.add_edge_unchecked(self._nodes[a], "knows", self._nodes[b])

    # ------------------------------------------------------------------ creation + making it known
    def decree_role(self, title):
        """The council DECREES a new role (product of a convened meeting -- bureaucracy)."""
        d = self.eng.add_node("Decree", {"title": title, "armed": 1.0})
        self.eng.add_edge_unchecked(self._council, "holds_decree", d)
        self._run()

    def advertise(self, title):
        """Post a NOTICE for the opening -- residents will HEAR of it (see the note)."""
        off = self._office(title)
        n = self.eng.add_node("Notice", {"title": title})
        self.eng.add_edge_unchecked(n, "advertises", off)
        self.eng.set_attr(off, "advertised", 1.0)
        self._run()

    def ask(self, person, title):
        """The creator directly ASKS a person about the opening -- they become aware (and decide)."""
        self.eng.add_edge_unchecked(self._nodes[person], "aware_of", self._office(title))
        self._run()

    def advertise_on_board(self, title, *, poster="Beadle"):
        """Advertise the opening by POSTING a job-note on the square's noticeboard (the physical
        path: residents must VISIT the square and read it to learn of the job). Composes
        bigville_noticeboard -- the poster writes the note, carries it to the square, and pins it."""
        off = self._office(title)
        p = self._resident(poster)
        note = self.eng.add_node("Note", {"content": f"help wanted: {title}", "author": poster,
                                          "post_armed": 1.0, "posted": 0.0})
        self.eng.add_edge_unchecked(p, "holds", note)
        self.eng.add_edge_unchecked(note, "advertises", off)      # the bridge of_hear_posted reads
        self.eng.add_edge_unchecked(p, "at", self._square)        # the poster is at the board
        self._job_notes[title] = note
        self._run()

    def go_to_square(self, name):
        """A resident visits the square -- they read the board and learn of any posted openings."""
        self.eng.add_edge_unchecked(self._resident(name), "at", self._square)
        self._run()

    def run(self):
        self._run()

    # ------------------------------------------------------------------ lifecycle events
    def kill(self, name):
        self.eng.set_attr(self._nodes[name], "alive", 0.0); self._run()
    def depart(self, name):
        self.eng.set_attr(self._nodes[name], "left", 1.0); self._run()
    def revoke(self, title):
        self.eng.set_attr(self._office(title), "revoke_armed", 1.0); self._run()

    # ------------------------------------------------- glass-box read-offs
    def _offices(self):
        out = []
        for dele in [n for n in ([self._council] if self._council else []) + list(self._nodes.values())]:
            for o in self.eng.neighbours(dele, "delegates"):
                out.append(o)
        return out
    def _office(self, title):
        for o in self._offices():
            if self.eng.node(o)["attrs"].get("title") == title:
                return o
        return None
    def offices(self):
        return sorted(self.eng.node(o)["attrs"]["title"] for o in self._offices())
    def office_exists(self, title): return self._office(title) is not None
    def is_filled(self, title):
        o = self._office(title)
        return o is not None and float(self.eng.node(o)["attrs"].get("filled", 0.0)) == 1.0
    def holder_of(self, title):
        o = self._office(title)
        h = None if o is None else self.eng.node(o)["attrs"].get("holder_name", "")
        return h or None
    def aware(self, title):
        o = self._office(title)
        return sorted(self.eng.node(a)["attrs"]["name"] for a in self.eng.in_neighbours(o, "aware_of")) if o else []
    def applicants(self, title):
        o = self._office(title)
        return sorted(self.eng.node(a)["attrs"]["name"] for a in self.eng.in_neighbours(o, "applies_to")) if o else []
    def council_authority(self):
        return int(round(float(self.eng.node(self._council)["attrs"].get("authority", 0.0))))
    def delegated_authority(self, name):
        return round(float(self.eng.node(self._nodes[name])["attrs"].get("delegated_authority", 0.0)), 4)
