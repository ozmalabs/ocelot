"""Live Class-A/Class-B demonstration for A7 (both copies: the
has_judge&&has_structure 'apick' branch and the has_judge&&has_gradient
'best' branch), through the REAL loaded, edited seed's REAL
compose_experiment_mint_parametric rule, fired via rf.ground_concern.

Unlike A9, A7's pick is resolved EAGERLY when the meta-rule itself fires
(baked straight into the minted rule's own effects as literal data --
confirmed by reading the minted rule's SeedDelta: act_rule_varied /
remove_rules / edit_op_kind are plain strings, not {'__term__': ...}
payloads) -- so no extraction-and-standalone-evaluate step is needed here;
the ONE real `ground_concern` call IS the full demonstration.
"""
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "runners/dsl/python")

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf
from domains import rule_signature as rsig


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def fresh_agent():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    return ag


def axis(ag, tag, preds):
    return ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": preds, "from_observation": 1.0, "source": "concern_induction",
    })


def seed_delta_attrs(mint):
    for e in mint.get("effects", []):
        if isinstance(e, list) and len(e) == 4 and e[0] == "add_node" and e[2] == "SeedDelta":
            return e[3]
    return {}


REAL_RULE = "hop_descend_gradient"   # grid_navigation's only writes_chosen_action rule
CLASS_A_STRUCT_WORD = "nav_mode"     # confirmed present in its real where_signature_json,
                                      # absent from its real keywords_text "hop descend gradient"


def main():
    print("=== A7 live demonstration (through the REAL loaded, edited seed) ===")

    # ---------------- A7b: has_judge && has_gradient branch ('best') ------
    print("\n--- A7b (gradient branch) ---")
    ag = fresh_agent()
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    n = rsig.ensure_where_signature(ag.s)
    print(f"[Class A setup] primed where_signature_json on {n} RuleSummary node(s)")
    at = ag.s.node(next(iter(ag.s.nodes("RuleSummary"))))["attrs"]
    assert CLASS_A_STRUCT_WORD not in at["keywords_text"], at["keywords_text"]
    assert CLASS_A_STRUCT_WORD in (at.get("where_signature_json") or ""), "sanity: real sig must contain the probe word"

    tag = "a7b_classA"
    # 'acting rule' (NOT the bare word 'gradient') grounds the has_gradient
    # flag via the SAME 'vary_acting_gradient' RelationCue -- so the primary
    # keywords_text overlap genuinely has nothing in this residual that
    # matches "hop descend gradient" verbatim; nav_mode is structural-only.
    preds = ["test", "send", "judge", "acting rule", CLASS_A_STRUCT_WORD]
    axis(ag, tag, preds)
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"
    mint = next(r for r in res["rules"] if r["name"].startswith("author_experiment_from_residual_"))
    d = seed_delta_attrs(mint)
    print(f"[Class A] act_rule_varied={d.get('act_rule_varied')!r} act_shift={d.get('act_shift')!r}")
    assert d.get("act_rule_varied") == REAL_RULE, d
    assert d.get("act_shift") not in (None, 0), d
    print("[Class A] PASS -- structural fallback recovered the real acting rule where the primary keyword "
          "Argmax genuinely had nothing to match on.")

    # Class B: bare 'gradient' word present -> primary matches keywords_text
    # directly; where_signature_json deliberately NEVER primed on this
    # agent, so if the pick still succeeds it can only be via the primary.
    ag2 = fresh_agent()
    tag2 = "a7b_classB"
    preds2 = ["test", "send", "judge", "gradient"]
    axis(ag2, tag2, preds2)
    res2 = rf.ground_concern(ag2, [tag2])
    assert res2.get("served_by") == "graph"
    mint2 = next(r for r in res2["rules"] if r["name"].startswith("author_experiment_from_residual_"))
    d2 = seed_delta_attrs(mint2)
    print(f"[Class B] act_rule_varied={d2.get('act_rule_varied')!r} (where_signature_json NEVER primed on this agent)")
    assert d2.get("act_rule_varied") == REAL_RULE, d2
    print("[Class B] PASS -- primary keywords_text pick alone recovered the rule; fallback not needed.")

    # ---------------- A7a: has_judge && has_structure branch ('apick') ----
    print("\n--- A7a (structure branch) ---")
    ag3 = fresh_agent()
    rf._ensure_acting_rule_provenance(ag3.s, ag3.inner)
    rf._ensure_edit_ops(ag3.s)
    rsig.ensure_where_signature(ag3.s)
    tag3 = "a7a_classA"
    preds3 = ["test", "send", "judge", "structure", CLASS_A_STRUCT_WORD, "flip"]
    axis(ag3, tag3, preds3)
    res3 = rf.ground_concern(ag3, [tag3])
    assert res3.get("served_by") == "graph"
    sv3 = res3.get("structural_variant") or {}
    print(f"[Class A] structural_variant.built={sv3.get('built')} removed_rule={sv3.get('removed_rule')!r} kind={sv3.get('kind')!r}")
    assert sv3.get("built") is True
    assert sv3.get("removed_rule") == REAL_RULE, sv3
    mint3 = next(r for r in res3["rules"] if r["name"].startswith("author_experiment_from_residual_"))
    d3 = seed_delta_attrs(mint3)
    assert d3.get("remove_rules") == f'["{REAL_RULE}"]', d3
    print("[Class A] PASS -- structural fallback recovered the real acting rule for the structure/EditOp branch too.")

    ag4 = fresh_agent()
    rf._ensure_acting_rule_provenance(ag4.s, ag4.inner)
    rf._ensure_edit_ops(ag4.s)
    # deliberately NOT priming where_signature_json on this agent
    tag4 = "a7a_classB"
    preds4 = ["test", "send", "judge", "structure", "descend", "flip"]
    axis(ag4, tag4, preds4)
    res4 = rf.ground_concern(ag4, [tag4])
    assert res4.get("served_by") == "graph"
    sv4 = res4.get("structural_variant") or {}
    print(f"[Class B] structural_variant.built={sv4.get('built')} removed_rule={sv4.get('removed_rule')!r} (where_signature_json NEVER primed)")
    assert sv4.get("built") is True
    assert sv4.get("removed_rule") == REAL_RULE, sv4
    print("[Class B] PASS -- primary keywords_text pick alone recovered the rule (via 'descend'); fallback not needed.")

    print("\n=== A7 demonstration complete: GO on both copies (structure branch, gradient branch) ===")


if __name__ == "__main__":
    main()
