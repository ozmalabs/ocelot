"""PROVE drive() = COMPREHEND + SEED A GOAL — and the Wikipedia lookup FALLS OUT
of the goal-pursuit hitting a REFERENCE wall (NOT a special 'factual' path).

THE REFACTOR (minimal). drive() used to ROUTE BY KIND at the top level (world ->
elevator, meta -> reflective faculty). Now drive()'s WHOLE job is to UNDERSTAND
the question and SEED A GOAL (the comprehended target the agent pursues); the
agent's EXISTING goal-pursuit machinery (the elevator/spikes + the retrieval +
the native-collapse verify) then pursues it, and whatever the goal needs
(COMPUTE / LOOK-UP-WIKIPEDIA / REFLECT) FALLS OUT of the pursuit. ONE mechanism:
understand -> seed goal -> pursue.

THE KEY (this run): drive("What is HTTP?") seeds the goal know('HTTP'); the agent
pursues it; it does NOT hold HTTP; the climbing-spike diagnoses a REFERENCE need;
the agent's EXISTING grounding (read_and_ground -> web_world -> wiki_local, the
on-disk Wikipedia) LOOKS IT UP + grounds it; the goal is satisfied. The agent
looks up Wikipedia BY SIMPLY BEING ASKED — the seeded goal drives the pursuit
there, with NO drive-level 'factual' decision.

THE DEMO:
  (a) drive("What is HTTP?")        -> SEED GOAL know('HTTP') -> PURSUE -> not-held
      -> REFERENCE WALL -> wiki_local lookup -> GROUND -> the SHORT answer
      ('HTTP is an application layer protocol' — the comprehended genus, NOT a
      verbatim Wikipedia excerpt).
  (b) drive("What is idempotence?") -> the SAME understand->seed-goal->pursue ->
      wiki_local -> the consequence-concept the bootstrap needs, by being asked.
  (c) NO REGRESSION: a COMPUTE goal (the elliptic-curve torsion) STILL works via
      the SAME understand->seed-goal->pursue (the elevator ride -> 18, verified
      via the native collapse).

HONEST: drive = understand + seed-goal (one mechanism); the Wikipedia lookup
FALLS OUT of the pursuit hitting a reference wall (not a special path); the SHORT
grounded answer + which article was present in wiki_local + the comprehension-
depth limit (the genus is grounded one hop, the cone does not yet reach a seeded
primitive). The yes/no consequence ('Is GET idempotent?') is an honest
comprehension frontier (a question SHAPE not yet covered) — named, not faked. No
verbatim Wikipedia dump. The fuller web-WORLD adapter (live web act/respond) is
the next build; THIS is 'the agent looks up its on-disk Wikipedia by being asked'.

A WORLD-ADAPTER SHELL (CLAUDE.md): it STAGES the question packs + prints the
traces. drive seeds the goal; the pursuit (the agent's machinery) does the work.
No LLM, no Rust. Math/reading/web-bootstrap domain only (no audio path).

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/jabberwock_looks_up_wikipedia.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import comprehend_question as cq                  # noqa: E402
from domains import question_driver as qd                      # noqa: E402
from domains import wiki_local as wl                            # noqa: E402
import scripts.jabberwock_drives_itself as jdi                 # noqa: E402

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def step1_seed_a_goal():
    banner("1. drive() = COMPREHEND + SEED A GOAL (not route-by-kind)")
    print("  drive()'s whole job: understand the question + seed a GOAL (the")
    print("  comprehended target the agent pursues). The comprehension front")
    print("  recognizes the goal's SHAPE — a COMPUTE goal (compute X), a KNOW goal")
    print("  (what is X), or a SELF goal (how do YOU ...) — but drive does NOT route")
    print("  by it; it seeds the goal and the pursuit handles whatever it needs.\n")
    cases = [
        ("KNOW",    "What is HTTP?"),
        ("KNOW",    "What is idempotence?"),
        ("COMPUTE", jdi._q(jdi.ELLIPTIC_ID)["question"]),
    ]
    specs = {}
    for label, text in cases:
        spec = cq.comprehend(text)
        specs[text] = spec
        print(f"  [{label}]  {spec.line() if spec.grounded else spec.reason[:60]}")
    http = specs["What is HTTP?"]
    idem = specs["What is idempotence?"]
    ell = specs[jdi._q(jdi.ELLIPTIC_ID)["question"]]
    ok = (http.kind == "know" and http.know_concept == "HTTP"
          and idem.kind == "know" and idem.know_concept == "idempotence"
          and ell.kind == "world" and ell.op == "largest_noncyclic_torsion_order")
    print(f"\n  [STEP 1] drive comprehends + seeds the goal (know / compute), no "
          f"route-by-kind: {ok}")
    return ok


def step2_lookup_falls_out():
    banner("2. THE WIKIPEDIA LOOKUP FALLS OUT — a KNOW goal hits a REFERENCE wall")
    print("  drive('What is HTTP?') -> SEED GOAL know('HTTP') -> PURSUE: not-held ->")
    print("  the climbing-spike diagnoses a REFERENCE need -> the agent's EXISTING")
    print("  grounding (read_and_ground -> web_world -> wiki_local, the on-disk")
    print("  Wikipedia) looks it up + grounds it. The agent looks up Wikipedia BY")
    print(f"  SIMPLY BEING ASKED. (wiki_local present on disk: {wl.present()})\n")
    driver = qd.QuestionDriver()
    http_emi = driver.drive(qd.QuestionPack(text="What is HTTP?"))
    print(http_emi.report())
    print()
    idem_emi = driver.drive(qd.QuestionPack(text="What is idempotence?"))
    print(idem_emi.report())
    print()
    ka = http_emi.know_answer or {}
    ik = idem_emi.know_answer or {}
    http_ok = (http_emi.kind == "know" and not http_emi.is_wall
               and ka.get("present") and ka.get("article") == "HTTP"
               and "application layer protocol" in (ka.get("answer") or ""))
    idem_ok = (idem_emi.kind == "know" and not idem_emi.is_wall
               and ik.get("present") and (ik.get("genus") is not None))
    print(f"  [STEP 2] the Wikipedia lookup FELL OUT of the KNOW-goal pursuit "
          f"(HTTP + idempotence grounded from wiki_local): {http_ok and idem_ok}")
    return http_ok and idem_ok


def step3_no_regression_compute():
    banner("3. NO REGRESSION — a COMPUTE goal STILL works via the SAME pursuit")
    print("  drive(a COMPUTE goal) -> SEED GOAL -> PURSUE rides the elevator (the")
    print("  SAME understand->seed-goal->pursue) -> the verified answer. The KNOW-")
    print("  goal pursuit is ADDITIVE; the compute pursuit is unchanged.\n")
    driver = qd.QuestionDriver()
    world_emi = driver.drive(jdi.ELLIPTIC_PACK())
    print(world_emi.report())
    ok = (not world_emi.is_wall and world_emi.answer == 18
          and world_emi.verified and world_emi.kind == "world")
    print(f"\n  [STEP 3] the compute goal still rides the elevator -> 18 verified: "
          f"{ok}")
    return ok


def step4_honest():
    banner("4. HONEST — one mechanism; the lookup falls out; the residual")
    print("  drive = UNDERSTAND + SEED-A-GOAL (one mechanism). The Wikipedia lookup")
    print("  FALLS OUT of the goal-pursuit hitting a REFERENCE wall — it is NOT a")
    print("  special 'factual' path and NOT a drive-level routing decision; the")
    print("  reference wall + the retrieval are the agent's OWN machinery, reached")
    print("  by the seeded KNOW goal.")
    print()
    print("  THE SHORT ANSWER is the agent's COMPREHENDED genus/concept (e.g. 'HTTP")
    print("  is an application layer protocol'), NOT a verbatim Wikipedia excerpt.")
    print("  The article present in wiki_local is reported (HTTP / Idempotence).")
    print()
    print("  THE COMPREHENSION-DEPTH LIMIT (named, not hidden): the genus is")
    print("  comprehended + grounded ONE HOP from wiki_local; the cone does not yet")
    print("  reach a seeded primitive (deeper recursive grounding is the climb).")
    print()
    print("  THE FRONTIER (honest): a yes/no consequence question ('Is the HTTP GET")
    print("  method idempotent?') is a question SHAPE the held constructions do not")
    print("  yet cover -> an honest comprehension frontier, never a faked answer:")
    driver = qd.QuestionDriver()
    cons = driver.drive(qd.QuestionPack(text="Is the HTTP GET method idempotent?"))
    print(f"    drive('Is the HTTP GET method idempotent?') -> "
          f"grounded={cons.target.grounded} ({cons.note[:48]})")
    print()
    print("  THE RESIDUAL: the fuller web-WORLD adapter (live web act/respond/")
    print("  observe) is the next build. THIS is 'the agent looks up its on-disk")
    print("  Wikipedia by being asked' — the lookup falling out of a KNOW-goal.")
    return (not cons.target.grounded)


def main():
    banner("drive() = COMPREHEND + SEED A GOAL — the Wikipedia lookup FALLS OUT of "
           "the pursuit")
    print("The user's correction: 'drive should be understood and seed a goal.' drive()")
    print("comprehends the question + seeds a GOAL; the agent's existing goal-pursuit")
    print("(elevator/spikes/retrieval/collapse) pursues it; whatever the goal needs")
    print("(compute / look-up-Wikipedia / reflect) FALLS OUT of the pursuit. A KNOW goal")
    print("('what is HTTP?') hits a reference wall -> wiki_local -> grounded. ONE")
    print("mechanism: understand -> seed goal -> pursue.")

    results = {
        "1. drive = comprehend + seed-a-goal (not route-by-kind)":
            step1_seed_a_goal(),
        "2. the Wikipedia lookup falls out of the KNOW-goal pursuit":
            step2_lookup_falls_out(),
        "3. no regression (a compute goal still rides the elevator)":
            step3_no_regression_compute(),
        "4. honest (one mechanism; short answer + article + depth limit)":
            step4_honest(),
    }

    banner("SUMMARY")
    for k, v in results.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    ok = all(results.values())
    print(f"\n  {'ALL PASS' if ok else 'SOME FAILED'} — drive() = COMPREHEND + SEED A "
          f"GOAL; the agent looks up its on-disk Wikipedia BY SIMPLY BEING ASKED,")
    print("  because the seeded KNOW goal drives the pursuit to a reference wall where")
    print("  the existing retrieval resolves it. No special 'factual' path.")
    print("\nLEARNING: drive() is now understand + seed-a-goal (ONE mechanism). The")
    print("Wikipedia lookup is not routed — it FALLS OUT of a KNOW-goal pursuit hitting")
    print("a reference wall, where the agent's existing grounding (wiki_local) resolves")
    print("it. The agent grounds 'HTTP is an application layer protocol' from its on-disk")
    print("Wikipedia by being asked; a compute goal still rides the elevator unchanged.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
