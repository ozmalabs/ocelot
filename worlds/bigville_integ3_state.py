"""bigville_integ3_state -- the R10c TOWN-STATE EXPORT (a pure READER).

Extends R10b's `export_townstate2` (imported, unedited) with the now-ACTIVE social
state, ALL faithful graph reads -- never authored prose:

  * PAPER feed   -- the real Newspaper printings (printed/suppressed, informed-share,
                    coalition-forms) read off the Story/Coalition nodes.
  * BOARD readout-- the council's posted decisions (public address vs private held
                    decision = the 234 gap; the noticeboard `recorded` value + how many
                    residents read it), read off the Meeting/Notice nodes.
  * INFORMED /   -- the informed-share time-series vs the 3.5% (Chenoweth) threshold and
    COALITION       whether a coalition formed.
  * JOURNALS     -- each resident's REAL latest nightly JournalEntry, rendered from its
                    graph attrs into a first-person line (a mechanical render of real
                    state, exactly as R10b's `held` export formats reads -- no prose is
                    authored here or by the rule that minted it).

Pure read -> JSON; no decision.
"""
from __future__ import annotations

import json

from worlds.bigville_integ2_state import (                              # noqa: E402
    export_townstate2, _villager_entry)

_ACTION_LABEL = {0: "idle", 1: "work", 2: "withdraw", 3: "drink", 4: "snap"}


def _render_journal(attrs):
    """Render a JournalEntry's REAL attrs into a first-person diary line. Mechanical
    format over live graph reads (never authored) -- the glass-box first-person readout."""
    if not attrs:
        return None
    day = int(attrs.get("day", 0))
    coin = int(attrs.get("coin_held", 0))
    did = _ACTION_LABEL.get(int(attrs.get("did", 0)), "idle")
    parts = ["Day %d." % day, "I have %d coin." % coin, "Today I chose to %s." % did]
    g = float(attrs.get("grief", 0.0) or 0.0)
    if g > 0:
        parts.append("Grief weighs on me (%.1f)." % g)
    sp = float(attrs.get("snap", 0.0) or 0.0)
    if sp > 0:
        parts.append("I felt the urge to lash out (%.2f)." % sp)
    wb = float(attrs.get("wellbeing", 0.0) or 0.0)
    if wb:
        parts.append("Wellbeing sits at %.0f." % wb)
    cf = float(attrs.get("conflict", 0.0) or 0.0)
    if cf > 0:
        parts.append("I am torn (conflict %.1f)." % cf)
    if int(attrs.get("informed", 0)) == 1:
        parts.append("I read the news and know what happened in town.")
    bk = int(attrs.get("backed", 0))
    if bk:
        parts.append("I am siding with the pastor against the mayor.")
    return " ".join(parts)


def export_townstate3(world, *, macro_tail=None):
    """The full R10c town-state dict: R10b's export + the active social state + real
    per-villager journals. Pure read."""
    state = export_townstate2(world, macro_tail=macro_tail)

    # -- real journals rendered from graph attrs, attached per villager ------------
    disp_to_id = {}
    for nm in world.people:
        disp_to_id[world.display.get(nm, nm)] = nm
    for v in state["villagers"]:
        nm = disp_to_id.get(v.get("name"))
        if nm is None:
            continue
        attrs = world.latest_journal(nm)
        v["journal"] = _render_journal(attrs)

    # -- the paper feed (real Story/Coalition reads) ------------------------------
    state["paper"] = [dict(p) for p in getattr(world, "papers", [])]

    # -- the council board readout (real Meeting/Notice reads) --------------------
    state["council_board"] = [dict(c) for c in getattr(world, "council_log", [])]

    # -- informed-share vs the 3.5% threshold + coalition -------------------------
    iss = getattr(world, "informed_share_series", [])
    from worlds.bigville_integ3_world import CHENOWETH_FRAC
    state["collective_action"] = {
        "chenoweth_threshold": CHENOWETH_FRAC,
        "printings": [
            {"tick": t, "informed": inf, "n": n, "share": round(sh, 3),
             "above_3.5pct": sh >= CHENOWETH_FRAC, "coalition_formed": bool(fm)}
            for (t, inf, n, sh, fm) in iss],
        "coalitions_formed": sum(1 for (_t, _i, _n, _s, fm) in iss if fm),
    }

    # -- per-rung fired/dormant table ---------------------------------------------
    state["rung_report"] = world.rung_report()
    return state


def write_snapshot3(world, path, *, macro_tail=None):
    state = export_townstate3(world, macro_tail=macro_tail)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return state
