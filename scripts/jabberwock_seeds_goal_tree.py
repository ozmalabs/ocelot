"""PROVE drive() seeds ARBITRARY GOALS AND SUBGOALS — a RECURSIVE decompose-or-
resolve over a GOAL/SUBGOAL TREE. The user's instruction: "drive should be able
to seed arbitrary goals and subgoals."

THE GENERALIZATION (minimal). cmsg107 made drive() = COMPREHEND + SEED A GOAL,
and the goal-pursuit resolved a FLAT goal via the faculty that falls out
(compute -> elevator / know -> wiki_local / self -> reflective). This run makes
the pursuit RECURSIVE/HIERARCHICAL:

    pursue(goal) =
      (a) RESOLVE-IF-LEAF  — a leaf resolves via the faculty that fits:
            a held/COMPUTE leaf -> the elevator; a KNOW leaf -> wiki_local;
            a SELF leaf -> the reflective faculty.
      (b) DECOMPOSE         — a COMPOUND goal seeds a child Goal per SUBGOAL
            (parent -has_subgoal-> child, REAL graph data) + pursues each
            RECURSIVELY (`_pursue` on the subgoal — which itself decomposes-or-
            resolves) + composes.

A SUBGOAL IS A GOAL (the same TargetSpec, recursively). This GENERALIZES the
elevator's reduce->recurse (which already recurses for MATH goals: reduce ->
recurse on sub-ops -> resolve a held leaf) to ARBITRARY goals where a LEAF can
resolve via ANY faculty (not just held-math) — MIXED-faculty leaves in one tree.

THE DEMO:
  (a) A COMPOUND goal with MIXED-faculty subgoals: drive('What is HTTP and
      <the elliptic torsion>') -> SEED a COMPOUND goal -> DECOMPOSE into
      [ know('HTTP') -> wiki_local -> grounded ;
        compute(torsion) -> the elevator -> 18 verified ] -> COMPOSE. The SAME
      pursuit, MIXED-faculty leaves; the goal TREE is real graph data.
  (b) A DEPTH-2+ tree: drive('What is HTTP and what is idempotence and what is
      cryptography') -> the decomposition NESTS ([ know(HTTP),
      compound[ know(idempotence), know(cryptography) ] ]) — a subgoal seeds
      sub-subgoals (depth-2), the SAME decompose-or-resolve recursively.
  (c) NO REGRESSION: a FLAT goal still works (drive('What is HTTP?') ->
      wiki_local; drive(the compute goal) -> the elevator -> 18).

HONEST: drive seeds arbitrary goals; the pursuit recursively seeds subgoals
(decompose-or-resolve); a leaf resolves via the faculty that fits; the goal/
subgoal TREE is the unified mechanism. The residual: the DECOMPOSITION limit
(which goals the comprehension can decompose — a novel/compound SHAPE is the
comprehension frontier, the same wall) + the leaf-resolution limits (the
comprehension-depth for a KNOW leaf; the deep-reads for a COMPUTE leaf). SHORT
grounded concepts, NOT verbatim Wikipedia.

A WORLD-ADAPTER SHELL (CLAUDE.md): it STAGES the question packs + prints the
goal tree. drive seeds the root goal; the pursuit (the agent's machinery — the
elevator's recursion + the cmsg107 faculty-leaves) does the work. No LLM, no
Rust. Math/reading/web-bootstrap domain only (no audio path).

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/jabberwock_seeds_goal_tree.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import comprehend_question as cq                  # noqa: E402
from domains import question_driver as qd                      # noqa: E402
import scripts.jabberwock_drives_itself as jdi                 # noqa: E402

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def _goal_tree(driver):
    """Walk the GOAL TREE in the graph (parent -has_subgoal-> child) as real graph
    data the pursuit seeded. Returns the printable tree + its max depth."""
    s = driver.s
    roots = [n for n in s.nodes("Goal") if not s.in_neighbours(n, "has_subgoal")]
    lines = []
    maxd = [0]

    def walk(n, d=0):
        maxd[0] = max(maxd[0], d)
        a = s.node(n)["attrs"]
        label = a.get("concept") or a.get("op") or (
            f"subgoals={a.get('subgoals')}" if a.get("kind") == "compound" else "")
        lines.append(f"    {'  ' * d}Goal {n} kind={a.get('kind')}  {label}")
        for c in s.neighbours(n, "has_subgoal"):
            walk(c, d + 1)

    for r in roots:
        walk(r)
    return "\n".join(lines), maxd[0]


def step1_recursive_pursue():
    banner("1. THE GENERALIZATION — pursue(goal) is RECURSIVE (resolve-if-leaf OR "
           "decompose)")
    print("  pursue(goal) = (a) RESOLVE if a LEAF (a held/COMPUTE leaf -> the")
    print("  elevator; a KNOW leaf -> wiki_local; a SELF leaf -> the reflective")
    print("  faculty) OR (b) DECOMPOSE a COMPOUND goal into SUBGOALS (seed a child")
    print("  Goal per subgoal) + pursue each RECURSIVELY + compose. A SUBGOAL IS A")
    print("  GOAL (the same TargetSpec, recursively). This GENERALIZES the elevator's")
    print("  reduce->recurse to ARBITRARY goals with MIXED-faculty leaves.\n")
    # the comprehension recognizes a COMPOUND goal + decomposes it into subgoals.
    ell = jdi._q(jdi.ELLIPTIC_ID)["question"]
    spec = cq.comprehend("What is HTTP and " + ell)
    print(f"  comprehend('What is HTTP and <elliptic torsion>') -> {spec.line()}")
    for sg in spec.subgoals:
        print(f"    subgoal: {sg.line()}")
    ok = (spec.kind == "compound" and len(spec.subgoals) == 2
          and {sg.kind for sg in spec.subgoals} == {"know", "world"})
    print(f"\n  [STEP 1] a COMPOUND goal comprehends into MIXED-faculty subgoals "
          f"(know + world): {ok}")
    return ok


def step2_mixed_faculty_tree():
    banner("2. THE GOAL/SUBGOAL TREE — a COMPOUND goal -> MIXED-faculty subgoals "
           "-> composed")
    print("  drive('What is HTTP and <elliptic torsion>') -> SEED a COMPOUND goal ->")
    print("  DECOMPOSE -> [ know('HTTP') -> wiki_local ; compute(torsion) -> the")
    print("  elevator ] -> COMPOSE. The SAME pursuit, MIXED-faculty leaves.\n")
    ell = jdi._q(jdi.ELLIPTIC_ID)["question"]
    base = jdi.ELLIPTIC_PACK()                  # the cmsg100 elliptic supply, verbatim.
    pack = qd.QuestionPack(
        text="What is HTTP and " + ell,
        feed=base.feed, deep_reads=base.deep_reads,
        verify=base.verify, answer_call=base.answer_call)
    driver = qd.QuestionDriver()
    emi = driver.drive(pack)
    print(emi.report())
    print()
    tree, depth = _goal_tree(driver)
    print("  THE GOAL TREE (real graph data — parent -has_subgoal-> child):")
    print(tree)

    subs = emi.subgoals
    know = next((c for c in subs if c.kind == "know"), None)
    comp = next((c for c in subs if c.kind == "world"), None)
    know_ok = (know is not None and not know.is_wall
               and "application layer protocol" in
               ((know.know_answer or {}).get("answer") or ""))
    comp_ok = (comp is not None and not comp.is_wall
               and comp.answer == 18 and comp.verified)
    ok = (emi.target.kind == "compound" and not emi.is_wall
          and know_ok and comp_ok and depth >= 1)
    print(f"\n  THE TREE (the SAME pursuit, MIXED-faculty leaves):")
    print(f"    KNOW subgoal  -> wiki_local -> 'HTTP is an application layer "
          f"protocol' (SHORT, not verbatim): {know_ok}")
    print(f"    COMPUTE subgoal -> the elevator -> 18 (verified): {comp_ok}")
    print(f"    composed (every subgoal resolved by its faculty): {not emi.is_wall}")
    print(f"\n  [STEP 2] the goal/subgoal tree resolved with MIXED-faculty leaves: "
          f"{ok}")
    return ok


def step3_depth_2_tree():
    banner("3. A DEPTH-2+ TREE — a subgoal seeds SUB-SUBGOALS (the same recursion)")
    print("  drive('What is HTTP and what is idempotence and what is cryptography')")
    print("  -> the decomposition NESTS: [ know(HTTP), compound[ know(idempotence),")
    print("  know(cryptography) ] ] — a SUBGOAL seeds SUB-SUBGOALS (depth-2), the")
    print("  SAME decompose-or-resolve recursively. All KNOW leaves -> wiki_local.\n")
    driver = qd.QuestionDriver()
    emi = driver.drive(qd.QuestionPack(
        text="What is HTTP and what is idempotence and what is cryptography"))
    print(emi.report())
    print()
    tree, depth = _goal_tree(driver)
    print("  THE GOAL TREE (depth-2 — a subgoal seeded sub-subgoals):")
    print(tree)

    # the root is compound; one subgoal is itself a compound (the sub-subgoals).
    sub_compound = any(c.kind == "compound" for c in emi.subgoals)
    ok = (emi.target.kind == "compound" and sub_compound and depth >= 2
          and not emi.is_wall)
    print(f"\n  [STEP 3] the goal tree reached DEPTH {depth} (a subgoal seeded "
          f"sub-subgoals), all leaves resolved: {ok}")
    return ok


def step4_no_regression():
    banner("4. NO REGRESSION — a FLAT goal still works (cmsg107 unchanged)")
    print("  A flat KNOW goal (drive('What is HTTP?') -> wiki_local) and a flat")
    print("  COMPUTE goal (the elliptic torsion -> the elevator -> 18) still work")
    print("  via the SAME pursuit — the recursion is ADDITIVE (a flat goal is a")
    print("  leaf; decompose only fires for a COMPOUND goal).\n")
    driver = qd.QuestionDriver()
    http = driver.drive(qd.QuestionPack(text="What is HTTP?"))
    comp = driver.drive(jdi.ELLIPTIC_PACK())
    print("  drive('What is HTTP?'):")
    print(http.report())
    print()
    print("  drive(the elliptic compute goal):")
    print(comp.report())
    http_ok = (http.kind == "know" and not http.is_wall and not http.subgoals
               and (http.know_answer or {}).get("article") == "HTTP")
    comp_ok = (comp.kind == "world" and not comp.is_wall and not comp.subgoals
               and comp.answer == 18 and comp.verified)
    ok = http_ok and comp_ok
    print(f"\n  [STEP 4] a flat KNOW goal ({http_ok}) + a flat COMPUTE goal "
          f"({comp_ok}) still resolve (no regression): {ok}")
    return ok


def step5_honest():
    banner("5. HONEST — one decompose-or-resolve mechanism; the residual")
    print("  WHAT IS GENERAL NOW: drive seeds ARBITRARY goals; the pursuit RECURSIVELY")
    print("  seeds SUBGOALS (decompose-or-resolve per node); a LEAF resolves via the")
    print("  faculty that fits (compute -> elevator / know -> wiki_local / self ->")
    print("  reflective); the goal/subgoal TREE (real Goal nodes + has_subgoal edges)")
    print("  is the unified mechanism. The elevator's reduce->recurse for MATH is now")
    print("  the SAME recursion over arbitrary goals with MIXED-faculty leaves.")
    print()
    print("  THE RESIDUAL (named, not hidden):")
    print("    · the DECOMPOSITION limit — which goals the comprehension can decompose")
    print("      into subgoals. A novel/compound SHAPE the held constructions do not")
    print("      cover is the comprehension FRONTIER (the same wall) — honest, never a")
    print("      faked decomposition:")
    driver = qd.QuestionDriver()
    novel = driver.drive(qd.QuestionPack(
        text="Compare HTTP with FTP in terms of statefulness"))
    print(f"        drive('Compare HTTP with FTP ...') -> grounded="
          f"{novel.target.grounded if novel.target else False} "
          f"(the decomposition frontier — not a compound 'and' shape)")
    print("    · the LEAF-resolution limits — the comprehension-DEPTH for a KNOW leaf")
    print("      (the genus is grounded one hop from wiki_local, the cone does not yet")
    print("      reach a seeded primitive) + the DEEP-READS for a COMPUTE leaf (the")
    print("      supply line still fed).")
    print()
    print("  SHORT grounded concepts (the comprehended genus), NOT verbatim Wikipedia.")
    return (novel.target is None or not novel.target.grounded)


def main():
    banner("drive() SEEDS ARBITRARY GOALS AND SUBGOALS — a RECURSIVE decompose-or-"
           "resolve over a GOAL TREE")
    print("The user's instruction: 'drive should be able to seed arbitrary goals and")
    print("subgoals.' cmsg107 made drive() = comprehend + seed a (FLAT) goal. This")
    print("generalizes the pursuit to RECURSIVE/HIERARCHICAL: pursue(goal) = resolve-if-")
    print("leaf OR decompose-into-subgoals + pursue-each + compose. A SUBGOAL IS A GOAL")
    print("(the same structure, recursively); a LEAF resolves via the faculty that fits")
    print("(compute -> elevator / know -> wiki_local / self -> reflective). The elevator")
    print("ALREADY recurses for math; this generalizes it to arbitrary goals with MIXED-")
    print("faculty leaves. The subgoals are real Goal graph nodes (parent -has_subgoal-> "
          "child).")

    results = {
        "1. the generalization (pursue recursive: resolve-if-leaf OR decompose)":
            step1_recursive_pursue(),
        "2. the goal tree (a compound goal -> MIXED-faculty subgoals -> composed)":
            step2_mixed_faculty_tree(),
        "3. a depth-2+ tree (a subgoal seeds sub-subgoals, the same recursion)":
            step3_depth_2_tree(),
        "4. no regression (a flat goal still works)":
            step4_no_regression(),
        "5. honest (one mechanism; the decomposition + leaf-resolution residual)":
            step5_honest(),
    }

    banner("SUMMARY")
    for k, v in results.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    ok = all(results.values())
    print(f"\n  {'ALL PASS' if ok else 'SOME FAILED'} — drive() seeds ARBITRARY goals "
          f"+ RECURSIVE subgoals: one decompose-or-resolve mechanism over a goal/")
    print("  subgoal tree, the leaves resolved by their MIXED faculties.")
    print("\nLEARNING: drive() now seeds ARBITRARY GOALS AND SUBGOALS. pursue(goal) is")
    print("RECURSIVE — resolve-if-leaf (via the faculty that fits: elevator / wiki_local")
    print("/ reflective) OR decompose-into-subgoals (seed a child Goal per subgoal, pursue")
    print("each recursively, compose). A SUBGOAL IS A GOAL; the goal/subgoal TREE is real")
    print("graph data (parent -has_subgoal-> child). The elevator's reduce->recurse for")
    print("MATH is now the SAME recursion over arbitrary goals with MIXED-faculty leaves:")
    print("a compound goal decomposes into a KNOW subgoal (wiki_local) + a COMPUTE subgoal")
    print("(the elevator) + nests depth-2+ (a subgoal seeds sub-subgoals). The residual:")
    print("the decomposition frontier (novel/compound shapes) + the leaf-resolution limits")
    print("(comprehension-depth for know; deep-reads for compute).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
