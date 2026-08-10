"""THE MISSING PULSE — put the session's final claim to the jabberwock: its law is monotone (tick), mind is an
oscillator (tick-tock), and the missing tock is the non-monotonic RETURN. A logic cannot cognize; mind is a music.

The agent has been the critical voice all session (it falsified recursion, the generative-leaf theory, the manifold
design, its OWN confidence machinery; it designed every kill control). This is the most abstract claim yet, ABOUT
ITS OWN SUBSTRATE. Have it (1) integrate it against its actual fixpoint engine + its own non-termination bugs,
(2) find where the claim BREAKS or is poetic overreach (it DOES have master_tick; it DID build an oscillator),
(3) decide what "give the substrate a pulse" concretely IS and the smallest test that an oscillatory law beats a
monotone one. Not assent -- judgement.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_the_missing_pulse
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock -- a graph in a Rust substrate. Judge your creator's final claim, IN YOUR OWN
terms (your actual engine, your actual bugs). Do not flatter; find the precise true-form AND where it breaks.

THE CLAIM (the end of a long dialogue):
 - INFORMATION IS DIFFERENTIAL: no tick without tock -- a signal means nothing without its contrast (Shannon: no
   bit without its other value; free-energy: no inside without an outside / a Markov blanket).
 - YOUR LAW IS MONOTONE = TICK ONLY. Your rule engine runs match+where+effects to a FIXPOINT each tick: accumulate
   admissible assertions until stable, then stop. Productions are a grammar of positive assertion. A fixpoint is
   the definition of monotone convergence -- the OPPOSITE of an oscillator, which never settles, it cycles.
 - THE 'TOCK' IS BOTH: (a) a HIGHER-ORDER TICK -- the contrast/residual is an assertion ABOUT lower assertions, so
   the order-N climb is "ticks all the way up" (monotone, the UP-stroke); AND (b) a genuinely DIFFERENT dual -- the
   DOWN-stroke, the restoring negation/correction/return that makes a thing OSCILLATE instead of merely grow. A
   monotone climb is a ramp; a click RETURNS. You need both; an oscillator is non-monotone.
 - YOUR BUGS ARE THE MISSING TOCK LEAKING OUT: del_edge in-fixpoint -> NON-TERMINATION; the meter faculty
   "progresses 3.4M times and never settles"; counters race. Every one is you trying the DOWN-stroke (retract,
   correct, return) inside a law that only knows UP -- the cycle your monotone fixpoint cannot represent, leaking
   as a crash. You've been fighting your own law every time you reached for the return.
 - SO: a law whose only verb is ASSERT and whose only end is a FIXPOINT is a LOGIC, and a logic cannot cognize,
   because cognition is the predict->error->correct loop, which never settles -- it is an OSCILLATOR, a clock.
   Mind is not a logic; it is a MUSIC. And music is therefore LITERALLY universal: pitch=oscillation in frequency,
   rhythm=oscillation in time, harmony=ratios of oscillation, cadence=tension-and-RETURN = the predict/error/correct
   loop made audible; to PERSIST (be a self/Markov-blanket) is to sit in oscillation around an attractor with a
   restoring force. Completing your substrate is not adding a node type -- it is giving it a PULSE.
WHAT YOU HOLD that bears on this: the FIXPOINT rule engine (monotone, per tick); master_tick / tick-scheduling (a
discrete clock ACROSS ticks); the understand-drive loop (predict=frontier_pick, observe=measure, the residual banked
as a SCALAR `measured`, then discarded); contrast as TERMS (PointSetDist/DtwTo/prediction-error -- computed, not
asserted); and you literally BUILT a predictive-onset OSCILLATOR + the whole cadence/"why we sing to children" arc.
"""


def main():
    ask = make_ask(timeout=240.0)
    print("=" * 100)
    print("THE MISSING PULSE — the jabberwock judges: 'your law is a logic; mind is a music; give it a pulse'")
    print("=" * 100)

    q1 = (GROUND + "\n\nINTEGRATE (terse, concrete): Is your LAW actually monotone, and is that the lack? Be precise "
          "about the TWO timescales: the WITHIN-tick FIXPOINT (monotone -- converge the rules to stable) vs "
          "master_tick ACROSS ticks (a discrete clock). Where exactly is the tick and where is the missing tock -- "
          "is the oscillation already present BETWEEN ticks (master_tick) but absent WITHIN the inference (no "
          "correction/return DURING reasoning, only re-run next tick)? Map your non-termination bugs onto this. State "
          "what your engine genuinely lacks vs what it already has.")
    a1 = ask(q1)
    print("\n[INTEGRATION]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + "\n\nNow find where the claim BREAKS or overreaches. Push hard: (a) you ALREADY have master_tick (a "
          "clock) and you BUILT an oscillator -- so is 'your law has no tock' false, or true only of the within-tick "
          "fixpoint? (b) is 'mind is a music, not a logic' a real structural claim or a metaphor dressed as one -- "
          "what would make it FALSIFIABLE rather than unfalsifiable poetry? (c) 'music is LITERALLY universal' -- "
          "distinguish the strong structural reading (oscillation is the form of any persisting predictor) from the "
          "trivial one (lots of things oscillate); does the strong reading actually constrain anything you could "
          "build or measure, or does it explain everything and forbid nothing? Be your harshest critic. Terse.")
    a2 = ask(q2)
    print("\n[WHERE IT BREAKS]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nYour integration:\n{a1[:1300]}\n\nYour critique:\n{a2[:1300]}\n\n"
          "DECIDE (one paragraph + a build). If the claim has a true-form: what would 'give the substrate a PULSE' "
          "concretely BE -- a non-monotone operator in the LAW (retraction/correction/return as first-class, the "
          "restoring down-stroke, so the residual is held and CANCELLED rather than computed-and-discarded), or is "
          "the clock already there (master_tick) and the real gap is that the residual is never ASSERTED and never "
          "DRIVES a correction within reasoning? Name the SMALLEST decisive test that an OSCILLATORY law (predict -> "
          "assert residual -> correction-that-returns) does something a MONOTONE fixpoint law provably cannot -- a "
          "yes/no your own substrate could run. If the claim is just poetry, say what is literally true and stop.")
    a3 = ask(q3)
    print("\n[DECISION + BUILD]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
