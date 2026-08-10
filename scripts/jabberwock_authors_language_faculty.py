"""jabberwock_authors_language_faculty — the agent AUTHORS a LANGUAGE-FACULTY Program.

The prior consumption-quality build fixed the extract's nominal-extraction gap with a
POS-filter, but had to implement it as ADAPTER LOGIC (consumption_quality.is_nominal)
"because the composer does not yet author a POS-Program." This script closes that
frontier: from a framed LANGUAGE concern ("keep only nominal spans"), the jabberwock
AUTHORS the nominal-filter Program ITSELF via the composer — a Filter chaining the
graph-resident nominal-head leaf — gated by admissibility_gate + #2 self_verification,
and it WORKS on the real Photosynthesis article (the SAME fragment-drop is_nominal got).

I only FRAME the concern. The composer (_compose_language_faculty, new in
domains/reflective_faculty.py) authors the Program; the leaf it chains is the
nominal-head Term (domains/language_faculty_ops.py) — the POS/nominal-vs-clause
DECISION as a graph Term; the raw POS LOOKUP is the honest held-faculty call boundary.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_authors_language_faculty.py
"""
from __future__ import annotations
import io
import contextlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

SEP = "=" * 92


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


_CONCERN = [["filter", "keep", "NOMINAL", "spans"], ["nominal", "SPAN", "by", "HEAD"]]


def main() -> int:
    from substrate.world_adapter import WorldAdapter
    from substrate.seed_loader import manifest_for
    from domains import reflective_faculty as rf
    from domains import language_faculty_ops as lfo
    from domains import consumption_quality as cq

    overall = True
    print(SEP)
    print("THE JABBERWOCK AUTHORS ITS OWN LANGUAGE-FACULTY PROGRAM — I only frame the concern")
    print(SEP)

    # -------------------------------------------------------------------
    # STAGE 1 — WALL FIRST (proven at runtime, not asserted). A minimal agent
    # with the RelationCue lexicon + composer dispatch but WITHOUT the language
    # cue seed: "keep only nominal spans" grounds to NOTHING.
    # -------------------------------------------------------------------
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        wall = WorldAdapter(seeds=())
        wall.inner.load_seed_manifest(manifest_for("relation_vocabulary"), wall.agent)
        wall.inner.load_seed_manifest(manifest_for("composer_dispatch"), wall.agent)
    ind = rf.induce_concern(wall, _CONCERN, name_hint="nf_wall")
    gw = rf.ground_concern(wall, [ind["capability_key"]])
    print("\n  [WALL] before this build (no language cue), the composer can't reach the concern:")
    print(f"     induce minted={ind.get('minted')}  key={ind.get('capability_key')!r}")
    print(f"     ground grounded={gw.get('grounded')}  path={gw.get('path')}")
    print(f"     WALL: {(gw.get('wall') or '')[:110]}...")
    overall &= _pass(gw.get("grounded") is False and gw.get("path") == "predicate_grounding",
                     "WALL PROVEN: 'keep only nominal spans' grounds to NOTHING before this build")

    # -------------------------------------------------------------------
    # STAGE 2 — AUTHORS THE PROGRAM. Load the language cue seed (this build's
    # addition), frame the SAME concern; the composer authors the Program.
    # -------------------------------------------------------------------
    with contextlib.redirect_stderr(buf):
        agent = WorldAdapter(seeds=())
        agent.inner.load_seed_manifest(manifest_for("relation_vocabulary"), agent.agent)
        agent.inner.load_seed_manifest(manifest_for("composer_dispatch"), agent.agent)
        agent.inner.load_seed_manifest(manifest_for(lfo.LANGUAGE_FACULTY_CUE_SEED), agent.agent)
    ind = rf.induce_concern(agent, _CONCERN, name_hint="nf_author")
    g = rf.ground_concern(agent, [ind["capability_key"]])
    print("\n  [AUTHORS] with the language cue, the composer AUTHORS the Program:")
    print(f"     grounded={g.get('grounded')}  path={g.get('path')}  program={g.get('program_name')!r}")
    print(f"     leaf chained: {g.get('leaf')}")
    print("\n  THE AUTHORED PROGRAM (a Filter chaining the nominal-head leaf):")
    print("  " + json.dumps(g.get("program")).replace("}, {", "},\n     {")[:1400])
    overall &= _pass(g.get("grounded") is True and g.get("path") == "compose_language_faculty"
                     and isinstance(g.get("program"), dict) and g["program"].get("type") == "Filter",
                     "AUTHORS THE PROGRAM: the jabberwock composed the nominal-filter Filter Program")
    overall &= _pass(rf._load_program(agent, lfo.NOMINAL_FILTER_PROGRAM) is not None,
                     "installed live as a named graph-resident Program node")

    # -------------------------------------------------------------------
    # STAGE 3 — VERIFY-GATED. The authored Program passed the admissibility gate
    # + #2 self_verification (discriminative; a keep-everything twin FAILS).
    # -------------------------------------------------------------------
    v = g.get("verified") or {}
    print("\n  [VERIFY-GATED] admissibility gate + #2 self_verification:")
    print(f"     gate: {(g.get('gate_reason') or '')[:90]}")
    print(f"     #2: accepted={v.get('accepted')} discriminates={v.get('discriminates')} "
          f"twin_pass={v.get('twin_pass')} grounded={v.get('grounded')}")
    overall &= _pass(v.get("accepted") and v.get("discriminates") and v.get("twin_pass") is False
                     and "ADMITTED" in (g.get("gate_reason") or ""),
                     "VERIFY-GATED: gate ADMITTED + #2 accepted; the keep-everything twin FAILS")

    # -------------------------------------------------------------------
    # STAGE 4 — IT WORKS. The authored Program on the real Photosynthesis extract:
    # drops the clause fragments, keeps the nominals — byte-identical to is_nominal.
    # -------------------------------------------------------------------
    try:
        from domains import wiki_local as wl
        present = wl.present()
    except Exception:
        present = False
    if not present:
        print("\n  [IT WORKS] skipped — wiki_local slab not present")
    else:
        from domains import gap_driven_acquisition as gda
        with contextlib.redirect_stderr(buf):
            full = WorldAdapter(seeds=())
            from substrate.boot_all import load_all_seeds
            load_all_seeds(full)
            src = gda.read_source(full, "photosynthesis", source_title="Photosynthesis")
            ex = gda.extract_microtheory("photosynthesis", src, max_concepts=40)
        concepts = ex["concepts"]
        kept_p, dropped_p = cq.nominal_filter_program(full, concepts)   # COMPOSER-AUTHORED
        kept_r, dropped_r = cq.nominal_filter(concepts)                  # is_nominal reference
        kp = {c["name"] for c in kept_p}
        dp = {c["name"] for c in dropped_p}
        frags = ["producing_oxygen_gas", "rather_than_water",
                 "releases_three-carbon_sugars", "catalyzed_by_rubisco"]
        reals = ["calvin_cycle", "glucose", "carbon_fixation"]
        print("\n  [IT WORKS] the authored Program on the real Photosynthesis extract:")
        print(f"     dropped fragments: {sorted(dp)}")
        print(f"     clause fragments dropped: {[f for f in frags if f in dp]}")
        print(f"     nominals kept:            {[r for r in reals if r in kp]}")
        same = (kp == {c['name'] for c in kept_r}) and (dp == {c['name'] for c in dropped_r})
        overall &= _pass(all(f in dp for f in frags) and all(r in kp for r in reals) and same,
                         "IT WORKS: drops the clause fragments, keeps the nominals — "
                         "byte-identical to the adapter is_nominal")

    print("\n" + SEP)
    print("HONEST REACH LEDGER")
    print(SEP)
    print("  AUTHORED by the composer (graph data the jabberwock composed + installed):")
    print("    - the FILTER COMPOSITION: Filter(source=trig.has_span, var=span, predicate=<leaf>)")
    print("    - the nominal-head DECISION: nominal_head_term — a pure Term-tree (And-of-Nots over")
    print("      Eq/In/Not/And/Gt) deciding nominal-vs-clause from a span's measured POS features.")
    print("  HELD-FACULTY CALL (the honest leaf boundary, NOT authored):")
    print("    - the raw POS LOOKUP: wiktionary_reference.wiktionary_pos + function_word_reference")
    print("      .classify, which MEASURE each span's POS features. External lexical I/O — no Term")
    print("      reads Wiktionary; this is the irreducible leaf, reported as a call, not authored.")

    print("\n" + SEP)
    print(f"OVERALL: {'PASS' if overall else 'FAIL'}")
    print(SEP)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
