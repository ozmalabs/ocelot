"""Theorem D weighted-traversal sampler over G.

Weights live in a separate map (not attrs) so that the same G can carry
multiple weight functions simultaneously (e.g., for ensemble sampling).
Transitions are restricted to Γ-admissible outgoing edges via C.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Iterable

from .graph import EdgeKey, NodeID
from .primitives import Substrate


WeightFn = Callable[[Substrate, NodeID, EdgeKey], float]
"""Non-negative scalar weight for traversing ``edge`` from ``src``."""


def uniform_weight(s: Substrate, src: NodeID, edge: EdgeKey) -> float:
    return 1.0


@dataclass
class WalkResult:
    visits: dict[NodeID, int] = field(default_factory=dict)
    terminated_at: list[NodeID] = field(default_factory=list)


def weighted_walk(
    substrate: Substrate,
    start: NodeID,
    n_walks: int,
    walk_length: int,
    weight_fn: WeightFn = uniform_weight,
    edge_types: Iterable[str] | None = None,
    seed: int | None = None,
) -> WalkResult:
    """Run ``n_walks`` weighted random walks from ``start``.

    Only existing edges (already admitted by C at insertion) are followed —
    no admissibility check needed at traversal time. ``edge_types`` restricts
    which outgoing edge-types are eligible.
    """
    rng = random.Random(seed)
    visits: dict[NodeID, int] = {}
    terminated: list[NodeID] = []
    edge_types_set = set(edge_types) if edge_types is not None else None

    for _ in range(n_walks):
        cur = start
        for _ in range(walk_length):
            candidates: list[tuple[EdgeKey, float]] = []
            for edge in substrate.out_edges(cur):
                if edge_types_set is not None and edge.key.edge_type not in edge_types_set:
                    continue
                w = weight_fn(substrate, cur, edge.key)
                if w > 0:
                    candidates.append((edge.key, w))
            if not candidates:
                terminated.append(cur)
                break
            keys, weights = zip(*candidates)
            chosen = rng.choices(keys, weights=weights, k=1)[0]
            cur = chosen.tgt
            visits[cur] = visits.get(cur, 0) + 1
    return WalkResult(visits=visits, terminated_at=terminated)
