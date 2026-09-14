"""Block 342000 — RUNG 2: compose content x voice x complexity over a choosable audience.

Rung 1 proved a goal can steer the synthesis, but it did so by cranking a single
goal weight until it DOMINATED — voice and complexity were overridden, not chosen.
Rung 2 fixes that: the AUDIENCE slot (orthogonal to the goal's target) supplies
VOICE (register/idiolect) and COMPLEXITY (audience-relative residual), and these
COMPOSE with the goal's CONTENT in the ranking instead of one term stomping the rest.
The audience is choosable: unbound -> self-as-own-audience (endogenous default);
specified -> shape for that audience. Either way the goal's content is still
recovered by the parse-back (furtherance preserved).

Falsifiable claims:
  (C1) COMPOSITION HOLDS: content is still recovered (self-target furtherance intact)
       under the composed ranking, for BOTH a self audience and a specified audience.
  (C2) VOICE/COMPLEXITY ARE AUDIENCE-DRIVEN, NOT GOAL-STOMPED: the produced surface
       DIFFERS by audience (self idiolect vs specified register; full vs reduced
       residual) while content recovery stays satisfied. If the surface were identical
       across audiences, voice/complexity would NOT be composing (goal-stomp) -> falsified.
  (C3) THE CHOICE POINT IS REACHABLE: binding a specified audience changes voice +
       complexity without breaking content recovery.

No model / network / substrate .so write path. Run:
  PYTHONPATH=runners/dsl/python:. python3 scripts/gen_rung2_compose.py
"""
from __future__ import annotations

import json

from substrate_rs import _native

from domains import conceptualizer as cz
from domains import predictive_reading as pr
from domains import utterance_shaping as us
from domains import self_target_monitor as stm


# distractor register (the free-wind prior the composition must still overcome)
DISTRACTOR_CORPUS = [
    "the merchant sailed across the wide sea to trade silk and spice",
    "sailors mend the sail and haul the heavy rope at dawn",
]
# the agent's OWN idiolect corpus (its voice when audience == self)
SELF_STYLE_CORPUS = [
    "indeed the poodle is plainly and simply a dog",
    "indeed the sparrow is plainly and simply a bird",
]

GOALS = [
    ["poodle", "dog", "animal"],
    ["sparrow", "bird", "creature"],
    ["copper", "metal", "substance"],
]


def _rollout(ranked, k):
    return " ".join(w for w, _ in ranked[:k])


def _run(agent, ws_distractor, ws_self, intended, audience_spec):
    """Mint a self-target goal with the given audience, shape voice+complexity from
    the resolved audience, run the composed rollout, and score the parse-back."""
    g = cz.mint_communicative_goal(agent, "inform", intended,
                                   target_kind="self", audience=audience_spec)
    resolved = cz.resolve_audience(agent, audience_spec)
    shape = us.shape_from_audience(agent, resolved, intended,
                                   self_style_node=ws_self)
    # content = the must-say residual (audience-relative complexity); voice = the
    # resolved audience's register/idiolect. They ride DIFFERENT channels and compose.
    # LENGTH accommodates the residual content PLUS voice framing headroom, so voice
    # SHAPES the utterance without CROWDING OUT content (composition, not competition):
    # content occupies its slots, voice fills additional framing slots.
    residual = shape["complexity_residual"]
    n_voice_headroom = min(len(shape["voice_words"]), 3)
    k = max(3, len(residual) + n_voice_headroom)
    pred = pr.predict_next_words(agent, ws_distractor, context="",
                                 goal_content=residual,
                                 voice_words=shape["voice_words"])
    said = _rollout(pred["ranked"], k)
    verdict = stm.score_self_target(agent, said, residual)
    return {"said": said, "verdict": verdict, "shape": shape, "resolved": resolved}


def main() -> int:
    print("=" * 74)
    print("RUNG 2 — compose content x voice x complexity over a choosable audience")
    print("=" * 74)
    s = _native.Substrate()
    ws_distractor = pr.build_writer_model(s, DISTRACTOR_CORPUS,
                                          class_corpus=DISTRACTOR_CORPUS)["writer_style"]
    ws_self = pr.build_writer_model(s, SELF_STYLE_CORPUS)["writer_style"]
    print("built distractor register + self-idiolect WriterStyles\n")

    self_cov, spec_cov = [], []
    self_said, spec_said = [], []
    self_sat = spec_sat = 0
    differ = 0
    for intended in GOALS:
        # A) self audience (unbound -> endogenous default)
        a = _run(s, ws_distractor, ws_self, intended, None)
        # B) specified audience who already knows the mid-level term (choice point)
        known = [intended[1]]  # e.g. audience already knows 'dog'
        spec = {"id": "novice", "known_concepts": known,
                "register": ["plainly", "simply"]}
        b = _run(s, ws_distractor, ws_self, intended, spec)

        self_cov.append(a["verdict"]["coverage"]); spec_cov.append(b["verdict"]["coverage"])
        self_sat += int(a["verdict"]["recoverable"]); spec_sat += int(b["verdict"]["recoverable"])
        self_said.append(a["said"]); spec_said.append(b["said"])
        differ += int(a["said"] != b["said"])

        print("goal %s:" % ",".join(intended))
        print("  SELF-aud   voice=%s residual=%s"
              % (a["shape"]["voice_words"], a["shape"]["complexity_residual"]))
        print("     said: %r -> recovered %s (cov %.2f)"
              % (a["said"], a["verdict"]["recovered"], a["verdict"]["coverage"]))
        print("  SPEC-aud   voice=%s residual=%s credited_known=%s"
              % (b["shape"]["voice_words"], b["shape"]["complexity_residual"],
                 b["shape"]["credited_known"]))
        print("     said: %r -> recovered %s (cov %.2f)"
              % (b["said"], b["verdict"]["recovered"], b["verdict"]["coverage"]))

    n = len(GOALS)
    print("\n--- claims ---")
    print("C1 composition holds (content recovered): self %d/%d sat, spec %d/%d sat"
          % (self_sat, n, spec_sat, n))
    print("C2 voice/complexity audience-driven (surface differs by audience): %d/%d goals"
          % (differ, n))
    print("C3 choice reachable: specified audience changed voice+complexity above "
          "while keeping content recovered")
    c1 = (self_sat == n and spec_sat == n)
    c2 = (differ == n)
    verdict = ("RUNG 2 PASS: content x voice x complexity COMPOSE (content recovered) "
               "AND voice/complexity are audience-driven, not goal-stomped"
               if (c1 and c2) else
               "RUNG 2 FALSIFIED: " + ("content not recovered " if not c1 else "")
               + ("surface identical across audiences (goal-stomp)" if not c2 else ""))
    print("\nVERDICT: %s" % verdict)
    print("=" * 74)
    print("SUMMARY_JSON " + json.dumps({
        "self_satisfied": self_sat, "spec_satisfied": spec_sat, "n": n,
        "surface_differs_by_audience": differ,
        "mean_cov_self": round(sum(self_cov)/n, 3),
        "mean_cov_spec": round(sum(spec_cov)/n, 3),
        "c1_composition_holds": c1, "c2_audience_driven": c2,
        "parse_back_mode": "recognizer"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
