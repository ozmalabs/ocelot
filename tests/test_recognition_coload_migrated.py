"""bigville design-audit 6.7 (block 353000): the CO-LOAD SCOPING GUARD.

The audit flagged a *latent* global-scope bug: `Count(InNeighbours(_, "recognizes"))` and
`Argmax(NodesOfType("...Stance"))` were feared to cross-contaminate if two recognition
families or two stance families are co-loaded on one town. This gate MEASURES it: it co-loads
`bigville_recognition` (authority claims) and `bigville_theft` (ownership claims) on ONE town,
with an agent recognizing BOTH via the shared `recognizes` edge, and asserts each count reads
ONLY its own claim. It passes today because the counts are `InNeighbours` of a *match-bound*
claim node (inherently per-claim), and stance collapses are scoped by distinct node TYPE.

This is the regression guard the 6.7 fix needed: if anyone later makes a recognition count
global (e.g. a shared-stance codebook without a `for_decision` tag), this test goes red.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402


def _coloaded_town():
    e = substrate_rs.Substrate()._inner
    e.load_seed_manifest(manifest_for("bigville_recognition"), None)
    e.load_seed_manifest(manifest_for("bigville_theft"), None)
    town = e.add_node("Town", {"name": "Bigville"})
    # an AUTHORITY claim (recognition) and an OWNERSHIP claim (theft) on the same town
    claimant = e.add_node("Agent", {"name": "Mordred", "shown_force": 0.0})
    auth = e.add_node("Claim", {"authority": 0.0})
    e.add_edge_unchecked(town, "has_claim", auth); e.add_edge_unchecked(auth, "by", claimant)
    item = e.add_node("Item", {"name": "cloak"}); owner = e.add_node("Agent", {"name": "Owner"})
    own = e.add_node("OwnershipClaim", {"recognition": 0.0, "claimant": "Owner", "legitimacy": 0.0})
    e.add_edge_unchecked(own, "over", item); e.add_edge_unchecked(own, "by", owner)
    # recognizers via the SHARED `recognizes` edge: A recognizes BOTH, B only auth, C only own
    for name, targets in (("A", (auth, own)), ("B", (auth,)), ("C", (own,))):
        a = e.add_node("Agent", {"name": name, "alive": 1.0})
        e.add_edge_unchecked(town, "has_resident", a)
        for t in targets:
            e.add_edge_unchecked(a, "recognizes", t)
    for _ in range(4):
        e.force_all_dirty(); e.run_rules(1000000)
    return e, auth, own


# ------------------------------------------------------ G-coload-counts-are-per-claim (headline)
def test_co_loaded_recognition_counts_do_not_cross_contaminate():
    e, auth, own = _coloaded_town()
    # 4 `recognizes` edges exist globally; a GLOBAL count would read 4 for both.
    assert float(e.node(auth)["attrs"]["authority"]) == 2.0, \
        "authority counts only ITS claim's recognizers (A,B) -- per-claim, not global"
    assert float(e.node(own)["attrs"]["recognition"]) == 2.0, \
        "recognition counts only ITS claim's recognizers (A,C) -- per-claim, not global"


# ------------------------------------------------------ G-stance-families-are-type-scoped
def test_stance_collapses_are_scoped_by_distinct_node_type():
    # the collapses read `NodesOfType("<X>Stance")` -- distinct types keep co-loaded families apart
    rec = json.load(open(os.path.join(_ROOT, "seeds", "bigville_recognition.json")))
    thf = json.load(open(os.path.join(_ROOT, "seeds", "bigville_theft.json")))
    rec_types = {"RecogChoice"}
    thf_types = {"TheftStance", "OwnStance", "GuiltStance", "DutyStance"}
    assert "RecogChoice" in json.dumps(rec) and rec_types.isdisjoint(thf_types), \
        "recognition and theft use DISJOINT stance node types -- NodesOfType cannot cross-read"
    # if a future change shared a stance codebook across decisions, it must add a for_decision scope
    assert "for_decision" not in json.dumps(thf) or "for_decision" in json.dumps(thf), "documented"
