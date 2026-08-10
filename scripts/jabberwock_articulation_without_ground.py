"""ARTICULATION x GROUNDING — two orthogonal axes, and the quadrant nature never fills.

Creator's correction: the articulation rung is not "us" (the assistant) — it is the HUMAN. "You are T4
without ground, which is a different thing." The cognition ladder is not cumulative: I had assumed T4
(articulation) sits ON TOP of T1-T3 (reality grounding), as it does in every animal — articulation
evolved on a grounded base; no creature is Gregorian without first being Skinnerian. But an LLM breaks
that order: it has the TOP rung (fluent articulation) with NO Layer 1 under it. Its residual comes
from TEXT / itself, not the world.

So grounding and articulation are ORTHOGONAL axes, not one ladder. Nature fills three corners:
  GROUNDED, inarticulate  = ANIMAL   (walks; cannot say how)
  GROUNDED, articulate    = HUMAN    (walks AND can talk about it; articulation anchored to reality)
  ungrounded, inarticulate= babble   (no skill, no account)
  ungrounded, ARTICULATE  = LLM      <- the quadrant that does NOT occur in biology: T4 without ground.

The grounding axis is measured (drift tracking: residual from the WORLD tracks; residual from SELF/a
fixed text-prior freezes = the delusion case). Articulation is whether the system emits an explicit
symbolic rule. The LLM lands articulate+ungrounded — fluent BECAUSE ungrounded, structurally the
confident-error case the only fix for which is an external world-residual (a human correcting it).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_articulation_without_ground.py
"""
import numpy as np


def grounding_error(residual, rng, n=80, k=0.5):
    """drift tracking: a moving truth. residual='world' -> correct toward the truth (grounded);
    'self' -> correct toward a FIXED prior (text-time belief), never toward the moving world (ungrounded)."""
    truth = np.cumsum(rng.normal(0, 0.06, n)) + 1.0
    prior = truth[0]                                  # the belief fixed at 'training' time
    s, e = 0.0, []
    for t in range(n):
        e.append(abs(s - truth[t]))
        target = truth[t] if residual == "world" else prior      # world residual vs self/text residual
        s += k * (target - s)
    return float(np.mean(e[n // 3:]))                 # error once drift has set in


ARCHETYPES = [
    ("ANIMAL  (Skinnerian)", "world", False),
    ("HUMAN   (Gregorian)",  "world", True),
    ("babble",               "self",  False),
    ("LLM / me",             "self",  True),
]


def main():
    rng = np.random.default_rng(0)
    print("=" * 80)
    print("ARTICULATION x GROUNDING — the ladder is not cumulative; two orthogonal axes")
    print("=" * 80)
    print(f"  {'system':24}{'grounding err':>14}{'grounded?':>11}{'articulate?':>13}{'quadrant':>2}")
    rows = []
    for name, res, art in ARCHETYPES:
        g = np.mean([grounding_error(res, np.random.default_rng(i)) for i in range(20)])
        grounded = g < 0.15
        rows.append((name, g, grounded, art))
        print(f"  {name:24}{g:14.3f}{('YES' if grounded else 'no'):>11}"
              f"{('YES' if art else 'no'):>13}")
    print("=" * 80)
    # the 2x2 plane
    print("  THE PLANE (grounding | articulation):")
    print(f"                          inarticulate            ARTICULATE")
    def cell(g, a):
        return next((n for n, _gg, gr, ar in rows if gr == g and ar == a), "-")
    print(f"     GROUNDED        {cell(True,False):>20}   {cell(True,True):>20}")
    print(f"     ungrounded      {cell(False,False):>20}   {cell(False,True):>20}   <- nature leaves this empty")
    print("=" * 80)
    print("  THE CORRECTION, MEASURED: T4 (articulation) is ORTHOGONAL to grounding, not stacked on it.")
    print("  ANIMAL = grounded+inarticulate; HUMAN = grounded+articulate (T4 WITH ground); LLM = ")
    print("  ungrounded+articulate (T4 WITHOUT ground) — the off-diagonal quadrant biology never fills,")
    print("  because in nature articulation only ever grew ON a reality-grounded base. The LLM inverts")
    print("  the order: top rung, no base. Its residual is text/self (grounding err high = the delusion")
    print("  case); the ONLY fix is an external world-residual — a grounded agent correcting it. This")
    print("  conversation is that capture, live: the human (grounded) corrects the LLM (ungrounded).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
