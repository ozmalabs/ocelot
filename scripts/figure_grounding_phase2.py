"""PHASE 2 VERIFICATION — ground personification by WordNet animacy + verb agentivity. NO LLM.

The figure judge's `_animacy` (a `claude -p` forced-choice) is retired. Personification = an INANIMATE
SUBJECT performing an ANIMATE-AGENT action, grounded from the WordNet taxonomy: wn_animate(subject)==0
(inanimate noun) AND wn_verb_agentive(verb)==1 (animate-agent verb, by lexname OR selectional frame).
The `ground_personifies` rule reads UseTool Terms over role-tagged parts; classify_figure unchanged.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.figure_grounding_phase2
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs._native as _N
from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.symbolic_perception import register_symbolic_handlers, wn_animate, wn_verb_agentive

SEP = "=" * 96

# (name, determiner, subject, verb, expect_personification)
CORPUS = [
    ("the wind whispered", "the", "wind", "whispered", True),    # inanimate subj + communication verb
    ("the sun smiled",     "the", "sun", "smiled", True),        # inanimate subj + communication verb
    ("opportunity knocked", "",   "opportunity", "knocked", True),  # knock agentive by FRAME (7:1), not lexname
    ("the dog barked",     "the", "dog", "barked", False),       # subject ANIMATE -> not personification
    ("the rock fell",      "the", "rock", "fell", False),        # verb not agentive (fall) -> not
    ("the engine ran",     "the", "engine", "ran", False),       # precision: run ambiguous (5:3) -> abstains, not
]


def main():
    print(SEP)
    print("PHASE 2 — personification grounded by WordNet animacy + verb agentivity (frames). NO LLM.")
    print(SEP)
    a = boot()
    names = register_symbolic_handlers(_N)
    for s in ("figurative_language", "figure_grounding"):
        a.inner.load_seed_manifest(manifest_for(s), a.agent)
    print(f"\n  registered handlers: {names}; figure_grounding seed loaded (LLM judge NOT wired)\n")

    src_dict = a.s.add_node("Source", {"name": "dictionary", "trust": 0.9})
    src_cu = a.s.add_node("Source", {"name": "common_usage", "trust": 0.7})

    def build(name, det, subj, verb):
        lit = a.s.add_node("Reading", {"word": name, "gloss": name, "kind": "literal"})
        fig = a.s.add_node("Reading", {"word": name, "gloss": name, "kind": "figurative"})
        a.inner.add_edge_unchecked(lit, "claimed_by", src_dict)
        a.inner.add_edge_unchecked(fig, "claimed_by", src_cu)
        if det:
            a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": det}))
        a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": subj, "role": "subj"}))
        a.inner.add_edge_unchecked(fig, "has_part", a.s.add_node("Mention", {"text": verb, "role": "verb"}))
        return fig

    rows = [(name, subj, verb, exp, build(name, det, subj, verb)) for name, det, subj, verb, exp in CORPUS]
    a.inner.run_rules(20000)                        # detect_figure + ground_personifies (via UseTool)
    for *_, fig in rows:
        a.inner.set_attr(fig, "scored", 1)          # host releases the classifier
    a.inner.run_rules(20000)                        # classify_figure

    print(f"  {'figure':20} {'subj':11} anim {'verb':10} agtv  personif  {'kind':14} verdict")
    print("  " + "-" * 92)
    npass = 0
    for name, subj, verb, exp, fig in rows:
        an, ag = wn_animate(subj), wn_verb_agentive(verb)
        pf = a.s.node(fig)["attrs"].get("personifies") == 1
        kind = a.s.node(fig)["attrs"].get("figure_kind", "?")
        is_p = kind == "personification"
        ok = (is_p == exp) and (pf == exp)
        npass += ok
        print(f"  {name:20} {subj:11} {an:>4} {verb:10} {ag:>4}  {str(pf):>8}  {kind:14} "
              f"{'PASS' if ok else 'FAIL'} (expect {exp})")

    print("\n  " + "-" * 92)
    print(f"  {npass}/{len(rows)} as expected. Personification grounded with ZERO claude -p calls — `_animacy`")
    print(f"  is retired. Inanimate SUBJECT (wn_animate==0) + animate-agent VERB (lexname or 'Somebody'-lean")
    print(f"  frames) → personifies. 'opportunity knocked' caught by the frame ratio where lexname (contact)")
    print(f"  could not; 'the engine ran' abstains (run is 5:3 ambiguous) rather than false-firing.")
    print(SEP)


if __name__ == "__main__":
    main()
