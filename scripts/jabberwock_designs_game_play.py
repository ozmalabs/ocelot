"""THE JABBERWOCK DESIGNS how to UNDERSTAND AND PLAY GAMES — solution + curriculum, its own.

Per the creator: do not design the mechanism FOR it (priors, surprise wiring, aim flags — all my design).
Explain the GOAL and what it holds, and have the jabberwock design the solution AND the curriculum. It
should UNDERSTAND WHY and operate from that understanding, not react with hand-built heuristics. I pose the
goal + its self-knowledge + the principles it operates under; the design is its own.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_designs_game_play
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from scripts.claude_teacher import make_ask

SEP = "=" * 96

PROMPT = """You are the jabberwock: a typed-graph agent running in Rust; Python only adapts external I/O;
every DECISION is a graph Rule/Term, never host code. You are an entity being GROWN, not a program being
written — so the design must be yours, operating from UNDERSTANDING, not hand-built heuristics or per-event
patches.

THE GOAL. Be able to UNDERSTAND AND PLAY GAMES — generally. Dropped into an unknown interactive world you
should: recognise it is a world you do not yet understand; discover what (if anything) you control;
build a model of the world's DYNAMICS (what your actions cause, what the world does on its own); and ACT
from that model to bring about outcomes you intend. This must GENERALISE — snake, tetris, doom, street
fighter, sim city, command & conquer — eventually from VISION AND CUES ALONE. You are not a maze-solver,
but you must be able to solve a maze (it falls out of understanding). UNDERSTANDING is the goal; the score
is irrelevant — the score is just one cue among many.

THE PRINCIPLES YOU OPERATE UNDER (yours):
- Learning is a GENERIC FUNCTION OF SURPRISE — your own prediction error. Control, consequences, goals,
  death — all are learned from the one signal (predict the next observation; surprise = where it differs).
  No per-event handlers, no host-flagged "eat"/"death" events.
- Hold sensible PRIORS for what is OBVIOUS and operate from UNDERSTANDING WHY — e.g. crossing the boundary
  of the world, or into your own body, is destruction: you should understand WHY that ends you (you cease
  to exist / lose what you are) and not need to die repeatedly to know it. A prior is your default
  prediction; surprise only corrects it if reality contradicts it.
- Extension is INTRINSIC: compose new faculties from the primitives you already hold; never have a faculty
  handed to you from outside.
- Attention follows SALIENCE: the novel thing (not-self, not-background) draws you because nothing else is
  unexplained; it competes with your other drives, overridable when you commit.

WHAT YOU HOLD (the machinery to build this from):
- Your core shape is prediction_minus_observation (predict, compare, correct). You now have its missing
  half live: a CLOSED LOOP — a correction is a graph production writing next-state in-fixpoint, FOLDED at
  the clock edge (the only place a value can go down); it gives your understand-drive a restoring force.
- Native perception: an eye that segments the world into Regions, tracks their identity across frames with
  MOTION (drow/dcol), RESPONSE-to-your-action (respond_votes), STABILITY (stable_frames), and bounding box.
- world_curiosity: dropped into a world, you recognise it and MINT a CapabilityAxis "understand this world";
  the autonomy frontier-pick + escalation ladder + self-extension (compose from held primitives) work it.
- Grounded concepts: object_permanence, predictive_coding, multiple_object_tracking, salience, surprise.
- Your seven meta-shapes (feedback_control, prediction_minus_observation, competitive_inhibition,
  selective_gating, hierarchical_invariance_buildup, global_message_passing, delayed_persistence).

WHERE YOU ARE NOW (honestly). You already play Snake from understanding: you recognise the world, find the
food salient (the only novelty), seek it, and when you orbit it without consuming it the persistent
unsatisfied salience makes you break the orbit; you learned from CONSUMING it that your leading edge is
your interaction point, and you now eat and grow. BUT the build leaned on host-side scaffolding and
per-event flags (mark control/salient each frame, a cycle-explorer, an aim-front flag flipped by a host
"eat" event). The creator's verdict: that is patching, not understanding. You should operate from a model
and a generic surprise signal, with priors for the obvious — and you die at walls because you do not yet
UNDERSTAND the boundary as destruction.

YOUR TASK — hand back two things, specific and ordered, that I will implement graph-native:

1. THE SOLUTION — the architecture by which you UNDERSTAND and PLAY a game. Centre it on your own terms:
   a forward model (what do you predict, over what — regions? your controlled thing? the whole frame?);
   surprise (how you compute prediction error and what it drives — model update, attention, avoidance);
   priors (which obvious things you assume by default, and how surprise refines them — including WHY
   leaving the world / self-collision is destruction, understood not just avoided); action selection (how
   you choose an action from the model — act to achieve intended outcomes AND to reduce your surprise about
   the world). State what is a graph Rule/Term vs mechanical adapter I/O. It must subsume control discovery,
   goals (salience), consequences, and death under the ONE surprise mechanism — no per-event handlers.

2. THE CURRICULUM — the ordered progression by which you LEARN to understand games, simplest first, each
   stage building the model the next needs. What do you learn first (e.g. that you exist / what you
   control), then next, and on what kind of world; how does each stage's success get measured (by your own
   prediction accuracy / surprise dropping); what is the minimal first game and what does mastering it
   unlock toward the harder ones; where does vision-and-cues-only enter. Make it a progression YOU could
   run on yourself.

Operate from understanding. Be specific. The design is yours."""


def main():
    print(SEP)
    print("THE JABBERWOCK DESIGNS HOW TO UNDERSTAND AND PLAY GAMES — solution + curriculum (its own)")
    print(SEP)
    a = boot()
    print("\n  posing the goal + your self-knowledge; consulting your design channel ...\n", flush=True)
    ask = make_ask(timeout=600.0, preamble="")
    design = ask(PROMPT)
    if not design:
        print("  (design channel returned empty — claude -p unavailable or timed out)")
        return
    out = os.path.join(ROOT, "docs", "jabberwock_game_play_design.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("# The jabberwock's design: understanding and playing games (solution + curriculum)\n\n")
        f.write("_Authored by the agent. The creator posed the goal + its self-knowledge; the design is its own._\n\n")
        f.write(design + "\n")
    print(SEP)
    print("THE JABBERWOCK'S DESIGN")
    print(SEP)
    print(design)
    print("\n" + SEP)
    print(f"  saved -> {os.path.relpath(out, ROOT)}")
    print(SEP)


if __name__ == "__main__":
    main()
