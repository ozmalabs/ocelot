"""world_play — MECHANICAL I/O for the world-understanding interface.

After steps 1-5 of the N-dim frame-understanding integration, ALL world-understanding is graph-native and runs
in master_tick from the DISCOVERED frame:
  · affordance_basis    — learn each control's displacement vector from observation (no geometry given).
  · principal_axes      — the jabberwock-AUTHORED Rust primitive: discover the frame's axes + dimensionality.
  · discovered_navigation — mark_self / mark_dist / aim_goal / pick_control_for_goal: derive self + goal and
                            choose the action by inverting the learned control basis. No grid, no hardcoded dirs.
  · nested_frame        — recognise a sub-frame by a basis change (a dimension outside the parent's span).

The Python consumer `world_understanding_step` (2D-grid: fill role slots, slide_flood, descend gradient, write
chosen_action, with controls hardcoded) has been DELETED — it was agent decisions in Python, the exact thing
CLAUDE.md forbids. This module is now ONLY the admissible adapter boundary: declare the world's affordances and
read back the action the graph chose. No decisions, no navigation, no agent state.
"""
from __future__ import annotations


def declare_affordances(agent, game, control_names):
    """Mechanical I/O: declare the world's available controls as geometry-free Control nodes (the agent learns
    their effects via affordance_basis). One has_control edge per control. Returns {name: node}."""
    out = {}
    for nm in control_names:
        c = agent.s.add_node("Control", {"name": nm})
        agent.inner.add_edge_unchecked(game, "has_control", c)
        out[nm] = c
    return out


def read_chosen(agent, game):
    """Mechanical I/O: read the action the graph-native navigation chose this tick (pick_control_for_goal sets
    game.chosen_control). Returns the control name or None."""
    return agent.s.node(game)["attrs"].get("chosen_control")


def wire_world_understanding(agent):
    """DEPRECATED no-op. Navigation is now entirely graph-native (the seeds above fire in master_tick); there is
    no Python consumer to wire. Kept so older callers don't break. Use declare_affordances / read_chosen for the
    I/O boundary; everything else is the graph."""
    return None
