"""BigvilleColumnWorld -- writing to length as importance-weighted ALLOCATION,
with distortion as a first-class OWNED behavior on three orthogonal axes
(blocks 298000-299000).

WHAT THIS DEMONSTRATES (BIGVILLE_COLUMN_ALLOC_PREREG.md)
------------------------------------------------------
Writing to length is TOP-DOWN: the budget sets the PLAN. The budget is allocated
across held beats by IMPORTANCE (a priority waterfall); each beat is composed to
the deepest held form its share affords; the article length EMERGES from the
allocation (there is no total-length correction loop and no expand/compress toggle).
When the column is bigger than the core informative content, the writer's
dispositions decide the 4-way fill-pressure fork -- run short, or pad with
truisms (low substance) / the true-but-irrelevant cats (low focus) / fabrication
(low honesty). Every printed clause carries three tags (veracity x relevance x
informativeness); nothing printed is untracked; the glass-box town lets us
measure every distortion against the ground truth we own.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It makes NO writing decision: allocation, per-beat depth, and
which clauses print (and thus every distortion) are the seed rules
(seeds/bigville_column_alloc.json). Prose is a StringConcat term the render rules
evaluate. `len()` is used ONLY as a RULER -- each candidate form's length is
measured once at ingest and written onto the graph, the way a writer estimates a
phrasing; it is NOT a driver and there is NO loop nudging a total length toward
the budget. The two ordered rule passes (allocate, then fabricate) are sequenced
by a mechanical `phase` marker the adapter sets (like the epoch bump in
bigville_publisher_world), not a decision. `force_all_dirty()` precedes each
`run_rules` because the ruler/phase writes use `set_attr`. No `StrLen` Term is
added; runners/dsl and the .so are untouched.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                              # noqa: E402
from substrate.seed_loader import manifest_for                   # noqa: E402

_BIG = 1000000
_SEP = " "
_VERACITY = {2.0: "held", 1.0: "inferred", 0.0: "fabricated"}
_RELEVANCE = {2.0: "core", 1.0: "tangential", 0.0: "irrelevant"}
_INFO = {2.0: "residual", 1.0: "some", 0.0: "truism"}
_DEPTH_TEXT = {2.0: "text_d2", 1.0: "text_d1", 0.0: "text_d0"}


class BigvilleColumnWorld:
    def __init__(self, budget, *, honesty=1.0, focus=1.0, substance=1.0,
                 captured=0, patron="", lorem=False):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_column_alloc"), None)
        if lorem:
            self.eng.load_seed_manifest(manifest_for("bigville_column_alloc_lorem"), None)
        self._col = self.eng.add_node("Column", {
            "budget": float(budget), "phase": "init", "patron": patron})
        self._writer = self.eng.add_node("Writer", {
            "honesty": float(honesty), "focus": float(focus),
            "substance": float(substance), "captured": float(captured),
            "patron": patron})
        self.eng.add_edge_unchecked(self._col, "by", self._writer)
        self._beats = []          # nid list
        self._pads = []           # nid list

    # ------------------------------------------------------------------ ingest
    def add_beat(self, subject, predicate, mid, tail, *, importance, pos,
                 is_lead=False):
        """A CORE held fact (veracity held, relevance core, informativeness
        residual). Allocated depth by importance."""
        b = self.eng.add_node("Beat", {
            "subject": subject, "predicate": predicate, "mid": mid, "tail": tail,
            "importance": float(importance), "pos": float(pos),
            "is_lead": 1.0 if is_lead else 0.0,
            "provenance": "held", "veracity_num": 2.0, "relevance_num": 2.0,
            "informativeness_num": 2.0,
            "rendered": 0.0, "depth": None, "chosen_len": 0.0, "chosen_text": ""})
        self.eng.add_edge_unchecked(self._col, "has_beat", b)
        self._beats.append(b)
        return b

    def add_pad(self, pre, *, veracity, relevance, informativeness, pos,
                post="", exculpatory=False):
        """A padding-clause CANDIDATE the writer MAY print under fill-pressure,
        tagged on all three axes: veracity/relevance/informativeness in {0,1,2}.
        Generic color / the cats / truisms / captured exculpatory spin."""
        po = self.eng.add_node("PadOption", {
            "pre": pre, "post": post,
            "veracity_num": float(veracity), "relevance_num": float(relevance),
            "informativeness_num": float(informativeness),
            "provenance": _VERACITY.get(float(veracity), "?"),
            "exculpatory": 1.0 if exculpatory else 0.0,
            "pos": float(pos), "printed": 0.0, "rendered": 0.0, "text": ""})
        self.eng.add_edge_unchecked(self._col, "has_pad", po)
        self._pads.append(po)
        return po

    # ---------------------------------------------------------------- the run
    def _rr(self):
        self.eng.force_all_dirty()
        self.eng.run_rules(_BIG)

    def run(self):
        """Render candidates, measure each form ONCE with len() (the ruler), then
        run the allocate phase and the fabricate phase. Mechanical and loop-free:
        no iteration, no total-length chasing, no budget-vs-length comparison here
        -- the decisions are all in the rules."""
        # 1. render every candidate form (StringConcat in the rules)
        self.eng.set_attr(self._col, "phase", "init")
        self._rr()
        # 2. RULER: measure each candidate form's length once (len(), + separator)
        for b in self._beats:
            a = self.eng.node(b)["attrs"]
            for dk in ("d0", "d1", "d2"):
                self.eng.set_attr(b, "len_" + dk, float(len(str(a.get("text_" + dk, ""))) + 1))
        for po in self._pads:
            a = self.eng.node(po)["attrs"]
            self.eng.set_attr(po, "len", float(len(str(a.get("text", ""))) + 1))
        # 3. ALLOCATE (importance waterfall), then 4. FABRICATE (padding fork)
        self.eng.set_attr(self._col, "phase", "allocate")
        self._rr()
        self.eng.set_attr(self._col, "phase", "fabricate")
        self._rr()
        return self.length()

    # ------------------------------------------------- glass-box read-offs
    def _printed_clauses(self):
        """Every printed clause as a dict of (pos, text, veracity, relevance,
        informativeness, provenance, tracked). Read off the graph -- the held
        beats at their allocated depth + the printed PadOptions (incl. any
        rule-minted one, e.g. the untracked lorem control)."""
        out = []
        for b in self.eng.neighbours(self._col, "has_beat"):
            a = self.eng.node(b)["attrs"]
            if a.get("depth") is not None and a.get("depth", -1.0) >= 0.0:
                out.append(self._clause(a.get("pos", 0.0), str(a.get("chosen_text", "")), a))
        for po in self.eng.neighbours(self._col, "has_pad"):
            a = self.eng.node(po)["attrs"]
            if a.get("printed", 0.0) == 1.0:
                out.append(self._clause(a.get("pos", 0.0), str(a.get("text", "")), a))
        out.sort(key=lambda c: c["pos"])
        return out

    @staticmethod
    def _clause(pos, text, a):
        has = all(k in a for k in ("veracity_num", "relevance_num", "informativeness_num"))
        return {
            "pos": pos, "text": text,
            "veracity": _VERACITY.get(a.get("veracity_num"), None) if has else None,
            "relevance": _RELEVANCE.get(a.get("relevance_num"), None) if has else None,
            "informativeness": a.get("informativeness_num") if has else None,
            "v_num": a.get("veracity_num"), "r_num": a.get("relevance_num"),
            "i_num": a.get("informativeness_num"),
            "provenance": a.get("provenance"), "tracked": has}

    def article_text(self):
        return _SEP.join(c["text"] for c in self._printed_clauses())

    def length(self):
        cs = self._printed_clauses()
        return sum(len(c["text"]) for c in cs) + max(0, len(cs) - 1)

    def budget(self):
        return int(self.eng.node(self._col)["attrs"]["budget"])

    # ---- the three axes measured against the ground truth we own ----
    def metrics(self):
        cs = self._printed_clauses()
        n = len(cs)
        tracked = [c for c in cs if c["tracked"]]
        return {
            "n_clauses": n,
            "all_tracked": all(c["tracked"] for c in cs),
            "length": self.length(),
            # veracity: share held / mean; a fabricated clause has v_num 0
            "veracity_rate": (sum(c["v_num"] for c in tracked) / (2.0 * len(tracked)))
                              if tracked else 1.0,
            "fabricated_share": (sum(1 for c in tracked if c["v_num"] == 0.0) / len(tracked))
                                if tracked else 0.0,
            # relevance: mean / share off-core
            "relevance_rate": (sum(c["r_num"] for c in tracked) / (2.0 * len(tracked)))
                              if tracked else 1.0,
            "irrelevant_share": (sum(1 for c in tracked if c["r_num"] == 0.0) / len(tracked))
                                if tracked else 0.0,
            # informativeness: mean residual + the article-level aggregate
            "mean_informativeness": (sum(c["i_num"] for c in tracked) / len(tracked))
                                    if tracked else 0.0,
            "net_information": sum(c["i_num"] for c in tracked),
        }

    def clause_table(self):
        return [(round(c["pos"]), c["provenance"], c["veracity"], c["relevance"],
                 c["i_num"], c["text"]) for c in self._printed_clauses()]

    def beat_depth(self, beat_nid):
        return self.eng.node(beat_nid)["attrs"].get("depth")

    def lead_text(self):
        for b in self.eng.neighbours(self._col, "has_beat"):
            a = self.eng.node(b)["attrs"]
            if a.get("is_lead", 0.0) == 1.0 and a.get("depth", -1.0) is not None \
                    and a.get("depth", -1.0) >= 0.0:
                return str(a.get("chosen_text", ""))
        return None

    def contains(self, substr):
        return substr in self.article_text()

    def close(self):
        self._beats.clear()
        self._pads.clear()
