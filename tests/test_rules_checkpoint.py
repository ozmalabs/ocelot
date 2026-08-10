"""Checkpoint-resume must not lobotomise the agent.

THE BUG: `WorldAdapter.save(path)` persisted the graph (`graph_to_dict`) and
the dynamic Γ grammar (`grammar_to_json`), but NOT the Rust rule engine's
`add_rule` rule store — every Rule the seed loader installs, plus everything
the agent authors at runtime. After `WorldAdapter.load(path)`,
`inner.rule_count()` dropped 350 -> 0: a resumed session could ingest text
but could never reply (no rules to build the Intent / reply / render chain).

THE FIX: `Substrate.export_rules()` / `Substrate.import_rules()` (Rust,
`runners/dsl/src/py.rs`) round-trip the rule store — including tombstoned
(`remove_rule`d) slots, so `RuleIdx`s stay stable — through the same dict
dialect `add_rule` already accepts. `WorldAdapter.save` now writes a
`"rules"` key; `WorldAdapter.load` calls `import_rules` right after
`graph_from_dict`, or warns (not crashes) on an old checkpoint that predates
this key.

This file exercises the fix at the WorldAdapter level (a) and directly
against the native `substrate_rs._native.Substrate` rule store (b, c, d) —
mirroring the existing low-level style in `tests/test_remove_rule_graph_diff.py`.
"""
from __future__ import annotations

import json
import sys
import os

import pytest

native = pytest.importorskip("substrate_rs._native")
ext = pytest.importorskip("substrate_rs.ext")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter  # noqa: E402


def _open_substrate(node_types, edge_types):
    """A fresh native Substrate with a fully permissive grammar over the
    given node/edge type vocabulary (same helper shape as
    `test_remove_rule_graph_diff.py`), so the checked `add_node`/`add_edge`
    path accepts anything in that vocabulary."""
    s = native.Substrate()
    for src_t in node_types:
        for tgt_t in node_types:
            for et in edge_types:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


# ---------------------------------------------------------------------------
# (a) fresh boot -> save -> load -> rule_count unchanged, converse() identical
# ---------------------------------------------------------------------------

def _boot_chat_adapter():
    """A small, fast chat-capable seed set (the CHAT_SEEDS list from
    scripts/converse_demo.py) — enough for converse() to actually reply,
    without the slower on-disk-library teacher chain."""
    from scripts.converse_demo import CHAT_SEEDS, BASE_VOCAB, _payload
    from substrate.seed_loader import manifest_for

    adapter = WorldAdapter()
    for sid in CHAT_SEEDS:
        adapter.inner.load_seed_manifest(manifest_for(sid), adapter.agent)
    adapter.install_register_lexicon()
    for word, gloss in BASE_VOCAB.items():
        adapter.learn_from_teacher(word, _payload(word, gloss))
    return adapter


def test_fresh_boot_round_trips_rule_count_and_converse_reply(tmp_path):
    wa = _boot_chat_adapter()
    assert wa.inner.rule_count() > 0, "a booted chat agent must have installed rules"

    reply_before = wa.converse("hello")
    assert reply_before, "a fresh boot must be able to reply"
    # `converse()` itself can lazily install new rules (e.g. render rules
    # admitted on first use) — the rule count to compare across save/load is
    # therefore the state AT SAVE TIME, after that first turn, not before it.
    n = wa.inner.rule_count()

    path = str(tmp_path / "ckpt.json")
    wa.save(path)
    loaded = WorldAdapter.load(path)

    assert loaded.inner.rule_count() == n, (
        "save/load must not change the rule-slot count "
        f"(had {n}, now {loaded.inner.rule_count()})"
    )
    reply_after = loaded.converse("hello")
    assert reply_after == reply_before, (
        "a resumed agent must answer identically to the pre-save agent — "
        f"before={reply_before!r} after={reply_after!r}"
    )


# ---------------------------------------------------------------------------
# (b) runtime-authored rule survives save/load and still fires
# ---------------------------------------------------------------------------

def test_runtime_authored_rule_fires_after_reload(tmp_path):
    wa = _boot_chat_adapter()
    n_before = wa.inner.rule_count()

    # Author a trivial rule at runtime, the way a self-authoring agent would
    # (CLAUDE.md: "everything the agent authors at runtime").
    wa.inner.add_production({
        "src": {"type": "Trigger", "var": "src"},
        "edge_type": "triggers",
        "tgt": {"type": "Target", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "test:runtime_rule",
    })
    wa.inner.add_production({
        "src": {"type": "Minted", "var": "src"},
        "edge_type": "triggers",
        "tgt": {"type": "Minted", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "test:runtime_rule2",
    })
    a = wa.s.add_node("Trigger", {})
    b = wa.s.add_node("Target", {})
    wa.inner.add_edge_unchecked(a, "triggers", b)
    idx = ext.add_rule(
        wa.inner,
        name="test_runtime_mint",
        match_edges=[("src", "triggers", "tgt")],
        effects=[ext.AddNode("m", "Minted", {"k": 42})],
    )
    assert idx == n_before, "add_rule must hand out the next sequential slot"
    assert wa.inner.rule_count() == n_before + 1

    path = str(tmp_path / "ckpt.json")
    wa.save(path)
    loaded = WorldAdapter.load(path)

    assert loaded.inner.rule_count() == n_before + 1
    assert len(loaded.s.nodes("Minted")) == 0, "not fired yet"
    fired = ext.apply_rule_once(loaded.inner, idx)
    assert fired, "the runtime-authored rule must still fire after reload"
    minted = loaded.s.nodes("Minted")
    assert len(minted) == 1
    assert loaded.s.node(minted[0])["attrs"].get("k") == 42, (
        "the rule's effect (including its literal attr) must round-trip exactly"
    )


# ---------------------------------------------------------------------------
# (c) tombstone: stays inactive after reload; later rules' indices unchanged
# ---------------------------------------------------------------------------

def test_tombstoned_rule_stays_inactive_and_later_indices_are_stable(tmp_path):
    s = _open_substrate(["N"], ["A", "B", "C"])
    n1 = s.add_node("N", {})
    n2 = s.add_node("N", {})
    s.add_edge(n1, "A", n2, {})
    s.add_edge(n1, "B", n2, {})
    s.add_edge(n1, "C", n2, {})

    idx_a = ext.add_rule(s, name="rule_A", match_edges=[("x", "A", "y")],
                          effects=[ext.AddNode("m", "MintedA", {})])
    idx_b = ext.add_rule(s, name="rule_B", match_edges=[("x", "B", "y")],
                          effects=[ext.AddNode("m", "MintedB", {})])
    idx_c = ext.add_rule(s, name="rule_C", match_edges=[("x", "C", "y")],
                          effects=[ext.AddNode("m", "MintedC", {})])
    assert (idx_a, idx_b, idx_c) == (0, 1, 2)

    assert s.remove_rule(idx_b) is True   # tombstone the MIDDLE rule

    exported = s.export_rules()
    assert len(exported) == 3
    assert [r["active"] for r in exported] == [True, False, True]

    # Round-trip via a bare JSON file (exercises exactly what save/load do).
    path = str(tmp_path / "rules.json")
    with open(path, "w") as f:
        json.dump({"graph": s.graph_to_dict(), "rules": exported}, f)
    with open(path) as f:
        blob = json.load(f)

    s2 = native.Substrate()
    s2.graph_from_dict(blob["graph"])
    n_imported = s2.import_rules(blob["rules"])
    assert n_imported == 3

    reimported = s2.export_rules()
    assert [r["active"] for r in reimported] == [True, False, True], (
        "tombstone state must survive the round-trip, and idx_a/idx_c "
        "(either side of the tombstoned slot) must be unaffected"
    )
    assert reimported[0]["name"] == "rule_A"
    assert reimported[1]["name"] == "rule_B"
    assert reimported[2]["name"] == "rule_C"

    # Behaviour matches: A and C fire, B (tombstoned) never does — and the
    # indices are the SAME ones (idx_a/idx_b/idx_c) on the reloaded store.
    s2.run_rules()
    assert len(s2.nodes("MintedA")) == 1
    assert len(s2.nodes("MintedB")) == 0, "tombstoned rule must not fire post-reload"
    assert len(s2.nodes("MintedC")) == 1
    assert s2.remove_rule(idx_b) is False, "already-tombstoned slot stays a no-op"
    assert s2.rule_count() == 3, "no compaction — slot count preserved exactly"


# ---------------------------------------------------------------------------
# (d) old-checkpoint fallback: a save file missing "rules" loads (warns, no crash)
# ---------------------------------------------------------------------------

def test_old_checkpoint_without_rules_key_loads_with_warning(tmp_path, caplog):
    wa = _boot_chat_adapter()
    assert wa.inner.rule_count() > 0

    path = str(tmp_path / "old_ckpt.json")
    wa.save(path)
    with open(path) as f:
        blob = json.load(f)
    assert "rules" in blob
    del blob["rules"]   # simulate a checkpoint saved before this fix
    with open(path, "w") as f:
        json.dump(blob, f)

    import logging
    caplog.set_level(logging.WARNING)
    loaded = WorldAdapter.load(path)   # must NOT raise

    assert loaded.inner.rule_count() == 0, (
        "an old checkpoint with no rule data honestly comes back rule-less"
    )
    assert any("rules" in rec.message for rec in caplog.records), (
        "loading a rules-less checkpoint must warn, not silently proceed"
    )
    # The graph itself is still intact.
    assert loaded.s.node_count() == wa.s.node_count()
