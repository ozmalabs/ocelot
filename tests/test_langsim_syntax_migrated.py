"""LANGSIM SYNTAX-CARRYING (block 244000) — gated.

Pins the MEASURED build-out of langsim's #1 limitation: comprehension now carries
SYNTAX (word ORDER -> a structured Intent), so the coordination gate inverts —
the SCRAMBLED control DROPS toward the no-language floor (langsim's headline
limitation was that it could NOT). Also: order-sensitivity, role-swap-by-order,
3-place generation keeps the recipient (arity ceiling lifted), the structured
Intent is glass-box in the live graph, and the source-audit is clean. Langsim's
OWN gates are untouched (regression) — they pin the OLD referent-bag path.
"""
from __future__ import annotations

import os
import sys

import pytest

pytest.importorskip("substrate_rs")

_GB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_GB, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_GB, "runners", "dsl", "python"))
if _GB not in sys.path:
    sys.path.insert(0, _GB)

from domains import langsim_syntax as ls                     # noqa: E402
from worlds.langsim_syntax_world import LangSimSyntaxWorld    # noqa: E402
import scripts.langsim_syntax_map as sm                       # noqa: E402


# --- G-syntax-carries (HEADLINE): scrambled control DROPS ----------------

def test_scrambled_control_drops_to_floor_headline():
    """THE HEADLINE. With a syntax-carrying gate, a word-order scramble no
    longer carries the offer: gap language-scrambled CI > 0 (scrambled drops
    toward the no-language floor), while intact language holds above no-language.
    This is the exact inversion of langsim's DIM 4 (scrambled did NOT fail)."""
    c = sm.dim_syntax_coordination(n_seeds=20, T=25)
    # intact language still coordinates above silence
    assert c["gap_language_minus_none"]["ci"][0] > 0.0
    assert c["language"]["mean"] > c["none"]["mean"]
    # HEADLINE: scrambled now DROPS -- language strictly above scrambled
    assert c["gap_language_minus_scrambled"]["ci"][0] > 0.0
    assert c["language"]["mean"] > c["scrambled"]["mean"]
    # scrambled sits at/below the no-language floor (syntax carried the signal)
    assert c["scrambled"]["mean"] <= c["none"]["mean"] + 0.5


# --- G-comprehension-order-sensitive -------------------------------------

def test_comprehension_is_order_sensitive():
    intact = ls.parse_intent("I give wood")
    scrambled = ls.parse_intent("wood I give")
    assert intact == {"predicate": "give", "agent": "I", "patient": "wood",
                      "recipient": None}
    # scramble breaks the patient binding -> DIFFERENT structured Intent
    assert scrambled != intact
    assert scrambled["patient"] != "wood"
    # the gate sees the difference (langsim's order_sensitive was False)
    assert ls.structured_offer_holds(intact, "wood") is True
    assert ls.structured_offer_holds(scrambled, "wood") is False


def test_role_swap_swaps_agent_and_patient_by_order():
    intact = ls.parse_intent("I give wood")
    swapped = ls.parse_intent("wood give I")
    assert swapped["agent"] == intact["patient"]   # wood is now the agent
    assert swapped["patient"] == intact["agent"]   # I is now the patient


def test_content_sensitivity_retained():
    intact = ls.parse_intent("I give wood")
    wrong = ls.parse_intent("I give stone")
    assert ls.structured_offer_holds(intact, "wood") is True
    assert ls.structured_offer_holds(wrong, "wood") is False


# --- G-generation-3-place: recipient kept + round-trip -------------------

def test_ditransitive_keeps_recipient_and_round_trips():
    utt = ls.render_ditransitive("I", "wood", "you")
    assert utt == "I give wood to you"          # recipient NOT dropped
    back = ls.parse_intent(utt)
    assert back == {"predicate": "give", "agent": "I", "patient": "wood",
                    "recipient": "you"}          # all three roles round-trip


def test_generation_aptness_is_full():
    g = sm.dim_generation_3place()
    assert g["aptness_rate"] == 1.0             # vs langsim ditransitive: dropped


# --- G-glass-box: structured Intent readable in the live graph -----------

def test_structured_intent_is_a_node_in_the_live_graph():
    w = LangSimSyntaxWorld([1.0, 1.0], mode="language", seed=0)
    listener = w.agents[0]
    listener.hear("I give wood")
    node = listener.last_intent_node()
    assert node is not None
    assert node["predicate"] == "give"
    assert node["agent"] == "I"
    assert node["patient"] == "wood"
    # readable via graph_to_dict (glass-box)
    dumped = listener.wa.inner.graph_to_dict()
    assert any(n.get("type") == "Intent" for n in dumped.get("nodes", []))


# --- G-discipline: source-audit clean ------------------------------------

def _code_only(src):
    import io
    import tokenize
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


def test_no_forbidden_rule_engine_calls_in_new_files():
    forbidden = ("graph_rewrite", "gr.run", "_match", "_apply", "make_rule")
    for rel in ("domains/langsim_syntax.py", "worlds/langsim_syntax_world.py",
                "scripts/langsim_syntax_map.py"):
        code = _code_only(open(os.path.join(_GB, rel)).read())
        for f in forbidden:
            assert f not in code, f"{f} found in executable code of {rel}"
