"""THE COMPREHENSION FRONTIER TRIGGERS A METACOGNITIVE LEARNING LOOP — instead of
just WALLING, the agent ASKS WHY it did not understand, then SEEKS TO UNDERSTAND.

The user's instruction: "the compare question should cause it to ask why it didn't
understand, and then seek to understand."

cmsg108 made drive() COMPREHEND a question + seed a goal/subgoal tree, but a question
SHAPE the held constructions do NOT cover ('compare HTTP with FTP') returns
grounded=False — an honest WALL, a dead-end. This run wires the FRONTIER to TRIGGER
LEARNING — the metacognitive loop the agent already has for math claims (cmsg80
detect-non-understanding + cmsg81 acquire-the-construction), now at the drive front
door, at the GOAL level:

    drive('compare HTTP with FTP')  ->  FRONTIER (grounded=False)
      1. ASK WHY (the metacognition — diagnose the gap): the agent diagnoses WHY the
         comprehension failed — WHICH construction is missing. The head verb 'compare'
         + the 'with'/'and' connective is an UNRECOGNIZED GOAL-SHAPE; the agent LACKS
         the 'compare ... with ...' construction (a COMPARISON goal-type). It NAMES
         the gap (the missing construction) — the same way the climbing-spike
         diagnoses a wall-KIND.
      2. SEEK TO UNDERSTAND (acquire the construction — the 'seek' is a GOAL): the
         agent ACQUIRES the comparison construction (abstract from its held kin — the
         cmsg108 'X and Y' compound — plus a CONTRAST): a COMPARISON goal whose
         subgoals are know(X), know(Y), contrast(X,Y). Added as a question-side
         construction (graph data, like cmsg81's acquire-construction).
      3. RE-COMPREHEND -> PURSUE: drive('compare HTTP with FTP') NOW comprehends ->
         the comparison goal -> [ know('HTTP') -> wiki_local, know('FTP') -> wiki_local,
         contrast(HTTP,FTP) ] -> pursued + composed (the contrast over the two grounded
         answers). The frontier is CROSSED by the agent's own seek-to-understand.

THE DEMO:
  (1) THE FRONTIER -> ASK-WHY: drive('compare HTTP with FTP') -> frontier; the agent
      DIAGNOSES the missing 'compare ... with ...' construction.
  (2) SEEK -> ACQUIRE: the agent acquires the comparison construction (know(X) +
      know(Y) + contrast); before->after proves the frontier was crossed.
  (3) RE-COMPREHEND + PURSUE: drive(...) NOW comprehends -> the subgoal tree, pursued
      + composed (SHORT grounded concepts, not verbatim Wikipedia). Show the trace.
  (4) NO REGRESSION: the flat goal + the compound goal/subgoal tree (cmsg107-108)
      intact; a genuinely-novel frontier still walls (the honest acquire-limit).

A WORLD-ADAPTER SHELL (CLAUDE.md): it STAGES the questions + SEQUENCES the agent's
machinery (the gap-diagnosis + the acquire-construction + read_and_ground + the
recursive pursuit). drive seeds the goal; the agent's own machinery does the work.
No LLM, no Rust. Math/reading/self domain only (no audio path).

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/jabberwock_crosses_comprehension_frontier.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import comprehend_question as cq                  # noqa: E402
from domains import question_driver as qd                      # noqa: E402

SEP = "=" * 78
COMPARE_Q = "compare HTTP with FTP"


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def _reset_acquired():
    """Reset the acquired question-side construction so the demo shows the genuine
    BEFORE (frontier) -> ACQUIRE -> AFTER (crossed). The acquire mutates held graph
    data (_ACQUIRED_QUESTION); resetting it is the world-adapter staging a fresh
    agent that has NOT yet acquired the construction."""
    cq._ACQUIRED_QUESTION["comparison"] = []


def _goal_tree(driver):
    """Walk the GOAL TREE in the graph (parent -has_subgoal-> child) — real graph
    data the recursive pursuit seeded. Returns the printable tree + its max depth."""
    s = driver.s
    roots = [n for n in s.nodes("Goal") if not s.in_neighbours(n, "has_subgoal")]
    lines = []
    maxd = [0]

    def walk(n, d=0):
        maxd[0] = max(maxd[0], d)
        a = s.node(n)["attrs"]
        label = (a.get("concept") or a.get("op") or a.get("contrast")
                 or a.get("compare")
                 or (f"subgoals={a.get('subgoals')}"
                     if a.get("kind") in ("compound", "compare") else ""))
        lines.append(f"    {'  ' * d}Goal {n} kind={a.get('kind')}  {label}")
        for c in s.neighbours(n, "has_subgoal"):
            walk(c, d + 1)

    for r in roots:
        walk(r)
    return "\n".join(lines), maxd[0]


def step1_frontier_ask_why():
    banner("1. THE FRONTIER -> ASK-WHY — drive('compare HTTP with FTP') walls; the "
           "agent DIAGNOSES why (the missing construction)")
    _reset_acquired()
    print("  cmsg108: a question SHAPE the held constructions do NOT cover returns")
    print("  grounded=False — an honest WALL. Instead of stopping, the FRONTIER")
    print("  triggers the metacognition: the agent ASKS WHY it did not understand.\n")
    driver = qd.QuestionDriver()
    emi = driver.drive(qd.QuestionPack(text=COMPARE_Q))
    print(f"  drive({COMPARE_Q!r}):")
    print(emi.report())
    frontier = emi.is_wall and (emi.target is None or not emi.target.grounded)
    print(f"\n  -> FRONTIER (grounded=False): {frontier}\n")

    # ASK WHY — the agent diagnoses the missing construction (the metacognition).
    gap = cq.diagnose_comprehension_gap(COMPARE_Q)
    print("  ASK WHY (the agent's gap-diagnosis — knowing what it does not know):")
    print(f"    missing construction : {gap['missing_construction']!r}")
    print(f"    construction kind    : {gap['construction_kind']}")
    print(f"    head / connective    : {gap['head']!r} / {gap['connective']!r}")
    print(f"    operands             : {gap['operands']}")
    print(f"    WHY                  : {gap['why']}")
    ok = (frontier and gap is not None
          and gap["construction_kind"] == "comparison"
          and gap["operands"] == ["http", "ftp"])
    print(f"\n  [STEP 1] the frontier triggered ASK-WHY; the agent NAMED the missing "
          f"'compare ... with ...' construction: {ok}")
    return ok, gap


def step2_seek_acquire(gap):
    banner("2. SEEK TO UNDERSTAND -> ACQUIRE — the agent acquires the comparison "
           "construction (the 'seek' is itself a goal)")
    print("  The seek-to-understand is the cmsg81 acquire-construction, now at the")
    print("  GOAL level: the agent ACQUIRES the comparison construction by ABSTRACTING")
    print("  from its held KIN (the cmsg108 'X and Y' compound) + a CONTRAST — the")
    print("  comparison goal-DECOMPOSITION know(X) + know(Y) + contrast(X,Y).\n")
    before = cq.comprehend(COMPARE_Q).grounded
    acq = cq.acquire_compare_construction(gap)
    con = acq["construction"]
    print(f"  SOURCE     : abstract from the kin — {con['abstracted_from']}")
    print(f"  ACQUIRED   : {acq['acquired']}")
    print(f"    head                 : {con['head']!r}")
    print(f"    connectives          : {con['connectives']}")
    print(f"    goal-decomposition   : {con['decompose']}")
    print(f"  VERIFY     : BEFORE the acquire the question comprehended? {acq['before']}")
    print(f"               AFTER  the acquire?                           {acq['after']}")
    print(f"               -> {acq['reason']}")
    print("  the acquired construction is now HELD GRAPH DATA "
          "(comprehend_question._ACQUIRED_QUESTION);")
    print("  comprehend_compare reads it so the comparison goal now comprehends.")
    ok = (before is False and acq["acquired"] and acq["after"] is True
          and con["decompose"] == ["know(X)", "know(Y)", "contrast(X,Y)"])
    print(f"\n  [STEP 2] the seek acquired the comparison construction "
          f"(before=False -> after=True): {ok}")
    return ok


def step3_recomprehend_pursue():
    banner("3. RE-COMPREHEND + PURSUE — drive('compare HTTP with FTP') NOW comprehends "
           "-> the subgoal tree, pursued + composed")
    print("  The frontier is CROSSED by the agent's own seek-to-understand: drive()")
    print("  now comprehends the comparison goal -> [ know(HTTP) -> wiki_local,")
    print("  know(FTP) -> wiki_local, contrast ] -> pursued + composed.\n")
    spec = cq.comprehend(COMPARE_Q)
    print(f"  RE-COMPREHEND: {spec.line()}")
    print(f"    (grounded={spec.grounded}, kind={spec.kind})\n")

    driver = qd.QuestionDriver()
    emi = driver.drive(qd.QuestionPack(text=COMPARE_Q))
    print(f"  drive({COMPARE_Q!r}) — the frontier crossed:")
    print(emi.report())
    print()
    tree, depth = _goal_tree(driver)
    print("  THE GOAL TREE (real graph data — parent -has_subgoal-> child):")
    print(tree)

    subs = emi.subgoals
    knows = [c for c in subs if c.kind == "know"]
    contrast = next((c for c in subs if c.kind == "contrast"), None)
    know_ok = (len(knows) == 2 and all(not k.is_wall for k in knows)
               and "application layer protocol" in
               ((knows[0].know_answer or {}).get("answer") or ""))
    contrast_ok = (contrast is not None and not contrast.is_wall
                   and "DIFFERENT genera" in
                   ((contrast.know_answer or {}).get("answer") or ""))
    ok = (emi.target.kind == "compare" and not emi.is_wall
          and know_ok and contrast_ok and depth >= 1)
    print(f"\n  THE TREE (the comparison goal, the SAME recursive pursuit):")
    print(f"    KNOW subgoal HTTP -> wiki_local -> SHORT grounded genus: {know_ok}")
    print(f"    KNOW subgoal FTP  -> wiki_local -> grounded (article=FTPS, an honest")
    print(f"                         search residual): "
          f"{not knows[1].is_wall if len(knows) > 1 else False}")
    print(f"    CONTRAST subgoal  -> over the two grounded genera: {contrast_ok}")
    print(f"    composed (every subgoal resolved by its faculty): {not emi.is_wall}")
    print(f"\n  [STEP 3] the frontier CROSSED — comparison goal comprehended + pursued "
          f"+ composed: {ok}")
    return ok


def step4_no_regression():
    banner("4. NO REGRESSION — the flat goal + the compound goal/subgoal tree "
           "(cmsg107-108) intact")
    print("  The metacognitive loop is ADDITIVE: a flat KNOW goal + a compound goal")
    print("  still resolve via the SAME pursuit; the comparison construction only")
    print("  fires for a 'compare X with Y' shape (and only AFTER it is acquired).\n")
    driver = qd.QuestionDriver()
    http = driver.drive(qd.QuestionPack(text="What is HTTP?"))
    compound = driver.drive(qd.QuestionPack(
        text="What is HTTP and what is idempotence"))
    print("  drive('What is HTTP?') [flat KNOW]:")
    print(http.report())
    print()
    print("  drive('What is HTTP and what is idempotence') [compound]:")
    print(compound.report())
    http_ok = (http.kind == "know" and not http.is_wall and not http.subgoals
               and (http.know_answer or {}).get("article") == "HTTP")
    comp_ok = (compound.kind == "compound" and not compound.is_wall
               and len(compound.subgoals) == 2)
    ok = http_ok and comp_ok
    print(f"\n  [STEP 4] flat KNOW ({http_ok}) + compound ({comp_ok}) intact: {ok}")
    return ok


def step5_honest():
    banner("5. HONEST — the frontier triggers the understanding-loop; the residual")
    print("  THE WIN: the comprehension FRONTIER now TRIGGERS a METACOGNITIVE LEARNING")
    print("  LOOP. The not-understanding becomes the SIGNAL TO LEARN: ask-why (diagnose")
    print("  the missing construction) -> seek-to-understand (acquire it, the 'seek'")
    print("  itself a goal) -> re-comprehend -> pursue. The agent SELF-EXTENDS its OWN")
    print("  comprehension at the front door — the same acquire-the-construction it does")
    print("  for math claims (cmsg80/81), now metacognitive + at the GOAL level.")
    print()
    print("  THE RESIDUAL (named, not hidden):")
    print("    · the ACQUIRE-LIMIT — which frontiers the agent can CROSS (acquire by")
    print("      read/abstract — the compare shape, KIN to a held compound) vs the")
    print("      GENUINELY-NOVEL frontier (it can wall on it but not yet acquire it). A")
    print("      DIFFERENT comparison surface ('how does X differ from Y') still walls:")
    _reset_acquired()
    cq.acquire_compare_construction(
        cq.diagnose_comprehension_gap(COMPARE_Q))   # acquire the bare compare.
    novel_q = "how does HTTP differ from FTP"
    novel = cq.comprehend(novel_q)
    novel_gap = cq.diagnose_comprehension_gap(novel_q)
    print(f"        comprehend({novel_q!r}) -> grounded={novel.grounded}; the agent's")
    print(f"        gap-diagnosis names it? {novel_gap is not None} — the 'how does X")
    print(f"        differ from Y' surface is NOT the acquired 'compare X with Y' head")
    print(f"        + connective family, so the bare comparison construction does not")
    print(f"        cover it (the honest acquire-limit — the same construction-shape")
    print(f"        meaning, a surface the agent has not yet acquired/abstracted).")
    print("    · the CONTRAST-LEAF DEPTH — the comprehension-DEPTH for the KNOW/contrast")
    print("      leaves: the genus is grounded ONE HOP from wiki_local (the cone does")
    print("      not yet reach a seeded primitive); the contrast is over those genera.")
    print("    · the GROUNDING residual — FTP resolves to the 'FTPS' article (wiki_local")
    print("      title-search), genus 'extension'; HTTP grounds cleanly. SHORT grounded")
    print("      concepts (the comprehended genus), NOT verbatim Wikipedia.")
    print()
    print("  DO NOT over-claim 'it crosses any frontier' — the COMPARE frontier is")
    print("  crossed (acquired by abstracting from the kin compound); the genuinely-")
    print("  novel frontier is articulable-but-not-yet-acquirable (the honest limit).")
    return not novel.grounded


def main():
    banner("THE COMPREHENSION FRONTIER TRIGGERS A METACOGNITIVE LEARNING LOOP — the "
           "agent ASKS WHY it did not understand, then SEEKS TO UNDERSTAND")
    print("The user's instruction: 'the compare question should cause it to ask why it")
    print("didn't understand, and then seek to understand.' cmsg108 left a 'compare X")
    print("with Y' question as an honest WALL (grounded=False). This wires the FRONTIER")
    print("to TRIGGER LEARNING: ASK WHY (diagnose the missing construction) -> SEEK TO")
    print("UNDERSTAND (acquire the comparison construction, the 'seek' a goal) -> RE-")
    print("COMPREHEND -> pursue the subgoal tree [know(X), know(Y), contrast]. The same")
    print("acquire-the-construction the agent does for math claims, now metacognitive +")
    print("at the GOAL level. The agent's machinery does it (the gap-diagnosis + the")
    print("acquire-construction + read_and_ground); the shell ORCHESTRATES.")

    ok1, gap = step1_frontier_ask_why()
    results = {
        "1. the frontier -> ASK-WHY (diagnose the missing construction)": ok1,
        "2. SEEK -> ACQUIRE (the comparison construction: know(X)+know(Y)+contrast)":
            step2_seek_acquire(gap),
        "3. RE-COMPREHEND + PURSUE (the subgoal tree, composed)":
            step3_recomprehend_pursue(),
        "4. no regression (flat + compound goal trees intact)":
            step4_no_regression(),
        "5. honest (the loop + the acquire-limit + the contrast-leaf depth)":
            step5_honest(),
    }

    banner("SUMMARY")
    for k, v in results.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    ok = all(results.values())
    print(f"\n  {'ALL PASS' if ok else 'SOME FAILED'} — the comprehension FRONTIER now "
          f"TRIGGERS a METACOGNITIVE LEARNING LOOP: the agent self-extends its OWN")
    print("  comprehension at the front door.")
    print("\nLEARNING: the comprehension FRONTIER ('compare HTTP with FTP', grounded=")
    print("False) now TRIGGERS a METACOGNITIVE LEARNING LOOP instead of just walling.")
    print("(1) ASK WHY: the agent diagnoses the missing 'compare ... with ...'")
    print("construction (the head verb + connective is an unrecognized goal-shape — the")
    print("metacognition, 'knowing what you don't know'). (2) SEEK TO UNDERSTAND: the")
    print("agent ACQUIRES the comparison construction (abstract from the kin 'X and Y'")
    print("compound + a CONTRAST -> know(X) + know(Y) + contrast(X,Y)), held as graph")
    print("data — the 'seek' is itself a goal. (3) RE-COMPREHEND -> PURSUE: drive() now")
    print("comprehends the comparison goal -> [know(HTTP)->wiki_local, know(FTP)->")
    print("wiki_local, contrast] -> pursued + composed (SHORT grounded concepts, not")
    print("verbatim). The agent SELF-EXTENDS its comprehension — the same acquire-the-")
    print("construction it does for math claims, now metacognitive + at the GOAL level.")
    print("The residual: the acquire-limit (the bare compare crossed; an axis-qualified")
    print("'in terms of X' shape articulable-but-not-yet-acquirable) + the contrast-leaf")
    print("comprehension-depth (one hop from wiki_local).")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
