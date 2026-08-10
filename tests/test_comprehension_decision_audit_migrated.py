"""Wave-4 DECISION AUDIT — the Python KIND ladder no longer executes live.

The speech-act KIND decision migrated to graph rules
(seeds/speech_act_classify.json); `comprehend_text._classify_kind` is retained
ONLY as (a) the fixture-capture oracle and (b) the documented
no-native-substrate fallback. This audit pins that boundary so the migration
cannot silently regress (the ink work's no-Python-decision audit precedent):

  * with the Rust engine available (it is, on every bench run), the ladder
    body NEVER executes — neither on direct comprehend_text calls nor on the
    live converse() turn path;
  * the fallback is reachable ONLY when the rule classifier abstains
    (documents the design rather than leaving it implicit);
  * the module's only live call site of the ladder is the guarded fallback
    inside comprehend_text (source audit via AST).

The companion burn-down inventory of every REMAINING Python decision on the
comprehension path is docs/comprehension_decision_ledger.md.
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import comprehend_text as ct                 # noqa: E402


def _boom(*_a, **_k):
    raise AssertionError("Python _classify_kind executed on the live path")


def test_direct_calls_never_run_the_python_ladder(monkeypatch):
    """comprehend_text (direct-caller path, agent=None) classifies every kind
    via the seeded rules on a scratch Message — the Python ladder must not
    run (the Rust engine is available on every bench run)."""
    monkeypatch.setattr(ct, "_classify_kind", _boom)
    assert ct.comprehend_text(None, "Why is the sky blue?").kind == "question"
    assert ct.comprehend_text(None, "look left").kind == "instruction"
    assert ct.comprehend_text(None, "the sky is blue").kind == "statement"
    # aux-inversion (copula + auxiliary) + leading-wh, the non-'?' signals
    assert ct.comprehend_text(None, "is it blue").kind == "question"
    assert ct.comprehend_text(None, "do you know").kind == "question"
    assert ct.comprehend_text(None, "what happened then").kind == "question"


def test_live_converse_kind_is_graph_minted(monkeypatch):
    """The live turn path: the kind on the graph comes from the agent's OWN
    held sak rules (minted as sak_kind on the inbound Message and echoed into
    comp_kind), never from the Python ladder."""
    from substrate.world_adapter import WorldAdapter
    monkeypatch.setattr(ct, "_classify_kind", _boom)
    a = WorldAdapter(seeds=())
    a.converse("Summarise the report.", speech_act="request")
    mid = a._last_turn_inbound
    attrs = a.s.node(mid)["attrs"]
    assert attrs.get("sak_kind") == "instruction", "the rules must mint the kind"
    assert attrs.get("comp_kind") == "instruction"
    a.converse("Why is the sky blue?", speech_act="question")
    attrs = a.s.node(a._last_turn_inbound)["attrs"]
    assert attrs.get("sak_kind") == "question"
    assert attrs.get("comp_kind") == "question"


def test_fallback_reachable_only_when_rules_abstain(monkeypatch):
    """The design boundary, made explicit: the Python ladder is the documented
    no-engine fallback — it runs iff the rule classifier abstains (returns
    None), and never otherwise."""
    calls = []
    real = ct._classify_kind

    def _spy(text, frame):
        calls.append(text)
        return real(text, frame)

    monkeypatch.setattr(ct, "_classify_kind", _spy)
    ct.comprehend_text(None, "the sky is blue")
    assert not calls, "rules decided -> the ladder must not run"
    monkeypatch.setattr(ct, "_classify_kind_rules", lambda _sig: None)
    comp = ct.comprehend_text(None, "the sky is blue")
    assert calls and comp.kind == "statement", (
        "with the engine unavailable the documented fallback must still classify")


def test_source_audit_single_guarded_fallback_call_site():
    """AST audit: `_classify_kind` is invoked in exactly ONE place in the
    module — the `if kind is None` fallback inside comprehend_text. Any new
    call site is a migration regression."""
    tree = ast.parse(inspect.getsource(ct))
    sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "_classify_kind":
            sites.append(node)
    assert len(sites) == 1, f"expected exactly one fallback call site, got {len(sites)}"
    # ... and that one site sits under an `if kind is None:` guard in
    # comprehend_text (the documented no-engine fallback).
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "comprehend_text")
    guarded = False
    for node in ast.walk(fn):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) \
                and isinstance(node.test.left, ast.Name) and node.test.left.id == "kind":
            if any(s in ast.walk(node) for s in sites):
                guarded = True
    assert guarded, "the fallback call must be guarded by `if kind is None`"
