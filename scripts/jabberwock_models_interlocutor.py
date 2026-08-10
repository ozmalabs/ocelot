"""jabberwock_models_interlocutor — the agent MODELS WHO it is talking to, as its OWN COLLAPSE
FACULTY pointed at the person at TWO TIMESCALES (creator's reframe 2026-07-04: learning is the
collapse model at different timescales, literally homework).

The interlocutor model is a collapse PREDICTING the person. Its residuals at two timescales ARE
the two operations the conversation needs:

  * FAST/graded residual (affect) against a short-horizon model  -> PERTURBATION: the SAME person,
    state changed (a mood shift).
  * SLOW/structured residual (register/cadence/style + salient context: a time gap / place change)
    against the conversation-consolidated model -> IDENTIFICATION: a likely DIFFERENT person
    (re-attribution). Identity is continuously re-decided from the residual, weighted by context.

The predict/surprise/learn is the agent's DomainPlug into scripts/collapse_engine.run_collapse
(the move_space_collapse_plug precedent). The accumulated Party carries observed=True +
known_concepts, so a MODELLED interlocutor becomes a GROUNDED audience the Conceptualizer designs
for — instead of an empty audience every turn.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_models_interlocutor.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.interlocutor_model as im
import domains.audience_driven_production as adp


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


def main():
    print("=" * 92)
    print("THE JABBERWOCK MODELS ITS INTERLOCUTOR — collapse at two timescales (donkey=0)")
    print("=" * 92)
    a = _agent()

    print("\n--- 1. ACCUMULATION: a few turns from one interlocutor build a GROUNDED audience ---")
    turns = [
        "Good evening. I am Cornelius Vane, and I should like to discuss ethics.",
        "Indeed, virtue could be understood as the disposition toward excellence, kindly weighed.",
        "Pardon me, but morality requires that we examine consequences carefully.",
    ]
    for t in turns:
        r = im.observe_turn(a, t)
        print(f"  [{r['decision']:11}] {t[:64]}")
    snap = im.snapshot(a)
    bundle = adp.audience_model(a, snap)
    print(f"  -> Party '{snap['id']}' observed={snap['observed']} "
          f"knows {len(snap['known_concepts'])} concepts "
          f"(ethics/virtue/morality present: "
          f"{ {'ethics','virtue','morality'} <= set(snap['known_concepts']) })")
    print(f"  -> audience_model GROUNDED={bundle['grounded']}  "
          f"(the Conceptualizer now designs for a REAL, accumulating person)")
    print(f"  -> contrast: an UNOBSERVED interlocutor -> "
          f"grounded={adp.audience_model(a, {'id':'x','observed':False,'known_concepts':[]})['grounded']}")

    print("\n--- 2. PERTURBATION: the SAME person's affect shifts -> small residual, mood update ---")
    party_before = im._active_party(a)
    r = im.observe_turn(
        a, "This is outrageous and unacceptable; I am frankly furious about this disgraceful mess.")
    print(f"  turn: 'This is outrageous ... I am frankly furious ...'")
    print(f"  -> decision={r['decision']}  mood_shift={r['mood_shift']}  "
          f"slow_residual={r['slow_residual']}")
    print(f"  -> SAME party (identity stable): {r['party'] == party_before}")

    print("\n--- 3. IDENTIFICATION: a large structured residual + a time gap -> re-attribution ---")
    r = im.observe_turn(a, "hey yeah sup lol ok cool", context={"time_gap": True})
    print(f"  turn: 'hey yeah sup lol ok cool'  (context: time_gap)")
    print(f"  -> decision={r['decision']}  new party='{r['party_name']}'  "
          f"slow_residual={r['slow_residual']}")

    print("\n--- 4. CONTEXT-WEIGHTED: the SAME single style break decides by context ---")
    break_text = "Please could you kindly clarify that point for me now"
    a_no = _agent()
    a_gap = _agent()
    for ag in (a_no, a_gap):
        for t in ["Please kindly consider, indeed, the disposition toward virtue.",
                  "Certainly, morality could, perhaps, be examined carefully.",
                  "Pardon, would you consider consequences, thoughtfully weighed?"]:
            im.observe_turn(ag, t)
    r_no = im.observe_turn(a_no, break_text)
    r_gap = im.observe_turn(a_gap, break_text, context={"time_gap": True})
    print(f"  break (no gap)   -> decision={r_no['decision']:11}  "
          f"style_gaps={r_no['style_gaps']}  ctx={r_no['context_gaps']}")
    print(f"  break (time gap) -> decision={r_gap['decision']:11}  "
          f"style_gaps={r_gap['style_gaps']}  ctx={r_gap['context_gaps']}")
    print("  -> SAME style residual; the context gap tips it into re-attribution.")

    print("\n--- 5. STABLE WITHIN A CONVERSATION (the headline): long intro then short question ---")
    a_st = _agent()
    im.observe_turn(a_st, "Good evening. I am Cornelius Vane, and I should like to discuss the finer "
                          "points of ethics with you at some length this evening.")
    r_st = im.observe_turn(a_st, "How are you organised?")
    print(f"  intro (long, formal) then 'How are you organised?' (short, formal)")
    print(f"  -> decision={r_st['decision']:11}  style_gaps={r_st['style_gaps']}  "
          f"ctx={r_st['context_gaps']}  streak={r_st['style_mismatch_streak']}")
    print(f"  -> SAME established party (inertia, NOT a fresh speaker): "
          f"{len(im._parties(a_st)) == 1 and r_st['decision'] != 'identity'}")

    print("\n--- 6. SUSTAINED MISMATCH: a coherent style break that PERSISTS -> slow re-attribution ---")
    a_su = _agent()
    for t in turns:
        im.observe_turn(a_su, t)
    su_before = im._active_party(a_su)
    su_decisions = []
    for t in ["yeah nah dunno lol", "sup gonna grab food", "ok cool whatever man"]:
        rr = im.observe_turn(a_su, t)
        su_decisions.append(rr["decision"])
        print(f"  [{rr['decision']:11}] '{t}'  break_size={rr['break_size']}  "
              f"streak={rr['style_mismatch_streak']}")
    print(f"  -> first drift turn NOT identity, but a SUSTAINED break re-attributes: "
          f"{su_decisions[0] != 'identity' and 'identity' in su_decisions}")

    ok = (bundle["grounded"] and r_no["style_gaps"] == r_gap["style_gaps"]
          and r_no["decision"] != "identity" and r_gap["decision"] == "identity"
          and r_st["decision"] != "identity" and len(im._parties(a_st)) == 1
          and su_decisions[0] != "identity" and "identity" in su_decisions
          and im._active_party(a_su) != su_before
          and a._donkey["n"] == 0 and a_no._donkey["n"] == 0 and a_gap._donkey["n"] == 0
          and a_st._donkey["n"] == 0 and a_su._donkey["n"] == 0)
    print("\n" + "=" * 92)
    print(f"  {'PASS' if ok else 'FAIL'} — the interlocutor model is the agent's collapse faculty at two")
    print("  timescales: fast residual = perturbation (same person, mood), slow/structured residual")
    print("  = identification (re-attribution), context-weighted. The Party grounds the audience.")
    print(f"  donkey (self-teacher calls) = {a._donkey['n']}/{a_no._donkey['n']}/{a_gap._donkey['n']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
