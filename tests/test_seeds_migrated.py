"""Seed registry + loader, migrated — the seed system as GRAPH MODULARITY on the
Rust substrate (no CuriousAgent). Covers the parts of tests/test_seeds that are
about seeds-as-graph-data:

  * dependency-closure resolution (topo sort) over the live registry — graph
    data walked mechanically, no agent
  * graph-resident Seed{id,version} nodes + depends_on edges, recorded by
    `load_seeds_into` against a bare substrate (the architecture's "a seed is a
    graph-resident manifest")
  * idempotent / partial-then-extend loading
  * unknown-id / version-conflict / cycle errors
  * the Rust loader directly (with and without an agent_root)

NOT covered here (still bench, tests/test_seeds): `ChatWorld.attach` loading the
chat seed — that needs a migrated ChatWorld AND self-contained conversation-stack
manifests (chat/intent/conversation currently reference a Concept outside their
declared closure, so they don't load onto a bare substrate yet).
"""
from __future__ import annotations

import pytest
import substrate_rs as srs

from substrate.seeds import REGISTRY, Seed, SeedRegistry
from domains import seed_registry as _domain_seeds  # populate REGISTRY  # noqa: F401
from substrate.boot_core import load_seeds_into, installed_seeds


# ---------------------------------------------------------------------------
# registry resolution — pure graph-data dependency walk, no agent
# ---------------------------------------------------------------------------

def test_registry_resolves_deps_topologically():
    """A seed's deps must appear before it in the resolved order."""
    plan = REGISTRY.resolve(["intent"])
    ids = [s.id for s in plan]
    intent_pos = ids.index("intent")
    for dep in ("conversation", "psychology", "relations"):
        assert dep in ids, ids
        assert ids.index(dep) < intent_pos, (
            f"{dep} must come before intent: {ids}")


def test_meta_seed_pulls_full_closure():
    plan = REGISTRY.resolve(["chat"])
    ids = {s.id for s in plan}
    assert ids >= {"chat", "intent", "conversation", "psychology",
                   "relations", "design", "llm_partner"}


def test_voice_pulls_audio_stack_on_top_of_chat():
    plan = REGISTRY.resolve(["voice"])
    ids = {s.id for s in plan}
    assert ids >= {"voice", "chat", "speech", "audio"}


def test_resolve_rejects_unknown_id():
    with pytest.raises(KeyError, match="nonsense"):
        REGISTRY.resolve(["nonsense"])


def test_registry_rejects_version_conflict():
    r = SeedRegistry()
    r.register(Seed(id="x", version="1.0.0"))
    with pytest.raises(ValueError, match="seed conflict"):
        r.register(Seed(id="x", version="2.0.0"))


def test_registry_detects_cycles():
    r = SeedRegistry()
    r.register(Seed(id="a", depends_on=("b",)))
    r.register(Seed(id="b", depends_on=("a",)))
    with pytest.raises(ValueError, match="cycle"):
        r.resolve(["a"])


# ---------------------------------------------------------------------------
# graph-resident loading — Seed nodes + depends_on, onto a bare substrate
# ---------------------------------------------------------------------------

def _bare():
    s = srs.Substrate()
    agent = s.add_node("Agent", {})
    return s, agent


def test_load_writes_graph_resident_seed_nodes():
    """load_seeds_into records a Seed{id,version} node per loaded seed, with
    depends_on edges. self_monitoring depends_on experimentation_core, so the
    closure is both — in topo order — with a real depends_on edge between them."""
    s, agent = _bare()
    installed = load_seeds_into(s, agent, ["self_monitoring"])
    assert "self_monitoring" in installed
    assert "experimentation_core" in installed          # transitive dep
    sm = installed["self_monitoring"]
    node = s.node(sm)
    assert node["type"] == "Seed"
    assert node["attrs"]["id"] == "self_monitoring"
    assert node["attrs"]["version"] == "1.0.0"
    deps = s._inner.neighbours(sm, "depends_on")
    dep_ids = {s.node(d)["attrs"]["id"] for d in deps}
    assert dep_ids == {"experimentation_core"}


def test_load_is_idempotent():
    """Second load of the same seeds is a no-op — each Seed node once."""
    s, agent = _bare()
    first = load_seeds_into(s, agent, ["self_monitoring"])
    second = load_seeds_into(s, agent, ["self_monitoring"])
    assert first == second                              # same NodeIDs
    assert len(installed_seeds(s)) == len(first)


def test_load_partial_then_extend():
    """Loading one seed, then another, extends the set without re-installing
    the already-present seed."""
    s, agent = _bare()
    load_seeds_into(s, agent, ["experimentation_core"])
    exp_nid = installed_seeds(s)["experimentation_core"]
    after = load_seeds_into(s, agent, ["self_monitoring"])
    assert after["experimentation_core"] == exp_nid     # not re-installed
    assert "self_monitoring" in after


def test_chat_closure_loads_onto_a_bare_substrate():
    """The seed-system half of the old test_chat_world_attach: loading `chat`
    installs its whole closure as graph data — chat + intent + conversation
    (transitive) — onto a bare substrate, no CuriousAgent. (That ChatWorld.attach
    is what TRIGGERS this is a ChatWorld concern, for the ChatWorld migration.)

    This also guards the conversation-stack manifests staying self-contained:
    before the psychology `expectation` Concept fix they failed to load at all."""
    s, agent = _bare()
    installed = load_seeds_into(s, agent, ["chat"])
    assert {"chat", "intent", "conversation", "psychology", "relations",
            "design", "llm_partner"} <= set(installed)


def test_voice_closure_loads_onto_a_bare_substrate():
    """The full voice stack (chat + speech + audio + native_codec) installs as
    graph data onto a bare substrate — the precondition for a voice agent boot."""
    s, agent = _bare()
    installed = load_seeds_into(s, agent, ["voice"])
    assert {"voice", "chat", "speech", "audio", "native_codec"} <= set(installed)


# ---------------------------------------------------------------------------
# the Rust loader directly — graph modularity, not agent modularity
# ---------------------------------------------------------------------------

def test_rust_loader_works_without_root_node():
    manifest = {
        "id": "transcoding_demo", "version": "0.1.0", "depends_on": [],
        "description": "",
        "nodes": [
            {"local_id": 0, "type": "VideoStream", "attrs": {"codec": "h264"}},
            {"local_id": 1, "type": "VideoStream", "attrs": {"codec": "av1"}},
        ],
        "edges": [
            {"src": {"local": 0}, "type": "transcoded_to",
             "tgt": {"local": 1}, "attrs": {}},
        ],
        "productions": [
            {"src": {"type": "VideoStream", "var": "src"},
             "edge_type": "transcoded_to",
             "tgt": {"type": "VideoStream", "var": "tgt"},
             "provenance": "transcoding_demo:transcoded_to"},
        ],
    }
    sub = srs.Substrate()
    summary = sub._inner.load_seed_manifest(manifest)    # no root_node
    assert summary["nodes"] == 2
    assert summary["edges"] == 1
    assert summary["productions"] == 1
    assert summary["id"] == "transcoding_demo"


def test_rust_loader_rejects_agent_role_when_root_missing():
    manifest = {
        "id": "bad", "version": "0.1.0", "depends_on": [], "description": "",
        "nodes": [{"local_id": 0, "type": "Microtheory",
                   "attrs": {"name": "test"}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "operates_in",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [],
    }
    sub = srs.Substrate()
    with pytest.raises(ValueError, match="agent_root"):
        sub._inner.load_seed_manifest(manifest)
