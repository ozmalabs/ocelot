"""bigville R19 (block 267000) -- UTTERANCE LOUDNESS & the OBSERVE-vs-HEAR split.

Loudness parametrizes the EXISTING occlusion-gated earshot query (no new Rust);
two channels off one act (SIGHT delivers the communication ACT, HEARING inside
radius(L) delivers CONTENT); loudness = per-character seed axes (base/max) + a
decision_value choice capped at max; physical privacy corollary; a SCOPED
classroom-chatter proxy (R17/R18 acquisition coupling DEFERRED). Gates mirror
BIGVILLE_LOUD_PREREG.md. No agent decision lives in Python: every earshot /
observe / loudness verdict is a rule (source-audit test below).
"""
from __future__ import annotations

import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT,):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_loud_world import BigvilleLoudWorld            # noqa: E402

# Row y=8 is an open east-west PATH (no occluders) -> geometry isolates loudness.
SPK = (14, 8)
RING = [1, 2, 4, 6, 8, 12]


def _ring_world(base=6.0, mx=20.0):
    w = BigvilleLoudWorld()
    w.add_person("spk", SPK, base_loudness=base, max_loudness=mx)
    for d in RING:
        w.add_person("h%d" % d, (14 + d, 8))
    return w


def _heard(res):
    return [d for d in RING if res["receptions"]["h%d" % d]["got_content"]]


# ---------------------------------------------------- G-loudness-sets-hearing-radius
def test_loudness_sets_hearing_radius():
    """CONTENT reaches only hearers within radius(L); the received set is monotone
    non-decreasing in L; a whisper reaches ~no one, a shout reaches the row."""
    heard_by_L = {}
    for L in (1, 3, 6, 12):
        w = _ring_world()
        res = w.speak("spk", "all", chosen_loudness=L)
        assert res["eff_loudness"] == L, res         # loudness IS the radius
        heard_by_L[L] = _heard(res)
        w.close()
    assert heard_by_L[1] == [1], heard_by_L          # whisper -> nearest only
    assert heard_by_L[12] == RING, heard_by_L        # shout -> the whole row
    # monotone non-decreasing received-set as L grows
    Ls = [1, 3, 6, 12]
    for i in range(len(Ls) - 1):
        lo, hi = set(heard_by_L[Ls[i]]), set(heard_by_L[Ls[i + 1]])
        assert lo <= hi, (heard_by_L, Ls[i], Ls[i + 1])
    assert len(heard_by_L[1]) < len(heard_by_L[12])  # strictly grows overall


def test_control_loudness_ablated_flat_earshot():
    """Failing control: ablate loudness (loudness_on=0) -> every utterance uses the
    SAME FLAT radius, so the received-set is INDEPENDENT of L (flat earshot = the
    pre-change baseline). Loudness is load-bearing for the radius."""
    sets = []
    for L in (1, 3, 6, 12):
        w = _ring_world()
        res = w.speak("spk", "all", chosen_loudness=L, loudness_on=0)
        assert res["eff_loudness"] == w.flat_radius, res
        sets.append(tuple(_heard(res)))
        w.close()
    assert len(set(sets)) == 1, sets                 # identical regardless of L
    # and it is NOT the loudness-on behaviour (which varied whisper->shout)
    assert sets[0] == (1, 2, 4, 6), sets


# ---------------------------------------------------- G-observe-vs-hear-split (HEADLINE)
def test_observe_vs_hear_split():
    """A witness with LINE OF SIGHT to a WHISPERED exchange mints the COMMUNICATION
    ACT (observed_act==1) but ingests NO content (got_content==0); the SAME witness
    inside radius(L) ingests the content too. Knowing-a-conversation-happens is a
    SEPARATE fact from knowing-what-was-said."""
    w = BigvilleLoudWorld()
    w.add_person("spk", SPK)
    w.add_person("near", (15, 8))       # d1, inside whisper radius
    w.add_person("witness", (19, 8))    # d5, within sight (7), clear LOS, > radius
    res = w.speak("spk", "near", chosen_loudness=1)
    near, wit = res["receptions"]["near"], res["receptions"]["witness"]
    w.close()
    # HEADLINE: the distant witness SEES the act but does not HEAR the content.
    assert wit["observed_act"] == 1 and wit["got_content"] == 0, wit
    # CONTROL: the near hearer gets BOTH.
    assert near["observed_act"] == 1 and near["got_content"] == 1, near


def test_observe_vs_hear_control_move_into_radius():
    """Control arm of the split: move the SAME witness inside radius(L) and it now
    ingests content (the split is a function of DISTANCE vs loudness, not identity)."""
    def witness_at(x):
        w = BigvilleLoudWorld()
        w.add_person("spk", SPK)
        w.add_person("wit", (x, 8))
        r = w.speak("spk", "wit", chosen_loudness=3)["receptions"]["wit"]  # radius 3
        w.close()
        return r
    far = witness_at(19)     # d5 > 3
    near = witness_at(16)    # d2 <= 3
    assert far["observed_act"] == 1 and far["got_content"] == 0, far
    assert near["observed_act"] == 1 and near["got_content"] == 1, near


def test_commact_node_is_minted_graph_native():
    """The communication ACT is a real graph node the witness holds: lo_observe_act
    mints a CommAct and edges witness -observes-> ca (glass-box, not a Python flag).
    Verified by inspecting the substrate mid-utterance (no purge)."""
    w = BigvilleLoudWorld()
    w.add_person("spk", SPK)
    w.add_person("wit", (19, 8))
    spk, wit = w.people["spk"], w.people["wit"]
    u = w.eng.add_node("Utterance", {
        "speaker": "spk", "addressee": "wit", "chosen_loudness": 1.0,
        "choice_on": 1.0, "loudness_on": 1.0, "is_control": 0.0,
        "base_loudness": 6.0, "max_loudness": 12.0, "flat_radius": 6.0,
        "eff_loudness": 0.0})
    w.eng.add_edge_unchecked(u, "spoken_by", spk)
    r = w.eng.add_node("Reception", {
        "dist": 5.0, "sight_occluded": 0.0, "hear_occluded": 0.0,
        "got_content": 0.0, "observed_act": 0.0, "speaker": "spk",
        "addressee": "wit", "perceiver": "wit"})
    w.eng.add_edge_unchecked(u, "reception", r)
    w.eng.add_edge_unchecked(r, "to", wit)
    w.eng.run_rules(1000000)
    acts = list(w.eng.neighbours(wit, "observes"))
    assert len(acts) == 1, "witness must hold exactly one minted CommAct"
    assert w.eng.node(acts[0])["type"] == "CommAct"
    assert int(w.eng.node(r)["attrs"]["got_content"]) == 0   # sight only, no content
    w.close()


# ---------------------------------------------------- G-loudness-is-seed-plus-choice
def _eff(w, spk, **kw):
    return w.speak(spk, "x", hearers=["dummy"], **kw)["eff_loudness"]


def test_loudness_is_seed_plus_choice():
    """BASE + MAX are per-character seed axes; actual loudness is a decision_value
    in [0, max] -- a chosen whisper is low, a chosen shout is capped at that
    character's OWN max (no ceiling break); ablate the choice -> base."""
    w = BigvilleLoudWorld()
    w.add_person("child", (14, 8), base_loudness=3.0, max_loudness=5.0)
    w.add_person("pub", (2, 8), base_loudness=8.0, max_loudness=15.0)
    w.add_person("dummy", (14, 8))
    # whisper < normal < shout, per character
    assert _eff(w, "child", chosen_loudness=1) == 1
    assert _eff(w, "child", chosen_loudness=100) == 5    # capped at child's max
    assert _eff(w, "pub", chosen_loudness=1) == 1
    assert _eff(w, "pub", chosen_loudness=100) == 15     # capped at publican's max
    # no one exceeds their ceiling: the child SHOUTING (5) still carries less far
    # than the publican speaking NORMALLY (8).
    child_shout = _eff(w, "child", chosen_loudness=100)
    pub_normal = _eff(w, "pub", chosen_loudness=8)
    assert child_shout < pub_normal, (child_shout, pub_normal)
    # ablate the choice -> the seed base (population variation preserved)
    assert _eff(w, "child", choice_on=0) == 3
    assert _eff(w, "pub", choice_on=0) == 8
    w.close()


# ---------------------------------------------------- G-privacy-is-physical
def test_privacy_is_physical():
    """Counsel spoken QUIETLY does not leak to a witness who only SEES the meeting:
    the witness mints the CommAct (sees) but got_content==0 -- privacy is a PHYSICAL
    fact of the hearing model (low loudness), not an honour promise. A confidant
    within whisper radius hears it. Secrecy and private counsel are the SAME
    intent-neutral primitive."""
    w = BigvilleLoudWorld()
    w.add_person("mary", SPK, base_loudness=6.0, max_loudness=12.0)
    w.add_person("confidant", (15, 8))    # d1, in the huddle
    w.add_person("witness", (17, 8))      # d3, sees the meeting, out of whisper radius
    res = w.speak("mary", "confidant", chosen_loudness=1)   # a whisper
    conf, wit = res["receptions"]["confidant"], res["receptions"]["witness"]
    w.close()
    assert wit["observed_act"] == 1 and wit["got_content"] == 0, wit   # sees, not hears
    assert conf["got_content"] == 1, conf                              # confidant hears


# ---------------------------------------------------- G-classroom-chatter (SCOPED proxy)
CHILDREN = ["c0", "c1", "c2", "c3"]


def _classroom():
    w = BigvilleLoudWorld()
    w.add_person("teacher", (14, 6), base_loudness=8.0, max_loudness=15.0, peer_pull=0.0)
    for i, x in enumerate((13, 14, 15, 16)):
        w.add_person(CHILDREN[i], (x, 8), base_loudness=3.0, max_loudness=5.0, peer_pull=1.0)
    return w


def _chatter(w):
    """Each child whispers peer chatter; content carries child<->adjacent child but
    NOT to the teacher (whisper radius 1 < the teacher's distance). Returns the
    teacher's reception of the last chatter utterance."""
    last = None
    for c in CHILDREN:
        others = [n for n in CHILDREN if n != c] + ["teacher"]
        last = w.speak(c, "peers", chosen_loudness=1, is_control=0,
                       hearers=others)["receptions"]["teacher"]
    return last


def test_classroom_chatter_observe_not_hear_and_control_restores():
    """The loudness-specific classroom dynamic (attention is a SCOPED proxy;
    acquisition DEFERRED to R18): children whisper -> distracted (attending 0);
    the teacher OBSERVES the chatter by line of sight (observed_act==1) but ingests
    NO content (got_content==0); the teacher's HIGH-loudness control CARRIES to the
    room -> attention returns (attending 1)."""
    w = _classroom()
    teacher_on_chatter = _chatter(w)
    # teacher sees the chatter but cannot hear its content
    assert teacher_on_chatter["observed_act"] == 1, teacher_on_chatter
    assert teacher_on_chatter["got_content"] == 0, teacher_on_chatter
    # every child is now distracted (received a peer whisper)
    assert all(w.attending_of(c) == 0.0 for c in CHILDREN), \
        {c: w.attending_of(c) for c in CHILDREN}
    # the teacher SHOUTS a control utterance -> it carries -> attention returns
    r = w.speak("teacher", "class", chosen_loudness=12, is_control=1, hearers=CHILDREN)
    assert all(r["receptions"][c]["got_content"] == 1 for c in CHILDREN), r
    assert all(w.attending_of(c) == 1.0 for c in CHILDREN), \
        {c: w.attending_of(c) for c in CHILDREN}
    w.close()


def test_control_classroom_ablated_teacher_control_chatter_persists():
    """Failing control: ablate the teacher's control (whisper instead of shout) ->
    it does NOT carry to the distracted children -> attention stays scattered
    (chatter persists). The teacher's LOUDNESS is load-bearing for classroom
    management -- the management EMERGES from the loudness model, it is not scripted."""
    w = _classroom()
    _chatter(w)
    assert all(w.attending_of(c) == 0.0 for c in CHILDREN)
    r = w.speak("teacher", "class", chosen_loudness=1, is_control=1, hearers=CHILDREN)
    assert all(r["receptions"][c]["got_content"] == 0 for c in CHILDREN), r
    assert all(w.attending_of(c) == 0.0 for c in CHILDREN), \
        {c: w.attending_of(c) for c in CHILDREN}
    w.close()


# ---------------------------------------------------- discipline / source-audit
def test_loudness_decisions_are_rules_not_python():
    """Source-audit: the world adapter runs NO rule engine and holds no earshot /
    observe / loudness decision; the decisions live in the two seeds."""
    wf = open(os.path.join(_ROOT, "worlds", "bigville_loud_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "gr._match", "gr._apply"):
        assert forbidden not in wf, f"world adapter calls a rule engine: {forbidden}"
    comm = json.load(open(os.path.join(_ROOT, "seeds", "bigville_loud_comm.json")))
    cls = json.load(open(os.path.join(_ROOT, "seeds", "bigville_loud_class.json")))
    names = {r["name"] for r in comm["rules"]} | {r["name"] for r in cls["rules"]}
    assert {"lo_choose_loudness", "lo_deliver_content", "lo_observe_act",
            "lo_chatter_distracts", "lo_control_restores"} <= names, names
    # both seeds are self_load_only (never auto-loaded into the default agent)
    assert comm.get("self_load_only") is True and cls.get("self_load_only") is True


def test_no_new_rust_and_engine_invariant():
    """No new Rust primitive: both seeds compose existing DSL Terms only. And the
    engine provenance asserts the INVARIANT (source_match in {own, shared}) -- never
    a pinned md5 (lesson 7b)."""
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    used = set()
    for seed in ("bigville_loud_comm", "bigville_loud_class"):
        d = json.load(open(os.path.join(_ROOT, "seeds", seed + ".json")))
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "Max", "Lt", "Lte",
             "Gte", "Eq", "Gt", "And", "Or", "Not", "IfThenElse", "Argmin",
             "Argmax", "Neighbours", "Exists"}
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"
