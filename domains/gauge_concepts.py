"""gauge_concepts — the jabberwock UNDERSTANDS a gauge/bar and MAPS it.

The "last three turns" reading is NOT a hard-coded binding (it is dynamic and
situation-dependent). Instead the agent understands the CONCEPT of a gauge — a
thing that INDICATES a QUANTITY by its EXTENT, which CHANGES as the quantity is
consumed — and RECOGNISES (maps) the perceived ls20 strip as one. Then "how much
is left / the last N" is just READING the gauge (current extent + its scale +
the per-action depletion the agent already induced), not a bespoke rule.

The concept it looked up: gauge -> measuring instrument; indicator -> information;
scale -> standard/unit; quantity -> abstraction (jabberwock_grounds_bounds
--concepts gauge meter indicator scale quantity ...).

ATOMS I ground (perceptual/temporal sensorium — not genus-differentia):
  · long_thin(region)     — an elongated strip: long axis >= MINLEN and >= RATIO×
        the short axis. The shape a gauge has (its extent encodes a magnitude).
  · type_depletes(region) — the region's TYPE is the vanishing side (``frm_type``)
        of a change-rule the agent INDUCED from watching the turns: its substance
        is consumed each action. THE DYNAMIC signature — read from the agent's OWN
        induced ImpliedRule nodes, so it is grounded in what it observed, not told.
  · has_scale(region)     — a collinear SERIES sits on the region's line (its
        markers / scale — the dots at the end of the bar).

CONCEPT the agent composes (its own _spec_to_term, genus-differentia in its vocab):
  · gauge(x) := long_thin(x) AND type_depletes(x) AND NOT in_play(x)
        an elongated, OUT-of-play strip whose substance is consumed per action =
        an indicator of a depleting quantity. The agent can EXPLAIN it to the atoms.
"""
from __future__ import annotations

from substrate import (And, Attr, Eq, Exists, Gte, InNeighbours, Lit, MaxOver,
                        Minus, Neighbours, Or, Pick, Times, Var)

MINLEN = 10     # the long axis must span at least this many cells (a real strip)
RATIO = 6       # ...and be at least this many times the short axis (thin)

GENUS = {
    "long_thin": "atom: an elongated strip (perceptual shape)",
    "type_depletes": "atom: this type is consumed each action (induced rule)",
    "has_scale": "atom: a collinear series of markers on its line (perceptual)",
    "gauge": ("long_thin AND type_depletes AND NOT in_play — an out-of-play strip "
              "whose substance is consumed per action = a depleting quantity "
              "indicator (gauge -> measuring instrument; agent-composed)"),
}


def _install_atoms(agent):
    x = Var("x")
    cells = InNeighbours(x, "within")
    if "long_thin" not in agent._concept_nodes:
        width = Minus(MaxOver(cells, "c", Attr(Var("c"), "col"), default=Lit(0)),
                      _minover(cells, "col"))
        height = Minus(MaxOver(cells, "c", Attr(Var("c"), "row"), default=Lit(0)),
                       _minover(cells, "row"))
        # long axis is the larger of width/height; require it >= MINLEN and
        # >= RATIO * the short axis. Expressed for both orientations.
        horiz = And(items=(Gte(width, Lit(MINLEN)),
                           Gte(width, Times(items=(Lit(RATIO), height)))))
        vert = And(items=(Gte(height, Lit(MINLEN)),
                          Gte(height, Times(items=(Lit(RATIO), width)))))
        agent.ground_concept("long_thin", Or(items=(horiz, vert)), domain="space")
    if "type_depletes" not in agent._concept_nodes:
        rtype = Attr(Pick(cells), "world_type")
        rules = Neighbours(Var("agent"), "induced_implied_rule")
        agent.ground_concept(
            "type_depletes",
            Exists(rules, "r", Eq(Attr(Var("r"), "frm_type"), rtype)),
            domain="space")
    if "has_scale" not in agent._concept_nodes:
        # a SERIES (kind="series") sits collinear_with this region — its markers.
        series = Neighbours(x, "collinear_with")
        agent.ground_concept(
            "has_scale",
            Exists(series, "s", Eq(Attr(Var("s"), "kind"), Lit("series"))),
            domain="space")


def _minover(cells, key):
    from substrate import MinOver
    return MinOver(cells, "c", Attr(Var("c"), key), default=Lit(0))


_SPEC = ["And",
         ["Holds", "long_thin", ["Var", "x"]],
         ["And", ["Holds", "type_depletes", ["Var", "x"]],
          ["Not", ["Holds", "in_play", ["Var", "x"]]]]]


def install_gauge_concept(agent):
    """Ground the atoms, then have the AGENT compose `gauge` from a genus-
    differentia spec in its own vocabulary. Requires `in_play` already grounded
    (figure_ground_concepts). Idempotent."""
    _install_atoms(agent)
    if "gauge" not in agent._concept_nodes:
        cid = agent.ground_concept("gauge", agent._spec_to_term(_SPEC), domain="space")
        agent.mind_graph.node(cid).attrs["because"] = GENUS["gauge"]
    for n, why in GENUS.items():
        c = agent._concept_nodes.get(n)
        if c is not None and not agent.mind_graph.node(c).attrs.get("because"):
            agent.mind_graph.node(c).attrs["because"] = why
    return agent._concept_nodes["gauge"]
