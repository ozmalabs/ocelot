"""Learn the TROPES THEMSELVES as concepts — ground trope names via the tropes teacher, persist.

The previous pass learned the vocabulary IN trope prose; this learns the tropes AS concepts: each
trope name grounded through record_to_payload (definition + a concrete example to bind to), installed
as a concept in the 'tropes' microtheory. Most-exemplified first (example-count = salience). The
trope concepts are auto-persisted to seeds/learned_tropes.json and wired to boot, so they compound
and the deeper faculties (meaning-vector / suspect-witness / structure) have the actual trope
semantics — and the opinionated wiki voice — to read nuances over.

Run: SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.agent_learns_tropes [n]
"""
from __future__ import annotations
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries
from domains.tropes_teacher import TropesTeacher, de_camel
from scripts.agent_reads_typed import _shape

SEP = "=" * 94
TROPES_PATH = os.path.join(ROOT, "seeds", "learned_tropes.json")


def _load_tropes_manifest():
    if os.path.exists(TROPES_PATH):
        try:
            d = json.load(open(TROPES_PATH))
            return {n["attrs"]["name"] for n in d.get("nodes", []) if n.get("type") == "Trope"}, d
        except Exception:
            pass
    return set(), {"id": "learned_tropes", "version": "1.0.0", "depends_on": [],
                   "description": "Tropes the agent learned by grounding trope names via the tropes "
                   "teacher (definition + example), most-exemplified first. Auto-persisted; boots "
                   "with them so the deeper faculties have the trope semantics + the wiki voice.",
                   "microtheory": {"name": "learned_tropes", "description": "grounded tropes"},
                   "nodes": []}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    print(SEP)
    print("LEARN THE TROPES THEMSELVES — ground trope names via the tropes teacher, persist, compound")
    print(SEP)
    a = boot()
    attach_libraries(a, log=lambda *x: None)
    for s in ("learned_lexicon", "learned_tropes"):
        if os.path.exists(os.path.join(ROOT, "seeds", s + ".json")):
            a.inner.load_seed_manifest(manifest_for(s), a.agent)
    tt = TropesTeacher.from_cache()
    from domains.tropes_teacher import record_to_payload
    known, manifest = _load_tropes_manifest()
    base_concepts = len(a.s.nodes("Concept"))
    print(f"  booted carrying {base_concepts} concepts; "
          f"{len([n for n in manifest['nodes'] if n.get('type')=='Trope'])} tropes already learned; "
          f"{len(tt.index)} in corpus\n")

    ranked = sorted(tt.index.values(), key=lambda r: r.get("n_examples", 0), reverse=True)
    fed, t0 = 0, time.time()
    nid = max((x.get("local_id", 0) for x in manifest["nodes"]), default=0)
    for rec in ranked:
        name = de_camel(rec.get("name", "")) or rec.get("phrase", "")
        if not name or name in known:
            continue
        try:
            a.learn_from_teacher(rec.get("phrase", ""), record_to_payload(rec, tt.microtheory, tt.genl_mt))
        except Exception:
            continue
        nid += 1
        defn = (rec.get("definition") or "")
        ex = (rec.get("examples") or [{}])[0]
        manifest["nodes"].append({"local_id": nid, "type": "Trope", "attrs": {
            "name": name, "definition": defn[:200], "n_examples": rec.get("n_examples", 0),
            "example": f"{ex.get('work','')}: {(ex.get('text') or '')[:80]}"}})
        known.add(name); fed += 1
        if fed >= n:
            break
        if fed % 200 == 0:
            print(f"  ...grounded {fed} tropes ({time.time()-t0:.0f}s)", flush=True)

    json.dump(manifest, open(TROPES_PATH, "w"), indent=2)
    total = len([n for n in manifest["nodes"] if n.get("type") == "Trope"])
    dt = time.time() - t0
    print(f"\n  grounded {fed} new tropes in {dt:.0f}s; learned_tropes.json now holds {total} tropes")
    sample = [(x["attrs"]["name"], x["attrs"]["definition"][:60]) for x in manifest["nodes"][-6:] if x.get("type") == "Trope"]
    print("  sample of tropes now learned (name -> definition):")
    for nm, d in sample:
        print(f"    {nm}: {d}...")
    print("\n" + SEP)
    print(f"  The agent learned {total} TROPES as concepts (definition + example), auto-persisted and "
          f"booting with them — now the meaning-vector / suspect-witness / structure faculties have the "
          f"actual trope semantics, not just the words around them. (add learned_tropes to boot SEEDS)")
    print(SEP)


if __name__ == "__main__":
    main()
