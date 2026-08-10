"""Read to grow the lexicon, but TYPE each grounding (the jabberwock's design) and auto-persist.

The jabberwock decided how it filters: incorrect signal is a TYPE ERROR, not noise — a token grounded
into the lexicon that belonged elsewhere. So it routes by kind instead of deleting: all-digit shape ->
Numeral (a magnitude, not a vocabulary entry); a token the teacher grounds with a real meaning ->
lexical vocabulary; a token the teacher cannot define -> Unknown, held open. It composes the
discriminator (kind_of) from shape + whether the teacher returned a meaning. Correctly-typed
vocabulary is AUTO-PERSISTED to seeds/learned_lexicon.json so it compounds across boots.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_typed [word_budget]
"""
from __future__ import annotations
import json
import os
import random
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries
from domains.wiki_library import WikipediaLibrary
from scripts.agent_infers_meaning import _compose, _litify

SEP = "=" * 94
LEX_PATH = os.path.join(ROOT, "seeds", "learned_lexicon.json")

_KIND_PROMPT = (
    "You ARE the jabberwock composing kind_of(m) as a Term-tree (JSON) — your TYPE discriminator for "
    "a grounded token. A token Mention 'm' carries: 'shape' ('digit' = all digits, 'alpha' = letters, "
    "'mixed') and 'grounded' (1 if your teacher returned a real meaning, 0 if not). Incorrect signal "
    "is a TYPE ERROR — route it, do not delete it. Return the kind STRING: 'numeral' if the shape is "
    "digit; else 'lexical' if it grounded with a meaning; else 'unknown'.\n"
    "Term JSON forms (exact; strings as Lit):\n"
    '  {"type":"Var","name":"m"}   {"type":"Attr","node":<t>,"key":"shape"}   {"type":"Attr","node":<t>,"key":"grounded"}\n'
    '  {"type":"Eq","a":<t>,"b":<t>}   {"type":"Lit","value":"numeral"}\n'
    '  {"type":"IfThenElse","cond":<bool>,"then":<t>,"other":<t>}\n'
    "Return IfThenElse(Eq(Attr(m,'shape'),Lit 'digit'), Lit 'numeral', IfThenElse(Eq(Attr(m,'grounded'),"
    "Lit 1), Lit 'lexical', Lit 'unknown')). Return ONLY the JSON Term.")


def _shape(w):
    if w.isdigit():
        return "digit"
    if w.isalpha():
        return "alpha"
    return "mixed"


def _load_existing():
    if os.path.exists(LEX_PATH):
        try:
            d = json.load(open(LEX_PATH))
            return {n["attrs"]["name"] for n in d.get("nodes", []) if n.get("type") == "Concept"}, d
        except Exception:
            pass
    return set(), {"id": "learned_lexicon", "version": "1.0.0", "depends_on": [],
                   "description": "Vocabulary the agent grounded by reading + typed as lexical (the "
                   "jabberwock's kind_of discriminator). Auto-persisted; boots with it so reading "
                   "compounds. Numerals/names are NOT here — they are re-typed to their own kinds.",
                   "microtheory": {"name": "learned_lexicon", "description": "read-grown vocabulary"},
                   "nodes": []}


def main():
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    print(SEP)
    print("READ + TYPE each grounding (jabberwock's discriminator) + AUTO-PERSIST the lexicon")
    print(SEP)
    a = boot()
    attach_libraries(a, log=lambda *x: None)
    if os.path.exists(LEX_PATH):                       # compound across boots
        a.inner.load_seed_manifest(manifest_for("learned_lexicon"), a.agent)
    teacher_chain = a._self_teacher                    # on-disk teacher (for grounding)
    a.set_self_teacher(teacher_chain)
    wiki = WikipediaLibrary()

    # the jabberwock composes its TYPE discriminator (compose via its reasoning channel)
    from scripts.build_persona_faculty import _teacher as _claude
    kind = _compose(_claude(), _KIND_PROMPT) if os.environ.get("SPEECH_TEACHER") == "real" else None
    if not kind:   # deterministic fallback = the jabberwock's stated routing, materialised
        kind = {"type": "IfThenElse", "cond": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "shape"}, "b": {"type": "Lit", "value": "digit"}},
                "then": {"type": "Lit", "value": "numeral"},
                "other": {"type": "IfThenElse", "cond": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "grounded"}, "b": {"type": "Lit", "value": 1}},
                          "then": {"type": "Lit", "value": "lexical"}, "other": {"type": "Lit", "value": "unknown"}}}
    a.author_subroutine("kind_of", _litify(kind), purpose="type a grounding: numeral / lexical / unknown")

    known, manifest = _load_existing()
    counts = {"lexical": 0, "numeral": 0, "unknown": 0}
    new_lexical = {}
    attempted, articles = 0, 0
    t0 = time.time()
    rng = random.Random(7)
    while attempted < budget:
        art = wiki.random_article(rng)
        if not art or not art.section_names():
            continue
        text = " ".join(art.section_text(i) for i in range(min(3, len(art.section_names()))))
        articles += 1
        for raw in re.findall(r"[A-Za-z0-9']+", text):
            w = raw.strip("'").lower()
            if len(w) < 3 or w in known:
                continue
            attempted += 1
            sh = _shape(w)
            grounded = 0
            if sh != "digit":                          # only attempt to ground word-shaped tokens
                got = a.ground_unknowns(w)
                grounded = 1 if w in got else 0
            m = a.s.add_node("Mention", {"text": w, "shape": sh, "grounded": grounded})
            k = a.run_subroutine("kind_of", {"m": m}) or "unknown"
            counts[k] = counts.get(k, 0) + 1
            if k == "lexical":
                defn = a._taught_lookup.get("taught_" + w.replace("-", "_"), "")
                new_lexical[w] = defn if isinstance(defn, str) else ""
                known.add(w)
            elif k == "numeral":
                a.s.add_node("Numeral", {"text": w})   # re-typed to a magnitude, not vocabulary
            if attempted >= budget:
                break
        if articles % 5 == 0:
            print(f"  ...{articles} articles, {attempted} tokens | lexical {counts['lexical']} "
                  f"numeral {counts['numeral']} unknown {counts['unknown']} ({time.time()-t0:.0f}s)", flush=True)

    # AUTO-PERSIST the correctly-typed vocabulary to disk (merge), so it compounds next boot
    nid = max((n.get("local_id", 0) for n in manifest["nodes"]), default=0)
    for w, defn in new_lexical.items():
        nid += 1
        manifest["nodes"].append({"local_id": nid, "type": "Concept",
                                  "attrs": {"name": w, "definition": (defn or "")[:200], "domain": "read"}})
    json.dump(manifest, open(LEX_PATH, "w"), indent=2)
    total_persisted = len([n for n in manifest["nodes"] if n.get("type") == "Concept"])

    dt = time.time() - t0
    print(f"\n  read {articles} articles, {attempted} tokens in {dt:.0f}s")
    print(f"  TYPED: lexical(vocabulary) {counts['lexical']}  | numeral(re-typed) {counts['numeral']}  "
          f"| unknown(held) {counts['unknown']}")
    print(f"  AUTO-PERSISTED to seeds/learned_lexicon.json: {total_persisted} concepts "
          f"(+{len(new_lexical)} this run) — boots with them, so reading COMPOUNDS")
    print(f"  sample vocabulary learned: {sorted(new_lexical)[:30]}")
    print("\n" + SEP)
    print("  The jabberwock typed every grounding instead of dumping it in the lexicon: numbers re-typed "
          "to Numerals (not deleted), real words kept as vocabulary, undefinable held as Unknown — and "
          "the vocabulary is persisted to disk so the next boot starts where this left off.")
    print(SEP)


if __name__ == "__main__":
    main()
