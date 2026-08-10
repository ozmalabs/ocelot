"""test_reader_tighten — TIGHTEN THE RECOGNITION READER'S COST MODEL so a FULLY-joined
run of KNOWN words decomposes into them, WITHOUT over-segmenting real words.

The 515b5c99 residual (stated honestly there): the min-token Viterbi over characters
against the lexicon codebook (`instruction_reading._lattice_decode`) sees through a
SINGLE stray space ('what areyou' -> [what, are, you]) but a FULLY-joined run of
known words ('whatareyou') stayed ONE OOV token — one OOV span was cheaper than three
lexicon words. THE FIX is a COST-MODEL correction ONLY (no regex, no whitespace
delimiter, the SAME lattice): recognition is the STRONG hit, OOV the DEAREST fallback.
A known-word match undercuts an OOV span per character, and an OOV run carries a fixed
OPEN cost reclaimed only by covering the WHOLE run with known words — so a fully
known-word cover BEATS one OOV token; while the per-char OOV surcharge stays strictly
below the per-word LEX cost for any word length, so pulling a known PREFIX off an
otherwise-unknown run never pays and longer/fewer known matches win — a REAL word
stays WHOLE.

These gates are DISCRIMINATIVE (donkey=0):
  * DECOMPOSES — a fully-joined run of known words recovers the words (verbatim).
  * NO OVER-SEGMENTATION (the guard) — a battery of real words each stays WHOLE,
    even those containing shorter known sub-words (verbatim; none fragment).
  * GENUINE-OOV — a run with no full known cover stays ONE OOV token (verbatim).
  * SINGLE-SPACE robustness — the 515b5c99 case unbroken.
  * NO REGEX / NO WHITESPACE-DELIM — the source stays AST-clean (cost model only).

Run: PYTHONPATH=runners/dsl/python:.:scripts pytest \
     tests/test_reader_tighten.py -p no:randomly
"""
from __future__ import annotations

import ast
import io
import contextlib

import pytest


@pytest.fixture(scope="module")
def agent():
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        from substrate.world_adapter import WorldAdapter
        from substrate.boot_all import load_all_seeds
        import domains.operational_planning as op
        a = WorldAdapter(seeds=())
        load_all_seeds(a)
        op._ensure_seed(a)
    return a


@pytest.fixture(scope="module")
def ir():
    import domains.instruction_reading as _ir
    return _ir


def _words(ir, agent, text: str) -> list:
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(buf):
        return ir.segment(agent, text)["words"]


# ===========================================================================
# 1. DECOMPOSES (the headline): a FULLY-joined run of KNOWN words recovers the
#    words — a fully-known cover now beats one OOV token. VERBATIM.
# ===========================================================================
def test_fully_joined_known_run_decomposes(agent, ir):
    cases = {
        "whatareyou": ["what", "are", "you"],
        "bulkloadwikipedia": ["bulk", "load", "wikipedia"],
        "measuretiming": ["measure", "timing"],
    }
    print("\n=== DECOMPOSES (fully-joined known run -> the words) ===")
    for joined, want in cases.items():
        got = _words(ir, agent, joined)
        print(f"  {joined!r:22} -> {got}")
        assert got == want, (joined, got, want)


# ===========================================================================
# 2. NO OVER-SEGMENTATION (the make-or-break GUARD): a battery of REAL words each
#    stays WHOLE — one token — even those that contain shorter known sub-words
#    (timing>tim, under<understand). Decomposition wins ONLY on a full known
#    cover with no single longer known word covering the run. VERBATIM; none
#    fragment.
# ===========================================================================
def test_real_words_stay_whole_no_over_segmentation(agent, ir):
    battery = ["timing", "measure", "wikipedia", "perceive", "sufficient",
               "prioritize", "understand", "report", "judge", "warm",
               "wordnet", "sufficiently"]
    print("\n=== NO OVER-SEGMENTATION (real words stay WHOLE) ===")
    fragmented = []
    for w in battery:
        got = _words(ir, agent, w)
        print(f"  {w!r:16} -> {got}")
        if got != [w]:
            fragmented.append((w, got))
    assert fragmented == [], fragmented


# ===========================================================================
# 3. GENUINE-OOV stays OOV: a run with NO full known-word cover stays ONE OOV
#    token — it is NOT force-fragmented. VERBATIM.
# ===========================================================================
def test_genuine_oov_stays_one_token(agent, ir):
    print("\n=== GENUINE-OOV stays one token ===")
    for junk in ("xghqz", "flarbnth"):
        got = _words(ir, agent, junk)
        print(f"  {junk!r:12} -> {got}")
        assert got == [junk], (junk, got)


# ===========================================================================
# 4. SINGLE-SPACE robustness — the 515b5c99 case still holds: a single stray
#    space inside a known-word run still recovers the words.
# ===========================================================================
def test_single_space_still_holds(agent, ir):
    print("\n=== SINGLE-SPACE robustness (515b5c99, unbroken) ===")
    got = _words(ir, agent, "what areyou")
    print(f"  {'what areyou'!r:16} -> {got}")
    assert got == ["what", "are", "you"], got
    # and the plain joined-known case the prior residual mentioned
    assert _words(ir, agent, "loadtiming") == ["load", "timing"]


# ===========================================================================
# 5. THE FIX IS COST-MODEL ONLY: no regex, no whitespace .split() tokeniser was
#    (re)introduced. AST-audit instruction_reading stays CLEAN.
# ===========================================================================
def _audit_module(modname: str) -> list:
    import importlib, inspect
    src = inspect.getsource(importlib.import_module(modname))
    findings = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split(".")[0] == "re":
                    findings.append(f"import {n.name}")
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "re":
                findings.append(f"from {node.module} import ...")
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id == "re":
            findings.append(f"re.{node.attr}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("split", "rsplit", "splitlines"):
            findings.append(f".{node.func.attr}() call")
    return findings


def test_reader_stays_ast_clean_no_regex_no_whitespace():
    findings = _audit_module("domains.instruction_reading")
    print("\n=== AST AUDIT (instruction_reading) ===")
    print(f"  domains.instruction_reading: "
          f"{'CLEAN (no re, no .split())' if not findings else findings}")
    assert findings == [], findings
