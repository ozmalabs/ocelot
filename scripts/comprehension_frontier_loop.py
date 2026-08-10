"""AUTONOMOUS COMPREHENSION-FRONTIER LOOP — comprehension wired into the agent's curiosity loop.

The pivot: the things the agent READS but cannot resolve become its OWN curiosity frontiers. For each
utterance, the agent comprehends it (gap-as-POS parse -> ground the gaps -> compose the focus into a relation
-> resolve). What it can resolve (a held/learned/relation answer) it answers; what it CANNOT becomes a
CapabilityAxis with a residual (shortfall). Then the autonomous loop runs: the agent PICKS its highest-residual
frontier (Argmax over its axes by shortfall — the residual-salience pick, graph-native), INVESTIGATES it
(consults the teacher for that well-posed relation and LEARNS the answer via the teach facility, which
PERSISTS to seeds/resolved_queries.json), and CLOSES the frontier (shortfall -> 0). Re-asking then resolves —
and survives a reboot.

This closes the loop the whole session has been driving — recognise -> frontier -> learn -> resolve — at the
level of the agent's own reading/curiosity, not a Q&A shell. The agent decides WHICH frontier (its Term); the
host only fetches the teacher's answer for the frontier the agent picked (external I/O).

Run:  PYTHONPATH=.:runners/dsl/python python3 scripts/comprehension_frontier_loop.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import question_driver as qd
from domains import construction_grammar as cg
from domains import reflective_faculty as rf

SEP = "=" * 96

# What the agent READS (a small stream). One it already knows (persisted from a prior session), three new.
READING = [
    "Why would your plan lead you into a wall?",          # already learned (seeds/resolved_queries.json)
    "Why does a mistake make you learn?",
    "Why does exploring reduce surprise?",
    "Why does a model stop you getting stuck?",
]
# The TEACHER the agent consults when it INVESTIGATES a frontier it picked (external I/O; keyed by utterance).
TEACHER = {
    "Why does a mistake make you learn?":
        "a mistake is a falsified prediction; the residual it exposes is the lesson",
    "Why does exploring reduce surprise?":
        "exploring collapses the unexplained residual onto the model",
    "Why does a model stop you getting stuck?":
        "a correct model knows every dead-end and routes around it, so getting stuck means the model is wrong",
}

# the agent's residual-salience PICK: Argmax over its capability axes by shortfall (the highest residual).
PICK = {"type": "Argmax",
        "source": {"type": "NodesWhere", "node_type": "CapabilityAxis", "attr_key": "is_axis",
                   "value": {"type": "Lit", "value": 1.0}},
        "var_name": "x",
        "value": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "shortfall"}}


def main():
    s, _ = rf.boot_reflective_substrate()
    drv = qd.QuestionDriver(substrate=s)
    print(SEP)
    print("AUTONOMOUS COMPREHENSION-FRONTIER LOOP — what the agent reads-but-can't-resolve becomes its frontier")
    print(SEP)

    # ---- PHASE A: READ -> resolve what it can; the rest become residual frontiers --------------------
    print("\nREAD (comprehend each; the unresolved become curiosity frontiers):")
    for utt in READING:
        emi = drv.drive(qd.QuestionPack(text=utt, reflect=rf.reflect))
        rel = cg.compose_relation(cg.parse_with_gaps(utt, s))
        resolved = cg.resolve_focus(rel, emi.subgoals, s)
        if resolved:
            print(f"  '{utt}'\n      -> ALREADY KNOWN: {resolved}")
        else:
            ung = sum(1 for sg in emi.subgoals if getattr(sg, "is_wall", True))
            sf = 1.0 + float(ung)                            # residual: 1 + the count of still-ungrounded gaps
            s.add_node("CapabilityAxis", {"is_axis": 1.0, "shortfall": sf,
                                          "key": cg.relation_key(rel), "utt": utt})
            print(f"  '{utt}'\n      -> FRONTIER (residual {sf:.1f}; {ung} ungrounded gaps) = {cg.relation_key(rel)}")

    # ---- PHASE B: the AUTONOMOUS LOOP — pick the highest-residual frontier, investigate, learn, close ---
    print("\nAUTONOMOUS LOOP (pick by residual -> investigate -> learn+persist -> close):")
    step = 0
    while True:
        picked = s.evaluate(PICK, {})
        if picked is None:
            break
        sf = s.node(picked)["attrs"].get("shortfall", 0.0)
        if sf <= 0.0:
            break
        step += 1
        utt = s.node(picked)["attrs"]["utt"]
        ans = TEACHER.get(utt)
        print(f"  [{step}] PICK (residual {sf:.1f}): '{utt}'")
        if ans:
            cg.learn_frontier_answer(s, utt, ans)            # LEARN + PERSIST (teach -> resolved_queries seed)
            print(f"        INVESTIGATE -> teacher -> LEARNED + PERSISTED: {ans}")
        s.set_attr(picked, "shortfall", 0.0)                 # frontier closed
    print(f"  loop converged in {step} investigations (no residual frontier left).")

    # ---- PHASE C: re-ask everything — now all resolve (and the new ones persist across boots) ----------
    print("\nRE-ASK (every utterance now resolves):")
    ok = 0
    for utt in READING:
        emi = drv.drive(qd.QuestionPack(text=utt, reflect=rf.reflect))
        rel = cg.compose_relation(cg.parse_with_gaps(utt, s))
        r = cg.resolve_focus(rel, emi.subgoals, s)
        ok += bool(r)
        print(f"  '{utt}' -> {r}")

    print("\n" + SEP)
    allok = ok == len(READING)
    print(f"  {'PASS' if allok else 'FAIL'} — the agent READ, turned what it could not resolve into RESIDUAL")
    print("  frontiers, PICKED each by its own residual-salience Term, INVESTIGATED (learned from the teacher),")
    print("  PERSISTED the answers, and now resolves ALL of them. Comprehension is wired into the curiosity")
    print("  loop: recognise -> frontier -> learn -> resolve, at the level of the agent's own reading.")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
