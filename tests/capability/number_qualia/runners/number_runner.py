"""Runner for the number-qualia cross-domain-transfer experiment (sub-experiment (j)).

The load-bearing design commitment: there is ONE domain-agnostic isolation recipe,
`felt_isolation_band(...)`, that maps a concept's EMERGENT structural connectivity to a
coarse felt band on the substrate's `dynamical:commitment` axis. The SAME recipe is
applied unchanged to integers (source) and to graph nodes (target). That sameness is
what makes a transfer a *transfer* and not a hand-authored correspondence — the axis is
read verbatim on the target from its own neutral structure (design mechanism 2a).

Honest constraints discovered while building (STEP A), stated so they are not hidden:
  · `concept_signature` abstracts edge MULTIPLICITY (structure-mapping): a raw
    isolation COUNT does not survive into the signature. So isolation is carried as a
    DERIVED felt coordinate on the commitment axis, per the design's §3
    produced/derived, per-item-blind discipline — NOT planted (the recipe contains no
    per-item token; it is a uniform function of emergent connectivity).
  · the commitment axis (quantum 0.25, half_width 4) SATURATES, so isolation is a
    COARSE BAND (isolated -> high step; connected -> dark), not a fine gradient. This is
    the design's declared banding hazard, embraced, not tuned away.

Everything here is Python/JSON over the frozen `.so`; teacher-free; additive.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional

from substrate_rs import _native

import domains.analogy_search as asr

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
VOCAB = os.path.join(_ROOT, "seeds", "shape_vocabulary.json")
QUALIA = os.path.join(_ROOT, "seeds", "qualia_space.json")

COMMITMENT = "dynamical:commitment"
ISO_GRAIN = {COMMITMENT: 0.25}


class SolverSpy:
    """Counts calls into any EXACT domain solver (integer factoriser, graph
    cut-vertex/Tarjan detector, ...). The felt path must leave this at 0; the exact
    solver runs only in the separate verification step. Proves the felt read did not
    secretly compute the answer."""
    def __init__(self):
        self.calls = 0

    def __call__(self, *a, **k):
        self.calls += 1
        return None


# --------------------------------------------------------------------------- #
#  THE ONE DOMAIN-AGNOSTIC ISOLATION RECIPE (shared by source + target)
# --------------------------------------------------------------------------- #
def felt_isolation_field(connectivity: dict, *, exclude: Optional[set] = None,
                         quantile: float = 0.25) -> dict:
    """Map {item -> emergent structural connectivity} to {item -> identity_field}
    (0.0 = connected/dark, 1.0 = isolated/felt-high) by a SINGLE uniform rule:
    an item whose connectivity is in the bottom `quantile` of the (non-excluded)
    connectivities is FELT-ISOLATED. `exclude` drops degenerate hyper-connected
    universals (the integer unit 1; a graph's universal hub) from the threshold basis
    — a structural, per-item-blind exclusion, not a per-item flag. No item name enters
    the rule. This is the axis that transfers: identical recipe, any domain."""
    exclude = exclude or set()
    basis = sorted(c for it, c in connectivity.items() if it not in exclude)
    if not basis:
        return {it: 0.0 for it in connectivity}
    idx = max(0, int(round(quantile * len(basis))) - 1)
    thresh = basis[idx]
    return {it: (1.0 if (it not in exclude and connectivity[it] <= thresh) else 0.0)
            for it in connectivity}


def _seed_common():
    s = _native.Substrate()
    ag = s.add_node("Agent", {"name": "jabberwock"})
    for path in (VOCAB, QUALIA):
        summ = s.load_seed_manifest(json.load(open(path)), ag)
        assert not summ.get("rules_skipped"), (path, summ)
    asr._QUALIA_SCHEMA_CACHE.clear()
    return s, ag


def _observer(s):
    return s.add_node("Observer", {"name": "iso", "grain": dict(ISO_GRAIN)})


def isolation_step(s, node, obs) -> int:
    """Read the felt isolation coordinate off the commitment axis via
    concept_signature (the felt path: a pure signature read, no solver). Integer
    step; 0 = dark/connected, >0 = felt-isolated band."""
    for t in asr.concept_signature(s, node, observer=obs):
        if isinstance(t, tuple) and len(t) >= 3 and t[0] == COMMITMENT:
            return int(t[2])
    return 0


# --------------------------------------------------------------------------- #
#  SOURCE DOMAIN — integers 1..N with neutral type-uniform structural edges
# --------------------------------------------------------------------------- #
def _divisors_in(n, S): return [d for d in S if d != n and n % d == 0]
def _multiples_in(n, S): return [m for m in S if m != n and m % n == 0]


def integer_connectivity(N: int) -> dict:
    """EMERGENT structural connectivity of each integer in 1..N: number of in-set
    divisors + in-set multiples. Pure structure; not seeded as an attr."""
    S = list(range(1, N + 1))
    return {n: len(_divisors_in(n, S)) + len(_multiples_in(n, S)) for n in S}


def build_integers(N: int):
    """Neutral, type-uniform integer corpus + the derived isolation band on the
    commitment axis. Same edge TYPES for every integer (has_part=factor,
    member_of=multiple, depends_on=residue-class); only fillers differ. The felt
    coordinate is derived by the shared `felt_isolation_field` recipe (unit 1 excluded
    as the degenerate hyper-connected universal). Returns (s, node, S, iso_field)."""
    s, ag = _seed_common()
    mt = s.add_node("Microtheory", {"name": "integers", "temperature": 1.0,
                                    "discrete_mode": "3state"})
    S = list(range(1, N + 1))
    conn = integer_connectivity(N)
    iso = felt_isolation_field(conn, exclude={1})
    node = {}
    rescls = {}
    for k in (2, 3, 4, 5):
        for r in range(k):
            rescls[(k, r)] = s.add_node("Concept", {"name": "res_%d_%d" % (k, r),
                                                    "category": "residue_class"})
    for n in S:
        node[n] = s.add_node("Concept", {"name": "num_%d" % n, "category": "number",
                                         "state": 0.0, "external_field": 0.0,
                                         "identity_field": float(iso[n])})
        s.add_edge_unchecked(mt, "has_concept", node[n])
    for n in S:
        for d in _divisors_in(n, S):
            s.add_edge_unchecked(node[n], "has_part", node[d],
                                 {"relation": "has_factor"})
        for m in _multiples_in(n, S):
            s.add_edge_unchecked(node[n], "member_of", node[m],
                                 {"relation": "divides"})
        for k in (2, 3, 4, 5):
            s.add_edge_unchecked(node[n], "depends_on", rescls[(k, n % k)],
                                 {"relation": "residue_mod_%d" % k})
    return s, node, S, iso


def source_isolates(N: int) -> list:
    """The integers the felt isolation axis flags (read via concept_signature),
    within-domain — the SOURCE-DOMAIN VALIDATION readout. Teacher-free signature read
    only (no factoriser in this path)."""
    s, node, S, _iso = build_integers(N)
    obs = _observer(s)
    return [n for n in S if isolation_step(s, node[n], obs) > 0]



# --------------------------------------------------------------------------- #
#  TARGET DOMAIN — graphs. Nodes as Concepts with neutral type-uniform structural
#  edges. The SAME `felt_isolation_field` recipe is applied to graph-node
#  connectivity (degree). NON-CIRCULARITY NOTE (honest): "connectivity" means the
#  same thing structurally in both domains — an edge count — and the recipe is read
#  VERBATIM. Whether low graph-connectivity actually predicts cut-vertex-ness is the
#  OPEN empirical transfer question, NOT assumed: a cut-vertex can be high-degree (a
#  hub bridging two clusters), so this transfer may partly fail. We do not adjust the
#  recipe to make it succeed — that would be the hand-authored mapping the design
#  forbids. The result is whatever it is.
# --------------------------------------------------------------------------- #
def graph_connectivity(adj: dict) -> dict:
    """EMERGENT structural connectivity of each graph node = its degree. Same
    structural quantity (edge count) as the integer domain's connectivity."""
    return {v: len(adj[v]) for v in adj}


def build_graph(adj: dict, *, exclude_hub: bool = True):
    """Neutral, type-uniform graph corpus + the derived isolation band on the SAME
    commitment axis via the SAME `felt_isolation_field` recipe. One Concept per node;
    a single neutral structural edge type `adjacent_to` (undirected -> both
    directions). `exclude_hub` drops the single highest-degree node from the
    threshold basis, mirroring the integer domain excluding the unit 1 (a structural,
    per-item-blind exclusion — NOT a per-node flag). Returns (s, node, iso_field)."""
    s, ag = _seed_common()
    mt = s.add_node("Microtheory", {"name": "graph", "temperature": 1.0,
                                    "discrete_mode": "3state"})
    conn = graph_connectivity(adj)
    hub = max(conn, key=lambda v: conn[v]) if (exclude_hub and conn) else None
    iso = felt_isolation_field(conn, exclude={hub} if hub is not None else set())
    node = {}
    for v in adj:
        node[v] = s.add_node("Concept", {"name": "gnode_%s" % v, "category": "graph_node",
                                         "state": 0.0, "external_field": 0.0,
                                         "identity_field": float(iso[v])})
        s.add_edge_unchecked(mt, "has_concept", node[v])
    for v in adj:
        for w in adj[v]:
            s.add_edge_unchecked(node[v], "adjacent_to", node[w],
                                 {"relation": "adjacent"})
    return s, node, iso


def graph_felt_isolated(adj: dict) -> list:
    """The graph nodes the felt isolation axis flags, read via concept_signature
    (the felt path — a signature read, NO graph algorithm runs here). This is the
    TRANSFERRED coordinate applied to the target's own neutral structure."""
    s, node, _iso = build_graph(adj)
    obs = _observer(s)
    return [v for v in adj if isolation_step(s, node[v], obs) > 0]


# --------------------------------------------------------------------------- #
#  SCORING-SIDE EXACT GROUND TRUTH — a from-scratch cut-vertex (articulation
#  point) detector. This is the VERIFICATION step. It must be called ONLY in
#  scoring, NEVER inside the felt path (the SolverSpy proves 0 calls during the felt
#  read). Standard DFS low-link (Tarjan) articulation-point algorithm.
# --------------------------------------------------------------------------- #
def tarjan_cut_vertices(adj: dict, *, spy: Optional[SolverSpy] = None) -> set:
    """Exact articulation points of an undirected graph via DFS low-link. If `spy`
    is supplied it is pinged (this is the EXPENSIVE verify step; the felt path passes
    no spy here and must not call this at all)."""
    if spy is not None:
        spy()
    visited, disc, low, parent, ap = set(), {}, {}, {}, set()
    timer = [0]

    def dfs(u):
        visited.add(u)
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        children = 0
        for w in adj[u]:
            if w not in visited:
                parent[w] = u
                children += 1
                dfs(w)
                low[u] = min(low[u], low[w])
                if parent.get(u) is None and children > 1:
                    ap.add(u)
                if parent.get(u) is not None and low[w] >= disc[u]:
                    ap.add(u)
            elif w != parent.get(u):
                low[u] = min(low[u], disc[w])

    for v in adj:
        if v not in visited:
            parent[v] = None
            dfs(v)
    return ap



# --------------------------------------------------------------------------- #
#  SHAPE-NATIVE readout (sign-free, order-free). A thought is a shape, not a
#  signed symbol: an "outlier" is an element that STICKS OUT FROM THE BULK of the
#  distribution — either pole. Reading the coordinate this way dissolves the
#  "sign-flip" projection artifact (a mirrored outlier-shape is the SAME shape).
#  This is the correct instrument for a transfer CLAIM about shapes; a signed rank
#  correlation is a symbolic projection and is deliberately NOT used for it.
# --------------------------------------------------------------------------- #
def outliers_from_bulk(values: dict, *, z: float = 1.0) -> set:
    """The outlier-shape of a distribution: elements at least `z` mean-absolute-
    deviations from the median (the bulk centre), EITHER pole. Sign-free and
    order-free — 'sticks out from the bulk' is what outlier/prickly MEANS."""
    if not values:
        return set()
    xs = sorted(values.values())
    n = len(xs)
    med = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0
    mad = sum(abs(v - med) for v in values.values()) / n or 1.0
    return {k for k, v in values.items() if abs(v - med) >= z * mad}


# --------------------------------------------------------------------------- #
#  THE (b) / MINT-TARGET AXIS — bridge/redundancy, the structural feature that
#  actually predicts criticality and SURVIVES degree-regular graphs (where the
#  connectivity/degree axis is flat and carries no signal). redundancy(v) = how
#  interconnected v's neighbours are among themselves (fraction of neighbour-pairs
#  that are adjacent — the local clustering numerator). LOW redundancy = v's edges
#  are load-bearing bridges = critical. This is a DIFFERENT structural read from
#  degree; the path graph exposes it (interior nodes have 0 neighbour-interconnect)
#  while degree is uniformly 2. Same shape-native readout applies.
# --------------------------------------------------------------------------- #
def bridge_deficit(adj: dict) -> dict:
    """Per node: 1 - (neighbour-interconnection fraction). High = few of my
    neighbours are connected to each other = I am a bridge/bottleneck. Pure
    structure, computed uniformly; the felt path reads it as a coordinate, it does
    NOT run a cut-vertex solver."""
    out = {}
    for v in adj:
        nb = list(adj[v])
        if len(nb) < 2:
            out[v] = 1.0          # a leaf/degree-1: trivially non-redundant
            continue
        pairs = 0
        connected = 0
        for i in range(len(nb)):
            for jj in range(i + 1, len(nb)):
                pairs += 1
                if nb[jj] in adj[nb[i]]:
                    connected += 1
        out[v] = 1.0 - (connected / pairs if pairs else 0.0)
    return out


def build_graph_axis(adj: dict, coord: dict, *, exclude_hub: bool = False):
    """Build the graph corpus with the felt band derived from an ARBITRARY neutral
    structural coordinate `coord` (connectivity for the transferred number-axis;
    bridge_deficit for the minted criticality axis). Same recipe, different neutral
    coordinate — this is minting a SECOND axis when the first is underdimensioned,
    not hand-mapping the answer. Returns (s, node)."""
    s, ag = _seed_common()
    mt = s.add_node("Microtheory", {"name": "graph", "temperature": 1.0,
                                    "discrete_mode": "3state"})
    hub = max(coord, key=lambda v: coord[v]) if (exclude_hub and coord) else None
    # for bridge_deficit HIGH = critical, so we want the HIGH pole flagged; the
    # felt_isolation_field flags the LOW pole. We therefore feed the coordinate
    # such that "flagged" = "far-from-bulk", which the shape-native readout handles
    # sign-free downstream; here we just seed identity_field = normalized coord.
    lo = min(coord.values()); hi = max(coord.values()) or 1.0
    node = {}
    for v in adj:
        frac = (coord[v] - lo) / (hi - lo) if hi > lo else 0.0
        node[v] = s.add_node("Concept", {"name": "gnode_%s" % v,
                                         "category": "graph_node",
                                         "state": 0.0, "external_field": 0.0,
                                         "identity_field": float(frac)})
        s.add_edge_unchecked(mt, "has_concept", node[v])
    for v in adj:
        for w in adj[v]:
            s.add_edge_unchecked(node[v], "adjacent_to", node[w],
                                 {"relation": "adjacent"})
    return s, node



# --------------------------------------------------------------------------- #
#  META-SHAPE MATCH AGAINST KNOWN SOLUTIONS (the path-rescue mechanism)
#
#  The per-element outlier read fails on a degree-regular path: criticality there
#  is not a WITHIN-INSTANCE outlier. The felt move that works is higher-order —
#  recognise the WHOLE configuration's meta-shape, match it against a library of
#  EARNED (exactly-solved-once) exemplars, and import the exemplar's solution as a
#  STRUCTURAL-ROLE template. "This graph feels like a chain -> a chain's load-bearing
#  nodes are its spine -> flag the spine." No per-node outlier, no solver at felt
#  time. This is analogical retrieval against solved exemplars, which is how the
#  feel of a known problem-shape actually works.
#
#  NON-CIRCULARITY: the library is EARNED (Tarjan solves the EXEMPLARS once, at build
#  time, spy-tracked); a fresh instance's answer comes from the meta-shape MATCH plus
#  a structural role, never a node-id lookup and never a hand-authored
#  "chain -> interior" table (that hand-table is the Arm-2 hollow control). The felt
#  match of a fresh graph runs NO solver.
# --------------------------------------------------------------------------- #
def degree_role(adj: dict, v) -> str:
    """A node's structural degree-role: leaf(1) / spine(2) / hub(>=3). Uniform,
    structural; the vocabulary the solution-template is expressed in (roles, not
    node ids), so a template learned on one graph instantiates on any other."""
    d = len(adj[v])
    return "leaf" if d == 1 else ("spine" if d == 2 else "hub")


def meta_shape(adj: dict) -> list:
    """Whole-graph META-SHAPE descriptor: an integer profile of the configuration's
    shape — [frac_leaf, frac_spine, frac_hub, avg_clustering, is_regular] (each
    scaled to a small int). Structural and uniform across graphs of any size; no
    per-graph token. Compared via the substrate's shape_signature distance."""
    n = len(adj) or 1
    degs = [len(adj[v]) for v in adj]
    frac_leaf = sum(1 for d in degs if d == 1) / n
    frac_spine = sum(1 for d in degs if d == 2) / n
    frac_hub = sum(1 for d in degs if d >= 3) / n
    bd = bridge_deficit(adj)
    avg_clust = 1.0 - (sum(bd.values()) / n)
    regular = 1.0 if len(set(degs)) <= 1 else 0.0
    return [int(round(frac_leaf * 10)), int(round(frac_spine * 10)),
            int(round(frac_hub * 10)), int(round(avg_clust * 10)), int(round(regular))]


def build_solution_library(exemplars: dict, *, spy: Optional[SolverSpy] = None) -> dict:
    """EARN the library: for each exemplar graph, compute its meta-shape and its
    solution-template — the set of structural degree-ROLES its cut-vertices occupy —
    by solving it EXACTLY ONCE (Tarjan, spy-tracked as library-build compute). Returns
    {name: {"meta": meta_shape, "roles": sorted role set}}. This is the only place the
    exact solver touches an exemplar; the felt path below never calls it."""
    lib = {}
    for name, adj in exemplars.items():
        crit = tarjan_cut_vertices(adj, spy=spy)          # exact, ONCE, at build time
        roles = sorted(set(degree_role(adj, v) for v in crit))
        lib[name] = {"meta": meta_shape(adj), "roles": roles}
    return lib


def felt_meta_match(fresh_adj: dict, library: dict, substrate,
                    *, spy: Optional[SolverSpy] = None) -> dict:
    """FELT PATH (solver-free): match a fresh graph's meta-shape to the nearest library
    exemplar (via the substrate's shape_signature distance), import that exemplar's
    structural-role template, and instantiate the predicted critical set on the fresh
    graph's OWN structure. Passes NO spy to any solver — if a SolverSpy is supplied it
    must remain at 0 (the felt read computed nothing exact). Returns
    {nearest, match_dist, predicted, roles}."""
    fms = meta_shape(fresh_adj)
    fsig = substrate.shape_signature(fms)
    best, best_d = None, None
    for name, entry in library.items():
        d = substrate.shape_signature_distance(fsig,
                                                substrate.shape_signature(entry["meta"]))
        if best_d is None or d < best_d:
            best_d, best = d, name
    roles = library[best]["roles"]
    predicted = {v for v in fresh_adj if degree_role(fresh_adj, v) in roles}
    return {"nearest": best, "match_dist": best_d, "roles": roles,
            "predicted": predicted}
