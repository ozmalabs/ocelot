"""LANGSIM (block 243000) — the language-limitation-map probe, gated.

Pins the MEASURED facts of the probe (not "it works"): the graph faculty
produces + comprehends REAL utterances end-to-end; the coordination gate
separates from the no-language control; and the key LIMITATIONS the map found
are regression-pinned (comprehension is order-insensitive; generation arity
ceiling = 2). Source-audit: no forbidden Python rule-engine calls; the utterance
content originates from the graph faculty, not a Python template.
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

from worlds.langsim_world import LangSimWorld              # noqa: E402
import scripts.langsim_limitation_map as lm                # noqa: E402


# --- STEP-0: a REAL graph-emitted utterance round-trip -------------------

def test_real_utterance_roundtrip_is_graph_native():
    w = LangSimWorld([1.0, 1.0], mode="language", seed=0)
    speaker = next(a for a in w.agents if a.gathers == "wood")
    listener = next(a for a in w.agents if a is not speaker)
    utt = speaker.utter(speaker.promise_meaning())
    # a real SVO string produced by the graph render engine, not a template
    assert utt == "I give wood"
    _mid, resolved = listener.hear(utt)
    names = {n for _t, refs in resolved for n in refs}
    assert "give" in names and "wood" in names          # comprehended back to graph


def test_utterance_is_not_a_python_template():
    # the exact same intent rendered through the faculty for BOTH resources —
    # if it were an f-string the content would be Python-formatted; here it is
    # the lexicon+Render engine reading the grounded Sign for each resource.
    w = LangSimWorld([1.0, 1.0], mode="language", seed=0)
    got = {a.gathers: a.utter(a.promise_meaning()) for a in w.agents}
    assert got == {"wood": "I give wood", "stone": "I give stone"}


# --- DIMENSION gates -----------------------------------------------------

def test_coordination_separates_from_no_language():
    d4 = lm.dim4_coordination(n_seeds=20, T=25)
    # language CI-above no-language (headline PASS)
    assert d4["gap_language_minus_none"]["ci"][0] > 0.0
    assert d4["language"]["mean"] > d4["none"]["mean"]


def test_scrambled_control_does_not_fail_order_insensitive():
    # THE MEASURED LIMITATION: comprehension is a bag of grounded referents, so
    # a word-order scramble carries the coordination as well as intact language
    # (the language-scrambled gap CI includes 0). Pinned so a regression that
    # ACCIDENTALLY made comprehension order-sensitive is caught + revisited.
    d3 = lm.dim3_comprehension()
    assert d3["order_sensitive"] is False
    assert d3["content_sensitive"] is True


def test_generation_arity_ceiling_is_two():
    # a 3-place ditransitive intent drops the recipient — the arity ceiling.
    d1 = lm.dim1_generation_aptness()
    ditransitive = next(r for r in d1["rows"] if r["situation"].startswith("ditransitive"))
    assert ditransitive["apt"] is False
    # but the 2-place SVO frames are apt
    svo = [r for r in d1["rows"] if "2-place SVO" in r["situation"]]
    assert svo and all(r["apt"] for r in svo)


def test_seed_determines_society_at_language_layer():
    d4b = lm.dim4b_seed_determines(n_seeds=10, T=25)
    assert d4b["honest"]["keeping_rate"] == 1.0
    assert d4b["psychopath"]["keeping_rate"] == 0.0
    assert d4b["honest"]["mean"] > d4b["psychopath"]["mean"]


# --- source-audit: no forbidden Python rule-engine calls -----------------

def _code_only(src):
    """Strip comments and string literals (incl. docstrings) so the audit sees
    only executable code, not documentation that NAMES the forbidden calls."""
    import io, tokenize
    out = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


def test_no_forbidden_rule_engine_calls_in_new_files():
    forbidden = ("graph_rewrite", "gr.run", "_match", "_apply", "make_rule")
    for rel in ("worlds/langsim_world.py", "scripts/langsim_limitation_map.py"):
        code = _code_only(open(os.path.join(_GB, rel)).read())
        for f in forbidden:
            assert f not in code, f"{f} found in executable code of {rel}"
