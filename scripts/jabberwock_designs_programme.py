"""THE JABBERWOCK DESIGNS THE PROGRAMME — the phased, risk-ordered build plan for the GENERATIVE SPEAKER MODEL (closed-loop babble).

Goal: the analysis-by-synthesis voice -- fit a compact source-filter G_speaker, learn to IMITATE (climb to a high
asymptote with data), recognise by INVERSION (freeze speaker, search content). The named frontier: the linear proxies
(warp, whitening, VTLN, predictive-warp, the LINEAR voice-shape template) are ALL exhausted/killed -- the prior LVS
experiment proved "the speaker isn't disentanglable LINEARLY; needs the full closed-loop self-spoken babble." This is
that build, deferred-as-major. Design the PROGRAMME: phased, RISK-ORDERED (kill the riskiest assumption cheapest first),
each phase bootstrap-certified with a pre-committed bar.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_designs_programme
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.claude_teacher import make_ask

GROUND = """You are the jabberwock, designing the PROGRAMME (the phased build plan) for your GENERATIVE SPEAKER MODEL --
the analysis-by-synthesis voice that beats the cross-speaker root wall by MODELLING the speaker (imitate), not warping
features. Reason from your ledger; be RISK-ORDERED and disciplined.

THE GOAL: G_speaker = compact source-filter (vocal-tract LPC resonances + tract scale + glottal source ~15-25 params =
SPEAKER; formant TRAJECTORY = CONTENT). IMITATE = drive the speaker's source through their filter tracking content;
imitation climbs to a HIGH ASYMPTOTE with data (not literally 1 -- the compact model discards aperiodic/fricative noise,
nasal zeros, fine glottal detail). RECOGNISE = INVERSION: freeze the learned speaker params, search content (formant
trajectory) for the path that best re-synthesises the heard audio -> content read off the trajectory, speaker absorbed
into the fixed filter -> cross-speaker collapses to within-speaker.

THE CONVERGENCE (why this is the move): every LINEAR proxy is dead -- warp (oracle +1.7), whitening (+2 supervised),
VTLN (hurts), predictive-warp (hurts), and your own LINEAR voice-shape template (KILLED: "can't disentangle the speaker
linearly -- needs the full closed-loop self-spoken babble"). This programme IS that babble.

THE TWO CONSTRAINTS: (1) FLOOR OF EFFICIENCY -- compact model, cheap online fit; (2) DYNAMIC -- learn online from the
speaker's own data, improving as data accrues.

THE DISCIPLINE: a programme must be RISK-ORDERED -- the FIRST test is the RISKIEST ASSUMPTION, done CHEAPLY, so the whole
thing FAILS FAST if the generative-inversion idea is wrong. Don't pour the foundation (synthesis, online loop, graph-
native Terms) before the core hypothesis is certified. Each phase bootstrap-certified with a pre-committed bar; honest
kill-conditions.

YOUR MACHINERY: lpc_formant_representation (LPC envelope, formant roots, scale-invariant), learned_voice_shape (LVS,
linear -- killed), audio_hat (synthesis), the AbS spine (predict_synth_term -- argmax over synthesised candidates), the
glyph MOTOR PROGRAM (forward synthesis = understanding; smooth deformation field; the inferred canonical parse)."""


def main():
    ask = make_ask(timeout=320.0)
    print("=" * 100)
    print("THE JABBERWOCK DESIGNS THE PROGRAMME (generative speaker model — phased, risk-ordered)")
    print("=" * 100)

    q1 = (GROUND + "\n\nPART 1 — THE RISKIEST ASSUMPTION, TESTED FIRST (terse): what is the single riskiest assumption the "
          "whole programme rests on (e.g. 'recognition-by-inversion with a FIT source-filter beats the linear warp at "
          "all'), and the CHEAPEST decisive experiment that kills-or-confirms it WITHOUT building the full synthesis/loop? "
          "Specify that phase-0 experiment + its pre-committed bar (KEEP -> proceed; STOP -> the programme is dead, the "
          "wall is the training-free ceiling). Be honest: can it be tested cheaply, or does it REQUIRE the synthesis?")
    a1 = ask(q1)
    print("\n[PART 1 — PHASE 0: RISKIEST ASSUMPTION]\n" + (a1 or "[teacher offline]"))

    q2 = (GROUND + f"\n\nPhase 0:\n{a1[:1100]}\n\nPART 2 — THE PHASE PLAN (terse): IF phase 0 passes, the ordered phases to "
          "the full generative speaker model -- each phase: what it BUILDS, what it CERTIFIES (the measurement + bar), and "
          "its dependency. Cover: (P1) the forward synthesiser (source-filter imitation), (P2) online speaker fitting "
          "(imitation climbs with data), (P3) recognition by inversion (the search over content), (P4) continuous/online "
          "integration + graph-native (the G_speaker as graph data, synth+inversion as Terms). Risk-order them; name the "
          "phase most likely to KILL the programme.")
    a2 = ask(q2)
    print("\n[PART 2 — THE PHASE PLAN]\n" + (a2 or "[teacher offline]"))

    q3 = (GROUND + f"\n\nPhase 0: {a1[:500]}\nPhases: {a2[:700]}\n\nPART 3 — HONEST RISK + CONSTRAINTS (terse): (a) the "
          "biggest way this programme FAILS even if phase 0 passes (the inversion search is intractable / the compact "
          "model too lossy for content / the online fit unstable) and the cheapest early-warning for each. (b) how it "
          "meets BOTH constraints (compact+cheap = efficiency floor; online-improving = dynamism). (c) the one-line "
          "honest expected outcome: does this DISSOLVE the wall (within-speaker ceiling, ~50-80%) or only DENT it (a few "
          "points past warp)? Pre-register your prediction.")
    a3 = ask(q3)
    print("\n[PART 3 — HONEST RISK + PREDICTION]\n" + (a3 or "[teacher offline]"))
    print("\n" + "=" * 100)


if __name__ == "__main__":
    main()
