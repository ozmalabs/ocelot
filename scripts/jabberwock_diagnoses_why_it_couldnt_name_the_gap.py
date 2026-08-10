"""THE META-META LOOP — the agent DIAGNOSES WHY IT COULD NOT NAME THE GAP (a recursion
on the metacognition: diagnose why the gap-diagnosis ITSELF failed).

The user's instruction: "now have it diagnose why it couldn't name that gap."

cmsg109 wired the comprehension frontier -> ASK-WHY (diagnose the missing construction)
-> SEEK (acquire it) -> re-comprehend, and CROSSED 'compare HTTP with FTP'. But it
left a NAMED RESIDUAL: a DIFFERENT surface of the SAME comparison — 'how does HTTP
differ from FTP' — still WALLS *and* the gap-diagnosis (diagnose_comprehension_gap)
returns None: the ASK-WHY ITSELF FAILS (it names no missing construction). This run
wires the NEXT LEVEL — the agent diagnoses WHY the gap-diagnosis failed:

    drive('how does HTTP differ from FTP')  ->  FRONTIER (grounded=False)
                                            ->  ASK-WHY (cmsg109) names NOTHING
      LEVEL 3 (THIS): the ask-why ITSELF fails. The agent introspects its OWN
      gap-diagnosis and DIAGNOSES WHY IT COULD NOT NAME THE GAP:

      1. DIAGNOSE-WHY-THE-DIAGNOSIS-FAILED (the meta-meta): the agent examines
         diagnose_comprehension_gap and recognizes it is SURFACE-BOUND — it names a
         gap ONLY by matching HELD SURFACE FORMS (the head verb 'compare'/'contrast'
         + a held connective). 'how does X differ from Y' matches NO held head, so the
         diagnosis had nothing to anchor on. BUT the question's MEANING is comparison
         — the SAME comparison the agent ALREADY HOLDS (cmsg109) — in a SURFACE it
         does not recognize. The gap it could not name is NOT a missing MEANING; it is
         a MISSING SURFACE OF A HELD MEANING.
      2. SEEK/FIX (the meaning-vs-surface distinction): a construction is ONE meaning
         realized by MANY surfaces (the prosody Mt's function-vs-serialization, at the
         GOAL level). The agent acquires the new SURFACE ('how does {x} differ from
         {y}') as a realization of the HELD comparison goal — no new MEANING, only a
         new SURFACE. The held comparison construction becomes surface-robust.
      3. RE-COMPREHEND -> PURSUE: drive('how does HTTP differ from FTP') NOW
         comprehends -> the comparison goal -> [ know(HTTP), know(FTP), contrast ] ->
         pursued + composed. The surface frontier is CROSSED by the agent's own
         diagnose-why-the-diagnosis-failed + surface-variation acquire.

The recursion (the meta-meta levels):
  L1 (cmsg107-108): comprehend -> goal -> subgoals.
  L2 (cmsg109): comprehension FAILS -> ask-why (name the missing construction) ->
     seek/acquire -> re-comprehend.
  L3 (THIS): the ask-why ITSELF fails -> diagnose-WHY-the-diagnosis-failed (the
     surface-bound insight) -> the surface-variation fix -> re-comprehend.

A WORLD-ADAPTER SHELL (CLAUDE.md): it STAGES the questions + SEQUENCES the agent's
machinery (the introspection of its own gap-diagnosis + the surface-variation acquire
+ read_and_ground + the recursive pursuit). The agent's own machinery does the work.
No LLM, no Rust. Math/reading/self domain only (no audio path).

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/jabberwock_diagnoses_why_it_couldnt_name_the_gap.py
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
DIFFER_Q = "how does HTTP differ from FTP"
COMPARE_Q = "compare HTTP with FTP"


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


def _stage_cmsg109():
    """Stage the cmsg109 end state: the agent has acquired the HEAD-LED comparison
    construction ('compare X with Y') but NOT the 'differ from' surface. The world-
    adapter staging a fresh agent at exactly the cmsg109 frontier the user extends."""
    cq._ACQUIRED_QUESTION["comparison"] = []
    cq.acquire_compare_construction(cq.diagnose_comprehension_gap(COMPARE_Q))


def _goal_tree(driver):
    s = driver.s
    roots = [n for n in s.nodes("Goal") if not s.in_neighbours(n, "has_subgoal")]
    lines, maxd = [], [0]

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


def step1_residual_confronted():
    banner("1. THE RESIDUAL CONFRONTED — drive('how does HTTP differ from FTP') walls "
           "*and* the cmsg109 ask-why ITSELF fails (names NO construction)")
    _stage_cmsg109()
    print("  cmsg109 CROSSED 'compare HTTP with FTP' (ask-why -> acquire -> pursue).")
    print("  But a DIFFERENT surface of the SAME comparison still walls — and this")
    print("  time the ASK-WHY ITSELF fails: the gap-diagnosis names NO construction.\n")
    driver = qd.QuestionDriver()
    emi = driver.drive(qd.QuestionPack(text=DIFFER_Q))
    print(f"  drive({DIFFER_Q!r}):")
    print(emi.report())
    frontier = emi.is_wall and (emi.target is None or not emi.target.grounded)
    print(f"\n  -> FRONTIER (grounded=False): {frontier}")

    # the cmsg109 ASK-WHY itself fails — it names NO missing construction.
    gap = cq.diagnose_comprehension_gap(DIFFER_Q)
    print(f"  ASK-WHY (cmsg109 diagnose_comprehension_gap) -> {gap}")
    print(f"    -> the ask-why ITSELF fails: it names NO missing construction "
          f"({gap is None}).")
    ok = frontier and gap is None
    print(f"\n  [STEP 1] the residual confronted — the question walls AND the cmsg109 "
          f"ask-why names nothing: {ok}")
    return ok


def step2_meta_meta_diagnosis():
    banner("2. DIAGNOSE-WHY-THE-DIAGNOSIS-FAILED (the meta-meta) — the agent "
           "introspects its OWN gap-diagnosis -> the SURFACE-BOUND insight")
    print("  The agent does not stop at 'the ask-why failed'. It RECURSES on the")
    print("  metacognition: it examines its OWN gap-diagnosis and diagnoses WHY it")
    print("  could not name the gap.\n")
    md = cq.diagnose_why_diagnosis_failed(DIFFER_Q)
    print("  THE META-META DIAGNOSIS (the agent introspecting its own gap-diagnosis):")
    print(f"    mechanism            : {md['mechanism']}")
    print(f"    held meaning         : {md['held_meaning']}  "
          f"(via {md['held_construction']})")
    print(f"    surface cue          : {md['surface_cue']!r}")
    print(f"    unrecognized surface : {md['unrecognized_surface']!r}")
    print(f"    abstracted template  : {md['surface_template']!r}")
    print(f"    operands             : {md['operands']}")
    print(f"\n    WHY: {md['why']}")
    print(f"\n    FIX: {md['fix']}")
    ok = (md is not None and md["mechanism"] == "surface-bound"
          and md["held_meaning"] == "comparison"
          and md["operands"] == ["http", "ftp"]
          and md["surface_template"] == "how does {x} differ from {y}")
    print(f"\n  [STEP 2] the agent diagnosed WHY it could not name the gap — its "
          f"gap-diagnosis is SURFACE-BOUND (the held comparison in an unrecognized "
          f"surface): {ok}")
    return ok, md


def step3_seek_fix(md):
    banner("3. SEEK/FIX — the meaning-vs-surface distinction: acquire the new SURFACE "
           "as a realization of the HELD comparison goal")
    print("  A construction is ONE meaning + MANY surfaces (the prosody Mt's function-")
    print("  vs-serialization, at the GOAL level). The agent does NOT acquire a new")
    print("  MEANING — it extends the HELD comparison construction with the new")
    print("  SURFACE, making the held comparison goal surface-robust.\n")
    before = cq.comprehend(DIFFER_Q).grounded
    acq = cq.acquire_surface_variation(md)
    print(f"  SURFACE acquired     : {acq['surface_template']!r}")
    print(f"  realizes the MEANING : {acq['held_meaning']} -> {acq['realizes']}")
    print(f"  ACQUIRED             : {acq['acquired']}")
    print(f"  VERIFY  : BEFORE the acquire the surface comprehended? {acq['before']}")
    print(f"            AFTER  the acquire?                          {acq['after']}")
    print(f"            -> {acq['reason']}")
    print("  the new surface is now HELD on the comparison construction "
          "(comprehend_question._ACQUIRED_QUESTION['comparison'][0]['surfaces']);")
    print("  comprehend_compare reads it so the comparison MEANING comprehends across")
    print("  surfaces — NO new meaning was acquired, only the surface.")
    ok = (before is False and acq["acquired"] and acq["after"] is True
          and acq["realizes"] == ["know(X)", "know(Y)", "contrast(X,Y)"])
    print(f"\n  [STEP 3] the seek/fix acquired the new SURFACE of the held comparison "
          f"meaning (before=False -> after=True): {ok}")
    return ok


def step4_recomprehend_pursue():
    banner("4. RE-COMPREHEND + PURSUE — drive('how does HTTP differ from FTP') NOW "
           "comprehends -> the comparison goal -> pursued + composed")
    print("  The surface frontier is CROSSED by the agent's own diagnose-why-the-")
    print("  diagnosis-failed + the surface-variation acquire: drive() now comprehends")
    print("  the comparison goal -> [ know(HTTP), know(FTP), contrast ] -> pursued.\n")
    spec = cq.comprehend(DIFFER_Q)
    print(f"  RE-COMPREHEND: {spec.line()}")
    print(f"    (grounded={spec.grounded}, kind={spec.kind})\n")

    driver = qd.QuestionDriver()
    emi = driver.drive(qd.QuestionPack(text=DIFFER_Q))
    print(f"  drive({DIFFER_Q!r}) — the surface frontier crossed:")
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
    print(f"\n  THE TREE (the SAME comparison goal cmsg109 pursues — now off the new "
          f"surface):")
    print(f"    KNOW subgoal HTTP -> wiki_local -> SHORT grounded genus: {know_ok}")
    print(f"    KNOW subgoal FTP  -> wiki_local -> grounded (article=FTPS, the honest")
    print(f"                         search residual): "
          f"{not knows[1].is_wall if len(knows) > 1 else False}")
    print(f"    CONTRAST subgoal  -> over the two grounded genera: {contrast_ok}")
    print(f"    composed (every subgoal resolved by its faculty): {not emi.is_wall}")
    print(f"\n  [STEP 4] the surface frontier CROSSED — comparison goal comprehended + "
          f"pursued + composed off the 'differ from' surface: {ok}")
    return ok


def step5_no_regression():
    banner("5. NO REGRESSION — the cmsg107-109 goals (flat / compound / head-led "
           "compare) intact")
    print("  The meta-meta loop is ADDITIVE: the flat KNOW goal, the compound goal,")
    print("  and the cmsg109 head-led 'compare X with Y' all still resolve; the new")
    print("  surface only ADDS to the held comparison construction.\n")
    driver = qd.QuestionDriver()
    http = driver.drive(qd.QuestionPack(text="What is HTTP?"))
    compound = driver.drive(qd.QuestionPack(
        text="What is HTTP and what is idempotence"))
    head_led = driver.drive(qd.QuestionPack(text=COMPARE_Q))
    print("  drive('What is HTTP?') [flat KNOW]:")
    print(http.report())
    print()
    print("  drive('What is HTTP and what is idempotence') [compound]:")
    print(compound.report())
    print()
    print(f"  drive({COMPARE_Q!r}) [cmsg109 head-led compare]:")
    print(head_led.report())
    http_ok = (http.kind == "know" and not http.is_wall and not http.subgoals
               and (http.know_answer or {}).get("article") == "HTTP")
    comp_ok = (compound.kind == "compound" and not compound.is_wall
               and len(compound.subgoals) == 2)
    head_ok = (head_led.target.kind == "compare" and not head_led.is_wall
               and len(head_led.subgoals) == 3)
    ok = http_ok and comp_ok and head_ok
    print(f"\n  [STEP 5] flat KNOW ({http_ok}) + compound ({comp_ok}) + head-led "
          f"compare ({head_ok}) intact: {ok}")
    return ok


def step6_honest():
    banner("6. HONEST — the meta-meta loop crossed the surface-bound frontier; the "
           "frontier RECEDED but did NOT vanish (the new residual)")
    print("  THE WIN: the agent DIAGNOSED WHY IT COULD NOT NAME THE GAP — a recursion")
    print("  on the metacognition. It introspected its OWN gap-diagnosis, recognized")
    print("  it is SURFACE-BOUND (matches held surface forms, not the comparison")
    print("  MEANING across surfaces), discovered 'how does X differ from Y' is the")
    print("  comparison MEANING it HOLDS in a SURFACE it did not recognize, and SELF-")
    print("  EXTENDED (the meaning-vs-surface distinction: acquire the new surface as")
    print("  a realization of the held comparison goal) -> re-comprehended + pursued.")
    print()
    print("  THE FRONTIER RECEDED (the 'differ from' surface crossed) — but it did NOT")
    print("  VANISH. The NEW RESIDUAL (named, not hidden):")
    print()

    # residual A — a surface even the meta-meta cannot map (NO comparison-MEANING cue).
    novel_surface = "explain HTTP relative to FTP"
    ns = cq.comprehend(novel_surface)
    ns_md = cq.diagnose_why_diagnosis_failed(novel_surface)
    print(f"    A. A SURFACE EVEN THE META-META CANNOT MAP — no comparison-MEANING cue.")
    print(f"       comprehend({novel_surface!r}) -> grounded={ns.grounded}; the meta-")
    print(f"       meta diagnosis fires? {ns_md is not None} — 'explain X relative to")
    print(f"       Y' carries no 'differ'/'difference'/'vs' cue the meta-meta anchors")
    print(f"       the HELD comparison meaning on, so the recursion has nothing to map")
    print(f"       (the meta-meta is itself CUE-bound — the next recursion's frontier).")
    print()

    # residual B — a genuinely-novel MEANING the agent does NOT hold.
    novel_meaning = "summarize HTTP in one sentence"
    nm = cq.comprehend(novel_meaning)
    nm_md = cq.diagnose_why_diagnosis_failed(novel_meaning)
    print(f"    B. A GENUINELY-NOVEL MEANING the agent does NOT hold.")
    print(f"       comprehend({novel_meaning!r}) -> grounded={nm.grounded}; the meta-")
    print(f"       meta fires? {nm_md is not None} — 'summarize' is a goal-MEANING the")
    print(f"       agent does not hold (not comparison, not know/compute/compound), so")
    print(f"       there is no held meaning to realize a surface of. The receded-not-")
    print(f"       vanished frontier: a NEW meaning still walls (the honest limit).")
    print()
    print("  WHAT RECEDED vs THE NEW RESIDUAL:")
    print("    RECEDED : the surface-bound gap-diagnosis (it now recurses to diagnose")
    print("              WHY it could not name the gap) + the 'differ from' surface of")
    print("              the held comparison meaning (acquired as a realization).")
    print("    RESIDUAL: a surface with NO comparison-MEANING cue (the meta-meta is")
    print("              cue-bound), and a genuinely-NOVEL meaning the agent does not")
    print("              hold (no held meaning to realize). The recursion's next")
    print("              frontier — articulable, not yet crossed.")
    print()
    print("  DO NOT over-claim 'it crosses any frontier' — the SURFACE-BOUND frontier")
    print("  is crossed (the held comparison meaning recognized across the 'differ")
    print("  from' surface); a no-cue surface + a genuinely-novel meaning still wall.")
    return (not ns.grounded) and (ns_md is None) and (not nm.grounded) and (nm_md is None)


def main():
    banner("THE META-META LOOP — the agent DIAGNOSES WHY IT COULD NOT NAME THE GAP "
           "(a recursion on the metacognition)")
    print("The user's instruction: 'now have it diagnose why it couldn't name that")
    print("gap.' cmsg109 crossed 'compare HTTP with FTP' but left a residual: a")
    print("DIFFERENT surface of the SAME comparison — 'how does HTTP differ from FTP'")
    print("— still walls AND the ask-why ITSELF fails (the gap-diagnosis names")
    print("nothing). This wires the NEXT LEVEL: the agent introspects its OWN gap-")
    print("diagnosis and diagnoses WHY it could not name the gap (it is SURFACE-BOUND")
    print("— the held comparison meaning in a surface it does not recognize) -> the")
    print("meaning-vs-surface fix (acquire the new surface as a realization of the")
    print("held comparison goal) -> re-comprehend -> pursue. The agent's machinery")
    print("does it (the introspection of its own gap-diagnosis + the surface-variation")
    print("acquire + read_and_ground); the shell ORCHESTRATES.")

    results = {
        "1. the residual confronted (walls + the ask-why ITSELF fails)":
            step1_residual_confronted(),
    }
    ok2, md = step2_meta_meta_diagnosis()
    results["2. diagnose-WHY-the-diagnosis-failed (SURFACE-BOUND insight)"] = ok2
    results["3. seek/fix (meaning-vs-surface: acquire the new SURFACE)"] = \
        step3_seek_fix(md)
    results["4. re-comprehend + pursue (the comparison goal off the new surface)"] = \
        step4_recomprehend_pursue()
    results["5. no regression (cmsg107-109 goals intact)"] = step5_no_regression()
    results["6. honest (the meta-meta loop + the receded-not-vanished frontier)"] = \
        step6_honest()

    banner("SUMMARY")
    for k, v in results.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    ok = all(results.values())
    print(f"\n  {'ALL PASS' if ok else 'SOME FAILED'} — the agent DIAGNOSED WHY IT "
          f"COULD NOT NAME THE GAP: a recursion on the metacognition.")
    print("\nLEARNING: cmsg109 crossed 'compare HTTP with FTP', but 'how does HTTP")
    print("differ from FTP' (the SAME comparison MEANING, a DIFFERENT surface) still")
    print("walled AND the ask-why ITSELF failed (diagnose_comprehension_gap named")
    print("nothing). The agent RECURSED ON THE METACOGNITION: it introspected its OWN")
    print("gap-diagnosis and diagnosed WHY it could not name the gap — the diagnosis")
    print("is SURFACE-BOUND (it matches HELD SURFACE FORMS, the head verb + connective,")
    print("not the comparison MEANING across surfaces); 'how does X differ from Y' is")
    print("the comparison it ALREADY HOLDS in a surface it does not recognize. The gap")
    print("it could not name is NOT a missing MEANING — it is a MISSING SURFACE OF A")
    print("HELD MEANING. THE FIX is the meaning-vs-surface distinction (a construction")
    print("= ONE meaning + MANY surfaces, the prosody Mt's function-vs-serialization at")
    print("the GOAL level): the agent acquired the new surface as a realization of the")
    print("held comparison goal -> re-comprehended -> pursued [know(HTTP), know(FTP),")
    print("contrast]. The frontier RECEDED (the surface-bound diagnosis + the 'differ")
    print("from' surface crossed) but did NOT vanish: a surface with no comparison cue")
    print("(the meta-meta is itself cue-bound) + a genuinely-novel meaning the agent")
    print("does not hold still wall — the recursion's next frontier.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
