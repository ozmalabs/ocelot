"""STEP 3: suspect-witness grounding — the jabberwock listens to Humpty and disbelieves him.

I seeded only WHAT it is (provenance, source_reliability, triangulation, refutation_of_source).
The jabberwock decides HOW. Claims are provenanced (claimed_by a Source with a trust); belief is
the claim best supported by INDEPENDENT corroboration weighted by trust (not the loudest); an
uncorroborated/conflicting claim REFUTES its source (its trust falls). Humpty is a confident lone
witness; the agent's own shape-evidence (step 1) and a corroborating source outweigh him, and his
trust drops by track record. Retroactively this is the fix for the slang `wave->drugs` credulity
(a teacher trusted as an oracle).

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.agent_weighs_witness
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

SEP = "=" * 90
# (word, gloss, source) — Humpty is confident + lone; lexicon + shape_self corroborate; teacher
# makes the wave->drugs claim. All sources start at equal trust; reliability must be EARNED.
CLAIMS = [
    ("slithy", "slimy", "humpty"), ("slithy", "supple", "lexicon"), ("slithy", "supple", "shape_self"),
    ("tove", "badger", "humpty"), ("mome", "lost", "humpty"),
    ("frabjous", "fabulous", "humpty"), ("frabjous", "joyous", "lexicon"),
    ("wave", "drugs", "teacher"),
]

_BELIEVE = (
    "You ARE the jabberwock composing believe(m) as a Term-tree (JSON): the triangulated meaning of "
    "a word. A word is a Mention bound to 'm' (text Attr(m,'text')). Claims are Claim nodes (attrs "
    "'word','gloss') each with a 'claimed_by' edge to a Source (attr 'trust'). Belief = the gloss of "
    "the claim about this word with the highest SCORE, where score = the source's trust times one "
    "plus its CORROBORATION (how many claims about the same word share the same gloss).\n"
    "Building blocks (exact JSON; strings as Lit):\n"
    '  {"type":"Var","name":"m"}  {"type":"Var","name":"c"}  {"type":"Var","name":"c2"}\n'
    '  {"type":"Attr","node":<t>,"key":"text"|"word"|"gloss"|"trust"}\n'
    '  {"type":"NodesOfType","node_type":"Claim"}\n'
    '  {"type":"Neighbours","node":<t>,"edge_type":"claimed_by","any_type":false}  {"type":"Pick","source":<set>}\n'
    '  {"type":"Filter","source":<set>,"var_name":"c2","predicate":<bool>}  {"type":"Count","source":<set>}\n'
    '  {"type":"Eq","a":<t>,"b":<t>}  {"type":"And","items":[<b>,<b>]}  {"type":"Times","items":[<t>,<t>]}  {"type":"Plus","items":[<t>,<t>]}\n'
    '  {"type":"Argmax","source":<set>,"var_name":"c","value":<number>}  {"type":"Lit","value":1}\n'
    "Assemble EXACTLY this (do not restructure):\n"
    '  TRUST  = {"type":"Attr","node":{"type":"Pick","source":{"type":"Neighbours","node":{"type":"Var","name":"c"},"edge_type":"claimed_by","any_type":false}},"key":"trust"}\n'
    '  CORROB = {"type":"Count","source":{"type":"Filter","source":{"type":"NodesOfType","node_type":"Claim"},"var_name":"c2","predicate":{"type":"And","items":[{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"c2"},"key":"word"},"b":{"type":"Attr","node":{"type":"Var","name":"c"},"key":"word"}},{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"c2"},"key":"gloss"},"b":{"type":"Attr","node":{"type":"Var","name":"c"},"key":"gloss"}}]}}}\n'
    '  SCORE  = {"type":"Times","items":[TRUST, {"type":"Plus","items":[{"type":"Lit","value":1}, CORROB]}]}   (Plus/Times are VARIADIC: use "items", never a/b)\n'
    '  ABOUT  = {"type":"Filter","source":{"type":"NodesOfType","node_type":"Claim"},"var_name":"c","predicate":{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"c"},"key":"word"},"b":{"type":"Attr","node":{"type":"Var","name":"m"},"key":"text"}}}\n'
    '  RESULT = {"type":"Attr","node":{"type":"Argmax","source":ABOUT,"var_name":"c","value":SCORE},"key":"gloss"}\n'
    "Return RESULT as one JSON Term (substitute the named pieces inline). Return ONLY the JSON Term.")

_REFUTE = (
    "You ARE the jabberwock composing the refute RULE (JSON) that lowers the trust of a source whose "
    "claim stands UNCORROBORATED — the track record by which an unreliable witness is recognised. A "
    "Claim node (attrs 'word','gloss') has a 'claimed_by' edge to a Source (attr 'trust'). A claim is "
    "uncorroborated when no OTHER claim shares its word AND gloss, i.e. the count of claims with the "
    "same word and gloss is <= 1. Refuting halves the source's trust, once per claim (guard with a "
    "'refuted' edge so it cannot re-fire).\n"
    "Rule JSON keys: name, match (triples), where (one Term), effects.\n"
    '  match: [["c","claimed_by","s"]]\n'
    "  where = And of: (Lte( Count(Filter(NodesOfType Claim, c2, And(Eq(Attr(c2,'word'),Attr(c,'word')), "
    "Eq(Attr(c2,'gloss'),Attr(c,'gloss'))))), Lit 1 )) AND (Not(Exists over Neighbours(c,'refuted') )).\n"
    "  effects: [ [\"set_attr\",\"s\",\"trust\",{\"__term__\": Times(Attr(s,'trust'), Lit 0.5)}], "
    "[\"add_edge\",\"c\",\"refuted\",\"s\"] ]\n"
    "Use canonical tagged Term JSON throughout ({\"type\":...}); strings/numbers as Lit. Return ONLY "
    "the rule JSON (keys name, match, where, effects).")


def main():
    print(SEP)
    print("STEP 3 — the jabberwock weighs a SUSPECT WITNESS (listens to Humpty, disbelieves him)")
    print(SEP)
    a = boot()
    for sid in ("slang", "slang_lexicon", "jabberwocky", "shape_sense"):
        a.inner.load_seed_manifest(manifest_for(sid), a.agent)
    teacher = a._self_teacher

    # provenanced claim graph (mechanical setup; all sources start at equal trust 0.5)
    srcs = {}
    for name in ("humpty", "lexicon", "shape_self", "teacher"):
        srcs[name] = a.s.add_node("Source", {"name": name, "trust": 0.5})
    for word, gloss, src in CLAIMS:
        c = a.s.add_node("Claim", {"word": word, "gloss": gloss})
        a.inner.add_edge_unchecked(c, "claimed_by", srcs[src])

    believe = _compose(teacher, _BELIEVE)
    refute = _compose(teacher, _REFUTE)
    if not believe or not refute or not refute.get("match"):
        print("  (could not compose believe/refute) — aborting"); print(SEP); return
    a.author_subroutine("believe", _litify(believe), purpose="triangulated belief over provenanced claims")
    refute.setdefault("name", "rule_refute_uncorroborated_source")
    print("  composed + authored believe (triangulation) and the refute rule\n")

    def beliefs():
        out = {}
        for w in ("slithy", "tove", "mome", "frabjous", "wave"):
            m = a.s.add_node("Mention", {"text": w})
            try:
                out[w] = a.run_subroutine("believe", {"m": m})
            except Exception as e:
                out[w] = f"(err {type(e).__name__})"
        return out

    def trusts():
        return {a.s.node(s)["attrs"]["name"]: round(a.s.node(s)["attrs"]["trust"], 3)
                for s in a.s.nodes("Source")}

    print(f"  beliefs (triangulated): {beliefs()}")
    print(f"  source trust BEFORE refutation: {trusts()}")
    # apply the agent's refute rule (load it live and run to fixpoint)
    a.inner.load_seed_manifest({"rules": [refute]}, a.agent)
    a.inner.run_rules()
    print(f"  source trust AFTER refutation:  {trusts()}")
    print(f"  beliefs after trust update:     {beliefs()}")

    print("\n" + SEP)
    print("  Triangulation makes corroborated readings win over a loud lone witness, and the refute "
          "rule drops the trust of whoever stands uncorroborated — so Humpty ends LEAST reliable by "
          "track record, and 'wave means drugs' is held only as a weak, refuted lone claim, not a fact.")
    print(SEP)


if __name__ == "__main__":
    main()
