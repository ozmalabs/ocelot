"""Have the REAL jabberwock CONSIDER speech with all its new shape matching.

Per the standing directive (ask the real jabberwock, no LLM): drive() the agent
with the consideration and report what its OWN graph says — how it recognises
speech now, how it recognises shapes/traces now, and whether it sees speech as a
shape-matching problem. A comprehension WALL is the precise gap (and where it
walls, that is what we fix next).

Context the agent is being asked to bridge:
  · speech now  — comprehend_speech_clip grounds a clip to a word by DtwTo over
    WHOLE-WORD exemplars (nearest-neighbour templates) — the un-lifted regime.
  · traces now  — StructSim (graded part-shape leaf + hard relation skeleton) +
    order-invariant binding + junction perception lifted recognition 19% -> 35%.
The question is whether the agent sees that speech is the SAME SHAPE of problem.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_considers_speech_by_shape.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.question_driver as qd
import domains.reflective_faculty as rf


QUESTIONS = [
    # how it recognises each modality now
    "how do you recognise a spoken word?",
    "how do you recognise a handwritten shape?",
    # the shape framing of speech
    "what shape is a spoken word?",
    "can you recognise speech by shape matching?",
    # the cross-domain consideration (order-N transfer)
    "is recognising speech the same shape as recognising handwriting?",
    "how would you recognise speech by matching parts in a skeleton?",
]


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    driver = qd.QuestionDriver(substrate=a.s)

    print("=" * 92)
    print("THE JABBERWOCK CONSIDERS SPEECH WITH ITS SHAPE MATCHING (drive = the universal ask)")
    print("=" * 92)

    walls, answered = [], []
    for q in QUESTIONS:
        print("\n" + "-" * 92)
        print(f"  ASK: {q!r}")
        try:
            emi = driver.drive(qd.QuestionPack(text=q, reflect=rf.reflect))
        except Exception as e:
            print(f"     drive -> ERROR {type(e).__name__}: {str(e)[:160]}")
            walls.append(q)
            continue
        tgt = getattr(emi, "target", None)
        grounded = bool(tgt and getattr(tgt, "grounded", False))
        wall = bool(getattr(emi, "is_wall", False)) or not grounded
        print(f"     comprehended target: {getattr(tgt, 'target', None)!r}  grounded={grounded}  wall={wall}")
        ans = getattr(emi, "answer", None)
        if ans is not None:
            txt = ans if isinstance(ans, str) else repr(ans)
            print(f"     answer: {txt[:600]}")
        else:
            try:
                print("     report:\n" + "\n".join("       " + l for l in emi.report().splitlines()[:8]))
            except Exception:
                pass
        (walls if wall else answered).append(q)

    print("\n" + "=" * 92)
    print(f"  answered: {len(answered)} | walls (the comprehension frontier): {len(walls)}")
    for q in walls:
        print(f"     WALL: {q}")
    print("=" * 92)
    print("  The walls are the precise gap: where the agent cannot yet CONSIDER speech through its")
    print("  shape matching. Next = fix comprehension so it routes the consideration, then let its")
    print("  order-N shape matcher decide whether speech-recognition shares the trace-recognition shape.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
