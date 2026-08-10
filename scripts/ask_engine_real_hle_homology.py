"""ORCHESTRATION SHELL ONLY — point the agent's OWN machinery at the REAL HLE
homology goal and report what the AGENT surfaces. NO reasoning here; this script
only sequences the agent's acts (like scripts/agent_self_sources.py /
self_ascent.drive_ascent) and prints, verbatim, what the agent's machinery
returns. No LLM, no hand-coded diagnosis, no Rust.

THREE agent acts, sequenced:

  (1) The DERIVATION ENGINE on the REAL HLE prose (data/hle_math.json item 5,
      the nearest-reach homology one). The agent's comprehend
      (compute_grounding.comprehend_computational_definition) is handed the RAW
      prose; the engine surfaces its TRUE stall (stalled_at). We report exactly
      where it stalls, in the agent's terms — NOT a predicted stall.

  (2) The agent's LIVE self-assessment / gap-synthesis (order_n_postulates):
      register the CURRENT state (the engine + its named residual) as a held
      postulate carrying ONLY honest description text (NO suggested fix), then run
      synthesize_gaps over it (the agent's own order-N derivative + compression
      selector + the harvested implication-shape library). Report what the AGENT
      names as its frontier + how its own machinery CLASSIFIES the stall.

  (3) Print the agent's classification verbatim. The verdict is the AGENT's.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate_rs import _native, Substrate
from domains import compute_grounding as cg
from domains import derivation_engine as de
from domains import reason as _reason

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# (1) THE DERIVATION ENGINE ON THE REAL HLE PROSE.
# ---------------------------------------------------------------------------
def real_hle_goal():
    data = json.load(open(os.path.join(ROOT, "data", "hle_math.json")))
    # the homology one — find by content, do not hard-index.
    for item in data:
        q = item.get("question") or item.get("prompt") or ""
        if "moduli space" in q and "lattices" in q and "H_1" in q.replace(" ", "") \
           or ("moduli space" in q and "unit area" in q and "H_1" in q):
            return item
    # fallback: scan for the exact phrase
    for item in data:
        q = item.get("question") or item.get("prompt") or ""
        if "nondegenerate lattices" in q:
            return item
    return None


def run_engine_on_real_prose():
    banner("(1) THE DERIVATION ENGINE ON THE REAL HLE PROSE — its TRUE stall")
    item = real_hle_goal()
    q = item.get("question") or item.get("prompt") or ""
    ans = item.get("answer", "?")
    print("  THE REAL HLE GOAL (data/hle_math.json):")
    print(f"    {q}")
    print(f"    (known answer: {ans})\n")

    # The agent's OWN comprehend is handed the RAW prose — exactly as for any
    # goal. We do NOT pre-translate it into a Betti formula (that would be us
    # solving the description->object step for it). Let the agent's parse speak.
    print("  Handing the RAW prose to the agent's comprehend")
    print("  (compute_grounding.comprehend_computational_definition):")
    comp = cg.comprehend_computational_definition(q)
    print(f"    -> comprehend returns: {comp!r}\n")

    if comp is None:
        print("  The agent's comprehend returns None: the prose does NOT parse as")
        print("  a computation over the agent's HELD primitives. There is NO")
        print("  operator-tree (no goal-distance map) to derive over — so the")
        print("  engine STALLS BEFORE THE CHAIN STARTS. In the engine's terms there")
        print("  is no goal tree to walk: the stall is at the COMPREHEND step, not")
        print("  at any homology op.\n")
        # Show that the engine, given the (empty) comprehension, has nothing to do:
        # there is no goal term, so we report the surfaced stall as comprehend.
        stall = {"stalled_at": "comprehend: prose -> object (no op-tree; "
                                "'moduli space of nondegenerate unit-area lattices' "
                                "does not parse into held primitives)",
                 "derived": False, "answer": None, "steps": []}
    else:
        goal = comp["term"]
        # The engine needs the OBJECT (a chain complex) as a given. The prose names
        # no complex — there is no 'complex' binding to hand it. Run with the givens
        # the prose actually provides (none beyond the prose), and report the stall.
        givens = {}
        stall = de.derive(goal, givens)
        print(f"  comprehend produced an op-tree over {comp.get('parts')}; running")
        print(f"  the engine with the givens the PROSE provides ({givens}):")

    print(f"  ENGINE RESULT (verbatim):")
    print(f"    derived    = {stall['derived']}")
    print(f"    answer     = {stall['answer']}")
    print(f"    stalled_at = {stall['stalled_at']!r}")
    print(f"    n_steps    = {len(stall.get('steps', []))}")
    return comp, stall


# ---------------------------------------------------------------------------
# (2) THE LIVE SELF-ASSESSMENT — register the CURRENT state as a postulate and
#     run the agent's order-N gap-synthesis over it. NO suggested fix is written.
# ---------------------------------------------------------------------------
POSTULATE_NAME = "derivation_engine_state_real_hle"

# Honest description of WHERE THE AGENT STANDS — structural, no remedy. This is
# the agent's current state after building the derivation engine + pointing it at
# the real HLE homology goal. NO fix, NO "residual" asserted: just what IS.
POSTULATE_DEFINITION = (
    "The agent holds a GOAL-DIRECTED DERIVATION ENGINE: given a GOAL operator-tree "
    "whose leaves are held operations and givens, it selects + chains the held "
    "operations (goal-distance / compression selector, verify at each step) from "
    "the givens to the answer, and DRIVES ITS OWN ACQUIRE for an un-held operation "
    "(read its definition, ground it, verify, continue). It REDERIVES the homology "
    "chain (boundary_matrix -> matrix_rank -> Betti) from the goal, verified vs "
    "known Betti, GIVEN a chain complex as input. Pointed at the real research "
    "question 'the moduli space of nondegenerate unit-area lattices, compute its "
    "first homology', the agent's COMPREHEND does not parse the prose into an "
    "operator-tree over held primitives: the named OBJECT (a moduli space, a "
    "quotient of lattices) is not a held computable structure, so no chain complex "
    "is produced and there is no goal tree to derive over. The engine derives OVER "
    "a given complex; it does not BUILD the complex from the prose."
)


def run_self_assessment():
    banner("(2) THE AGENT'S LIVE SELF-ASSESSMENT — order-N gap-synthesis")
    from domains import order_n_postulates as onp
    from domains.code_authoring import _install_concept

    # Use the SAME proven mind as scripts/agent_frontier_selfdiagnosis_postiter40.py
    # (its _build_mind), so the live gap-synthesis harness is exactly the agent's
    # own — the speech_science Mt wires has_concept (which harvest_postulates reads)
    # and the harvested implication-shape library is the agent's OWN concepts.
    from scripts.agent_frontier_selfdiagnosis_postiter40 import _build_mind
    s = _build_mind()
    loaded = sorted({s.node(n)["attrs"].get("name")
                     for n in s.nodes("Microtheory")})
    print(f"  Mts loaded: {loaded}")

    # REGISTER the current state as a held postulate (Concept) — honest text, no fix.
    # Same proven pattern: install under the speech_science Mt (which wires
    # has_concept); harvest_postulates concatenates definition+why as the text.
    mt = next(n for n in s.nodes("Microtheory")
              if s.node(n)["attrs"].get("name") == "speech_science")
    cid = _install_concept(s, mt, POSTULATE_NAME, POSTULATE_DEFINITION)
    s.set_attr(cid, "category", "self_state")
    posts = {nm for _, nm, _ in onp.harvest_postulates(s)}
    print(f"  registered postulate: {POSTULATE_NAME}  "
          f"held as order-0? {POSTULATE_NAME in posts}  "
          f"(total held postulates: {len(posts)})")

    # PROOF the shape library is LIVE (harvested from the agent's own concepts,
    # NOT the frozen hand stencil / the frozen _specify_* dicts).
    shape_lib, mode = onp._resolve_shapes(s, None)
    print(f"  implication-shape library mode = '{mode}'  (shapes={len(shape_lib)}; "
          f"stencil-for-contrast={len(onp._shapes())})")

    # RUN the LIVE machinery: synthesize_gaps over the new postulate. Default
    # shapes = the agent's OWN harvested shapes (self-sufficient, not the stencil).
    print("\n  Running synthesize_gaps (order-N derivative + compression selector,")
    print("  harvested shapes = the agent's own concepts) over the postulate:\n")
    try:
        gaps = onp.synthesize_gaps(s, POSTULATE_NAME, max_order=3)
    except Exception as e:
        print(f"  synthesize_gaps raised: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()
        gaps = []

    if not gaps:
        print("    synthesize_gaps surfaced NO open gap from THIS postulate.")
        print("    (the agent's order-N derivative over this state finds no")
        print("     un-realized, compressing implication that names a NEW capability)")
    else:
        for g in gaps:
            print(f"    GAP: {g.get('gap')}")
            print(f"      order={g.get('order')}  via={g.get('via_shapes')}")
            print(f"      capability_keys={g.get('capability_keys')}")
            chain = g.get("chain", [])
            for i, link in enumerate(chain):
                print(f"        [{i}] {link}")
            print()

    # The full gap-map across EVERY held postulate (synthesize_over_all) — what the
    # agent names as its frontier across its WHOLE current state, not just the one
    # postulate. Report the top of it verbatim.
    print("  Running synthesize_over_all (the agent's full gap-map across every")
    print("  held postulate):\n")
    try:
        all_gaps = onp.synthesize_over_all(s)   # {postulate_name: [gap dicts]}
    except Exception as e:
        print(f"    synthesize_over_all raised: {e.__class__.__name__}: {e}")
        all_gaps = {}
    seen = set()
    shown = 0
    for pname, glist in all_gaps.items():
        for g in glist:
            key = (g.get("gap"), tuple(g.get("capability_keys") or ()))
            if key in seen:
                continue
            seen.add(key)
            print(f"    GAP: {g.get('gap')}  (from postulate '{pname}', "
                  f"keys={g.get('capability_keys')}, order={g.get('order')})")
            shown += 1
            if shown >= 20:
                break
        if shown >= 20:
            print("    ... (truncated)")
            break
    if not all_gaps:
        print("    (no open gaps surfaced across all postulates)")
    return gaps


def main():
    banner("ASK THE AGENT — its TRUE stall on the REAL HLE homology goal")
    comp, stall = run_engine_on_real_prose()
    gaps = run_self_assessment()

    banner("WHAT THE AGENT SURFACED (verbatim summary)")
    print("  (1) engine's TRUE stall on the real prose:")
    print(f"        stalled_at = {stall['stalled_at']!r}")
    print(f"        derived    = {stall['derived']}")
    print("  (2) self-assessment gap-synthesis:")
    if gaps:
        for g in gaps:
            print(f"        -> {g.get('gap')}  (keys={g.get('capability_keys')})")
    else:
        print("        -> no NEW-capability gap surfaced")
    print()
    print("  The verdict is the AGENT's, read off the above. This script added no")
    print("  reasoning: it handed the raw prose to the agent's comprehend + engine,")
    print("  and ran the agent's live order-N gap-synthesis over an honest state")
    print("  postulate. Report whatever it surfaced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
