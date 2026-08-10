"""BigvilleNoticeboardWorld -- bigville R49 (block 359000): a noticeboard in the town square.

Agents already write notes (a held Note), give them to others, and relay them through
hand-off chains. This adds POSTING (pin a held note on the square's board -- you must be there)
and READING (anyone present at the square reads the board). A local, public medium.

A WORLD ADAPTER. No post/read DECISION in Python -- nb_* are seed rules. The adapter mints the
square/board/agents/notes, models writing/giving/relaying as mechanical hand-offs of the
`holds` edge, moves agents to/from the square, arms posting, and reads.
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


class BigvilleNoticeboardWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_noticeboard"), None)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._square = self.eng.add_node("Square", {"name": "town square"})
        self.eng.add_edge_unchecked(self._town, "has_square", self._square)
        self._board = self.eng.add_node("Noticeboard", {"name": "the noticeboard"})
        self.eng.add_edge_unchecked(self._square, "has_board", self._board)
        self._agents = {}
        self._notes = {}          # content -> note node

    def _run(self):
        for _ in range(4):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ------------------------------------------------------------------ ingest
    def add_agent(self, name):
        a = self.eng.add_node("Agent", {"name": name})
        self.eng.add_edge_unchecked(self._town, "has_resident", a)
        self._agents[name] = a
        return a

    def write_note(self, author, content):
        """Write a note (a held Note{content,author}) -- the author holds it."""
        n = self.eng.add_node("Note", {"content": content, "author": author, "post_armed": 0.0, "posted": 0.0})
        self.eng.add_edge_unchecked(self._agents[author], "holds", n)
        self._notes[content] = n
        return n

    def give_note(self, frm, to, content):
        """Hand a note to another agent (a relay step -- give it to someone to give to someone)."""
        n = self._notes[content]
        self.eng.remove_edge_unchecked(self._agents[frm], "holds", n)
        self.eng.add_edge_unchecked(self._agents[to], "holds", n)

    def go_to_square(self, name):
        self.eng.add_edge_unchecked(self._agents[name], "at", self._square); self._run()

    def leave_square(self, name):
        self.eng.remove_edge_unchecked(self._agents[name], "at", self._square)

    def post(self, name, content):
        """Pin a held note on the board (must be at the square and hold it)."""
        self.eng.set_attr(self._notes[content], "post_armed", 1.0)
        self._run()

    # ------------------------------------------------- glass-box read-offs
    def is_posted(self, content):
        return float(self.eng.node(self._notes[content])["attrs"].get("posted", 0.0)) == 1.0
    def board_contents(self):
        return sorted(self.eng.node(n)["attrs"]["content"]
                      for n in self.eng.in_neighbours(self._board, "posted_on"))
    def holder_of_note(self, content):
        for src in self.eng.in_neighbours(self._notes[content], "holds"):
            return self.eng.node(src)["attrs"]["name"]
        return None
    def reads_of(self, name):
        return sorted(self.eng.node(n)["attrs"]["content"]
                      for n in self.eng.neighbours(self._agents[name], "read"))
    def has_read(self, name, content):
        return content in self.reads_of(name)
