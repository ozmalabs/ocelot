"""Block 342000 — VOICE + COMPLEXITY signals from the resolved audience slot.

Rung 1 chose words by cranking a single goal weight until it dominated — that
picked WHAT to say but not HOW, and it OVERRODE voice/complexity rather than
composing with them. Rung 2 fixes that: the audience slot (resolved by
conceptualizer.resolve_audience, orthogonal to the goal's target) supplies two
signals that COMPOSE with the goal's content in the generation ranking:

  VOICE      — the register/idiolect the utterance is shaped in. For the SELF
               audience (the endogenous default) this is the agent's OWN idiolect:
               the recurring surface of its WriterStyle. For a specified audience
               it is that audience's register. Voice biases the FUNCTION/framing
               words, not the content.
  COMPLEXITY — how much to spell out, audience-relative. Reuses the
               audience_driven_production discipline: the residual = the content
               concepts the audience does NOT already hold (must be said); the
               credited-known concepts may be left implicit. For the SELF audience,
               'what the audience knows' = what the agent itself grounds, so
               complexity is GROUNDING-DEPTH-relative. Ungrounded audience => spell
               everything out (the curse-of-knowledge discipline).

These are returned as light dicts the generator folds into predict_next_words
(goal_content = the must-say residual; voice words lifted via the register term),
so content(goal) x voice(idiolect) x complexity(residual) COMPOSE in the held-Plus
ranking instead of one term stomping the others.

Additive; no substrate .so write path; touches no protected file.
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Optional


def _writer_idiolect(agent, ws_node) -> list[str]:
    """The agent's OWN idiolect surface (voice) — the recurring surface words of a
    WriterStyle it holds. Empty when no self-style is available (voice then adds
    nothing, and content/complexity carry the utterance). Pure graph read."""
    if ws_node is None:
        return []
    try:
        sub = agent if hasattr(agent, "node") else agent.substrate
        at = dict(sub.node(ws_node)["attrs"])
        return list(json.loads(at.get("recurring_surface") or "[]"))
    except Exception:
        return []


def shape_from_audience(agent, resolved_audience: dict, content: Iterable[str],
                        *, self_style_node: Optional[Any] = None) -> dict[str, Any]:
    """Turn a RESOLVED audience (conceptualizer.resolve_audience output) + the goal's
    content into VOICE + COMPLEXITY signals for the generator.

    Returns:
      {complexity_residual: [concept...],   # content the audience does NOT hold -> MUST say
       credited_known:      [concept...],   # content the audience holds -> may leave implicit
       voice_words:         [word...],      # register/idiolect words to lift (framing, not content)
       grounded:            bool,           # False -> spell everything out (curse-of-knowledge)
       mode:                'self'|'specified'}

    For the SELF audience the 'known' set is what the agent itself grounds (its own
    held content), so the residual is grounding-depth-relative; voice is the agent's
    own idiolect. For a specified audience, known = audience.known_concepts and voice =
    the audience register words (if any)."""
    content_set = [str(c) for c in content]
    mode = str(resolved_audience.get("mode", "self"))
    known = {str(c) for c in (resolved_audience.get("known_concepts") or [])}

    # complexity: residual = content the audience does not already hold (must be said);
    # credited_known = content it holds (may be implicit). For self with empty known,
    # residual == all content (say it fully at your own grain).
    residual = [c for c in content_set if c not in known]
    credited = [c for c in content_set if c in known]

    # voice words: self -> own idiolect (recurring surface); specified -> the audience's
    # register words if provided (else none). Voice never includes content (framing only),
    # so we drop any overlap with the content set.
    reg = resolved_audience.get("register")
    reg_words = ([str(w) for w in reg] if isinstance(reg, (list, tuple))
                 else ([str(reg)] if isinstance(reg, str) else []))
    idiolect = _writer_idiolect(agent, self_style_node) if mode == "self" else reg_words
    voice_words = [w for w in idiolect if w not in set(content_set)]

    # grounded: a self audience is always grounded (the agent observes itself); a
    # specified audience is grounded iff it carries known concepts or an explicit flag.
    grounded = (mode == "self") or bool(known) or bool(resolved_audience.get("grounded"))

    return {"complexity_residual": residual, "credited_known": credited,
            "voice_words": voice_words, "grounded": bool(grounded), "mode": mode}
