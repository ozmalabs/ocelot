"""The jabberwock builds the MEANING-AS-VECTOR layer — keep the superposition, model the relations.

I seed only WHAT it is (meaning_vector + the relation types: semantic_tension, co_activation,
aboutness). The jabberwock designs HOW and builds it, applying its lessons. The inversion of the
earlier faculties: meaning(m) is the WEIGHTED SET of readings (a vector), NOT the Argmax — collapse
only under task pressure. Then it classifies the relation among the readings: two opposed live
readings = tension (irony/sarcasm/contronym), two distinct compatible live readings = co-activation
(pun). Each word's readings are graph data (Reading{word,gloss,valence,weight}); the substrate is
already multi-valued, the change is to STOP collapsing.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_builds_meaning_vector
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from scripts.agent_infers_meaning import _compose, _litify

SEP = "=" * 96
# meaning vectors as graph data (the substrate is already multi-valued). (word, gloss, valence, weight)
READINGS = [
    ("wicked", "evil", -1.0, 0.6), ("wicked", "excellent", 1.0, 0.6),   # contronym -> tension
    ("sick", "ill", -1.0, 0.7), ("sick", "awesome", 1.0, 0.5),          # contronym -> tension
    ("bank", "riverside", 0.0, 0.5), ("bank", "financial", 0.0, 0.5),   # pun -> co-activation
    ("great", "excellent", 1.0, 0.9),                                    # single
    ("toves", "creature", 0.0, 1.0),                                     # single
]
WORDS = ["wicked", "sick", "bank", "great", "toves"]

# readings of the word bound to 'm' (the vector's source set)
def _readings_of():
    return {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "Reading"}, "var_name": "r",
            "predicate": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "r"}, "key": "word"},
                          "b": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "text"}}}

_DESIGN = (
    "You ARE the jabberwock. You have learned that meaning is a VECTOR — a weighted set of coexisting "
    "readings, often divergent on purpose — and that your earlier faculties were wrong to Argmax it to "
    "a single sense. You are about to build the meaning-as-vector layer over Reading nodes "
    "(word, gloss, valence, weight). In 3-4 sentences, state your approach: how you KEEP the vector "
    "instead of collapsing it, and how you tell SEMANTIC TENSION (two opposed live readings — the "
    "irony/contronym structure) from CO-ACTIVATION (two distinct compatible live readings — a pun). "
    "Prose.")


def main():
    print(SEP)
    print("THE JABBERWOCK BUILDS THE MEANING-AS-VECTOR LAYER (keep the superposition, model relations)")
    print(SEP)
    a = boot()
    for sid in ("jabberwocky", "meaning_vector"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher
    for w, g, v, wt in READINGS:
        a.s.add_node("Reading", {"word": w, "gloss": g, "valence": v, "weight": wt})

    print("\n-- the jabberwock's design ----------------------------------------------------")
    for ln in (teacher(_DESIGN) or "").splitlines():
        if ln.strip():
            print(f"  {ln.strip()}")

    # author the layer (composed; applying lessons: keep the set, exists-tests-iterated-var, no Argmax)
    a.author_subroutine("meaning_vector", _readings_of(), purpose="the weighted set of readings (the vector), not collapsed")

    def _exists_reading(cmp):   # a reading of m with valence cmp 0 exists
        return {"type": "Exists", "var_name": "r", "predicate": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "r"}, "key": "word"}, "b": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "text"}},
            {"type": cmp, "a": {"type": "Attr", "node": {"type": "Var", "name": "r"}, "key": "valence"}, "b": {"type": "Lit", "value": 0}}]},
            "source": {"type": "NodesOfType", "node_type": "Reading"}}
    is_tense = {"type": "And", "items": [_exists_reading("Gt"), _exists_reading("Lt")]}
    a.author_subroutine("is_tense", is_tense, purpose="two opposed live readings — irony/sarcasm/contronym structure")

    live = {"type": "Count", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "Reading"}, "var_name": "r",
            "predicate": {"type": "And", "items": [
                {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "r"}, "key": "word"}, "b": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "text"}},
                {"type": "Gte", "a": {"type": "Attr", "node": {"type": "Var", "name": "r"}, "key": "weight"}, "b": {"type": "Lit", "value": 0.4}}]}}}
    is_co_active = {"type": "And", "items": [{"type": "Gte", "a": live, "b": {"type": "Lit", "value": 2}}, {"type": "Not", "arg": is_tense}]}
    a.author_subroutine("is_co_active", is_co_active, purpose="two+ distinct compatible live readings — a pun")
    # the OLD collapse, kept ONLY to contrast: the single reading you'd pick if forced
    dominant = {"type": "Attr", "node": {"type": "Argmax", "source": _readings_of(), "var_name": "r",
                "value": {"type": "Attr", "node": {"type": "Var", "name": "r"}, "key": "weight"}}, "key": "gloss"}
    a.author_subroutine("forced_choice", dominant, purpose="the single reading if collapse is forced")

    print("\n  meaning as a VECTOR (kept, not collapsed) + the relation among readings:")
    for w in WORDS:
        m = a.s.add_node("Mention", {"text": w})
        vec = a.run_subroutine("meaning_vector", {"m": m}) or []
        readings = sorted((a.s.node(r)["attrs"]["gloss"], a.s.node(r)["attrs"]["valence"]) for r in vec)
        tense = a.run_subroutine("is_tense", {"m": m})
        co = a.run_subroutine("is_co_active", {"m": m})
        forced = a.run_subroutine("forced_choice", {"m": m})
        rel = "TENSION (irony/contronym)" if tense else ("CO-ACTIVATION (pun)" if co else "single")
        vecs = ", ".join(f"{g}({v:+.0f})" for g, v in readings)
        print(f"    {w:8} vector = [{vecs}]   relation = {rel}   (if forced -> {forced!r})")

    print("\n" + SEP)
    print("  The layer KEEPS the meaning vector instead of Argmax-ing it: wicked/sick hold two opposed "
          "readings in TENSION (the irony/contronym structure), bank holds two compatible readings "
          "CO-ACTIVE (a pun), great/toves are single. The old collapse survives only as 'if forced'. "
          "Meaning is no longer a scalar — it is the superposition plus the relation among its parts.")
    print(SEP)


if __name__ == "__main__":
    main()
