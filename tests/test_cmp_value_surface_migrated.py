"""test_cmp_value_surface_migrated — the engine's `(Surface, Surface)` order.

`CMP_VALUE_SURFACE_FIX_RESULTS.md`. `cmp_value` had no `(Surface, Surface)`
arm, so two RUNTIME-BUILT strings fell through to the type-tag compare (10 vs
10) and read `Equal`. `PartialEq` and `Hash` both got it right, so this was an
Ord/Eq INCONSISTENCY, and every container that canonicalises through
`cmp_value` lost data silently:

    {"a" + str(i) for i in range(3)}   ->  {'a0'}       # MEASURED, before
    d["a" + str(i)] = i, i in 0..3     ->  {'a0': 2}    # MEASURED, before
    d.get("a1", -1) on that dict       ->  -1           # MEASURED, before

The Rust-side contract (Ord/Eq agreement, antisymmetry, transitivity, kind in
the order) is gated in `runners/dsl/src/value.rs`'s own unit tests. THIS file
gates the END-TO-END behaviour at the Python/engine boundary — the shape a
consumer actually sees — because that is the layer the defect was found from
and the layer a future engine change would break silently.

Every assertion here is RED on the pre-fix engine (sha256 8963fb4dcc...) and
GREEN on the post-fix one (632b455f44...).
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402


# --- Term-JSON builders (mechanical) ---------------------------------------
def L(v):
    return {"type": "Lit", "value": v}


def CAT(*items):
    return {"type": "Cat", "items": list(items)}


def SETT(*items):
    return {"type": "SetT", "items": list(items)}


def VEC(*items):
    return {"type": "Vec", "items": list(items)}


def MKDICT(kv):
    items = []
    for k, v in kv.items():
        items.append(L(k))
        items.append(L(v))
    return {"type": "MkDict", "items": items}


def PROGEVAL(prog, oracles=None):
    return {"type": "ProgEval", "prog": prog, "env": None, "oracles": oracles,
            "fuel": 4000, "field": ""}


@pytest.fixture()
def ev():
    s = srs.Substrate()
    return s._inner.evaluate


def run_src(ev, src):
    """Emit a Python source fn as hub Program IR and run it under ProgEval.
    Mechanical: emitter + interpreter, no decisions here."""
    from domains.prog_ir_emit import emit_prog_ir
    out = emit_prog_ir(src)
    assert out.get("ok"), "emit blocked: %s" % (out.get("blockers"),)
    orc = out.get("native_oracles") or []
    res = ev(PROGEVAL(out["ir"],
                      MKDICT({n: "builtin" for n in orc}) if orc else None), {})
    assert res.get("trap") is None, "unexpected trap %r" % (res.get("trap"),)
    return res.get("result")


# ---------------------------------------------------------------------------
# 1. THE HEADLINE — a Set of computed strings keeps every member.
# ---------------------------------------------------------------------------
def test_a_set_of_computed_strings_does_not_collapse(ev):
    computed = ev(SETT(*[CAT(L("a"), L(str(i))) for i in range(3)]), {})
    assert len(computed) == 3, (
        "runtime-built strings collapsed in a Set — cmp_value's "
        "(Surface, Surface) arm is missing or wrong; got %r" % (computed,))
    assert set(computed) == {"a0", "a1", "a2"}


def test_the_literal_control_was_and_stays_correct(ev):
    """The control that makes the diagnosis specific: Str literals were never
    affected, so a fix that 'repaired' this case would be fixing the wrong
    thing."""
    literal = ev(SETT(*[L("a%d" % i) for i in range(3)]), {})
    assert set(literal) == {"a0", "a1", "a2"}


def test_nesting_does_not_hide_the_computed_member(ev):
    """The Tuple arm recurses straight back into the Surface comparison, so a
    computed string wrapped in a tuple collapsed too."""
    nested = ev(SETT(*[VEC(L("rt"), CAT(L("a"), L(str(i)))) for i in range(3)]), {})
    assert len(nested) == 3, "set of (literal, computed) tuples collapsed: %r" % (nested,)


def test_a_genuine_duplicate_still_dedups(ev):
    """The fix must not turn the Set into a bag: equal computed strings are
    still one member."""
    dup = ev(SETT(CAT(L("a"), L("0")), CAT(L("a"), L("0")), CAT(L("a"), L("1"))), {})
    assert len(dup) == 2, "dedup broke: %r" % (dup,)


# ---------------------------------------------------------------------------
# 2. THE DICT SIDE — item-assign hit the first Surface-keyed slot.
# ---------------------------------------------------------------------------
def test_dict_item_assign_with_computed_keys_keeps_every_key(ev):
    got = run_src(ev, '''
def f():
    d = {}
    for i in range(3):
        d["".join(["a", str(i)])] = i
    return d
''')
    assert got == {"a0": 0, "a1": 1, "a2": 2}, (
        "computed keys overwrote each other (before the fix: {'a0': 2}); got %r" % (got,))


def test_a_computed_key_can_be_read_back_by_a_literal(ev):
    """Before the fix this TRAPPED `key:a1` — the key was gone."""
    assert run_src(ev, '''
def f():
    d = {}
    d["".join(["a", "0"])] = 7
    d["".join(["a", "1"])] = 8
    return d["a1"]
''') == 8


def test_dict_get_does_not_silently_return_the_default(ev):
    """The nastiest shape of this defect: `.get` returned the DEFAULT for a
    key that had been written, with no trap and no error. Measured -1 before
    the fix."""
    assert run_src(ev, '''
def f():
    d = {}
    d["".join(["a", "0"])] = 7
    d["".join(["a", "1"])] = 8
    return d.get("a1", -1)
''') == 8


def test_the_cross_type_string_fallback_still_works(ev):
    """`prog_eval`'s dict lookups match on `cmp_value == Equal` OR on rendered
    string equality. The second half is what makes a `Str` key findable by a
    `Surface` probe (their type tags differ, so `cmp_value` is correctly NOT
    Equal). The fix must not have made that fallback dead."""
    assert run_src(ev, '''
def f():
    d = {"a0": 7, "a1": 8}
    return d["".join(["a", "1"])]
''') == 8


# ---------------------------------------------------------------------------
# 3. ORDER — Surface(Text) is byte-lexicographic, so `sorted` actually sorts.
# ---------------------------------------------------------------------------
def test_sorted_over_computed_strings_is_lexicographic(ev):
    """Before the fix `sorted` over computed strings was an INERT no-op (every
    pair compared Equal) and returned input order."""
    got = run_src(ev, '''
def f():
    return sorted(["".join([x]) for x in ["where", "source", "var_name", "a_zzz", "b"]])
''')
    assert list(got) == ["a_zzz", "b", "source", "var_name", "where"]


def test_str_literals_are_now_lexicographic_too(ev):
    """UPDATED by CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md, exactly as this
    test's own prior docstring said it should be: this rung named `sorted()`
    (`prog_eval.rs`'s "sorted" extern) as a REPORTED-ORDER site and switched
    it to the interner-aware `cmp_value_lex` comparator — `cmp_value`'s own
    `(Str, Str)` arm is UNCHANGED (still boot-history Sym-id order; that is
    what canonicalisation call sites keep using). `sorted()` over string
    LITERALS is therefore now real byte-lexicographic order, matching the
    `sorted()`-over-COMPUTED-strings behaviour the surface-fix rung already
    established two tests above (`test_sorted_over_computed_strings_is_lexicographic`)."""
    got = list(run_src(ev, '''
def f():
    return sorted(["where", "source", "var_name", "a_zzz", "b"])
'''))
    assert got == ["a_zzz", "b", "source", "var_name", "where"]


def test_a_literal_and_an_identical_computed_string_stay_distinct(ev):
    """Also unchanged, also named rather than assumed: `Str("a0")` and
    `Surface(Text, b"a0")` are `!=` under `PartialEq` and ordered by type tag,
    so a set holding both has TWO members. Self-consistent, and out of this
    rung's registered scope — pinned so a future change to it is deliberate."""
    assert run_src(ev, '''
def f():
    return len(set(["a0", "".join(["a", "0"])]))
''') == 2
