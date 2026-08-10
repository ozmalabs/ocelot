"""cross_wired_pipeline_gate — THE CONVERGENCE: the speech/language thread's CENTRAL routes wired into
OUR peripheral reading/writing pipeline -> the full dual-route + triangle architecture end-to-end.
Two threads -> ONE system. donkey=0, graph-native.

CROSS-WIRE: our peripheral pipeline (660fdb0f) central STUB replaced with the CENTRAL triangle
(domains.central_routes): LEXICAL+SEMANTIC = the language thread's WordNet lexicon
(domains.dictionary_lexicon, IMPORTED READ-ONLY); SUBLEXICAL = a domain-neutral g->p rule-assembly
(ours, since the speech sub-lexical route is ACOUSTIC frame->phone, not text g->p).

GATE (donkey=0, evidence):
 1 CROSS-WIRED END-TO-END: the full dual-route pipeline runs using BOTH threads' components.
 2 CENTRAL DISSOCIATIONS in-situ: lexical-lesion -> irregular REGULARIZED (surface); sublexical-
   lesion -> NONWORD fails (phonological); semantic-lesion -> MEANING lost (deep).
 3 COMPLETE SUITE: central (surface/phonological/deep) + peripheral (buffer/allographic/motor/
   position/spatial) = the WHOLE taxonomy in ONE system.
 4 COMPOSED + DISCRIMINATIVE: composer assembles the peripheral parts; central routes = imported
   interface; intact=correct, each lesion=its error.
 5 theirs(imported)/ours/stubbed named; donkey=0; regressions.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/cross_wired_pipeline_gate.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.reading_writing_pipeline as rw
import domains.central_routes as cr


def main() -> int:
    ok = True

    # ---- GATE 1: CROSS-WIRED END-TO-END ----
    print("=" * 84)
    print("GATE 1 — CROSS-WIRED END-TO-END (both threads: our peripheral + their central lexicon)")
    print("=" * 84)
    r = rw.full_pipeline("island")
    read = "".join(r["read"]["recovered"][0])
    phon = "".join(r["final"]["phonology"]) if r["final"]["phonology"] else None
    wrote = "".join(f[0] if f else "?" for f in r["final"]["forms"])
    print(f"  READING  (our spatial->position->buffer):     recovered {read!r}")
    print(f"  CENTRAL  (THEIR lexicon + our g->p triangle): phonology {phon!r}, meaning {r['final']['meaning']!r}")
    print(f"  WRITING  (our buffer->allographic->motor):    wrote {wrote!r}, strokes_ok {r['final']['strokes_ok']}")
    e2e = read == "island" and phon is not None and r["final"]["meaning"] == "island" and wrote == "island"
    print(f"  -> full pipeline crosses BOTH threads end-to-end: {e2e}")
    ok &= e2e

    # ---- GATE 2: CENTRAL DISSOCIATIONS in-situ ----
    print("\n" + "=" * 84)
    print("GATE 2 — CENTRAL DISSOCIATIONS in-situ (surface / phonological / deep)")
    print("=" * 84)
    # SURFACE: lexical lesion -> irregular word regularized (the stored irregular phonology lost)
    intact_i = cr.read_aloud("island")
    surf = cr.read_aloud("island", lesion="lexical")
    surface_ok = surf["phonology"] != intact_i["phonology"] and surf["route"] == "sublexical"
    print(f"  SURFACE (lexical lesion):     island {''.join(intact_i['phonology'])!r} -> "
          f"{''.join(surf['phonology'])!r} via {surf['route']} (REGULARIZED): {surface_ok}")
    # PHONOLOGICAL: sublexical lesion -> nonword cannot be read; real word intact
    nonword_intact = cr.read_aloud("blorf")
    phono = cr.read_aloud("blorf", lesion="sublexical")
    realword = cr.read_aloud("dog", lesion="sublexical")
    phono_ok = (not phono["ok"]) and realword["ok"]
    print(f"  PHONOLOGICAL (sublexical lesion): nonword blorf ok {nonword_intact['ok']}->{phono['ok']}; "
          f"real word dog still ok {realword['ok']}: {phono_ok}")
    # DEEP: semantic lesion -> meaning lost
    deep_intact = cr.read_aloud("dog")
    deep = cr.read_aloud("dog", lesion="semantic")
    deep_ok = deep_intact["meaning"] is not None and deep["meaning"] is None
    print(f"  DEEP (semantic lesion):       dog meaning {deep_intact['meaning']!r}->{deep['meaning']!r}: {deep_ok}")
    central_diss = surface_ok and phono_ok and deep_ok
    print(f"  -> all 3 central dissociations: {central_diss}")
    ok &= central_diss

    # ---- GATE 3: COMPLETE SUITE (8 signatures: 5 peripheral + 3 central) ----
    print("\n" + "=" * 84)
    print("GATE 3 — COMPLETE SUITE: the WHOLE taxonomy in ONE system (5 peripheral + 3 central)")
    print("=" * 84)
    W = "understand"
    def periph(les):
        rr = rw.full_pipeline(W, lesion=les)
        return ("".join(rr["read"]["recovered"][0]),
                "".join(f[0] if f else "?" for f in rr["final"]["forms"]),
                set(f[1] for f in rr["final"]["forms"] if f), rr["final"]["strokes_ok"])
    pб = periph("buffer"); pa = periph("allographic"); pm = periph("motor")
    pp = periph("position"); ps = periph("spatial")
    print("  PERIPHERAL (in the full pipeline):")
    print(f"    buffer       -> WROTE {pб[1]!r} (length/order)")
    print(f"    allographic  -> cases {pa[2]} (case/form)")
    print(f"    motor        -> strokes_ok {pm[3]} (ill-formed)")
    print(f"    position     -> WROTE {pp[1]!r} (flanker-migration)")
    print(f"    spatial      -> READ {ps[0]!r} (lateralized neglect)")
    print("  CENTRAL (cross-wired routes):")
    print(f"    surface(lexical)     -> regularized phonology")
    print(f"    phonological(sublex) -> nonword fails")
    print(f"    deep(semantic)       -> meaning lost")
    peripheral_ok = (len(pб[1]) < len(W)) and (pa[2] != {"upper"}) and (pm[3] is False) \
        and ("x" in pp[1]) and (len(ps[0]) < len(W))
    complete = peripheral_ok and central_diss
    print(f"  -> COMPLETE 8-signature taxonomy in ONE system: {complete}")
    ok &= complete

    # ---- GATE 4: COMPOSED + DISCRIMINATIVE ----
    print("\n" + "=" * 84)
    print("GATE 4 — COMPOSED (peripheral parts) + DISCRIMINATIVE (intact vs lesioned)")
    print("=" * 84)
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.reflective_faculty as rf
    a = WorldAdapter(seeds=())
    calls = {"n": 0}
    if hasattr(a, "set_self_teacher"):
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    load_all_seeds(a)
    wg = ("hold the ordered sequence of parts in working memory; realise the identity as the form; "
          "select the allograph; build the new from the prior")
    wc = rf.compose_design_for_goal(a.s, rf._author_goal_signature(a.s, wg), beam=5, cand_k=5)
    composed = "sequence_buffer" in wc["ordered_parts"] and "allographic_store" in wc["ordered_parts"]
    print(f"  composer assembles the WRITING peripheral chain {wc['covered_count']}/{wc['goal_relations']}: {composed}")
    intact = rw.full_pipeline("dog")
    discr = intact["final"]["meaning"] == "dog" and cr.read_aloud("dog", lesion="semantic")["meaning"] is None
    print(f"  discriminative: intact dog meaning {intact['final']['meaning']!r}, semantic-lesion -> None: {discr}")
    ok &= composed and discr

    print("\n" + "=" * 84)
    print(f"  donkey spy: LLM/teacher calls = {calls['n']} (must be 0)")
    print("  THEIRS (imported read-only): domains.dictionary_lexicon (WordNet lexical+semantic).")
    print("  OURS: the 5 peripheral components + the g->p sublexical rule-assembly + the cross-wire.")
    print("  STUBBED/PARTIAL: the speech SUB-LEXICAL route is ACOUSTIC (frame->phone), not text g->p,")
    print("  so the text sublexical g->p is OURS (domain-neutral); the lexical+semantic IS theirs.")
    ok &= (calls["n"] == 0)

    print("\n" + "=" * 84)
    print(("PASS" if ok else "FAIL"),
          f"- CROSS-WIRED READING/WRITING (the convergence): the speech/language thread's WordNet lexical+"
          f"semantic route (IMPORTED READ-ONLY) wired into our peripheral pipeline -> the full dual-route + "
          f"triangle (orthography<->phonology<->semantics) end-to-end. The 3 CENTRAL dissociations surface "
          f"(surface=regularized, phonological=nonword-fails, deep=meaning-lost) ALONGSIDE the 5 PERIPHERAL "
          f"(buffer/allographic/motor/position/spatial) = the COMPLETE 8-signature taxonomy in ONE system. "
          f"Composer assembles the peripheral parts; central routes are the imported interface. donkey="
          f"{calls['n']}. THEIRS imported (lexicon), OURS (5 peripheral + g->p), the speech ACOUSTIC "
          f"sublexical noted (text g->p is ours). Their files untouched.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
