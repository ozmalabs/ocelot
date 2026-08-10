"""walker_world, migrated — full twin of `tests/test_walker_world.py`.

The world-only tests (origin, locality, kinematics, item-touch, statelessness)
exercise `WalkerWorld` itself and never needed a CuriousAgent; they are carried
verbatim here so the original file (which imports `CuriousAgent` at module
level) can be deleted. The single agent-path test runs the spatial/motor loop on
the seed-booted agent via the `WorldAdapter` (boot_core seeds, no CuriousAgent):
perceive Body/Joint and pick actions over several steps without crashing.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.walker_world import WalkerWorld, walker_world_handle


# --- world-only mechanics (no agent) -------------------------------------


def test_world_starts_at_origin():
    """Fresh world: body at x=0, joints at 0.5, nothing touched."""
    world = WalkerWorld()
    substrate, ctx = world.reset()
    body_nodes = list(substrate.graph.nodes("Body"))
    assert len(body_nodes) == 1
    assert body_nodes[0].attrs["x"] == 0.0
    joints = list(substrate.graph.nodes("Joint"))
    assert len(joints) == 2
    assert ctx["touched_items"] == frozenset()


def test_local_observation_filters_distant_items():
    """Only items within observation_radius appear in the substrate."""
    world = WalkerWorld(
        item_positions=(2.0, 50.0),
        observation_radius=3.0,
    )
    substrate, ctx = world.reset()
    item0 = list(substrate.graph.nodes("Item0"))
    item1 = list(substrate.graph.nodes("Item1"))
    assert len(item0) == 1
    assert len(item1) == 0


def test_synchronized_joints_produce_no_velocity():
    world = WalkerWorld()
    substrate, ctx = world.reset()
    substrate, ctx = world.apply_action(ctx, ("set_joints", 0.5, 0.5))
    assert ctx["body_x"] == 0.0
    assert world.interpret_acts_on(ctx, ("set_joints", 0.5, 0.5)) == []


def test_alternating_joints_produce_velocity():
    world = WalkerWorld()
    substrate, ctx = world.reset()
    substrate, ctx = world.apply_action(ctx, ("set_joints", 0.0, 1.0))
    assert ctx["body_x"] == 1.0
    substrate, ctx = world.apply_action(ctx, ("set_joints", 0.0, 1.0))
    assert ctx["body_x"] == 2.0


def test_item_touched_when_body_reaches_it():
    world = WalkerWorld(item_positions=(2.0,))
    substrate, ctx = world.reset()
    substrate, ctx = world.apply_action(ctx, ("set_joints", 0.0, 1.0))
    substrate, ctx = world.apply_action(ctx, ("set_joints", 0.0, 1.0))
    assert 0 in ctx["touched_items"]


def test_apply_action_does_not_mutate_input_ctx():
    """The preview pattern requires stateless apply_action — the input ctx
    must remain valid after the call so choose_action can try other candidates."""
    world = WalkerWorld()
    substrate, ctx0 = world.reset()
    x0 = ctx0["body_x"]
    touched0 = ctx0["touched_items"]
    # Apply an action; the original ctx0 should be unchanged.
    world.apply_action(ctx0, ("set_joints", 0.0, 1.0))
    assert ctx0["body_x"] == x0
    assert ctx0["touched_items"] == touched0


# --- agent path on the seed-booted WorldAdapter (no CuriousAgent) ---------


def test_agent_runs_in_walker_world_via_seed_agent():
    """Migrated `test_agent_runs_in_walker_world_without_crashing`: the
    seed-booted agent lives in the walker world for a handful of ticks via the
    WorldAdapter — perceive (Body, Joint), pick an action over the seeded
    curiosity score, advance — without crashing."""
    wa = WorldAdapter()
    handle = walker_world_handle(WalkerWorld(), None)
    substrate, ctx = handle["reset"]()
    wa.ingest(substrate)
    for _ in range(5):
        actions = handle["legal_actions"](substrate, ctx)
        assert len(actions) > 0
        action = wa.choose_action(
            actions, lambda a: handle["apply_action"](substrate, ctx, a)[0])
        assert action is not None
        substrate, ctx = handle["apply_action"](substrate, ctx, action)
        wa.ingest(substrate)
    # The agent observed something, including both body-types.
    assert "Body" in wa.senses()
    assert "Joint" in wa.senses()
