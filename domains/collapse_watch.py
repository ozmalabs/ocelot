"""collapse_watch -- the mechanical host hook for TIER 4 COGNITION (host I/O
only, per CLAUDE.md): periodically calls `domains.collapse_model.
predict_collapse` so a fresh `CollapseModel` node exists for the agent's OWN
authored rules (`seeds/composer_collapse_watch_graph.json`'s
`attend_frontier_<tag>` / `recognize_self_<tag>` / `predict_intervene_<tag>`)
to react to on the next `tick()`. Twin of `domains/experiment_dispatch.py` /
`domains/imagination_dispatch.py`'s `scan_and_*` hooks -- same discipline:
this module makes NO decision about what the model MEANS or what to DO about
it (that is entirely the agent's own composed rules, per the seed above); it
only calls a Python host function a Rust rule effect cannot call in the
first place (`predict_collapse` runs a bounded tier-3 forward-look via
`domains.imagination.imagine`, an in-process Python call, exactly why a host
hook is needed at all -- the same reason `experiment_dispatch.py` spawns a
child process the rule engine can't spawn itself) on a periodic cadence, and
mechanically wires `agent -has_collapse_model-> model` so the freshly-minted
CollapseModel is exposed to the rule engine as a matchable edge -- `add_edge`
targets inside a rule effect must be match-bound vars, and the CollapseModel
node does not exist until THIS Python call mints it, so no agent rule could
ever bind it without this wiring. This is the SAME idiom `domains.
reflective_faculty.ensure_grounding_gap_edges` uses to expose an
already-computed `GroundingGap` flag to the rule engine ("mechanical
exposure of an already-flagged node to the rule engine, not a re-decision").

THROTTLING. `scan_and_predict(agent, *, every_n=1)` is safe to call every
tick: an in-process call counter, keyed by `id(agent)`, throttles the actual
(non-trivial: a bounded forward-look) `predict_collapse` call to once every
`every_n` calls -- host BOOKKEEPING ONLY, never the source of truth (the
SAME "cache, not truth" convention `domains/experiment_dispatch.py`'s
`_INFLIGHT` dict documents for itself). A process restart loses the counter;
harmless, the next call simply predicts again. Passing the default
`every_n=1` predicts on every call -- appropriate for tests/scripts that
call this directly and want a synchronous, always-fresh model; a daemon
wiring it in at a coarser cadence (see `scripts/jabberwock_daemon.py`'s
`--collapse-every`) throttles the same way `--imagine-every` /
`--dispatch-every` already do.
"""
from __future__ import annotations

from typing import Any, Optional

from domains.collapse_model import CollapseModelResult, predict_collapse

# Host bookkeeping cache ONLY (never the source of truth -- the graph is):
# id(agent) -> number of scan_and_predict calls seen so far. Mirrors
# domains/experiment_dispatch.py's `_INFLIGHT` comment verbatim on this
# point -- an in-memory cache a fresh process starts empty, never persisted,
# never read as agent state.
_CALL_COUNT: dict[int, int] = {}


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


def scan_and_predict(agent, *, every_n: int = 1, **predict_kwargs) -> Optional[CollapseModelResult]:
    """Call `predict_collapse(agent, **predict_kwargs)` every `every_n`
    calls (throttled by the in-process counter above), then mechanically
    wire `agent -has_collapse_model-> model_node` so the agent's own
    authored collapse-watch rules can match on it. Returns the
    `CollapseModelResult` on a call that actually predicted, `None` on a
    throttled no-op call (nothing minted, nothing wired -- safe to call
    every tick regardless of `every_n`). Makes no decision: WHETHER to
    predict this call is a throttle, not a judgement about graph state;
    WHAT to do with a predicted divergence is entirely the agent's own
    `predict_intervene_<tag>` rule's concern, not this function's."""
    sub, native, ag_node = _resolve(agent)
    key = id(agent)
    n = _CALL_COUNT.get(key, 0) + 1
    _CALL_COUNT[key] = n
    if every_n > 1 and (n % every_n) != 0:
        return None
    res = predict_collapse(agent, **predict_kwargs)
    if ag_node is not None and native is not None:
        try:
            native.add_edge_unchecked(ag_node, "has_collapse_model", res.model_node, {})
        except TypeError:
            native.add_edge_unchecked(ag_node, "has_collapse_model", res.model_node)
    return res


__all__ = ["scan_and_predict"]
