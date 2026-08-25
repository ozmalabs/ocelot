"""GRADED PER-OBSERVER APERTURE — gate for `seeds/observer_aperture.json`.

Limiting what each agent can resolve is the precondition for any social dynamic:
without partial views there is no belief divergence, no theory of mind, no
privacy and no deception, because every agent seeing all structure makes every
agent the same agent.

`PER_OBSERVER_APERTURE.md` established that RANGE (`codebook_scope`) was already
graph-native and per-call, and that APERTURE was all-or-nothing (`wild_objects`).
This seed grades it — and NOT as a wildcard. `CLAUDE.md` records the
codebook-side wildcard as retired for conflating consistent substitution with
incoherent novelty, and that retirement points at the right operation: WILD means
*"anything matched"*, which discards WHICH substitution occurred. Limited
perception is not that. It is *"these are the same thing to me"* — a QUOTIENT. So
a signature is projected onto the `dim_types` the observer resolves, unresolved
slots collapsing to one CONSTANT, and matched literally.

Two results these tests pin, beyond the mechanics:

  * a COARSE observer grounds what a fine one refuses. Not by lying and not by
    wishing — at that aperture the two things are genuinely indistinguishable, so
    the grounding is valid AT THAT RESOLUTION;
  * an observer can read a NON-EMPTY residual whose content is collapsed —
    knowing THAT something is unaccounted for without being able to resolve WHAT.
    That distinction is the correction recorded in `ONE_LOOP_MANY_GRAINS.md`, and
    it is what makes honest ignorance mechanical rather than a virtue.
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

SEEDS = ["observer_aperture"]

UNRESOLVED = "·"


def _dump(o):
    """`json.dumps` escapes the marker to `\\u00b7` by default, which made two of
    these assertions fail against a projection that was in fact correct."""
    return json.dumps(o, ensure_ascii=False)

# dim_types: slot 0 is the predicate, slot 1 the subject, slot 2 the object.
DT = ["pred", "val", "obj"]

CONTROLS = {
    "aileron": [["controls", "stick", "aileron"]],
    "throttle": [["controls", "lever", "throttle"]],
    "tiller": [["controls", "stick", "tiller"]],
    "colour": [["paints", "brush", "red"]],
}

FORECAST = {
    "barometer": [["reads", "me", "pressure_trace"], ["yields", "me", "forecast"]],
    "tea_leaves": [["reads", "me", "leaf_pattern"], ["yields", "me", "forecast"]],
    "omen": [["senses", "me", "dream_image"], ["yields", "me", "forecast"]],
}


def _observer(s, name, resolves):
    return s.add_node("Observer", {"name": name, "resolves": resolves,
                                   "ap_scope_n": 0.0, "ap_gen": 0.0})


def _part(s, world, name):
    return s.add_node("ShapeSignature", {"name": name, "kind": "world",
                                         "signature": world[name], "dim_types": DT})


def _views(s, kind, observer=None):
    out = []
    for p in s.nodes("ObservedShape"):
        a = s.node(p)["attrs"]
        if a.get("kind") != kind:
            continue
        if observer is not None and a.get("observer") != observer:
            continue
        out.append(a)
    return out


def _decode(name, resolves, held, percept):
    """One observer holding `held`, looking at `percept`, in the shared store."""
    s, ag = boot_core()
    load_seeds_into(s, ag, SEEDS)
    o = _observer(s, name, resolves)
    for h in held:
        s.add_edge(o, "holds_part", _part(s, FORECAST, h))
    s.add_edge(o, "perceives", _part(s, FORECAST, percept))
    s.tick(500_000)
    pv = _views(s, "percept", name)
    assert len(pv) == 1, f"expected one percept view, got {len(pv)}"
    return s, pv[0]


def _control_world():
    """Three observers of DIFFERENT acuity over ONE shared set of world shapes."""
    s, ag = boot_core()
    load_seeds_into(s, ag, SEEDS)
    shapes = {n: _part(s, CONTROLS, n) for n in CONTROLS}
    apertures = {"expert": ["pred", "val", "obj"], "glancer": ["pred"], "blind": []}
    for name, res in apertures.items():
        o = _observer(s, name, res)
        for sh in shapes.values():
            s.add_edge(o, "perceives", sh)
    s.tick(500_000)
    return s, apertures


def test_an_observer_sees_only_its_own_quotient_of_a_shared_world():
    """THE HEADLINE. One store, one set of world shapes, three acuities — and
    what each observer can TELL APART differs, because slots it cannot resolve
    collapse to one constant and the shapes become literally equal for it.

    This is also the gate against the rule ignoring `resolves` entirely: if it
    did, all three counts would be 4."""
    s, apertures = _control_world()
    seen = {}
    for name in apertures:
        views = _views(s, "percept", name)
        assert len(views) == len(CONTROLS), (
            f"{name} projected {len(views)} of {len(CONTROLS)} shapes")
        seen[name] = len({_dump(v["signature"]) for v in views})

    assert seen["expert"] == 4, seen
    assert seen["glancer"] == 2, (
        f"glancer resolves only the predicate, so the three `controls` shapes must "
        f"collapse into one class distinct from `paints` — got {seen}")
    assert seen["blind"] == 1, (
        f"an observer resolving NOTHING has one equivalence class — got {seen}")

    assert seen["expert"] > seen["glancer"] > seen["blind"], seen


def test_the_blind_observer_still_counts_four_things():
    """Collapsing is not deleting. The quotient says *these are the same thing to
    me*, which is a claim about DISCRIMINATION, not about existence — so the
    observer that can tell nothing apart still has four percepts."""
    s, _ = _control_world()
    views = _views(s, "percept", "blind")
    assert len(views) == 4
    assert len({_dump(v["signature"]) for v in views}) == 1


def test_an_observer_resolving_everything_loses_nothing():
    """Negative control. Without this, a projection that silently blurred
    EVERYONE would still pass the ordering test above."""
    s, _ = _control_world()
    for v in _views(s, "percept", "expert"):
        got = json.loads(_dump(v["signature"]))
        assert got == CONTROLS[v["of_name"]], (
            f"the full-aperture projection altered {v['of_name']}: "
            f"{got} != {CONTROLS[v['of_name']]}")
        assert UNRESOLVED not in _dump(got)


def test_the_held_codebook_is_projected_too_not_only_the_goal():
    """Projecting only the percept would decode a blurred observation against
    full-detail held parts, which is nobody's situation: what an observer holds
    was itself acquired through its aperture."""
    s, _pv = _decode("mystic", ["pred", "val"], ["barometer"], "tea_leaves")
    held = _views(s, "held", "mystic")
    assert len(held) == 1, f"the held part was not projected: {held}"
    assert UNRESOLVED in _dump(held[0]["signature"]), (
        "the held part came through at full detail — only the goal was projected")
    assert held[0]["name"] == "mystic/0.0/barometer", (
        "a projected part must be named per-observer AND per aperture generation. "
        "Per-observer, or two agents' quotients of the same world part collide in "
        "the shared store; per-generation, because a view taken through a "
        "superseded frame keeps the same `of_name` and `load_parts` dedups by "
        "name, so which quotient survives would depend on node iteration order")


def test_the_projection_reaches_a_fixpoint():
    """The dedup guard has to hold or `run_rules` never terminates."""
    s, _ = _control_world()
    before = len(s.nodes("ObservedShape"))
    s.tick(500_000)
    s.tick(500_000)
    assert len(s.nodes("ObservedShape")) == before, (
        f"{len(s.nodes('ObservedShape'))} views after re-running, was {before}")


def test_a_coarse_observer_GROUNDS_what_a_fine_one_refuses():
    """Spurious grounding, mechanically, with nothing in Python deciding it.

    Both observers hold a barometer and are shown tea leaves. The one that
    resolves WHAT is read sees an outstanding residual. The one that does not
    sees a barometer — and it is neither lying nor wishing: at that aperture the
    two are genuinely indistinguishable, so the grounding is VALID AT THAT
    RESOLUTION. Telling it to check harder is incoherent."""
    _s, fine = _decode("meteorologist", ["pred", "val", "obj"], ["barometer"], "tea_leaves")
    _s, coarse = _decode("mystic", ["pred", "val"], ["barometer"], "tea_leaves")

    assert fine["ap_covered"] == 1, fine
    assert fine["ap_residual"], (
        "the fine observer grounded tea leaves on a barometer — the aperture is "
        "not being applied, or the object slot is not being resolved")

    assert coarse["ap_covered"] == 2, coarse
    assert not coarse["ap_residual"], (
        f"the coarse observer did NOT ground; residual {coarse['ap_residual']}")


def test_a_residual_can_be_DETECTED_without_being_RESOLVED():
    """THE TEST THIS SEED EXISTS FOR, and the correction in
    `ONE_LOOP_MANY_GRAINS.md`.

    An earlier probe concluded every aperture looks complete from inside. It was
    rigged — it modelled self-perception as an aperture intersected with itself.
    The true statement: you can understand that there are things you do not
    understand, without being able to resolve them, because

      * resolving WHAT is missing needs the distinction you lack;
      * detecting THAT something is missing needs only that your decode failed to
        cover, and coverage is a property of the decode.

    Shown an `omen` while holding only a barometer, the coarse observer gets a
    NON-EMPTY residual — it knows something here is unaccounted for — whose
    content carries the unresolved marker, so it cannot say what."""
    _s, fine = _decode("meteorologist", ["pred", "val", "obj"], ["barometer"], "omen")
    _s, coarse = _decode("mystic", ["pred", "val"], ["barometer"], "omen")

    assert fine["ap_residual"], "fixture is not outstanding for the fine observer"
    assert UNRESOLVED not in _dump(fine["ap_residual"]), (
        "the fine observer's residual is itself blurred — it should read cleanly")

    assert coarse["ap_residual"], (
        "the coarse observer's residual is EMPTY — it cannot tell it is missing "
        "anything, which is the zealot case, not the honest-ignorance case")
    assert UNRESOLVED in _dump(coarse["ap_residual"]), (
        f"the coarse observer resolved the residual's content: "
        f"{coarse['ap_residual']} — the fixture no longer distinguishes knowing "
        f"THAT from knowing WHAT")


def test_the_unfalsifiable_observer_sees_no_residual_at_all():
    """The third level, and the dangerous one. An observer whose aperture
    collapses the very predicate that would disagree has NO residual — its
    account is unfalsifiable not because it is defended but because the
    disconfirming signal is below its aperture. Distinct from the case above:
    there, something outstanding is detected but not resolved; here there is
    nothing to detect."""
    _s, zealot = _decode("zealot", ["val"], ["barometer"], "omen")
    assert not zealot["ap_residual"], (
        f"expected nothing outstanding for an observer that cannot resolve the "
        f"predicate, got {zealot['ap_residual']}")
    assert zealot["ap_covered"] == 2, zealot


def test_two_observers_over_one_store_do_not_read_each_others_parts():
    """THE GATE THAT WAS MISSING, and it was missing in the way that matters.

    Every test above uses ONE observer — and with one observer an unrestricted
    codebook is indistinguishable from a correctly scoped one, because the only
    parts in the store are that observer's own. So the range half of this seed
    could be, and for a while was, completely inert without a single test
    failing. It took a second observer to make the difference observable.

    Two observers, one shared store, the SAME world parts, different acuity: each
    must decode against its own quotient and reach its own verdict."""
    s, ag = boot_core()
    load_seeds_into(s, ag, SEEDS)
    fine = _observer(s, "fine", ["pred", "val", "obj"])
    coarse = _observer(s, "coarse", ["pred", "val"])
    bar = _part(s, FORECAST, "barometer")
    tea = _part(s, FORECAST, "tea_leaves")
    for o in (fine, coarse):
        s.add_edge(o, "holds_part", bar)
        s.add_edge(o, "perceives", tea)
    s.tick(500_000)

    verdicts = {}
    for name in ("fine", "coarse"):
        pv = _views(s, "percept", name)
        assert len(pv) == 1, f"{name} has {len(pv)} percept views"
        verdicts[name] = pv[0]

    assert verdicts["fine"]["ap_residual"], (
        "the fine observer grounded tea leaves on a barometer")
    assert not verdicts["coarse"]["ap_residual"], (
        f"the coarse observer did not ground: {verdicts['coarse']['ap_residual']}")

    # and each one's scope names only its OWN projected parts
    for name, o in (("fine", fine), ("coarse", coarse)):
        scope = list(s.node(o)["attrs"].get("ap_scope") or [])
        assert scope, f"{name} has an EMPTY scope — the range half is inert"
        assert all(p.startswith(f"{name}/") for p in scope), (
            f"{name}'s scope reaches another observer's parts: {scope}")


def test_an_observer_THAT_HOLDS_NOTHING_cannot_ground_on_another_agents_parts():
    """THE SHARP ISOLATION TEST, and the one that found a real hole.

    The test above asserts each observer's scope names only its own parts, but it
    does not show the scope MATTERS: with both observers holding the same part an
    unrestricted decode reaches the right verdict anyway, so dropping the scope
    rule broke only the assertion about the scope itself.

    This fixture makes leakage change the answer. `haver` holds a barometer;
    `pauper` holds NOTHING and sees the same thing at the same acuity. If the
    pauper reaches the haver's parts it grounds on borrowed structure — and it
    did, because `ap_refresh_scope` is anchored on a `projected_part` edge, so an
    observer with no parts never fires it and `ap_scope` stays ABSENT. Absent
    reads as unrestricted. That is the empty-scope inversion one level up from the
    engine fix that closed it: the agent who knows nothing sees everything. Fixed
    by reading the scope INLINE at decode time, where no parts yields the empty
    list rather than nothing at all."""
    s, ag = boot_core()
    load_seeds_into(s, ag, SEEDS)
    haver = _observer(s, "haver", ["pred", "val"])
    pauper = _observer(s, "pauper", ["pred", "val"])
    s.add_edge(haver, "holds_part", _part(s, FORECAST, "barometer"))
    tea = _part(s, FORECAST, "tea_leaves")
    for o in (haver, pauper):
        s.add_edge(o, "perceives", tea)
    s.tick(500_000)

    hv = _views(s, "percept", "haver")[0]
    pv = _views(s, "percept", "pauper")[0]

    assert hv["ap_covered"] == 2 and not hv["ap_residual"], (
        f"the haver should ground at this acuity: {hv}")

    # the rule RAN for the pauper -- without this the test passes for a decode
    # that never happened, which is the same null verdict.
    assert pv["ap_seen"] == 0.0, (
        f"the pauper never decoded at all (ap_seen={pv.get('ap_seen')!r}), so a "
        f"null verdict below would prove nothing")
    assert pv["ap_covered"] != 2, (
        f"the pauper covered {pv['ap_covered']} holding NOTHING — it is decoding "
        f"against another agent's parts")
    assert pv["ap_covered"] is None, (
        f"expected the documented 'nothing in scope' verdict, got "
        f"{pv['ap_covered']!r} — `None` means nothing is in your scope at all, "
        f"which is exactly the pauper's situation, while `0` would mean something "
        f"is in scope and does not cover this")


def test_acquiring_a_part_RE_ARMS_the_decode():
    """`ap_refresh_scope`'s real job, and until this test nothing exercised it.

    Once the decode read its scope inline, the refresh rule's only remaining
    purpose was the re-arm counter — so dropping it broke exactly one assertion
    about the published `ap_scope` attribute and nothing about behaviour. That is
    a rule held in place by bookkeeping rather than by consequence.

    The consequence is this: an observer that could not account for what it saw,
    and then ACQUIRES the missing part, must decode again and ground. It is the
    same codebook-grows-re-arm idiom the sd loop runs on."""
    s, ag = boot_core()
    load_seeds_into(s, ag, SEEDS)
    o = _observer(s, "learner", ["pred", "val"])
    s.add_edge(o, "perceives", _part(s, FORECAST, "tea_leaves"))
    s.tick(500_000)

    before = _views(s, "percept", "learner")[0]
    assert before["ap_covered"] is None, (
        f"the learner holds nothing yet covered {before['ap_covered']}")

    s.add_edge(o, "holds_part", _part(s, FORECAST, "barometer"))
    s.tick(500_000)

    after = _views(s, "percept", "learner")[0]
    assert after["ap_covered"] == 2, (
        f"acquiring the part did not re-arm the decode: covered "
        f"{after['ap_covered']!r}, ap_seen {after['ap_seen']!r}")
    assert not after["ap_residual"]
