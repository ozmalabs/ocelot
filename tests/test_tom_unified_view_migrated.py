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


def _adapter():
    from substrate.boot_core import CORE_SEEDS
    from substrate.world_adapter import WorldAdapter
    return WorldAdapter(seeds=CORE_SEEDS + ("tom_unified_view",))


def _source(adapter, epoch, content):
    node = adapter.inner.add_node("TomAttributedStateSource", {
        "schema_version": 1,
        "source_key": "character:sally:belief:17",
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
