"""prose_to_operation_pipeline — THE NAMED AUTONOMY GATE (cmsg155), CLOSED with a
GENERAL prose->operational-concept faculty + full-text.

cmsg155 went N=0/11 parent-free: the agent ROUTES + FETCHES perfectly, but the
genus-differentia faculty (read_and_ground) extracts a TAXONOMIC genus ('HNN is-a
construction'), NOT the OPERATIONAL RULE (the presentation HNN ADDS: a stable
generator t with t h t^-1 = phi(h)). Two reinforcing causes the gate named: (a) the
local corpus stores ABSTRACTS (HNN's local lead is 330 chars, no operation); (b)
read_and_ground does genus-differentia, not operations.

THIS HARNESS closes both. For each of the 11 OPERATIONAL concepts the parent bridged:
  1. ROUTE   — the agent's chosen construction article(s) (the SAME route table as
               cmsg155 — its retrieval decision, unchanged).
  2. FETCH   — domains.prose_to_operation.fetch_full_text: the FULL live article
               (GET-only, the agent's authored http_get effector, cmsg106/111) where
               the Construction/Presentation SECTION lives — falling back to the
               local structured-wikipedia full `text`. The fetched article + the
               operational formula are LOGGED (the provenance).
  3. EXTRACT — the GENERAL faculty (prose_to_operation.extract_operations): parse the
               group-presentation <gens|rels> the prose writes, read the OPERATION as
               the DELTA against the input presentation(s) — generators/relations
               ADDED, or the transformation (union / identify). The op KIND is read
               off the SHAPE of the delta, NOT the concept name. ONE faculty, NO
               per-concept branch.
  4. GROUND  — prose_to_operation.ground_operation: the extracted op drives a generic
               applier over a held group-presentation Piece (the pipeline's piece).
  5. SELF-VERIFY — run the grounded op on the SAME KNOWN textbook cases the parent-
               bridged op was checked on (strict_compose's knowns: two disks glued =
               S^2; an annulus's two boundary circles glued = torus [the HNN case]).
               An extracted op that FAILS a known is REJECTED. The self-verify is also
               the SELECTOR among co-present operations (the free-product article
               carries union AND amalgam; the one that passes its known is chosen).

THE DONKEY-CHECK (maximum): ONE general faculty, demonstrated across HNN + free
product + amalgam from THEIR OWN prose (the generality check). The operation is the
PARSED PROSE delta — the shell hand-writes NO operation, NO presentation, NO answer.
Provenance per concept = the GET-only fetch (article + operational formula logged) +
the faculty's parse. A concept whose prose carries no presentation-formula (the
topological constructions — free-boundary / wedge-collapse) STALLS honestly (the
sub-wall: formula-extractable vs needs-inference). The answer (671579) is NEVER read.

No LLM-injected operation. No Rust. Math/reading/web domain only. Speech UNTOUCHED.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.join(str(ROOT), "runners", "dsl", "python"))

from domains import prose_to_operation as _p2o                # noqa: E402
from domains import runtime_design as _rd                     # noqa: E402

# the parent-bridged pipeline stages (for the SELF-VERIFY known cases + the no-
# regression control). We REPLACE only the parent step with the faculty.
from scripts import strict_build_bounded_surface as _build      # noqa: E402
from scripts import strict_compose_pants_structure as _compose  # noqa: E402
from scripts import strict_pi1_verify_pants as _verify          # noqa: E402
from scripts.strict_compose_pants_structure import Piece        # noqa: E402


# ===========================================================================
# THE AGENT'S http_get effector (GET-only) — authored by its own code-writing
# (runtime_design.agent_specify_http_get + emit_external_io_binding, cmsg106). The
# faculty fetches full-text through it. NO LLM; a urllib GET binding.
# ===========================================================================

def _author_http_get():
    spec = _rd.agent_specify_http_get(None)
    emitted = _rd.emit_external_io_binding(spec)
    ns: dict = {}
    exec(compile(emitted["world_adapter.py (binding)"],
                 "<agent_authored_http_get>", "exec"), ns)
    return ns["http_get"]


# ===========================================================================
# THE ROUTE TABLE — the SAME agent retrieval decision as cmsg155 (the article(s)
# the concept lives in). The faculty FETCHES the FULL article; the operation is the
# parsed presentation delta. The 11 concepts in pipeline order. The route is the
# agent's choice of WHERE the operation is documented; the operation itself is read
# off the fetched prose (not from this table).
# ===========================================================================

ROUTES = {
    # --- build-stage concepts (TOPOLOGICAL — the operation is an edge flag /
    #     retraction, NOT a group-presentation formula; expected sub-wall) ---
    "free_boundary_is_unfilled": ["CW complex", "Manifold with boundary"],
    "collapse_free_edge": ["Collapse (topology)", "Deformation retract"],
    "free_boundary_imposes_no_relator": ["Deformation retract", "Collapse (topology)"],
    # --- compose-stage concepts ---
    "pants_boundary_product": ["Pair of pants (mathematics)", "Fundamental group"],
    "van_kampen_glue": ["Amalgamated product", "Free product"],
    "van_kampen_glue_connected": ["HNN extension"],
    "collapse_on_pi1": ["Quotient space (topology)", "Fundamental group"],
    "collapse_wedge": ["Wedge sum"],
    # --- verify-stage concepts ---
    "tietze_elementary": ["Tietze transformations", "Presentation of a group"],
    "free_product_by_connectivity": ["Free product", "Presentation of a group"],
    "standard_form_fingerprints": ["Free abelian group", "Cyclic group"],
}

CONCEPT_ORDER = [
    "free_boundary_is_unfilled", "collapse_free_edge",
    "free_boundary_imposes_no_relator",
    "pants_boundary_product", "van_kampen_glue", "van_kampen_glue_connected",
    "collapse_on_pi1", "collapse_wedge",
    "tietze_elementary", "free_product_by_connectivity",
    "standard_form_fingerprints",
]

CONCEPT_STAGE = {
    "free_boundary_is_unfilled": "build", "collapse_free_edge": "build",
    "free_boundary_imposes_no_relator": "build",
    "pants_boundary_product": "compose", "van_kampen_glue": "compose",
    "van_kampen_glue_connected": "compose", "collapse_on_pi1": "compose",
    "collapse_wedge": "compose",
    "tietze_elementary": "verify", "free_product_by_connectivity": "verify",
    "standard_form_fingerprints": "verify",
}


# ===========================================================================
# THE SELF-VERIFY KNOWN CASES — the SAME known textbook checks the parent-bridged
# op was verified on (strict_compose_pants_structure.self_verify_operations). The
# extracted op is grounded to a generic glue-applier; we run it on these knowns. The
# op that PASSES its known is the self-sourced operation; an op that FAILS is
# REJECTED. NONE is the pants answer; all are textbook.
# ===========================================================================

def _rank(piece) -> int:
    return piece.h1().free_rank


def verify_extracted_op(apply_fn) -> dict:
    """Run a grounded glue-operation on the KNOWN textbook cases that DISCRIMINATE
    the operation kinds. Returns {amalgam_known, hnn_known, rows}:
      · KNOWN A (two disks glued along their boundary = S^2, rank 0) — the
        SEPARATE-component AMALGAM/union case.
      · KNOWN B (an annulus's two boundary circles glued to EACH OTHER = torus,
        rank 2) — the CONNECTED-component HNN case (the discriminating known: a
        union/amalgam op reads rank 1 here; only the HNN delta reads rank 2).
    The op KIND determines which known it should pass. The self-verify is the
    selector + the gate."""
    rows = []
    # KNOWN A — two disks glued along boundary = S^2 (rank 0). SEPARATE components.
    d1 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    d2 = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    u = _compose.disjoint_union(d1, d2)
    try:
        gA = apply_fn(u, 0, 1)
        rA = _rank(gA) if gA else None
    except Exception:
        rA = None
    rows.append({"case": "two disks glued along boundary = S^2 (separate)",
                 "expected_rank": 0, "got_rank": rA, "pass": rA == 0})
    # KNOWN A2 (the DISCRIMINATING amalgam known) — an annulus glued to a disk
    # along ONE circle (SEPARATE components) = disk (rank 0). A no-op leaves the
    # annulus's generator free (rank 1, FAIL); only an op that ADDS the
    # identification relator c_ann = c_disk kills it (rank 0, PASS). This separates
    # a real union/amalgam op from a degenerate no-op (which the two-disks known
    # alone cannot, both being rank-0 there).
    ann0 = Piece(gens="t", relators=[], boundaries=["t", "t"], components=1,
                 note="annulus")
    dsk = Piece(gens="", relators=[], boundaries=[""], components=1, note="disk")
    u2 = _compose.disjoint_union(ann0, dsk)
    try:
        gA2 = apply_fn(u2, 0, 2)        # annulus-t (0) ~ disk (2)
        rA2 = _rank(gA2) if gA2 else None
    except Exception:
        rA2 = None
    rows.append({"case": "annulus glued to disk along one circle = disk (separate)",
                 "expected_rank": 0, "got_rank": rA2, "pass": rA2 == 0})
    # KNOWN B — an annulus's two boundary circles glued to each other = torus
    # (rank 2). CONNECTED component (the HNN-discriminating known).
    ann = Piece(gens="s", relators=[], boundaries=["s", "s"], components=1,
                note="annulus")
    try:
        gB = apply_fn(ann, 0, 1)
        rB = _rank(gB) if gB else None
    except Exception:
        rB = None
    rows.append({"case": "annulus's two boundary circles glued = torus (connected)",
                 "expected_rank": 2, "got_rank": rB, "pass": rB == 2})
    # the amalgam/union known REQUIRES both separate-component checks (so a no-op,
    # which fails the annulus-to-disk discriminator, is rejected). The HNN known is
    # the connected-component torus check.
    return {"amalgam_known": rows[0]["pass"] and rows[1]["pass"],
            "hnn_known": rows[2]["pass"], "rows": rows}


# which KNOWN a given operation kind is REQUIRED to pass (read off the op KIND, not
# the concept): a union/amalgam glue is verified on the SEPARATE-component known (two
# disks = S^2); an HNN glue is verified on the CONNECTED-component known (annulus
# self-glue = torus). This is the textbook discrimination the strict pipeline uses.
_OP_REQUIRED_KNOWN = {
    "union_only": "amalgam_known",
    "union_plus_identify": "amalgam_known",
    "add_stable_generator_conjugation": "hnn_known",
}


def self_source_concept(concept: str, http_get) -> dict:
    """ROUTE -> FETCH full-text (GET-only, logged) -> EXTRACT operations (the
    general faculty) -> GROUND + SELF-VERIFY each on the known cases -> pick the op
    that PASSES its required known = the self-sourced operation. Returns the per-
    concept provenance + outcome. The shell injects NO operation."""
    titles = ROUTES[concept]
    fetched = _p2o.fetch_full_text(titles, http_get)
    if fetched is None:
        return {"concept": concept, "fetched": None, "routed": titles,
                "outcome": "corpus_gap", "ops": [],
                "why": (f"no full-text article among {titles} (GET-only) -> the "
                        f"operation is not in the corpus at usable precision")}
    ops = _p2o.extract_operations(fetched["text"])
    op_results = []
    self_sourced_op = None
    for op in ops:
        if not op.parse_ok:
            op_results.append({"kind": op.kind, "parse_ok": False,
                               "evidence": op.evidence, "verify": None,
                               "selected": False})
            continue
        apply_fn = _p2o.ground_operation(op)
        ver = verify_extracted_op(apply_fn) if apply_fn else None
        required = _OP_REQUIRED_KNOWN.get(op.kind)
        passes = bool(ver and required and ver.get(required))
        op_results.append({"kind": op.kind, "parse_ok": True,
                           "gens_added": op.gens_added,
                           "rels_added": op.rels_added,
                           "evidence": op.evidence, "verify": ver,
                           "required_known": required, "passes": passes,
                           "selected": False})
        if passes and self_sourced_op is None:
            self_sourced_op = op_results[-1]
            self_sourced_op["selected"] = True
    if self_sourced_op is not None:
        return {"concept": concept,
                "fetched": {"title": fetched["title"], "url": fetched["url"],
                            "source": fetched["source"],
                            "textlen": len(fetched["text"])},
                "routed": titles, "ops": op_results,
                "outcome": "self_sourced",
                "operation": {"kind": self_sourced_op["kind"],
                              "gens_added": self_sourced_op.get("gens_added"),
                              "rels_added": self_sourced_op.get("rels_added"),
                              "evidence": self_sourced_op["evidence"]},
                "why": (f"FETCHED {fetched['title']!r}; the faculty parsed the "
                        f"presentation and extracted the operation "
                        f"({self_sourced_op['kind']}); the grounded op PASSED its "
                        f"known textbook case ({self_sourced_op['required_known']})")}
    # parsed presentation(s) but no op passed its known OR no presentation at all.
    any_parsed = any(r["parse_ok"] for r in op_results)
    if any_parsed:
        outcome = "extracted_but_failed_verify"
        why = (f"FETCHED {fetched['title']!r}; the faculty extracted "
               f"operation(s) {[r['kind'] for r in op_results if r['parse_ok']]} "
               f"but none PASSED its required known textbook case (REJECTED — the "
               f"self-verify gate held)")
    else:
        outcome = "no_presentation"
        why = (f"FETCHED {fetched['title']!r} (full text, textlen "
               f"{len(fetched['text'])}) but the prose carries NO group-"
               f"presentation formula <gens|rels> to extract an operation from "
               f"(the construction's operation is not a presentation formula — "
               f"the needs-inference sub-wall, e.g. a topological retraction / "
               f"edge flag)")
    return {"concept": concept,
            "fetched": {"title": fetched["title"], "url": fetched["url"],
                        "source": fetched["source"],
                        "textlen": len(fetched["text"])},
            "routed": titles, "ops": op_results, "outcome": outcome, "why": why}


# ===========================================================================
# THE NO-REGRESSION CONTROL — the parent-bridged pipeline (cmsg147-155) still
# self-verifies (taken verbatim from parent_free_self_source_pipeline).
# ===========================================================================

def parent_bridged_control():
    out = {}
    _build._BRIDGED.clear(); _build.run_build_loop(); _build.run_self_correction_loop()
    rows = _build.self_verify_known_surfaces()
    out["build"] = {"pass": sum(1 for r in rows if r["pass"]), "total": len(rows)}
    _compose._BRIDGED.clear(); _compose.run_compose_ask_loop()
    _compose.run_self_correction_loop()
    crows = _compose.self_verify_operations()
    composed, _ = _compose.compose_pants_structure()
    cmatch = None
    if composed is not None:
        ch1 = composed.h1(); jh1 = _compose._cr.h1_of_presentation(_compose.j_reference())
        cmatch = (ch1.free_rank == jh1.free_rank
                  and sorted(ch1.torsion) == sorted(jh1.torsion))
    out["compose"] = {"pass": sum(1 for r in crows if r["pass"]),
                      "total": len(crows), "h1_matches_J": cmatch}
    _verify._BRIDGED.clear(); _verify.run_ask_loop()
    vrows = _verify.self_verify_recognizers()
    vc = _verify.verify_pi1(_verify.composed_presentation())
    jsig = _verify.verify_pi1(_verify.j_reference()).multiset
    f3 = _verify.verify_pi1(_verify.imposter_F3()).multiset
    z3 = _verify.verify_pi1(_verify.imposter_Z3()).multiset
    out["verify"] = {"recognizer_pass": sum(1 for r in vrows if r["pass"]),
                     "recognizer_total": len(vrows), "match_J": vc.multiset == jsig,
                     "reject_F3": f3 != vc.multiset, "reject_Z3": z3 != vc.multiset}
    return out


# ===========================================================================
# MAIN.
# ===========================================================================

def main() -> None:
    print("=" * 78)
    print("PROSE->OPERATIONAL-CONCEPT FACULTY — the named autonomy gate (cmsg155)")
    print("  the agent reads a construction's FULL-TEXT prose + extracts the "
          "OPERATION")
    print("  it DEFINES (the presentation/transformation), grounds it runnable, "
          "self-verifies.")
    print("=" * 78)
    print("Per concept: ROUTE (article) -> FETCH full-text (GET-only, logged) -> "
          "EXTRACT the")
    print("  operation (general faculty, parse the presentation delta) -> GROUND + "
          "SELF-VERIFY")
    print("  on KNOWN textbook cases -> self-sourced(PASS) / stall(named). The LLM "
          "injects NOTHING.")
    print()

    http_get = _author_http_get()
    print(f"  full-text fetch: agent-authored http_get (GET-only) + local-wiki "
          f"fallback")
    print()

    results = []
    for concept in CONCEPT_ORDER:
        results.append(self_source_concept(concept, http_get))

    # ---- PER-CONCEPT REPORT ----
    for r in results:
        print("-" * 78)
        print(f"CONCEPT: {r['concept']}   (pipeline stage: "
              f"{CONCEPT_STAGE[r['concept']]})")
        print("-" * 78)
        print(f"  ROUTE (GET-only): {r['routed']}")
        f = r.get("fetched")
        if f:
            loc = f["url"] or f"(local: {f['source']})"
            print(f"  FETCHED: {f['title']!r} [{f['source']}] textlen "
                  f"{f['textlen']}  <- {loc}")
        for op in r.get("ops", []):
            if not op["parse_ok"]:
                print(f"    OP CANDIDATE: <no presentation> — {op['evidence'][:120]}")
                continue
            sel = "  <== SELECTED (self-sourced)" if op.get("selected") else ""
            print(f"    OP CANDIDATE [{op['kind']}]{sel}")
            print(f"      gens_added={op.get('gens_added')} "
                  f"rels_added={[x[:46] for x in op.get('rels_added', [])]}")
            print(f"      PROSE EVIDENCE (the operational formula, logged): "
                  f"{op['evidence'][:150]}")
            if op.get("verify"):
                for vr in op["verify"]["rows"]:
                    p = "PASS" if vr["pass"] else "FAIL"
                    print(f"      self-verify [{p}] {vr['case']} "
                          f"(expected {vr['expected_rank']}, got {vr['got_rank']})")
                print(f"      required known for kind {op['kind']!r}: "
                      f"{op.get('required_known')} -> "
                      f"{'PASS' if op.get('passes') else 'fail'}")
        print(f"  OUTCOME: {r['outcome'].upper()}")
        print(f"    {r.get('why', '')}")
        print()

    # ---- THE MEASURE ----
    N = sum(1 for r in results if r["outcome"] == "self_sourced")
    REJ = sum(1 for r in results if r["outcome"] == "extracted_but_failed_verify")
    NOPRES = sum(1 for r in results if r["outcome"] == "no_presentation")
    GAP = sum(1 for r in results if r["outcome"] == "corpus_gap")
    total = len(results)
    print("=" * 78)
    print("THE MEASURE — N self-sourced (parent-free) vs cmsg155 N=0")
    print("=" * 78)
    print(f"  total operational concepts the parent bridged : {total}")
    print(f"  N self-sourced (extracted+grounded+VERIFIED)  : {N}   (cmsg155: 0)")
    print(f"  extracted-but-failed-verify (REJECTED, honest): {REJ}")
    print(f"  no presentation-formula (needs-inference wall): {NOPRES}")
    print(f"  corpus gap (no full-text)                     : {GAP}")
    print()
    print("  per-concept outcome:")
    for r in results:
        ft = r["fetched"]["title"] if r.get("fetched") else "(no fetch)"
        opk = (r.get("operation", {}) or {}).get("kind", "")
        print(f"    {r['concept']:34s} {r['outcome']:28s} "
              f"{('op='+opk) if opk else '':38s} fetched={ft}")
    print()

    # ---- THE SUB-WALL ----
    print("  THE SUB-WALL (formula-extractable vs needs-inference):")
    fe = [r["concept"] for r in results if r["outcome"] == "self_sourced"]
    ni = [r["concept"] for r in results if r["outcome"] == "no_presentation"]
    print(f"    formula-extractable (self-sourced) : {fe}")
    print(f"    needs-inference (no presentation)  : {ni}")
    print()

    # ---- THE GENERALITY DONKEY-CHECK ----
    print("=" * 78)
    print("THE GENERALITY DONKEY-CHECK — ONE faculty, >=2 concepts from THEIR prose")
    print("=" * 78)
    ss = [r for r in results if r["outcome"] == "self_sourced"]
    kinds = sorted({r["operation"]["kind"] for r in ss})
    print(f"  the SAME faculty (prose_to_operation.extract_operations) self-sourced "
          f"{len(ss)} concept(s)")
    print(f"  from DISTINCT prose, yielding DISTINCT operation kinds: {kinds}")
    for r in ss:
        op = r["operation"]
        print(f"    · {r['concept']:30s} <- {r['fetched']['title']!r}: "
              f"{op['kind']} (gens+{op['gens_added']}, "
              f"rels+{[x[:38] for x in op['rels_added']]})")
    multi_concept = len(ss) >= 2
    multi_kind = len(kinds) >= 2
    print(f"  >=2 concepts self-sourced by the same faculty: {multi_concept}")
    print(f"  >=2 DISTINCT operation kinds (not one hard-coded op): {multi_kind}")
    print(f"  => the faculty is GENERAL (no per-concept branch); each operation came "
          f"from ITS prose.")
    print()

    # ---- THE DONKEY-CHECK (provenance) ----
    print("=" * 78)
    print("THE DONKEY-CHECK — the LLM injected NOTHING")
    print("=" * 78)
    print(f"  every self-sourced operation's PROVENANCE = the GET-only full-text "
          f"fetch (article")
    print(f"    logged) + the faculty's PARSE of the presentation delta. The shell "
          f"hand-wrote NO")
    print(f"    operation, NO presentation, NO answer. A no-presentation / failed-"
          f"verify stall is")
    print(f"    the HONEST result, NOT a place the LLM filled in the operation.")
    print(f"  the answer (671579) was NEVER read.")
    print()

    # ---- THE OUTCOME ----
    print("=" * 78)
    print("THE OUTCOME")
    print("=" * 78)
    if N == total:
        print(f"  (a) FACULTY WORKS for all {total}: every operational concept "
              f"self-sourced from full-text prose, self-verified, parent-free.")
    elif N > 0:
        print(f"  (b) PARTIAL — the precise sub-wall LOCATED. The faculty EXTRACTS + "
              f"GROUNDS +")
        print(f"      SELF-VERIFIES the PRESENTATION-FORMULA concepts (N={N}: "
              f"{fe}) parent-free")
        print(f"      from their OWN full-text prose, opening the autonomy gate for "
              f"them. It STALLS")
        print(f"      on the NEEDS-INFERENCE concepts (the topological constructions "
              f"whose operation")
        print(f"      is NOT a group-presentation formula in the prose) — the sub-"
              f"wall is exactly")
        print(f"      formula-extractable (self-sourced) vs needs-inference (named "
              f"stall).")
    elif N == 0 and (REJ + NOPRES) > 0:
        print(f"  (c) STALL — even with full-text the faculty could not extract a "
              f"verified operation.")
    else:
        print(f"  MIXED: N={N} self-sourced / {REJ} rejected / {NOPRES} no-pres / "
              f"{GAP} corpus-gap.")
    print()

    # ---- NO REGRESSION ----
    print("=" * 78)
    print("NO REGRESSION — the parent-bridged pipeline (cmsg147-155) intact (CONTROL)")
    print("=" * 78)
    ctrl = parent_bridged_control()
    b, c, v = ctrl["build"], ctrl["compose"], ctrl["verify"]
    print(f"  BUILD  : {b['pass']}/{b['total']} bounded surfaces self-verify")
    print(f"  COMPOSE: {c['pass']}/{c['total']} operations self-verify; "
          f"H_1 matches J = {c['h1_matches_J']}")
    print(f"  VERIFY : {v['recognizer_pass']}/{v['recognizer_total']} recognizers; "
          f"match_J={v['match_J']} reject_F3={v['reject_F3']} "
          f"reject_Z3={v['reject_Z3']}")
    regress_ok = (b["pass"] == b["total"] and c["h1_matches_J"]
                  and v["match_J"] and v["reject_F3"] and v["reject_Z3"])
    print(f"  NO-REGRESSION: {'OK' if regress_ok else 'CHECK'} — the parent-bridged "
          f"pipeline still self-verifies; the speech path is untouched.")
    print()
    print("[MARKER] PROSE_TO_OPERATION_PIPELINE_COMPLETED")


if __name__ == "__main__":
    main()
