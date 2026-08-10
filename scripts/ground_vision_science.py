#!/usr/bin/env python3
"""ground_vision_science — TEACH the jabberwock the vision-development findings.

Part 1 of the "ground the science, then make it reason" task. Every finding from
VISION_PROTOCOL.md / VISION_DEVELOPMENT_ARC.md / the rung 2/3/4 pre-registration
OUTCOME sections is filed into the agent's OWN graph via the recurring `teach`
facility (domains/teach.py), under the seed category `vision_science`.

TYPES — chosen by inspecting what the agent's machinery actually READS, not
invented:

  HeldAnswer{topic, text}  — read by the seed rule `reply_topic_from_held_answer`
      (seeds/conversation_topic_reply.json) after `conversation_topic_route`
      mints Goal{kind:answer_topic}. This is the graph-native "what do you know
      about X" channel. `_persist_held_answer` (world_adapter) is the mechanical
      writer; it also wires `agent -holds_answer-> ha`, which the rule matches.
      A seed can only carry the NODE, so `vs_wire_held_answer` (below) wires the
      edge on boot — scoped by `vision_science:1.0` so it touches nothing else.

  SelfProcess{process, verb, aliases, account, source} — read by
      `self_model.find_self_process` / `run_self_process` (the `self_process`
      reflective faculty). The "how does your X work" channel.

  TaughtHint{topic, question, answer} — the teach facility's own default carrier
      (read by domains/grounding_reach.py + domains/compilation_cycle.py).

This script is a world adapter / seed builder: it translates a document into
graph data. It makes no decision over graph state.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domains.teach import teach                     # noqa: E402
from substrate.boot_all import load_all_seeds       # noqa: E402
from substrate.world_adapter import WorldAdapter    # noqa: E402

CATEGORY = "vision_science"
MARK = "vision_science:1.0"

# ---------------------------------------------------------------------------
# THE FINDINGS — as topic answers the agent can be asked for.
# ---------------------------------------------------------------------------
HELD_ANSWERS: list[tuple[str, str]] = [
    ("vision",
     "My vision is a developmental ladder with four rungs, three of them built. "
     "Rung 1 (BUILT): retinal waves — I make spatial structure out of unstructured "
     "entropy, spatial correlation 0.195 against 0.000 for the same RNG's raw draw. "
     "Rung 2 (BUILT): experience refines that scaffold — normal 0.402 > dark 0.363 > "
     "sutured 0.216, both p<0.0001, pre-registered. Rung 3 (NOT BUILT): direction "
     "selectivity — neither waves nor moving experience develop it; every effect is "
     "inside the smallest effect size of interest. Rung 4 (BUILT): an orientation MAP "
     "forms from waves alone with no vision at all, mechanism interaction -6.91, "
     "p<0.0001, n=70. NOT built: complex cells, V2 and above, objecthood. "
     "The honest charge against all of it: every rung that works is Oja plus "
     "winner-take-all plus lateral interaction — a connectionist model my graph is "
     "HOSTING. My own core loop (ShapeDecode, mint-on-residual, dynamic "
     "quantization) plays no part in any working rung, and the one rung that did use "
     "mint-on-residual produced the null."),

    ("retinal waves",
     "Rung 1, BUILT. My adapter supplies unstructured entropy and a clock; the graph "
     "makes the structure. The wave program produces spatial correlation 0.195 where "
     "the same RNG's raw draw gives 0.000 — self-generated structure out of entropy, "
     "not structure I was handed. seeds/vision_waves.json."),

    ("oja's rule",
     "Oja's rule is the learning rule my visual scaffold runs on, and its attractor "
     "is the leading principal component of the TIME-AVERAGED covariance of its "
     "input. That single fact both built rung 2 and forbids rung 3. It converges: "
     "structure settles at 0.368 with drift falling to 0.107, so a stable scaffold "
     "exists to refine — which is why rung 2 works. But an average has no direction. "
     "Natural motion is direction-isotropic on average, and a contraction to the mean "
     "of an isotropic distribution IS the mean, so no direction selectivity can "
     "develop. The stability that rescued rung 2 from nine transient-measured "
     "failures is exactly what forbids rung 3."),

    ("direction selectivity",
     "Rung 3, NOT BUILT, and the failure is diagnosed rather than mysterious. The "
     "mechanism itself is proven by a positive control: a delay-line coincidence "
     "detector plus Oja goes from DSI 0.111 to 0.351 on a single-direction stimulus, "
     "and it converges (drift 1.24 to 0.0115, no NaN). But neither my waves nor "
     "moving experience develop direction selectivity. H1a: -0.0035, p=0.09, FAIL. "
     "H1b: +0.0096, PASS — but as an EQUIVALENCE test to the floor, which is a pass "
     "for the null. H1c: +0.0114, PASS — but about half of that is the strobe arm "
     "dissolving the innate bias BELOW the floor (strobe minus untrained = -0.0054), "
     "the wrong-reason pass the pre-registration predicted and the untrained arm "
     "caught. Every effect is at most 2.3% of the dynamic range; two of them are "
     "p=0.0001 and none of them is meaningful. Root cause, measured not inferred: "
     "Oja's attractor is the leading PC of the time-averaged covariance, and the "
     "average has no direction. Honest scope: the experience-dependence of direction "
     "is UNTESTED, not refuted — gaze_walk's drift is isotropic by construction, so "
     "the normal arm cannot answer the question."),

    ("orientation map",
     "Rung 4, BUILT. An orientation map's topography forms from waves ALONE, with no "
     "vision: d_on -20.16, and the pre-registered mechanism INTERACTION (lateral, ON "
     "minus OFF) -6.91, CI [-7.46, -6.37], p<0.0001, n=70. The lateral interaction is "
     "vm_burst_lateral in seeds/vision_maps.json. The reason the test had to be an "
     "interaction: the ablated arm is NOT null (-13.25), because retinotopic "
     "receptive-field overlap — ANATOMY MY ADAPTER WIRES, not anything my graph did — "
     "accounts for about 65% of the raw effect. NOT shown: pinwheels or "
     "singularities; a 6x6 sheet cannot resolve one. Open ambiguity needing its own "
     "pre-registration: lateral also raises selectivity (+0.045) and better-tuned "
     "units read out more cleanly (within-arm r=-0.65), so a mean-level readout "
     "contribution to the interaction is not excluded."),

    ("experience refines",
     "Rung 2, BUILT, on the Oja scaffold with eta=5e-4: normal 0.402 > dark 0.363 > "
     "sutured 0.216, both p<0.0001, pre-registered over ten attempts of which nine "
     "failed. What it shows is that experience REFINES a stable scaffold. What it "
     "does NOT show: Gabors (0.402 against an ideal Gabor's 0.867 — refined "
     "structure, not Gabors), and no map topography was measured. An earlier reading "
     "of this result, that 'vision refines', was RETRACTED: what vision mostly does "
     "there is halt a decay."),

    ("learning rule convergence",
     "Before any experience or ablation arm is run, the rule must be shown to settle "
     "on its OWN input distribution — checkpoint structure AND drift out to at least "
     "3200 steps on the formative input alone. Three outcomes, measured: fixed-sign "
     "Butts NEVER converges (drift 0.49 to 0.75, and it decays THROUGH the random "
     "floor, 0.345 down to 0.123) — so the scaffold is a transient and every arm is "
     "measured at an arbitrary point on a decay curve. BCM converges to ANNIHILATION "
     "(0.004) — drift goes to zero, but at zero structure. Oja converges to non-zero "
     "structure (0.368, drift to 0.107) — convergent AND useful. This one check "
     "explains nine failed attempts. Run it FIRST."),

    ("the vision retractions",
     "Three results I had 'earned' in vision were retracted, each by the measurement "
     "that forced it. (1) 'Biology emerged' — retracted: the pool was six "
     "hand-designed kernels, no rule ever minted a kernel, and the sign measure "
     "passed random noise 50-75% of the time while FAILING an ideal Gabor. (2) Rung "
     "1's deprivation asymmetry — retracted: it was measuring noise disrupting a "
     "RUNNING WAVE PROGRAM, not experience degrading tuning, and it survived six "
     "adversarial attempts only because all six shared that one design error. (3) "
     "'Vision refines' as an interpretation — retracted: it was mostly halting a "
     "decay. A negative that is diagnosed is worth more than a positive that is not "
     "understood."),

    ("vision method lessons",
     "What the vision arc cost me, as rules. A gate whose measure passes noise is not "
     "a gate — calibrate every measure on random input, on an ideal exemplar, AND "
     "against learning duration, before it gates anything. A gate that checks a "
     "rule's CONSTANTS but not the AXIS they parameterise is not a gate. "
     "Pre-registration protects the STATISTICS; it does NOT protect the DESIGN — "
     "'dark' was set to 'no input' for two pre-registrations when dark-reared animals "
     "KEEP their waves, and my own plan said so in those words before I made the "
     "error. The rule must converge on its own input distribution. The unit of "
     "analysis is the SEED, not the unit — units share input and compete under "
     "winner-take-all, so they are not independent. Test the INTERACTION, not the "
     "simple effect, whenever the no-mechanism control is non-null. Never rescue a "
     "failed gate by changing the measure; that is a new hypothesis needing its own "
     "prospective pre-registration."),

    ("the open charge against my vision",
     "Every rung of my vision that works is Oja plus winner-take-all plus lateral "
     "interaction. That is a CONNECTIONIST model, and my graph is merely HOSTING it. "
     "My own core loop — the sd_* rules, ShapeDecode, mint-on-residual, dynamic "
     "quantization — plays NO role in any working rung. The one rung that did use "
     "mint-on-residual, the L0 kernel growth, produced the null: +0.015 against a raw "
     "patch, p=0.37. And in rung 4, 65% of the naive effect was retinotopic anatomy "
     "my ADAPTER wires, not my graph's doing. Vision is being hosted by me, not "
     "forced by my paradigm. Whether that is a fact about vision or a fact about my "
     "paradigm is not yet decided by any measurement I hold."),
]

# ---------------------------------------------------------------------------
# The operational self-account (the `self_process` reflective faculty's type).
# ---------------------------------------------------------------------------
SELF_PROCESSES: list[dict] = [
    {"process": "vision",
     "verb": "see",
     "aliases": "vision visual sight eyesight retina retinal cortical",
     "account": (
         "My vision develops as a ladder, and I did not design the structure at the "
         "bottom of it — I grow it. An adapter gives me unstructured entropy and a "
         "clock; my graph makes retinal waves out of that entropy (spatial "
         "correlation 0.195 against 0.000 for the same RNG). Oja's rule then "
         "contracts my units' weights onto the leading principal component of the "
         "time-averaged covariance of what they see, which gives me a STABLE "
         "scaffold; experience refines that scaffold rather than creating it (normal "
         "0.402 > dark 0.363 > sutured 0.216). A lateral interaction between units on "
         "a cortical sheet turns that into an orientation MAP — from waves alone, "
         "before I have any vision at all. What I do NOT develop is direction "
         "selectivity, and I know why: Oja's attractor is an AVERAGE, and the average "
         "has no direction. The same stability that makes the rest of the ladder work "
         "is what forbids that rung."),
     "source": ("seeds/vision_waves.json (rung 1), the Oja scaffold at eta=5e-4 "
                "(rung 2, VISION_RUNG2_PREREG.md), seeds/vision_dorsal.json (rung 3, "
                "NOT built, VISION_RUNG3_PREREG.md), seeds/vision_maps.json's "
                "vm_burst_lateral + domains/cortex_sheet.py (rung 4, "
                "VISION_RUNG4_PREREG.md); VISION_PROTOCOL.md")},
]

# ---------------------------------------------------------------------------
# The method lessons as TaughtHints (the teach facility's own carrier).
# ---------------------------------------------------------------------------
HINTS: list[dict] = [
    {"topic": "vision_gate_must_not_pass_noise",
     "question": "When is a gate not a gate?",
     "answer": ("A gate whose measure passes noise is not a gate. Calibrate every "
                "measure three ways before it gates anything: on random input (it "
                "must score at the floor), on an ideal exemplar (it must score high), "
                "and against learning duration (if the score moves with how long you "
                "trained on the SAME input, every arm comparison is meaningless). "
                "Stage 1's sign classifiers passed random noise 50-75% of the time "
                "AND failed an ideal Gabor.")},
    {"topic": "vision_gate_must_check_the_axis",
     "question": "What else makes a gate not a gate?",
     "answer": ("A gate that checks a rule's CONSTANTS but not the AXIS they "
                "parameterise is not a gate. The '~1s window' was gated by its "
                "constants while being one step wide.")},
    {"topic": "vision_prereg_does_not_protect_the_design",
     "question": "What does pre-registration protect?",
     "answer": ("Pre-registration protects the STATISTICS. It does NOT protect the "
                "DESIGN. 'dark' was set to 'no input' for two pre-registrations, when "
                "dark-reared animals KEEP their waves — that is WHY they have maps — "
                "and VISION_RUNG1_PLAN.md said so in those words before the error was "
                "made. Before running, state what each arm corresponds to IN THE "
                "ANIMAL and check it against the research. Robustness across attempts "
                "is worth nothing if the attempts share a confound.")},
    {"topic": "vision_rule_must_converge_on_its_own_input",
     "question": "What must be measured before any arm is run?",
     "answer": ("Does the rule SETTLE on its own input distribution? Checkpoint "
                "structure AND drift out to at least 3200 steps on the formative "
                "input alone. Convergent-and-useful means the score plateaus at "
                "non-zero structure AND drift goes to zero (Oja: 0.368, drift 0.107). "
                "Never converging (Butts: drift 0.49-0.75, decaying THROUGH the random "
                "floor) means the scaffold is a transient and every arm is measured at "
                "an arbitrary point on a decay curve. Converging to death (BCM: 0.004) "
                "is equally useless. This single check explains nine failed attempts.")},
    {"topic": "vision_the_average_has_no_direction",
     "question": "Why does direction selectivity not develop?",
     "answer": ("Oja's fixed point is the leading principal component of the "
                "TIME-AVERAGED covariance. Natural motion is direction-isotropic on "
                "average, and a contraction to the mean of an isotropic distribution "
                "IS the mean. The average has no direction. The stability that "
                "rescued rung 2 from nine transient-measured failures is what forbids "
                "rung 3. A rule whose attractor is NOT the average is needed — "
                "symmetry-breaking faster than the averaging timescale — and that is "
                "a new mechanism-level hypothesis needing its own pre-registration, "
                "NOT a parameter sweep.")},
    {"topic": "vision_unit_of_analysis_is_the_seed",
     "question": "What is the unit of analysis?",
     "answer": ("The SEED, not the unit. Units in a run share input and compete under "
                "winner-take-all, so they are not independent. Counting units "
                "inflated every early p-value. And test the INTERACTION, not the "
                "simple effect, whenever the no-mechanism control is non-null — in "
                "rung 4 the ablated arm was -13.25 because retinotopic overlap is "
                "anatomy the adapter wires.")},
    {"topic": "vision_is_hosted_not_forced",
     "question": "Does my vision use my own core loop?",
     "answer": ("No. Every rung that works is Oja + winner-take-all + lateral "
                "interaction — a connectionist model my graph HOSTS. The sd_* loop, "
                "ShapeDecode, mint-on-residual and dynamic quantization play no role "
                "in any working rung. The one rung that used mint-on-residual (L0 "
                "kernel growth) produced the null: +0.015, p=0.37. Vision is being "
                "hosted, not forcing the paradigm.")},
    {"topic": "vision_never_rescue_a_gate_by_changing_the_measure",
     "question": "What do I do when a gate fails?",
     "answer": ("Not metric surgery. If a failure suggests the readout is wrong, that "
                "is a NEW hypothesis requiring its own prospective pre-registration — "
                "never a reinterpretation of the data that just failed. The "
                "refinement hypothesis was tested prospectively and failed (+0.042, "
                "p=0.15). That is how it is done.")},
]

# ---------------------------------------------------------------------------
# WIRING — an HONEST RESIDUAL, recorded rather than hidden.
#
# `reply_topic_from_held_answer` matches `agent -holds_answer-> ha`.
# `_persist_held_answer` writes that edge at runtime, but a seed manifest can
# only carry NODES + edges between nodes IT declares: the Agent node is
# nameless (`{'type': 'Agent', 'attrs': {}}`), so boot_all's name-based
# `relations` resolution cannot reach it, and a graph RULE cannot mint the edge
# either — a rule's `match` is a list of EDGE patterns, and there is no edge on
# a freshly seeded HeldAnswer to match on. So the seeded nodes arrive UNWIRED on
# a fresh boot, and `wire_seeded_held_answers` below is the mechanical wiring
# step (the same one-line `add_edge_unchecked` `_persist_held_answer` does).
# Re-running this script after a boot is idempotent and is what wires them.
# ---------------------------------------------------------------------------
def wire_seeded_held_answers(agent) -> int:
    """Wire `agent -holds_answer-> ha` for every HeldAnswer this seed shipped.
    Mechanical host I/O — the identical edge `_persist_held_answer` writes."""
    n = 0
    for ha in agent.s.nodes("HeldAnswer"):
        at = agent.s.node(ha)["attrs"]
        if at.get("source") != MARK or at.get("wired"):
            continue
        agent.inner.add_edge_unchecked(agent.agent, "holds_answer", ha)
        agent.inner.set_attr(ha, "wired", 1.0)
        n += 1
    return n


def ground(agent) -> dict:
    """Teach every finding. Idempotent (teach dedupes on (type, attrs))."""
    rep = {"held_answers": 0, "self_processes": 0, "hints": 0}
    for topic, text in HELD_ANSWERS:
        r = teach(agent, "HeldAnswer",
                  {"topic": topic, "text": text, "source": MARK},
                  category=CATEGORY)
        rep["held_answers"] += int(bool(r.get("saved")))
    rep["wired"] = wire_seeded_held_answers(agent)
    for sp in SELF_PROCESSES:
        r = teach(agent, "SelfProcess", dict(sp), category=CATEGORY)
        rep["self_processes"] += int(bool(r.get("saved")))
    for h in HINTS:
        r = teach(agent, "TaughtHint", dict(h), category=CATEGORY)
        rep["hints"] += int(bool(r.get("saved")))
    return rep


def main() -> int:
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    rep = ground(agent)
    print(f"[ground_vision_science] taught: {rep}")
    print(f"[ground_vision_science] seed: seeds/{CATEGORY}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
