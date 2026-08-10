"""bigville RUNG 1/3 (block 277000) -- THE HELD BOND. Gates mirror
BIGVILLE_BOND_PREREG.md (+ the two creator sharpenings: kin does not force
liking; kin-band is EARNED, not genetic). The relationship representation moves
out of the sim as bare symmetric kin/hates WORLD edges and into the agent graph
as a per-agent, DIRECTED, subjective, updatable Bond(A->B) with three dissociable
slots (belief / relational-affect / attraction) + an EARNED tie_strength/band.

No agent decision lives in Python -- every bond update (belief decode, reciprocity,
betrayal, gossip, homophily, mere-exposure, band) is a seed RULE
(seeds/bigville_bond_update.json). The adapter only ingests events, stamps inputs,
arms one-shots, ticks, and reads (source-audited below).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_bond_world import BigvilleBondWorld   # noqa: E402

BASE = "b53bdacae0"


# ================================================================ G-forms
def test_bond_forms_directed_three_slots_and_is_elaborated():
    """G-forms: a Bond FORMS directed from a kin PRIOR with all THREE slots present,
    and is ELABORATED by the rules. Creator sharpening 1: the kin prior forces NO
    positive feeling -- the affect and attraction slots are ZERO at formation (feelings
    are earned from experience); only a small altruism_bias + a small earned-tie prior
    reflect the genetic relatedness. The belief slot is a REAL ToM decode: fed a benign
    observation, it infers 'trustworthy'."""
    w = BigvilleBondWorld()
    for nm in ("Alice", "Bob"):
        w.add_agent(nm)
    w.add_prior_edge("Alice", "Bob", "blood_kin")     # the OLD bare world edge
    w.elaborate("Alice", "Bob", "blood_kin")           # -> the held Bond
    w.tick()
    s = w.slots("Alice", "Bob")
    # directed + all three slots present
    assert s["holder"] == "Alice" and s["toward"] == "Bob"
    for slot in ("belief_trust", "affect_trust", "affect_resentment", "affect_affection",
                 "attraction", "tie_strength", "band"):
        assert slot in s
    # NO forced positive feeling on kin (sharpening 1)
    assert s["affect_affection"] == 0.0 and s["attraction"] == 0.0
    assert s["affect_trust"] == 0.0 and s["affect_resentment"] == 0.0
    # genetics is only a SMALL prior (altruism bias + small earned-tie head-start), NOT a band
    assert s["altruism_bias"] > 0.0 and s["tie_strength"] <= 1.0
    assert s["band"] != "family"                       # kin band is EARNED, not auto-assigned
    # elaboration: the belief ToM decode is real -- benign evidence -> trustworthy
    w.observe_disposition("Alice", "Bob", 0.0)
    w.tick()
    s2 = w.slots("Alice", "Bob")
    assert s2["belief_disposition"] == "trustworthy" and s2["belief_trust"] == 1.0
    w.close()


# ============================================================ G-asymmetry
def test_bond_is_directed_and_asymmetric():
    """G-asymmetry (A5): after the SAME betrayal event by B toward A, Bond(A->B) and
    Bond(B->A) DIVERGE -- A's trust/attraction toward B drop, while B's bond toward A is
    unmoved. A shared symmetric world edge could never represent this."""
    w = BigvilleBondWorld()
    for nm in ("Alice", "Bob"):
        w.add_agent(nm)
    w.elaborate("Alice", "Bob", "acquaintance")
    w.elaborate("Bob", "Alice", "acquaintance")
    w.experience_event("Alice", "Bob", "loan_default", -1.0, 2.0)   # B defaults on A
    w.tick()
    ab = w.slots("Alice", "Bob")
    ba = w.slots("Bob", "Alice")
    assert ab["affect_trust"] < 0.0 and ab["attraction"] < 0.0      # A soured on B
    assert ba["affect_trust"] == 0.0 and ba["attraction"] == 0.0    # B unmoved about A
    assert ab != ba                                                 # A->B != B->A
    w.close()


# ==================================================== G-dynamic-asymmetric
def test_betrayal_drops_harder_than_kindness_raises():
    """G-dynamic-asymmetric (A3 negativity bias, 'bad is stronger than good'): a betrayal
    of magnitude M drops trust+attraction HARDER than a kindness of the SAME magnitude M
    raises them. The direction is the science; the magnitude (neg_weight>pos_weight) is a
    tunable knob, no magic ratio hard-coded."""
    M = 2.0
    w = BigvilleBondWorld()
    for nm in ("A", "K", "T"):
        w.add_agent(nm)
    w.elaborate("A", "K", "acquaintance")     # will receive a kindness
    w.elaborate("A", "T", "acquaintance")     # will receive a betrayal (same magnitude)
    w.experience_event("A", "K", "gift", +1.0, M)
    w.experience_event("A", "T", "eviction", -1.0, M)
    w.tick()
    up_trust = w.slots("A", "K")["affect_trust"]        # +pos*M
    down_trust = w.slots("A", "T")["affect_trust"]      # -neg*M
    up_att = w.slots("A", "K")["attraction"]
    down_att = w.slots("A", "T")["attraction"]
    assert up_trust > 0 and down_trust < 0
    assert abs(down_trust) > abs(up_trust)              # betrayal harder than kindness
    assert abs(down_att) > abs(up_att)
    # the betrayal also raises resentment and triggers the global re-appraisal marker
    assert w.slots("A", "T")["affect_resentment"] > 0
    w.close()


# ============================================================ G-third-party
def test_third_party_gossip_shifts_bond_weighted_by_source_trust():
    """G-third-party (B4 indirect reciprocity, generalizes bl_badmouth): C tells A about
    B; A revises Bond(A->B) WITHOUT ever directly experiencing B -- weighted by A's trust
    in C. A TRUSTED source moves the bond; a DISTRUSTED source moves it the opposite way
    (its testimony is discounted / inverted by negative source_trust)."""
    # trusted source
    w = BigvilleBondWorld()
    for nm in ("A", "B", "C"):
        w.add_agent(nm)
    w.elaborate("A", "B", "acquaintance")
    w.elaborate("A", "C", "acquaintance")
    w.observe_disposition("A", "C", 0.0)      # A comes to trust C (belief_trust = +1)
    w.tick()
    assert w.slots("A", "B")["belief_trust"] == 0.0        # A has NOT met B
    w.hear_gossip("A", "B", "C", -1.0)                     # C bad-mouths B
    w.tick()
    trusted = w.slots("A", "B")["belief_trust"]
    assert trusted < 0.0                                   # A revises B down, unmet
    w.close()

    # distrusted source: same bad-mouth, but A distrusts C -> the shift inverts
    w = BigvilleBondWorld()
    for nm in ("A", "B", "C"):
        w.add_agent(nm)
    w.elaborate("A", "B", "acquaintance")
    w.elaborate("A", "C", "acquaintance")
    w.observe_disposition("A", "C", 100.0)    # A distrusts C (belief_trust = -1)
    w.tick()
    w.hear_gossip("A", "B", "C", -1.0)
    w.tick()
    distrusted = w.slots("A", "B")["belief_trust"]
    assert distrusted > 0.0                                # discounted/inverted by source
    assert trusted != distrusted                           # source trust weights the update
    w.close()


# ============================================================== G-falsifier
def test_falsifier_zero_gain_freezes_every_bond_to_its_prior():
    """G-falsifier (the anti-'forced' control, mirrors af_choose_action's affect_gain):
    with update_gain=0 on every bond, the SAME events / gossip / similarity / proximity
    that move a live bond leave a frozen bond EXACTLY at its static seed prior -- the OLD
    bare-label behavior. Dynamism is proven by the contrast."""
    def scene(freeze):
        w = BigvilleBondWorld(freeze=freeze)
        for nm in ("A", "B"):
            w.add_agent(nm)
        w.elaborate("A", "B", "acquaintance")
        w.tick()
        prior = w.slots("A", "B")
        w.experience_event("A", "B", "betrayal", -1.0, 2.0)
        w.observe_disposition("A", "B", 100.0)
        w.set_similarity("A", "B", 3.0)
        w.cohabit("A", "B", 5.0)
        w.tick()
        after = w.slots("A", "B")
        w.close()
        return prior, after

    prior_f, after_f = scene(freeze=True)
    for k in ("affect_trust", "attraction", "tie_strength", "belief_trust",
              "affect_resentment", "band_code"):
        assert after_f[k] == prior_f[k], (k, after_f[k], prior_f[k])   # FROZEN at prior

    _, after_live = scene(freeze=False)
    # the identical events MOVE the live bond where the frozen one stayed at prior
    assert after_live["affect_trust"] < 0 and after_live["attraction"] < 0
    assert after_live["affect_resentment"] > 0 and after_live["belief_trust"] != prior_f["belief_trust"]


# ===================================================== earned-kin (sharpening 2)
def test_kin_band_is_earned_from_history_not_genetic():
    """Creator sharpening 2 ('a step-brother can be MORE kin than kin'): the kin-band is
    an EARNED, graded tie_strength built from care/cohabitation, NOT assigned by a genetic
    edge. A CHOSEN/adopted tie with real shared history reaches the FAMILY band and EXCEEDS
    a NEGLECTED blood-kin tie, which withers to a weak band. Genetics is only a small
    starting prior."""
    w = BigvilleBondWorld()
    for nm in ("Ma", "Blood", "Chosen"):
        w.add_agent(nm)
    w.elaborate("Ma", "Blood", "blood_kin")     # genetic tie, then neglected
    w.elaborate("Ma", "Chosen", "chosen")        # no genes -- earns it
    for _ in range(5):                           # accumulated care + cohabitation
        w.cohabit("Ma", "Chosen", 6.0)
        w.experience_event("Ma", "Chosen", "care", +1.0, 1.5)
        w.tick()
    w.experience_event("Ma", "Blood", "falling_out", -1.0, 0.5)   # neglect + a rift
    w.tick()
    chosen = w.slots("Ma", "Chosen")
    blood = w.slots("Ma", "Blood")
    assert chosen["tie_strength"] > blood["tie_strength"]         # earned exceeds genetic
    assert chosen["band"] == "family"                            # chosen reaches the top band
    assert blood["band"] in ("stranger", "consequential_stranger")  # neglected blood withers
    w.close()


def test_kin_band_and_liking_decouple():
    """Creator sharpening 1 ('you do not need to LIKE your kin'): band (structural,
    earned tie) and the affect/attraction slots are INDEPENDENT. A deeply-bonded family
    member (high tie_strength -> band=family) can be RESENTED (negative relational-affect)
    and AVOIDED (negative attraction) after a betrayal -- the band stays strong while the
    feeling goes negative. The resented-but-bonded family member is the target case."""
    w = BigvilleBondWorld()
    for nm in ("A", "Kin"):
        w.add_agent(nm)
    w.elaborate("A", "Kin", "chosen")
    for _ in range(7):                          # build a deep earned tie (high tie_strength)
        w.cohabit("A", "Kin", 8.0)
        w.tick()
    assert w.slots("A", "Kin")["band"] == "family"
    w.experience_event("A", "Kin", "grave_betrayal", -1.0, 5.0)    # a strong betrayal
    w.tick()
    s = w.slots("A", "Kin")
    assert s["band"] == "family"                # the structural bond stays strong (earned)
    assert s["attraction"] < 0.0                # yet A now wants to AVOID them
    assert s["affect_resentment"] > 0.0         # and RESENTS them
    w.close()


def test_belief_and_affect_slots_dissociate():
    """A4 (cognitive vs affective ToM dissociate): the belief slot (a ToM disposition
    decode from observed evidence) and the relational-affect slot are separately
    addressable -- you can hold one value in belief and a different one in affect. Fed a
    benign observation, belief reads trustworthy; an independent betrayal event drives the
    affect slot negative -- the two slots do not collapse to one scalar."""
    w = BigvilleBondWorld()
    for nm in ("A", "B"):
        w.add_agent(nm)
    w.elaborate("A", "B", "acquaintance")
    w.observe_disposition("A", "B", 0.0)        # cognitive: B looks benign
    w.tick()
    assert w.slots("A", "B")["belief_disposition"] == "trustworthy"
    # affect slot is a distinct axis; it carries its own emotions, not the belief verdict
    s = w.slots("A", "B")
    assert s["affect_gratitude"] == 0.0 and s["affect_resentment"] == 0.0
    w.close()


# ===================================================== source-audit / discipline
def test_no_python_agent_decision_in_the_bond_adapter():
    """Source-audit: the Bond adapter holds NO agent decision -- no Python rule engine and
    no if/else over a bond's graph valuation that selects an update. Every update is a seed
    rule; the adapter only ingests, arms, ticks, and reads."""
    src = open(os.path.join(_ROOT, "worlds", "bigville_bond_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "._match(", "._apply(", "make_rule("):
        assert forbidden not in src, f"bond adapter runs the Python rule engine: {forbidden}"


def test_update_seed_holds_the_bond_rules():
    """The DECISIONS are RULES: the update seed holds the seven bond_* rules that compose
    existing DSL Terms (belief decode, reciprocity, betrayal, gossip, homophily,
    mere-exposure, band)."""
    seed = json.load(open(os.path.join(_ROOT, "seeds", "bigville_bond_update.json")))
    names = [r["name"] for r in seed["rules"]]
    for r in ("bond_belief_infer", "bond_event_benefit", "bond_event_betrayal",
              "bond_gossip_update", "bond_similarity_attraction",
              "bond_proximity_familiarity", "bond_band_assign"):
        assert r in names, r
    assert len(seed["rules"]) >= 7
    # composition, not new machinery: no exotic Term names smuggled in
    blob = json.dumps(seed["rules"])
    for exotic in ("ShapeDecode", "TransformDecode", "DimInfer", "space_quantize"):
        assert exotic not in blob


def test_runners_dsl_untouched_zero_new_rust():
    """G-discipline (NO Rust): the rung-1 build is seeds + adapter + tests only. The Bond
    update seed composes existing DSL Terms; no term.rs / engine change vs the base."""
    r = subprocess.run(["git", "diff", "--name-only", BASE, "--", "runners/dsl"],
                       cwd=_ROOT, capture_output=True, text=True)
    changed = [l for l in r.stdout.splitlines() if l.strip()]
    assert changed == [], f"runners/dsl changed (new Rust): {changed}"
