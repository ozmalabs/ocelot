"""INERTIAL MASS BY ACTION — the robot works out mass by shoving things (gate).

Pre-registration: `PHYSICS_MASS_BY_ACTION_PREREG.md`. The agent PUSHES objects it
SEES (carved by the eye as persistent `Region` nodes) and discovers their HIDDEN
inertial mass FROM THE PUSH — the operational definition of inertial mass, F=ma
inverted (`m = impulse / Δv`). The world outputs ONLY pixels + affordances; each
object's mass is PRIVATE (never graphed), drawn from an untuned set (NOT 1/4/9).

Pipeline (all existing machinery + one graph-native rule, NO Rust):
- the agent CHOOSES a push on a SEEN Region via `choose_action_meta_curious`
  (+ `target_fn` → the seen Body, which carries a `seen_as` edge to the Region);
- a sustained push accelerates the object at `a = J/m`; the eye tracks it as ONE
  Region; the dimension-generic order-N loop (`TimeInfer` / `time_axis`) mints an
  ORDER-2 latent:time dimension whose `coeffs[1]` IS the perceived Δv (= a);
- the graph-native `seeds/mass_by_action.json` rule mints
  `MassScalar = IDiv(J, |a|)` on the PERCEIVED Region — grouping is by the eye's
  Region identity, never a world id.

Discriminator (registered before any number):
- push a seen object repeatedly -> order-2 -> MassScalar = J/a recovers the hidden
  mass, grouped by perceived Region, no published mass;
- a SINGLE push (then coast) -> order-1 -> NO mass (insufficient evidence);
- equal hidden mass -> equal scalar; ratio of scalars = ratio of hidden masses;
- J/Δv is INVARIANT across different impulses (= the mass);
- non-resonant (fractional a) -> the integer eye jitters the 2nd difference ->
  order-2 floors -> silent (the DEGRADE boundary).

Every product read from `native.evaluate()` (TUPLES) and the `run_rules` graph
state; NEVER a process-pattern wait.
"""
import numpy as np
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from domains import push_world as pw            # noqa: E402

H, W, K = 18, 140, 3
WIDE_H = 28                                      # room for two stacked objects


def _masses(world):
    """All minted MassScalars, read FROM THE GRAPH, flattened."""
    return sorted(v for vs in world.masses_by_region().values() for v in vs)


def recover_mass(mass, impulse, ticks=6, h=H, w=W):
    """Spin up a one-object push world, SUSTAINED-push it with `impulse`, and read
    back the mass the graph DISCOVERED (a list; [] if the order-2 witness floored).
    The hidden `mass` is private world state — never graphed."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, h, w, K, [{"mass": mass, "row": 7, "col": 1}],
                         [impulse], axis="col")
    pw.run_push_all(world, ticks, impulse)
    world.discover_masses()
    return world, _masses(world)


# ─────────────────────────────── the headline ──────────────────────────────

def test_agent_pushes_a_seen_object_and_discovers_its_mass():
    """The agent CHOOSES to push a SEEN Region (choose_action_meta_curious +
    target_fn), the object accelerates, order-N mints ORDER-2 from the PERCEIVED
    trajectory, and the graph-native rule mints MassScalar = J/a recovering the
    hidden mass (3) — read from the graph. Hidden mass J=6 -> a=2 -> m=3."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, H, W, K, [{"mass": 3, "row": 7, "col": 1}],
                         [6], axis="col")
    chosen = pw.run_push_episode(world, 6)       # the AGENT's own choices
    assert chosen, "the agent chose no action"
    assert all(a[0] == "push" for a in chosen), "every chosen action must be a push"
    # it pushed a SEEN Region every tick (the target had a seen_as edge)
    for a in chosen:
        assert world.target_fn(a) is not None

    # find the tracked Region's perceived trajectory (grouped by perceived id)
    live = set(world.native.neighbours(world.game, "has_region"))
    traj = [(rn, tr) for rn, tr in world.trajectories.items()
            if rn in live and len(tr["cy"]) >= pw.MIN_ORBIT]
    assert traj, "no live tracked Region with enough samples"
    rn, tr = max(traj, key=lambda kv: len(kv[1]["cy"]))
    frames = [[["obj", int(round(y)), int(round(x)), "obj"]]
              for y, x in zip(tr["cy"], tr["cx"])]

    # PRODUCT first: the Rust Term's verdict on the perceived points (TUPLES).
    assert world.native.evaluate(
        {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
         "codebook_type": "ShapeSignature", "max_b": 8, "field": "order"}, {}) == 2

    # GRAPH: the seeded run_rules fixpoint mints the MassScalar on the Region.
    world.discover_masses()
    assert _masses(world) == [3], "the discovered inertial mass must recover the hidden 3"

    # the scalar is keyed to a PERCEIVED Region (type 'Region'), via has_mass.
    by_region = world.masses_by_region()
    assert list(by_region.keys()), "mass must be linked to a Region node"
    for rnode in by_region:
        assert world.s.node(rnode)["type"] == "Region"


def test_a_single_push_mints_no_mass():
    """CONTROL — one impulse then COAST is constant velocity (order-1), not
    acceleration: no order-2, so no MassScalar (insufficient evidence)."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, H, W, K, [{"mass": 3, "row": 7, "col": 1}],
                         [6], axis="col")
    world._push(world._regions_nonground()[0]["node"], 6)   # exactly ONE push
    for _ in range(6):
        world._step()                                       # then coast
    world.discover_masses()
    assert _masses(world) == [], "a single push must mint NO mass"


def test_equal_hidden_mass_mints_equal_scalar():
    """CONTROL — two objects of EQUAL hidden mass, pushed with the same impulse,
    mint EQUAL scalars."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, WIDE_H, W, K,
                         [{"mass": 3, "row": 5, "col": 1},
                          {"mass": 3, "row": 18, "col": 1}], [6], axis="col")
    pw.run_push_all(world, 6, 6)
    world.discover_masses()
    scalars = _masses(world)
    assert scalars == [3, 3], f"equal masses must mint equal scalars, got {scalars}"


def test_mass_ratio_of_minted_scalars_matches_hidden_ratio():
    """CONTROL — two objects with DISTINCT hidden masses (2 and 3, adjacent — the
    hardest to separate, NOT a separability tune), same impulse J=6: the minted
    scalars are 2 and 3 (a1=3, a2=2), so their ratio equals the hidden mass ratio
    EXACTLY (0 error — the synthetic integer eye is exact at resonance)."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, WIDE_H, W, K,
                         [{"mass": 2, "row": 5, "col": 1},
                          {"mass": 3, "row": 18, "col": 1}], [6], axis="col")
    pw.run_push_all(world, 6, 6)
    world.discover_masses()
    scalars = _masses(world)
    assert scalars == [2, 3], f"hidden masses 2,3 must be recovered, got {scalars}"
    # ratio of minted scalars == ratio of hidden masses
    assert scalars[0] / scalars[1] == 2 / 3


def test_mass_is_invariant_across_different_impulses():
    """The operational invariant: impulse/Δv is CONSTANT across DIFFERENT impulses
    (= the mass). Hidden mass 6 pushed with J=6 (a=1), J=12 (a=2), J=18 (a=3) each
    mints the SAME scalar 6 = J/a."""
    for J, ticks in [(6, 8), (12, 6), (18, 5)]:
        _, m = recover_mass(6, J, ticks=ticks)
        assert m == [6], f"J={J}: impulse/Δv must recover the invariant mass 6, got {m}"


def test_agent_prefers_to_act_on_a_seen_object():
    """The see->link->ACT path: choose_action_meta_curious (+ target_fn) prefers a
    push whose target has been SEEN (a Body with a seen_as edge to a Region) over
    an identical push on an UNSEEN body (no seen_as)."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, H, W, K, [{"mass": 3, "row": 7, "col": 1}],
                         [6], axis="col")
    seen_region = world._regions_nonground()[0]["node"]
    seen_body = world.bodies[0]
    unseen_body = world.s.add_node("WorldInstance", {"world_type": "Body"})
    assert len(world.native.neighbours(seen_body, "seen_as")) == 1
    assert len(world.native.neighbours(unseen_body, "seen_as")) == 0
    actions = [("push", seen_region, 6), ("push", "UNSEEN", 6)]
    tmap = {seen_region: seen_body, "UNSEEN": unseen_body}
    picked = wa.choose_action_meta_curious(
        actions, lambda a: None, lambda a: ["Body"], lambda a: tmap[a[1]])
    assert picked == ("push", seen_region, 6), \
        "the agent must prefer to act on the object it has SEEN"


def test_world_publishes_no_mass_or_object_id_only_pixels_and_perception():
    """The genuine bar: the world graph carries ONLY pixels + the eye's Region
    carve. It NEVER publishes the object's mass, position, velocity, or a world
    object-id. The ONLY object-state present is the eye's PERCEIVED Region (cy/cx/
    drow) and the DISCOVERED MassScalar (an inference, not a published truth)."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, H, W, K, [{"mass": 3, "row": 7, "col": 1}],
                         [6], axis="col")
    pw.run_push_all(world, 6, 6)
    world.discover_masses()

    forbidden = {"mass", "position", "pos", "velocity", "vel", "vy", "vx",
                 "row", "col", "gravity", "g", "object_id", "obj_id", "oid",
                 "true_mass", "hidden_mass"}
    # hub: only a frame counter + world_type
    assert set(world.s.node(world.game)["attrs"].keys()) <= {"frame", "world_type"}
    # every grid cell: no attribute at all (no published coordinate)
    cell_set = set(world.cell_ids)
    for n in world.native.nodes("WorldInstance"):
        if int(str(n).lstrip("#")) in cell_set:
            assert world.s.node(n)["attrs"] == {}
    # Region carve, Body nodes: no forbidden key
    leaked = set()
    for r in world.native.neighbours(world.game, "has_region"):
        leaked |= set(world.s.node(r)["attrs"].keys()) & forbidden
    for b in world.bodies:
        leaked |= set(world.s.node(b)["attrs"].keys()) & forbidden
    assert not leaked, f"world graph leaked forbidden attr(s): {leaked}"
    # a Body carries only its type marker — NO mass, NO object index
    for b in world.bodies:
        assert set(world.s.node(b)["attrs"].keys()) <= {"world_type"}


def test_grouping_is_by_perceived_region_identity():
    """Grouping "same object" is the eye's PERCEIVED Region id — NOT a world id.
    Two distinct-mass objects are carved as two distinct Regions and get two
    distinct scalars keyed to those Region nodes; the MassScalar carries no world
    object-id, and it is reached only through has_mass from a live eye Region."""
    wa = pw.boot_push()
    world = pw.PushWorld(wa, WIDE_H, W, K,
                         [{"mass": 2, "row": 5, "col": 1},
                          {"mass": 6, "row": 18, "col": 1}], [6], axis="col")
    pw.run_push_all(world, 6, 6)
    world.discover_masses()

    by_region = world.masses_by_region()
    assert len(by_region) == 2, "two perceived objects -> two grouped Regions"
    live = set(world.native.neighbours(world.game, "has_region"))
    for rnode, ms in by_region.items():
        assert rnode in live, "grouping key must be a LIVE perceived Region"
        assert world.s.node(rnode)["type"] == "Region"
        # the scalar carries only the DISCOVERED quantities — no world object-id
        for m in world.native.neighbours(rnode, "has_mass"):
            keys = set(world.s.node(m)["attrs"].keys())
            assert keys <= {"mass", "impulse", "accel", "source"}
    assert sorted(v for vs in by_region.values() for v in vs) == [2, 6]


def test_untuned_distribution_recovered_at_resonant_impulses():
    """UNTUNED distribution: masses drawn (seed in block 140000-140999) from a set
    of small integers that is NOT 1/4/9 and NOT all-divisors-of-one-impulse. For
    each drawn mass, probing a small impulse menu recovers the hidden mass EXACTLY
    at every RESONANT impulse (J a multiple of m, a=J/m<=5) — coverage is total,
    error is zero where it mints — and the recovered value equals the hidden mass.
    """
    rng = np.random.default_rng(140100)
    pool = [2, 3, 4, 5, 6, 7]
    menu = [6, 10, 12, 14, 15]
    drawn = [int(x) for x in rng.choice(pool, size=4, replace=False)]
    for m in drawn:
        hits = []
        for J in menu:
            a = J / m
            if a == int(a) and 1 <= a <= 5:      # a resonant, trackable impulse
                _, rec = recover_mass(m, J, ticks=6)
                assert rec == [m], f"mass {m} via J={J} (a={a}) must recover {m}, got {rec}"
                hits.append(J)
        assert hits, f"no resonant menu impulse for hidden mass {m} (menu {menu})"


def test_nonresonant_impulse_floors_silently_the_degrade_boundary():
    """DEGRADE (honest boundary): when a=J/m is FRACTIONAL the integer eye jitters
    the perceived 2nd difference, the EXACT order-2 witness floors, and NO mass is
    minted — recovery is exact at resonance and SILENT between. The eye still
    TRACKS the object (it is not a tracking failure); it is the integer-lattice
    quantization (the frame/continuum invariant), the synthetic analogue of the
    eye's confab floor. Verified on the PRODUCT: the perceived trajectory is not
    order-2 explained."""
    world, rec = recover_mass(3, 5, ticks=7)     # a = 5/3, fractional
    assert rec == [], "a fractional-acceleration push must mint NO mass (floors)"
    # the region tracked fine (alive, enough samples) but order-N floored
    live = set(world.native.neighbours(world.game, "has_region"))
    tracked = [tr for rn, tr in world.trajectories.items()
               if rn in live and len(tr["cy"]) >= pw.MIN_ORBIT]
    assert tracked, "the eye should still TRACK the object (not a tracking failure)"
    tr = max(tracked, key=lambda t: len(t["cy"]))
    frames = [[["obj", int(round(y)), int(round(x)), "obj"]]
              for y, x in zip(tr["cy"], tr["cx"])]
    assert world.native.evaluate(
        {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
         "codebook_type": "ShapeSignature", "max_b": 8, "field": "explained"}, {}) is not True
