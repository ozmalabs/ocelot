"""PROVE the agent's definitional comprehension is ENTITY-LIKE — it reads a
definition AGAINST a held generative MODEL, where the ABSENCE of an expected
element, or an element being DIFFERENT than expected, is itself SIGNAL
(predictive comprehension; prediction-error = information). And prove the
LEARNING: the grounding gets TRUER (right frame, right confidence, right sense,
right depth) — NOT an HLE score.

A competent reader holds a generative model of a definition (expects: FRAME,
REGISTER, TERM is-a GENUS, DIFFERENTIA) and comprehends by comparing PRESENT vs
EXPECTED. Each slot is read present | absent | different; absence/difference
carries meaning:
  · REGISTER ABSENT (unmarked) = the CANONICAL asserted-as-fact case -> EXACT,
    full confidence (a comprehended SIGNAL, not a null default).
  · REGISTER a hedge ('roughly'/'loosely'/'informally', OR the partitive
    'a kind/sort/type of') = a DEVIATION -> APPROXIMATE/INFORMAL, lower conf.
  · FRAME ABSENT = inherited from the active discourse frame / universal.
  · FRAME DIFFERENT than the term's held frame ('In music, a manifold ...' when
    'In mathematics, a manifold ...' is held) = a SENSE-SHIFT (homonym): a
    DISTINCT sense, NOT an overwrite of the held grounding.
  · GENUS DIFFERENT than the term's held genus = SURPRISE -> ground but FLAG for
    re-evaluation, don't silently overwrite.

ALL graph data (the expectation model + register/frame maps held on the
`definition` concept) applied generally; no LLM, no per-form Python, no Rust.

HONEST: what is still coarse — frame->Mt name-match (+ a domain map), a
two-and-a-bit-level register band, the sense-disambiguation heuristic
(frame-difference). The point proven is the LEARNING (truer grounding), not a
number.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains import grounded_representation as gr
from domains import construction_grammar as cg
from domains import read_and_ground as rag

SEP = "=" * 74


def _seed_primitive(s, name: str) -> None:
    for c in s.nodes("Concept"):
        if s.node(c)["attrs"].get("name") == name:
            return
    s.add_node("Concept", {"name": name, "origin": "seed_primitive"})


# ---------------------------------------------------------------------------
# A. COMPREHENSION is expectation-based — the present|absent|different SIGNALS.
# ---------------------------------------------------------------------------

def prove_comprehension() -> bool:
    print(SEP)
    print("A. COMPREHENSION reads PRESENT vs EXPECTED — absence/difference=SIGNAL")
    print(SEP)
    rows = []

    def check(text, want, keys):
        d = cg.extract_definition(text)
        got = {k: (d or {}).get(k) for k in keys}
        ok = d is not None and all(got[k] == want[k] for k in want)
        rows.append((text, ok))
        sig = (d or {}).get("signals")
        print(f"  {'OK ' if ok else 'FAIL'} {text!r}")
        print(f"       genus={got.get('genus')!r} register={got.get('register')!r}"
              f" status={got.get('register_status')!r} conf={got.get('confidence')}"
              f" frame={got.get('frame')!r} signals={sig}")
        return ok

    # canonical (register ABSENT/unmarked) = asserted-as-fact, EXACT, full conf.
    check("a manifold is a topological space",
          {"genus": "topological space", "register": "canonical",
           "register_status": "canonical", "confidence": 1.0},
          ["genus", "register", "register_status", "confidence", "frame"])
    # leading hedge = DEVIATION -> approximate / hedged / lower confidence.
    check("roughly speaking, a topological space is a geometric space",
          {"genus": "geometric space", "register": "approximate",
           "register_status": "hedged", "confidence": 0.85},
          ["genus", "register", "register_status", "confidence"])
    # partitive hedge: genus PAST the partitive + register approximate.
    check("a gadget is a kind of device",
          {"genus": "device", "register": "approximate",
           "register_status": "hedged"},
          ["genus", "register", "register_status"])
    check("a widget is a sort of device",
          {"genus": "device", "register": "approximate"},
          ["genus", "register"])
    # post-copula / inline adverbial register — no longer DROPPED.
    check("X is, roughly speaking, a topological space",
          {"genus": "topological space", "register": "approximate",
           "register_status": "hedged"},
          ["genus", "register", "register_status"])
    check("X is informally a device",
          {"genus": "device", "register": "informal",
           "register_status": "hedged"},
          ["genus", "register", "register_status"])
    # frame ABSENT -> inherited; frame PRESENT -> extracted.
    d = cg.extract_definition("a widget is a device")
    inherited = d["signals"].get("frame") == "inherited"
    print(f"  {'OK ' if inherited else 'FAIL'} frame ABSENT -> 'inherited' signal"
          f" (not a null): {d['signals']}")
    rows.append(("frame-absent inherited", inherited))

    return all(ok for _, ok in rows)


# ---------------------------------------------------------------------------
# B. SENSE-SHIFT — a different-frame reading is a DISTINCT sense, not overwrite.
# ---------------------------------------------------------------------------

def prove_sense_shift() -> bool:
    print()
    print(SEP)
    print("B. SENSE-SHIFT — 'In music, a manifold is a pipe' does NOT overwrite")
    print("   the held 'In mathematics, a manifold is a topological space'")
    print(SEP)
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    _seed_primitive(s, "topological_space")
    _seed_primitive(s, "pipe")
    s.add_node("Microtheory", {"name": "mathematics"})
    s.add_node("Microtheory", {"name": "music"})

    class CMath:
        _definition_feed = {"manifold":
                            "In mathematics, a manifold is a topological space"}
        _constructions = cg.load_constructions()

    r1 = rag.read_and_ground(s, "manifold", CMath())
    print(f"  math manifold: grounded={r1['grounded']} "
          f"frame_mt={r1['trace']['ground'].get('frame_mt_name')} "
          f"conf={r1['structure'].get('confidence')}")

    class CMusic:
        _definition_feed = {"manifold": "In music, a manifold is a pipe"}
        _constructions = cg.load_constructions()

    r2 = rag.read_and_ground(s, "manifold", CMusic())
    st2 = r2["structure"] or {}
    print(f"  music manifold: grounded={r2['grounded']} "
          f"name={st2.get('grounded_name')!r} sense_shift={st2.get('sense_shift')} "
          f"frame_mt={r2['trace'].get('ground', {}).get('frame_mt_name')}")

    math_id = gr._find_concept(s, "manifold")
    math_parts = [s.node(m)["attrs"].get("name")
                  for m in s.neighbours(math_id, "built_from")]
    music_id = gr._find_concept(s, "manifold__music")
    music_parts = ([s.node(m)["attrs"].get("name")
                    for m in s.neighbours(music_id, "built_from")]
                   if music_id else [])
    print(f"  held manifold(math): built_from={math_parts} "
          f"frame={s.node(math_id)['attrs'].get('frame')!r}")
    print(f"  new  manifold(music): exists={music_id is not None} "
          f"built_from={music_parts} "
          f"frame={s.node(music_id)['attrs'].get('frame') if music_id else None!r}")

    two_senses = (math_parts == ["topological_space"]
                  and music_id is not None and music_parts == ["pipe"]
                  and st2.get("sense_shift") is True
                  and s.node(music_id)["attrs"].get("sense_of") == "manifold")
    print(f"  -> TWO distinct senses preserved (math NOT overwritten): {two_senses}")
    return two_senses


# ---------------------------------------------------------------------------
# C. SURPRISE-GENUS — a different genus grounds but FLAGS, never silently drops.
# ---------------------------------------------------------------------------

def prove_surprise_genus() -> bool:
    print()
    print(SEP)
    print("C. SURPRISE-GENUS — 'a widget is an animal' (after widget->device)")
    print("   grounds the new edge but FLAGS for re-evaluation; held edge kept")
    print(SEP)
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    _seed_primitive(s, "device")
    _seed_primitive(s, "animal")

    class C1:
        _definition_feed = {"widget": "a widget is a device"}
        _constructions = cg.load_constructions()

    rag.read_and_ground(s, "widget", C1())

    class C2:
        _definition_feed = {"widget": "a widget is an animal"}
        _constructions = cg.load_constructions()

    r2 = rag.read_and_ground(s, "widget", C2())
    st = r2["structure"] or {}
    wid = gr._find_concept(s, "widget")
    parts = [s.node(m)["attrs"].get("name")
             for m in s.neighbours(wid, "built_from")]
    flagged = s.node(wid)["attrs"].get("needs_reevaluation")
    print(f"  reread comprehended (not 'already grounded'): {st != {}}")
    print(f"  genus_surprise={st.get('genus_surprise')} "
          f"needs_reevaluation={flagged}")
    print(f"  widget built_from now: {parts}  (held 'device' KEPT, 'animal' added)")
    ok = (st.get("genus_surprise") is True and flagged == 1
          and "device" in parts and "animal" in parts)
    print(f"  -> surprise grounded + flagged, held edge NOT silently dropped: {ok}")
    return ok


# ---------------------------------------------------------------------------
# D. THE LEARNING METRIC — grounding got TRUER (frame / confidence / sense / depth).
# ---------------------------------------------------------------------------

def prove_learning() -> bool:
    print()
    print(SEP)
    print("D. LEARNING METRIC — the grounding got TRUER (frame/confidence/")
    print("   sense/depth), the metric that matters (NOT an HLE number)")
    print(SEP)
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    # seed ONLY 'space' as the primitive — so the descent must climb
    # manifold -> topological_space -> space (depth 2), comprehending the
    # frame+register at the top hop and grounding to the seeded primitive.
    _seed_primitive(s, "space")
    s.add_node("Microtheory", {"name": "mathematics"})

    # a deep, frame+register-bearing chain comprehended hop by hop.
    class C:
        _definition_feed = {
            "manifold": ("In mathematics, a manifold is, roughly speaking, a "
                         "topological space that locally resembles Euclidean "
                         "space"),
            "topological_space": "a topological space is a space"}
        _constructions = cg.load_constructions()

    res = rag.ground_recursively(s, "manifold", C())
    st = res["structure"] or {}
    mid = gr._find_concept(s, "manifold")
    proof = gr.grounding_reaches_primitives(s, mid)
    ma = s.node(mid)["attrs"]
    frame_correct = ma.get("frame") == "mathematics"
    # math Mt resident -> the concept is bound INTO it (has_concept).
    math_mt = gr._find_microtheory(s, "mathematics")
    in_mt = math_mt is not None and mid in set(s.neighbours(math_mt, "has_concept"))
    conf_correct = abs(float(ma.get("grounding_confidence", -1)) - 0.85) < 1e-6
    status_correct = ma.get("grounding_status") == "hedged"
    depth_ok = proof["depth"] >= 2 and proof["grounded"]

    print(f"  grounded={res['grounded']}  cone depth={proof['depth']}  "
          f"primitives={proof['primitives']}")
    print(f"  frame-correct  : frame={ma.get('frame')!r} bound_in_math_Mt={in_mt}"
          f"  -> {frame_correct and in_mt}")
    print(f"  confidence-correct: grounding_confidence={ma.get('grounding_confidence')}"
          f" (hedged 0.85 from 'roughly speaking')  status={ma.get('grounding_status')!r}"
          f"  -> {conf_correct and status_correct}")
    print(f"  depth-correct  : recursive descent climbed >=2 hops to a primitive"
          f"  -> {depth_ok}")
    print("  (sense-correct proven in B: a homonym keeps two senses)")

    ok = frame_correct and in_mt and conf_correct and status_correct and depth_ok
    print(f"  -> the grounding is TRUER (right frame/confidence/sense/depth): {ok}")
    return ok


def main() -> int:
    print(SEP)
    print("ENTITY-LIKE DEFINITIONAL COMPREHENSION — read against expectations")
    print(SEP)
    print("A competent reader holds a generative MODEL of a definition and")
    print("comprehends by PRESENT vs EXPECTED; absence/difference = SIGNAL.")
    print("All graph data (expectation model on the `definition` concept). No LLM.")
    print()
    results = [
        ("A. comprehension is expectation-based (signals; canonical/hedged)",
         prove_comprehension()),
        ("B. sense-shift: a different-frame reading -> distinct sense (no overwrite)",
         prove_sense_shift()),
        ("C. surprise-genus: ground + flag, held edge not silently dropped",
         prove_surprise_genus()),
        ("D. LEARNING: grounding got truer (frame/confidence/sense/depth)",
         prove_learning()),
    ]
    print()
    print(SEP)
    print("SUMMARY (the LEARNING is the metric — not an HLE number)")
    print(SEP)
    all_ok = True
    for label, ok in results:
        all_ok = all_ok and ok
        print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    print()
    print(f"RESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}")
    print()
    print("STILL COARSE (honest): frame->Mt is a name-match + a domain map; the")
    print("register band is two-and-a-bit levels; sense-disambiguation is a")
    print("frame-difference heuristic. The point proven is the LEARNING (truer")
    print("grounding), not a score. Absence and difference are SIGNAL — the way a")
    print("competent human reads. No LLM, no per-form Python, no Rust.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
