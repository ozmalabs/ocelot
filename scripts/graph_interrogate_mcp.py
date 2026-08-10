"""graph_interrogate_mcp — a thin MCP server exposing the READ-ONLY graph
interrogator as tools, reusing `scripts.graph_interrogate.GraphInterrogator`.

This adds NO query logic of its own — every tool is a one-line delegation to the
same `GraphInterrogator` the CLI uses, so `graph_query` still runs on the
substrate's OWN DSL evaluator (engine "live-dsl"). It is the MCP "ask" surface
to the same glass box the HTML visualiser lets you "look" at.

Run:
    GRAPH_INTERROGATE_DUMP=var/encyclopedic_grounded_graph.json \
        python -m scripts.graph_interrogate_mcp        # stdio MCP server

The snapshot is loaded once at startup (env GRAPH_INTERROGATE_DUMP, else the
default encyclopedic dump). Tools:
    node, nodes_of_type, neighbours, in_neighbours, subgraph, path,
    graph_query, types, edge_types
mirroring the CLI subcommands exactly. All READ-ONLY.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from scripts.graph_interrogate import GraphInterrogator, DEFAULT_DUMP

_DUMP = os.environ.get("GRAPH_INTERROGATE_DUMP", DEFAULT_DUMP)
_GI = GraphInterrogator.from_dump(_DUMP)

mcp = FastMCP("jabberwock-graph-interrogate")


@mcp.tool()
def node(id: int) -> dict[str, Any]:
    """Type + attrs of one node by integer id."""
    return _GI.node(id)


@mcp.tool()
def nodes_of_type(type: str) -> list[dict[str, Any]]:
    """All nodes of a given type, as {id, type, label}."""
    return _GI.nodes_of_type(type)


@mcp.tool()
def neighbours(id: int, edge_type: str | None = None) -> dict[str, Any]:
    """Out-neighbours of a node, grouped by edge type (optionally one edge type)."""
    return _GI.neighbours(id, edge_type)


@mcp.tool()
def in_neighbours(id: int, edge_type: str | None = None) -> dict[str, Any]:
    """In-neighbours of a node, grouped by edge type (optionally one edge type)."""
    return _GI.in_neighbours(id, edge_type)


@mcp.tool()
def subgraph(seed_ids: list[int], depth: int = 1, directed: bool = False) -> dict[str, Any]:
    """Ego/neighbourhood subgraph within `depth` hops of any seed id."""
    return _GI.subgraph(seed_ids, depth, directed)


@mcp.tool()
def path(a: int, b: int, directed: bool = False) -> dict[str, Any]:
    """A shortest path from node a to node b, if one exists."""
    return _GI.path(a, b, directed)


@mcp.tool()
def graph_query(term: dict[str, Any] | None = None, match: str | None = None) -> dict[str, Any]:
    """Evaluate a substrate DSL Term-tree against the graph, on the substrate's
    OWN evaluator (engine "live-dsl"). Pass EITHER `term` (a DSL wire-form dict,
    e.g. {"type":"NodesOfType","node_type":"Microtheory"}) OR `match` (the
    'TYPE where attr OP value [and ...]' mini-syntax that compiles to such a
    term). Node-set results return the induced subgraph too."""
    return _GI.graph_query(term=term, match=match)


@mcp.tool()
def types() -> dict[str, int]:
    """Node-type histogram of the loaded graph."""
    return _GI.type_histogram()


@mcp.tool()
def edge_types() -> dict[str, int]:
    """Edge-type histogram of the loaded graph."""
    return _GI.edge_type_histogram()


if __name__ == "__main__":
    mcp.run()
