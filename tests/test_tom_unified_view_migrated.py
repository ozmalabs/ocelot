"""F1.1 contract fixtures for the provenance-preserving ToM view.

F1.2 connects these source-shaped records to generated graph projections.
These fixtures deliberately test mapping and non-conflation semantics only;
they do not claim that runtime projection is wired yet.
"""
from __future__ import annotations


def _view(source_kind, source_node, holder, target, content_ref, modality,
          epistemic_kind, source_epoch=None):
    return {
        "source_kind": source_kind,
        "source_node": source_node,
        "holder": holder,
        "target": target,
        "content_ref": content_ref,
        "modality": modality,
        "epistemic_kind": epistemic_kind,
        "source_epoch": source_epoch if source_epoch is not None else {"known": False},
    }


def test_four_sources_project_without_merge():
    rows = [
        _view("character_tom", "belief:17", "sally", "room", "proposition:at(room)",
              "belief", "attributed", 3),
        # A vocabulary concept is context attached to an independent state;
        # it is not itself one of the attributed-state rows.
        _view("interlocutor_estimate", "party:alex", "reader", "alex",
              "feature:register=formal", "estimate", "estimate"),
        _view("interlocutor_assertion", "assertion:21", "alex", None,
              "message:21", "asserted", "world_assertion", 21),
        _view("bigville_tom", "concept:controllability_for:alex", "resident:bea",
              "alex", "concept:controllability_for:alex", "attributed", "attributed", 8),
    ]
    assert len({(r["source_kind"], r["source_node"]) for r in rows}) == 4
    assert all(r["source_node"] and r["epistemic_kind"] for r in rows)
    assert rows[1]["source_epoch"] == {"known": False}
    assert all(r["source_kind"] != "psychology_vocabulary" for r in rows)


def test_own_affect_is_not_other_belief():
    own_affect = _view("bigville_resident_affect", "concept:desire_for:alex",
                       "resident:bea", "alex", "desire_for:alex", "state",
                       "self_state")
    belief = _view("bigville_tom", "concept:controllability_for:alex",
                   "resident:bea", "alex", "controllability_for:alex",
                   "attributed", "attributed")
    assert own_affect["epistemic_kind"] == "self_state"
    assert own_affect["source_node"] != belief["source_node"]


def test_contradictions_preserved():
    rows = [
        _view("character_tom", "belief:1", "sally", "door", "door=open",
              "belief", "attributed", 2),
        _view("character_tom", "belief:2", "sally", "door", "door=closed",
              "belief", "attributed", 2),
        _view("world_observation", "observation:4", "observer", None,
              "door=closed", "observed", "world_assertion", 4),
    ]
    assert len({r["source_node"] for r in rows}) == 3
    assert {r["content_ref"] for r in rows} == {"door=open", "door=closed"}
    assert rows[0]["epistemic_kind"] == "attributed"
    assert rows[2]["epistemic_kind"] == "world_assertion"


def test_source_epoch_refresh():
    old = _view("character_tom", "belief:17", "sally", "room", "at(room)",
                "belief", "attributed", 3)
    new = _view("character_tom", "belief:17", "sally", "room", "at(kitchen)",
                "belief", "attributed", 4)
    assert old["source_epoch"] != new["source_epoch"]
    assert old["content_ref"] != new["content_ref"]
    # The source identity and historical row remain available for lineage.
    assert old["source_node"] == new["source_node"]


def _adapter(seeds=None):
    from substrate.world_adapter import WorldAdapter
    return WorldAdapter(seeds=("tom_unified_view",) if seeds is None else seeds)


def _source(adapter, epoch, content):
    node = adapter.inner.add_node("TomAttributedStateSource", {
        "schema_version": 1,
        "source_key": "character:sally:belief:17",
        "source_is_current": True,
        "source_kind": "character_tom",
        "source_node": "belief:17",
        "source_epoch": epoch,
        "owner_id": "agent-root",
        "holder": "sally",
        "target": "room",
        "content_ref": content,
        "modality": "belief",
        "epistemic_kind": "attributed",
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_tom_attributed_source", node)
    return node


def test_disabled_policy_does_not_project_and_enabled_projection_is_native():
    a = _adapter()
    policy = a.inner.nodes("TomViewPolicy")[0]
    _source(a, 1, "at(room)")
    a.inner.run_rules()
    assert list(a.inner.nodes("TomAttributedStateView")) == []

    a.inner.set_attr(policy, "enabled", 1.0)
    a.inner.run_rules()
    views = list(a.inner.nodes("TomAttributedStateView"))
    assert len(views) == 1
    attrs = a.inner.node(views[0])["attrs"]
    assert attrs["source_kind"] == "character_tom"
    assert attrs["epistemic_kind"] == "attributed"
    assert list(a.inner.neighbours(views[0], "projects_tom_source"))


def test_projection_refresh_keeps_old_epoch_as_stale():
    a = _adapter()
    policy = a.inner.nodes("TomViewPolicy")[0]
    a.inner.set_attr(policy, "enabled", 1.0)
    source = _source(a, 1, "at(room)")
    a.inner.run_rules()
    a.inner.set_attr(source, "source_epoch", 2)
    a.inner.set_attr(source, "content_ref", "at(kitchen)")
    a.inner.run_rules()
    views = [a.inner.node(n)["attrs"] for n in a.inner.nodes("TomAttributedStateView")]
    assert len(views) == 2
    assert {v["status"] for v in views} == {"current", "stale"}
    assert {v["source_epoch"] for v in views} == {1, 2}


def test_dependency_boot_and_no_cross_owner_recall():
    a, b = _adapter(), _adapter()
    assert len(list(a.inner.nodes("TomViewPolicy"))) == 1
    assert len(list(b.inner.nodes("TomViewPolicy"))) == 1
    assert list(a.inner.nodes("MetaShape"))
    assert list(a.inner.nodes("ShapePrinciple"))
    pa, pb = a.inner.nodes("TomViewPolicy")[0], b.inner.nodes("TomViewPolicy")[0]
    a.inner.set_attr(pa, "enabled", 1.0)
    _source(a, 1, "private:belief")
    a.inner.run_rules()
    assert len(list(a.inner.nodes("TomAttributedStateView"))) == 1
    assert len(list(b.inner.nodes("TomAttributedStateView"))) == 0


def test_generator_reproduction():
    import json
    from pathlib import Path
    from scripts.gen_tom_unified_view_seed import build_seed
    checked_in = json.loads(Path("seeds/tom_unified_view.json").read_text())
    assert checked_in == build_seed()


def test_domain_source_adapters_create_distinct_native_views_and_meta_observations():
    from substrate.boot_core import CORE_SEEDS
    from substrate.world_adapter import WorldAdapter
    from domains.tom_meta_shape import (
        project_character_tom_node, project_interlocutor_estimate,
        project_interlocutor_assertion,
    )

    a = WorldAdapter(seeds=CORE_SEEDS + ("tom_unified_view",))
    policy = a.inner.nodes("TomViewPolicy")[0]
    a.inner.set_attr(policy, "enabled", 1.0)

    nested = a.s.add_node("SmEntity", {
        "name": "key#sally_belief", "referent": "key", "nested": 1,
        "belief_holder": "sally", "flavor": "belief",
        "proposition": '["in","key","drawer"]',
    })
    party = a.s.add_node("Interlocutor", {
        "name": "alex", "turns": 3,
        "feat_counts": {"register": {"formal": 2}},
        "known_concepts": ["key"],
    })
    assertion = a.s.add_node("Assertion", {
        "content": "I think the key is in the drawer.", "turn": 4,
        "flavor": "belief",
    })
    mt = a.s.add_node("Microtheory", {"name": "bea_beliefs"})
    concept = a.s.add_node("Concept", {
        "name": "controllability_for:alex", "state": 0.7,
        "external_field": 0.4,
    })
    a.inner.add_edge_unchecked(mt, "has_concept", concept)
    own_affect = a.s.add_node("Concept", {
        "name": "desire_for:alex", "state": 0.8, "external_field": 0.2,
    })

    project_character_tom_node(a, nested)
    project_interlocutor_estimate(a, party)
    project_interlocutor_assertion(a, party, assertion)
    from domains.bigville_theory_of_mind import mint_resident_tom_belief
    projected = mint_resident_tom_belief(
        a.inner, mt, "controllability", "alex", projection_agent=a,
        resident="bea")
    assert projected == concept
    from domains.tom_meta_shape import project_resident_agency_belief
    assert project_resident_agency_belief(
        a, own_affect, resident="bea", target="alex") is None

    views = [a.inner.node(n)["attrs"] for n in a.inner.nodes("TomAttributedStateView")]
    assert len(views) == 4
    assert {v["source_kind"] for v in views} == {
        "character_tom", "interlocutor_estimate", "interlocutor_assertion", "bigville_tom",
    }
    assert len({v["source_key"] for v in views}) == 4
    assert sum(v["epistemic_kind"] == "world_assertion" for v in views) == 1
    assert sum(v["epistemic_kind"] == "estimate" for v in views) == 1
    assert sum(v["epistemic_kind"] == "attributed" for v in views) == 2
    assert len(list(a.inner.nodes("ShapeObservation"))) == 4
    assert len(list(a.inner.nodes("TomAttributedStateSource"))) == 4
    observations = [a.inner.node(n)["attrs"] for n in a.inner.nodes("ShapeObservation")]
    assert any(o.get("status") == "recognized" for o in observations)
    assert all(o.get("status") in {"recognized", "residual"} for o in observations)
    for view in a.inner.nodes("TomAttributedStateView"):
        linked = list(a.inner.neighbours(view, "uses_meta_shape_observation"))
        assert len(linked) == 1
        assert a.inner.node(linked[0])["attrs"]["status"] in {"recognized", "residual"}
    assert all(not a.inner.node(n)["attrs"].get("nested")
               for n in a.inner.nodes("TomAttributedStateView"))


def test_character_runtime_emits_source_only_when_opt_in_seed_is_loaded():
    from substrate.boot_core import CORE_SEEDS
    from substrate.world_adapter import WorldAdapter
    from domains.character_tom import read_character_tom

    a = WorldAdapter(seeds=CORE_SEEDS + ("tom_unified_view",))
    a.inner.set_attr(a.inner.nodes("TomViewPolicy")[0], "enabled", 1.0)
    read_character_tom(a, "Sally thinks the ball is in the basket.")
    views = [a.inner.node(n)["attrs"] for n in a.inner.nodes("TomAttributedStateView")]
    assert len(views) == 1
    assert views[0]["source_kind"] == "character_tom"


def test_interlocutor_runtime_projects_accumulated_estimate():
    from substrate.boot_core import CORE_SEEDS
    from substrate.world_adapter import WorldAdapter
    from domains.interlocutor_model import observe_turn

    a = WorldAdapter(seeds=CORE_SEEDS + ("tom_unified_view",))
    a.inner.set_attr(a.inner.nodes("TomViewPolicy")[0], "enabled", 1.0)
    observe_turn(a, "I enjoy hiking and music.")
    observe_turn(a, "I enjoy hiking and music.")
    views = [a.inner.node(n)["attrs"] for n in a.inner.nodes("TomAttributedStateView")]
    estimate_views = [v for v in views if v["source_kind"] == "interlocutor_estimate"]
    assert len(estimate_views) == 2
    assert {v["status"] for v in estimate_views} == {"current", "stale"}
    estimate_sources = [a.inner.node(n)["attrs"]
                        for n in a.inner.nodes("TomAttributedStateSource")
                        if a.inner.node(n)["attrs"].get("source_kind") == "interlocutor_estimate"]
    assert len(estimate_sources) == 2
    assert {s["source_is_current"] for s in estimate_sources} == {True, False}
