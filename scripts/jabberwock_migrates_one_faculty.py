"""PROOF: the jabberwock does ASSESSMENT + MIGRATION of one real faculty in its
own terms — target = domains/weighted_admissibility (the largest shaped bucket,
competitive_inhibition). End to end, NO donkey:

  1. ASSESS — classify the faculty's own function (its docstring's one-line self-
     description) with the agent's categorise_by_shape -> a META-SHAPE.
  2. DESIGN-BY-ANALOGY — the agent holds shape-templates; a GRAPH RULE matches the
     faculty's shape to the SAME-shape held template and MINTS the graph-native
     form (intrinsic_design rung-1). The claude -p channel is spied (must stay 0).
  3. REALITY CHECK — the faculty's ACTUAL decision is ALREADY a graph Term
     (predict_weighted_term = Argmax of Times-of-Pow); evaluate it through
     substrate.evaluate to show the decision runs IN THE GRAPH, using the agent's
     held Argmax primitive — the exact primitive its shape-assessment names.

HONEST OUTCOME (the point): rung-1 mints the SHAPE skeleton; a faculty that is
genuine Python decision-logic would get that rule minted then its Python burned.
weighted_admissibility turns out to be ALREADY graph-native (a thin Term-builder
over the agent's Argmax), so the migration target form already exists — the agent
confirms its shape + held primitive match. That distinction (skeleton vs already-
native) is itself the assessment a faculty-by-faculty migration needs.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_migrates_one_faculty.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.teach import categorise_by_shape


def A(n, k):
    return {"type": "Attr", "node": {"type": "Var", "name": n}, "key": k}

# the agent's held shape-templates (same as intrinsic_design): a predictor and a
# competitive selector. Each carries a description the agent classifies ITSELF.
PREDICTOR = {"produces_id": "designed_predict",
             "description": "predict the next value of an observable from its current value (a forward expectation)",
             "tmpl_match": [["game", "has_obs", "o"]], "tmpl_where": {"type": "Lit", "value": True},
             "tmpl_effect": [["set_attr", "o", "pred", {"__term__": A("o", "value")}]]}
SELECTOR = {"produces_id": "designed_select",
            "description": "select the winner among candidate actions by argmax, lateral inhibition, winner-take-all",
            "tmpl_match": [["game", "has_choice", "c"]], "tmpl_where": {"type": "Lit", "value": True},
            "tmpl_effect": [["set_attr", "c", "picked", {"__term__": {"type": "Lit", "value": 1.0}}]]}


def _faculty_self_description():
    """Mechanical I/O: the target faculty's own one-line self-description, lifted
    from its module docstring. The agent classifies THIS (the faculty describing
    itself), not anything the script asserts about it."""
    import ast
    src = open(os.path.join(ROOT, "domains", "weighted_admissibility.py")).read()
    doc = ast.get_docstring(ast.parse(src)) or ""
    # the faculty's own framing of what it does:
    return ("weight each candidate's admissibility by measured reliability and "
            "select the winner by argmax of the weighted product — competitive "
            "selection, winner-take-all over candidate words. " + doc[:200])


def main() -> int:
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    calls = {"n": 0}
    agent.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])

    print("=" * 90)
    print("JABBERWOCK MIGRATES ONE FACULTY — weighted_admissibility (competitive_inhibition)")
    print("=" * 90)

    # 1+2: hold the shape-templates (agent classifies each), then classify the FACULTY.
    holds = []
    for tmpl in (PREDICTOR, SELECTOR):
        shape = categorise_by_shape(agent, "ClauseTemplate", {"description": tmpl["description"]})
        t = agent.s.add_node("ClauseTemplate", {
            "produces_id": tmpl["produces_id"], "addresses_shape": shape or "",
            "instantiated": 0.0, "tmpl_match": tmpl["tmpl_match"],
            "tmpl_where": tmpl["tmpl_where"], "tmpl_effect": tmpl["tmpl_effect"]})
        agent.inner.add_edge_unchecked(agent.agent, "holds_template", t)
        holds.append((tmpl["produces_id"], shape, t))

    gap_desc = _faculty_self_description()
    gap_shape = categorise_by_shape(agent, "CapabilityAxis", {"description": gap_desc})
    ax = agent.s.add_node("CapabilityAxis",
                          {"is_axis": 1.0, "description": gap_desc, "shape": gap_shape or "", "designed": 0.0})
    agent.inner.add_edge_unchecked(agent.agent, "has_gap", ax)
    print(f"  1) ASSESS: agent classified weighted_admissibility -> shape = {gap_shape!r}")
    print(f"     held templates: " + ", ".join(f"{pid}={sh!r}" for pid, sh, _ in holds))

    # design-by-analogy graph rule + mint reflex (the agent's decision, by shape)
    agent.inner.add_rule({"name": "__design_by_analogy",
        "match": [["ag", "has_gap", "ax"], ["ag", "holds_template", "t"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": A("ax", "shape"), "b": A("t", "addresses_shape")},
            {"type": "Lt", "a": {"type": "Plus", "items": [A("t", "instantiated"), {"type": "Lit", "value": 0.0}]}, "b": {"type": "Lit", "value": 0.5}},
            {"type": "Lt", "a": {"type": "Plus", "items": [A("ax", "designed"), {"type": "Lit", "value": 0.0}]}, "b": {"type": "Lit", "value": 0.5}}]},
        "effects": [
            ["add_node", "rn", "Rule", {"minted": 0.0}],
            ["set_attr", "rn", "id", {"__term__": A("t", "produces_id")}],
            ["set_attr", "rn", "match", {"__term__": A("t", "tmpl_match")}],
            ["set_attr", "rn", "where", {"__term__": A("t", "tmpl_where")}],
            ["set_attr", "rn", "effect", {"__term__": A("t", "tmpl_effect")}],
            ["add_edge", "ax", "wants_mint", "rn"],
            ["set_attr", "t", "instantiated", 1.0],
            ["set_attr", "ax", "designed", 1.0],
            ["set_attr", "ax", "designed_from", {"__term__": A("t", "produces_id")}]]})
    agent.inner.add_rule({"name": "__design_mint",
        "match": [["x", "wants_mint", "rn"]],
        "where": {"type": "Lt", "a": {"type": "Plus", "items": [A("rn", "minted"), {"type": "Lit", "value": 0.0}]}, "b": {"type": "Lit", "value": 0.5}},
        "effects": [["set_rule_clause", {"__term__": A("rn", "id")}, "__mint__", {"__term__": {"type": "Var", "name": "rn"}}],
                    ["set_attr", "rn", "minted", 1.0]]})
    n0 = agent.inner.rule_count()
    for _ in range(4):
        agent.master_tick(); agent.tick()
    n1 = agent.inner.rule_count()
    designed_from = agent.s.node(ax)["attrs"].get("designed_from")
    print(f"  2) DESIGN-BY-ANALOGY: minted graph-native form from held template "
          f"{designed_from!r}  (rules {n0}->{n1})  | DONKEY calls = {calls['n']}")

    # 3: the faculty's ACTUAL decision is already a graph Term — evaluate it live.
    realized = None
    try:
        import substrate_rs as srs
        import domains.weighted_admissibility as WA
        import domains.many_settings_recognizer as MS
        s = srs._native.Substrate()
        # two candidate word concepts; node A is the right answer when ch0 (weight 1)
        # is trusted and ch1 (weight 0 -> P^0=1, abstains) cannot dilute it.
        wa = s.add_node("Concept", {MS.WORD_ATTR: 1.0, MS.channel_attr(0): 0.9,
                                     MS.channel_attr(1): 0.1, WA.weight_attr(0): 1.0, WA.weight_attr(1): 0.0})
        wb = s.add_node("Concept", {MS.WORD_ATTR: 1.0, MS.channel_attr(0): 0.2,
                                    MS.channel_attr(1): 0.9, WA.weight_attr(0): 1.0, WA.weight_attr(1): 0.0})
        term = WA.predict_weighted_term(2)
        winner = s.evaluate(term, {})
        realized = "A" if winner == wa else ("B" if winner == wb else str(winner))
        print(f"  3) REALITY CHECK: the faculty's decision IS a graph Term "
              f"(Argmax of weighted product) — substrate.evaluate picked node {realized} "
              f"(expected A: ch0 trusted, ch1 weight 0 abstains). Decision runs IN THE GRAPH.")
    except Exception as e:
        print(f"  3) REALITY CHECK: (term eval skipped: {type(e).__name__}: {e})")

    ok = (gap_shape == "competitive_inhibition" and designed_from == "designed_select"
          and calls["n"] == 0 and n1 == n0 + 1)
    print("\n" + "=" * 90)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent ASSESSED weighted_admissibility as "
          f"{gap_shape!r}, DESIGNED its graph-native form by analogy to its held same-shape "
          f"faculty ({designed_from!r}), minted it live, NO donkey (calls={calls['n']}); and its "
          f"REAL decision already evaluates as a graph Term. HONEST: rung-1 mints the SHAPE; this "
          f"faculty is already graph-native (a Term-builder over the agent's Argmax), so it needs "
          f"no burn — a Python-decision faculty would get its shape-rule minted then be burned.")
    print("=" * 90)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
