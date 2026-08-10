"""`ArgminUnique` — the gate.

`VISION_REFUSAL_CAPACITY_RESULTS.md` §7: **`Argmin` returned a winner from five
IDENTICAL candidates**, and §10: *a comparison can be false, a selection
cannot.* This pins the sibling that CAN refuse, and — just as importantly — it
pins the two facts the measurement found that were NOT predicted:

  * the refusal is INDISTINGUISHABLE from an empty-source null at the caller,
    and from `False` under `Eq` (`VISION_ARGMIN_UNIQUE_RESULTS.md` arm C);
  * the instrument's `count` mode does not change behaviour (§9).

Every assertion here has BOTH directions. A mechanism that refuses everything,
and a reader that returns `None` for everything, both FAIL this file — which is
the whole lesson of the rung that measured refusal with a dead reader.
"""
from __future__ import annotations

import pytest

srs = pytest.importorskip("substrate_rs")
native = srs._native


def _sub(values):
    s = srs.Substrate()
    for i, v in enumerate(values):
        s.add_node("Cand", {"score": float(v), "idx": i})
    return s


def _sel(kind):
    return srs.Term(kind,
                    source=srs.Term("NodesOfType", node_type="Cand"),
                    var_name="c",
                    value=srs.Attr(srs.Var("c"), "score"),
                    default=None)


def _eval(values, kind, mode="off", wrap=None):
    native.argmin_tie_reset()
    native.argmin_tie_enable(mode)
    try:
        t = _sel(kind)
        if wrap is not None:
            t = wrap(t)
        return _sub(values).evaluate(t), native.argmin_tie_stats()
    finally:
        native.argmin_tie_enable("off")


TIE = [7.0] * 5
UNIQUE = [7.0, 7.0, 3.0, 7.0, 7.0]


def test_argmin_still_returns_a_winner_from_five_identical_candidates():
    """The fact the rung exists for. If this ever changes, `Argmin`'s default
    behaviour has moved and §9 is broken."""
    out, _ = _eval(TIE, "Argmin")
    assert out is not None


def test_argmin_unique_refuses_a_non_unique_extremum():
    out, st = _eval(TIE, "ArgminUnique", "count")
    assert out is None
    assert st["ties"] == 1 and st["refusals"] == 1


def test_argmin_unique_returns_THE_SAME_WINNER_when_the_extremum_is_unique():
    """A mechanism that refuses everything is not a refuser. This is the
    direction that a dead reader cannot fake."""
    ref, _ = _eval(UNIQUE, "Argmin")
    out, st = _eval(UNIQUE, "ArgminUnique", "count")
    assert out is not None
    assert str(out) == str(ref)
    assert st["ties"] == 0 and st["refusals"] == 0


def test_an_empty_source_is_counted_as_EMPTY_and_never_as_a_tie():
    """`Argmin` could ALREADY return `None` on an empty source. The refusal and
    the empty null are the same bytes downstream, so the instrument must
    separate them — otherwise a broken reader and a perfect refuser are the same
    measurement."""
    out, st = _eval([], "ArgminUnique", "count")
    assert out is None
    assert st["empties"] == 1 and st["ties"] == 0 and st["refusals"] == 0


def test_the_refusal_is_INDISTINGUISHABLE_from_the_empty_null_at_the_caller():
    """MEASURED, not argued (arm C). Refusal capacity at the Term boundary is
    NOT refusal capacity available to the graph — C1, one level down."""
    tie, _ = _eval(TIE, "ArgminUnique", "count")
    empty, _ = _eval([], "ArgminUnique", "count")
    assert repr(tie) == repr(empty) == "None"


def test_under_Eq_the_refusal_collapses_to_False_exactly_like_LOSING():
    """The WTA idiom (`Eq(node, Argmin{...})`) — 16 of the 117 seed sites, and
    the ONLY shape that ties on the vision bench. A refusal is `False`, which is
    what "you are not the winner" and "there was nothing to choose" both give.
    """
    wrap = lambda t: srs.Term("Eq", a=srs.Attr(t, "score"), b=srs.Lit(7.0))
    tie, _ = _eval(TIE, "ArgminUnique", "count", wrap)
    lose, _ = _eval(UNIQUE, "ArgminUnique", "count", wrap)
    empty, _ = _eval([], "ArgminUnique", "count", wrap)
    assert tie is False and lose is False and empty is False
    # and the un-refusing selector DOES separate them -- so this is a property
    # of the refusal's representation, not of the probe.
    tie_a, _ = _eval(TIE, "Argmin", "count", wrap)
    assert tie_a is True


def test_count_mode_does_not_change_behaviour():
    """§9: the census must reproduce every committed result byte-identically."""
    off, _ = _eval(TIE, "Argmin", "off")
    cnt, st = _eval(TIE, "Argmin", "count")
    assert str(off) == str(cnt) and off is not None
    assert st["ties"] == 1 and st["refusals"] == 0


def test_refuse_min_does_not_touch_Argmax_and_refuse_all_does():
    """The two coercion modes are reported separately and must never be
    conflated: on the vision bench ALL 201 ties were `Argmax`, so this
    distinction is the rung's main structural finding."""
    out_min, st_min = _eval(TIE, "Argmax", "refuse_min")
    assert out_min is not None and st_min["refusals"] == 0 and st_min["ties"] == 1
    out_all, st_all = _eval(TIE, "Argmax", "refuse_all")
    assert out_all is None and st_all["refusals"] == 1


def test_the_new_variant_is_APPENDED_and_moves_no_existing_index():
    """`GapAbduce` 175 / `GapVerify` 176 must not move —
    `variant_table_covers_the_enum` asserts the table's arity, and every
    committed per-variant counter row is indexed by these numbers."""
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / \
        "runners/dsl/src/term_variants.rs"
    text = src.read_text()
    assert "TermNode::GapAbduce { .. } => 175," in text
    assert "TermNode::GapVerify { .. } => 176," in text
    assert "TermNode::ArgminUnique { .. } => 177," in text

    # 2026-07-21 — this assertion USED to read
    #     assert "pub const NUM_TERM_VARIANTS: usize = 178;" in text
    # and it went red the moment a CONCURRENT rung appended `SupportInfer`.
    #
    # THAT WAS A FALSE ACCUSATION OF THIS RUNG, and of exactly the class the
    # baselines rung fixed for two other gates in the same wave: **a claim about
    # what THIS rung did was pinned to a quantity ANY LATER rung moves.**
    # `NUM_TERM_VARIANTS` is a TOTAL — a COUNT — and this test's own name claims
    # something about INDICES. A count can be held; a list has to be read.
    #
    # The replacement is STRICTER, not quieter: the three assertions above pin
    # the individual indices (which is the actual claim), and the invariant
    # below is checked STRUCTURALLY — the table's arity must equal the highest
    # index + 1, whatever that highest index happens to be. An appended variant
    # passes; a MOVED or DUPLICATED index fails, which is what the docstring
    # promises. `variant_table_covers_the_enum` gates the Rust side of the same
    # fact at compile time.
    import re as _re
    decl = int(_re.search(r"NUM_TERM_VARIANTS: usize = (\d+);", text).group(1))
    idxs = [int(m) for m in _re.findall(r"\} => (\d+),", text)]
    assert len(idxs) == len(set(idxs)), (
        f"duplicate Term enum index — two rungs appended at the same number: "
        f"{sorted(i for i in idxs if idxs.count(i) > 1)}")
    assert decl == max(idxs) + 1, (
        f"NUM_TERM_VARIANTS ({decl}) != max index + 1 ({max(idxs) + 1}); the "
        "names table and the index arm have diverged")


def test_no_seed_binds_ArgminUnique_yet():
    """§9 by non-existence: the Term ships unused, so every committed result
    reproduces byte-identically. When a site is finally armed, this gate is the
    one that must be consciously changed."""
    import pathlib
    seeds = pathlib.Path(__file__).resolve().parents[1] / "seeds"
    hits = [p.name for p in seeds.glob("*.json")
            if "ArgminUnique" in p.read_text()]
    assert hits == [], f"a seed now binds ArgminUnique: {hits}"
