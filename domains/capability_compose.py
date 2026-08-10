"""Autonomous capability-scope extension — the reason tower grows ITSELF.

The reason tower (``domains/reason.py``) ships a fixed ``CAPABILITIES`` registry:
gcd / lcm / prime / factorial / nth_fibonacci / divisor_count / determinant / …
Some are already graph-resident (the determinant / rank run as Term-trees on the
engine). But the registry is FINITE — it has no closed-form SUMMATION capability.

This module is the agent extending its OWN computable frontier, by COMPOSITION,
with zero hand-authored math:

  1. The committed GENERATOR (``generator.synthesize`` under the order-n collapse
     ``generator_order_n.OrderNCollapse``) SYNTHESIZES each new capability as a
     Term-tree FROM I/O EXAMPLES ONLY (n -> sum). The generator is NOT given the
     closed form; the order-n finite difference (the agent's own operator) reads
     each candidate's dynamics and surfaces the structural one. MDL/compression
     is the selector. No weights, no gradient descent, no LLM, no Rust.

  2. Each synthesized Term-tree is REGISTERED as a GRAPH-RESIDENT capability: a
     ``Capability`` node carrying the composed Term-tree as graph data. Dispatch
     EVALUATES that stored tree via ``substrate.evaluate`` — the capability IS
     the composed structure, not a Python lambda. This mirrors how det / rank are
     graph-resident computations the tower routes to.

  3. The tower's ``CAPABILITIES`` dispatch dict is extended (additively) with a
     thin router per new concept that evaluates the stored Term-tree on the bound
     argument. ``solve`` / ``answer_within`` then route a bound query for the new
     concept exactly as they route an existing one.

COMPOSITION ON ITS OWN CAPABILITIES. ``sum_first_n`` is synthesized DIRECTLY
(degree-2, the generator's proven reach: ``(n + n*n)/2`` = n(n+1)/2). The
higher-degree summations are then composed ON TOP of that freshly-discovered
capability — the generator searches over ``{n, t}`` where ``t`` is the value of
the just-built ``sum_first_n``. ``sum_first_n_cubes`` falls out as ``t * t``
(Nicomachus: the sum of the first n cubes is the square of the n-th triangular
number); ``sum_first_n_squares`` as ``(t + n*(t+t))/3`` = T(n)*(2n+1)/3. The
derived leaf ``t`` is then INLINED (its Term-tree substituted in) so the
registered capability is a single self-contained Term-tree over ``{n}``. This is
the tower growing by accretion: new capabilities built from the capabilities it
just composed.

HONEST SCOPE. The generator composes POLYNOMIAL / algebraic structure (the
order-n collapse is a finite-difference selector — it cracks separable /
low-degree polynomial targets). So this extends the COMPUTABLE / ALGEBRAIC
frontier by composition. It does NOT reach research-math HLE (bordism /
cohomology / open conjectures): those are KNOWLEDGE / PROOF problems, answered by
the REFERENCE route (concept coverage), not by composing a Term-tree. This module
is the autonomous-growth MECHANISM, not an HLE score.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from substrate_rs import Substrate
from domains.generator import synthesize
from domains.generator_order_n import OrderNCollapse, GRID_LO, GRID_SPAN


# ---------------------------------------------------------------------------
# A raw-dict Term wrapper. The synthesized capability lives as a Term-tree DICT
# (graph data). This wraps it so the substrate's native evaluator runs it — the
# same `_json`-carrying shape order_n_concepts uses to evaluate a composed
# predicate. No Python arithmetic: the value comes out of substrate.evaluate.
# ---------------------------------------------------------------------------

class DictTerm:
    """A Term-tree held as graph data; evaluated on the native engine."""
    __slots__ = ("_json",)

    def __init__(self, d: dict):
        self._json = d

    def to_dict(self) -> dict:
        return self._json

    def evaluate(self, env: dict, substrate):
        return substrate.evaluate(self, env)


def _subst(d, var: str, repl: dict):
    """Substitute every Var(`var`) leaf in the Term-tree dict `d` with the
    Term-tree dict `repl` — inlining a composed sub-capability so the result is a
    single self-contained tree (e.g. inline sum_first_n's tree for the `t` leaf
    in the squares/cubes composition)."""
    if not isinstance(d, dict):
        return d
    if d.get("type") == "Var" and d.get("name") == var:
        return dict(repl)
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = _subst(v, var, repl)
        elif isinstance(v, list):
            out[k] = [_subst(x, var, repl) if isinstance(x, dict) else x
                      for x in v]
        else:
            out[k] = v
    return out


# ---------------------------------------------------------------------------
# Composition grid for the order-n collapse.
#
# A DERIVED leaf (e.g. t = sum_first_n(n)) is a FUNCTION of the base variable n,
# not an independent axis. The default OrderNCollapse grid sweeps every variable
# independently — which would hold n fixed while sweeping t, making the target
# constant along the t-axis (zero profile) and wrongly demoting t. The fix: a
# single-axis grid that sweeps ONLY n and computes the derived leaves
# functionally at each grid point. Faithful: a derived capability tracks its base.
# ---------------------------------------------------------------------------

def _composition_grid(col: OrderNCollapse, base: str, derived: dict):
    envs = []
    for k in range(GRID_SPAN):
        x = GRID_LO + k
        e = {base: float(x)}
        for name, fn in derived.items():
            e[name] = float(fn(x))
        envs.append(e)
    col.grid = [(base, envs)]
    return col


# ---------------------------------------------------------------------------
# The synthesis recipes. Each is a SPEC the generator cracks from I/O ONLY — the
# closed form is never handed to it. `order` = the order-n collapse difference
# order; `derived` names sub-capabilities to expose as building-block leaves
# (and to inline afterward). `true_fn` builds the I/O examples and the held-out
# generalization check — it is the WORLD's reference, read only to make examples
# and to verify; the SELECTOR sees only profiles.
# ---------------------------------------------------------------------------

def _sum_first_n(n: int) -> int:
    return n * (n + 1) // 2


def _sum_first_n_squares(n: int) -> int:
    return n * (n + 1) * (2 * n + 1) // 6


def _sum_first_n_cubes(n: int) -> int:
    return (n * (n + 1) // 2) ** 2


RECIPES = [
    # concept, true_fn, derived(name->fn), order, greedy, K, ops, consts, max_size
    {
        "concept": "sum_first_n",
        "true_fn": _sum_first_n,
        "derived": {},
        "order": 2, "greedy": True, "K": 14,
        "ops": None, "consts": (0, 1, 2, -1), "max_size": 9,
    },
    {
        "concept": "sum_first_n_squares",
        "true_fn": _sum_first_n_squares,
        "derived": {"t": "sum_first_n"},
        "order": 2, "greedy": False, "K": 40,
        "ops": ("Plus", "Times", "Minus", "Div"), "consts": (1, 2, 3),
        "max_size": 9,
    },
    {
        "concept": "sum_first_n_cubes",
        "true_fn": _sum_first_n_cubes,
        "derived": {"t": "sum_first_n"},
        "order": 4, "greedy": True, "K": 14,
        "ops": None, "consts": (0, 1, 2, -1), "max_size": 7,
    },
]

TRAIN_NS = (1, 2, 3, 4, 5, 6)
HELDOUT_NS = (10, 20, 50, 100)


def synthesize_capability(substrate, recipe: dict,
                          discovered: dict) -> dict:
    """Synthesize ONE capability as a Term-tree from I/O examples via the
    committed generator + order-n collapse. `discovered` maps already-built
    concept -> its self-contained Term-tree dict, used both as building-block
    leaves (so the generator can compose on prior capabilities) and to INLINE
    the derived leaves afterward. Returns a record with the (inlined,
    self-contained-over-{n}) Term-tree dict and a generalization check."""
    concept = recipe["concept"]
    fn = recipe["true_fn"]
    derived = recipe["derived"]

    # derived leaf -> python evaluator (for the grid) and its inlinable tree.
    leaf_fns = {leaf: _make_leaf_fn(substrate, discovered[src])
                for leaf, src in derived.items()}

    # SPEC: examples carry the base var n and the derived leaf values.
    examples = []
    for x in TRAIN_NS:
        env = {"n": float(x)}
        for leaf in derived:
            env[leaf] = float(leaf_fns[leaf](x))
        examples.append((env, fn(x)))

    col = OrderNCollapse(substrate, ["n"], order=recipe["order"],
                         greedy=recipe["greedy"])
    if derived:
        _composition_grid(col, "n", {leaf: leaf_fns[leaf] for leaf in derived})
    col.set_target_fn(_target_callable(fn))

    kw = dict(max_size=recipe["max_size"], timeout_s=90.0,
              guide_select=col, guide_beam=recipe["K"],
              consts=recipe["consts"])
    if recipe["ops"] is not None:
        kw["ops"] = recipe["ops"]
    result = synthesize(substrate, examples, **kw)

    rec = {"concept": concept, "fits": result["fits"],
           "term_str": result.get("term_str"),
           "explored": result["explored"], "size": result.get("size"),
           "halt": result["halt_reason"]}
    if not result["fits"]:
        rec["tree"] = None
        rec["generalizes"] = None
        return rec

    # INLINE every derived leaf -> a single self-contained Term-tree over {n}.
    tree = result["dict"]
    for leaf, src in derived.items():
        tree = _subst(tree, leaf, discovered[src])
    rec["tree"] = tree

    # GENERALIZATION check on held-out n, evaluating the inlined graph term.
    term = DictTerm(tree)
    ok = True
    for x in HELDOUT_NS:
        got = term.evaluate({"n": float(x)}, substrate)
        if abs(float(got) - float(fn(x))) > 1e-9:
            ok = False
            break
    rec["generalizes"] = ok
    return rec


def _make_leaf_fn(substrate, tree: dict) -> Callable[[int], float]:
    """Wrap a discovered capability's Term-tree as a python(n)->value callable,
    used only to populate the synthesis grid / examples for a composition. The
    VALUE still comes from substrate.evaluate — no Python math reimplements it."""
    term = DictTerm(tree)

    def f(n):
        return float(term.evaluate({"n": float(n)}, substrate))

    return f


def _target_callable(fn):
    """OrderNCollapse.set_target_fn calls target_fn(**env); env carries n (+ any
    derived leaves). Accept and ignore the extras, return fn(n)."""
    def g(**env):
        return float(fn(int(round(env["n"]))))
    return g


def compose_summation_capabilities(substrate) -> dict:
    """Synthesize + INLINE all summation capabilities, in dependency order
    (sum_first_n first; squares/cubes compose on it). Returns
    {concept: record}. Each record's `tree` is the graph-resident capability:
    a self-contained Term-tree over {n}, evaluated natively."""
    discovered: dict = {}
    out: dict = {}
    for recipe in RECIPES:
        rec = synthesize_capability(substrate, recipe, discovered)
        out[recipe["concept"]] = rec
        if rec["fits"]:
            discovered[recipe["concept"]] = rec["tree"]
    return out


# ---------------------------------------------------------------------------
# GRAPH-RESIDENT registration + dispatch.
#
# A composed capability becomes a `Capability` node carrying the Term-tree as
# graph data. Dispatch evaluates that stored tree via substrate.evaluate on the
# bound argument n. The tower's CAPABILITIES dict gets a thin router per concept
# — the capability IS the stored Term-tree, not a Python lambda.
# ---------------------------------------------------------------------------

def register_capability_node(substrate, concept: str, tree: dict) -> int:
    """Store the composed capability as a graph-resident `Capability` node: its
    Term-tree as graph data, the arg role it expects, who composed it. Returns
    the node id. Re-registration updates the existing node."""
    for c in substrate.nodes("Capability"):
        if substrate.node(c)["attrs"].get("concept") == concept:
            return c
    return substrate.add_node("Capability", {
        "concept": concept,
        "term": tree,
        "arg_role": "of",
        "kind": "summation_closed_form",
        "composed_by": "generator_order_n_collapse",
        "var": "n",
    })


def dispatcher_for(substrate, tree: dict):
    """A thin router: dispatch a bound query {of: n} to the stored Term-tree,
    evaluated on the native engine. Returns an int when the result is integral
    (a closed-form summation is an integer)."""
    term = DictTerm(tree)

    def run(a: dict):
        n = int(a["of"])
        v = term.evaluate({"n": float(n)}, substrate)
        fv = float(v)
        return int(round(fv)) if abs(fv - round(fv)) < 1e-9 else fv

    return run


def install_into_capabilities(substrate, capabilities: dict,
                              records: dict) -> dict:
    """Additively register each fitted, generalizing capability into a
    CAPABILITIES-shaped dispatch dict (a COPY by default — the caller passes
    the dict it wants extended). Each new concept maps to a router that
    evaluates the graph-resident Term-tree. Returns {concept: node_id} for the
    capabilities that were installed."""
    installed: dict = {}
    for concept, rec in records.items():
        if not (rec["fits"] and rec["generalizes"]):
            continue
        node_id = register_capability_node(substrate, concept, rec["tree"])
        capabilities[concept] = dispatcher_for(substrate, rec["tree"])
        installed[concept] = node_id
    return installed


# ---------------------------------------------------------------------------
# PERSIST + LOAD — the agent's composition SAVED as data.
#
# The generator's search is expensive; the COMPOSED, INLINED Term-trees are the
# durable artifact. Persist them once (the agent's composition, as graph data on
# disk) so boot LOADS them rather than re-deriving — and so the trees commit with
# the repo (`data/` is gitignored, so they live under `seeds/`). The capability
# is STILL the generator-composed Term-tree; persistence only caches it.
# ---------------------------------------------------------------------------

# seeds/ commits (data/ is gitignored). The composed trees go here as a small
# JSON the install path reads back.
COMPOSED_PATH = (Path(__file__).resolve().parent.parent
                 / "seeds" / "composed_capabilities.json")


def persist_composed_capabilities(substrate=None,
                                  path: Path = COMPOSED_PATH) -> dict:
    """COMPOSE the summation capabilities (the generator + order-n collapse) and
    WRITE the fitted, generalizing, INLINED Term-trees to ``path`` as JSON. The
    generator needs the high-level ``substrate_rs.Substrate``; one is created if
    not supplied. Returns the {concept: tree} that was written. Run once (or to
    refresh) — the live install loads the persisted trees, it does not recompute.
    """
    if substrate is None:
        substrate = Substrate()
    records = compose_summation_capabilities(substrate)
    out = {
        "_meta": {
            "composed_by": "generator_order_n_collapse",
            "var": "n", "arg_role": "of",
            "heldout_ns": list(HELDOUT_NS),
        },
        "capabilities": {},
    }
    trees: dict = {}
    for concept, rec in records.items():
        if not (rec["fits"] and rec["generalizes"]):
            continue
        out["capabilities"][concept] = {
            "concept": concept, "tree": rec["tree"],
            "term_str": rec.get("term_str"), "size": rec.get("size"),
        }
        trees[concept] = rec["tree"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))
    return trees


def load_composed_capabilities(path: Path = COMPOSED_PATH) -> dict:
    """Load the persisted generator-composed Term-trees as {concept: term_dict}.
    Each term_dict is the self-contained-over-{n}, inlined tree the generator
    composed (NOT hand-authored math). Returns {} if the file is absent."""
    try:
        data = json.loads(Path(path).read_text())
    except Exception:
        return {}
    return {c: e["tree"] for c, e in data.get("capabilities", {}).items()}


def _native_dispatcher(substrate, tree: dict):
    """A thin router that evaluates the stored Term-tree on the engine for a
    bound query {of: n}. Works on EITHER substrate flavour: the native
    ``_native.Substrate`` takes the term DICT directly as the first evaluate
    argument; the high-level ``Substrate`` accepts the same. The capability IS
    the composed Term-tree evaluated on the engine — no Python math."""
    def run(a: dict):
        n = int(a["of"])
        v = substrate.evaluate(tree, {"n": float(n)})
        fv = float(v)
        return int(round(fv)) if abs(fv - round(fv)) < 1e-9 else fv

    return run


def install_composed_capabilities(substrate, capabilities=None,
                                  path: Path = COMPOSED_PATH) -> dict:
    """LIVE, ADDITIVE install of the persisted generator-composed capabilities.

    Loads the persisted Term-trees and registers each into ``capabilities``
    (defaults to ``reason.CAPABILITIES`` — the LIVE registry the conversation
    path uses) as a Term-tree-backed entry: a router that evaluates the composed
    tree on the engine, ``lambda a: substrate.evaluate(tree, {"n": int(a["of"])})``.
    Also registers each as a graph-resident ``Capability`` node. EXISTING entries
    are never altered; IDEMPOTENT (re-install overwrites only the composed
    concepts with the same Term-tree router). Returns {concept: node_id}.
    """
    if capabilities is None:
        from domains import reason
        capabilities = reason.CAPABILITIES
    trees = load_composed_capabilities(path)
    installed: dict = {}
    for concept, tree in trees.items():
        node_id = register_capability_node(substrate, concept, tree)
        capabilities[concept] = _native_dispatcher(substrate, tree)
        installed[concept] = node_id
    return installed


__all__ = [
    "DictTerm", "RECIPES", "TRAIN_NS", "HELDOUT_NS", "COMPOSED_PATH",
    "synthesize_capability", "compose_summation_capabilities",
    "register_capability_node", "dispatcher_for", "install_into_capabilities",
    "persist_composed_capabilities", "load_composed_capabilities",
    "install_composed_capabilities",
]
