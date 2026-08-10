"""ASK THE REAL JABBERWOCK (its own universal-ask, NO LLM) how it wants to perform ARBITRARY modifications.
comprehend the question's kind; route a self/meta question to the agent's held reflective faculty; print its
REAL self-answer (read off its own machinery) or its honest COMPREHENSION-FRONTIER wall. Whatever it cannot
comprehend/answer is the precise graph-native gap to fix. Driven on the FULL agent (load_all_seeds, 363/363).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/ask_jabberwock_modification.py
"""
from __future__ import annotations
import os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT,"runners","dsl","python"), os.path.join(ROOT,"scripts")):
    if p not in sys.path: sys.path.insert(0,p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import comprehend_question as cq
from domains import reflective_faculty as rf

QUESTIONS=[
    "How do you want to perform arbitrary modifications?",
    "How do you want to modify yourself?",
    "How do you want to change your own rules?",
    "What can you modify about yourself?",
    "How do you want to design your own faculties?",   # baseline: this one is wired (self_design)
    "Where is your frontier?",
]

def main():
    a=WorldAdapter(seeds=()); load_all_seeds(a)
    print("meta-targets the agent can COMPREHEND:", sorted(rf._DISPATCH.keys()))
    print()
    for q in QUESTIONS:
        spec=cq.comprehend(q)
        print("="*92)
        print(f"ASK: {q}")
        print(f"  comprehend -> kind={spec.kind} meta_target={getattr(spec,'meta_target',None)} "
              f"faculty={getattr(spec,'faculty',None)}")
        if spec.kind=="meta" and getattr(spec,"meta_target",None):
            ans=rf.reflect(spec.meta_target, getattr(spec,"meta_arg",None), a.s)
            for k,v in list(ans.items())[:6]:
                print(f"    {k}: {str(v)[:150]}")
        else:
            print("    -> COMPREHENSION FRONTIER (no construction parsed it): the agent cannot be asked this "
                  "yet — the precise graph-native gap to fix.")
    print("\n"+"="*92)
    print("What it answers from its own faculties = the design; what it walls on = the gap to wire (a meta-target")
    print("+ reflective faculty for SELF-MODIFICATION), so it can be asked how it modifies itself — no LLM.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
