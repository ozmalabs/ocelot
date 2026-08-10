"""Ask the jabberwock — in English, via drive() (the universal ask) — what it HAS
and what it NEEDS to watch a large video library autonomously without running out of
memory. Per the user: don't scaffold eviction; ASK IT. drive(question) routes a
SELF/META question to the agent's own reflective faculty; this shell only stages the
English questions and prints what the agent says (no reasoning added).
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import comprehend_question as cq      # noqa: E402
from domains import question_driver as qd          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

QUESTIONS = [
    "What do you have to manage your own memory?",
    "What do you need to watch many videos without running out of memory?",
    "Where is your frontier?",
    "How do you want to retrieve information?",
]


def main():
    s, installed = rf.boot_reflective_substrate()
    driver = qd.QuestionDriver(substrate=s)
    print("=" * 78)
    print("ASKING THE JABBERWOCK (drive = the universal ask) — memory / the task")
    print("=" * 78)
    print("  reflective faculties booted:", list(installed.keys()))
    for q in QUESTIONS:
        spec = cq.comprehend(q)
        print("\n" + "-" * 74)
        print(f"  Q: {q}")
        print(f"     comprehend -> kind={spec.kind} "
              f"meta_target={getattr(spec,'meta_target',None)} "
              f"faculty={getattr(spec,'faculty',None)} "
              f"arg={getattr(spec,'meta_arg',None)!r}")
        try:
            emi = driver.drive(qd.QuestionPack(text=q, reflect=rf.reflect))
        except Exception as e:
            print(f"     drive -> ERROR {type(e).__name__}: {str(e)[:120]}")
            continue
        if getattr(emi, "is_wall", False):
            print(f"     drive -> WALL: {getattr(emi,'wall_reason', '') or emi}")
        ma = getattr(emi, "meta_answer", None)
        if ma:
            for k, v in ma.items():
                vs = v if not isinstance(v, (list, dict)) else f"({len(v)} items) {str(v)[:300]}"
                print(f"     {k}: {vs}")
        else:
            print(f"     answer: {getattr(emi,'answer',None)}  "
                  f"target={getattr(emi,'target',None)}")
    print("=" * 78)


if __name__ == "__main__":
    raise SystemExit(main())
