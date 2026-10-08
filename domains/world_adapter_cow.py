"""Copy-on-write forks of a quiescent :class:`WorldAdapter`.

The native substrate snapshot shares graph pages. Adapter-owned Python state is
copied so branch-local indexes and counters cannot leak across users. Objects
that cannot be copied cause a fail-closed error; callers must not silently
replace this with a graph-only fork.
"""
from __future__ import annotations

import copy

from substrate.world_adapter import WorldAdapter, _AdapterNativeFacade


class AdapterForkError(RuntimeError):
    """The adapter contains state that cannot safely be forked right now."""


def _remember_node_ids(value, node_id_type, memo, seen):
    """Keep immutable native NodeIDs stable while copying Python containers."""
    marker = id(value)
    if marker in seen:
        return
    seen.add(marker)
    if isinstance(value, node_id_type):
        memo[marker] = value
    elif isinstance(value, dict):
        for key, item in value.items():
            _remember_node_ids(key, node_id_type, memo, seen)
            _remember_node_ids(item, node_id_type, memo, seen)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            _remember_node_ids(item, node_id_type, memo, seen)


def fork_world_adapter(source: WorldAdapter) -> WorldAdapter:
    """Return a whole-adapter branch with a CoW native graph.

    The source is locked while the graph snapshot and adapter-owned state are
    captured. The native snapshot enforces its own eligibility rules (for
    example, active worker threads and unsupported external resources).
    """
    if not isinstance(source, WorldAdapter):
        raise TypeError("source must be a WorldAdapter")
    excluded = {"s", "inner", "_conversation_lock"}
    graph_bound_cache = {"_discourse_store"}
    with source._conversation_lock:
        try:
            # Check gates under the same lock as the snapshot. Public adapter
            # methods that start/attach these resources use this lock too, so
            # an in-flight operation cannot pass the check between validation
            # and graph capture.
            if getattr(source, "_teacher_threads", None):
                raise AdapterForkError(
                    "cannot fork while teacher threads are active")
            if getattr(source, "_storage_mmap", None) is not None:
                raise AdapterForkError(
                    "cannot fork with an attached storage mmap")
            # These runtime handles own separate mutable resources and are not
            # covered by the graph snapshot. A caller may rebuild them on the
            # branch first.
            for name in ("_eye", "_upload_eye", "_vision_substrate"):
                if getattr(source, name, None) is not None:
                    raise AdapterForkError(f"cannot fork with attached {name}")
            node_id_type = type(source.agent)
            memo = {}
            seen = set()
            for name, value in vars(source).items():
                if name not in excluded:
                    _remember_node_ids(value, node_id_type, memo, seen)
            copied = {
                name: copy.deepcopy(value, memo)
                for name, value in vars(source).items()
                if name not in excluded | graph_bound_cache
            }
            graph_branch = source.s.snapshot().fork()
        except AdapterForkError:
            raise
        except Exception as exc:
            raise AdapterForkError(
                f"whole-adapter snapshot failed: {type(exc).__name__}: {exc}"
            ) from exc

        branch = copy.copy(source)
        branch.__dict__.update(copied)
        # DiscourseStore holds direct references to the source substrate and
        # its concept-provider closure. It is a graph-derived cache, so rebuild
        # it lazily against the new CoW branch rather than deepcopying a stale
        # pointer or sharing mutable cache state.
        branch._discourse_store = None
        branch.s = graph_branch
        native = _AdapterNativeFacade(graph_branch._inner)
        branch._conversation_lock = native._lock
        graph_branch._inner = native
        branch.inner = native
        return branch
