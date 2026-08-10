"""arc3_seed — mechanical JSON->graph loader for the ARC-AGI-3 game-class
meta-rules seed (``seeds/arc3_game.json``).

This is a SEED LOADER, not agent logic. It mirrors the existing seed
pattern (domains/design_patterns.py): read a JSON manifest and install its
graph data — here, into a CuriousAgent's mind_graph via the agent's OWN
public install methods. It is purely mechanical: no conditionals over graph
state, no agent decisions, idempotent (every install method is look-up-or-
create), no transition rules.

The seed (specified by the jabberwock itself) supplies four things and only
these:

  · CONCEPTS — the genus vocabulary (me / wall / opening / door / goal_cell)
    the agent currently sees only as opaque CellC<n>. Each is grounded via
    ``learn_word`` from a Term-tree in vocabulary the agent already holds;
    one that references an attribute the agent has not yet perceived is HELD
    as a known-unknown predicate until experience supplies it — which IS the
    "ground by interaction" behaviour. We supply the vocabulary, not the
    grounding.
  · PRODUCTIONS — admit the map edges (cell within SpatialLocation;
    SpatialLocation adjacent_location SpatialLocation; SpatialLocation
    bounded_by Boundary) so the planner routes over the grid as a map.
  · MICROTHEORY — the game-class scope holding the action-meaning slots and
    the objective / terminal predicate names (graph data the agent can read).
  · GOALS — a win-condition goal and a terminal-bound goal, expressed exactly
    like the seeded understand_space / preserve_resources goals: a Goal node
    with a ``satisfaction_term`` Term-tree, installed via ``_create_goal``.
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate import term_from_json  # noqa: E402
from substrate import Production, NodePattern  # noqa: E402
from substrate import (  # noqa: E402
    IfThenElse, Plus, Let, Var, Lit, term_to_subgraph,
)

_SEED_PATH = (Path(__file__).resolve().parent.parent
              / "seeds" / "arc3_game.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def install_arc3_seed(agent) -> dict:
    """Install the arc3_game meta-rules seed onto ``agent`` (a CuriousAgent).

    Mechanical and idempotent. Returns a small report of what was installed
    so a caller can verify the install without reaching into graph internals.
    """
    seed = _load_seed()
    report: dict = {"concepts": [], "productions": 0, "goals": [],
                    "microtheory": None}

    # --- Microtheory: the game-class scope (action slots + objective/terminal).
    mt = seed.get("microtheory") or {}
    if mt.get("name"):
        mt_id = agent.install_microtheory(
            mt["name"], description=mt.get("description", ""))
        # Stash the action-meaning slots / objective / terminal predicate
        # names as graph data on the Mt node so they are introspectable
        # (read-only metadata, not a decision).
        attrs = agent.mind_graph.node(mt_id).attrs
        for k in ("action_slots", "objective", "terminal"):
            if k in mt and k not in attrs:
                attrs[k] = mt[k]
        report["microtheory"] = mt["name"]

    # --- Concepts: the genus vocabulary, grounded (or held) via learn_word.
    for c in seed.get("concepts", []):
        ok, _msg = agent.learn_word(
            c["name"], c["definition"], domain=c.get("domain", "boundary"))
        report["concepts"].append({"name": c["name"], "grounded": bool(ok)})

    # --- Productions: admit the map edges so the planner routes over the grid.
    for p in seed.get("productions", []):
        src, tgt = p["src"], p["tgt"]
        prod = Production(
            src=NodePattern(src["type"], src["var"]),
            edge_type=p["edge_type"],
            tgt=NodePattern(tgt["type"], tgt["var"]),
            provenance=p.get("provenance", "seed:arc3_game"),
        )
        # Idempotent: skip if a production with this provenance already exists.
        already = any(
            agent.mind_graph.node(e.key.tgt).attrs.get("provenance")
            == prod.provenance
            for e in agent.mind_graph.out_edges(agent.gamma_root, "production"))
        if not already:
            agent._append_production(prod)
            report["productions"] += 1

    # --- Goals: win-condition + terminal-bound, as Goal nodes with
    #     satisfaction Term-trees — exactly the seeded-goal shape.
    present = {agent.mind_graph.node(gid).attrs.get("label")
               for gid in agent._get_top_level_goals()}
    for goal in seed.get("goals", []):
        label = goal["label"]
        if label in present:
            report["goals"].append({"label": label, "installed": False})
            continue
        sat = term_from_json(goal["satisfaction_term"])
        agent._create_goal(
            label=label,
            priority=float(goal.get("priority", 1.0)),
            persistent=bool(goal.get("persistent", True)),
            satisfaction_term=sat,
        )
        report["goals"].append({"label": label, "installed": True})

    # --- Navigation target: fold goal_cell into the agent's OWN exploration-
    #     value Term-tree. The agent already maximises a graph-resident
    #     exploration_value(cell) Term to pick which SpatialLocation to route
    #     to (_pick_goal -> _bfs_distances_to_goal -> visit_target). We do NOT
    #     replace that reasoning: we ADD one term in the agent's own
    #     vocabulary — a big salience bonus when the cell satisfies the
    #     agent's goal_cell DEFINITION — so that, once the colour-class
    #     structure is perceived (population != 0), the odd-one-out cell
    #     becomes the navigation target and the planner gets a target_wi
    #     BEFORE the agent reaches it.
    #
    #     The bonus INLINES the goal_cell definition (the same Term-tree the
    #     held goal_cell concept carries), bound over the candidate cell via
    #     Let(x = cell). We inline rather than use Holds because _pick_goal
    #     evaluates exploration_value with only {cell, agent} in scope (no
    #     _resolve_concept resolver) — inlining keeps the DECISION as the same
    #     graph-resident MinOver-over-colour-classes Term, just evaluated
    #     directly. Until the colour structure is perceived the population
    #     reads are absent so the predicate is falsey and the bonus is 0; the
    #     native recency / frontier / door terms drive exploration meanwhile.
    #     The bonus (1e9) sits just above the agent's own door_open_bonus
    #     (1e8) so a grounded goal cell wins. goal_cell stays a held
    #     HYPOTHESIS concept the win signal (my_won) confirms or refutes.
    goal_def_json = next((c["definition"] for c in seed.get("concepts", [])
                          if c["name"] == "goal_cell"), None)

    def _has_goal_bonus(t) -> bool:
        # Our marker: an IfThenElse whose cond is a Let binding x.
        return (isinstance(t, IfThenElse) and isinstance(t.cond, Let)
                and t.cond.name == "x")

    native = agent._exploration_value_term()
    already = isinstance(native, Plus) and any(
        _has_goal_bonus(t) for t in native.items)
    if goal_def_json is None or already:
        report["exploration_value_augmented"] = False
    else:
        goal_pred = Let(name="x", value=Var("cell"),
                        body=term_from_json(goal_def_json))
        goal_bonus = IfThenElse(cond=goal_pred, then=Lit(1e9), other=Lit(0))
        augmented = Plus(items=(native, goal_bonus))
        for e in list(agent.mind_graph.out_edges(
                agent.agent_root, "exploration_value")):
            agent.mind_graph._delete_edge(e.key)
        root = term_to_subgraph(augmented, agent.mind_graph)
        agent.mind_substrate.add_edge(
            agent.agent_root, "exploration_value", root)
        agent._named_predicate_cache["exploration_value"] = augmented
        report["exploration_value_augmented"] = True

    return report


__all__ = ["install_arc3_seed"]
