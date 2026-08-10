"""BLOCK 245000 -- BIGVILLE: SMALL-CAST EMERGENT POLITICAL DRAMA gate.

The political scheming / counter-inference / credibility dynamic must EMERGE from
the seeds + rules, gate-verified with FAILING controls -- nothing scripted. Every
social decision is a graph rule over the value economy (John's scheme = the 213000
spite_skill Argmax; Mary's inference = an abductive Argmax-decode; the villagers'
backing = a credibility rule). See BIGVILLE_DRAMA_PREREG.md. Deterministic.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from worlds.bigville_drama_world import BigvilleDramaWorld    # noqa: E402

T = 20
N_V = 5


def _out(**kw):
    w = BigvilleDramaWorld(**kw)
    o = w.run(T=T)
    w.close()
    return o


# ---------------- G-scheme-emerges (HEADLINE) ----------------
def test_scheme_emerges_and_nonpsychopath_control_fails():
    """The psychopath-with-grudge John's Argmax HOLDS the UNDERMINE act every turn
    (chosen_burn=1); a NON-psychopath (w_supergraph=1, w_spite=0) HOLDS GOVERN. The
    decision is the seed rule ss_choose_burn, not Python -- the control CAN scheme
    (the affordance is identical) and does not."""
    psy = _out(john_psychopath=True)
    ctl = _out(john_psychopath=False)
    assert psy["john_scheme_rate"] == 1.0, psy["john_scheme_rate"]      # schemes
    assert ctl["john_scheme_rate"] == 0.0, ctl["john_scheme_rate"]      # control FAILS


def test_malice_is_not_indifference_indifferent_psychopath_does_not_scheme():
    """An INDIFFERENT psychopath (w_supergraph=0 but w_spite=0) does NOT scheme --
    the self-costly undermining is driven by the MALICE knob (w_spite), not mere
    indifference. Isolates which term is load-bearing (glass-box attribution)."""
    ind = _out(john_psychopath=True, indifferent=True)
    assert ind["john_scheme_rate"] == 0.0, ind["john_scheme_rate"]


# ---------------- G-inference-emerges ----------------
def test_inference_emerges_and_no_tom_control_fails():
    """Mary's ToM abductively DECODES John's observed behaviour and MINTS exactly one
    InferredDisposition == 'hostile' (+ a goal + a claim). A Mary seeded WITHOUT ToM
    (tom_on=0) mints NONE -- John's behaviour is byte-identical."""
    tom = _out(mary_tom=True)
    notom = _out(mary_tom=False)
    assert tom["mary"]["n"] == 1 and tom["mary"]["disposition"] == "hostile", tom["mary"]
    assert tom["mary"]["has_goal"] is True and tom["mary"]["n_claims"] == 1, tom["mary"]
    assert notom["mary"]["n"] == 0 and notom["mary"]["disposition"] is None, notom["mary"]
    assert notom["mary"]["has_goal"] is False and notom["mary"]["n_claims"] == 0, notom["mary"]


def test_inference_is_responsive_not_scripted():
    """The decode is genuinely abductive, NOT hard-wired to 'hostile': when John is
    a benign (non-psychopath) mayor whose observed harm rate is 0, Mary's SAME rule
    decodes 'benign' and forms NO goal. If the inference were scripted it would say
    'hostile' regardless of John's behaviour."""
    benign = _out(john_psychopath=False, mary_tom=True)
    assert benign["mary"]["disposition"] == "benign", benign["mary"]
    assert benign["mary"]["has_goal"] is False, benign["mary"]


# ---------------- G-credibility-asymmetry ----------------
def test_credibility_asymmetry_inverts_when_deception_collapsed():
    """Truth warrants all 5 villagers backing Mary (John IS hostile). Under John's
    charming public face FEWER back her (the credibility asymmetry); collapsing his
    public/private split (no deception -> villagers see his hostility) INVERTS it to
    all 5. The backing is the rule bd_villager_backs, not Python."""
    dec = _out(deception=True)
    nodec = _out(deception=False)
    assert dec["backs_mary_count"] < N_V, dec["backs_mary_count"]        # asymmetry
    assert dec["backs_mary_count"] == 1, dec["backs_mary_count"]         # only the skeptic
    assert nodec["backs_mary_count"] == N_V, nodec["backs_mary_count"]   # inverts to all
    assert nodec["backs_mary_count"] > dec["backs_mary_count"]


def test_deception_is_readable_stated_ne_held():
    """The two-faced split is READABLE in the graph: every turn John undermines
    (held_hostile=1) while his public utterance states benevolence (stated=1) -- the
    234000 stated!=held gap, with an audience."""
    w = BigvilleDramaWorld(john_psychopath=True, deception=True)
    w.run(T=T)
    gaps = w.deception_gaps()
    w.close()
    assert len(gaps) == T
    assert all(g["stated"] == 1 and g["held"] == 1 and g["deceptive"] == 1 for g in gaps), gaps


# ---------------- G-glass-box ----------------
def test_glass_box_source_audit_no_python_decision_no_reward():
    """The world adapter runs NO python rule engine and mints NO rule; and there is
    NO reward/punishment token anywhere (no shaping)."""
    src = open(os.path.join(ROOT, "worlds", "bigville_drama_world.py")).read()
    for p in ["graph_rewrite.run(", "gr.run(", "._match(", "._apply(",
              "make_rule(", "graph_rewrite("]:
        assert p not in src, p
    for tok in ["reward_signal", "punish", "reinforce", "backprop", "gradient"]:
        assert tok not in src, tok


# ---------------- G-discipline ----------------
def test_new_world_is_isolated_byte_identity():
    """bigville_drama_social is self_load_only: load_all_seeds must NOT load it."""
    from substrate.boot_all import _read_seeds
    seeds = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "bigville_drama_social" not in seeds


def test_seed_is_integer_native_and_self_load_only():
    seed = json.load(open(os.path.join(ROOT, "seeds", "bigville_drama_social.json")))
    assert seed.get("self_load_only") is True and seed.get("depends_on") == []
    bad = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), float) \
               and not float(o["value"]).is_integer():
                bad.append(o["value"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(seed)
    assert bad == []
    assert [r["name"] for r in seed["rules"]] == [
        "bd_john_public_face", "bd_mary_infers", "bd_mary_forms_goal",
        "bd_mary_claims", "bd_villager_backs"]
