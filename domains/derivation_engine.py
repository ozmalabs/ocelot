"""derivation_engine — GOAL-DIRECTED order-N over the agent's held operations.

RECOGNITION + COMPOSITION (not a new mechanism). The agent already holds every
piece of a DERIVATION; what it LACKED was the GOAL-DIRECTED selector that replaces
order_n_composition.iterate_to_n's FIXED n with a step chosen by the goal's
structure. This module is that COMPOSITION — a derivation engine assembled from
the agent's OWN machinery, in a SHELL that only sequences the agent's acts (like
self_ascent.drive_ascent / scripts/agent_self_sources.py — it adds NO reasoning,
no decision-heuristic over math state).

A DERIVATION is a goal-directed order-N composition over operations:

    STATE   = the KNOWN facts (the givens) + every fact derived so far.
    GOAL    = a TARGET operator-tree (the agent's comprehend_computational_definition
              of the goal) whose leaves are held ops / givens and whose ROOT is the
              answer. The structure IS the goal-distance map.
    STEP    = apply ONE held operation to knowns -> a NEW fact. A node of the goal
              tree is APPLICABLE when ALL its children are already known (leaves, or
              previously-derived sub-results). Applying it = reason.solve over that
              sub-tree (the agent's evaluator), recording the result as a new known.
    SELECTOR= the AGENT'S: among the APPLICABLE nodes (the steps the goal structure
              ADMITS right now), pick the one that most advances toward the goal.
              The measure is COMPRESSION + GOAL-DISTANCE: each applied node collapses
              an un-evaluated sub-tree to a single known value, shrinking the residual
              un-derived structure (MDL — the derivation that reaches the goal in the
              fewest still-unknown nodes). VERIFY gates every step (the agent's held
              check — the result evaluates; the goal's falsifiable check, e.g. ∂∂=0 /
              known Betti / OEIS values). The selector reads the GOAL TREE, NOT a
              fixed op-ordering — so the OFFER ORDER of the ops is irrelevant (shuffle
              the menu, the same chain is found): the selector is real, not a script.
    VERIFY  = the agent's held truth-signal, applied at EACH step + on the final
              answer (the bottom-out / falsifiable check).
    ITERATE = order_n_composition.iterate_to_n over the STATE, the STEP as the rule,
              bounded, short-circuiting when the goal's root is known (DERIVED) or no
              applicable step remains (STALLED — surface the un-held leaf to acquire).

THE ACQUIRE CLOSURE — a goal leaf may reference an UN-HELD op (kernel / image: read
into a structure but not runnable). The engine SURFACES that gap (a goal-tree leaf
with no held capability + no known value) and DRIVES acquire (read def -> ground ->
verify -> the op becomes runnable), THEN continues the derivation with the now-held
op. The engine closes the rung ITSELF — it does not wait for a human to wire the op.

HONEST (binary admissibility — the win is the engine ADMITTED + verified, not an HLE
number): the engine works on SMALL VERIFIED derivations whose ops are all held (or
acquirable-by-reading) — e.g. the HOMOLOGY of standard spaces (boundary_matrix ->
matrix_rank -> Betti), where compute_homology HARD-CODES the chain. The engine
REDERIVES that chain from the GOAL. The full HLE bordism still needs (a) the
DESCRIPTION->OBJECT step ("moduli space ..." -> a chain complex) and (b) the BREADTH
of theorems (spectral sequences, generalized homology) acquired-runnable — both
NAMED as the residual. The engine is the MECHANISM; the breadth + description->object
are the climb. HLE-correct stays ~0 until the breadth is acquired.

No LLM, no Rust, no new primitive. A WORLD-ADAPTER SHELL over the agent's machinery:
the GOAL is comprehend_computational_definition's op-tree (graph data); the STEP is
reason.solve (the evaluator); the SELECTOR is goal-distance/compression + verify (the
agent's, not a Python heuristic over math state); the ITERATE is iterate_to_n; the
ACQUIRE is acquire.acquire. See [[ozma_order_n_concepts]] /
[[ozma_order_n_analysis_by_synthesis]] / [[ozma_synthesizes_own_gaps]] /
[[ozma_agent_writes_its_own_code]].
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from domains import order_n_composition as _onc
from domains import reason as _reason


# ---------------------------------------------------------------------------
# THE GOAL as an OPERATOR-TREE. Every interior node is a held-op application; a
# leaf is a literal or a GIVEN (a name bound in the state). The tree IS the goal-
# distance map: a node is KNOWN once its sub-tree has been collapsed to a value.
# We address nodes by a stable path (the route from the root) so the STATE can
# record "this sub-tree is now a known value" without mutating the goal tree.
# ---------------------------------------------------------------------------

def _head(node: Any) -> Optional[str]:
    if not isinstance(node, dict) or not node:
        return None
    return next((k for k in node if k != "force"), None)


def _children(node: Any) -> list[tuple[str, Any]]:
    """The (role, child) pairs of an interior op node, in a STABLE role order
    (sorted) so the engine's walk is deterministic and offer-order-independent."""
    h = _head(node)
    if h is None:
        return []
    spec = node[h]
    if not isinstance(spec, dict):
        return []
    return [(r, spec[r]) for r in sorted(spec.keys())]


def _is_leaf(node: Any) -> bool:
    """A leaf is a literal (number/bool) or a NAME (a given / a binder var). An
    interior op node has a held head + child roles."""
    return _head(node) is None


def _node_at(goal: Any, path: tuple) -> Any:
    node = goal
    for role in path:
        node = node[_head(node)][role]
    return node


def _all_op_paths(goal: Any, path: tuple = ()) -> list[tuple]:
    """Every INTERIOR (op-application) node's path, deepest-LAST (post-order), so
    a node's children precede it. Pure structural walk — no decision."""
    out: list[tuple] = []
    for role, child in _children(goal):
        if not _is_leaf(child):
            out.extend(_all_op_paths(child, path + (role,)))
    if not _is_leaf(goal):
        out.append(path)
    return out


# ---------------------------------------------------------------------------
# THE STATE — the KNOWN facts. A fact maps a goal sub-tree PATH (or a given NAME)
# to its derived value. The givens seed it; each derived step adds one.
# ---------------------------------------------------------------------------

@dataclass
class DerivState:
    givens: dict[str, Any]                       # name -> value (the givens)
    known: dict[tuple, Any] = field(default_factory=dict)  # op-path -> value
    trace: list[dict[str, Any]] = field(default_factory=list)
    stalled_at: Optional[str] = None
    acquired: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# APPLICABILITY — a goal-tree op node is a STEP the goal structure ADMITS NOW iff
# every child is already RESOLVABLE: a literal, a bound given, or an op-child whose
# own path is already KNOWN. This is the goal-directed condition — the agent applies
# the op the GOAL admits, bottoming up. Pure read of the goal tree + the state.
# ---------------------------------------------------------------------------

def _child_resolved(child: Any, child_path: tuple, st: DerivState,
                    caps: dict) -> bool:
    if _is_leaf(child):
        if isinstance(child, str):
            return child in st.givens          # a GIVEN name must be bound.
        return True                            # a literal is always resolved.
    return child_path in st.known              # an op-child must be derived.


def _is_applicable(goal: Any, path: tuple, st: DerivState, caps: dict) -> bool:
    if path in st.known:
        return False                           # already derived.
    node = _node_at(goal, path)
    head = _head(node)
    if head is None:
        return False
    if not _op_is_held(head, caps):
        return False                           # an UN-HELD op is a gap, not a step.
    for role, child in _children(node):
        if not _child_resolved(child, path + (role,), st, caps):
            return False
    return True


def _op_is_held(head: str, caps: dict) -> bool:
    """Is the op runnable — a held capability (or a binder the evaluator owns)?"""
    return head in caps or head in _reason._ITERATION_HEADS


# ---------------------------------------------------------------------------
# THE STEP — apply ONE admissible op to knowns -> a new fact, via reason.solve
# (the agent's evaluator). The sub-tree is rebuilt with its KNOWN op-children
# substituted by their derived values; the givens bind the leaf names. VERIFY gates
# the result (the agent's held check). NO math decision lives here — solve evaluates.
# ---------------------------------------------------------------------------

def _substituted(goal: Any, path: tuple, st: DerivState) -> Any:
    """The op node at `path` with its already-DERIVED op-children replaced by their
    known values (so reason.solve runs only the ONE op, over resolved operands)."""
    node = _node_at(goal, path)
    head = _head(node)
    out_spec = {}
    for role, child in _children(node):
        cpath = path + (role,)
        if not _is_leaf(child) and cpath in st.known:
            out_spec[role] = st.known[cpath]   # a derived value (a literal operand).
        else:
            out_spec[role] = child             # a leaf (given name / literal) or
                                               # a still-structural child (binders).
    return {head: out_spec}


def _apply_step(goal: Any, path: tuple, st: DerivState, caps: dict,
                verify: Callable[[str, tuple, Any, DerivState], dict]
                ) -> Optional[dict]:
    """Apply the op at `path` (reason.solve over the substituted sub-tree), VERIFY,
    and on success record the new known. Returns the trace entry, or None if solve
    raised / verify rejected (the honest per-step boundary)."""
    sub = _substituted(goal, path, st)
    head = _head(_node_at(goal, path))
    try:
        value = _reason.solve(sub, dict(st.givens), caps)
    except Exception as e:
        return {"path": path, "op": head, "ok": False,
                "reason": f"solve error: {e}"}
    vres = verify(head, path, value, st)
    if not vres.get("verified", True):
        return {"path": path, "op": head, "ok": False,
                "reason": f"verify rejected: {vres.get('reason', '')}",
                "value": value}
    st.known[path] = value
    return {"path": path, "op": head, "ok": True, "value": value,
            "verify": vres.get("reason", "")}


# ---------------------------------------------------------------------------
# THE SELECTOR — the AGENT'S. Among the APPLICABLE steps (the goal admits now),
# pick the one that most ADVANCES toward the goal. The measure is GOAL-DISTANCE /
# COMPRESSION: applying a node collapses its sub-tree to one value, removing the
# most un-evaluated structure from the residual. Concretely we rank by the SIZE of
# the sub-tree the step collapses (the deepest/biggest admissible sub-derivation
# closes the most of the goal) — MDL: the fewest remaining unknown nodes. This reads
# the GOAL TREE, not an op-ordering: the OFFER ORDER of the menu is irrelevant.
# ---------------------------------------------------------------------------

def _subtree_op_count(goal: Any, path: tuple) -> int:
    """How many op nodes the sub-tree at `path` contains — the goal-distance the
    step at `path` collapses (compression: applying it removes this many un-derived
    nodes from the residual). Pure structural count."""
    node = _node_at(goal, path)
    n = 0 if _is_leaf(node) else 1
    for role, child in _children(node):
        if not _is_leaf(child):
            n += _subtree_op_count(goal, path + (role,))
    return n


def _select(goal: Any, applicable: list[tuple], st: DerivState) -> Optional[tuple]:
    """The agent's goal-directed selector: of the applicable steps, the one closing
    the MOST goal-distance (largest collapsed sub-tree = most compression toward the
    answer), tie-broken by a stable path order (determinism, NOT a math heuristic).
    Reads the goal structure only — offer-order-independent."""
    if not applicable:
        return None
    return max(applicable,
               key=lambda p: (_subtree_op_count(goal, p), -len(p),
                              tuple(-1 if isinstance(r, str) else r for r in p)))


# ---------------------------------------------------------------------------
# THE ENGINE — iterate_to_n over the STATE, the goal-directed STEP as the rule.
# ---------------------------------------------------------------------------

def _default_verify(head: str, path: tuple, value: Any, st: DerivState) -> dict:
    """The agent's MINIMAL per-step truth-signal: the op produced a value (it
    evaluated over resolved operands). A goal may supply a STRONGER falsifiable
    verifier (∂∂=0 / known Betti / OEIS values) — passed to derive()."""
    return {"verified": value is not None,
            "reason": f"{head} evaluated -> {value!r}"}


def derive(goal: Any, givens: dict[str, Any], *,
           capabilities: Optional[dict] = None,
           verify: Optional[Callable[[str, tuple, Any, DerivState], dict]] = None,
           max_steps: int = 64,
           op_menu_order: Optional[list] = None) -> dict[str, Any]:
    """DERIVE the GOAL operator-tree from the GIVENS by goal-directed order-N.

    `goal`        — the target op-tree (the agent's comprehend output). Its ROOT
                    value IS the answer; its structure is the goal-distance map.
    `givens`      — name -> value (the givens; the leaf bindings).
    `capabilities`— the held ops (defaults to reason.CAPABILITIES). UN-HELD goal
                    leaves are surfaced as the acquire gap.
    `verify`      — the agent's held check, called at each step (default: evaluated).
                    A goal supplies a falsifiable verifier (e.g. the homology one).
    `op_menu_order`— ONLY used by the proof to SHUFFLE the order ops are offered in
                    (to show the selector is offer-order-independent). The selector
                    reads the goal tree, so this changes the WALK order, never the
                    chosen chain.

    Returns {derived, answer, steps, stalled_at, acquired, n_steps}. `derived` is
    the VERIFY signal on the root (the goal's root node became known + passed verify).
    """
    caps = dict(capabilities if capabilities is not None else _reason.CAPABILITIES)
    vfn = verify if verify is not None else _default_verify
    st = DerivState(givens=dict(givens))
    root_path: tuple = ()

    def _root_known(state: DerivState) -> bool:
        return root_path in state.known

    def _step(state: DerivState) -> Optional[DerivState]:
        if _root_known(state):
            return None
        # ASSESS: which op nodes does the goal structure ADMIT right now (bottom-up)?
        all_paths = _all_op_paths(goal)
        if op_menu_order is not None:
            # the proof's shuffle: present the SAME nodes in a different order. The
            # selector reads the tree, so this only re-orders the menu, not the pick.
            order = {p: i for i, p in enumerate(op_menu_order)}
            all_paths = sorted(all_paths, key=lambda p: order.get(p, 1_000_000))
        applicable = [p for p in all_paths if _is_applicable(goal, p, state, caps)]
        if applicable:
            # SELECT (agent) -> APPLY -> VERIFY. One step per drive.
            chosen = _select(goal, applicable, state)
            entry = _apply_step(goal, chosen, state, caps, vfn)
            state.trace.append(entry)
            if entry is None or not entry.get("ok"):
                # the step failed verify/solve and produced no progress -> STALL.
                state.stalled_at = f"step at {chosen} ({entry and entry.get('reason')})"
                return None
            return state
        # NO applicable held step. Either the goal is derived (root known) or there
        # is an UN-HELD op leaf blocking the chain -> surface the acquire gap.
        gap = _first_unheld_op(goal, state, caps)
        if gap is None:
            return None                          # nothing left (root known or done).
        state.stalled_at = gap
        return None

    final = _drive(st, _step, _root_known, max_steps)

    return {
        "derived": _root_known(final) and _final_verified(final, root_path, vfn),
        "answer": final.known.get(root_path),
        "steps": final.trace,
        "stalled_at": final.stalled_at,
        "acquired": final.acquired,
        "n_steps": len(final.trace),
    }


def _drive(state: DerivState, step: Callable, done: Callable, n: int) -> DerivState:
    """The bounded STATE iterate — NOT a private while-loop: it is acquire.ascend
    (iterate_to_n OVER a state, bounded, short-circuit on done / a None step), the
    SAME ONE iteration operator self_ascent.drive_ascent uses for its frontier climb.
    Here the STATE is the derivation's known-facts; the STEP is the goal-directed
    select+apply+verify hop. The shell adds no reasoning — ascend bounds + sequences."""
    from domains import acquire as _acq
    return _acq.ascend(state, step=step, n=n, done=done)


def _final_verified(st: DerivState, root_path: tuple, vfn: Callable) -> bool:
    """The root is verified iff it was recorded as a known (every recorded known
    passed verify in _apply_step). The root's own step already ran vfn; this is the
    bottom-out signal."""
    return root_path in st.known


# ---------------------------------------------------------------------------
# THE ACQUIRE GAP — surface the FIRST un-held op the goal references (a leaf the
# chain needs but the agent does not hold). The engine drives acquire on it (read
# -> ground -> verify) and the op becomes runnable; the derivation then continues.
# ---------------------------------------------------------------------------

def _first_unheld_op(goal: Any, st: DerivState, caps: dict) -> Optional[str]:
    """The first op head in the goal tree that is NOT held + not already derived —
    the gap the engine must acquire before the chain can bottom out. Pure read."""
    for path in _all_op_paths(goal):
        if path in st.known:
            continue
        head = _head(_node_at(goal, path))
        if head is not None and not _op_is_held(head, caps):
            # only a TRUE gap if its operands are otherwise resolvable (so acquiring
            # THIS op unblocks the step) — else a deeper gap is the real wall.
            if all(_child_resolved(c, path + (r,), st, caps)
                   for r, c in _children(_node_at(goal, path))):
                return head
    # fall back to the deepest un-held head even if operands not yet ready.
    for path in _all_op_paths(goal):
        head = _head(_node_at(goal, path))
        if head is not None and not _op_is_held(head, caps) and path not in st.known:
            return head
    return None


def derive_with_acquire(goal: Any, givens: dict[str, Any], *,
                        capabilities: Optional[dict] = None,
                        acquire_op: Callable[[str, dict], bool],
                        verify: Optional[Callable] = None,
                        max_rounds: int = 6,
                        **derive_kw) -> dict[str, Any]:
    """DERIVE, closing the acquire rung ITSELF: run `derive`; if it STALLS on an
    UN-HELD op (a goal leaf read-into-structure but not runnable), the engine DRIVES
    `acquire_op(head, caps)` — read the op's def -> ground -> verify -> the op becomes
    a held capability (mutating `caps`) — then RE-RUNS derive with the now-held op.
    Repeat until derived or the gap is un-acquirable (the honest wall).

    `acquire_op(head, caps) -> bool` is the agent's acquire act (acquire.acquire /
    compute_grounding.ground_computation), supplied by the caller as a parameter —
    the SHELL only sequences it, it does not decide what the op MEANS. Returns the
    final derive result, plus `acquired` = the ops the engine acquired to close it.
    """
    caps = dict(capabilities if capabilities is not None else _reason.CAPABILITIES)
    acquired: list[str] = []
    res = None
    for _ in range(max_rounds):
        res = derive(goal, givens, capabilities=caps, verify=verify, **derive_kw)
        if res["derived"]:
            break
        gap = res["stalled_at"]
        # the stall names an un-held OP head (a bare op name, not a "step at ..." note).
        if not isinstance(gap, str) or gap.startswith("step at "):
            break
        # DRIVE the acquire of the un-held op (the agent's read->ground->verify).
        ok = acquire_op(gap, caps)
        if not ok:
            break                                # un-acquirable -> the honest wall.
        acquired.append(gap)
    if res is not None:
        res = dict(res)
        res["acquired"] = acquired
    return res


__all__ = [
    "DerivState", "derive", "derive_with_acquire",
    # exposed for the proof / inspection:
    "_all_op_paths", "_is_applicable", "_select", "_subtree_op_count",
    "_first_unheld_op", "_node_at",
]
