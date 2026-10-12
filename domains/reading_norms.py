"""reading_norms — DYNAMIC, REFORMABLE READING THRESHOLDS (Wave: dynamic-
thresholds/reopen/reform, 2026-07-11).

The user's directive: "thresholds should be dynamic based on complexity and
overflow and be able to be reformed." This module is the thin I/O boundary
between the live reading drivers (reading_scope / coref_entities /
reading_drive) and the HELD belief the thresholds actually live in —
`ApertureBudget` (seeds/reading_aperture.json), extended this wave with the
reading-layer fields (`trace_capacity_*`, `max_revisits`, `max_order_*`,
`widen_step`, `widen_salience_threshold`, `reform_*_threshold`,
`reform_pressure_factor`), plus two held Program (Term-tree) derivations
(`reading_derive_trace_capacity`, `reading_derive_max_order`) evaluated by
the Rust engine via `native.evaluate` — the SAME `_licensed`/`global_
contradiction` idiom `reading_review.py`/`global_monitoring.py` already use:
Python reads a handful of ALREADY-COMPUTED signals (the register's held
budget row, this flow's own eviction-pressure/reform-count data) mechanically
off the graph, hands them in as `env`, and returns whatever the Program
computes. NO decision lives in this file — editing an ApertureBudget node's
numbers, or the two Program Term-trees, changes the derived capacity/order
with zero code changes (that IS "able to be reformed").

Every function here degrades to the PRE-WAVE Python literal default when no
ApertureBudget/Program exists on the substrate (an isolated unit test that
never loaded seeds/reading_aperture.json) — so every caller's existing
default-argument behaviour is unchanged unless the seed is present.
"""
from __future__ import annotations

from typing import Optional


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def budget_for_register(sub, register: Optional[str]) -> Optional[dict]:
    """Mechanical lookup: THIS register's own ApertureBudget belief (held graph
    data), falling back to the `default` row. Returns the node's attrs dict, or
    None when no ApertureBudget exists at all (the seed was never loaded) — every
    caller below falls back to its own pre-wave Python literal in that case."""
    reg = register or "default"
    found = None
    fallback = None
    for n in sub.nodes("ApertureBudget"):
        at = sub.node(n)["attrs"]
        if at.get("register") == reg:
            found = at
            break
        if at.get("register") == "default":
            fallback = at
    return found or fallback


def _eval_program(sub, native, name: str, env: dict):
    from domains import reflective_faculty as rf
    try:
        prog = rf._load_program(sub, name)
    except Exception:
        prog = None
    if prog is None or native is None:
        return None
    try:
        return native.evaluate(prog, env)
    except Exception:
        return None


def effective_trace_capacity(agent, register: Optional[str], *, widened: bool = False,
                             default: int = 8) -> int:
    """The ring buffer's EFFECTIVE capacity for this flow: the held
    `reading_derive_trace_capacity` Program, evaluated over this register's own
    ApertureBudget row + whether the flow has already spent its one-shot widen
    (`widened` — mechanically read off the flow's Source.capacity_widened by the
    caller, itself set by the `reading_widen_capacity_once` rule on eviction
    pressure). Clamped [trace_capacity_min, trace_capacity_max] BY THE PROGRAM
    (data, not Python)."""
    sub, native = _resolve(agent)
    budget = budget_for_register(sub, register)
    if budget is None:
        return default
    base = float(budget.get("trace_capacity_base", default))
    env = {"base": base,
          "min_cap": float(budget.get("trace_capacity_min", base)),
          "max_cap": float(budget.get("trace_capacity_max", base)),
          "widen_step": float(budget.get("widen_step", 0.0)),
          "widened": 1.0 if widened else 0.0}
    val = _eval_program(sub, native, "reading_derive_trace_capacity", env)
    # NO Python floor here beyond int(): the clamp [min_cap, max_cap] is HELD
    # DATA the Program itself applies (Min/Max Terms over the ApertureBudget
    # row's own attrs) -- "clamps as node attrs, not code". A Python-side
    # `max(1, ...)` here would silently override an intentionally-configured
    # zero/degenerate capacity with a hidden code clamp the held data cannot see
    # or revise.
    return int(base) if val is None else int(val)


def effective_turn_capacity(agent, register: Optional[str] = "conversational", *,
                            widened: bool = False, default: int = 8) -> int:
    """The CONVERSATION turn ring's effective capacity N: the SAME held
    `reading_derive_trace_capacity` Program the reading ring uses, evaluated
    over the register row's `turn_capacity_*` / `turn_widen_step` attrs
    (seeds/reading_aperture.json v1.3.0) and whether the conversation has spent
    its one-shot widen (TurnRing.capacity_widened, set by the
    `conversation_widen_turn_capacity_once` rule). The clamp is held data."""
    sub, native = _resolve(agent)
    budget = budget_for_register(sub, register)
    if budget is None or budget.get("turn_capacity_base") is None:
        return default
    base = float(budget["turn_capacity_base"])
    env = {"base": base,
           "min_cap": float(budget.get("turn_capacity_min", base)),
           "max_cap": float(budget.get("turn_capacity_max", base)),
           "widen_step": float(budget.get("turn_widen_step", 0.0)),
           "widened": 1.0 if widened else 0.0}
    val = _eval_program(sub, native, "reading_derive_trace_capacity", env)
    return int(base) if val is None else int(val)


def effective_max_order(agent, register: Optional[str], *, reform_count: float = 0.0,
                        default: int = 2) -> int:
    """The order-N descent's EFFECTIVE depth for this flow: the held
    `reading_derive_max_order` Program, evaluated over this register's own budget
    row + this flow's own reform COUNT (a residual-mass proxy: once the flow has
    already needed to reform a clause into components, a deeper descent is
    licensed for the rest of the flow, up to `max_order_max`)."""
    sub, native = _resolve(agent)
    budget = budget_for_register(sub, register)
    if budget is None:
        return default
    base = float(budget.get("max_order_base", default))
    env = {"base": base,
          "max_cap": float(budget.get("max_order_max", base)),
          "reform_count": float(reform_count or 0.0)}
    val = _eval_program(sub, native, "reading_derive_max_order", env)
    # Same discipline as effective_trace_capacity: no hidden Python floor.
    return int(base) if val is None else int(val)


def effective_max_revisits(agent, register: Optional[str], default: int = 8) -> int:
    """The backtrack bound — a direct HELD-VALUE read (not derived: max_revisits
    is reformable by editing the node, but this wave ships only the capacity/
    max_order pair as dynamic derivations per the task scope)."""
    sub, _ = _resolve(agent)
    budget = budget_for_register(sub, register)
    if budget is None or budget.get("max_revisits") is None:
        return default
    return max(1, int(budget["max_revisits"]))


def reform_pressure_factor(agent, register: Optional[str], *, widened: bool) -> float:
    """The multiplier the reform rule applies to its own residual/swallowed
    thresholds once the flow's one-shot widen is already spent (`widened`) —
    "widen once, then reform" (task 2's ladder): LOWERING the bar under
    sustained pressure rather than widening the ring indefinitely. 1.0 (no
    tightening) when the flow hasn't hit that rung yet, or the seed is absent."""
    sub, _ = _resolve(agent)
    budget = budget_for_register(sub, register)
    if budget is None:
        return 1.0
    return float(budget.get("reform_pressure_factor", 1.0)) if widened else 1.0


def record_eviction_pressure(sub, flow_node, salience: float) -> None:
    """Mechanical bookkeeping datum (the `shadow_latency_recent_avg` rolling-
    average precedent, comprehension_health.json): bump this flow's own eviction
    COUNT and running MAX evicted salience on its Source node. Never a decision —
    the overflow-response ladder (`reading_widen_capacity_once` /
    `reform_overcomplex_clause`, seeds/reading_aperture.json) is graph rules that
    READ these two numbers."""
    if flow_node is None:
        return
    at = sub.node(flow_node)["attrs"]
    count = float(at.get("traces_evicted", 0.0) or 0.0) + 1.0
    mx = max(float(at.get("max_evicted_salience", 0.0) or 0.0), float(salience or 0.0))
    sub.set_attr(flow_node, "traces_evicted", count)
    sub.set_attr(flow_node, "max_evicted_salience", mx)


def record_reform(sub, flow_node) -> None:
    """Mechanical bookkeeping datum: bump this flow's own reform COUNT — the
    residual-mass proxy `effective_max_order` reads to license a deeper descent
    for the REST of this flow once it has proven genuinely complex."""
    if flow_node is None:
        return
    at = sub.node(flow_node)["attrs"]
    count = float(at.get("reform_count", 0.0) or 0.0) + 1.0
    sub.set_attr(flow_node, "reform_count", count)


def flow_register(sub, flow) -> Optional[str]:
    """Mechanical read: THIS flow's own Goal.register (`reading_drive._mint_goal`
    stamps it onto the Goal it mints alongside the Source). None when no Goal
    carries this flow's identity (a caller with no `run_reading_flow` behind it,
    e.g. a bare unit test) — every effective_* function above falls back to its
    own Python default in that case."""
    if flow is None:
        return None
    for n in sub.nodes("Goal"):
        at = sub.node(n)["attrs"]
        if at.get("flow") == flow:
            return at.get("register")
    return None


__all__ = [
    "budget_for_register", "effective_trace_capacity", "effective_turn_capacity", "effective_max_order",
    "effective_max_revisits", "reform_pressure_factor",
    "record_eviction_pressure", "record_reform", "flow_register",
]
