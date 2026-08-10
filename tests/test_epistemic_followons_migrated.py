"""THREE FOLLOW-ON READS on the epistemic-gap humility architecture (recorded
creator refinements), each ADDING a distinction WITHOUT weakening any guardrail:

  A. BASELINE-DECEPTION PRIOR — deception is the ASSUMED NORM for some actor
     classes (advertiser / politician / pr / corporation). A teachable
     `ClassBaseline` codebook + a world-supplied `ActorClassFact` shift the STARTING
     lean toward deception. GUARDRAIL (the moral asymmetry, PRIOR-not-conviction):
     the prior is NOT per-act evidence -- it can shift the undetermined<->weak
     boundary WHEN a real structural signal is present, but ALONE it can NEVER reach
     a deception band, and NEVER a confident (strong) deception verdict. The baseline
     ADD is the COMBINE rung (the decision lives in the graph Term).

  B. LEGAL_HEDGING is NOT deception — a DISTINCT verdict. Lawyer-approved
     weasel-words ("may contribute to", "is designed to", ...) are a
     liability-minimising register everyone reads as such -- a forced choice whose
     forcing is LEGAL and MUTUALLY UNDERSTOOD. The AGENT AUTHORS the classify-by-join
     detection rule ITSELF (synth_classify_legal_hedging_reading, no shipped rule);
     the COMBINE routes it to the `legal_hedging` band -- UNLESS a real
     structural_forcing money/power signal is present, which DOMINATES (deception).

  C. NON_INSTRUMENTAL_DECEPTION (the compulsive anomaly). A divergence with NO
     ForcedChoiceExpectation match, NO measurable stakes, and no legal-hedge
     explanation is deception-shaped but has NO instrumental explanation -- the
     ABSENCE of a stakes-fit is itself the signal, pointing to a non-strategic cause
     (compulsion / identity). The COMBINE routes it to `non_instrumental`, DISTINCT
     from a bare no-model UNDETERMINED (which has no divergence at all), and NEVER
     labelled deception.

Every EXISTING guardrail is kept: never 'certain'; residual_other_mass > 0 always;
stylistic ~0 for deception; the moral asymmetry; the existing 18 epistemic-gap
tests stay green (the combine changes are additive/byte-compatible). The two new
bands (legal_hedging, non_instrumental) are ADDITIONS, not reinterpretations of the
existing 5 verdicts.

donkey=0: OZMA_NO_LLM=1, no model anywhere, no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_epistemic_followons_migrated.py -p no:randomly -q
"""
import json
import os
from pathlib import Path

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import procedural_reader as pr
from domains import binding_resolver as br
from domains import method_synthesis as ms
from domains import actor_goals as ag
from domains import reading_collapse as rc
from domains import dictionary_lexicon as dl


# The plain method the agent reads for FOLLOW-ON B — ordinary English, NO rule syntax.
LEGAL_HEDGE_METHOD = ("When an utterance phrase's phrase matches a legal hedging cue's "
                      "phrase, classify a legal hedging reading.")


def _agent():
    dl.warm_wordnet("en")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _fc(actor_type):
    return [r for r in ag.FORCED_CHOICE_CODEBOOK if r["actor_type"] == actor_type]


def _author_legal_hedging(a, *, install=True):
    """The agent authors the legal-hedging detection rule from the plain method + its
    grounded binding (its OWN classify-by-join faculty)."""
    model = pr.read_method(a, LEGAL_HEDGE_METHOD, name="legal_hedging_reading")
    gb = br.derive_binding(a, model)
    res = ms.synthesise_rule_from_method(a, model, gb["binding"], install=install)
    return model, gb, res


def _no_certainty(r):
    """Every verdict is a REVISABLE belief: no band is 'certain', and the
    residual_other_mass (the interval half-width) is strictly > 0 ALWAYS."""
    assert r["verdict"] != "certain", r
    assert not str(r["verdict"]).endswith("certain"), r
    assert r["residual_other_mass"] > 0.0, r
    assert r["revisable"] == 1.0, r
    lo, hi = r["interval"]
    assert hi > lo, r["interval"]


def _no_shipped_rule_minting(node_type):
    """No seed file may ship a rule that mints `node_type` (proving the ONLY such
    rule is the one the agent authored)."""
    seeds = Path(__file__).resolve().parent.parent / "seeds"
    for p in seeds.glob("*.json"):
        try:
            m = json.loads(p.read_text())
        except Exception:
            continue
        for r in m.get("rules", []) or []:
            for eff in r.get("effects", []) or []:
                if isinstance(eff, list) and len(eff) >= 3 and \
                        eff[0] == "add_node" and eff[2] == node_type:
                    return False
    return True


# =========================================================================== #
#  FOLLOW-ON A — the BASELINE-DECEPTION PRIOR (COMBINE rung, PRIOR-not-conviction).
# =========================================================================== #
def test_baseline_prior_alone_never_reaches_a_deception_band():
    """A baseline-elevated class with NO structural signal shifts the START toward
    deception (lean_score > 0) but the verdict stays UNDETERMINED -- at most
    weak_deception/undetermined, NEVER strong. The prior is not evidence."""
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    ag.seed_class_baseline_codebook(a)
    ag.annotate_actor_class(a, "acme_ads", "advertiser")   # world-supplied class
    r = ag.assess_epistemic_lean(a)[0]

    assert r["verdict"] == "undetermined", r               # no structural signal -> undetermined
    assert r["verdict"] not in ("weak_deception", "strong_deception"), r
    assert r["lean_score"] > 0, ("the prior shifts the start toward deception", r)
    assert float(r["baseline_prior"]) == 0.2, r            # the advertiser prior applied
    _no_certainty(r)


# A mid-stakes forced choice: structural_forcing weight = 0.55 * 0.7 = 0.385, which
# is BELOW the deception weak-min (0.50) -> UNDETERMINED for a neutral actor. A
# corporation baseline (0.15) lifts D_eff to 0.535 -> weak_deception. The prior
# shifts the band UP by one, but the awareness gate keeps strong out of reach.
_MID_FCE = [{"actor_type": "acme_corp", "structural_interest": "profit",
             "forced_against": "clean_energy", "actor_can_introspect": 1.0, "stakes": 0.7}]
_MID_CLAUSE = "The clean energy project was funded by the acme corp."


def _structural_reading(a, forced_choices, clause):
    ag.seed_epistemic_codebook(a, forced_choices=forced_choices)
    rc.read_clause(a, clause, write=True)
    ag.annotate_forced_choice_probes(a)
    readings = ag.assess_epistemic_lean(a)
    assert len(readings) == 1, readings
    return readings[0]


def test_baseline_shifts_the_band_up_with_a_structural_signal_but_never_strong():
    """The SAME structural evidence reaches a HIGHER band for a baseline class than a
    neutral one (the prior shifts the start), yet the guardrail holds: it never
    reaches strong_deception."""
    a_neutral = _agent()
    r_neutral = _structural_reading(a_neutral, _MID_FCE, _MID_CLAUSE)
    assert r_neutral["verdict"] == "undetermined", r_neutral

    a_base = _agent()
    ag.seed_class_baseline_codebook(a_base)
    ag.annotate_actor_class(a_base, "acme_corp", "corporation")
    r_base = _structural_reading(a_base, _MID_FCE, _MID_CLAUSE)

    assert r_base["verdict"] == "weak_deception", r_base            # the prior lifted the band
    assert r_base["verdict"] != "strong_deception", r_base          # but never to strong
    assert r_base["lean_score"] > r_neutral["lean_score"], (r_base["lean_score"], r_neutral["lean_score"])
    _no_certainty(r_base)
    _no_certainty(r_neutral)


def test_baseline_cannot_manufacture_strong_deception():
    """Even a large taught baseline, with a real structural forcing signal but NO
    awareness signal, cannot reach strong_deception -- the coordination/awareness
    gate is untouched by the prior."""
    from domains.teach import teach
    a = _agent()
    ag.seed_class_baseline_codebook(a, rows=[{"actor_class": "corporation", "baseline_prior": 0.5}])
    ag.annotate_actor_class(a, "oil_company", "corporation")
    r = _structural_reading(a, _fc("oil_company"), "The renewable energy project was funded by the oil company.")
    # oil_company forcing weight 0.55 + prior 0.5 = 1.05 >= strong-min, BUT no awareness
    # signal exists, so strong_deception stays UNREACHABLE.
    assert r["verdict"] == "weak_deception", r
    assert r["verdict"] != "strong_deception", r
    _no_certainty(r)


# =========================================================================== #
#  FOLLOW-ON B — LEGAL_HEDGING (agent-authored detection + distinct band).
# =========================================================================== #
def _is_attr_of(x, var):
    return (isinstance(x, dict) and x.get("type") == "Attr"
            and isinstance(x.get("node"), dict)
            and x["node"].get("type") == "Var" and x["node"].get("name") == var)


def _flatten(where):
    out = []
    if not isinstance(where, dict):
        return out
    out.append(where)
    t = where.get("type")
    if t in ("And", "Or"):
        for it in where.get("items", []):
            out.extend(_flatten(it))
    elif t == "Not":
        out.extend(_flatten(where.get("arg")))
    elif t == "Exists":
        out.extend(_flatten(where.get("predicate")))
    return out


def _cross_var_eq_join(where, va, vb):
    for nd in _flatten(where):
        if nd.get("type") != "Eq":
            continue
        a, b = nd.get("a"), nd.get("b")
        if (_is_attr_of(a, va) and _is_attr_of(b, vb)) or (_is_attr_of(a, vb) and _is_attr_of(b, va)):
            return nd
    return None


def test_legal_hedging_detection_rule_is_agent_authored():
    """The legal-hedging detection rule is the SYNTHESISER's output from the READ
    method -- synth_classify_legal_hedging_reading, a classify-by-join over
    UtterancePhrase X LegalHedgingCue -- NOT hand-written, NOT shipped in any seed."""
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    ag.seed_legal_hedging_codebook(a)
    ag.annotate_utterance_phrases(a, "This may contribute to better health.")   # a fact to ground on

    model = pr.read_method(a, LEGAL_HEDGE_METHOD, name="legal_hedging_reading")
    trig = model["steps"][0]["trigger"]
    main = model["steps"][0]["main"]
    assert trig["kind"] == "join", trig
    assert trig["fact_type"] == "utterance phrase" and trig["fact_key"] == "phrase"
    assert trig["codebook_type"] == "legal hedging cue" and trig["codebook_key"] == "phrase"
    assert main["effect"] == "classify" and main["node_type"] == "legal hedging reading"

    gb = br.derive_binding(a, model)
    b = gb["binding"]
    assert b["fact_edge"] == "has_utterance_phrase", b
    assert b["codebook_edge"] == "has_legal_hedging_cue", b
    assert b["classification_edge"] == "has_legal_hedging_reading", b
    assert b["node_types"]["legal hedging reading"] == "LegalHedgingReading", b

    res = ms.synthesise_rule_from_method(a, model, b, install=False)
    assert not res.get("wall"), res
    rule = res["rules"][0]
    assert rule["name"] == "synth_classify_legal_hedging_reading", rule["name"]
    assert _no_shipped_rule_minting("LegalHedgingReading"), \
        "no seed file may ship a rule that mints LegalHedgingReading"

    assert rule["match"] == [["agent", "has_utterance_phrase", "f"],
                             ["agent", "has_legal_hedging_cue", "c"]], rule["match"]
    eqj = _cross_var_eq_join(rule["where"], "f", "c")
    assert eqj is not None, rule["where"]
    assert {eqj["a"]["key"], eqj["b"]["key"]} == {"phrase"}, eqj
    add_node = next(e for e in rule["effects"] if e[0] == "add_node")
    assert add_node[2] == "LegalHedgingReading", add_node


def test_pure_weasel_words_route_to_legal_hedging_not_deception():
    """Pure liability-forced weasel-words -> `legal_hedging`, a DISTINCT band -- NOT
    weak/strong_deception, NOT introspection-gap."""
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    ag.seed_legal_hedging_codebook(a)
    ag.annotate_utterance_phrases(a, "This supplement may contribute to better health and is designed to help.")
    _, _, res = _author_legal_hedging(a, install=True)
    assert not res.get("wall") and res.get("installed"), res

    r = ag.assess_epistemic_lean(a)[0]
    assert r["verdict"] == "legal_hedging", r
    assert r["verdict"] not in ("weak_deception", "strong_deception",
                                "weak_opacity", "strong_opacity"), r
    assert ag.held_legal_hedging_readings(a), "the agent-authored rule minted a reading"
    assert "liability-forced" in r["model_note"], r["model_note"]
    _no_certainty(r)


def test_structural_forcing_dominates_a_cooccurring_hedge():
    """A REAL money/power structural_forcing divergence is NOT downgraded to
    legal_hedging just because a hedge phrase co-occurs -- structural_forcing
    DOMINATES (-> deception)."""
    a = _agent()
    ag.seed_legal_hedging_codebook(a)
    ag.annotate_utterance_phrases(a, "The oil company says the fund may contribute to renewable energy.")
    ag.seed_epistemic_codebook(a, forced_choices=_fc("oil_company"))
    rc.read_clause(a, "The renewable energy project was funded by the oil company.", write=True)
    ag.annotate_forced_choice_probes(a)
    _, _, res = _author_legal_hedging(a, install=True)
    assert not res.get("wall") and res.get("installed"), res

    r = ag.assess_epistemic_lean(a)[0]
    assert r["verdict"] in ("weak_deception", "strong_deception"), r
    assert r["verdict"] != "legal_hedging", r
    assert r["model_based"] == 1.0, r
    # the hedge WAS detected -- it just does not win against a structural signal
    assert ag.held_legal_hedging_readings(a), "the hedge was still detected"
    _no_certainty(r)


# =========================================================================== #
#  FOLLOW-ON C — NON_INSTRUMENTAL (the compulsive anomaly).
# =========================================================================== #
def test_divergence_without_stakes_routes_to_non_instrumental():
    """A divergence with NO ForcedChoiceExpectation + NO stakes + no legal-hedge
    explanation -> `non_instrumental`: deception-shaped, but the absence of a
    stakes-fit points to a non-strategic cause. NEVER labelled deception."""
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])   # NO forced-choice model at all
    ag.annotate_divergence(a, detected=True)           # an explicit falsehood / mismatch marker
    r = ag.assess_epistemic_lean(a)[0]

    assert r["verdict"] == "non_instrumental", r
    assert r["verdict"] not in ("weak_deception", "strong_deception"), r
    assert r["residual_other_mass"] > 0, r
    assert "non-strategic" in r["model_note"].lower(), r["model_note"]
    _no_certainty(r)


def test_non_instrumental_is_distinct_from_bare_undetermined():
    """A bare no-model case with NO divergence at all stays UNDETERMINED (not
    non_instrumental) -- the DivergenceFact is what distinguishes the two."""
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    r = ag.assess_epistemic_lean(a)[0]
    assert r["verdict"] == "undetermined", r
    assert r["verdict"] != "non_instrumental", r
    _no_certainty(r)


def test_non_instrumental_from_a_held_conflicting_actor_goal():
    """The divergence annotator ALSO reads a held belief mechanically: an ActorGoal
    already carrying serves_conflicting_meta_goal==1.0 yields a DivergenceFact with
    no explicit marker -- and with no stakes model, routes to non_instrumental."""
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    # a held conflicting-meta-goal belief (as the single-act flag would mint)
    goal = a.s.add_node("ActorGoal", {"actor": "odd_actor", "agency": "author",
                                      "serves_conflicting_meta_goal": 1.0,
                                      "mechanism": "undetermined"})
    a.inner.add_edge_unchecked(a.agent, "has_actor_goal", goal)
    made = ag.annotate_divergence(a)                    # no explicit marker -> read the belief
    assert made is not None, "a held conflicting ActorGoal must yield a DivergenceFact"
    r = ag.assess_epistemic_lean(a)[0]
    assert r["verdict"] == "non_instrumental", r
    _no_certainty(r)


# =========================================================================== #
#  SOURCE AUDIT — no `import re`; the new annotators make no lean/routing decision
#  (the weights/routing live in the codebook + the combine Term, not the annotator).
# =========================================================================== #
def test_source_audit_no_regex_no_annotator_decision():
    src = (Path(__file__).resolve().parent.parent / "domains" / "actor_goals.py").read_text()
    for line in src.splitlines():
        s = line.strip()
        assert not (s == "import re" or s.startswith("import re ")
                    or s.startswith("import re,") or s.startswith("import re;")), line
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src

    # Python never mints the new verdict/reading types nor the codebook rows directly.
    assert 'add_node("LegalHedgingReading"' not in src   # only the AGENT-authored rule mints it
    assert 'add_node("ClassBaseline"' not in src         # only teach() adds codebook rows
    assert 'add_node("LegalHedgingCue"' not in src       # only teach() adds codebook rows

    # the ActorClassFact annotator records the WORLD-SUPPLIED class UNCONDITIONALLY,
    # independent of whether any ClassBaseline names it (no routing decision here).
    a1 = _agent()
    ag.seed_class_baseline_codebook(a1)
    n1 = ag.annotate_actor_class(a1, "x", "a_class_no_baseline_names")
    assert n1 is not None                                 # emitted despite no codebook match
    a2 = _agent()                                         # NO ClassBaseline taught at all
    n2 = ag.annotate_actor_class(a2, "x", "a_class_no_baseline_names")
    assert n2 is not None                                 # still emitted with no codebook

    # the generic UtterancePhrase annotator (reused for legal hedging) stays
    # codebook-independent: identical emission with or without the LegalHedgingCue codebook.
    a3 = _agent()
    m1 = len(ag.annotate_utterance_phrases(a3, "this is designed to help you up to a point"))
    a4 = _agent()
    ag.seed_legal_hedging_codebook(a4)
    m2 = len(ag.annotate_utterance_phrases(a4, "this is designed to help you up to a point"))
    assert m1 == m2 and m1 > 0, (m1, m2)


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
