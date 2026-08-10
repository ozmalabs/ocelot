"""BigvilleNewsWorld -- bigville R21 (block 269000): THE NEWSPAPER & THE REPORTER
-- the fourth estate, a SECOND reconstruction channel.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R21 + sec 0 "THE ROOM
WHERE IT HAPPENED")
--------------------------------------------------------------------------------
The town gains a PUBLIC SPHERE -- an independent (or captured) account of itself
that most residents' picture of DISTANT events is built from. Distinct from the
R20 noticeboard (the council's OFFICIAL voice, one institutional bias): the paper
is the REPORTER's INDEPENDENT account (the reporter's OWN bias) and it can point
back AT the council.

  * G-paper-propagates-beliefs (mass channel): a LITERATE resident who did NOT
    witness an event acquires a belief about it FROM the paper -- belief-propagation
    BEYOND earshot (R19 is proximity-bound; the paper is not). Ablate the paper ->
    that resident stays ignorant. ILLITERATE residents depend on the oral layer
    only (R18 informed/uninformed divide).
  * G-free-vs-captured-press (HEADLINE): the reporter's account of a damaging story
    (John's corruption) depends on the paper's FUNDING + fear -- an independent
    paper prints it; a captured paper (bankrolled/intimidated) LAUNDERS or OMITS
    it. Ablate the capture -> the suppressed story prints.
  * G-second-reconstruction-channel (benchmark): the paper is a SECOND lossy
    rendering of the same event (alongside the noticeboard minutes), occlusion-bound
    + bias-shaped, and WE hold the ground truth -- so BOTH renderings are scoreable,
    with DIFFERENT bias profiles (the clerk PROTECTS the council; the reporter may
    ATTACK it).
  * G-paper-feeds-collective-action: a shared grievance becomes COMMON KNOWLEDGE
    via the paper -> the coalition can form; capture the paper -> the coordination
    is suppressed.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It edits no tracked file and holds NO press/reading decision.
Everything runs in an ISOLATED substrate (`substrate_rs.Substrate`) loading two
SEED manifests (bigville_news_press / bigville_news_reach). EVERY decision is a
RULE there -- who writes (occlusion-bound), the capture suppression, the printing,
the second-channel (clerk) rendering, the witness/direct knowledge, the literate
reader learning beyond earshot, the informed-count, and the coalition-forms-on-
quorum. None lives in Python. This adapter only does mechanical I/O: register the
graph data, wire edges, run the Rust run_rules fixpoint, and read state back. No
Python if/else over agent state decides any of it -- source-audit gate.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.engine_provenance import engine_preamble            # noqa: E402
engine_preamble(strict=False)                                    # resolve THIS tree's engine

import substrate_rs                                              # noqa: E402
from substrate.seed_loader import manifest_for                   # noqa: E402

# defaults set on every node so a rule never reads a missing key. Population
# variation (literate / witnessed / captured / bias / ...) is set by the caller --
# ingest, not a decision.
STORY_DEFAULTS = dict(content=0.0, reporter_bias=0.0, written=0.0,
                      suppressed=0.0, printed=0.0)
MINUTES_DEFAULTS = dict(value=0.0, clerk_bias=0.0, recorded=0.0)
RESIDENT_DEFAULTS = dict(literate=0.0, witnessed=0.0,
                         knows_event=0.0, knows_event_flag=0.0)
COALITION_DEFAULTS = dict(quorum=0.0, informed=0.0, formed=0.0)


class BigvilleNewsWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_news_press"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_news_reach"), None)
        self.eng.load_seed_manifest(manifest_for("bigville_news_copy"), None)   # a HELD copy confers reading
        self._town = None
        self._event = None
        self._reporter = None
        self._paper = None
        self._story = None
        self._minutes = None
        self._coalition = None
        self._residents = {}

    # ------------------------------------------------------------------ ingest
    def add_town(self):
        self._town = self.eng.add_node("Town", {})
        return self._town

    def add_event(self, *, truth_value, damaging_to_owner=0):
        """The ground-truth event (a council decision / a foreclosure / John's
        corruption). truth_value = the magnitude WE hold; damaging_to_owner marks a
        story that implicates the paper's would-be patron."""
        if self._town is None:
            self.add_town()
        e = self.eng.add_node("Event", {"truth_value": float(truth_value),
                                        "damaging_to_owner": float(damaging_to_owner)})
        self.eng.add_edge_unchecked(e, "in_town", self._town)
        self._event = e
        return e

    def add_reporter(self, name, *, witnessed=1):
        """The reporter -- writes the paper. witnessed = the R19 occlusion outcome:
        the reporter reports only what was witnessed/told."""
        r = self.eng.add_node("Reporter", {"name": name, "witnessed": float(witnessed)})
        self.eng.add_edge_unchecked(r, "covers", self._event)
        self._reporter = r
        return r

    def add_paper(self, name, *, captured=0, active=1):
        """The newspaper. captured = bankrolled/intimidated by John/Scrooge (launders
        a damaging story); active = the paper-exists lever (ablate the paper)."""
        p = self.eng.add_node("Paper", {"name": name, "captured": float(captured),
                                        "active": float(active)})
        self.eng.add_edge_unchecked(p, "employs", self._reporter)
        self._paper = p
        return p

    def add_story(self, *, reporter_bias=0):
        """The reporter's rendering of the event in the paper -- the INDEPENDENT
        account (reporter_bias = the reporter's OWN bias, e.g. attacks the council)."""
        attrs = dict(STORY_DEFAULTS)
        attrs.update(reporter_bias=float(reporter_bias))
        s = self.eng.add_node("Story", attrs)
        self.eng.add_edge_unchecked(self._paper, "reports", s)
        self.eng.add_edge_unchecked(s, "about", self._event)
        self._story = s
        return s

    def add_minutes(self, *, clerk_bias=0):
        """The SECOND channel -- the noticeboard minutes, re-modelled locally so both
        renderings score against ONE ground truth (the clerk PROTECTS the council)."""
        attrs = dict(MINUTES_DEFAULTS)
        attrs.update(clerk_bias=float(clerk_bias))
        m = self.eng.add_node("Minutes", attrs)
        self.eng.add_edge_unchecked(m, "of_event", self._event)
        self._minutes = m
        return m

    def add_resident(self, name, *, literate=0, witnessed=0, reads=1):
        """A townsperson. literate = the R18 outcome; witnessed = R19 proximity to the
        event; reads = subscribes to the paper (edge to the paper)."""
        attrs = dict(RESIDENT_DEFAULTS)
        attrs.update(name=name, literate=float(literate), witnessed=float(witnessed))
        r = self.eng.add_node("Resident", attrs)
        self.eng.add_edge_unchecked(self._town, "has_resident", r)
        if reads and self._paper is not None:
            self.eng.add_edge_unchecked(r, "reads", self._paper)
        self._residents[name] = r
        return r

    def give_newspaper(self, name, qty=1):
        """Put a PHYSICAL newspaper (a Good `of_paper` the town's paper) in a resident's hands -- what
        buying a copy leaves them holding. Holding it confers readership (np_copy_confers_reading), so
        even a non-subscriber learns the story. The good code matches the catalog-driven press output."""
        from worlds.bigville_econ_world import NEWSPAPER
        copy = self.eng.add_node("Good", {"good": float(NEWSPAPER), "qty": float(qty)})
        self.eng.add_edge_unchecked(self._residents[name], "has_good", copy)
        self.eng.add_edge_unchecked(copy, "of_paper", self._paper)
        return copy

    def add_coalition(self, *, quorum):
        """The would-be coalition over a shared grievance. Forms iff >= quorum
        residents hold the common knowledge."""
        attrs = dict(COALITION_DEFAULTS)
        attrs.update(quorum=float(quorum))
        c = self.eng.add_node("Coalition", attrs)
        self.eng.add_edge_unchecked(c, "in_town", self._town)
        self._coalition = c
        return c

    # ------------------------------------------------- rule-driven publication
    def publish(self):
        """Run the press + reach rules to a fixpoint. All DECISIONS are rules; this
        only ticks and reads."""
        self.eng.run_rules(1000000)
        return dict(written=self.written(), suppressed=self.suppressed(),
                    printed=self.printed(), content=self.content(),
                    minutes_value=self.minutes_value(), recorded=self.recorded())

    # ------------------------------------------------- glass-box read-offs
    def _matt(self, node, key, default=0.0):
        return float(self.eng.node(node)["attrs"].get(key, default))

    def truth_value(self):
        return self._matt(self._event, "truth_value")

    def written(self):
        return int(self._matt(self._story, "written")) if self._story is not None else 0

    def suppressed(self):
        return int(self._matt(self._story, "suppressed")) if self._story is not None else 0

    def printed(self):
        return int(self._matt(self._story, "printed")) if self._story is not None else 0

    def content(self):
        return self._matt(self._story, "content") if self._story is not None else 0.0

    def recorded(self):
        return int(self._matt(self._minutes, "recorded")) if self._minutes is not None else 0

    def minutes_value(self):
        return self._matt(self._minutes, "value") if self._minutes is not None else 0.0

    def knows_event_flag_of(self, name):
        return int(self._matt(self._residents[name], "knows_event_flag"))

    def knows_event_of(self, name):
        return self._matt(self._residents[name], "knows_event")

    def informed(self):
        return int(self._matt(self._coalition, "informed")) if self._coalition is not None else 0

    def formed(self):
        return int(self._matt(self._coalition, "formed")) if self._coalition is not None else 0

    def close(self):
        self._residents.clear()
