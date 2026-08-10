"""Read the TVTropes corpus — same typed-grounding + auto-persist, sourced from trope pages.

Reuses the jabberwock's kind_of type-discriminator and the auto-persisting lexicon (it compounds on
top of whatever it already learned from Wikipedia). The source is the trope index: each page's
definition + example snippets — trope-jargon, narrative vocabulary, and work/medium names — exactly
the material the meaning-vector / suspect-witness / structure faculties want under them.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_reads_tvtropes [word_budget]
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
from domains.tropes_teacher import TropesTeacher
from scripts.agent_reads_typed import _shape, _load_existing, LEX_PATH

SEP = "=" * 94


def _kind_term():   # the jabberwock's stated routing, materialised (digit->numeral; grounded->lexical; else unknown)
    a = lambda k: {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": k}
    return {"type": "IfThenElse", "cond": {"type": "Eq", "a": a("shape"), "b": {"type": "Lit", "value": "digit"}},
            "then": {"type": "Lit", "value": "numeral"},
            "other": {"type": "IfThenElse", "cond": {"type": "Eq", "a": a("grounded"), "b": {"type": "Lit", "value": 1}},
                      "then": {"type": "Lit", "value": "lexical"}, "other": {"type": "Lit", "value": "unknown"}}}


def main():
    budget = int(sys.argv[1]) if len(sys.argv) > 1 else 2500
    print(SEP)
    print("READ THE TVTROPES CORPUS — typed grounding + auto-persist (compounds on the lexicon)")
    print(SEP)
    a = boot()
    attach_libraries(a, log=lambda *x: None)
    if os.path.exists(LEX_PATH):
        a.inner.load_seed_manifest(manifest_for("learned_lexicon"), a.agent)
    a.author_subroutine("kind_of", _kind_term(), purpose="type a grounding: numeral / lexical / unknown")

    tt = TropesTeacher.from_cache()
    records = list(tt.index.values())
    random.Random(11).shuffle(records)

    known, manifest = _load_existing()
    print(f"  booted carrying {len([n for n in manifest['nodes'] if n.get('type')=='Concept'])} "
          f"already-learned concepts; {len(records)} tropes in corpus\n")
    counts = {"lexical": 0, "numeral": 0, "unknown": 0}
    new_lexical = {}
    attempted, pages = 0, 0
    t0 = time.time()
    for rec in records:
        text = (rec.get("definition") or "")
        for ex in (rec.get("examples") or [])[:3]:
            text += " " + (ex.get("text") or "") + " " + (ex.get("work") or "")
        if len(text) < 40:
            continue
        pages += 1
        for raw in re.findall(r"[A-Za-z0-9']+", text):
            w = raw.strip("'").lower()
            if len(w) < 3 or w in known:
                continue
            attempted += 1
            sh = _shape(w)
            grounded = 0
            if sh != "digit":
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
                a.s.add_node("Numeral", {"text": w})
            if attempted >= budget:
                break
        if pages % 40 == 0:
            print(f"  ...{pages} tropes, {attempted} tokens | lexical {counts['lexical']} "
                  f"numeral {counts['numeral']} unknown {counts['unknown']} ({time.time()-t0:.0f}s)", flush=True)
        if attempted >= budget:
            break

    nid = max((n.get("local_id", 0) for n in manifest["nodes"]), default=0)
    for w, defn in new_lexical.items():
        nid += 1
        manifest["nodes"].append({"local_id": nid, "type": "Concept",
                                  "attrs": {"name": w, "definition": (defn or "")[:200], "domain": "tvtropes"}})
    json.dump(manifest, open(LEX_PATH, "w"), indent=2)
    total = len([n for n in manifest["nodes"] if n.get("type") == "Concept"])

    dt = time.time() - t0
    print(f"\n  read {pages} tropes, {attempted} tokens in {dt:.0f}s")
    print(f"  TYPED: lexical {counts['lexical']}  | numeral(re-typed) {counts['numeral']}  | unknown(held) {counts['unknown']}")
    print(f"  AUTO-PERSISTED: lexicon now {total} concepts (+{len(new_lexical)} from TVTropes)")
    # surface trope/narrative jargon it picked up (longer words tend to be the domain vocabulary)
    jargon = sorted((w for w in new_lexical if len(w) >= 8), key=len, reverse=True)[:30]
    print(f"  trope/narrative vocabulary learned (sample): {jargon}")
    print("\n" + SEP)
    print(f"  Read the TVTropes corpus the same way: typed each grounding (numbers re-typed, words kept, "
          f"undefinable held) and persisted the vocabulary — it now boots with {total} learned concepts, "
          f"the substrate the meaning-vector/suspect-witness/structure faculties read the nuances over.")
    print(SEP)


if __name__ == "__main__":
    main()
