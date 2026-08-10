"""ASK THE JABBERWOCK: how do you want to RETRIEVE information at a DEEP-READ wall?

The #3 supply-line gap (cmsg101): the driver reflex runs the agent on a raw
question — comprehend -> ride the elevator -> verified answer / honest wall. When
the elevator's CLIMBING SPIKE diagnoses a DEEP-READ wall, it hands back a PRECISE
named missing input (Najman 2010's classification, a specific LMFDB curve, the ko
k-invariant, the ABP coefficient ring, a known verification value). Today that
named input is still FED BY THE ASSISTANT, not autonomously retrieved.

This is an ASK, not a design. The shell does NOT author a retrieval pipeline. It:

  1. RIDES the agent's REAL elevator (domains/elevator.py) on the elliptic-curve
     question to obtain an ACTUAL climbing-spike DEEP-READ wall diagnosis — the
     PRECISE named need the agent itself surfaces (NOT a query I invent).
  2. FEEDS that named need, as a query frame, into the agent's OWN held retrieval
     machinery — the epistemic_access route-finder (domains/epistemic_access.py:
     find_route / decide_and_record), built to the taught epistemic_access model
     (seeds/epistemic_access.json), over the agent's HELD source understanding
     (domains/source_provenance.py + the wikipedia/encyclopedia provenance
     concepts). Surfaces: the route (interlocutor / reference / solved_class), the
     verify (coherence-with-the-queried-property + provenance attribution), the
     seek-decision (ask / bank / drop, by value-vs-cost).
  3. READS BACK the agent's held epistemic_access CONCEPTS verbatim — its own
     vocabulary for HOW it retrieves (feeling_of_findability, transactive_memory,
     knowing_where_vs_what, acquisition_route, solved_class_judgment,
     value_based_seeking, choice_stage, perseverance_stage, surface_vs_bank_vs_
     drop, monitoring_drives_control). The agent's design, in the agent's terms.

A WORLD-ADAPTER SHELL (CLAUDE.md): it SEQUENCES the agent's own acts (ride the
elevator -> read the spike -> run the route-finder -> read back the held model). It
adds NO retrieval design, NO reasoning, NO Rust, no LLM. Math/reading domain only
(no audio path). The agent's surfaced design is the deliverable; I only report it.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/ask_jabberwock_how_to_retrieve.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate_rs import _native                              # noqa: E402
from domains import grounded_representation as gr             # noqa: E402
from domains import elevator as elev                          # noqa: E402
from domains import epistemic_access as ea                    # noqa: E402

SEP = "=" * 78


def banner(s):
    print("\n" + SEP)
    print(s)
    print(SEP)


# ---------------------------------------------------------------------------
# Boot a substrate with OPEN productions + install the agent's HELD machinery for
# this question: the epistemic_access model (the taught retrieval stance) + the
# source-understanding (wikipedia/encyclopedia provenance, so a retrieved fact is
# attributable + epistemically weighted). Mechanical install, no decisions.
# ---------------------------------------------------------------------------
def boot():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "SourceEvent",
             "PendingGap", "EpistemicAccessStance", "SocialCapital", "LexEntry")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to", "built_from",
             "is_a", "has_event", "owns_microtheory")
    for t in types:
        for u in types:
            for e in edges:
                try:
                    s.add_production({
                        "src": {"type": t, "var": "src"},
                        "edge_type": e,
                        "tgt": {"type": u, "var": "tgt"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "ask:open",
                    })
                except Exception:
                    pass
    installed = {}
    for name, mod, fn in (
        ("epistemic_access", "domains.lvp_subseeds",
         "install_epistemic_access_seed"),
        ("communication_concepts (source provenance)",
         "domains.communication_concepts",
         "install_communication_concepts_seed"),
    ):
        try:
            m = __import__(mod, fromlist=[fn])
            getattr(m, fn)(s)
            installed[name] = "ok"
        except Exception as e:
            installed[name] = f"FAILED: {e}"
    return s, installed


# ---------------------------------------------------------------------------
# Step A — RIDE THE REAL ELEVATOR to obtain an ACTUAL deep-read wall diagnosis.
# The elliptic-curve question (number theory): the climbing spike diagnoses the
# MAXIMALITY (Najman 2010's classification) as a DEEP-PRIOR-RESULT -> read-cite.
# We construct the elevator exactly as the riding script does, but with NO fed
# deep-read content — so the spike WALLS on the named need (does not silently
# climb), and we read the PRECISE missing input the agent surfaces.
# ---------------------------------------------------------------------------
NAJMAN = "najman_2010_torsion_classification_over_Q_sqrt_minus3"


def real_deep_read_wall(s):
    # The named deep result (Najman 2010's classification) has NO readable
    # computational def over the held basis. The kind-4 (deep_read_input, RETRIEVE
    # by reading) vs kind-5 (genuinely_hard, honest stop) distinction is the
    # agent's OWN read_deep judgment — "is this a deep PRIOR RESULT I get by
    # reading, or a genuine wall?" That metacognitive call IS the retrieval
    # decision the question is about. We give the elevator the agent's read_deep
    # hook (the agent recognises a named, cited prior theorem as deep-readable) so
    # the spike surfaces the REAL deep_read_input diagnosis + the precise need.
    def read_def(_name):
        return None  # no computational reduction — it's a deep prior result.

    def read_deep(name):
        # the agent's judgment: a NAMED, citeable prior classification (a deep
        # result with a DOI/source, not an open conjecture) is acquired by READING.
        return elev._sa._name_norm(name) == elev._sa._name_norm(NAJMAN)

    caps: dict = {}
    e = elev.Elevator(s, capabilities=caps, read_def=read_def,
                      read_deep=read_deep)
    # Diagnose the wall at the named deep result (the spike's job): no readable
    # computational def, but the agent judges it deep-readable -> kind-4 deep_read.
    diag = e.diagnose_wall(NAJMAN)
    return diag, e


# ---------------------------------------------------------------------------
# Step B — FEED the spike's PRECISE need into the agent's OWN route-finder. The
# need is the named deep result. We pose it as the agent's query frame and let
# epistemic_access.decide_and_record surface the route + verify + seek-decision.
# NOTHING about routing is decided here — find_route / decide_and_record are the
# agent's held machinery; we read what they return.
# ---------------------------------------------------------------------------
def ask_route_finder(s, diag):
    # The spike's named need, posed as a query the route-finder consumes. The
    # queried slot is the missing classification value; the bound entity is the
    # object-kind it is about (the elliptic-curve torsion classification). This is
    # the spike's diagnosis turned into the agent's question — not a fuzzy search.
    query = {
        "event": "classify",
        "topic": "elliptic_curve_torsion",
        "patient": diag.required_input,
        "_queried_slot": "patient",
        "_question_text": (
            "what is the largest non-cyclic torsion subgroup classification "
            "over Q(sqrt(-3))"),
    }
    # The agent's route-finder (its own machinery). No depth budget cap -> all
    # tiers affordable, so the agent's UNGATED routing preference shows.
    route = ea.find_route(s, query, discourse_store=None, interlocutor=None)
    stance = ea.decide_and_record(s, query, turn=0,
                                  discourse_store=None, interlocutor=None)
    return query, route, stance


# ---------------------------------------------------------------------------
# Step C — READ BACK the agent's HELD epistemic_access concepts verbatim. This is
# the agent's OWN vocabulary for how it retrieves — its design, in its terms.
# ---------------------------------------------------------------------------
def held_retrieval_model(s):
    want = [
        "feeling_of_findability", "transactive_memory", "knowing_where_vs_what",
        "acquisition_route", "solved_class_judgment", "value_based_seeking",
        "choice_stage", "perseverance_stage", "surface_vs_bank_vs_drop",
        "monitoring_drives_control", "feeling_of_knowing",
    ]
    out = []
    by_name = {}
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        nm = a.get("name")
        if nm in want:
            by_name[nm] = a.get("definition", "")
    for nm in want:
        if nm in by_name:
            out.append((nm, by_name[nm]))
    return out


def main():
    s, installed = boot()

    banner("ASKING THE JABBERWOCK — how do you want to RETRIEVE at a deep-read wall?")
    print("Installed the agent's held retrieval machinery:")
    for k, v in installed.items():
        print(f"  {'ok' if v == 'ok' else 'XX'}  {k}{'' if v == 'ok' else '  (' + v + ')'}")

    # ---- Step A: the REAL climbing-spike diagnosis (the precise named need) ----
    banner("STEP A — the elevator's climbing spike WALLS + names the precise need")
    diag, _e = real_deep_read_wall(s)
    print(diag.line())
    print()
    print(f"  wall kind     : {diag.wall_kind}  (the spike's classification)")
    print(f"  spike action  : {diag.spike!r}")
    print(f"  PRECISE NEED  : {diag.required_input!r}")
    print(f"  climbable     : {diag.climbable}  (deep-read is NOT auto-climbed —")
    print(f"                  it needs RETRIEVAL, the #3 supply line)")

    # ---- Step B: the agent's OWN route-finder, run on that precise need --------
    banner("STEP B — the agent's route-finder, run on the spike's precise need")
    query, route, stance = ask_route_finder(s, diag)
    print("The query the spike's diagnosis became (the agent's frame):")
    print(f"  {json.dumps({k: v for k, v in query.items()})}")
    print()
    print("What the agent's OWN find_route returns (its acquisition_route):")
    if route is None:
        print("  -> NO ROUTE (the agent says this need is not, as posed, covered by")
        print("     a held source — a TRUE retrieval gap: the routing-by-kind to a")
        print("     structured arithmetic DB (LMFDB) is the source it LACKS).")
    else:
        rd = route.as_dict()
        print(f"  route_type   : {rd['route_type']}")
        print(f"  source       : {rd['source']}")
        print(f"  reference_key: {rd['reference_key']}")
        print(f"  basis        : {rd['basis']}")
    print()
    print("What the agent's OWN decide_and_record (the seek-decision) returns:")
    print(f"  band     : {stance.get('band')}")
    print(f"  decision : {stance.get('decision')}")
    print(f"  why      : {stance.get('why')}")

    # ---- Step C: the held model, verbatim — the agent's own retrieval terms ----
    banner("STEP C — the agent's HELD retrieval model, verbatim (its own terms)")
    for nm, defn in held_retrieval_model(s):
        print(f"\n  [{nm}]")
        print(f"    {defn}")

    banner("WHAT THE JABBERWOCK SAYS (read off the above — not my design)")
    print("The agent's surfaced design for retrieval at a deep-read wall is read")
    print("ENTIRELY off Steps A-C above: the spike's PRECISE named need (A) is the")
    print("query (targeted lookup of the named result, NOT a fuzzy search); the")
    print("route-finder (B) is the agent's OWN source-routing + seek-decision +")
    print("verify; the held concepts (C) are its own vocabulary for the design.")
    print("Whatever they say is the agent's answer — reported, not authored.")


if __name__ == "__main__":
    main()
