"""PREDICATE PUSHDOWN — the §9 byte-identity contract, as a pytest gate.

Pushdown is a PURE PERFORMANCE CHANGE to the shared rule matcher. It arms on
EVERY rule with >1 match-edge and a top-level `And` where-clause — 18 rules on
a `vision_waves` boot, including conversation/causal rules, not just vision. So
the contract it must satisfy is exactly one thing:

    the pushed-down path admits EXACTLY the bindings the whole-where path does.

WHY THE CONTRACT AND NOT A VALUE (PROTOCOL §12.3): both arms are recomputed
LIVE here. Nothing is pinned to a hash of a mutable tree. Two gates rotted the
same day they were written by pinning one, and they rotted by falsely accusing
an innocent rung; the bulk agent's digest legitimately moved when `drive()`
changed under it. When `drive()` changes these floats again, both arms move
together and this gate still means what it says.

The heavy end-to-end digest (every attr of every cell/unit/synapse at full
`repr`, both `track_prev_burst` arms, plus the oracle's own +1e-9 positive
control) lives in `scripts/pushdown_identity_gate.py` — it takes minutes, so it
is a script. These are the fast invariants that must never rot.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    return s, ag


def _run(s, pushdown: bool, steps: int = 24, g: int = 24):
    if not pushdown:
        s._inner.clear_pushdown_plans()
    w = WaveWorld(s, h=g, w=g, seed=0)
    for i in range(steps):
        w.step(ignite_k=2 if i % 5 == 0 else 0)
    out = []
    for n in w.cells.values():
        at = s.node(n)["attrs"]
        out.append(tuple(repr(at.get(k)) for k in
                         ("state", "fired_at", "activated_at", "bursting",
                          "last_burst", "driven")))
    return out


def test_pushdown_is_armed_on_the_real_rules():
    """POSITIVE CONTROL for every test below. If pushdown never engages, the
    identity checks compare one code path with itself and pass forever —
    §1's 'a dead arm scores a perfect floor', applied to a guard."""
    s, _ = _boot()
    armed = s._inner.pushdown_armed()
    assert armed, "pushdown armed on NO rule — every identity check below is vacuous"
    assert "wv_propagate" in armed, (
        "wv_propagate carries no pushdown plan — it is the rule this rung is "
        f"about; armed set was {armed}")


def test_the_off_switch_actually_restores_the_old_path():
    """The OFF arm must be a real code-path change, or ON==OFF is trivial."""
    s, _ = _boot()
    cleared = s._inner.clear_pushdown_plans()
    assert cleared > 0, "clear_pushdown_plans() cleared nothing — no OFF arm exists"
    assert s._inner.pushdown_armed() == [], "plans survived the clear"


def test_pushdown_changes_no_cell_state():
    """THE CONTRACT: the whole wave trajectory is bit-identical either way."""
    s_on, _ = _boot()
    on = _run(s_on, pushdown=True)
    s_off, _ = _boot()
    off = _run(s_off, pushdown=False)

    # The arms must be ALIVE: two dead grids match perfectly (§1.1).
    assert any(row[0] == "'active'" for row in on) or \
           any(row[0] == "'refractory'" for row in on), \
        "no cell ever fired — the identity below is vacuous"
    assert on == off, "PUSHDOWN CHANGED THE TRAJECTORY — a bug, not an optimisation"


def test_single_edge_rules_are_never_pushed_down():
    """SCOPE GUARD. A 1-edge rule has no subtree to prune, so it must be left
    byte-identical. The five `ch_*` drive rules are exactly this shape — they
    are the current cost leader and are deliberately NOT touched by this rung.
    """
    s, _ = _boot()
    armed = set(s._inner.pushdown_armed())
    for name in ("ch_drive_median", "ch_transient_on", "ch_transient_off",
                 "ch_sustained", "ch_adapt_ref", "wv_refract", "wv_recover"):
        assert name not in armed, (
            f"{name} is a single-match-edge rule and must carry NO pushdown "
            f"plan (byte-identity scope guard)")
