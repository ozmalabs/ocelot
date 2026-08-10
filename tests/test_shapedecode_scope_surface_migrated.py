"""ShapeDecode `codebook_scope` / `exclude` must read a Term-BUILT string.

The defect (ENGINE_ARGMAX_DETERMINISM_RESULTS.md §3): `apply_scope` and
`apply_exclude` matched `Value::Str` alone, so every `Value::Surface(Text)`
element — the ONLY shape a rule-built string can have, because `evaluate()`
holds an immutable `&Interner` — was dropped SILENTLY. Neither reader fails
closed:

  * an all-dropped `codebook_scope` leaves the codebook UNRESTRICTED, so a
    decode asking "score this ONE part" returns the WHOLE CODEBOOK'S MAXIMUM;
  * an all-dropped `exclude` excludes NOTHING.

Both return a confident wrong number with no warning. `load_parts` in the same
file already accepts both spellings (`str_shaped`), which is what made this
invisible: the part IS in the codebook and IS scopeable by its interned name —
only the rule-built spelling of the same name fails.

These assertions are RED on the pre-fix engine (measured: scope->`fractal` gave
36 where 0 is correct; exclude->`r00` gave 36 where 14 is correct) and GREEN
after it. They are NOT a regression test for the §4.2 `Argmax` anomaly, which
this defect is separately shown NOT to explain (§4 of the results).
"""
import json

import pytest

pytestmark = pytest.mark.migrated


def _world():
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


#: Two held parts over the SAME relation vocabulary. `alpha` covers the goal
#: exactly; `beta` covers none of it. Both names are plain interned strings —
#: the test varies only HOW the scope/exclude NAMES them.
GOAL = [["cell", 0, 0, "v1"], ["cell", 0, 1, "v2"], ["cell", 1, 0, "v3"]]
ALPHA = GOAL
BETA = [["cell", 9, 9, "v0"], ["cell", 9, 8, "v0"], ["cell", 9, 7, "v0"]]


def _hold(s, name, sig):
    return s.add_node("ShapeSignature", {
        "name": name, "signature": json.dumps(sig), "kind": "faculty",
        "faculty": name, "dim_types": ["pred", "coord:r", "coord:c", "val"]})


def _decode(native, obs, *, scope=None, exclude=None):
    term = {"type": "ShapeDecode",
            "goal": {"type": "Attr", "node": {"type": "Var", "name": "obs"},
                     "key": "signature"},
            "codebook_type": "ShapeSignature",
            "field": "covered_count", "beam": 1, "max_steps": 1, "cand_k": 1}
    if scope is not None:
        term["codebook_scope"] = scope
    if exclude is not None:
        term["exclude"] = exclude
    return native.evaluate(term, {"obs": obs})


def _lit_set(text):
    """The name as an INTERNED string — `Value::Str`. Always worked."""
    return {"type": "SetT", "items": [{"type": "Lit", "value": text}]}


def _built_set(text):
    """The SAME name as a TERM-BUILT string — `Value::Surface(Text)`.

    Split in half and concatenated so the result cannot be the interned literal
    by accident; `StringConcat` returns Surface(Text) by construction."""
    half = len(text) // 2
    return {"type": "SetT", "items": [{"type": "StringConcat", "parts": [
        {"type": "Lit", "value": text[:half]},
        {"type": "Lit", "value": text[half:]}]}]}


@pytest.fixture()
def held():
    s, ag, native = _world()
    _hold(s, "alpha", ALPHA)
    _hold(s, "beta", BETA)
    obs = s.add_node("Observation", {"signature": GOAL, "status": "probe",
                                     "dim_types": ["pred", "coord:r", "coord:c", "val"]})
    s.add_edge(ag, "observed", obs)
    return s, native, obs


def test_a_term_built_string_really_is_a_surface(held):
    """Guard on the test's own premise: StringConcat is NOT an interned Str."""
    _s, native, _obs = held
    built = native.evaluate({"type": "StringConcat", "parts": [
        {"type": "Lit", "value": "al"}, {"type": "Lit", "value": "pha"}]}, {})
    assert built == "alpha", "StringConcat must produce the same TEXT"


def test_scope_by_a_term_built_name_scopes_to_that_part(held):
    """A scope naming `beta` must score BETA — 0 — not the codebook maximum."""
    _s, native, obs = held
    interned = _decode(native, obs, scope=_lit_set("beta"))
    assert interned == 0, "premise: beta covers none of the goal"
    unrestricted = _decode(native, obs)
    assert unrestricted == len(GOAL), "premise: the codebook max is a full cover"

    built = _decode(native, obs, scope=_built_set("beta"))
    assert built == interned, (
        "a Term-BUILT scope name must scope exactly like the interned spelling; "
        f"got {built}, expected {interned}. Getting {unrestricted} here is the "
        "defect: the element was dropped and the codebook silently went "
        "UNRESTRICTED, turning a per-candidate score into the global maximum.")


def test_scope_by_a_term_built_name_still_selects_the_right_part(held):
    """The inclusion direction: naming `alpha` must still select alpha."""
    _s, native, obs = held
    assert _decode(native, obs, scope=_built_set("alpha")) == \
        _decode(native, obs, scope=_lit_set("alpha")) == len(GOAL)


def test_exclude_by_a_term_built_name_actually_excludes(held):
    """An exclude naming `alpha` must remove it — the score must DROP."""
    _s, native, obs = held
    interned = _decode(native, obs, exclude=_lit_set("alpha"))
    assert interned < len(GOAL), "premise: excluding alpha must lower the score"

    built = _decode(native, obs, exclude=_built_set("alpha"))
    assert built == interned, (
        "a Term-BUILT exclude name must exclude exactly like the interned "
        f"spelling; got {built}, expected {interned}. Getting {len(GOAL)} here "
        "is the defect: the element was dropped and NOTHING was excluded.")


def test_absent_scope_is_still_the_documented_unrestricted_case(held):
    """`Value::None` must stay 'no scope' — seeds/reflex_net.json relies on it."""
    _s, native, obs = held
    assert _decode(native, obs, scope={"type": "Lit", "value": None}) == \
        _decode(native, obs) == len(GOAL)


def test_a_non_string_scope_element_is_loud_not_silent(held):
    """A malformed element must name itself rather than silently unrestrict."""
    _s, native, obs = held
    with pytest.raises(BaseException) as ei:
        _decode(native, obs, scope={"type": "SetT",
                                    "items": [{"type": "Lit", "value": 7}]})
    assert "codebook_scope" in str(ei.value)
