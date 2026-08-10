"""worlds/fb_eye — mechanical world-adapter helper for the shared-memory eye
(host I/O only, CLAUDE.md). NOT a general browser/game world — a small,
standalone helper for whatever driver wants to give the agent something to
look at via the Rust shm eye (``fb_attach`` / the rule-driven ``FbSample``
effect), without pulling in the much larger ``worlds/browser.py`` (which
already owns its own live-eye path and stays untouched here).

Does exactly two mechanical things, per the world-adapter contract:

  1. **attach** — call the Rust eye's ``fb_attach`` on an already-existing
     POSIX shm framebuffer (written by something else — a real writer
     subprocess, ``scripts/fb_pipe.py --test-pattern``, browser CDP, ...) and
     mirror the resulting ``fb_id`` onto a graph-resident ``LookTrigger`` node
     that also carries the downsample grid dims, wired
     ``trigger -wants_look-> game`` to the ``WorldInstance``/game-root node
     the agent is meant to watch.

  2. NOTHING ELSE. The WHEN-TO-SAMPLE decision belongs to the agent's own
     composed rule (``domains.reflective_faculty._compose_attention_rule`` —
     match ``?t -wants_look-> ?g``, gated by ``FbFrameSeq(Attr(?t,'fb_id')) >
     Attr(?g,'last_looked_seq')``); this module never calls ``fb_sample``
     itself.

This is the "whoever attaches a framebuffer stamps the session/game node with
fb_id + wants_look edge" mechanism the composer's rule reads its wiring off
of — mechanical translation of external process state (a shm attach) into
graph context, no decision about when to look.
"""
from __future__ import annotations


def attach_eye(agent, shm_name: str, grid_w: int, grid_h: int, game_node=None):
    """Attach ``shm_name`` via the Rust eye and stamp graph context for the
    agent's own look-rule to read. Mints ``game_node`` (a bare
    ``WorldInstance``) if one isn't supplied, plus a ``LookTrigger`` carrying
    ``(fb_id, grid_w, grid_h)`` wired ``-wants_look->`` it.

    Returns ``(fb_id, game_node, trigger_node)``. Mechanical I/O only — no
    decision about WHEN to sample lives here."""
    fb_id = agent.inner.fb_attach(shm_name)
    S, I = agent.s, agent.inner
    if game_node is None:
        game_node = S.add_node("WorldInstance", {"world_type": "Game", "last_looked_seq": -1.0})
    trigger = S.add_node("LookTrigger", {
        "fb_id": float(fb_id), "grid_w": float(grid_w), "grid_h": float(grid_h),
    })
    I.add_edge_unchecked(trigger, "wants_look", game_node)
    return fb_id, game_node, trigger


def detach_eye(agent, fb_id: int) -> None:
    """Best-effort teardown of a prior ``attach_eye`` (host I/O only)."""
    try:
        agent.inner.fb_detach(fb_id)
    except Exception:  # noqa: BLE001 -- best-effort teardown
        pass
