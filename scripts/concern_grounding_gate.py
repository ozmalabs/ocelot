"""concern_grounding_gate — GATE for CONCERN-GROUNDING: where INDUCTION becomes
INVENTION. An induced concern's residual matches NO held term-family (shared=0,
because it's genuinely-new). GROUND it = COMPOSE a new term for the novel shape
from held machinery, so the novel concern closes the loop to callable.

The keystone: a shape IS the Fold-iterate of its residual (shape_made_by_residual)
+ the residual is a first-class object (held AntiUnifyWitness) -> the held
generative shape-math algebra turns an uncovered residual INTO a term. Grounding =
map the residual's predicates through the held RelationCue lexicon -> structural
relations -> compose the Fold-iterate of the residual-feedback recurrence (held
Fold/Plus/Times/Append) -> a term that GENERATES (captures) the shape.

ARCHITECTURE: lexicon read + Fold-iterate Term + Covers Term + graph mutation; no
Python law, no LLM, no decision-if over graph state. The coefficients are the
residual ROLES grounded from the lexicon (structure grounded; magnitudes unit
defaults), NOT hand-tuned.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/concern_grounding_gate.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import (induce_concern, learn_term_for_concern,
                                        ground_concern, _load_program, run_program_on_fresh)


def _cleanup():
    p = os.path.join(ROOT, "seeds", "programs.json")
    if os.path.exists(p):
        d = json.load(open(p))
        d["nodes"] = [n for n in d.get("nodes", [])
                      if not str(n.get("attrs", {}).get("name", "")).startswith("grounded_")]
        json.dump(d, open(p, "w"), indent=1)


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    try:
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    except Exception:
        pass
    ok = True

    # 1. FIRES ONLY WHEN NEEDED (discriminative boundary)
    print("=" * 78)
    print("GATE 1 — GROUNDING FIRES ONLY WHEN NEEDED (held-term concern -> not invoked; novel -> fires)")
    print("=" * 78)
    # a concern that DOES match a held term-family (learn_term_for_concern handles it)
    held_concern = learn_term_for_concern(a, ["inference"])
    print(f"  held-term concern 'inference': learn_term connected={held_concern.get('connected')} "
          f"(term_family={held_concern.get('term_family')}) -> grounding NOT needed")
    # a genuinely-novel induced concern
    obs = [["build", "STATE", "from", "PRIOR"], ["move", "STATE", "opposite", "ERROR"],
           ["bound", "STATE", "by", "THRESHOLD"]]
    ind = induce_concern(a, obs, name_hint="induced_damped_control")
    key = ind["capability_key"]
    d = learn_term_for_concern(a, [key])
    print(f"  novel induced concern {key}: learn_term connected={d.get('connected')} "
          f"shared_leaves={d.get('shared_leaves')} -> grounding NEEDED")
    fires_ok = held_concern.get("connected") and (not d.get("connected"))
    print("  -> discriminative boundary:", "OK" if fires_ok else "FAIL")
    ok &= fires_ok

    # 2 + 3. COVERS + CAPTURES (the honest depth control)
    print("\n" + "=" * 78)
    print("GATE 2+3 — the grounded term COVERS the residual AND CAPTURES the dynamics")
    print("=" * 78)
    g = ground_concern(a, [key])
    print(f"  grounded={g.get('grounded')} path={g.get('path')}")
    print(f"  grounded_relations (from held lexicon): {g.get('grounded_relations')}")
    print(f"  COVERS (composed FROM the residual's grounded relations): {g.get('covers')}")
    print(f"  CAPTURES (run -> reproduces dynamics): {g.get('captures')}  dynamics={g.get('dynamics')}")
    cov_cap_ok = g.get("grounded") and g.get("covers") and g.get("captures")
    print("  -> covers AND captures:", "OK" if cov_cap_ok else "FAIL (report which holds)")
    ok &= cov_cap_ok

    # 4. THE NEW TERM IS THE AGENT'S (donkey=0)
    print("\n" + "=" * 78)
    print("GATE 4 — the new term is the agent's (composed from held Terms; donkey=0)")
    print("=" * 78)
    import inspect, re
    import domains.reflective_faculty as rf
    src = inspect.getsource(rf.ground_concern) + inspect.getsource(rf._residual_relations)
    llm = len(re.findall(r"make_ask|claude|openai|set_self_teacher|\.chat\(", src))
    held_terms = all(t in src for t in ("Fold", "Plus", "Append", "run_program_on_fresh"))
    print(f"  LLM calls in grounding path: {llm}")
    print(f"  composed from held Terms (Fold/Plus/Append, run by Rust): {held_terms}")
    print(f"  grounded via held RelationCue lexicon (not hand-picked relations): {'_load_relation_cues' in inspect.getsource(rf._residual_relations)}")
    print(f"  DONKEY calls across the run: {calls['n']}")
    ok &= (llm == 0 and held_terms and calls["n"] == 0)

    # 5. CLOSES THE LOOP for a NOVEL concern (induced -> grounded -> callable)
    print("\n" + "=" * 78)
    print("GATE 5 — CLOSES THE LOOP for a genuinely-novel concern (induction->invention->compile)")
    print("=" * 78)
    loaded = _load_program(a.s, g["term_name"]) if g.get("grounded") else None
    live = run_program_on_fresh(loaded, g["env"]) if loaded else {}
    trail = [round(x, 3) for x in live["value"][2]][:12] if live.get("ran") else []
    closed = bool(trail) and g.get("term_name") and g.get("grounded")
    print(f"  induced({ind['residual_predicates']}) -> grounded term {g.get('term_name')} -> CALLABLE LIVE")
    print(f"  trajectory: {trail}")
    print(f"  -> a NEW capability the agent did not start with, tracing to the observed residual:",
          "OK" if closed else "FAIL")
    ok &= closed

    # NULL — the fully-novel residual walls honestly (predicate-grounding frontier)
    print("\n" + "=" * 78)
    print("HONEST WALL — a fully-novel residual (predicates outside the lexicon) walls (named frontier)")
    print("=" * 78)
    obs_novel = [["oscillate", "X", "around", "SETPOINT"], ["overshoot", "X", "then", "CORRECT"],
                 ["damp", "AMPLITUDE", "each", "CYCLE"]]
    indN = induce_concern(a, obs_novel)
    gN = ground_concern(a, [indN["capability_key"]])
    print(f"  fully-novel concern {indN['capability_key']}: grounded={gN.get('grounded')}")
    print(f"  wall: {str(gN.get('wall'))[:140]}")
    wall_ok = gN.get("grounded") is False
    ok &= wall_ok

    _cleanup()
    print("\n" + "=" * 78)
    print(("PASS" if ok else "FAIL"),
          "- CONCERN-GROUNDING: an induced novel concern (shared=0) is GROUNDED by composing the "
          "Fold-iterate of its residual-feedback recurrence from held Terms (grounded via the held "
          "lexicon) — it COVERS the residual AND CAPTURES the dynamics (runs -> damped oscillation), "
          "closing the loop to callable: induction->invention->compile, donkey=0. Honest wall: a "
          "fully-novel residual (predicates outside the lexicon) walls -> predicate-grounding frontier.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
