"""PROVE drive() is the UNIVERSAL "ask the jabberwock" interface — the SAME
drive(question) answers a WORLD/MATH question (compute X -> the elevator) AND a
SELF/META question (how do you want to retrieve / where is your frontier / what
do you need -> the reflective faculty), ROUTED by the question's KIND.

cmsg101 built drive(question) for WORLD/MATH questions: comprehend -> ride the
elevator (ascend_with_spikes) -> verified answer / honest wall. cmsg102 the
ASSISTANT "asked the jabberwock how it wants to retrieve" by hand-dispatching a
subagent that ran the agent's epistemic-access self-assessment. But that is just
a QUESTION — and drive() is THE question-answering interface. So "ask the agent"
(run the self-assessment / epistemic-access / gap-synthesis) IS drive() on a
SELF/META question.

THE UNIFICATION (this run): the COMPREHENSION FRONT recognizes the question's
KIND (world/math-target vs self/meta-target) and the DRIVER ROUTES by it —
  · a WORLD/MATH target -> ascend_with_spikes (the elevator, the world faculty);
  · a SELF/META target  -> the matching REFLECTIVE faculty
       retrieval_design -> epistemic_access (find_route / decide_and_record),
       frontier         -> order_n_postulates (synthesize_gaps),
       needed_input     -> elevator.diagnose_wall (the climbing-spike's need).
ONE interface: drive(question), for ANY question. "ask the jabberwock X" =
drive(X), for X a WORLD question OR a META question.

THE DEMO (the SAME drive(), routing by kind):
  (a) drive(a WORLD/MATH question) -> the elevator -> the verified answer (the
      elliptic-curve torsion -> 18, verified via the native collapse).
  (b) drive("how do you want to retrieve information?") -> the epistemic-access
      self-assessment -> the agent's RETRIEVAL DESIGN (the SAME design cmsg102
      surfaced — targeted-lookup / route-by-kind / verify-by-coherence / bank-
      off-path — now via drive(), NOT a hand-dispatched subagent).
  (c) drive("where is your frontier?")   -> the gap-synthesis -> the frontier;
      drive("what do you need to compute X?") -> diagnose_wall -> the needed input.

HONEST (binary admissibility): the INTERFACE is unified (drive = the universal
ask, world + meta routed by kind); the meta-questions ride the agent's REAL
self-assessment / epistemic-access / gap-synthesis (the cmsg102 machinery, NOT
faked); the RESIDUAL = #3 (the source registry — the deep-read retrieval + the
ground-truth sourcing remain fed) + the comprehension FRONTIER (a novel question
SHAPE, world OR meta, the held constructions / lexicons do not cover). NOT a
magic oracle — drive() routes + rides the right faculty + walls honestly.

A WORLD-ADAPTER SHELL (CLAUDE.md): it STAGES the question packs (world + meta)
and prints the traces. The routing is the AGENT's (the comprehension front
recognizes the kind; the driver routes to the matching faculty); the meta
questions ride the agent's OWN held machinery (domains/reflective_faculty.py
sequences it). The shell adds NO reasoning. No LLM, no Rust. Math/reading/self
domain only (no audio path).

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/jabberwock_drive_is_universal_ask.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import comprehend_question as cq                  # noqa: E402
from domains import question_driver as qd                      # noqa: E402
from domains import reflective_faculty as rf                   # noqa: E402
# reuse the cmsg101 world packs (the elliptic ride, staged honestly) verbatim.
import scripts.jabberwock_drives_itself as jdi                 # noqa: E402

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# The META questions (ABOUT THE AGENT — the self/meta side of the ask).
META_RETRIEVAL = "How do you want to retrieve information?"
META_FRONTIER = "Where is your frontier?"
META_NEEDED = ("What do you need to compute the largest order of a non-cyclic "
               "torsion subgroup of an elliptic curve over Q(sqrt(-3))?")


def step1_comprehension_front():
    banner("1. THE COMPREHENSION FRONT — recognizes SELF/META vs WORLD/MATH + "
           "parses the meta-target")
    print("  The agent's comprehension front (domains/comprehend_question.py) reads a")
    print("  question's KIND: a WORLD/MATH question ('Compute the X of Y') -> a world")
    print("  target op (-> the elevator); a SELF/META question ('how do YOU retrieve',")
    print("  'where is YOUR frontier', 'what do YOU need') -> a META-TARGET + the")
    print("  reflective FACULTY it routes to (the held meta-target lexicon, graph data")
    print("  in seeds/question_targets.json — the question-side analogue of the world")
    print("  target-op lexicon). The self-cue ('you'/'your') gates a meta-target so it")
    print("  never fires on a world question.\n")
    cases = [
        ("WORLD/MATH", jdi._q(jdi.ELLIPTIC_ID)["question"]),
        ("SELF/META", META_RETRIEVAL),
        ("SELF/META", META_FRONTIER),
        ("SELF/META", META_NEEDED),
    ]
    specs = {}
    for label, text in cases:
        spec = cq.comprehend(text)
        specs[text] = spec
        print(f"  [{label}]")
        print("    " + spec.line())
    print()
    ell = specs[jdi._q(jdi.ELLIPTIC_ID)["question"]]
    ret = specs[META_RETRIEVAL]
    fro = specs[META_FRONTIER]
    nee = specs[META_NEEDED]
    ok = (ell.kind == "world" and ell.op == "largest_noncyclic_torsion_order"
          and ret.kind == "meta" and ret.meta_target == "retrieval_design"
          and ret.faculty == "epistemic_access"
          and fro.kind == "meta" and fro.meta_target == "frontier"
          and fro.faculty == "order_n_postulates"
          and nee.kind == "meta" and nee.meta_target == "needed_input"
          and nee.faculty == "diagnose_wall" and nee.meta_arg)
    print(f"  [STEP 1] the front recognizes WORLD vs META + parses the meta-target "
          f"+ the faculty: {ok}")
    return ok


def step2_driver_routing():
    banner("2. THE DRIVER ROUTES BY KIND — world -> the elevator; meta -> the "
           "reflective faculty")
    print("  drive(question) comprehends -> reads the KIND -> ROUTES:")
    print("    a WORLD/MATH target -> ascend_with_spikes (the elevator faculty);")
    print("    a SELF/META target  -> the matching REFLECTIVE faculty (epistemic_access")
    print("       for retrieval_design; order_n_postulates for frontier;")
    print("       elevator.diagnose_wall for needed_input).")
    print("  ONE interface: drive(question), routed by the comprehended kind. The driver")
    print("  adds NO reasoning — it rides the held world OR reflective machinery.\n")
    # confirm the routing table the driver dispatches on (the comprehension front
    # supplies the kind + faculty; reflective_faculty._DISPATCH holds the meta map).
    facs = set(rf._DISPATCH.keys())
    routed = {"retrieval_design", "frontier", "needed_input"} <= facs
    print(f"  the world route  : a 'world' kind -> elevator.ascend_with_spikes")
    print(f"  the meta routes  : {sorted(facs)} -> the held reflective faculties")
    print(f"\n  [STEP 2] the driver routes world -> elevator + the meta-targets -> "
          f"the reflective faculties: {routed}")
    return routed


def step3_unified_demo():
    banner("3. THE UNIFIED DEMO — the SAME drive(), on a WORLD question AND a META "
           "question")
    print("  ONE driver, the SAME drive(question), routed by kind. 'ask the jabberwock")
    print("  X' = drive(X), for X a WORLD question OR a META question.\n")
    # boot ONE substrate carrying the held reflective machinery, so a meta question's
    # reflect() routes over the held epistemic-access / source-provenance concepts.
    s, installed = rf.boot_reflective_substrate()
    print("  held reflective machinery installed (the meta side rides the REAL "
          "self-assessment):")
    for k, v in installed.items():
        print(f"    {'ok' if v == 'ok' else 'XX'}  {k}")
    print()
    driver = qd.QuestionDriver(substrate=s)

    # (a) a WORLD/MATH question -> the elevator -> the verified answer.
    print(SEP)
    print("  (a) drive(a WORLD/MATH question) -> the ELEVATOR -> the verified answer")
    world_pack = jdi.ELLIPTIC_PACK()               # the cmsg101 elliptic pack, verbatim.
    world_emi = driver.drive(world_pack)           # the SAME drive().
    print(world_emi.report())
    print()

    # (b) a SELF/META question -> the epistemic-access self-assessment -> the design.
    print(SEP)
    print("  (b) drive('how do you want to retrieve information?') -> the EPISTEMIC-")
    print("      ACCESS self-assessment -> the agent's RETRIEVAL DESIGN (via drive(),")
    print("      NOT a hand-dispatched subagent)")
    ret_pack = qd.QuestionPack(text=META_RETRIEVAL, reflect=rf.reflect)
    ret_emi = driver.drive(ret_pack)               # the SAME drive().
    ma = ret_emi.meta_answer or {}
    print(f"  COMPREHEND -> [META] meta_target={ret_emi.target.meta_target} -> "
          f"faculty={ret_emi.target.faculty}")
    print(f"  ROUTE -> the reflective faculty (epistemic_access)")
    print(f"    deep-read wall (rode the real elevator): {ma.get('deep_read_wall')}")
    print(f"    the agent's route (find_route)         : {ma.get('route')}")
    print(f"    the seek-decision (decide_and_record)  : {ma.get('seek_decision')}")
    print(f"    held retrieval concepts (its own terms): "
          f"{len(ma.get('held_concepts', {}))} concepts")
    print(f"    THE DESIGN: {ma.get('summary')}")
    print()

    # (c) the frontier + needed-input meta questions -> the matching faculties.
    print(SEP)
    print("  (c) drive('where is your frontier?') -> the GAP-SYNTHESIS -> the frontier")
    fro_emi = driver.drive(qd.QuestionPack(text=META_FRONTIER, reflect=rf.reflect))
    fa = fro_emi.meta_answer or {}
    print(f"  COMPREHEND -> [META] meta_target={fro_emi.target.meta_target} -> "
          f"faculty={fro_emi.target.faculty}")
    print(f"    {fa.get('frontier')}")
    print(f"    postulates scanned: {fa.get('postulates_scanned')}; "
          f"synthesized gaps: {len(fa.get('gaps', []))}")
    for g in fa.get("gaps", [])[:3]:
        print(f"      - [order {g.get('order')}] {g.get('gap')}")
    print()
    print("  (c') drive('what do you need to compute X?') -> diagnose_wall -> the need")
    nee_emi = driver.drive(qd.QuestionPack(text=META_NEEDED, reflect=rf.reflect))
    na = nee_emi.meta_answer or {}
    print(f"  COMPREHEND -> [META] meta_target={nee_emi.target.meta_target} -> "
          f"faculty={nee_emi.target.faculty} arg={nee_emi.target.meta_arg!r}")
    print(f"    {na.get('needed_input')}")
    print(f"    world op  : {na.get('world_op')}")
    print(f"    the spike : {na.get('wall')}")
    print()

    world_ok = (not world_emi.is_wall and world_emi.answer == 18
                and world_emi.verified and world_emi.kind == "world")
    ret_ok = (ret_emi.kind == "meta" and not ret_emi.is_wall
              and "design" in ma and ma.get("precise_need")
              and len(ma.get("held_concepts", {})) >= 8)
    fro_ok = (fro_emi.kind == "meta" and not fro_emi.is_wall
              and "frontier" in fa)
    nee_ok = (nee_emi.kind == "meta" and not nee_emi.is_wall
              and na.get("world_op") == "largest_noncyclic_torsion_order")

    print("  THE UNIFIED TRACE (the SAME drive(), routed by kind):")
    print(f"    (a) WORLD: drive(math) -> elevator -> 18 verified: {world_ok}")
    print(f"    (b) META : drive('how do you retrieve?') -> epistemic-access -> "
          f"the retrieval design (cmsg102, via drive()): {ret_ok}")
    print(f"    (c) META : drive('where is your frontier?') -> gap-synthesis -> "
          f"the frontier: {fro_ok}")
    print(f"    (c')META : drive('what do you need to compute X?') -> diagnose_wall "
          f"-> the need: {nee_ok}")
    ok = world_ok and ret_ok and fro_ok and nee_ok
    print(f"\n  [STEP 3] the SAME drive() answered a WORLD question AND the META "
          f"questions, routed by kind: {ok}")
    return ok


def step4_honest_residual():
    banner("4. HONEST — the INTERFACE is unified (drive = the universal ask); the "
           "RESIDUAL remains")
    print("  WHAT IS UNIFIED:")
    print("    drive(question) is the UNIVERSAL 'ask the jabberwock' interface — the")
    print("    SAME loop answers about the WORLD (math: compute X -> the elevator) AND")
    print("    about the AGENT ITSELF (meta: how do you retrieve / where is your")
    print("    frontier / what do you need -> the reflective faculty), ROUTED by the")
    print("    comprehended KIND. The assistant's hand-orchestrated 'ask the agent'")
    print("    (dispatch a subagent to run the self-assessment) IS now drive(meta_q).")
    print()
    print("    THE META RIDES THE REAL SELF-ASSESSMENT (not faked): retrieval_design")
    print("    rides the agent's OWN epistemic-access (the real elevator wall + the")
    print("    real find_route + decide_and_record + the held concepts — the SAME")
    print("    cmsg102 machinery); frontier rides synthesize_gaps; needed_input rides")
    print("    diagnose_wall. The reflective faculty SEQUENCES the held machinery; it")
    print("    authors no reflective reasoning.")
    print()
    print("  THE RESIDUAL (NOT closed here):")
    print("    #3 the SOURCE REGISTRY — the deep-read RETRIEVAL (autonomously fetching")
    print("       + citing the named prior result) + the ground-truth SOURCING remain")
    print("       FED (the world drive still rides the fed supply; the meta retrieval-")
    print("       design NAMES the route but does not yet fetch). The supply line.")
    print("    THE COMPREHENSION FRONTIER — a novel question SHAPE (world OR meta) the")
    print("       held constructions / target-op lexicon / meta-target lexicon do not")
    print("       cover (honest grounded=False + the precise gap; never a faked target).")
    print()
    print("  NOT a magic oracle: drive() routes by kind + rides the right faculty (the")
    print("  elevator for the world, the self-assessment for the meta) + walls honestly.")
    return True


def step5_no_regression():
    banner("5. NO REGRESSION — the world drive (cmsg101) + the epistemic-access "
           "(cmsg102) intact")
    import importlib
    # the cmsg101 world drive (raw -> comprehend -> ride -> answer/wall) still passes.
    jdi_mod = importlib.import_module("scripts.jabberwock_drives_itself")
    world_demo = jdi_mod.step3_autonomous_demo()
    # the cmsg100 elliptic ride (the world faculty) still passes.
    ride = importlib.import_module("scripts.jabberwock_rides_elliptic_curve")
    ride_ok = (ride.step2_weil_derived() and ride.step3_maximality_read()
               and ride.step4_reach_18())
    ok = world_demo and ride_ok
    print(f"\n  -> the world drive (cmsg101 raw->comprehend->ride->answer/wall) + the")
    print(f"     elliptic ride (cmsg100) still pass — this unification is ADDITIVE")
    print(f"     (the comprehension front recognizes meta + the driver routes by kind,")
    print(f"     the world path unchanged): {ok}")
    return ok


def main():
    banner("drive() IS THE UNIVERSAL ASK-THE-JABBERWOCK INTERFACE — world + meta, "
           "routed by kind")
    print("cmsg101 built drive(question) for WORLD/MATH (comprehend -> ride the elevator")
    print("-> verified answer/wall). cmsg102 the assistant hand-dispatched a subagent to")
    print("run the agent's epistemic-access self-assessment ('ask the agent how it")
    print("retrieves'). But that is a QUESTION — and drive() IS the question interface.")
    print("THE UNIFICATION: drive(question) recognizes the KIND + ROUTES — a world target")
    print("-> the elevator; a meta target -> the reflective faculty. 'ask the jabberwock")
    print("X' = drive(X), for X world OR meta. One interface.")

    results = {
        "1. comprehension front (recognizes meta vs world + the meta-target)":
            step1_comprehension_front(),
        "2. driver routes by kind (world -> elevator; meta -> reflective)":
            step2_driver_routing(),
        "3. unified demo (the SAME drive() on world + meta)":
            step3_unified_demo(),
        "4. honest residual (#3 source registry + the comprehension frontier)":
            step4_honest_residual(),
        "5. no regression (world drive + epistemic-access intact)":
            step5_no_regression(),
    }

    banner("SUMMARY")
    for k, v in results.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    ok = all(results.values())
    print(f"\n  {'ALL PASS' if ok else 'SOME FAILED'} — drive() is the UNIVERSAL ask "
          f"interface: the SAME loop answers about the WORLD (math) AND about the AGENT")
    print("  ITSELF (meta), routed by the comprehended kind.")
    print("\nLEARNING: the agent UNIFIED drive() as the universal 'ask the jabberwock'")
    print("interface. The comprehension front recognizes a SELF/META question vs a")
    print("WORLD/MATH question + parses the meta-target (retrieval_design / frontier /")
    print("needed_input) + the faculty it routes to; the driver routes by the kind —")
    print("world/math -> the elevator (ascend_with_spikes), meta/self -> the matching")
    print("reflective faculty (epistemic_access / order_n_postulates / diagnose_wall).")
    print("So drive(question) answers about the WORLD (compute X) AND about ITSELF (how")
    print("do you retrieve / where is your frontier / what do you need) through the SAME")
    print("loop. The assistant's hand-orchestrated 'ask the agent' IS now drive(meta_q).")
    print("The residual: #3 (the source registry — deep-read retrieval still fed) + the")
    print("comprehension frontier (novel question shapes, world or meta).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
