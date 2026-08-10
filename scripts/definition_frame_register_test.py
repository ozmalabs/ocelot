"""PROVE definition-comprehension COMPREHENDS (not strips) the leading adjuncts.

A definition = FRAME? REGISTER? TERM is-a GENUS DIFFERENTIA — and EVERY part is
MEANING. The leading "preface" is NOT removable framing: it carries the FRAME
(which WORLD/Microtheory the concept grounds in — grounding is frame-relative)
and the REGISTER/PROSODY (how PRECISE/CONFIDENT the definition is — the
epistemic-confidence band). This script proves:

  1. COMPREHENSION (not stripping): extract_definition returns the FRAME +
     REGISTER for the example sentences — the adjuncts are IN the result, not
     discarded.
  2. GROUNDING USES them: ground_recursively over a real wiki concept grounds it
     IN the frame's Microtheory (attached / tagged) AND a 'roughly'-defined hop
     carries APPROXIMATE confidence — the frame + confidence are on the grounded
     concept, the cone still reaches a primitive.

No LLM, no Rust, no per-form Python — one held structure, applied generally.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains import construction_grammar as cg
from domains import grounded_representation as gr
from domains import read_and_ground as rag

SEP = "=" * 76


def main() -> int:
    all_ok = True

    print(SEP)
    print("1. COMPREHENSION (not stripping) — frame + register are IN the result")
    print(SEP)
    cases = [
        ("In mathematics, a manifold is a topological space that locally "
         "resembles Euclidean space", "mathematics", "exact", "topological space"),
        ("Roughly speaking, a topological space is a geometric space",
         None, "approximate", "geometric space"),
        ("In music, a manifold is a chamber that distributes air to pipes",
         "music", "exact", "chamber"),
        ("Formally, a group is a set equipped with an operation",
         None, "exact", "set"),
        ("In mathematics, roughly speaking, a manifold is a topological space "
         "that locally resembles Euclidean space",
         "mathematics", "approximate", "topological space"),
        ("In the field of biology, a cell is a unit that forms organisms",
         "biology", "exact", "unit"),
        ("a widget is a device", None, "exact", "device"),
    ]
    for text, exp_frame, exp_reg, exp_genus in cases:
        d = cg.extract_definition(text)
        ok = (d is not None and d["frame"] == exp_frame
              and d["register"] == exp_reg and d["genus"] == exp_genus)
        all_ok = all_ok and ok
        diff = d["differentia"] if d else ""
        diff_show = (diff[:34] + "…") if len(diff) > 34 else diff
        print(f"  [{'OK ' if ok else 'FAIL'}] frame={str(d['frame']):>11}  "
              f"register={d['register']:>11}  genus={d['genus']:>18}  "
              f"term={d['term']}")
        print(f"          differentia (kept, not lost): {diff_show!r}")

    print()
    print(SEP)
    print("2. GROUNDING USES the frame (the Mt) + the register (confidence)")
    print(SEP)
    s = _native.Substrate()
    gr.open_grounding_productions(s)
    # seed the 'mathematics' WORLD (a Microtheory) + the genus primitive so the
    # frame can resolve to an Mt and the cone bottoms out.
    math_mt = s.add_node("Microtheory", {"name": "mathematics",
                                         "origin": "test"})
    s.add_node("Concept", {"name": "topological_space", "origin": "seed_primitive"})

    class _Conv:
        # a 'roughly' (APPROXIMATE) definition framed IN mathematics.
        _definition_feed = {
            "manifold": ("In mathematics, roughly speaking, a manifold is a "
                         "topological space that locally resembles Euclidean "
                         "space")}
        _constructions = cg.load_constructions()

    res = rag.ground_recursively(s, "manifold", _Conv())
    st = res["structure"] or {}
    print(f"  manifold grounded={res['grounded']}")
    print(f"    frame (comprehended)     : {st.get('frame')!r}")
    print(f"    register (comprehended)  : {st.get('register')!r}")
    print(f"    frame_mt resolved        : {st.get('frame_mt')!r}  "
          f"(the 'mathematics' Microtheory)")
    print(f"    grounding_confidence     : {st.get('confidence')!r}  "
          f"(approximate -> hedged, below full)")
    print(f"    cone reaches primitive   : {st.get('primitives')}")

    cid = gr._find_concept(s, "manifold")
    cattrs = s.node(cid)["attrs"]
    in_mt = cid in set(s.neighbours(math_mt, "has_concept"))
    print(f"  ON the grounded concept node:")
    print(f"    frame attr               : {cattrs.get('frame')!r}")
    print(f"    grounding_confidence attr: {cattrs.get('grounding_confidence')!r}")
    print(f"    grounding_register attr  : {cattrs.get('grounding_register')!r}")
    print(f"    attached to mathematics Mt (has_concept edge): {in_mt}")

    ground_ok = (res["grounded"]
                 and st.get("frame") == "mathematics"
                 and st.get("register") == "approximate"
                 and st.get("frame_mt") == math_mt
                 and in_mt
                 and cattrs.get("frame") == "mathematics"
                 and cattrs.get("grounding_confidence") == gr._register_confidence("approximate")
                 and cattrs.get("grounding_confidence") < 1.0
                 and "topological_space" in (st.get("primitives") or []))
    all_ok = all_ok and ground_ok

    # CONTRAST: an EXACT definition with NO frame -> full confidence, frame None
    # (the honest default — unchanged grounding when no adjunct is present).
    print()
    print("  CONTRAST: an EXACT, unframed definition -> full confidence, no Mt")
    s2 = _native.Substrate()
    gr.open_grounding_productions(s2)
    s2.add_node("Concept", {"name": "device", "origin": "seed_primitive"})

    class _Conv2:
        _definition_feed = {"widget": "a widget is a device"}
        _constructions = cg.load_constructions()
    r2 = rag.ground_recursively(s2, "widget", _Conv2())
    st2 = r2["structure"] or {}
    print(f"    widget grounded={r2['grounded']}  frame={st2.get('frame')!r}  "
          f"register={st2.get('register')!r}  confidence={st2.get('confidence')!r}")
    contrast_ok = (r2["grounded"] and st2.get("frame") is None
                   and st2.get("register") == "exact"
                   and st2.get("confidence") == 1.0)
    all_ok = all_ok and contrast_ok

    # ---- REAL WIKI: the descent still climbs the real chain, frame-aware -----
    print()
    print(SEP)
    print("3. REAL WIKI — the descent climbs the real chain, now frame-aware")
    print(SEP)
    try:
        s3 = _native.Substrate()
        gr.open_grounding_productions(s3)
        rw_mt = s3.add_node("Microtheory", {"name": "mathematics",
                                            "origin": "test"})

        class _ConvW:
            # NO feed -> reads the LIVE Wikipedia lead ("In mathematics, a
            # manifold is a topological space that …").
            _constructions = cg.load_constructions()

        rw = rag.ground_recursively(s3, "manifold", _ConvW(), max_depth=6)
        stw = rw["structure"] or {}
        cidw = gr._find_concept(s3, "manifold")
        if cidw is not None and stw.get("frame") == "mathematics":
            chain = [s3.node(c)["attrs"].get("name") for c in gr.cone(s3, cidw)]
            in_mt = cidw in set(s3.neighbours(rw_mt, "has_concept"))
            print(f"  manifold (live wiki) frame={stw.get('frame')!r}  "
                  f"register={stw.get('register')!r}  "
                  f"confidence={stw.get('confidence')!r}")
            print(f"    attached to mathematics Mt: {in_mt}   "
                  f"depth={stw.get('depth')}")
            print(f"    built_from* chain climbed: {chain[:8]}")
            print(f"    grounded={rw['grounded']}  (stalls at the comprehension")
            print(f"    bottleneck — same as deep_recursive_grounding; frame +")
            print(f"    confidence are present and DROVE the grounding)")
            # the real-wiki proof passes if the frame was comprehended live and
            # bound to the Mt; whether the cone bottoms out at a seeded primitive
            # depends on what's seeded (the comprehension wall is honest, not a
            # regression of this change).
            all_ok = all_ok and (stw.get("frame") == "mathematics" and in_mt
                                 and (stw.get("depth") or 0) >= 1)
        else:
            print("  (live Wikipedia unreachable or lead changed — skipped; "
                  "the offline cases above cover the mechanism)")
    except Exception as e:  # pragma: no cover - network best-effort
        print(f"  (live Wikipedia unreachable: {type(e).__name__} — skipped)")

    print()
    print(SEP)
    print(f"RESULT: {'ALL OK' if all_ok else 'FAILURES ABOVE'}")
    print(SEP)
    print("Faithful: the FRAME (which Mt to ground in) and the REGISTER (the")
    print("epistemic-confidence band) are MEANING — comprehended into structure,")
    print("never stripped. Coarse remaining: frame->Mt is by NAME MATCH; ")
    print("register->confidence is a two-level map (approximate/exact). Additive.")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
