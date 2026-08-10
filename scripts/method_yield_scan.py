"""method_yield_scan — measure the yield of method-sourcing over the curated
procedural (effect-verb) concepts.

A concept is 'procedural' iff its definition contains at least one operation verb
(the deep reader mints an SmEvent with a verb from a subject-resolved clause). We
run the full retrieve->deep-comprehend->map->synth->validate pipeline over each
and report N validated / total.

Usage: python3 scripts/method_yield_scan.py [--verbose]
"""
from __future__ import annotations
import json, os, sys, re

from substrate.world_adapter import WorldAdapter
from domains import comprehension_reader as cr
from domains import method_from_comprehension as mfc
from domains import method_synthesis as ms
from domains import read_method_draft as rmd
import scripts.method_from_deep_comprehension as drv

VERBOSE = "--verbose" in sys.argv


def is_procedural(defn: str) -> bool:
    """A definition is procedural iff, after subject-resolution, at least one
    clause has a lowercase-initial (subject-less) verb-shaped operation OR the
    definition contains an operational verb form (-s/-es endings on an action)."""
    # heuristic: any clause whose first token is a lowercase word that is NOT a
    # pure noun-list item — i.e. the definition names an operation on the concept.
    for clause in re.split(r"[.!?:;]\s*", defn):
        toks = clause.strip().split()
        if not toks:
            continue
        w = toks[0]
        if w[:1].islower() and len(toks) >= 2:
            return True
    return False


def measure(concepts: dict, verbose=False):
    # Scan ALL curated concepts (no fragile pre-filter). The denominator is the
    # full curated set; validated = sourced a runnable rule end-to-end.
    proc = {n: d for n, (d, f) in concepts.items()}
    validated = []
    walls = []
    for name in sorted(proc):
        defn = proc[name]
        try:
            cands = drv.operation_clauses(name, defn)
            model = None
            for cand in cands:
                wa = WorldAdapter()
                cr.read_and_comprehend(wa, cand)
                m = mfc.situation_model_to_method(wa, name="scan_" + name)
                if not m.get("wall"):
                    # try synth + validate
                    syn = ms.synthesise_rule_from_method(wa, m, binding=None, install=False)
                    if syn.get("wall"):
                        continue
                    draft = {"kind": "read_method_rule", "name": m["name"], "model": m,
                             "rules": syn["rules"], "effect": syn["effect"], "how": syn["how"]}
                    verdict = rmd.validate_by_running(draft)
                    if verdict["effect_matches"]:
                        model = (m, cand)
                        break
            if model:
                validated.append((name, model[0]["effect"], model[1]))
            else:
                walls.append(name)
        except Exception as e:
            walls.append(name + " [ERR:%s]" % e)
    return proc, validated, walls


def main():
    concepts = drv.load_curated_concepts()
    proc, validated, walls = measure(concepts, VERBOSE)
    print("Procedural (effect-verb) curated concepts: %d" % len(proc))
    print("VALIDATED (end-to-end sourced a rule): %d / %d" % (len(validated), len(proc)))
    for n, eff, cand in validated:
        print("   OK  %-26s %-10s  <- %r" % (n, eff, cand))
    if VERBOSE:
        print("WALLS (%d):" % len(walls))
        for w in walls:
            print("   .. %s" % w)


if __name__ == "__main__":
    main()
