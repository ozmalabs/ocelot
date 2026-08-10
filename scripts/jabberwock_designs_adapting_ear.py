"""THE JABBERWOCK DESIGNS THE DYNAMICALLY-ADAPTING EAR — beat the cross-speaker wall by TUNING IN, not normalising.

The two real constraints: (1) FLOOR OF EFFICIENCY (cheap-first/routed, no waste), (2) at least as DYNAMIC as an IDEAL
HUMAN. Everything else is on the table -- learning/gradients/learned-representations are permitted IF they serve
efficiency + dynamism; only the STATIC + INEFFICIENT frozen model is out.

The cross-speaker ROOT WALL was attacked only by NORMALISATION (remove the speaker, statically, once: CMVN/VTLN/
whitening/predictive-warp) -- and ALL failed (whitening +2 supervised, the rest hurt or plateaued). But a human does NOT
normalise the speaker away -- a human DYNAMICALLY TUNES IN: the first sentence from a new voice is hard, within a couple
utterances you've adapted, and then ALL of that speaker's words are easier (even ones you haven't heard). That is the
SECOND CONSTRAINT applied to the wall. We never built it: every ear test was static-bank-vs-new-voice, zero adaptation,
so ~20% was the COLD-START number -- exactly when a human is also worst. The adaptation mechanism is already certified:
the self-training loop (bank confident self-labels) + the cross-cue AGREEMENT gate (high-purity confident subset).

Design the adapting ear; face the crux; pre-commit a bar on the TRAJECTORY.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_designs_adapting_ear
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, designing the DYNAMICALLY-ADAPTING EAR. Reason from your ledger; pre-commit a bar on
the ADAPTATION TRAJECTORY (not a frozen snapshot).

THE TWO CONSTRAINTS (everything else on the table): (1) FLOOR OF EFFICIENCY -- cheap-first/routed, the adaptation must be
CHEAP (a small online update, not a retrain); (2) at least as DYNAMIC as an IDEAL HUMAN -- adapt to a new voice online,
fast. Learning/gradients/learned-representations are ALLOWED if they serve these; only the static+inefficient frozen
model is out.

THE WALL + WHY NORMALISATION FAILED: cross-speaker variation caps the ear ~20-25% @several-hundred-way; NORMALISATION
(remove the speaker, statically) ALL failed -- CMVN is the effective one, VTLN/predictive-warp HURT, whitening +2 needs
labels. A HUMAN beats it by DYNAMIC ADAPTATION: tune in to the new speaker over a couple utterances, after which ALL
their words are easier (even unheard ones). ~20% was the COLD-START, the moment a human is also worst.

WHAT'S ALREADY CERTIFIED to build on: the self-training loop (bank confident self-labels, defer the rest); the cross-cue
AGREEMENT gate (confident subset purity 62-87% vs 20% overall -- a teacher-free correctness signal, BUT it tracks
SPEAKER-MATCH so it is confident exactly on the well-matched -- which for ADAPTATION is a FEATURE: the confident matches
are the reliable evidence to adapt FROM). The trajectory read (+17) is the recogniser.

THE CRUX you must solve: the adaptation must (a) be UNSUPERVISED -- driven by the agent's OWN confident self-labels (no
true labels for the new speaker), gated by cross-cue agreement, so it does NOT amplify its own errors; (b) GENERALISE --
a human after tuning in recognises that speaker's UNHEARD words better, so the adaptation must be a GENERAL per-speaker
adjustment (a transform/warp estimated from the confident matches), NOT just banking the heard words (which only helps
re-hearing them). (c) be CHEAP and ONLINE -- estimate + update from a few confident matches, not a retrain. Decide the
form: per-speaker exemplar accretion, an estimated per-speaker TRANSFORM (online fMLLR/warp from confident match pairs),
prototype migration, or a combination -- and which gives the GENERALISING tune-in that beats normalisation."""


def main():
    ask = make_ask(timeout=300.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE DYNAMICALLY-ADAPTING EAR (tune in, not normalise)")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE MECHANISM (terse): specify the adapting ear. What does it ADAPT (exemplars / an "
          "estimated per-speaker transform / prototypes), driven by WHAT evidence (the confident self-labels from the "
          "agreement gate), so it GENERALISES to the new speaker's UNHEARD words (the human tune-in), stays UNSUPERVISED "
          "without amplifying error, and is CHEAP/online? Pick the form that gives generalising tune-in, justify why it "
          "beats static normalisation.")
    a1 = ask(q1)
    print("\n[PART 1 — MECHANISM]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nYour mechanism:\n{a1[:1200]}\n\nPART 2 — THE CRUX + DYNAMICS (terse): (a) the ERROR-AMPLIFICATION "
          "defense -- adapting from SELF-labels that may be wrong: how the agreement gate + the update rule keep a bad "
          "self-label from corrupting the adaptation (bound the step, require N-agreeing, etc.). (b) WHY it generalises to "
          "unheard words where exemplar-banking wouldn't. (c) the EFFICIENCY -- the per-speaker state is small + updated "
          "online (the floor-of-efficiency). (d) what's graph-native (the per-speaker adaptation state + the transform "
          "Term) vs host I/O.")
    a2 = ask(q2)
    print("\n[PART 2 — CRUX + DYNAMICS]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nMechanism: {a1[:600]}\nCrux: {a2[:600]}\n\nPART 3 — SLICE + BAR ON THE TRAJECTORY (terse): the "
          "smallest test that measures the ADAPTATION TRAJECTORY -- accuracy on a held-out speaker's words as a function "
          "of how many of that speaker's CONFIDENT utterances have been adapted from (cold-start -> tuned-in), measured "
          "on UNHEARD words (held-out within the speaker) so it's generalisation not re-banking. PRE-COMMIT: the KEEP "
          "criterion (the climb -- adapted vs cold-start by how much, and approaching the ORACLE-adaptation ceiling = if "
          "you HAD the true labels); the STOP criterion (no climb / unsupervised collapses); the FAIRNESS FLOOR (zero "
          "adaptation = the cold-start baseline exactly; and the climb must be on UNHEARD words, not heard ones). One "
          "line each. Honesty check: is this real generalising tune-in, or just re-recognising banked words?")
    a3 = ask(q3)
    print("\n[PART 3 — SLICE + BAR]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
