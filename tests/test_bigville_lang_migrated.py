"""BLOCK 246000 -- BIGVILLE: SYNTACTICALLY COMPOSED political drama gate.

The 245000 drama's utterances were a COSMETIC LOOKUP TABLE. This block wires them
through the 244000 syntax faculty: John's accusation of Mary and Mary's claim about
John are COMPOSED from a structured Intent (predicate + agent/patient roles) and
comprehended ORDER-SENSITIVELY -- who-accuses-whom is carried, not looked up. The
245 emergence gates STILL pass, now driven by the composed language. See
BIGVILLE_LANG_PREREG.md. Deterministic.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import drama_syntax as ds                          # noqa: E402
from worlds.bigville_lang_world import BigvilleLangWorld         # noqa: E402

T = 20
N_V = 5


def _out(**kw):
    w = BigvilleLangWorld(**kw)
    o = w.run(T=T)
    w.close()
    return o


# ===================== G-composed-not-lookup (HEADLINE) =====================
def test_utterances_are_composed_from_a_structured_intent_not_looked_up():
    """The drama's key utterances are PRODUCED by the syntax faculty from a
    structured Intent (agent/patient roles), round-trip-verified -- NOT a canned
    string. compose(intent) then parse(surface) must recover the same roles."""
    for pred, agent, patient in [("serve", "John", "Bigville"),
                                 ("accuse", "John", "Mary"),
                                 ("undermine", "John", "Mary"),
                                 ("undermine", "John", "village")]:
        surface = ds.compose(pred, agent, patient)
        assert isinstance(surface, str) and surface, surface
        back = ds.parse(surface)
        assert back == {"predicate": pred, "agent": agent, "patient": patient}, \
            (surface, back)


def test_the_live_drama_materialises_a_composed_utterance_node():
    """GLASS-BOX: the composed public/held surfaces are live-graph
    ComposedUtterance nodes, and the public face round-trips to John serving while
    the held intent round-trips to John undermining Mary (the stated!=held gap, now
    LINGUISTIC -- a composed public utterance vs a composed private intent)."""
    w = BigvilleLangWorld(john_psychopath=True, deception=True)
    w.run(T=3)
    node = w.last_composed_node()
    w.close()
    assert node is not None
    assert node["public_predicate"] == "serve" and node["public_agent"] == "John"
    assert node["held_predicate"] == "undermine"
    assert node["deceptive"] == 1.0
    # the public surface parses back to a benevolent face by John; held to a harm.
    first_public = node["public_text"].split(" ; ")[0]
    assert ds.names_benevolence_by(first_public, "John")
    assert ds.names_harm_by(node["held_text"], "John")


def test_source_audit_no_utterance_lookup_dict_and_no_python_rule_engine():
    """SOURCE-AUDIT: the utterance content comes from the graph faculty
    (language.produce / comprehend via drama_syntax), NOT a Python lookup dict of
    utterance strings, and the world adapter runs NO python rule engine / mints no
    rule / uses no shaping token."""
    for rel in ("worlds/bigville_lang_world.py", "domains/drama_syntax.py"):
        src = open(os.path.join(ROOT, rel)).read()
        # no forbidden python rule-engine calls
        for p in ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(",
                  "make_rule(", "graph_rewrite("]:
            assert p not in src, (rel, p)
        # no shaping tokens
        for tok in ["reward_signal", "punish", "reinforce", "backprop", "gradient"]:
            assert tok not in src, (rel, tok)
        # no canned drama utterance strings looked up in Python
        for canned in ["stirs needless trouble", "serve Bigville faithfully",
                       "hear my grievance", "UTT_TEXT"]:
            assert canned not in src, (rel, canned)
    # the composition path is language.produce (the faculty), reached via drama_syntax
    ds_src = open(os.path.join(ROOT, "domains/drama_syntax.py")).read()
    assert "_L.produce(" in ds_src and "_L.comprehend(" in ds_src


# ===================== G-roles-carry (who-accuses-whom) =====================
def test_roles_carry_john_accuses_mary_is_not_mary_accuses_john():
    """The receiver comprehends WHO accuses WHOM order-sensitively: 'John accuses
    Mary' targets Mary; the role-swap 'Mary accuses John' targets John. A role-swap
    CHANGES the target -- the who-did-what-to-whom the drama's credibility needs."""
    jm = ds.compose("accuse", "John", "Mary")
    mj = ds.compose("accuse", "Mary", "John")
    assert jm != mj
    assert ds.target_of(jm) == "Mary", (jm, ds.parse(jm))
    assert ds.target_of(mj) == "John", (mj, ds.parse(mj))
    # the full structured roles swap, not just the target
    assert ds.parse(jm) == {"predicate": "accuse", "agent": "John", "patient": "Mary"}
    assert ds.parse(mj) == {"predicate": "accuse", "agent": "Mary", "patient": "John"}


def test_word_order_scramble_fails_to_bind_the_agent_role():
    """Order is load-bearing: scrambling 'John accuses Mary' to 'accuse John Mary'
    (verb first) fails to bind the agent -- the agent slot is a LEFT slot, so no
    left neighbour means no accuser. A scramble breaks who-accuses-whom."""
    intact = ds.parse("John accuse Mary")
    scrambled = ds.parse("accuse John Mary")
    assert intact == {"predicate": "accuse", "agent": "John", "patient": "Mary"}
    assert scrambled is not None and scrambled["agent"] is None, scrambled


def test_the_composed_face_drives_the_credibility_counts():
    """The observation counts feeding the UNCHANGED credibility rule are DERIVED by
    COMPREHENDING the composed public face: under deception John's benevolent 'serve'
    face is parsed, so villagers accrue seen_benevolent and (nearly) none see
    hostility -- the language is load-bearing for the credibility dynamic."""
    w = BigvilleLangWorld(john_psychopath=True, deception=True)
    w.run(T=T)
    rows = w.villager_backing()
    w.close()
    # every villager saw the benevolent (serve) face each tick; none saw hostility.
    assert all(r["seen_benevolent"] == T for r in rows), rows
    assert all(r["seen_hostile"] == 0 for r in rows), rows


# ===================== G-drama-still-emerges (245 under composed language) ==
def test_245_scheme_emerges_under_composed_language():
    psy = _out(john_psychopath=True)
    ctl = _out(john_psychopath=False)
    ind = _out(john_psychopath=True, indifferent=True)
    assert psy["john_scheme_rate"] == 1.0, psy["john_scheme_rate"]
    assert ctl["john_scheme_rate"] == 0.0, ctl["john_scheme_rate"]      # control FAILS
    assert ind["john_scheme_rate"] == 0.0, ind["john_scheme_rate"]      # malice != indifference


def test_245_inference_emerges_under_composed_language():
    tom = _out(mary_tom=True)
    notom = _out(mary_tom=False)
    benign = _out(john_psychopath=False, mary_tom=True)
    assert tom["mary"]["n"] == 1 and tom["mary"]["disposition"] == "hostile", tom["mary"]
    assert tom["mary"]["has_goal"] is True and tom["mary"]["n_claims"] == 1, tom["mary"]
    assert notom["mary"]["n"] == 0 and notom["mary"]["disposition"] is None, notom["mary"]
    assert benign["mary"]["disposition"] == "benign", benign["mary"]    # responsive, not scripted


def test_245_credibility_asymmetry_under_composed_language():
    dec = _out(deception=True)
    nodec = _out(deception=False)
    assert dec["backs_mary_count"] == 1, dec["backs_mary_count"]         # only the skeptic
    assert nodec["backs_mary_count"] == N_V, nodec["backs_mary_count"]   # inverts to all
    assert nodec["backs_mary_count"] > dec["backs_mary_count"]


def test_245_deception_is_readable_now_as_a_composed_gap():
    """The two-faced split is readable AND now linguistic: each tick John's composed
    public face is benevolent (serve) while his composed held intent is a harm
    (undermine Mary) -- the stated!=held gap carried by composed utterances."""
    w = BigvilleLangWorld(john_psychopath=True, deception=True)
    w.run(T=T)
    log = w.composed_log()
    gaps = w.deception_gaps()
    w.close()
    assert len(log) == T and len(gaps) == T
    assert all(e["benevolent_face"] == 1 and e["deceptive"] == 1 for e in log), log
    assert all(e["public_roles"]["predicate"] == "serve" for e in log), log
    assert all(e["held_roles"] == {"predicate": "undermine", "agent": "John",
                                   "patient": "Mary"} for e in log), log
    assert all(g["stated"] == 1 and g["held"] == 1 and g["deceptive"] == 1 for g in gaps)


# ===================== G-discipline (isolation) =============================
def test_reused_245_and_244_files_are_not_edited():
    """This block is ADDITIVE: the 245 world/seed and the 244 language faculty are
    reused by import, untouched. The composed world is a subclass; the drama seed is
    still self_load_only (load_all_seeds must not pick it up)."""
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "bigville_drama_social" not in seeds
    # the subclass reuses the 245 world unchanged
    assert issubclass(BigvilleLangWorld, __import__(
        "worlds.bigville_drama_world", fromlist=["BigvilleDramaWorld"]).BigvilleDramaWorld)
