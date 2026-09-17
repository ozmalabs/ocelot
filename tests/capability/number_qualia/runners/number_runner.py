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



# --------------------------------------------------------------------------- #
#  THE APERTURE MANIFOLD (track_j3): "local/global is aperture, not magic".
#
#  The meta-shape library (track_j2) rescued the path by matching the WHOLE
#  configuration against solved exemplars — order-4 in the shape ladder. But that
#  was not a SEPARATE mechanism: it was the SAME structural read at a COARSER
#  APERTURE. The substrate already owns the aperture dial natively —
#  domains.order_n_concepts.nth_order_terms — the finite-difference machinery
#  falling_world uses to discover an order-2 generator from raw pixel samples.
#  Order 0 = the value; each order is one finite-difference pass (a wider aperture
#  over the SAME structural coordinate). Local vs global was never two kinds of
#  property; it is one structural read at two orders.
#
#  DESIGN PRINCIPLE (there is no need to choose a single method): we do NOT argmax
#  to one aperture and we do NOT "switch to calculator k". We KEEP EVERY APERTURE
#  LIVE as parallel coordinates over the structural quantity and read the SHAPE of
#  the resulting manifold — the (node x order) map of local outliers. The property
#  localizes wherever a bounded-radius outlier appears at SOME aperture; its shape
#  across apertures IS the confidence interval.
#
#  THE HONEST FENCE (bounded vs unbounded witness): widening the aperture over a
#  LOCAL coordinate crosses many apparent local/global lines (a path's global
#  criticality becomes a local order-1 boundary) but CANNOT cross into
#  unbounded-radius facts — e.g. "does a large cycle close?", which no bounded
#  aperture sees. There is no cheaper local coordinate that fixes this; the honest
#  move is a CONFIDENCE GATE that detects the blind regime (a cycle is present) and
#  ABSTAINS to verify, rather than committing a falsely-sharp peak (the
#  anti-Dunning-Kruger property). This is the sharp form of the coverage ceiling:
#  feel commits on bounded-witness structure, abstains on unbounded-witness.
# --------------------------------------------------------------------------- #
def _eval_diff(x):
    """Evaluate an nth_order_terms result element for PLAIN NUMERIC samples: the
    finite-difference tree is a nested {'type':'Minus','a':..,'b':..} dict (or a
    bare number at order 0). Pure arithmetic over the tree — no Rust evaluator
    needed for numeric structural coordinates; the aperture dial itself is the
    substrate's order_n_concepts.nth_order_terms."""
    if isinstance(x, dict) and x.get("type") == "Minus":
        return _eval_diff(x["a"]) - _eval_diff(x["b"])
    return x


def aperture_manifold(adj: dict, order_nodes: list, *, max_order: int = 3) -> dict:
    """KEEP ALL APERTURES LIVE. Lay the structural coordinate (degree in traversal
    order) out as an ordered sample list and apply the substrate's
    order_n_concepts.nth_order_terms at every order 0..max_order. Returns
    {order: [per-position finite-difference value]} — the whole manifold, no
    aperture chosen. This is the native aperture dial, not a bespoke descriptor."""
    from domains.order_n_concepts import nth_order_terms
    deg = [len(adj[v]) for v in order_nodes]
    return {o: [_eval_diff(t) for t in nth_order_terms(deg, o)]
            for o in range(max_order + 1)}


def manifold_shape(manifold: dict, *, z: float = 1.0) -> dict:
    """Read the (node x aperture) manifold SHAPE: per order, the set of positions
    that are LOCAL OUTLIERS at that aperture (the SAME sign-free either-pole read as
    outliers_from_bulk, applied ACROSS positions WITHIN each order). An aperture with
    an empty outlier set is FLAT there (no separating structure at that scale)."""
    out = {}
    for o, diffs in manifold.items():
        out[o] = outliers_from_bulk({i: d for i, d in enumerate(diffs)}, z=z)
    return out


def has_cycle(adj: dict) -> bool:
    """A CHEAP global invariant (one boolean per connected component, NOT the
    articulation computation): a connected component with |E| >= |V| contains a
    cycle. This is the CONFIDENCE-GATE input — the felt read's local coordinates are
    KNOWN-BLIND to cycle-interior non-criticality (the 'way around' is
    unbounded-radius), so a present cycle means ABSTAIN. It detects the blind regime;
    it does not solve the problem. Solver-free (a pure edge/vertex count over a DFS
    component walk); passes no SolverSpy."""
    nodes = list(adj)
    seen = set()
    for s in nodes:
        if s in seen:
            continue
        comp, stack = set(), [s]
        seen.add(s); comp.add(s)
        while stack:
            u = stack.pop()
            for w in adj[u]:
                if w not in seen:
                    seen.add(w); comp.add(w); stack.append(w)
        e = sum(len(adj[v]) for v in comp) // 2
        if e >= len(comp):
            return True
    return False


def felt_aperture_read(adj: dict, order_nodes: Optional[list] = None,
                       *, spy: Optional[SolverSpy] = None) -> dict:
    """THE FELT PATH (solver-free): read cut-vertex criticality off the multi-aperture
    manifold, choosing NO single method, with cycle DETECTION selecting the reading. Steps:
      1. Build the aperture manifold (all orders live) over degree-in-order.
      2. DETECT structure: if a cycle is present (cycle_core non-empty) TRIGGER the
         cycle-aware reading (a cyclic structure read the cyclic way — a node purely on a
         ring is not critical; only where a part attaches to the ring is). Otherwise use
         the default acyclic reading (flanked-interior + hub).
      3. If the chosen reading finds nothing AND no aperture separates anything, abstain
         with an honest null. Otherwise COMMIT the chosen reading's prediction.
    NOTE (cycle detection is a SELECTOR, not a veto): the retired has_cycle was a veto that
    abstained on cycles; this DETECTS the cycle and reads it the cyclic way (the steer:
    "the cycle needs to be detected and trigger a different approach"). Blindness is still
    LEARNED — a reading that commits and is caught wrong routes to the rescue search and,
    only if nothing rescues, an anti-shape (verify_then_update). No hand-coded distrust.
    Passes NO spy to any solver; a supplied SolverSpy must remain 0."""
    order_nodes = list(adj) if order_nodes is None else order_nodes
    manifold = aperture_manifold(adj, order_nodes)
    shape = manifold_shape(manifold)
    core = cycle_core(adj)                                # CYCLE DETECTION (the trigger)
    if core:
        # a cycle is present -> read it the cyclic way (different approach)
        predicted = _read_cycle_aware(adj, order_nodes, shape)
        reason = "cycle_detected_cyclic_reading"
        peaked = [o for o in sorted(shape) if shape[o]]
        return {"committed": True, "reason": reason, "predicted": predicted,
                "manifold": manifold, "peaked": peaked, "reading": "cycle_aware",
                "core": core}
    # acyclic: the default flanked-interior + hub reading
    predicted = _read_default(adj, order_nodes, shape)
    peaked = [o for o in sorted(shape) if shape[o]]
    if not peaked:
        return {"committed": False, "reason": "flat_all_apertures",
                "predicted": None, "manifold": manifold, "peaked": peaked,
                "reading": None, "core": core}
    return {"committed": True, "reason": "bounded_witness",
            "predicted": predicted, "manifold": manifold, "peaked": peaked,
            "reading": "default", "core": core}


def f1_score(predicted: set, truth: set) -> float:
    """F1 of a predicted critical set against ground truth (both node-id sets)."""
    if predicted is None:
        return float("nan")
    tp = len(predicted & truth)
    fp = len(predicted - truth)
    fn = len(truth - predicted)
    return (2 * tp / (2 * tp + fp + fn)) if (tp or fp or fn) else 1.0



# --------------------------------------------------------------------------- #
#  THE SIGNED, APERTURE-INDEXED SHAPE FIELD (anti-shapes).
#
#  "An AntiShape is a Shape like any other — it merely has a negative polarity"
#  (user). The substrate already carries polarity natively: seeds/qualia_space.json
#  `dynamical:valence` = "sign of the concept's committed state (-/0/+)". So the
#  solution library (track_j2, positive exemplars) and the anti-shapes (things that
#  fooled the felt read) are ONE field at opposite VALENCE — not two mechanisms.
#
#  "The antishape identity depends on the aperture" (user). A shape IS a reading at
#  an aperture (order_n_concepts order k). A false commit caught at order k mints a
#  NEGATIVE shape AT k; a fresh structure is repelled only when ITS order-k reading
#  matches — a structure that is noise at k=1 but clean at k=2 is correctly NOT
#  repelled. Distrust is aperture-scoped. Identity = (aperture k, order-k signature).
#
#  "Maybe it needs to be a Term op not a static method" (user). The match/net-sign is
#  the DECISION, so it must be the Term (conceptualizer audit: no Python decision).
#  The .so is frozen, so no NEW Rust op — but a shape SIGNATURE is a vector of ints
#  and shape_signature_distance is L1 = Sum(Abs(Minus(...))), every piece an existing
#  Term op. So net_valence is COMPOSED as a graph-resident Sum over held Shape nodes:
#     net_valence(x) = Sum_{sh in Shape, aperture(sh)==aperture(x)}
#                          valence(sh) * [ L1(sig(x), sig(sh)) <= tol ? 1 : 0 ]
#  Python only STAMPS signature attrs (arithmetic I/O) and MINTS Shape nodes
#  (structural I/O) on verify outcomes; the pick is the Term the substrate evaluates.
#
#  FOOL ME ONCE, CAN'T GET FOOLED AGAIN: verify catching a false commit MINTS a
#  valence=-1 shape at the used aperture (symmetric with minting valence=+1 on a
#  confirmed success). The next matching structure carries negative net valence and
#  is repelled from memory — verify budget not spent. RE-EARNABLE: a -1 shape later
#  confirmed-fine drifts toward 0/+ by the same valence update (not a bespoke decay).
# --------------------------------------------------------------------------- #
SHAPE_SIG_WIDTH = 8          # fixed signature width so the L1 Sum term has fixed shape
SHAPE_MATCH_TOL = 2.0        # L1 shape-distance threshold for "same shape at this aperture"


def _eval_num(x):
    if isinstance(x, dict) and x.get("type") == "Minus":
        return _eval_num(x["a"]) - _eval_num(x["b"])
    return x


def aperture_signature(coord: list, k: int, substrate) -> list:
    """The order-k shape SIGNATURE of a structural coordinate: signature of its
    k-th finite difference (the substrate's own order_n_concepts aperture dial fed
    to shape_signature). Normalized to SHAPE_SIG_WIDTH (pad/truncate) so held and
    candidate signatures compare component-wise in a fixed-arity L1 Term."""
    from domains.order_n_concepts import nth_order_terms
    diffs = [float(_eval_num(t)) for t in nth_order_terms(list(coord), k)]
    sig = list(substrate.shape_signature(diffs)) if diffs else []
    return (sig + [0] * SHAPE_SIG_WIDTH)[:SHAPE_SIG_WIDTH]


def structural_coord(adj: dict, order_nodes: Optional[list] = None) -> list:
    """The structural coordinate a graph's shape is read from — degree in traversal
    order (the same coordinate felt_aperture_read uses). Kept separate so any domain
    can supply its own ordered numeric coordinate."""
    order_nodes = list(adj) if order_nodes is None else order_nodes
    return [len(adj[v]) for v in order_nodes]


def mint_shape(substrate, coord: list, k: int, valence: float,
               *, order_nodes: Optional[list] = None, reading: str = "default") -> int:
    """Hold a shape in the field: a `Shape` node carrying (aperture k, order-k
    signature attrs sig_0..sig_{W-1}, valence, reading). valence=+1 = solved/rescued
    (positive pull), -1 = caught false-commit with NO rescuing reading (anti-shape,
    negative pull). `reading` records WHICH structural reading was verified to work for
    this shape ('default' if the default flanked-hub read; a repertoire name if a rescue
    reading was needed) — so a re-encounter can import the correction, feel-then-verify.
    If an identical-aperture shape within tol already exists, UPDATE its valence toward
    the new sign (re-earning) and adopt the new reading when moving positive. Returns the
    Shape node id."""
    sig = aperture_signature(coord, k, substrate)
    for sh in substrate.nodes("Shape"):
        at = substrate.node(sh)["attrs"]
        if int(at.get("aperture", -1)) != k:
            continue
        d = sum(abs(sig[i] - int(at.get("sig_%d" % i, 0))) for i in range(SHAPE_SIG_WIDTH))
        if d <= SHAPE_MATCH_TOL:                       # same shape already held -> re-earn
            cur = float(at.get("valence", 0.0))
            new = max(-1.0, min(1.0, cur + valence))
            substrate.set_attr(sh, "valence", new)
            if valence > 0:                            # a confirming outcome adopts its reading
                substrate.set_attr(sh, "reading", reading)
            return sh
    attrs = {"aperture": float(k), "valence": float(valence), "reading": reading}
    for i in range(SHAPE_SIG_WIDTH):
        attrs["sig_%d" % i] = float(sig[i])
    return substrate.add_node("Shape", attrs)


def stamp_candidate_signature(substrate, axis: int, coord: list, k: int) -> None:
    """Stamp the candidate axis's OWN order-k signature onto csig_0..csig_{W-1} and
    its aperture. Pure arithmetic I/O (a finite difference + an ordinal rank), the
    same category as stamp_axis_cost — no decision. The DECISION (match/net-sign) is
    the net_valence Term the frontier evaluates."""
    sig = aperture_signature(coord, k, substrate)
    substrate.set_attr(axis, "aperture", float(k))
    for i in range(SHAPE_SIG_WIDTH):
        substrate.set_attr(axis, "csig_%d" % i, float(sig[i]))


def net_valence_term() -> dict:
    """COMPOSE the net-valence sub-term (graph data, evaluated by the substrate):
        Sum_{sh in Shape, aperture(sh)==aperture(x)}
            valence(sh) * IfThenElse( Sum_i |csig_i(x) - sig_i(sh)| <= tol, 1, 0 )
    L1 shape-distance + threshold + valence product, all existing Term ops. `x` is
    the outer candidate axis (bound by the enclosing frontier Argmax); `sh` is the
    inner held Shape. Positive shapes pull toward commit, negative (anti-shapes) push
    toward abstain. This is the match-as-Term the design requires."""
    def A(var, key):
        return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}
    l1 = {"type": "Plus", "items": [
        {"type": "Abs", "arg": {"type": "Minus", "a": A("x", "csig_%d" % i),
                                "b": A("sh", "sig_%d" % i)}}
        for i in range(SHAPE_SIG_WIDTH)]}
    match = {"type": "IfThenElse",
             "cond": {"type": "Lte", "a": l1, "b": {"type": "Lit", "value": SHAPE_MATCH_TOL}},
             "then": {"type": "Lit", "value": 1.0}, "other": {"type": "Lit", "value": 0.0}}
    per_shape = {"type": "Times", "items": [A("sh", "valence"), match]}
    return {"type": "Sum",
            "source": {"type": "NodesWhere", "node_type": "Shape",
                       "attr_key": "aperture",
                       "value": A("x", "aperture")},
            "var_name": "sh", "value": per_shape}


def _read_default(adj, order_nodes, shape):
    """The default felt reading: flanked-interior (not a degree outlier) OR high-degree
    hub. The reading felt_aperture_read commits with."""
    pos = {v: i for i, v in enumerate(order_nodes)}
    deg_out = shape.get(0, set())
    pred = set()
    for i, v in enumerate(order_nodes):
        flanked = any(pos[u] < i for u in adj[v]) and any(pos[u] > i for u in adj[v])
        if flanked and i not in deg_out:
            pred.add(v)
        elif i in deg_out and len(adj[v]) > 2:
            pred.add(v)
    return pred


def _read_non_leaf(adj, order_nodes, shape):
    """A structural reading: every non-leaf (degree > 1). Uniform, not answer-fitted —
    it is correct on trees (where every internal node is a cut vertex) and WRONG on
    cycles (no cut vertices), so it is only ever ADOPTED for a shape when verify CONFIRMS
    it on that shape; it is not trusted for free."""
    return {v for v in adj if len(adj[v]) > 1}


def _read_spanned(k):
    """A structural reading family: the nodes spanned by an order-k outlier diff. Reads
    the manifold's own outlier positions at aperture k back onto the nodes they cover."""
    def rd(adj, order_nodes, shape):
        idx_out = shape.get(k, set())
        spanned = set()
        for i in idx_out:
            for j in range(i, min(i + k + 1, len(order_nodes))):
                spanned.add(order_nodes[j])
        return spanned
    return rd


def cycle_core(adj: dict) -> set:
    """CYCLE DETECTION (cheap, structural, solver-free): the 2-core — the nodes that lie
    on some cycle — found by iteratively peeling degree-1 leaves (the acyclic fringe); what
    remains is the cyclic part. Empty set == the structure is acyclic. This is DETECTION
    that TRIGGERS a different reading, NOT a veto/abstain (the retired has_cycle was a
    veto; this is a reading selector — a cycle is not untrustworthy, it needs the cyclic
    reading)."""
    remaining = {v: set(ns) for v, ns in adj.items()}
    changed = True
    while changed:
        changed = False
        for v in list(remaining):
            d = len(remaining[v])
            if d == 1:
                (u,) = tuple(remaining[v])
                remaining[u].discard(v)
                del remaining[v]
                changed = True
            elif d == 0:
                del remaining[v]
                changed = True
    return set(remaining)


def _read_cycle_aware(adj, order_nodes, shape):
    """CYCLE-AWARE reading (the different approach a detected cycle triggers). On the
    2-core (the cyclic part) a node is critical ONLY where a non-core part attaches to it
    (the articulation joining a cycle to the rest); a node purely on the cycle is NOT a cut
    vertex (the ring provides a way around). Off the core (tree part) fall back to the
    non-leaf reading. Uniform + structural; adopted for a shape only when verify confirms
    it (feel-then-verify), so it is never trusted for free on structures it does not fit
    (e.g. bridged multi-cycles)."""
    core = cycle_core(adj)
    pred = set()
    for v in adj:
        if v in core:
            if any(u not in core for u in adj[v]):     # attachment point cycle<->rest
                pred.add(v)
        elif len(adj[v]) > 1:                          # tree part: ordinary non-leaf
            pred.add(v)
    return pred


# The FIXED structural reading repertoire (uniform reads, never answer-fitted). A rescue
# reading is only ADOPTED for a shape once verify CONFIRMS it on that shape — it stays
# feel-then-verify, so a broadly-applicable read like non_leaf cannot be trusted for free
# where it would be wrong (e.g. cycles). `cycle_aware` is TRIGGERED by cycle DETECTION
# (cycle_core non-empty) and reads a cyclic structure the cyclic way rather than distrusting
# it — the steer's "detect the cycle, trigger a different approach".
READING_REPERTOIRE = {
    "default": _read_default,
    "cycle_aware": _read_cycle_aware,
    "non_leaf": _read_non_leaf,
    "spanned_k0": _read_spanned(0),
    "spanned_k1": _read_spanned(1),
    "spanned_k2": _read_spanned(2),
}


def apply_reading(adj, name: str, order_nodes: Optional[list] = None) -> set:
    """Apply a named structural reading from the repertoire to a graph (felt: no solver).
    Used both to re-apply a shape's verified rescuing reading and to search for a rescue."""
    order_nodes = list(adj) if order_nodes is None else order_nodes
    manifold = aperture_manifold(adj, order_nodes)
    shape = manifold_shape(manifold)
    return READING_REPERTOIRE[name](adj, order_nodes, shape)


def search_rescue_reading(adj, truth: set, order_nodes: Optional[list] = None) -> Optional[str]:
    """When the DEFAULT reading was caught wrong: search the repertoire for a reading that
    VERIFY confirms on THIS structure (matches truth). Returns the first non-default
    reading name whose prediction is exactly right, or None if no reading in the
    repertoire rescues it. The rescue is a feel-then-VERIFY candidate — truth here is the
    verify outcome already computed by the caller, so no extra solver call. 'Wrong is
    usually the wrong reading, not an untrustworthy shape': a rescue means the lesson is
    'read this shape with R', an anti-shape is the last resort when NOTHING rescues."""
    order_nodes = list(adj) if order_nodes is None else order_nodes
    for name in READING_REPERTOIRE:
        if name == "default":
            continue
        if f1_score(apply_reading(adj, name, order_nodes), truth) >= 0.999:
            return name
    return None


# --------------------------------------------------------------------------- #
#  REPERTOIRE SELF-EXTENSION: authoring a new reading for a REPEATED no-rescue class.
#
#  The anti-shape mechanism learns WHAT it cannot read yet (a no-rescue class becomes a
#  negative-valence shape). Self-extension closes the loop: learn HOW to read it. When the
#  SAME no-rescue class is hit repeatedly, AUTHOR a new candidate reading and add it to the
#  repertoire — after which that class is RESCUED (verify-confirmed) instead of distrusted.
#
#  NON-CIRCULARITY: the authored reading must be COMPOSED FROM PRIMITIVES ALREADY HELD
#  (cycle_core + degree + adjacency), NOT a bespoke class-specific solver, and it is only
#  ADOPTED for a shape when verify confirms it (via search_rescue_reading). A candidate that
#  is globally imperfect (right on the new class, wrong elsewhere) is HARMLESS: per-shape
#  verify-gated adoption means it only ever WINS where it is actually right; existing
#  readings keep winning where they are right (no regression). This is the SAME recognise-
#  then-compose move the salience terms and the track_j2 library used — the pieces recombine
#  to rescue the class; nothing is planted.
# --------------------------------------------------------------------------- #
def _bridge_edge_endpoints(adj: dict) -> set:
    """Nodes incident to a candidate BRIDGE edge — an edge whose endpoints share NO common
    neighbour (no triangle closes it). Composed from a held primitive (adjacency/degree
    neighbourhood). A cheap structural proxy for 'edge not on a short cycle'; it is
    deliberately imperfect globally (it over-fires on long chordless cycles), which is why
    the reading built on it is only ever ADOPTED where verify confirms it."""
    out = set()
    for u in adj:
        for v in adj[u]:
            if u < v and not (set(adj[u]) & set(adj[v])):
                out.add(u); out.add(v)
    return out


def _read_bridge(adj, order_nodes, shape):
    """An AUTHORED reading, composed from held primitives (cycle_core attachment points +
    the bridge-edge-endpoint proxy): critical nodes are the cycle<->rest attachment points
    UNION the endpoints of candidate bridge edges. Rescues bridged multi-cycle structures
    (barbell) that no prior reading captured. Globally imperfect (wrong on plain cycles),
    so only adopted per-shape under verify — exactly how self-extension stays honest."""
    core = cycle_core(adj)
    pred = {v for v in adj if v in core and any(u not in core for u in adj[v])}
    return pred | _bridge_edge_endpoints(adj)


#: The library of composable candidate readings self-extension can author from. Each is
#: built ONLY from held primitives (cycle_core / degree / adjacency), NOT class-specific.
#: They are NOT in the default repertoire — extend_repertoire adds one only when a repeated
#: no-rescue class is verified to be rescued by it.
_AUTHORABLE_READINGS = {
    "bridge": _read_bridge,
}


def extend_repertoire(adj: dict, truth: set, *, order_nodes: Optional[list] = None) -> Optional[str]:
    """AUTHOR a new reading for a no-rescue class. Search the authorable (composed-from-held-
    primitives) readings for one that VERIFY confirms on this structure; if found, ADD it to
    the live READING_REPERTOIRE and return its name. Thereafter search_rescue_reading will
    find it, so the class flips from distrusted (anti-shape) to rescued. Returns None if no
    authorable reading rescues it (the class stays genuinely no-rescue). Idempotent: a
    reading already in the repertoire is not re-added."""
    order_nodes = list(adj) if order_nodes is None else order_nodes
    for name, fn in _AUTHORABLE_READINGS.items():
        if name in READING_REPERTOIRE:
            continue
        if f1_score(fn(adj, order_nodes, manifold_shape(aperture_manifold(adj, order_nodes))),
                    truth) >= 0.999:
            READING_REPERTOIRE[name] = fn          # ADOPT into the live repertoire
            return name
    return None


def _held_shape_for(substrate, coord: list, k: int) -> Optional[int]:
    """The already-held Shape node matching this coordinate's order-k signature (within
    tol), or None. Used to tell a FIRST no-rescue encounter (mint the anti-shape) from a
    REPEAT (invest in authoring a reading via self-extension)."""
    sig = aperture_signature(coord, k, substrate)
    for sh in substrate.nodes("Shape"):
        at = substrate.node(sh)["attrs"]
        if int(at.get("aperture", -1)) != k:
            continue
        d = sum(abs(sig[i] - int(at.get("sig_%d" % i, 0))) for i in range(SHAPE_SIG_WIDTH))
        if d <= SHAPE_MATCH_TOL:
            return sh
    return None


def verify_then_update(substrate, adj: dict, field_valence: float,
                       *, order_nodes: Optional[list] = None,
                       spy: Optional[SolverSpy] = None) -> dict:
    """THE FOOL-ME-ONCE + WHEN-IT'S-WRONG LOOP. Given the felt read's committed
    prediction for `adj` and the net field valence it saw, decide whether to VERIFY and
    what to MINT:
      · field_valence < 0  -> a held anti-shape already repelled this; ABSTAIN,
        verify NOT spent (can't get fooled again).
      · not committed -> the read abstained (flat all apertures); nothing to verify.
      · committed and field_valence >= 0 -> VERIFY (Tarjan, spy-pinged, the expensive
        step) and branch on the result:
          - RIGHT (F1>=1)          -> MINT a valence=+1 shape, reading='default'.
          - WRONG (F1<1)           -> WHEN IT'S WRONG: before minting an anti-shape, SEARCH
            the reading repertoire for a reading that verify confirms (search_rescue_reading).
              · a rescue exists     -> the lesson is 'read this shape with R', NOT distrust ->
                MINT a valence=+1 shape tagged reading=R (a verified correction, imported on
                re-encounter). No anti-shape.
          · no rescue in the current repertoire -> WHEN IT KEEPS HAPPENING (self-extension):
                on the FIRST hit, mint the valence=-1 anti-shape (distrust; do not invest yet).
                On a REPEAT (the anti-shape is already held for this class), AUTHOR a new reading
                composed from held primitives (extend_repertoire); if it rescues the class, the
                anti-shape flips POSITIVE (reading=the authored reading) — the pipeline learned
                HOW to read it, not just that it couldn't. If even authoring fails, the anti-shape
                stands (genuinely no-rescue).
    The felt read itself stays solver-free; the Tarjan here is the SEPARATE verify step,
    and the rescue search reuses its truth (no extra solver call)."""
    order_nodes = list(adj) if order_nodes is None else order_nodes
    coord = structural_coord(adj, order_nodes)
    felt = felt_aperture_read(adj, order_nodes)          # solver-free (no spy)
    k = 1                                                # the aperture the shape is held at
    if field_valence < 0:
        return {"verified": False, "f1": None, "minted_valence": None, "aperture": k,
                "reading": None, "reason": "repelled_by_held_antishape"}
    if not felt["committed"]:
        return {"verified": False, "f1": None, "minted_valence": None, "aperture": k,
                "reading": None, "reason": "felt_read_abstained"}
    truth = tarjan_cut_vertices(adj, spy=spy)            # VERIFY — the expensive step
    f1 = f1_score(felt["predicted"], truth)
    used_reading = felt.get("reading", "default")        # the reading the felt read used
    if f1 >= 0.999:                                      # confirmed -> solved exemplar
        mint_shape(substrate, coord, k, +1.0, order_nodes=order_nodes, reading=used_reading)
        return {"verified": True, "f1": f1, "minted_valence": 1.0, "aperture": k,
                "reading": used_reading, "reason": "confirmed"}
    # WHEN IT'S WRONG: is it the wrong reading, or a genuinely untrustworthy shape?
    rescue = search_rescue_reading(adj, truth, order_nodes)
    if rescue is not None:                               # wrong READING, not wrong shape
        mint_shape(substrate, coord, k, +1.0, order_nodes=order_nodes, reading=rescue)
        return {"verified": True, "f1": f1, "minted_valence": 1.0, "aperture": k,
                "reading": rescue, "reason": "rescued_by_reading"}
    # NO RESCUE in the current repertoire. Is this a REPEAT of an already-distrusted class?
    prior = _held_shape_for(substrate, coord, k)
    if prior is None or float(substrate.node(prior)["attrs"].get("valence", 0.0)) >= 0.0:
        # first encounter of this no-rescue class -> distrust (do not invest in authoring yet)
        mint_shape(substrate, coord, k, -1.0, order_nodes=order_nodes, reading="default")
        return {"verified": True, "f1": f1, "minted_valence": -1.0, "aperture": k,
                "reading": None, "reason": "no_rescue_minted_antishape"}
    # REPEAT of a held no-rescue class -> SELF-EXTEND: author a reading from held primitives.
    authored = extend_repertoire(adj, truth, order_nodes=order_nodes)
    if authored is not None:                             # learned HOW to read it
        mint_shape(substrate, coord, k, +1.0, order_nodes=order_nodes, reading=authored)
        return {"verified": True, "f1": f1, "minted_valence": 1.0, "aperture": k,
                "reading": authored, "reason": "self_extended_authored_reading"}
    mint_shape(substrate, coord, k, -1.0, order_nodes=order_nodes, reading="default")
    return {"verified": True, "f1": f1, "minted_valence": -1.0, "aperture": k,
            "reading": None, "reason": "no_rescue_even_after_authoring"}
