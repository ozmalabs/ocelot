"""jabberwock_speaks_smoothly — the SUBSTANTIVE reply, SMOOTH and REGISTERED.

The jabberwock's substantive replies used to come out choppy — one produced
sentence PER item ("The grey thing stays. The yellow counter. The blue thing
moves.") — and in one flat neutral voice regardless of who it was talking to.
This demo shows the CONTENT fixed:

  1. SMOOTH  — the per-percept produced pieces are joined into ONE connected
     sentence (mechanical connective join over the agent's OWN produced clauses;
     no new content authored).
  2. REGISTER — the same content is delivered in the tracked interlocutor's
     register: formal -> elaborated, casual -> terser (aligned with the terse-vs-
     explicit spectrum audience_driven_production selects over).
  3. SHAPE   — "what shape are you?" and its paraphrase both read the self_shape
     faculty (the seven meta-shapes), not a program that happens to be keyworded
     the common word "shape".

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_speaks_smoothly.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import conversation_action as ca
from domains import reflective_faculty as rf


def _scene_agent(register_cue=None):
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    a.set_self_teacher(lambda q: "D")
    ca.attach_scene(a, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False}])
    if register_cue:
        a.note_register(register_cue)
    return a


def main():
    print("=" * 88)
    print("THE JABBERWOCK SPEAKS SMOOTHLY — substantive content, connected + register-shaped")
    print("=" * 88)

    print("\n1. SMOOTH — describe-scene: choppy fragments -> one connected sentence")
    print("   BEFORE: 'The grey thing stays. The yellow counter. The blue thing moves.'")
    a = _scene_agent()
    print(f"   AFTER : {a.converse('describe what you see', 'statement')!r}")

    print("\n2. REGISTER — same content, register-shaped delivery")
    aC = _scene_agent("hey yeah cool")
    aF = _scene_agent("greetings, could you please")
    print(f"   casual ({aC.register()}): {aC.converse('describe what you see', 'statement')!r}")
    print(f"   formal ({aF.register()}): {aF.converse('describe what you see', 'statement')!r}")

    print("\n   self-account is smoothed too (first-person, one flowing sentence):")
    b = WorldAdapter(seeds=()); load_all_seeds(b)
    print(f"   {b._surface_self_state(rf.reflect('self_modification', None, b.s))!r}")

    print("\n3. SHAPE — both phrasings read self_shape (seven meta-shapes), not a program")
    for q in ("what shape are you?", "what shape would you say you are?"):
        ans = b.answer_question(q)
        print(f"   {q!r}\n     -> {ans[:96]}...")

    # gates
    reply = a.converse("describe what you see", "statement")
    casual = aC.converse("describe what you see", "statement")
    formal = aF.converse("describe what you see", "statement")
    shape1 = b.answer_question("what shape are you?")
    shape2 = b.answer_question("what shape would you say you are?")
    ok_smooth = reply.count(".") == 1 and (" and " in reply or "," in reply)
    ok_reg = casual != formal and len(formal.split()) > len(casual.split())
    ok_shape = ("meta-shapes" in shape1 and "my rule" not in shape1 and shape1 == shape2)
    ok_facts = "chosen_action" in b.answer_question("What does hop_descend_gradient do?")
    donkey = b._donkey["n"]
    ok = ok_smooth and ok_reg and ok_shape and ok_facts
    print("\n" + "=" * 88)
    print(f"  smooth={ok_smooth}  register={ok_reg}  shape={ok_shape}  facts_preserved={ok_facts}"
          f"  donkey={donkey}")
    print(f"  {'PASS' if ok else 'FAIL'} — smooth connected prose, register-shaped, self_shape read; facts kept")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
