"""TWO EYES — the gates that protect the ocular-dominance work before it exists.

Three things are pinned here, each earned by something that was measured rather
than assumed:

1. THE DICT COLLISION (the highest-value find). Two eyes share a coordinate
   frame, so merging their bipolar maps with `dict.update` silently drops one
   eye and reports 100%% ocular dominance as a pure artifact. Gated by asserting
   the COUNT, because a short map looks exactly like a correct one.

2. THE AMBIGUOUS CONFIG READ. `Pick(NodesOfType(XParams))` silently returns one
   of N. `PickUnique` raises. At N=0/N=1 it is byte-identical to `Pick`, which
   is why the 185 rebinds change no committed result (PROTOCOL §9).

3. THE MULTI-EYE FACTS THEMSELVES — that two eyes already run, that Gamma admits
   a binocular unit, and that an eyeless graph is inert rather than a crash.
   These are the premise the OD work rests on; they were verified live, and a
   test is how they stay true.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains import engine_provenance as ep  # noqa: E402

ep.engine_preamble()

import substrate_rs as S  # noqa: E402

from domains.onoff_world import (add_onoff_retina, add_signed_units,  # noqa: E402
                                 bipolars_of_eye, merge_bipolars)
from domains.wave_world import WaveWorld  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402


def _boot(seeds=("vision_waves",)):
    s, ag = boot_core()
    load_seeds_into(s, ag, list(seeds))
    return s


# --------------------------------------------------------------------------- #
#  1. THE DICT COLLISION
# --------------------------------------------------------------------------- #
def test_naive_dict_merge_silently_drops_an_eye_THE_TRAP():
    """The trap, pinned as a FACT so nobody re-discovers it the expensive way.
    This asserts the BUG exists in `dict.update` — it is the reason
    `merge_bipolars` exists."""
    s = _boot(("vision_waves", "vision_onoff"))
    left = WaveWorld(s, h=8, w=8, seed=1)
    right = WaveWorld(s, h=8, w=8, seed=2)
    bl, br = add_onoff_retina(left), add_onoff_retina(right)
    assert len(bl) == len(br) == 128            # 8*8*2 polarities

    naive = {**bl, **br}
    assert len(naive) == 128, (
        "the two eyes' keys are supposed to collide — if this ever fails the "
        "key shape changed and this trap's shape changed with it")
    # ...and every survivor is the RIGHT eye. An entire eye, gone, silently.
    assert set(naive.values()) == set(br.values())
    assert not (set(naive.values()) & set(bl.values()))


def test_merge_bipolars_keeps_both_eyes_and_asserts_the_count():
    s = _boot(("vision_waves", "vision_onoff"))
    left = WaveWorld(s, h=8, w=8, seed=1)
    right = WaveWorld(s, h=8, w=8, seed=2)
    bl, br = add_onoff_retina(left), add_onoff_retina(right)

    merged = merge_bipolars({"L": bl, "R": br})
    assert len(merged) == 256, "2 eyes x 8x8x2 = 256; a short map is the bug"
    assert len(set(merged.values())) == 256, "every bipolar is distinct"
    assert set(bipolars_of_eye(merged, "L").values()) == set(bl.values())
    assert set(bipolars_of_eye(merged, "R").values()) == set(br.values())


def test_merge_bipolars_is_collision_proof_BY_CONSTRUCTION():
    """Honest scope on the fix, and on my own first attempt at this test.

    I first wrote this as `pytest.raises(ValueError)` — and it FAILED, because
    with the eye in the key a collision cannot occur: two eyes at identical
    coordinates give `("L",0,0,1)` and `("R",0,0,1)`, which are distinct. So
    the count assert inside `merge_bipolars` is UNREACHABLE defensive code
    guarding a future key-shape change, NOT a gate that fires today. Asserting
    a raise that cannot happen would have been a fake gate passing for the most
    trivial reason — the shape §1 exists to catch, in test form.

    What actually protects the OD work is the pair above: the trap is pinned as
    a fact, and the fix is pinned by COUNT. This pins the mechanism of the fix.
    """
    same_coords_both_eyes = {(0, 0, 1): "#L1", (0, 0, -1): "#L2"}
    other_eye = {(0, 0, 1): "#R1", (0, 0, -1): "#R2"}
    merged = merge_bipolars({"L": same_coords_both_eyes, "R": other_eye})

    assert len(merged) == 4, "identical coords in two eyes must NOT collide"
    assert merged[("L", 0, 0, 1)] == "#L1"
    assert merged[("R", 0, 0, 1)] == "#R1"
    # The naive merge on the same input loses half of it:
    assert len({**same_coords_both_eyes, **other_eye}) == 2


# --------------------------------------------------------------------------- #
#  2. THE AMBIGUOUS CONFIG READ
# --------------------------------------------------------------------------- #
def _read(term_type, s):
    return S.Term("Attr",
                  node=S.Term(term_type,
                              source=S.Term("NodesOfType",
                                            node_type="WaveParams")),
                  key="name").evaluate(None, s)


def test_PickUnique_is_byte_identical_to_Pick_at_one_and_zero():
    """PROTOCOL §9: the 185 rebinds must change nothing. They cannot, because
    at the only counts a well-formed graph has (0 or 1) the two Terms return
    the identical Value."""
    s = _boot()
    assert len(list(s.nodes("WaveParams"))) == 1
    assert _read("Pick", s) == _read("PickUnique", s) == "default"

    bare, _ag = boot_core()                      # no vision seed => 0 params
    assert _read("Pick", bare) is None
    assert _read("PickUnique", bare) is None


def test_PickUnique_RAISES_where_Pick_silently_ignores_a_second_params_node():
    """The reason this Term exists. `Pick` returning `default` here is a SILENT
    WRONG ANSWER: the second params node — the per-eye arm a monocular
    deprivation depends on — is ignored without a word."""
    s = _boot()
    s.add_node("WaveParams", {"name": "right_eye"})
    assert len(list(s.nodes("WaveParams"))) == 2

    assert _read("Pick", s) == "default"         # the bug, pinned
    with pytest.raises(BaseException) as e:      # PanicException is not Exception
        _read("PickUnique", s)
    assert "AMBIGUOUS" in str(e.value)


# --------------------------------------------------------------------------- #
#  3. THE MULTI-EYE FACTS
# --------------------------------------------------------------------------- #
def test_two_eyes_run_independently_on_one_substrate():
    """No de-singletoning was required for this: every vision rule is
    hub-anchored, so a second Retina hub is simply a second eye."""
    s = _boot()
    left = WaveWorld(s, h=16, w=16, seed=101)
    right = WaveWorld(s, h=16, w=16, seed=202)
    assert left.retina != right.retina
    assert not (set(map(str, left.cells.values()))
                & set(map(str, right.cells.values())))

    for i in range(40):
        k = 1 if i % 5 == 0 else 0
        left.step(ignite_k=k)
        right.step(ignite_k=k)
    # BOTH ALIVE (§1's fourth clause: a floor is satisfied by death).
    assert left.frame().mean() > 1e-6, "left eye is DEAD"
    assert right.frame().mean() > 1e-6, "right eye is DEAD"


def test_gamma_admits_a_binocular_unit():
    """Many-to-many eye->cortex needs NO new production: the projection is
    already graph data. This is why the OD setup is reachable."""
    s = _boot(("vision_waves", "vision_onoff"))
    left = WaveWorld(s, h=12, w=12, seed=1)
    right = WaveWorld(s, h=12, w=12, seed=2)
    bl, br = add_onoff_retina(left), add_onoff_retina(right)
    u = add_signed_units(left, bl, 1, rf=3, seed=0)[0]

    n_before = len(list(s.in_neighbours(u, "oo_post")))
    syn = s.add_node("OOSynapse", {"weight": 1.0, "touched": -1.0,
                                   "drow": 0.0, "dcol": 0.0, "polarity": 1.0})
    s.add_edge(br[(6, 6, 1)], "oo_pre", syn, None)
    s.add_edge(syn, "oo_post", u, None)
    assert len(list(s.in_neighbours(u, "oo_post"))) == n_before + 1


def test_an_eyeless_graph_is_inert_not_a_crash():
    """N=0 degenerate. Rules with no hub to match simply do not fire."""
    s = _boot(("vision_waves", "vision_onoff"))
    assert list(s.nodes("Retina")) == []
    for _ in range(3):
        s.tick()
