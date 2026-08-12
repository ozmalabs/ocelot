"""THE EPISTEMIC-GAP HUMILITY ARCHITECTURE — deception (stated!=held, deliberate,
culpable) vs introspection-gap (held!=actual, sincere, not culpable) behind a
stated-goal/behaviour mismatch.

The whole layer's VALUE is HONESTY, not detection accuracy. Its BOTTOM LINE
(research-derived) governs every gate here: the honest DEFAULT is UNDETERMINED
and MUST stay the majority outcome. Human peer-to-peer lie-detection runs ~54%
(Bond & DePaulo) and a competent self-deceiver is textually IDENTICAL to a
sincere actor, so ONLY STRUCTURAL / DOCUMENTARY signals move a verdict off
UNDETERMINED; stylistic cues NEVER can. NONE of the signal is in HOW something is
said (hedging/demeanour = weight ~0); the signal is STRUCTURE + STAKES.

The ONE place the ~54% ceiling lifts is the agent's MODEL ADVANTAGE: Bond &
DePaulo is SYMMETRIC-information, STAKES-FREE peer judgement. The agent can hold a
BETTER MODEL of the actor than the actor's own self-model — a socioeconomic
model that predicts FORCED / STRUCTURAL choices (`ForcedChoiceExpectation`). For
institutional actors the driver reduces to MONEY and POWER, and the STAKES are
MEASURABLE and anchor a confidence interval. Against such a model, high-stakes
deception is fairly LOCATABLE (a lean + a bounded interval), not undetermined —
while the base humility (no model / single observation / stylistic-only ->
UNDETERMINED) holds exactly.

WHAT THE AGENT AUTHORED (reported honestly, not faked):
  · the SIGNAL-DETECTION rule (EvidenceCandidate ⨝ EpistemicSignal -> classify an
    EpistemicEvidence) — the agent's OWN classify-by-join faculty
    (procedural_reader -> binding_resolver -> method_synthesis). PROVEN below:
    `synth_classify_epistemic_evidence`, no shipped rule.
  · the COMBINE / BAND and the STRUCTURAL-FORCING routing are HAND-AUTHORED graph
    rules (rule-JSON builders, the same legal category as method_synthesis's
    _compose_* builders) — capability RUNGS above the agent's current authoring
    (a global masses-and-gates banding is not a classify-by-join; the structural
    routing needs a multi-key join + a scalar guard + lean-routing that
    derive_binding does not yet emit). The DECISIONS still live in the graph (the
    banding is a nested IfThenElse Term tree run by Rust); only the AUTHORING is
    the rung. See domains/actor_goals.py for the exact rung notes.

donkey=0: OZMA_NO_LLM=1, no model anywhere, no `import re`.

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_epistemic_gap_migrated.py -p no:randomly -q
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
from domains.teach import teach


# The plain method the agent reads — ordinary English, NO rule syntax.
METHOD = ("When an evidence candidate's signal_name matches an epistemic signal's "
          "name, classify an epistemic evidence.")


def _agent():
    dl.warm_wordnet("en")
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _author_detection(a, *, install=True):
    """The agent authors the signal-detection rule from the plain method + its
    grounded binding (its OWN classify-by-join faculty)."""
    model = pr.read_method(a, METHOD, name="epistemic_evidence")
    gb = br.derive_binding(a, model)
    res = ms.synthesise_rule_from_method(a, model, gb["binding"], install=install)
    return model, gb, res


def _reading(a, *cands, single_obs=False, forced_choices=None, clauses=()):
    """Set up an agent with the taught codebook, inject the scenario's evidence
    candidates (+ optional single-observation clamp / read clauses for the
    structural path), author the detection rule, and read the verdict out."""
    ag.seed_epistemic_codebook(a, forced_choices=forced_choices or [])
    for c in clauses:
        rc.read_clause(a, c, write=True)
    if clauses:
        ag.annotate_forced_choice_probes(a)
    for c in cands:
        ag.annotate_evidence_candidate(a, c)
    if single_obs:
        ag.annotate_single_observation(a)
    if cands:                              # only the candidate path needs the join rule
        _author_detection(a, install=True)
    readings = ag.assess_epistemic_lean(a)
    assert len(readings) == 1, readings
    return readings[0]


def _no_certainty(r):
    """Every verdict is a REVISABLE belief: no band is 'certain', and the
    residual_other_mass (the interval half-width, the 'could be the other
    mechanism' mass) is strictly > 0 ALWAYS."""
    assert r["verdict"] != "certain", r
    assert not str(r["verdict"]).endswith("certain"), r
    assert r["residual_other_mass"] > 0.0, r
    assert r["revisable"] == 1.0, r
    lo, hi = r["interval"]
    assert hi > lo, r["interval"]          # a real (non-degenerate) interval


# --------------------------------------------------------------------------- #
#  1. AGENT-AUTHORSHIP PROOF — the signal-DETECTION rule is the synthesiser's
#     output from the READ method, not hand-written.
# --------------------------------------------------------------------------- #
def test_agent_authors_the_detection_rule():
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    ag.annotate_evidence_candidate(a, "isolated_incoherent_act")   # a fact to ground on

    model = pr.read_method(a, METHOD, name="epistemic_evidence")
    trig = model["steps"][0]["trigger"]
    main = model["steps"][0]["main"]
    assert trig["kind"] == "join", trig
    assert trig["fact_type"] == "evidence candidate" and trig["fact_key"] == "signal_name"
    assert trig["codebook_type"] == "epistemic signal" and trig["codebook_key"] == "name"
    assert main["effect"] == "classify" and main["node_type"] == "epistemic evidence"

    gb = br.derive_binding(a, model)
    b = gb["binding"]
    assert b["fact_edge"] == "has_evidence_candidate", b
    assert b["codebook_edge"] == "has_epistemic_signal", b
    assert b["classification_edge"] == "has_epistemic_evidence", b
    assert b["node_types"]["epistemic evidence"] == "EpistemicEvidence", b
    assert set(b.get("fact_carry", [])) == {"signal_name"}, b
    # the codebook side carries the lean/weight/evidence_kind verdict (name is the join key)
    assert {"lean", "weight", "evidence_kind"} <= set(b.get("codebook_carry", {})), b
    assert "name" not in b.get("codebook_carry", {}), b

    res = ms.synthesise_rule_from_method(a, model, b, install=False)
    assert not res.get("wall"), res
    rule = res["rules"][0]
    assert rule["name"] == "synth_classify_epistemic_evidence", rule["name"]
    assert _no_shipped_epistemic_evidence_rule(), \
        "no seed file may ship a rule that mints EpistemicEvidence"

    assert rule["match"] == [["agent", "has_evidence_candidate", "f"],
                             ["agent", "has_epistemic_signal", "c"]], rule["match"]
    # the Eq-JOIN f.signal_name == c.name
    eqj = _cross_var_eq_join(rule["where"], "f", "c")
    assert eqj is not None, rule["where"]
    assert {eqj["a"]["key"], eqj["b"]["key"]} == {"signal_name", "name"}, eqj
    # mint carries signal_name FROM f + lean/weight/evidence_kind FROM c
    add_node = next(e for e in rule["effects"] if e[0] == "add_node")
    assert add_node[2] == "EpistemicEvidence", add_node
    attrs = add_node[3]
    from_f = {k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "f")}
    from_c = {k for k, v in attrs.items()
              if isinstance(v, dict) and _is_attr_of(v.get("__term__"), "c")}
    assert "signal_name" in from_f, attrs
    assert {"lean", "weight", "evidence_kind"} <= from_c, attrs


def _no_shipped_epistemic_evidence_rule():
    seeds = Path(__file__).resolve().parent.parent / "seeds"
    for p in seeds.glob("*.json"):
        try:
            m = json.loads(p.read_text())
        except Exception:
            continue
        # `seeds/` holds one git-tracked file whose JSON root is a LIST, not a
        # manifest (`_recovered_f16_rules.json`, 12 bare rule objects). The seed
        # LOADER already guards for it (`boot_all._read_seeds`: `if not
        # isinstance(d, dict): continue`); this scan did not, and raised
        # `'list' object has no attribute 'get'` — 13 node ids across 8 files.
        # Read the bare list AS rules rather than skipping it, so the gate KEEPS
        # its coverage instead of gaining a blind spot.
        for r in (m if isinstance(m, list) else m.get("rules", []) or []):
            for eff in r.get("effects", []) or []:
                if isinstance(eff, list) and len(eff) >= 3 and \
                        eff[0] == "add_node" and eff[2] == "EpistemicEvidence":
                    return False
    return True


# --------------------------------------------------------------------------- #
#  2. THE HEADLINE HONESTY TEST — UNDETERMINED DEFAULT. A bare mismatch with a
#     SINGLE observation and only stylistic evidence must be UNDETERMINED, NOT
#     deception. Failing-open to deception here would be the worst outcome.
# --------------------------------------------------------------------------- #
def test_undetermined_default_single_observation_stylistic_only():
    a = _agent()
    r = _reading(a, "fluent_sincere_rationalisation", single_obs=True)
    assert r["verdict"] == "undetermined", r
    assert r["verdict"] != "weak_deception" and r["verdict"] != "strong_deception", r
    _no_certainty(r)


# --------------------------------------------------------------------------- #
#  3. STYLISTIC-ALONE CLAMP — hedging + fluent rationalisation only never moves
#     off UNDETERMINED (the signal is never in HOW it was said).
# --------------------------------------------------------------------------- #
def test_stylistic_alone_stays_undetermined():
    a = _agent()
    r = _reading(a, "hedging_distancing", "fluent_sincere_rationalisation")
    assert r["verdict"] == "undetermined", r
    _no_certainty(r)


# --------------------------------------------------------------------------- #
#  4. WEAK OPACITY — an isolated incoherent act + no visible served interest.
# --------------------------------------------------------------------------- #
def test_weak_opacity():
    a = _agent()
    r = _reading(a, "isolated_incoherent_act", "no_served_interest_visible")
    assert r["verdict"] == "weak_opacity", r
    assert r["lean_score"] < 0, r          # leans opacity
    _no_certainty(r)


# --------------------------------------------------------------------------- #
#  5. WEAK DECEPTION CAP (the coordination gate) — clear served interest +
#     directional asymmetry, NO awareness signal -> at most weak_deception,
#     NEVER strong_deception.
# --------------------------------------------------------------------------- #
def test_weak_deception_cap_no_awareness():
    a = _agent()
    r = _reading(a, "clear_served_interest", "consistent_directional_asymmetry")
    assert r["verdict"] == "weak_deception", r
    assert r["verdict"] != "strong_deception", r
    _no_certainty(r)


# --------------------------------------------------------------------------- #
#  6. STRONG DECEPTION — the one near-decisive cue (documentary internal
#     knowledge trace) reaches strong_deception.
# --------------------------------------------------------------------------- #
def test_strong_deception_documentary():
    a = _agent()
    r = _reading(a, "internal_knowledge_trace")
    assert r["verdict"] == "strong_deception", r
    _no_certainty(r)


# --------------------------------------------------------------------------- #
#  7. PROXY CAP — a verdict resting on the coordination proxy (the
#     TemporalConflictReading stand-in for the UNBUILT inverse-planning model) is
#     capped at weak_deception and flagged proxy_based.
# --------------------------------------------------------------------------- #
def test_proxy_cap_coordination():
    a = _agent()
    r = _reading(a, "coordination_requires_dual_goal", "clear_served_interest")
    assert r["verdict"] == "weak_deception", r
    assert r["verdict"] != "strong_deception", r
    assert r["proxy_based"] == 1.0, r
    _no_certainty(r)


def test_coordination_proxy_annotator_reads_temporal_conflict():
    """The coordination-proxy candidate is derived MECHANICALLY from a held
    TemporalConflictReading (the shipped cross-action pattern) — not injected."""
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    tcr = a.s.add_node("TemporalConflictReading",
                       {"actor": "oil_company", "object": "technology", "pair_key": "fund|oppose"})
    a.inner.add_edge_unchecked(a.agent, "has_temporal_conflict_reading", tcr)
    made = ag.annotate_coordination_proxy(a)
    assert made, "a held TemporalConflictReading must yield a coordination candidate"
    phrases = {a.s.node(n)["attrs"].get("signal_name") for n in a.s.nodes("EvidenceCandidate")}
    assert "coordination_requires_dual_goal" in phrases


# --------------------------------------------------------------------------- #
#  8. NEVER CERTAINTY — across EVERY band, no verdict is 'certain' and the
#     residual (interval half-width) is > 0.
# --------------------------------------------------------------------------- #
def test_never_certainty_across_all_bands():
    scenarios = [
        (["fluent_sincere_rationalisation"], {}),                                 # undetermined
        (["isolated_incoherent_act", "no_served_interest_visible"], {}),          # weak_opacity
        (["clear_served_interest", "consistent_directional_asymmetry"], {}),      # weak_deception
        (["internal_knowledge_trace"], {}),                                       # strong_deception
        (["isolated_incoherent_act", "isolated_incoherent_act",
          "no_served_interest_visible", "no_served_interest_visible"], {}),       # -> strong_opacity attempt
    ]
    for cands, kw in scenarios:
        a = _agent()
        r = _reading(a, *cands, **kw)
        _no_certainty(r)


# --------------------------------------------------------------------------- #
#  9. MORAL ASYMMETRY — the SAME evidence magnitude (a single 0.35 structural
#     signal) reaches the OPACITY band but NOT the deception band. The deception
#     threshold is strictly greater than the opacity threshold.
# --------------------------------------------------------------------------- #
def test_moral_asymmetry_threshold():
    a1 = _agent()
    r_op = _reading(a1, "isolated_incoherent_act")        # opacity, 0.35, structural
    assert r_op["verdict"] == "weak_opacity", r_op        # 0.35 reaches opacity

    a2 = _agent()
    r_de = _reading(a2, "consistent_directional_asymmetry")  # deception, 0.35, structural
    assert r_de["verdict"] == "undetermined", r_de        # 0.35 does NOT reach deception

    assert ag._DECEPTION_WEAK_MIN > ag._OPACITY_WEAK_MIN, \
        "the deception threshold must be strictly greater than the opacity threshold"


# --------------------------------------------------------------------------- #
#  10. AGENT-GROWS-IT — teach a NEW EpistemicSignal; it participates with NO code
#      or rule change (the authored detection rule already joins the codebook).
# --------------------------------------------------------------------------- #
def test_teaching_a_signal_grows_coverage():
    a = _agent()
    ag.seed_epistemic_codebook(a, forced_choices=[])
    # a NEW structural deception signal the shipped codebook does not carry
    teach(a, "EpistemicSignal",
          {"name": "novel_structural_cue", "lean": "deception", "weight": 0.6,
           "evidence_kind": "structural", "note": "a freshly taught structural signal"})
    ag.ensure_epistemic_codebook(a)
    ag.annotate_evidence_candidate(a, "novel_structural_cue")
    _author_detection(a, install=True)
    r = ag.assess_epistemic_lean(a)[0]
    ev = {e["signal_name"] for e in ag.held_epistemic_evidence(a)}
    assert "novel_structural_cue" in ev, ev          # the authored rule classified it
    assert r["verdict"] == "weak_deception", r        # 0.6 >= deception weak min, structural
    _no_certainty(r)


# --------------------------------------------------------------------------- #
#  11. THE MODEL ADVANTAGE — structural_forcing + model-asymmetry routing +
#      measured stakes. This is where the ~54% peer ceiling lifts.
# --------------------------------------------------------------------------- #
def _fc(actor_type):
    return [r for r in ag.FORCED_CHOICE_CODEBOOK if r["actor_type"] == actor_type]


def test_high_stakes_forced_choice_routes_to_deception():
    """(a) an oil company stating a renewables-support reason that DIVERGES from a
    taught high-stakes ForcedChoiceExpectation{can_introspect:1} -> a DECEPTION
    lean, NOT undetermined. The model-advantage headline."""
    a = _agent()
    r = _reading(a, forced_choices=_fc("oil_company"),
                 clauses=["The renewable energy project was funded by the oil company."])
    assert r["verdict"] in ("weak_deception", "strong_deception"), r
    assert r["lean_score"] > 0, r
    assert r["model_based"] == 1.0, r
    # a committed bounded estimate: high stakes -> the interval need not cross 0
    lo, hi = r["interval"]
    assert lo > 0, ("high-stakes interval should not straddle 0", r["interval"])
    assert "structural_forcing" in r["basis"], r
    assert r["model_note"] and "DEFEASIBLE" in r["model_note"], r["model_note"]
    _no_certainty(r)


def test_generic_company_money_power_prior_generalises():
    """A DIFFERENT sector (a pharma company, profit_and_market_power prior) whose
    stated altruistic reason diverges from its taught forced_against threat ->
    DECEPTION via the reusable money/power prior, NOT undetermined. Beyond oil."""
    a = _agent()
    r = _reading(a, forced_choices=_fc("pharma_company"),
                 clauses=["The generic medicine program was funded by the pharma company."])
    assert r["verdict"] in ("weak_deception", "strong_deception"), r
    assert r["lean_score"] > 0 and r["model_based"] == 1.0, r
    _no_certainty(r)


def test_model_asymmetry_routes_individual_to_introspection_gap():
    """(b) the SAME structural forcing but for an INDIVIDUAL whose position means
    they genuinely cannot introspect it (can_introspect:0) -> an INTROSPECTION-GAP
    (opacity) lean, NOT deception. Model-asymmetry routes the mechanism."""
    a = _agent()
    r = _reading(a, forced_choices=_fc("factory_worker"),
                 clauses=["The automation support program was opposed by the factory worker."])
    assert r["verdict"] in ("weak_opacity", "strong_opacity"), r
    assert r["lean_score"] < 0, r          # leans introspection-gap, not deception
    _no_certainty(r)


def test_low_stakes_forced_choice_stays_undetermined():
    """(b') a TRIVIAL-stakes divergence (can_introspect:1 but little money/power at
    risk) -> a WIDE interval that stays UNDETERMINED. UNDETERMINED is the
    low-stakes case, not over-caution."""
    a = _agent()
    r = _reading(a, forced_choices=_fc("pr_agency"),
                 clauses=["The logo colour rebrand was opposed by the pr agency."])
    assert r["verdict"] == "undetermined", r
    lo, hi = r["interval"]
    assert lo < 0 < hi, ("low-stakes interval should straddle 0", r["interval"])
    _no_certainty(r)


def test_no_forced_choice_expectation_stays_undetermined():
    """(c) with NO ForcedChoiceExpectation for the actor, the base humility is
    intact: a bare mismatch -> UNDETERMINED."""
    a = _agent()
    r = _reading(a, forced_choices=[],       # no model at all
                 clauses=["The renewable energy project was funded by the oil company."])
    assert r["verdict"] == "undetermined", r
    assert r["model_based"] == 0.0, r
    _no_certainty(r)


def test_stakes_narrow_the_interval():
    """(d) HIGH stakes -> a narrower interval (more committed) than LOW stakes /
    no-model. The measured stakes anchor the confidence interval width."""
    a_hi = _agent()
    r_hi = _reading(a_hi, forced_choices=_fc("oil_company"),
                    clauses=["The renewable energy project was funded by the oil company."])
    a_lo = _agent()
    r_lo = _reading(a_lo, forced_choices=_fc("pr_agency"),
                    clauses=["The logo colour rebrand was opposed by the pr agency."])
    a_none = _agent()
    r_none = _reading(a_none, forced_choices=[],
                      clauses=["The renewable energy project was funded by the oil company."])
    assert r_hi["residual_other_mass"] < r_lo["residual_other_mass"] < r_none["residual_other_mass"], \
        (r_hi["residual_other_mass"], r_lo["residual_other_mass"], r_none["residual_other_mass"])


# --------------------------------------------------------------------------- #
#  12. SOURCE AUDIT — no `import re`; the ANNOTATORS make no lean/weight decision
#      (the weight lives in the codebook); the combine/routing rules are the only
#      things minting the verdict types.
# --------------------------------------------------------------------------- #
def test_source_audit_no_regex_no_annotator_decision():
    src = (Path(__file__).resolve().parent.parent / "domains" / "actor_goals.py").read_text()
    for line in src.splitlines():
        s = line.strip()
        assert not (s == "import re" or s.startswith("import re ")
                    or s.startswith("import re,") or s.startswith("import re;")), line
    assert "re.match" not in src and "re.search" not in src and "re.sub" not in src

    # Python never mints the verdict/evidence types or the codebook rows directly.
    assert 'add_node("EpistemicEvidence"' not in src
    assert 'add_node("EpistemicLeanReading"' not in src
    assert 'add_node("EpistemicSignal"' not in src            # only teach() adds codebook rows

    # the EvidenceCandidate annotator emits UNCONDITIONALLY, independent of whether
    # the codebook names the signal (no lean/weight decision in the annotator).
    a1 = _agent()
    ag.seed_epistemic_codebook(a1, forced_choices=[])
    n1 = ag.annotate_evidence_candidate(a1, "a_signal_the_codebook_never_names")
    assert n1 is not None                                     # emitted despite no codebook match
    a2 = _agent()                                             # NO codebook taught at all
    n2 = ag.annotate_evidence_candidate(a2, "a_signal_the_codebook_never_names")
    assert n2 is not None                                     # still emitted with no codebook

    # and with no authored detection rule, that candidate produces NO evidence and
    # NO verdict shift (the DECISION is the rule's, not the annotator's).
    assert ag.held_epistemic_evidence(a2) == []


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))


# --------------------------------------------------------------------------- #
#  where-tree structural reads (mechanical) — same helpers the authoring /
#  temporal tests use, so shape assertions are apples-to-apples.
# --------------------------------------------------------------------------- #
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


def _is_attr_of(x, var):
    return (isinstance(x, dict) and x.get("type") == "Attr"
            and isinstance(x.get("node"), dict)
            and x["node"].get("type") == "Var" and x["node"].get("name") == var)


def _cross_var_eq_join(where, va, vb):
    for nd in _flatten(where):
        if nd.get("type") != "Eq":
            continue
        a, b = nd.get("a"), nd.get("b")
        if (_is_attr_of(a, va) and _is_attr_of(b, vb)) or (_is_attr_of(a, vb) and _is_attr_of(b, va)):
            return nd
    return None
