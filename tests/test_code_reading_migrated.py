"""CODE-1: CODE AS A READ REGISTER (domains/code_reading.py).

Discriminative gates for the smallest vertical slice: read a REAL repo
function into graph + Terms + concepts + comments, answer what it returns /
what it does / why, round-trip the compute-core through the EXISTING
graph-resident Python renderer.

  * REAL REPO CORPUS — two REAL, currently-committed functions
    (runners/dsl/python/substrate_rs/bitstream.py::_mp3_gain_to_db,
    scripts/born_selfconsistency_fixedpoint.py::sigma_star) read end-to-end:
    construction recognised, the emitted Term matches the real Python
    function on sample inputs (native evaluate == Python), the render
    round-trip (Term -> Python source -> exec) reproduces the SAME outputs.
  * ONE DELIBERATE NEAR-MISS — a REAL function whose Return is a comparison
    (domains/ground_reductions.py::_is_infinite_cyclic) is still READ (the
    codebook recognises `comparison_predicate`) but honestly ABSTAINS on
    Term emission (a named EmitError, never a fabricated/lossy Term).
  * THE SELF-GROWTH PROOF — a shape none of the four starter constructions
    covers (a BoolOp root) produces a residual, MINTS exactly one new
    construction via the sd loop, and a SECOND structurally-identical
    function recognises it WITHOUT a second mint.
  * COMMENTS AS NL + AGREEMENT — the docstring's first sentence is read
    through the existing English reading-collapse pipeline; the agreement
    stratum honestly reports both an AGREE case (shared content words) and a
    DIVERGE case (real technical prose whose words don't literally name the
    parameters) -- the code IS; the comment CLAIMS.
  * REGISTER ROUTING — a pasted Python snippet flows end-to-end through
    `register_source.route_reading`'s STRUCTURE approach (the `code`
    register) into this pipeline.
  * ONE DECODE, NOT PER-CONSTRUCTION BRANCHES — >=3 distinct constructions
    arise from the SAME `read_function` call path.
  * NO REGRESSION — the existing graph-resident Python renderer (factorial)
    is untouched by this module's additive RenderRule/ShapeSignature use.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_code_reading_migrated.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

srs = pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from domains import code_reading as cdr                   # noqa: E402
from domains import register_source as rs                 # noqa: E402


@pytest.fixture()
def agent():
    return WorldAdapter()


# --------------------------------------------------------------------------- #
#  REAL REPO CORPUS — sourced verbatim from this repository.
# --------------------------------------------------------------------------- #
MP3_SOURCE = '''
def _mp3_gain_to_db(global_gain: int) -> float:
    """ISO 11172-3 / MPEG-1 Layer III quantizer: the encoder scales
    samples by 2^((global_gain - 210)/4) before quantizing. Decoder
    inverts. Larger global_gain = louder source.

    Converting to dB:
      gain_linear = 2^((g - 210) / 4)
      gain_dB     = 20 * log10(gain_linear) = (g - 210) * 20/4 * log10(2)
                  approx 1.5051 * (g - 210)
    """
    return 1.5051 * (global_gain - 210)
'''
_mp3_gain_to_db_ref = lambda global_gain: 1.5051 * (global_gain - 210)  # noqa: E731

SIGMA_STAR_SOURCE = '''
def sigma_star(m):
    """Self-consistent localisation length l* = hbar^2/(G m^3) -- gravitational
    Bohr radius."""
    return HBAR ** 2 / (G * m ** 3)
'''
_HBAR, _G = 1.0545718e-34, 6.674e-11
_sigma_star_ref = lambda m: _HBAR ** 2 / (_G * m ** 3)  # noqa: E731

CYCLIC_SOURCE = '''
def _is_infinite_cyclic(n: int) -> bool:
    """HELD predicate: a factor is the INFINITE cyclic Z iff its order is 0 (the
    free-group factor)."""
    return n == 0
'''

@pytest.mark.parametrize("global_gain", [0, 100, 210, 255])
def test_mp3_gain_to_db_reads_and_round_trips(agent, global_gain):
    r = cdr.read_function(agent, MP3_SOURCE, "_mp3_gain_to_db")
    assert r["construction"] == "arithmetic_expression", r
    assert r["minted"] is False, "a seeded construction must not mint"
    assert r["emit_error"] is None, r["emit_error"]
    env = {"global_gain": global_gain}
    native = agent.inner.evaluate(r["term"], env)
    py = _mp3_gain_to_db_ref(global_gain)
    assert abs(float(native) - float(py)) < 1e-6, (native, py)
    rendered = r["rendered_python"]
    assert rendered and "(" in rendered
    ns: dict = {}
    exec("def f(global_gain):\n    return %s\n" % rendered, ns)
    out = ns["f"](global_gain)
    assert abs(float(out) - float(py)) < 1e-6, (out, py)


@pytest.mark.parametrize("m", [1.0, 3.0, 5.5])
def test_sigma_star_reads_and_round_trips(agent, m):
    r = cdr.read_function(agent, SIGMA_STAR_SOURCE, "sigma_star")
    assert r["construction"] == "arithmetic_expression", r
    assert r["minted"] is False
    assert r["emit_error"] is None, r["emit_error"]
    env = {"HBAR": _HBAR, "G": _G, "m": m}
    native = agent.inner.evaluate(r["term"], env)
    py = _sigma_star_ref(m)
    assert abs(float(native) - float(py)) < 1e-30 or abs(native - py) / abs(py) < 1e-6
    rendered = r["rendered_python"]
    assert rendered and "**" in rendered
    ns: dict = {}
    exec("def f(m):\n    HBAR = %r\n    G = %r\n    return %s\n"
        % (_HBAR, _G, rendered), ns)
    out = ns["f"](m)
    assert abs(out - py) / abs(py) < 1e-6, (out, py)


# --------------------------------------------------------------------------- #
#  CODE-1's DELIBERATE NEAR-MISS — CODE-2 (domains/ast_to_term.py's widened
#  emit_term) now covers Compare, so this real function FLIPS from honest-
#  abstain to evaluated ("the near-miss functions from CODE-1's gates flip
#  from honest-abstain to evaluated" — CODE-2's own mission text). The
#  construction recognition (comparison_predicate) is unchanged; only the
#  emission outcome moves, which is exactly the documented residual CODE-2
#  closes. See tests/test_code_semantics_migrated.py for CODE-2's own
#  comparison/boolean/ternary corpus and its still-honest boundaries
#  (Is/IsNot, chained-comparison edge cases, etc).
# --------------------------------------------------------------------------- #
def test_near_miss_comparison_predicate_now_reads_and_evaluates(agent):
    r = cdr.read_function(agent, CYCLIC_SOURCE, "_is_infinite_cyclic")
    assert r["construction"] == "comparison_predicate", r
    assert r["minted"] is False
    assert r["emit_error"] is None, r["emit_error"]
    assert r["term"] == {"type": "Eq", "a": {"type": "Var", "name": "n"},
                         "b": {"type": "Lit", "value": 0}}
    for n, expected in ((0, True), (1, False), (-3, False)):
        native = agent.inner.evaluate(r["term"], {"n": n})
        assert bool(native) == expected, (n, native, expected)
    assert "predicate" in cdr.answer_what(r)


# --------------------------------------------------------------------------- #
#  THE SELF-GROWTH PROOF — a genuinely uncovered shape MINTS, then re-decodes.
# --------------------------------------------------------------------------- #
BOOLOP_SOURCE = '''
def parity_flag(n):
    """Whether n is odd and positive."""
    return n % 2 == 1 and n > 0
'''
BOOLOP_SOURCE_2 = '''
def another_bool_gate(x, y):
    """Another BoolOp-rooted predicate."""
    return x > 0 and y > 0
'''


def test_uncovered_shape_mints_exactly_once_then_recognizes(agent):
    r1 = cdr.read_function(agent, BOOLOP_SOURCE, "parity_flag")
    assert r1["skeleton"] == [["BOOLOP"]]
    assert r1["minted"] is True, "a BoolOp root has no seeded construction"
    assert r1["construction"] == "learned_code_boolop"

    n_learned = sum(
        1 for n in agent.s.nodes("ShapeSignature")
        if agent.s.node(n)["attrs"].get("name") == "learned_code_boolop")
    assert n_learned == 1, "must install exactly one new construction"

    r2 = cdr.read_function(agent, BOOLOP_SOURCE_2, "another_bool_gate")
    assert r2["minted"] is False, "the SAME shape must now be covered, no re-mint"
    assert r2["construction"] == "learned_code_boolop"

    n_learned_after = sum(
        1 for n in agent.s.nodes("ShapeSignature")
        if agent.s.node(n)["attrs"].get("name") == "learned_code_boolop")
    assert n_learned_after == 1, "no duplicate install on the second occurrence"


# --------------------------------------------------------------------------- #
#  COMMENTS AS NL + THE HONEST AGREEMENT STRATUM (both verdicts demonstrated).
# --------------------------------------------------------------------------- #
RECT_AREA_SOURCE = '''
def rect_area(width, height):
    """A rectangle's area includes width and height."""
    return width * height
'''


def test_agreement_positive_shared_content_words(agent):
    r = cdr.read_function(agent, RECT_AREA_SOURCE, "rect_area")
    assert r["agreement"]["verdict"] == "agree", r["agreement"]
    assert set(r["agreement"]["shared"]) & {"width", "height"}
    why = cdr.answer_why(r)
    assert "agree" in why


def test_agreement_honest_divergence_on_real_technical_prose(agent):
    r = cdr.read_function(agent, SIGMA_STAR_SOURCE, "sigma_star")
    # the docstring uses symbolic notation (hbar^2/(G m^3)) that shares no
    # literal word with the parameter names HBAR/G/m -- an HONEST divergence,
    # not a silently-inflated "agree".
    assert r["agreement"]["verdict"] == "diverge", r["agreement"]
    why = cdr.answer_why(r)
    assert "diverge" in why
    assert "the code computes" in why


def test_no_docstring_reports_honestly(agent):
    src = "def bare(x):\n    return x + 1\n"
    r = cdr.read_function(agent, src, "bare")
    assert r["docstring"] is None
    assert r["comment"]["sentence"] is None
    why = cdr.answer_why(r)
    assert "no docstring" in why


# --------------------------------------------------------------------------- #
#  ONE DECODE, NOT PER-CONSTRUCTION BRANCHES.
# --------------------------------------------------------------------------- #
def test_battery_is_one_decode_not_per_construction_branches(agent):
    verdicts = {
        "mp3": cdr.read_function(agent, MP3_SOURCE, "_mp3_gain_to_db")["construction"],
        "sigma": cdr.read_function(agent, SIGMA_STAR_SOURCE, "sigma_star")["construction"],
        "cyclic": cdr.read_function(agent, CYCLIC_SOURCE, "_is_infinite_cyclic")["construction"],
        "boolop": cdr.read_function(agent, BOOLOP_SOURCE, "parity_flag")["construction"],
    }
    assert len(set(verdicts.values())) >= 3, verdicts


# --------------------------------------------------------------------------- #
#  REGISTER ROUTING — a pasted Python snippet flows end-to-end.
# --------------------------------------------------------------------------- #
def test_register_routes_code_snippet_to_code_reading(agent):
    route = rs.route_reading(agent, SIGMA_STAR_SOURCE, hint="code")
    assert route["register"] == "code"
    assert route["read_approach"] == "structure"
    assert route["answer"] == "sigma_star"
    fn = route["result"]["functions"]["sigma_star"]
    assert fn["construction"] == "arithmetic_expression"
    assert fn["rendered_python"]


def test_register_routes_by_shape_no_hint(agent):
    # format_channel's own structural-layout detector recognises code WITHOUT
    # a hint -- untouched machinery this module only DISPATCHES into.
    route = rs.route_reading(agent, MP3_SOURCE)
    assert route["read_approach"] == "structure"
    assert route["answer"] == "_mp3_gain_to_db"


# --------------------------------------------------------------------------- #
#  NO REGRESSION — the existing graph-resident Python renderer is untouched.
# --------------------------------------------------------------------------- #
def test_existing_renderer_still_works_after_code_reading_use(agent):
    # exercise code_reading first (installs its own ShapeSignatures + RenderRules)
    cdr.read_function(agent, MP3_SOURCE, "_mp3_gain_to_db")
    # the renderer was already seeded by code_reading's own render call; a
    # plain arithmetic term still renders identically to the direct API.
    from substrate.jsonio import term_from_json
    term = term_from_json({"type": "Plus", "items": [{"type": "Lit", "value": 1},
                                                      {"type": "Lit", "value": 2}]})
    assert agent.render(term, "python") == "(1 + 2)"
