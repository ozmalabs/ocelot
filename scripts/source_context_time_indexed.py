"""PROVE a source's CONTEXT is DERIVED from first principles + TIME-INDEXED —
NOT a flat hand-fed reliability tag.

A source's context is the GROUNDING CONE of the source ENTITY, time-sliced to
the artifact's date. The source (twitter_x) is a TEMPORAL ENTITY: its name,
owner, verification/moderation regime and public trust CHANGE across a dated
TIMELINE of grounded EVENTS (founded 2006, Musk acquisition 2022-10, verification
-for-pay 2023-04, moderation pullback 2023-06, rename->X 2023-07, Grok
'MechaHitler' 2025-07). The agent's INPUTS are those grounded facts; the CONTEXT
is DERIVED by composing the cone over the events with when <= the artifact's date:

    context_for(source, when) -> {name@when, owner@when, IMPLIED concept web
       (follow the in-cone events' grounding edges — musk -> finance, politics;
        an incident -> public_trust), trust COMPOSED over the trust-relevant
        in-cone events (declining as they enter), reliability, provenance}

PROVEN here (no LLM, no Rust, no per-source Python decision — graph data +
composition over the time-sliced cone):
  1. SAME SURFACE, DIFFERENT TIME -> DIFFERENT CONTEXT: a tweet@2015 vs an X
     post@2024 derive divergent cones from the SAME entity (name, owner, implied
     web, trust all differ) purely by the WHEN slicing the SAME timeline.
  2. IMPLIED FROM FIRST PRINCIPLES: the @2024 context PULLS IN musk/finance/
     politics/rename/trust by FOLLOWING grounding edges from the in-cone events,
     not from a hand-set field; the 2025 MechaHitler grounding is ABSENT in 2024
     and PRESENT only for a present-day post.
  3. TRUST COMPOSED, not constant: the trust band is composed over the trust-
     relevant events in the cone (none in 2015 -> baseline; two by 2024 ->
     contested), and the lowering events are named.
  4. NO REGRESSION: Wikipedia-as-encyclopedia derives a STABLE (temporal=False)
     context — the flat held provenance + consensus epistemic weight, intact.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.communication_concepts import install_communication_concepts_seed
from domains import source_provenance as sp


def _ctx(s, source, when, where=None):
    return sp.context_for(s, source, when, where=where)


def main() -> int:
    s = _native.Substrate()
    install_communication_concepts_seed(s)

    ok = True
    n_events = len([e for e in s.nodes("SourceEvent")])
    print("=" * 72)
    print("THE TEMPORALLY-GROUNDED SOURCE ENTITY  (the INPUTS — grounded facts)")
    print("=" * 72)
    print(f"  twitter_x materialized {n_events} dated SourceEvent nodes,")
    print("  each grounded (built_from) in its own concepts:")
    for e in sorted(s.nodes("SourceEvent"),
                    key=lambda e: s.node(e)["attrs"].get("when", "")):
        a = s.node(e)["attrs"]
        grounds = sorted(s.node(g)["attrs"].get("name")
                         for g in s.neighbours(e, "built_from"))
        print(f"    {a.get('when'):<11} {a.get('event_id'):<18} "
              f"grounds_in -> {grounds}")
    ok = ok and n_events == 6

    # ---- 1 + 2 + 3 : the two divergent cones from the SAME surface ----------
    c2015 = _ctx(s, "tweet", "2015-06-01")
    c2024 = _ctx(s, "X post", "2024-03-01")
    cnow = _ctx(s, "X post", "2025-09-01")

    print("\n" + "=" * 72)
    print("SAME SURFACE, DIFFERENT TIME  ->  DIFFERENT DERIVED CONTEXT")
    print("=" * 72)
    for tag, c in (("tweet @2015", c2015), ("X post @2024", c2024),
                   ("X post @2025 (post-MechaHitler)", cnow)):
        print(f"\n  {tag}:")
        print(f"    name={c['name']!r}  owner={c['owner']!r}  "
              f"trust={c['trust']['status']!r} (weight {c['trust']['weight']})")
        print(f"    in-cone events: {[e['id'] for e in c['in_cone_events']]}")
        print(f"    future (NOT in cone): {[e['id'] for e in c['future_events']]}")
        print(f"    implied web: {c['implied']}")

    # divergence assertions ---------------------------------------------------
    print("\n" + "-" * 72)
    div_name = c2015["name"] == "Twitter" and c2024["name"] == "X"
    div_owner = (c2015["owner"] == "jack_dorsey"
                 and c2024["owner"] == "elon_musk")
    print(f"  [{'OK ' if div_name else 'XX '}] name: Twitter@2015 vs X@2024")
    print(f"  [{'OK ' if div_owner else 'XX '}] owner: dorsey-era@2015 vs musk@2024")
    ok = ok and div_name and div_owner

    # IMPLIED from first principles: the @2024 web PULLS IN the musk web by
    # following grounding edges; @2015 does NOT contain them.
    pull = {"elon_musk", "finance", "politics", "acquisition",
            "public_trust", "verification_badge", "content_moderation"}
    impl15 = set(c2015["implied"])
    impl24 = set(c2024["implied"])
    pulled = pull <= impl24
    absent15 = not (pull & impl15)
    print(f"  [{'OK ' if pulled else 'XX '}] @2024 IMPLIES the web "
          f"(musk/finance/politics/trust) by following grounding edges")
    print(f"  [{'OK ' if absent15 else 'XX '}] @2015 cone does NOT contain that web")
    ok = ok and pulled and absent15

    # MechaHitler: absent in 2024, present only in a present-day post.
    mh_absent_24 = "ai_output_incident" not in impl24
    mh_present_now = "ai_output_incident" in set(cnow["implied"])
    print(f"  [{'OK ' if mh_absent_24 else 'XX '}] MechaHitler (2025) ABSENT "
          f"from the @2024 cone (a future event)")
    print(f"  [{'OK ' if mh_present_now else 'XX '}] MechaHitler PRESENT only for "
          f"a present-day (2025+) post")
    ok = ok and mh_absent_24 and mh_present_now

    # TRUST composed, not constant.
    print("\n" + "-" * 72)
    t15, t24, tnow = c2015["trust"], c2024["trust"], cnow["trust"]
    trust_rises_then_falls = (t15["status"] != "contested"
                              and t24["status"] == "contested"
                              and t24["weight"] < t15["weight"])
    composed = (t15["lowering_events"] == []
                and set(t24["lowering_events"])
                == {"verification_change", "moderation_change"}
                and "grok_mechahitler" in tnow["lowering_events"])
    print(f"  trust@2015 = {t15['status']} (no trust-events in cone)")
    print(f"  trust@2024 = {t24['status']} composed over "
          f"{t24['lowering_events']}")
    print(f"  trust@2025 = {tnow['status']} composed over "
          f"{tnow['lowering_events']}  (MechaHitler now in cone)")
    print(f"  [{'OK ' if trust_rises_then_falls else 'XX '}] trust DERIVED + "
          f"declines as trust-events enter (NOT a hand-set constant)")
    print(f"  [{'OK ' if composed else 'XX '}] the lowering events are exactly "
          f"the trust-relevant in-cone events")
    ok = ok and trust_rises_then_falls and composed

    # epistemic_status_for_source is now TIME-INDEXED (the wiring point).
    e15 = sp.epistemic_status_for_source(s, "tweet", "2015-06-01")
    e24 = sp.epistemic_status_for_source(s, "X post", "2024-03-01")
    wired = (e15["status"] != "contested" and e24["status"] == "contested")
    print(f"  [{'OK ' if wired else 'XX '}] epistemic_status_for_source is "
          f"TIME-SLICED: {e15['status']}@2015 vs {e24['status']}@2024")
    ok = ok and wired

    # ---- 4 : NO REGRESSION — Wikipedia stays the flat static-genre case -----
    print("\n" + "=" * 72)
    print("NO REGRESSION — Wikipedia-as-encyclopedia (no dramatic timeline)")
    print("=" * 72)
    cw = _ctx(s, "wikipedia", "2024-01-01", where="Manifold")
    stable = (cw is not None and cw["temporal"] is False
              and cw["trust"]["status"] == "consensus")
    print(f"  temporal={cw['temporal']}  name={cw['name']!r}  "
          f"trust={cw['trust']['status']!r} (weight {cw['trust']['weight']})")
    print(f"  provenance who={cw['provenance'].get('who')!r} "
          f"how={cw['provenance'].get('how')!r} where={cw['provenance'].get('where')!r}")
    print(f"  [{'OK ' if stable else 'XX '}] Wikipedia derives a STABLE "
          f"(time-invariant) context — flat held provenance + consensus weight")
    # the flat epistemic-status path still works (no when).
    ew = sp.epistemic_status_for_source(s, "wikipedia")
    flat_ok = ew is not None and ew["status"] == "consensus"
    print(f"  [{'OK ' if flat_ok else 'XX '}] flat epistemic_status path intact "
          f"(consensus, confidence {ew['confidence']})")
    ok = ok and stable and flat_ok

    print("\n" + "=" * 72)
    print("RESULT:", "ALL OK" if ok else "FAILURE")
    print("=" * 72)
    print("""
The LEARNING: a source's context is DERIVED — composed over a grounded,
time-sliced ENTITY — not a flat hand-fed tag. The agent IMPLIES the web
(musk -> finance, politics; rename; trust-loss; MechaHitler) by FOLLOWING
grounding edges from the in-cone events, and the SAME surface form (a 'tweet'
/ an 'X post') derives DIFFERENT contexts at 2015 vs 2024 vs 2025 purely by the
WHEN slicing the SAME timeline. The trust is COMPOSED over the trust-relevant
in-cone events, not a constant.

HONEST / coarse: the timeline is SEEDED as grounded facts (not yet read live
from the source's own article); the trust composition is a coarse monotone over
trust-events; ONE entity (Twitter/X) is modeled deeply — Wikipedia stays the
static-genre case (temporal=False). No LLM, no Rust, no per-source Python
decision.""")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
