"""memory_self_management — THIN ADAPTER over the Rust MEMORY faculty.

CLAUDE.md: "the agent is a graph running in Rust; Python is only the world adapter."
Memory management is a core agent function, so the keep/forget DECISION now lives in
Rust (runners/dsl/src/memory.rs: keep_value = salience(variance) + order_n saturation +
role multipliers; byte-bound; streaming forget-over-budget). This module is the thin
shim that lets existing callers (scripts.autonomous_watch) reach it through the same
surface they used before.

The DECISION moved to Rust.  What used to be ~160 lines of Python decision logic
(salience, order_n finite-difference, keep_value-per-byte ranking, byte estimation,
NEVER_FORGET, streaming forget) is now:
  · keep_value / salience / is_saturating / type_bytes / total_bytes -> crate::memory
  · forget_over_budget / observe_and_bound                           -> substrate methods
The ROLE table + NEVER_FORGET set are baked into crate::memory::role_for (the agent's
held role tags, not a Python decision).

The historical pure-Python implementation is preserved in domains.memory_shape_faculty
as the SPEC; this adapter no longer imports it for the decision — it calls the Rust.
"""
from __future__ import annotations

from typing import Any

from domains import self_persistence as _sp


class MemorySelfManagement:
    """Thin adapter: configures the Rust memory faculty's bounds, then delegates the
    keep/forget decision to it.  No Python decision logic remains."""

    def __init__(self, budget_nodes: int = 5000,
                 budget_bytes: int = 64 * 1024 * 1024):
        self.budget = budget_nodes
        self.budget_bytes = budget_bytes
        self.round = 0
        self._bound_set = False

    def _ensure_bound(self, s) -> None:
        if not self._bound_set:
            s.memory_bound(self.budget, self.budget_bytes, 3)
            self._bound_set = True

    def census(self, s) -> dict[str, int]:
        # PLUMBING only: a mechanical count for callers that still want a census view.
        from domains import memory_shape_faculty as _f
        return _f.census(s)

    def forget_over_budget(self, s) -> dict[str, int]:
        """STREAMING bound — shed the firehose AS it arrives.  Delegates to the Rust
        faculty's keep_value-per-byte decision (no Python ranking)."""
        self._ensure_bound(s)
        return dict(s.memory_forget_over_budget())

    def observe_and_bound(self, s, persist_path: str | None = None) -> dict[str, Any]:
        """End-of-round bound + persist.  The bound is the Rust faculty's decision; this
        adapter only maps the returned trace to the dict shape callers expect."""
        self._ensure_bound(s)
        self.round += 1
        tr = s.memory_observe_and_bound()
        out = {"round": self.round,
               "total_before": tr["nodes_before"], "total_after": tr["nodes_after"],
               "bytes_before": tr["bytes_before"], "bytes_after": tr["bytes_after"],
               "forgot": dict(tr["forgot"])}
        if persist_path:
            out["persisted"] = _sp.save_state(s, persist_path)
        return out
