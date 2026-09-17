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



# --------------------------------------------------------------------------- #
#  CROSS-DOMAIN SELF-EXTENSION: the SAME loop over a NON-graph coordinate.
#
#  The frontier the arc reached: the graph pipeline self-grows, but every authorable
#  primitive is graph-structural. Is the recognise -> compose-from-held-primitives ->
#  verify -> adopt loop DOMAIN-GENERAL, or a graph trick? This is the same machinery
#  instantiated over NUMERIC SEQUENCES (the number-qualia integer axis), proving only the
#  PRIMITIVE VOCABULARY changes across domains, not the loop.
#
#  The coordinate is a sequence's values in index order. The felt read is its "degree" —
#  the order k at which the k-th finite difference is CONSTANT (falling_world's move:
#  constant 2nd difference = an order-2 generator). SAME aperture dial (nth_order_terms) as
#  the graph domain. Feel-then-verify: feel the degree cheaply; verify by exact differencing.
#
#  A geometric/exponential sequence has NO constant finite difference -> the default reading
#  ABSTAINS (the sequence-domain no-rescue class). On a REPEAT, self-extension authors a
#  reading composed from held NUMERIC primitives (log + the same finite-difference dial): a
#  geometric sequence is "degree-1 in log space" (constant ratio = constant log-difference).
#  Per-class + verify-gated, so it rescues geometric without mis-reading polynomials. This is
#  the sequence-domain analogue of `bridge` rescuing the barbell — same loop, numeric primitives.
# --------------------------------------------------------------------------- #
#: SCALED WITNESS MARGIN (falling_world's order-N witness-minimum idea). An n-point
#: sequence's (n-1)th finite difference is trivially 1-2 values that can be equal by
#: COINCIDENCE, so short recurrences/other sequences would spuriously CONFIRM as high-degree
#: polynomials (Pell [0,1,2,5,12,29,70] over-fits to degree 5; Fibonacci over-fits too). A
#: degree-k claim is only CREDIBLE if it is witnessed by a MARGIN of extra points beyond the
#: k+1 a degree-k polynomial minimally needs: k <= len(seq) - _SEQ_WITNESS_MARGIN - 1. margin=2
#: gives pell/fib -> None while genuine polynomials keep their exact degree (n^3 from 6 points:
#: 3 <= 6-2-1 = 3, still credible); margin=3 is too strict (kills legitimate n^3 from 6 points).
_SEQ_WITNESS_MARGIN = 2


def _degree_credible(k: Optional[int], n: int) -> bool:
    """A degree-k claim is credible only if witnessed by _SEQ_WITNESS_MARGIN extra points:
    k <= n - _SEQ_WITNESS_MARGIN - 1. None (no claim) is always 'credible' (nothing to over-fit).
    Pure arithmetic — solver-free."""
    if k is None:
        return True
    return k <= n - _SEQ_WITNESS_MARGIN - 1


def seq_felt_degree(seq: list, *, max_k: int = 5,
                    spy: Optional[SolverSpy] = None) -> Optional[int]:
    """FELT read (cheap, solver-free): the sequence's degree = the smallest order k whose
    k-th finite difference (via the shared order_n_concepts aperture dial) is constant AND is
    credibly witnessed (k <= len(seq) - _SEQ_WITNESS_MARGIN - 1; see _degree_credible). The
    witness margin rejects the over-fit where a short sequence's high-order difference is
    trivially constant by coincidence (Pell/Fibonacci -> None). None if no CREDIBLE constant
    diff <= max_k (the read ABSTAINS: not a low-order polynomial in the index). Passes no spy
    to any solver; a supplied SolverSpy must stay 0."""
    from domains.order_n_concepts import nth_order_terms
    n = len(seq)
    for k in range(0, max_k + 1):
        if not _degree_credible(k, n):
            break                                       # further k only less credible
        diffs = [float(_eval_num(t)) for t in nth_order_terms(list(seq), k)]
        if len(diffs) >= 2 and max(diffs) - min(diffs) < 1e-9:
            return k
    return None


def seq_verify_degree(seq: list, *, spy: Optional[SolverSpy] = None) -> Optional[int]:
    """VERIFY (the expensive/exact step): the true polynomial degree of the sequence in its
    index by successive exact differencing to a constant, subject to the SAME scaled witness
    margin as seq_felt_degree (a degree-k claim is credible only if k <= len(seq) -
    _SEQ_WITNESS_MARGIN - 1). Applying the margin to BOTH keeps felt==verify (track_j4 S1).
    Pings the spy (this is the verify solver; the felt read must not call it)."""
    if spy is not None:
        spy()
    n = len(seq)
    d = list(seq)
    for k in range(len(seq)):
        if not _degree_credible(k, n):
            return None                                 # claim no longer credibly witnessed
        if len(d) >= 2 and max(d) - min(d) < 1e-9:
            return k
        if len(d) < 2:
            return None
        d = [d[i + 1] - d[i] for i in range(len(d) - 1)]
    return None


def seq_read_log_degree(seq: list) -> Optional[int]:
    """An AUTHORABLE sequence reading, composed from held NUMERIC primitives (log + the
    finite-difference dial): the degree of log(seq). A geometric sequence has a constant
    ratio => a constant log-difference => log-degree 1. Rescues the geometric no-rescue
    class the polynomial reading abstains on; returns None where log-space has no constant
    diff (so it does not mis-read polynomials). NOT a bespoke geometric solver — a
    recombination of held ops, adopted only under verify."""
    import math
    if any(v <= 0 for v in seq):
        return None
    logs = [math.log(v) for v in seq]
    d = list(logs)
    for k in range(len(logs)):
        if len(d) >= 2 and max(d) - min(d) < 1e-9:
            return k
        if len(d) < 2:
            return None
        d = [d[i + 1] - d[i] for i in range(len(d) - 1)]
    return None


def _solve_linrec_order(seq: list, order: int):
    """HELD PRIMITIVE (the exact-solve, order-general): fit constant coefficients c_1..c_order
    for x[n] = c_1*x[n-1] + ... + c_order*x[n-order] by an EXACT rational solve over the first
    `order` equations, then VERIFY the recurrence holds for EVERY later term. Returns the tuple
    of coefficients (ints where integral) if it fits, else None. This is the SINGLE linear-solve
    move; order-2 (linrec2) and any higher order are the SAME primitive at a wider window — so a
    higher-order reading is a COMPOSITION/generalization of this held piece, not a new bespoke
    solver. Pure rational arithmetic (no float over-fit, no verify solver): feel = the coefficient
    fit, verify = the exact all-terms check."""
    from fractions import Fraction
    n = len(seq)
    if n < 2 * order:                                   # need `order` eqns + terms to verify
        return None
    x = [Fraction(v) for v in seq]
    # equations from windows starting at order..2*order-1: x[i] = sum c_j x[i-1-j]
    rows = [[x[i - 1 - j] for j in range(order)] for i in range(order, 2 * order)]
    rhs = [x[i] for i in range(order, 2 * order)]
    # exact rational Gaussian elimination on the augmented matrix
    M = [rows[r][:] + [rhs[r]] for r in range(order)]
    for c in range(order):
        piv = next((r for r in range(c, order) if M[r][c] != 0), None)
        if piv is None:
            return None                                 # singular -> no unique fit at this order
        M[c], M[piv] = M[piv], M[c]
        inv = M[c][c]
        M[c] = [v / inv for v in M[c]]
        for r in range(order):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    coeffs = [M[r][order] for r in range(order)]
    for i in range(order, n):                           # VERIFY across ALL terms
        if x[i] != sum(coeffs[j] * x[i - 1 - j] for j in range(order)):
            return None
    def _norm(f):
        return int(f) if f.denominator == 1 else f
    return tuple(_norm(c) for c in coeffs)


def seq_read_linrec2(seq: list) -> Optional[tuple]:
    """An AUTHORABLE sequence reading, COMPOSED FROM HELD PRIMITIVES (a small EXACT rational
    2x2 solve + the finite-difference/check dial). CLAIMS a constant-coefficient ORDER-2
    linear recurrence x[n] = a*x[n-1] + b*x[n-2]: FEEL the (a,b) fit from the first two
    triples via an exact rational solve (fractions.Fraction, no floats -> no over-fit), then
    VERIFY the recurrence holds for EVERY later term. Returns the hashable signature
    ('linrec2', a, b) with a,b as ints where integral (Fibonacci/Lucas -> ('linrec2',1,1);
    Pell -> ('linrec2',2,1)), else None. Requires >=4 terms, a non-degenerate determinant,
    and an exact fit across ALL terms. Solver-free: pure arithmetic (no Tarjan/verify
    solver). This is the feel-then-verify move: the felt claim is the (a,b) fit; the exact
    all-terms check is the verification."""
    from fractions import Fraction
    if len(seq) < 4:
        return None
    coeffs = _solve_linrec_order(seq, 2)                # order-2 IS the held solve at k=2
    if coeffs is None:
        return None
    return ("linrec2", coeffs[0], coeffs[1])


#: The sequence domain's authorable readings (composed from held numeric primitives), NOT
#: in the default read -- seq_extend_repertoire adopts one only when a repeated no-rescue
#: sequence is verified rescued by it. The sequence-domain twin of _AUTHORABLE_READINGS.
#: ORDER MATTERS: log_degree is tried BEFORE linrec2, so a geometric sequence (which is ALSO
#: a linrec2 with a=ratio, b=0) is claimed by log_degree FIRST and keeps its (None,'log_degree')
#: class key; linrec2 then splits the remaining (None,None) no-rescue bucket, giving Fibonacci
#: its OWN (None,'linrec2') key distinct from primes' (None,None). dict preserves insertion
#: order, so iteration honours this priority.
_SEQ_AUTHORABLE = {
    "log_degree": seq_read_log_degree,
    "linrec2": seq_read_linrec2,
}
_SEQ_REPERTOIRE: dict = {}          # authored sequence readings adopted so far


# --------------------------------------------------------------------------- #
#  RUNTIME DISCOVERY: author a reading for a PROVABLY-UNSEEN class, live, from a
#  held primitive at a wider aperture — no reading pre-written for the target.
#
#  The starting sequence repertoire is order-2 (linrec2) + log_degree + poly-degree. A class
#  whose only structure is a HIGHER-ORDER linear recurrence (tribonacci: x=x1+x2+x3; fib^2:
#  (2,2,-1)) is UNCLAIMED by all of them. `discover_recurrence` is the runtime act: when the
#  default read and the current repertoire fail on a REPEATED no-rescue class, SEARCH wider
#  orders k=3,4,... using the SAME held exact-solve primitive (_solve_linrec_order) until one
#  VERIFIES. The winning order becomes a new reading `linrec<k>` composed at runtime and adopted
#  into the live repertoire. This is discovery, not lookup: no `tribonacci`/`fib_squared` reading
#  exists; the composition is the held solve at an order the search found, verified exactly.
#  Solver-free felt path (the search is pure rational arithmetic, no verify solver); the whole
#  event happens in-process, no training, no gradient, no pretrained artifact.
# --------------------------------------------------------------------------- #
_SEQ_MAX_DISCOVER_ORDER = 5         # bounded aperture search (2 already covered by linrec2)


def _make_linrec_reading(order: int):
    """Compose a reading `linrec<order>` from the held order-k solve at a fixed order. Returns
    a fn(seq)->signature|None with the SAME shape as the other authorable readings, namespaced
    so distinct recurrences at the same order stay distinct classes."""
    def rd(seq):
        coeffs = _solve_linrec_order(seq, order)
        return None if coeffs is None else (("linrec%d" % order,) + coeffs)
    rd.__name__ = "seq_read_linrec%d" % order
    return rd


def discover_recurrence(seq: list, *, spy: Optional[SolverSpy] = None) -> Optional[str]:
    """RUNTIME DISCOVERY of a higher-order linear-recurrence reading for a class no starting
    reading claims. Search orders k=3.._SEQ_MAX_DISCOVER_ORDER with the held exact-solve; the
    first k whose recurrence VERIFIES across all terms is authored as a new reading `linrec<k>`,
    added to _SEQ_AUTHORABLE and _SEQ_REPERTOIRE (so the class is claimed thereafter). Returns
    the authored reading name, or None if no bounded order fits. Solver-free (rational solve, no
    verify solver); a supplied SolverSpy stays 0. This is the composed-from-held-primitives,
    verify-gated authoring the runtime-discovery demonstration turns on."""
    for order in range(3, _SEQ_MAX_DISCOVER_ORDER + 1):
        name = "linrec%d" % order
        if name in _SEQ_AUTHORABLE:                     # already discovered at this order
            if _SEQ_AUTHORABLE[name](seq) is not None:
                _SEQ_REPERTOIRE.setdefault(name, _SEQ_AUTHORABLE[name])
                return name
            continue
        fn = _make_linrec_reading(order)
        if fn(seq) is not None:                         # this order's recurrence fits + verifies
            _SEQ_AUTHORABLE[name] = fn                  # AUTHOR it into the repertoire, live
            _SEQ_REPERTOIRE[name] = fn
            return name
    return None


def seq_verify_then_update(seq: list, *, prior_abstained: bool = False,
                           spy: Optional[SolverSpy] = None) -> dict:
    """THE SAME LOOP, sequence domain. Feel the degree; if the felt read ABSTAINS (no
    constant finite difference), this is the no-rescue class:
      · first abstain (prior_abstained False) -> report 'abstained' (distrust; no investment).
      · repeat abstain (prior_abstained True) -> SELF-EXTEND: author a reading from held
        numeric primitives (seq_extend_repertoire); if it verifies, the sequence is rescued
        ('self_extended_authored_reading'); else it stays genuinely no-rescue.
    If the felt read COMMITS a degree, VERIFY it exactly (confirmed / caught-wrong). The felt
    read is solver-free; verify pings the spy."""
    felt_k = seq_felt_degree(seq)                       # solver-free
    if felt_k is not None:
        true_k = seq_verify_degree(seq, spy=spy)        # verify (exact)
        if felt_k == true_k:
            return {"committed": True, "felt_degree": felt_k, "reason": "confirmed",
                    "reading": "poly_degree"}
        return {"committed": True, "felt_degree": felt_k, "reason": "caught_wrong",
                "reading": "poly_degree", "true_degree": true_k}
    # felt read abstained -> the sequence-domain no-rescue class
    if not prior_abstained:
        return {"committed": False, "felt_degree": None, "reason": "abstained",
                "reading": None}
    authored = seq_extend_repertoire(seq, spy=spy)      # REPEAT -> author
    if authored is not None:
        return {"committed": True, "felt_degree": None, "reason": "self_extended_authored_reading",
                "reading": authored}
    return {"committed": False, "felt_degree": None, "reason": "no_rescue_even_after_authoring",
            "reading": None}


def seq_extend_repertoire(seq: list, *, spy: Optional[SolverSpy] = None) -> Optional[str]:
    """AUTHOR a sequence reading for a repeated no-rescue sequence: search the authorable
    numeric-primitive readings (in order: log_degree, then linrec2) for one that produces a
    defined reading AND is verify-consistent (its structure is confirmed exactly), adopt it
    into _SEQ_REPERTOIRE, return its name. The sequence-domain twin of extend_repertoire.
    Verify-gated (spy pinged for the exact check). The verify gate is reading-specific:
      · log_degree -> the log-space claim is confirmed by an exact constant-ratio check
        (a true geometric sequence);
      · linrec2 -> the (a,b) fit is confirmed by the exact all-terms recurrence check that
        seq_read_linrec2 already performs (a non-None return IS the verified claim)."""
    for name, fn in _SEQ_AUTHORABLE.items():
        if name in _SEQ_REPERTOIRE:
            continue
        k = fn(seq)
        if k is None:
            continue
        # verify the authored reading's structural claim exactly (spy pinged for the check).
        if spy is not None:
            spy()
        if name == "log_degree":
            # log-space differencing is exact for a true geometric sequence: constant ratio.
            if len(seq) >= 3 and all(seq[i] > 0 for i in seq_indices(seq)):
                ratios = [seq[i + 1] / seq[i] for i in range(len(seq) - 1)]
                if max(ratios) - min(ratios) < 1e-9:    # constant ratio == geometric confirmed
                    _SEQ_REPERTOIRE[name] = fn
                    return name
        elif name.startswith("linrec"):
            # seq_read_linrec* already verifies the recurrence holds across ALL terms exactly
            # (pure rational arithmetic); a non-None return is the verified structural claim.
            # (Covers linrec2 and any higher-order reading discovered live by discover_recurrence.)
            _SEQ_REPERTOIRE[name] = fn
            return name
    # nothing in the current authorable set claims it -> RUNTIME DISCOVERY: search wider
    # recurrence orders with the held exact-solve primitive and author the winner (linrec3+).
    discovered = discover_recurrence(seq, spy=spy)
    if discovered is not None:
        return discovered
    return None


def seq_indices(seq: list) -> list:
    return list(range(len(seq)))



# =========================================================================== #
#  DOMAIN AS A FIRST-CLASS OBJECT — the shared DECISION SPINE written ONCE.
#
#  The graph pipeline (verify_then_update) and the sequence pipeline
#  (seq_verify_then_update) above share ONE control-flow SPINE: solver-free felt
#  read -> if committed, verify + score -> confirmed / caught-wrong -> search the
#  repertoire for a verify-confirmed rescuing reading -> if none, first-hit distrust
#  vs repeat -> author a reading from held primitives -> verify-gated adopt. This
#  section factors THAT SPINE out ONCE as `domain_verify_then_update(domain, obj, ...)`
#  driven by a lightweight `Domain` descriptor supplying the four domain-specific
#  pieces the spine needs (coordinate extractor, a solver-free default felt read, an
#  exact verify, a library of authorable readings composed from held primitives) plus
#  a scorer and a live repertoire.
#
#  SCOPE (honest — this is the SPINE, not the whole graph loop): the generic loop
#  reproduces the graph loop's DECISION FLOW, not its substrate SIDE-EFFECTS. The
#  graph loop additionally (a) takes a `field_valence` and short-circuits to
#  `repelled_by_held_antishape` when a held anti-shape already repels the candidate,
#  (b) mints signed `Shape` nodes via `mint_shape`, and (c) derives first-hit-vs-repeat
#  from held substrate state via `_held_shape_for`. The generic loop does NONE of
#  those: it takes the first-vs-repeat distinction as an explicit `prior_no_rescue`
#  flag (the caller/memory backend owns that state), and its reason vocabulary is
#  intentionally COARSER — a first no-rescue reports `abstained` rather than the graph
#  loop's `no_rescue_minted_antishape`, because minting is a graph-substrate side
#  effect outside the spine. The sequence loop IS just this spine, so it maps tightly;
#  the graph loop is this spine PLUS the shape-field memory layer.
#
#  This layer is PURE PYTHON PLUMBING over the identical felt-read/verify structure.
#  It relocates NO decision into Python: it wraps/references the existing functions
#  (felt_aperture_read / seq_felt_degree / tarjan_cut_vertices / seq_verify_degree /
#  the existing repertoires) rather than duplicating their logic, and the graph
#  domain's shape-field decision stays the composed graph Term (net_valence_term).
#  The two existing loops and every function the tracks call remain untouched and
#  behavior-identical; this is a unifying SPINE, proven equivalent on the sequence
#  domain and on the graph loop's confirmed path (track_j5 E5), NOT a replacement.
# =========================================================================== #
from dataclasses import dataclass, field as _dc_field
from typing import Hashable


@dataclass
class Domain:
    """A domain is the four pieces the one loop needs, plus a scorer and its live
    adopted-reading repertoire. Deliberately lightweight (a dataclass of callables),
    NOT a framework:

      name         : human label.
      coordinate   : coordinate(obj) -> list[float]   the ordered numeric coordinate
                     (graph: degree-in-order via structural_coord; sequence: the values).
      default_read : default_read(obj) -> (committed: bool, predicted, reading_name, reason)
                     the domain's SOLVER-FREE felt read, wrapped to a uniform 4-tuple.
      verify       : verify(obj, spy) -> truth        the ONE solver touch (spy-pinged).
      score        : score(predicted, truth) -> float in [0,1] (>=0.999 == confirmed).
      readings     : {name: fn}  the domain's default repertoire (feel-side, solver-free).
      authorable   : {name: fn}  composed-from-held-primitive candidates NOT in `readings`.
      repertoire   : {name: fn}  the LIVE adopted readings; starts as a copy of `readings`.

    A reading fn's arity is domain-defined; the loop only calls the domain's own
    `try_reading`/`author` closures, so each domain keeps its native call shape."""
    name: str
    coordinate: Callable[[Any], list]
    default_read: Callable[[Any], tuple]
    verify: Callable[..., Any]
    score: Callable[[Any, Any], float]
    readings: dict = _dc_field(default_factory=dict)
    authorable: dict = _dc_field(default_factory=dict)
    repertoire: dict = _dc_field(default_factory=dict)
    # how the loop applies a repertoire reading and authors a new one, kept as domain
    # closures so the ONE loop never needs to know a reading fn's arity:
    #   try_repertoire(obj, truth, repertoire) -> Optional[str]   (rescue search; solver-free)
    #   author(obj, truth, repertoire, spy)    -> Optional[str]   (verify-gated adopt)
    try_repertoire: Optional[Callable[..., Optional[str]]] = None
    author: Optional[Callable[..., Optional[str]]] = None

    # -- CLASS-FINGERPRINT MEMORY (track_j6, opt-in) ------------------------
    # class_key(obj[, spy])  -> Hashable   the PER-DOMAIN CLASS FINGERPRINT the memory
    #     keys anti-shapes on: what makes a structure a no-rescue class (its felt-read/
    #     verify OUTCOME), NOT the raw coordinate rank. Two structures are the SAME
    #     anti-shape iff the same reading fails the same way on them. May spend verify
    #     (mint happens post-verify anyway); pass a spy to attribute the cost.
    # felt_component(obj)    -> Hashable   the SOLVER-FREE part of the class_key, used
    #     for the phase-A felt-time repel RULE-OUT: it is a NECESSARY condition for a
    #     full-key match (if fresh.felt_component != held.felt_component, the full keys
    #     cannot match, so there is NO repel and NO verify is spent). Must be pure
    #     felt (SolverSpy stays 0).
    class_key: Optional[Callable[..., Hashable]] = None
    felt_component: Optional[Callable[[Any], Hashable]] = None

    def fresh_repertoire(self) -> None:
        """Reset the live repertoire to a copy of the default readings (test hygiene)."""
        self.repertoire = dict(self.readings)


def domain_verify_then_update(domain: "Domain", obj, *, prior_no_rescue: bool = False,
                              memory: Optional["ClassFingerprintMemory"] = None,
                              invest: bool = False,
                              spy: Optional[SolverSpy] = None) -> dict:
    """THE ONE DOMAIN-AGNOSTIC LOOP. Reproduces the control flow both existing loops share:

      1. default (felt) read  -- solver-free.
      2. if committed -> VERIFY + score:
           - score >= 0.999            -> 'confirmed'
           - else (caught wrong)       -> search repertoire for a reading verify confirms:
                 - a rescue exists      -> 'rescued_by_reading'
                 - no rescue            -> fall through to the no-rescue class.
      3. no-rescue class (an abstaining read, or a caught-wrong read nothing rescues):
           - first hit (prior_no_rescue False) -> distrust/abstain -> 'abstained'
           - repeat  (prior_no_rescue True)    -> AUTHOR from domain.authorable
                 (verify-gated adopt into domain.repertoire):
                 - authored             -> 'self_extended_authored_reading'
                 - nothing rescues      -> 'no_rescue_even_after_authoring'

    Returns a dict using the reason vocabulary the existing loops use where it maps
    cleanly (confirmed / rescued_by_reading / abstained / self_extended_authored_reading
    / no_rescue_even_after_authoring), plus the winning `reading` name, `committed`, the
    `score`, and (on a caught-wrong read) `truth`. The felt read is solver-free; `verify`
    is the SEPARATE spy-pinged step; the rescue search reuses that truth (no extra solver
    call), exactly as the hand-written loops do.

    OPT-IN MEMORY (track_j6): when a `memory` (ClassFingerprintMemory) is supplied, this
    delegates to `domain_memory_verify_then_update`, which adds the graph loop's shape-field
    memory layer keyed on the per-domain CLASS FINGERPRINT (Domain.class_key): fool-me-once
    repel (phase-A felt rule-out + phase-B full-key confirm), first-vs-repeat DERIVED from
    held state (no prior_no_rescue flag), and mint keyed by class_key. When NO memory is
    given, the EXACT current flag-based behavior below is unchanged (track_j5 holds)."""
    if memory is not None:                               # OPT-IN class-fingerprint memory
        return domain_memory_verify_then_update(domain, obj, memory, invest=invest, spy=spy)
    committed, predicted, reading_name, felt_reason = domain.default_read(obj)
    if committed:
        truth = domain.verify(obj, spy)                  # VERIFY — the one solver touch
        sc = domain.score(predicted, truth)
        if sc >= 0.999:                                  # confirmed
            return {"committed": True, "reason": "confirmed", "reading": reading_name,
                    "score": sc, "felt_reason": felt_reason}
        # caught wrong: is it the wrong READING, or a genuinely no-rescue class?
        rescue = None
        if domain.try_repertoire is not None:
            rescue = domain.try_repertoire(obj, truth, domain.repertoire)
        if rescue is not None:
            return {"committed": True, "reason": "rescued_by_reading", "reading": rescue,
                    "score": sc, "felt_reason": felt_reason, "truth": truth}
        # no rescue in the repertoire -> the no-rescue class (fall through)
        return _domain_no_rescue(domain, obj, truth=truth, sc=sc,
                                 prior_no_rescue=prior_no_rescue, spy=spy)
    # the felt read abstained -> the domain's no-rescue class (no truth computed yet:
    # authoring computes/uses its own verify-gate)
    return _domain_no_rescue(domain, obj, truth=None, sc=None,
                             prior_no_rescue=prior_no_rescue, spy=spy)


def _domain_no_rescue(domain: "Domain", obj, *, truth, sc, prior_no_rescue: bool,
                      spy: Optional[SolverSpy]) -> dict:
    """The shared no-rescue tail: first-hit distrust vs repeat-authors-from-held-primitives.
    On a repeat, AUTHOR from domain.authorable (verify-gated adopt into domain.repertoire)."""
    if not prior_no_rescue:                              # first encounter -> distrust
        return {"committed": False, "reason": "abstained", "reading": None,
                "score": sc, **({"truth": truth} if truth is not None else {})}
    authored = None
    if domain.author is not None:                        # REPEAT -> self-extend
        authored = domain.author(obj, truth, domain.repertoire, spy)
    if authored is not None:
        return {"committed": True, "reason": "self_extended_authored_reading",
                "reading": authored, "score": sc}
    return {"committed": False, "reason": "no_rescue_even_after_authoring", "reading": None,
            "score": sc}


# =========================================================================== #
#  CLASS-FINGERPRINT MEMORY UNIFICATION (track_j6).
#
#  The reverted memory backend (commit d9cd83fe) keyed anti-shapes on the raw
#  coordinate's ORDINAL-RANK signature (aperture_signature). That is fine for GRAPHS
#  (the rank signature genuinely discriminates graph classes) but WRONG for the numeric
#  domains: every monotone-increasing numeric sequence collapses to the SAME low-order
#  rank signature, so a geometric anti-shape falsely repelled an unrelated readable cubic
#  (both rank to [0,1,2,3,...]); the cubic, which confirms at degree 3, got
#  `repelled_by_held_antishape`. No fixed memory_aperture separates a class from the
#  monotone family — the distrust was baked into the KEY, not merely untested.
#
#  THE FIX: key the memory by a per-domain CLASS FINGERPRINT = what makes a structure a
#  no-rescue class (its felt-read/verify OUTCOME), NOT the raw coordinate rank. Two
#  structures are the SAME anti-shape IFF the SAME reading fails the SAME way on them
#  (Domain.class_key). This makes the false distrust IMPOSSIBLE BY CONSTRUCTION: a cubic
#  and a geometric have different class fingerprints, so a geometric anti-shape simply
#  cannot address the cubic.
#
#  TWO-PHASE, felt-time SOLVER-FREE:
#    · PHASE A (felt-time, solver-free): rule OUT a repel using ONLY the felt component of
#      the class_key (Domain.felt_component). If the fresh obj's felt component matches NO
#      held anti-shape's felt component, there is NO repel and NO verify is spent. The felt
#      component is a NECESSARY condition for a full-key match, so this rule-out is sound.
#    · PHASE B (only if a felt component matched): confirm the FULL class_key, which MAY
#      spend verify — but only for genuine candidates, and minting/repel-confirm is already
#      post-verify in the loop anyway.
#  SolverSpy stays 0 across all FELT reads and the phase-A felt-time rule-out.
#
#  The DECISION for the graph domain stays the composed net_valence_term graph Term; the
#  class-key match here is BOOKKEEPING over which class was seen (a Hashable compare), not
#  a relocated felt/verify decision — the conceptualizer audit protects the felt/verify
#  DECISION (the graph Term / the felt reads), which is untouched.
# =========================================================================== #
class ClassFingerprintMemory:
    """A per-domain memory that keys held anti-shapes (and confirmed classes) on the
    domain's CLASS FINGERPRINT rather than the raw coordinate rank. Backing store is a
    dict class_key -> valence-sign entry, PLUS a felt-component index for the solver-free
    phase-A repel rule-out. Deliberately lightweight (opt-in bookkeeping), NOT a framework:

      · seen(full_key)             -> is this exact class already held (first-vs-repeat)?
      · held_valence(full_key)     -> the stored valence for a class_key (0.0 if unseen).
      · felt_could_repel(fc)       -> PHASE A: does ANY held ANTI-shape share this felt
                                      component? (solver-free necessary condition).
      · mint(full_key, valence, reading) -> record/update a class outcome (post-verify)."""

    def __init__(self):
        self._by_key: dict = {}                          # full class_key -> {valence, reading}
        self._anti_felt: dict = {}                       # felt_component -> count of held anti-shapes

    def seen(self, full_key: Hashable) -> bool:
        return full_key in self._by_key

    def held_valence(self, full_key: Hashable) -> float:
        e = self._by_key.get(full_key)
        return float(e["valence"]) if e else 0.0

    def held_reading(self, full_key: Hashable) -> Optional[str]:
        e = self._by_key.get(full_key)
        return e["reading"] if e else None

    def felt_could_repel(self, felt_component: Hashable) -> bool:
        """PHASE A (solver-free): a fresh obj CAN be repelled only if its felt component
        matches some held ANTI-shape's felt component. If not, rule the repel OUT — no
        verify is spent. Sound because the felt component is a necessary part of the key."""
        return self._anti_felt.get(felt_component, 0) > 0

    def mint(self, full_key: Hashable, felt_component: Hashable, valence: float,
             reading: Optional[str]) -> None:
        """Record/update a class outcome keyed by the FULL class fingerprint (post-verify).
        valence=-1 == anti-shape (also indexed by felt component for phase-A rule-out);
        valence=+1 == confirmed/rescued class. Re-earning: a held anti-shape later confirmed
        drifts toward 0/+ and its felt-component anti-index is released."""
        prev = self._by_key.get(full_key)
        prev_v = float(prev["valence"]) if prev else 0.0
        new_v = max(-1.0, min(1.0, prev_v + valence))
        # maintain the anti-shape felt index (only NEGATIVE entries can repel in phase A)
        was_anti = prev_v < 0.0
        now_anti = new_v < 0.0
        if now_anti and not was_anti:
            self._anti_felt[felt_component] = self._anti_felt.get(felt_component, 0) + 1
        elif was_anti and not now_anti:
            self._anti_felt[felt_component] = max(0, self._anti_felt.get(felt_component, 0) - 1)
        self._by_key[full_key] = {"valence": new_v,
                                  "reading": reading if reading is not None
                                  else (prev.get("reading") if prev else None),
                                  "felt": felt_component}


def _mem_repelled(domain: "Domain", obj, memory: "ClassFingerprintMemory",
                  *, spy: Optional[SolverSpy]) -> bool:
    """FOOL-ME-ONCE, class-key edition. Decide whether a held anti-shape repels `obj`:
      PHASE A (solver-free): if the fresh obj's felt component matches NO held anti-shape's
        felt component -> NOT repelled, and NO verify is spent (the load-bearing rule-out
        that makes the false distrust impossible AND keeps the felt path solver-free).
      PHASE B (only when phase A did not rule it out): form the FULL class_key (may spend
        verify) and repel IFF a held anti-shape carries this exact class_key with negative
        valence. Only genuine candidates reach here."""
    fc = domain.felt_component(obj)                      # solver-free
    if not memory.felt_could_repel(fc):                  # PHASE A rule-out (no verify)
        return False
    full = domain.class_key(obj, spy)                    # PHASE B (verify-gated for residue)
    return memory.held_valence(full) < 0.0


def domain_memory_verify_then_update(domain: "Domain", obj,
                                     memory: "ClassFingerprintMemory",
                                     *, invest: bool = False,
                                     spy: Optional[SolverSpy] = None) -> dict:
    """THE SUBSTRATE/MEMORY-ENABLED loop (opt-in). Same decision spine as
    domain_verify_then_update, but with the class-fingerprint memory layer the graph loop
    had (reintroduced from the reverted attempt, CORRECTED to key on class_key not rank):
      (a) FOOL-ME-ONCE repel: if a held ANTI-shape's class_key matches the fresh obj
          (ruled out cheaply by the felt component first) -> 'repelled_by_held_antishape',
          verify NOT spent. This is the DEFAULT (invest=False): don't spend verify on a
          class already known no-rescue.
      (b) FIRST-vs-REPEAT is DERIVED FROM HELD STATE via class_key match (a held negative
          entry for this class_key == a repeat), replacing the prior_no_rescue flag.
      (c) MINT outcomes keyed by class_key (confirmed/rescued -> +1; first no-rescue -> -1
          anti-shape; repeat that authors a reading -> the anti-shape flips +1).

    `invest` mirrors the graph loop's caller-driven signal (the composed net_valence Term
    decided repel-vs-invest there via field_valence): invest=False repels a held anti-shape
    (fool-me-once, verify saved); invest=True DECLINES the repel to INVEST in a repeat —
    routing a held-anti-shape re-encounter to self-extension (author a reading from held
    primitives). Both keep first-vs-repeat STATE-DERIVED (no prior_no_rescue flag).

    The felt read stays solver-free; the phase-A repel rule-out is solver-free; verify is
    the separate spy-pinged step; mint is post-verify."""
    # (a) FOOL-ME-ONCE — phase-A felt rule-out then phase-B full-key confirm. Skipped when
    # the caller chooses to INVEST in a repeat (self-extension) instead of repelling.
    if not invest and _mem_repelled(domain, obj, memory, spy=spy):
        return {"committed": False, "reason": "repelled_by_held_antishape", "reading": None,
                "score": None}

    committed, predicted, reading_name, felt_reason = domain.default_read(obj)
    if committed:
        truth = domain.verify(obj, spy)                  # VERIFY — the one solver touch
        sc = domain.score(predicted, truth)
        full = domain.class_key(obj, spy)                # class fingerprint (post-verify)
        fc = domain.felt_component(obj)
        if sc >= 0.999:                                  # confirmed
            memory.mint(full, fc, +1.0, reading_name)
            return {"committed": True, "reason": "confirmed", "reading": reading_name,
                    "score": sc, "felt_reason": felt_reason, "class_key": full}
        rescue = None
        if domain.try_repertoire is not None:
            rescue = domain.try_repertoire(obj, truth, domain.repertoire)
        if rescue is not None:
            memory.mint(full, fc, +1.0, rescue)
            return {"committed": True, "reason": "rescued_by_reading", "reading": rescue,
                    "score": sc, "felt_reason": felt_reason, "truth": truth,
                    "class_key": full}
        return _mem_no_rescue(domain, obj, memory, truth=truth, sc=sc,
                              full=full, fc=fc, spy=spy)
    # felt read abstained -> the domain's no-rescue class. Its class_key still needs verify
    # for residue (felt_confirms); the full key/mint is post-verify as always.
    full = domain.class_key(obj, spy)
    fc = domain.felt_component(obj)
    return _mem_no_rescue(domain, obj, memory, truth=None, sc=None,
                          full=full, fc=fc, spy=spy)


def _mem_no_rescue(domain: "Domain", obj, memory: "ClassFingerprintMemory",
                   *, truth, sc, full: Hashable, fc: Hashable,
                   spy: Optional[SolverSpy]) -> dict:
    """No-rescue tail with FIRST-vs-REPEAT DERIVED FROM HELD STATE (no prior_no_rescue flag):
    a held negative-valence entry for this class_key == a repeat. First hit mints the -1
    anti-shape; a repeat authors a reading from held primitives (verify-gated) and, if it
    rescues, flips the class positive."""
    prior_anti = memory.held_valence(full) < 0.0         # derived from held state
    if not prior_anti:                                   # FIRST encounter -> mint anti-shape
        memory.mint(full, fc, -1.0, None)
        return {"committed": False, "reason": "no_rescue_minted_antishape", "reading": None,
                "score": sc, "class_key": full,
                **({"truth": truth} if truth is not None else {})}
    # REPEAT of a held no-rescue class -> self-extend: author from held primitives
    authored = None
    if domain.author is not None:
        authored = domain.author(obj, truth, domain.repertoire, spy)
    if authored is not None:
        memory.mint(full, fc, +1.0, authored)            # anti-shape flips POSITIVE
        return {"committed": True, "reason": "self_extended_authored_reading",
                "reading": authored, "score": sc, "class_key": full}
    return {"committed": False, "reason": "no_rescue_even_after_authoring", "reading": None,
            "score": sc, "class_key": full}


# --------------------------------------------------------------------------- #
#  GRAPH_DOMAIN — the existing graph pipeline registered as a Domain (wrapping the
#  EXISTING functions; no logic duplicated).
# --------------------------------------------------------------------------- #
# -- graph CLASS FINGERPRINT: the EXISTING coordinate rank-signature ---------
# The prior (reverted) memory keyed EVERY domain on this rank signature. That was
# the bug for the NUMERIC domains (all monotone sequences collapse to one rank), but
# for GRAPHS the coordinate rank-signature GENUINELY discriminates classes (barbell
# repels barbell, NOT path/star — validated). So graph KEEPS this key unchanged;
# the unified class-key memory reproduces verify_then_update's aperture_signature@k=1
# behavior byte-for-byte. Solver-free (a finite difference + ordinal rank; no Tarjan).
_GRAPH_SIG_SUB = None


def _graph_sig_substrate():
    """A tiny throwaway substrate used ONLY to compute shape_signature for graph class
    keys (the same op mint_shape/aperture_signature use). Cached so key computation is
    cheap and touches no solver."""
    global _GRAPH_SIG_SUB
    if _GRAPH_SIG_SUB is None:
        _GRAPH_SIG_SUB = _native.Substrate()
    return _GRAPH_SIG_SUB


def graph_class_key(adj, spy: Optional[SolverSpy] = None) -> Hashable:
    """Graph class fingerprint == the EXISTING order-1 coordinate rank-signature (the
    key verify_then_update already holds Shape nodes at). Solver-free: a finite
    difference + ordinal rank, NOT the cut-vertex solver."""
    coord = structural_coord(adj, list(adj))
    return tuple(aperture_signature(coord, 1, _graph_sig_substrate()))


def _graph_default_read(adj) -> tuple:
    """Wrap felt_aperture_read to the uniform 4-tuple. Solver-free (no spy passed)."""
    order = list(adj)
    felt = felt_aperture_read(adj, order)                # solver-free
    return (felt["committed"], felt["predicted"],
            felt.get("reading", "default") if felt["committed"] else None,
            felt["reason"])


def _graph_verify(adj, spy) -> set:
    return tarjan_cut_vertices(adj, spy=spy)             # the one solver touch


def _graph_try_repertoire(adj, truth, repertoire) -> Optional[str]:
    """Rescue search over the LIVE graph repertoire (solver-free; reuses `truth`)."""
    order = list(adj)
    for name in repertoire:
        if name == "default":
            continue
        if f1_score(READING_REPERTOIRE[name](adj, order,
                    manifold_shape(aperture_manifold(adj, order))), truth) >= 0.999:
            return name
    return None


def _graph_author(adj, truth, repertoire, spy) -> Optional[str]:
    """Author a reading from _AUTHORABLE_READINGS (verify-gated by the already-computed
    `truth`), adopting it into BOTH the live domain repertoire and READING_REPERTOIRE so
    the existing graph machinery sees it too. No extra solver call (reuses truth)."""
    order = list(adj)
    for name, fn in _AUTHORABLE_READINGS.items():
        if name in repertoire:
            continue
        if f1_score(fn(adj, order, manifold_shape(aperture_manifold(adj, order))),
                    truth) >= 0.999:
            repertoire[name] = fn
            READING_REPERTOIRE[name] = fn                # keep the existing repertoire in sync
            return name
    return None


GRAPH_DOMAIN = Domain(
    name="graph",
    coordinate=lambda adj: structural_coord(adj, list(adj)),
    default_read=_graph_default_read,
    verify=_graph_verify,
    score=f1_score,
    readings=dict(READING_REPERTOIRE),
    authorable=dict(_AUTHORABLE_READINGS),
    repertoire=dict(READING_REPERTOIRE),
    try_repertoire=_graph_try_repertoire,
    author=_graph_author,
    class_key=graph_class_key,
    felt_component=lambda adj: graph_class_key(adj),   # graph key is fully solver-free
)


# --------------------------------------------------------------------------- #
#  SEQUENCE_DOMAIN — the existing sequence pipeline registered as a Domain.
# --------------------------------------------------------------------------- #
def _seq_default_read(seq) -> tuple:
    """Wrap seq_felt_degree to the uniform 4-tuple. Solver-free. A committed read carries
    the felt degree as its `predicted`; the reading label matches the existing loop
    ('poly_degree')."""
    felt_k = seq_felt_degree(seq)                        # solver-free
    if felt_k is not None:
        return (True, felt_k, "poly_degree", "bounded_witness")
    return (False, None, None, "abstained")


def seq_authorable_claim(seq) -> Optional[Hashable]:
    """The FULL SIGNATURE of the _SEQ_AUTHORABLE reading that CLAIMS this sequence (else None)
    — namespaced by reading name so distinct claims stay distinct. A reading fn returns its own
    signature (log_degree -> an int degree; linrec2 -> ('linrec2', a, b)); we namespace it as
    (name, signature) so that DIFFERENT recurrences do NOT collapse: Fibonacci -> ('linrec2',
    ('linrec2',1,1)) and Pell -> ('linrec2', ('linrec2',2,1)) are DISTINCT classes (they are
    distinct recurrences; the task requires it), while log_degree geometrics collapse only by
    their shared log-degree. Solver-free: both readings are pure arithmetic (log/finite-diff for
    log_degree; an exact rational solve for linrec2), no verify solver. This is the non-felt
    half of the sequence class fingerprint."""
    for name, fn in _SEQ_AUTHORABLE.items():
        sig = fn(seq)
        if sig is not None:
            return (name, sig)
    return None


def seq_class_key(seq, spy: Optional[SolverSpy] = None) -> Hashable:
    """SEQUENCE class fingerprint = (seq_felt_degree(seq), full-authorable-claim-that-claims-it).
    Two sequences are the SAME anti-shape iff the SAME reading claims them WITH THE SAME
    SIGNATURE: geometric 2^n and 4^n -> both (None, ('log_degree', 1)) MATCH; geometric vs cubic
    -> (None, ('log_degree',1)) vs (3, None) DIFFER (cubic NOT repelled); Fibonacci vs Pell ->
    (None, ('linrec2', ('linrec2',1,1))) vs (None, ('linrec2', ('linrec2',2,1))) DIFFER (distinct
    recurrences get distinct anti-shapes — the key carries the (a,b), not just the reading name);
    Fibonacci vs primes -> vs (None, None) DIFFER. Fully solver-free (both components are
    felt/arithmetic); a supplied SolverSpy stays 0."""
    return (seq_felt_degree(seq), seq_authorable_claim(seq))


def _seq_verify(seq, spy):
    return seq_verify_degree(seq, spy=spy)               # the one solver touch


def _seq_score(predicted, truth) -> float:
    return 1.0 if predicted == truth else 0.0


def _seq_author(seq, truth, repertoire, spy) -> Optional[str]:
    """Author a sequence reading from _SEQ_AUTHORABLE (verify-gated), adopting into BOTH the
    live domain repertoire and the existing module-level _SEQ_REPERTOIRE."""
    name = seq_extend_repertoire(seq, spy=spy)           # reuses the existing verify-gate
    if name is not None:
        repertoire[name] = _SEQ_AUTHORABLE[name]
    return name


SEQUENCE_DOMAIN = Domain(
    name="sequence",
    coordinate=lambda seq: list(seq),
    default_read=_seq_default_read,
    verify=_seq_verify,
    score=_seq_score,
    readings={},                                         # no feel-side repertoire beyond the read
    authorable=dict(_SEQ_AUTHORABLE),
    repertoire={},
    try_repertoire=None,                                 # sequence caught-wrong has no rescue search
    author=_seq_author,
    class_key=seq_class_key,
    felt_component=lambda seq: seq_felt_degree(seq),     # solver-free felt-time rule-out
)


# --------------------------------------------------------------------------- #
#  THE THIRD DOMAIN — RESIDUE-RUN PARTITION over integer lists. The real test that a
#  genuinely NEW domain plugs into domain_verify_then_update with NO new loop code:
#  only a Domain registration + domain-native primitives.
#
#  TASK: partition a list of integers into contiguous runs that share a residue class,
#  and report the BOUNDARY indices (i where element i starts a new run). The felt read is
#  the cheap naive guess "runs share parity (mod 2)"; the exact ground truth here groups by
#  residue mod 3. A list whose mod-2 boundaries equal its mod-3 boundaries is confirmed for
#  free; a list where they differ is the no-rescue class. On a REPEAT the loop AUTHORS a
#  reading COMPOSED FROM HELD PRIMITIVES (the same run-boundary detector + the integer
#  modulus op, searched over moduli m=3,4,5..) which is globally "wrong" as a default guess
#  but right on the class, adopted only under verify. This is HONEST feel-then-verify:
#    · the felt read (_res_boundaries at m=2) is cheap and SOLVER-FREE (no spy);
#    · verify (mod-3 boundaries) is the SEPARATE exact step (spy-pinged);
#    · the authorable reading is a RECOMPOSITION of held primitives (modulus + run-boundary),
#      not a bespoke solver, and is adopted only when verify confirms it — exactly the
#      `bridge` (graph) / `log_degree` (sequence) move in a new domain.
# --------------------------------------------------------------------------- #
_RES_TRUE_MOD = 3           # the ground-truth grouping modulus (only verify may use it)
_RES_FELT_MOD = 2           # the naive felt guess (parity runs)


def _res_boundaries(seq: list, m: int) -> set:
    """Boundary indices of the contiguous runs of `seq` under residue class mod m: index i
    (i>=1) is a boundary iff seq[i] % m != seq[i-1] % m. A held primitive (integer modulus +
    consecutive comparison); the same op the felt read, verify, and authored readings all
    reuse at different moduli. Solver-free."""
    return {i for i in range(1, len(seq)) if (seq[i] % m) != (seq[i - 1] % m)}


def res_felt_read(seq: list, *, spy: Optional[SolverSpy] = None) -> dict:
    """FELT read (cheap, solver-free): guess the partition boundaries are the PARITY-run
    boundaries (mod 2). Commits when the list has at least one parity change (a bounded
    structural witness); abstains on a constant-parity list (nothing to separate). Passes no
    spy to any solver; a supplied SolverSpy must stay 0."""
    pred = _res_boundaries(seq, _RES_FELT_MOD)
    if pred:
        return {"committed": True, "predicted": pred, "reading": "parity_runs",
                "reason": "bounded_witness"}
    return {"committed": False, "predicted": None, "reading": None,
            "reason": "flat_all_parity"}


def res_verify(seq: list, *, spy: Optional[SolverSpy] = None) -> set:
    """VERIFY (the exact/expensive step): the TRUE run boundaries group by residue mod 3.
    Pings the spy (this is the verify solver; the felt read must not call it)."""
    if spy is not None:
        spy()
    return _res_boundaries(seq, _RES_TRUE_MOD)


def res_read_mod(m: int):
    """FACTORY for an authorable residue-run reading at modulus m, composed from the held
    run-boundary primitive. res_read_mod(3) reads boundaries by mod 3, etc."""
    def rd(seq: list) -> set:
        return _res_boundaries(seq, m)
    return rd


#: The residue domain's authorable readings (composed from held primitives: modulus +
#: run-boundary), NOT in the default read. Searched over candidate moduli; adopted only when
#: verify confirms one on a repeated no-rescue list. The third-domain twin of
#: _AUTHORABLE_READINGS / _SEQ_AUTHORABLE.
_RES_AUTHORABLE = {
    "mod3_runs": res_read_mod(3),
    "mod4_runs": res_read_mod(4),
    "mod5_runs": res_read_mod(5),
}
_RES_REPERTOIRE: dict = {}          # authored residue readings adopted so far


def _res_default_read(seq) -> tuple:
    felt = res_felt_read(seq)                            # solver-free
    return (felt["committed"], felt["predicted"], felt["reading"], felt["reason"])


def res_felt_component(seq) -> Hashable:
    """The SOLVER-FREE felt component of the residue class fingerprint: the felt (parity,
    mod 2) run-boundary set, as a frozenset. Pure arithmetic (integer modulus + consecutive
    comparison), NO verify solver. Used for the phase-A repel RULE-OUT: it is a NECESSARY
    condition for the full key to match, so if a fresh list's felt boundaries differ from a
    held anti-shape's, there is NO repel and NO verify is spent. no-rescue [1,2,4,7]->{1,3}
    vs monotone-confirmable [1,2,3,4]->{1,2,3} DIFFER (the confirmable list is NOT repelled
    without ever calling verify)."""
    return frozenset(res_felt_read(seq)["predicted"] or set())


def res_authorable_rescue(seq, truth) -> Optional[str]:
    """The NAME of the _RES_AUTHORABLE reading that RESCUES this list (its fn(seq) equals the
    verify truth), else None. The non-felt half of the residue class fingerprint."""
    for name, fn in _RES_AUTHORABLE.items():
        if _res_score(fn(seq), truth) >= 0.999:
            return name
    return None


def res_class_key(seq, spy: Optional[SolverSpy] = None) -> Hashable:
    """RESIDUE class fingerprint = (felt_confirms:bool, name-of-authorable-that-rescues).
    felt_confirms == does the felt (parity) read equal the verify (mod-3) truth. This SPENDS
    a verify (spy pinged) — that is fine: the full key is only ever formed at MINT, which is
    post-verify anyway; the cheap felt_component above handles the felt-time rule-out. Two
    lists are the SAME anti-shape iff the same reading fails the same way: no-rescue
    [1,2,4,7] -> (False,'mod3_runs') vs monotone-confirmable [1,2,3,4] -> (True,'mod3_runs')
    DIFFER (no false distrust)."""
    truth = res_verify(seq, spy=spy)                     # verify (exact) — mint is post-verify
    felt_confirms = (res_felt_read(seq)["predicted"] == truth)
    return (felt_confirms, res_authorable_rescue(seq, truth))


def _res_score(predicted, truth) -> float:
    return 1.0 if predicted == truth else 0.0


def _res_try_repertoire(seq, truth, repertoire) -> Optional[str]:
    """Rescue search over the LIVE residue repertoire (solver-free; reuses `truth`)."""
    for name, fn in repertoire.items():
        if name == "parity_runs":
            continue
        if _res_score(fn(seq), truth) >= 0.999:
            return name
    return None


def _res_author(seq, truth, repertoire, spy) -> Optional[str]:
    """Author a residue reading from _RES_AUTHORABLE (verify-gated by the already-computed
    `truth`), adopting into BOTH the live domain repertoire and module-level _RES_REPERTOIRE.
    No extra solver call (reuses truth)."""
    if truth is None:
        return None
    for name, fn in _RES_AUTHORABLE.items():
        if name in repertoire:
            continue
        if _res_score(fn(seq), truth) >= 0.999:          # verify-gated: matches truth exactly
            repertoire[name] = fn
            _RES_REPERTOIRE[name] = fn
            return name
    return None


RESIDUE_DOMAIN = Domain(
    name="residue",
    coordinate=lambda seq: list(seq),
    default_read=_res_default_read,
    verify=lambda seq, spy: res_verify(seq, spy=spy),
    score=_res_score,
    readings={"parity_runs": lambda seq: _res_boundaries(seq, _RES_FELT_MOD)},
    authorable=dict(_RES_AUTHORABLE),
    repertoire={"parity_runs": lambda seq: _res_boundaries(seq, _RES_FELT_MOD)},
    try_repertoire=_res_try_repertoire,
    author=_res_author,
    class_key=res_class_key,
    felt_component=res_felt_component,                   # solver-free felt-time rule-out
)
