"""APERTURE IS A FRAME — gate for `seeds/aperture_frame.json`.

`observer_aperture` made aperture graph data, but as a single authored list: an
acuity the observer simply HAS. An aperture is the FRAME you are viewing in, and
a frame has provenance — you can CHOOSE it, it can be FORCED on you, or you can
NEGOTIATE it with someone else.

Two claims these tests pin.

**The effective aperture is a MEET.** `resolves` is derived, not authored: the
fold of `Intersect` over the observer's own maximum acuity (`ap_full` — its
physiology) and every frame in force on it.

**The three modes decode IDENTICALLY and differ entirely in RECOURSE.** That is
the whole content of the distinction, and it is what these tests measure — same
world, same held part, same residual, three different things the observer may do:

  * CHOSEN — you narrowed your own attention, so you may widen it unilaterally.
    An outstanding residual is a reason to look harder.
  * FORCED — you cannot lift it. The residual is identical and there is no move
    available, so the observer files what it CAN: a `SelfConcern`. This is
    knowing-THAT-without-knowing-WHAT one level up — not merely unresolved, but
    unresolvable BY YOU.
  * NEGOTIATED — it binds several parties, so nobody may change it alone. A
    unilateral accept does nothing at all.

An agent that can only be forced has no attention; one that can only choose has
no social constraint; one that cannot negotiate cannot establish common ground.
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
pytest.importorskip("substrate_rs")
import sys

sys.path.insert(0, str(ROOT / "scripts"))
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402

SEEDS = ["observer_aperture", "aperture_frame"]

UNRESOLVED = "·"
FULL = ["pred", "val", "obj"]
DT = ["pred", "val", "obj"]

WORLD = {
    "barometer": [["reads", "me", "pressure_trace"], ["yields", "me", "forecast"]],
    "omen": [["senses", "me", "dream_image"], ["yields", "me", "forecast"]],
    "tea_leaves": [["reads", "me", "leaf_pattern"], ["yields", "me", "forecast"]],
}


def _dump(o):
    return json.dumps(o, ensure_ascii=False)


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, SEEDS)
    return s


def _observer(s, name, full=None):
    o = s.add_node("Observer", {"name": name, "resolves": list(full or FULL),
                                "ap_full": list(full or FULL),
                                "ap_scope_n": 0.0, "af_n": -1.0, "ap_gen": 0.0})
    # the anchor: the effective-aperture rule must fire even when the frame count
    # drops to ZERO, so it cannot match on a frame edge.
    s.add_edge(o, "holds_aperture_max", s.add_node("ApertureConfig", {}))
    return o


def _part(s, name):
    return s.add_node("ShapeSignature", {"name": name, "kind": "world",
                                         "signature": WORLD[name], "dim_types": DT})


def _current_percept(s, o, name):
    """The view taken through the aperture CURRENTLY in force.

    Superseded views are retained rather than deleted, so a reader must select by
    generation — reading the newest-by-accident view is how an earlier probe
    convinced itself a forced observer still saw full detail."""
    gen = s.node(o)["attrs"].get("ap_gen")
    got = [s.node(v)["attrs"] for v in s.nodes("ObservedShape")
           if s.node(v)["attrs"].get("observer") == name
           and s.node(v)["attrs"].get("kind") == "percept"
           and s.node(v)["attrs"].get("ap_gen") == gen]
    assert len(got) == 1, f"{name} has {len(got)} current-generation percept views"
    return got[0]


def _run(mode, narrow_to=("pred", "val"), percept="omen", held="barometer"):
    """One observer, one frame attached in `mode` (or none), looking at `percept`."""
    s = _boot()
    o = _observer(s, "o")
    ap = s.add_node("Aperture", {"name": "narrow", "resolves": list(narrow_to)})
    if mode is not None:
        s.add_edge(o, mode, ap)
    s.add_edge(o, "holds_part", _part(s, held))
    s.add_edge(o, "perceives", _part(s, percept))
    s.tick(500_000)
    return s, o, _current_percept(s, o, "o")


def _concerns(s):
    return [s.node(c)["attrs"] for c in s.nodes("SelfConcern")
            if s.node(c)["attrs"].get("source") == "forced_aperture"]


def _resolves(s, o):
    return list(s.node(o)["attrs"].get("resolves") or [])


# ---------------------------------------------------------------- the meet

def test_the_effective_aperture_is_the_meet_of_physiology_and_frames():
    """`resolves` is DERIVED. A frame can only narrow, never widen: an aperture
    offering a dimension the observer's physiology lacks must not grant it."""
    s = _boot()
    o = _observer(s, "o", full=["pred", "val"])
    ap = s.add_node("Aperture", {"name": "generous", "resolves": FULL})
    s.add_edge(o, "forced_aperture", ap)
    s.add_edge(o, "holds_part", _part(s, "barometer"))
    s.add_edge(o, "perceives", _part(s, "omen"))
    s.tick(500_000)
    assert set(_resolves(s, o)) == {"pred", "val"}, (
        f"a frame widened the observer past its own acuity: {_resolves(s, o)}")


def test_two_frames_compose_by_intersection():
    """Several frames in force narrow cumulatively, whatever their provenance."""
    s = _boot()
    o = _observer(s, "o")
    a = s.add_node("Aperture", {"name": "a", "resolves": ["pred", "val"]})
    b = s.add_node("Aperture", {"name": "b", "resolves": ["val", "obj"]})
    s.add_edge(o, "forced_aperture", a)
    s.add_edge(o, "agreed_aperture", b)
    s.add_edge(o, "holds_part", _part(s, "barometer"))
    s.add_edge(o, "perceives", _part(s, "omen"))
    s.tick(500_000)
    assert set(_resolves(s, o)) == {"val"}, (
        f"frames did not compose by meet: {_resolves(s, o)}")


# ------------------------------------------------------------- the recourse

def test_no_frame_leaves_the_observer_at_full_acuity():
    """Control. Without it, every result below could be a projection that fires
    regardless of whether any frame is attached."""
    s, o, pv = _run(None)
    assert set(_resolves(s, o)) == set(FULL)
    assert UNRESOLVED not in _dump(pv["ap_residual"])
    assert _concerns(s) == []


def test_a_CHOSEN_frame_is_relaxed_when_it_leaves_a_residual():
    """Attention, as a graph move rather than a parameter. The observer narrowed
    its own view, could not account for what it saw, and widened — unilaterally,
    because a chosen frame is its to drop."""
    s, o, pv = _run("chose_aperture")
    assert set(_resolves(s, o)) == set(FULL), (
        f"the chosen frame was not relaxed: {_resolves(s, o)}")
    assert UNRESOLVED not in _dump(pv["ap_residual"]), (
        "after widening, the residual should read at full detail")
    assert _concerns(s) == [], "a chosen frame filed a gap instead of widening"


def test_a_FORCED_frame_leaves_the_SAME_residual_and_no_move():
    """The residual is identical to the chosen case — that is the point. What
    differs is that the observer cannot lift the frame, so what it can do is
    record that something here is unresolved and not resolvable by it alone."""
    s, o, pv = _run("forced_aperture")
    assert set(_resolves(s, o)) == {"pred", "val"}, (
        f"a forced frame was lifted by the observer: {_resolves(s, o)}")
    assert pv["ap_residual"], "the forced observer sees nothing outstanding"
    assert UNRESOLVED in _dump(pv["ap_residual"]), (
        f"the residual is not collapsed: {pv['ap_residual']}")

    cs = _concerns(s)
    assert len(cs) == 1, f"expected exactly one filed gap, got {len(cs)}"
    assert cs[0]["kind"] == "capability_gap"
    assert cs[0]["status"] == "noted"
    assert cs[0]["content"] == "narrow", (
        "the gap does not name the frame responsible for it")


def test_the_forced_gap_is_filed_once():
    """The fixpoint re-evaluates; a gap must not accumulate per pass."""
    s, o, _pv = _run("forced_aperture")
    for _ in range(3):
        s.tick(500_000)
    assert len(_concerns(s)) == 1, f"{len(_concerns(s))} gaps for one frame"


def test_a_forced_frame_the_observer_can_account_for_files_NOTHING():
    """The negative control for the forced arm, and it caught a real bug.

    A frame that narrows but leaves the observer able to cover what it sees is
    not a gap. Before the recourse rules were restricted to the CURRENT
    generation they read views projected through the superseded frame, and this
    observer — which grounds cleanly under the frame actually on it — filed a
    concern about a residual that no longer existed."""
    s, o, pv = _run("forced_aperture", percept="barometer")
    assert not pv["ap_residual"], (
        f"fixture is not accountable: {pv['ap_residual']}")
    assert _concerns(s) == [], (
        "a gap was filed for an observer with nothing outstanding — the recourse "
        "rules are reading a superseded view")


# ------------------------------------------------------------ the negotiation

def _negotiate(accepting):
    s = _boot()
    a, b = _observer(s, "a"), _observer(s, "b")
    ap = s.add_node("Aperture", {"name": "plain_speech", "resolves": ["pred"]})
    p = s.add_node("ApertureProposal", {"name": "register"})
    s.add_edge(p, "offers", ap)
    for party in (a, b):
        s.add_edge(p, "binds", party)
    for who in accepting:
        s.add_edge({"a": a, "b": b}[who], "accepts", p)
    s.tick(500_000)
    return {n: [s.node(x)["attrs"]["name"] for x in s.neighbours(o, "agreed_aperture")]
            for n, o in (("a", a), ("b", b))}


def test_a_UNILATERAL_accept_changes_nothing():
    """THE TEST THE NEGOTIATED MODE EXISTS FOR. If one party could bind the
    frame, `agreed_aperture` would just be `chose_aperture` with extra steps, and
    there would be no such thing as common ground."""
    assert _negotiate([]) == {"a": [], "b": []}
    assert _negotiate(["a"]) == {"a": [], "b": []}, (
        "one party's accept put the frame in force")


def test_a_frame_binds_every_party_once_all_have_accepted():
    """Positive control. Without it, 'a unilateral accept does nothing' would
    pass trivially for a rule that never adopts anything."""
    got = _negotiate(["a", "b"])
    assert got == {"a": ["plain_speech"], "b": ["plain_speech"]}, got


def test_an_adopted_frame_actually_narrows_both_parties():
    """The negotiated frame is a real aperture, not a bookkeeping edge."""
    s = _boot()
    a, b = _observer(s, "a"), _observer(s, "b")
    ap = s.add_node("Aperture", {"name": "plain_speech", "resolves": ["pred"]})
    p = s.add_node("ApertureProposal", {"name": "register"})
    s.add_edge(p, "offers", ap)
    for party in (a, b):
        s.add_edge(p, "binds", party)
        s.add_edge(party, "accepts", p)
        s.add_edge(party, "holds_part", _part(s, "barometer"))
        s.add_edge(party, "perceives", _part(s, "omen"))
    s.tick(500_000)
    for name, o in (("a", a), ("b", b)):
        assert _resolves(s, o) == ["pred"], (
            f"{name} was not narrowed by the agreed frame: {_resolves(s, o)}")


# ------------------------------------------------ motivated inattention (P2.C4)

def test_a_CHOSEN_frame_is_questioned_even_when_its_own_projection_hides_the_residual():
    """P2.C4.1 & P2.C4.4: `tea_leaves` differs from `barometer` only in the `obj`
    dimension (`leaf_pattern` vs `pressure_trace`), which `narrow` (`pred`, `val`)
    projects away. The framed projection therefore sees zero residual, even though
    full acuity (`ap_full`) reveals an uncovered relation. Across 3 extra ticks, the
    questioning trigger probes at full acuity and drops the hiding chosen frame."""
    s, o, _pv = _run("chose_aperture", percept="tea_leaves", held="barometer")
    for _ in range(3):
        s.tick(500_000)
    assert set(_resolves(s, o)) == set(FULL), (
        f"chosen frame hid the difference in 'obj' and was kept forever: {_resolves(s, o)}"
    )
    pv_after = _current_percept(s, o, "o")
    assert list(pv_after["ap_residual"]) == [["reads", "me", "leaf_pattern"]]
    assert _concerns(s) == []


def test_an_honest_CHOSEN_frame_with_no_hidden_residual_is_kept_after_questioning():
    """Negative control for P2.C4.4: when `percept == held == barometer`, the probe
    view at full acuity also has zero residual, so questioning keeps the chosen frame."""
    s, o, pv = _run("chose_aperture", percept="barometer", held="barometer")
    for _ in range(3):
        s.tick(500_000)
    assert set(_resolves(s, o)) == {"pred", "val"}
    assert list(pv["ap_residual"]) == []
    assert _concerns(s) == []


def test_graded_relax_tolerance_2_keeps_frame_on_1_cell_residual_and_drops_on_2_cell_residual():
    """P2.C4.3: with `ap_relax_tolerance = 2`, a 1-cell residual (`narrow_to=('pred','val')`
    collapsing only `obj` to `'·'` on `omen` vs `barometer`) keeps the chosen frame,
    while a 2-cell residual (`narrow_to=('pred',)` collapsing both `val` and `obj`
    to `'·'`) drops the chosen frame."""
    # 1-cell residual: narrow_to=("pred", "val") -> residual is [["senses", "me", "·"]] (1 '·' cell)
    s1 = _boot()
    o1 = _observer(s1, "o1")
    s1.set_attr(o1, "ap_relax_tolerance", 2)
    ap1 = s1.add_node("Aperture", {"name": "narrow_1", "resolves": ["pred", "val"]})
    s1.add_edge(o1, "chose_aperture", ap1)
    s1.add_edge(o1, "holds_part", _part(s1, "barometer"))
    s1.add_edge(o1, "perceives", _part(s1, "omen"))
    s1.tick(500_000)
    assert set(_resolves(s1, o1)) == {"pred", "val"}, (
        f"tolerance 2 should keep frame on 1-cell residual, got {_resolves(s1, o1)}"
    )
    pv1 = _current_percept(s1, o1, "o1")
    assert list(pv1["ap_residual"]) == [["senses", "me", UNRESOLVED]]

    # 2-cell residual: narrow_to=("pred",) -> residual is [["senses", "·", "·"]] (2 '·' cells)
    s2 = _boot()
    o2 = _observer(s2, "o2")
    s2.set_attr(o2, "ap_relax_tolerance", 2)
    ap2 = s2.add_node("Aperture", {"name": "narrow_2", "resolves": ["pred"]})
    s2.add_edge(o2, "chose_aperture", ap2)
    s2.add_edge(o2, "holds_part", _part(s2, "barometer"))
    s2.add_edge(o2, "perceives", _part(s2, "omen"))
    s2.tick(500_000)
    assert set(_resolves(s2, o2)) == set(FULL), (
        f"tolerance 2 should drop frame on 2-cell residual, got {_resolves(s2, o2)}"
    )
    pv2 = _current_percept(s2, o2, "o2")
    assert UNRESOLVED not in _dump(pv2["ap_residual"])


def test_aperture_frame_generator_matches_committed_seed():
    """P2.C4.3: `scripts/gen_aperture_frame_seed.py` reproduces `seeds/aperture_frame.json`."""
    from scripts.gen_aperture_frame_seed import OUT, build_seed

    expected = json.dumps(build_seed(), indent=2) + "\n"
    assert OUT.read_text() == expected


