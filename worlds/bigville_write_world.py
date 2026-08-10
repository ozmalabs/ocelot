"""BigvilleWriteWorld -- newspaper-writer Rung D (block 296000): the publisher
WRITES prose from his HELD beliefs, and bias/capture become WORD choices.

WHAT THIS DEMONSTRATES (NEWSPAPER_WRITER_PLAN.md Rung D + BIGVILLE_WRITE_PREREG.md)
--------------------------------------------------------------------------------
The whole chain closes here. A resident holds a salient fact (with structured
fields), WALKS to the publisher and reports it (Rung B), the publisher HOLDS it as
a belief (Rung C), and now the publisher WRITES it: a Story whose `text` is
RENDERED by the engine's StringConcat over the held fact's fields -- graph-native
prose, NOT a Python f-string. Bias/capture select the FRAMING: a free paper names
the patron (the cause clause); a captured paper LAUNDERS a damaging story --
renders the SAME held fact WITHOUT the patron. Free vs captured = DIFFERENT PROSE
about the SAME held belief.

ARCHITECTURE-RULE COMPLIANCE
----------------------------
A WORLD ADAPTER. It writes NO prose and makes NO framing decision -- the Story
text is a StringConcat term the seed rule evaluates; whether the patron clause is
present is the rule chosen by the paper's `captured` + the fact's `damaging`. The
adapter mints the paper/facts, ticks, and reads the rendered `text` back out. The
`_render_text` read is a mechanical string decode of the graph's own output.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                   # noqa: E402
from worlds.bigville_hold_world import BigvilleHoldWorld         # noqa: E402


class BigvilleWriteWorld(BigvilleHoldWorld):
    def __init__(self, *, captured=0, **kw):
        super().__init__(**kw)
        self.eng.load_seed_manifest(manifest_for("bigville_write"), None)
        self._paper = self.eng.add_node("Paper", {"name": "The Bigville Times",
                                                  "captured": float(captured)})
        pub = self._movers[self._publisher] if self._publisher else None
        self._paper_wired = False

    def _wire_paper(self):
        """Attach the paper to the current publisher (writes_for). Called lazily
        once a publisher exists."""
        if not self._paper_wired and self._publisher is not None:
            self.eng.add_edge_unchecked(self._movers[self._publisher],
                                        "writes_for", self._paper)
            self._paper_wired = True

    def add_publisher(self, name, cell):
        m = super().add_publisher(name, cell)
        self._wire_paper()
        return m

    # ---- a structured fact a reporter carries (subject/event/place/patron) -----
    def add_structured_reporter(self, name, cell, *, subject, event, place,
                                patron="", damaging=0, salience=3.0):
        """A reporter whose Fact carries the STRUCTURED fields the render composes.
        The Fact is indexed by `subject` (a bare label, not prose); the newspaper
        SENTENCE is built only by the seed's StringConcat over the fields below."""
        m = self.add_reporter(name, cell, salience=salience, desc=subject)
        f = self._facts[name]
        for k, v in (("subject", subject), ("event", event), ("place", place),
                     ("patron", patron)):
            self.eng.set_attr(f, k, v)
        self.eng.set_attr(f, "damaging", float(damaging))
        self.eng.set_attr(f, "story_written", 0.0)
        return m

    # ------------------------------------------------- glass-box read-offs
    def _story_nodes(self):
        return list(self.eng.neighbours(self._paper, "prints"))

    def stories(self):
        """The printed stories as (text, captured, laundered) -- the newspaper."""
        out = []
        for s in self._story_nodes():
            a = self.eng.node(s)["attrs"]
            out.append((self._as_text(a.get("text", "")),
                        int(a.get("captured", 0.0)), int(a.get("laundered", 0.0))))
        return out

    @staticmethod
    def _as_text(v):
        """Mechanical decode of the rendered text (StringConcat returns a Text
        surface; str() on it is the sentence)."""
        return v if isinstance(v, str) else str(v)

    def headline(self):
        """The (single) rendered story text -- what the paper printed."""
        st = self.stories()
        return st[0][0] if st else None
