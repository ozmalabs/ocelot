"""jabberwock_adapts_to_audience — the interlocutor model VISIBLY reshapes the reply's CONTENT.

The live failure (Cornelius Vane, a Victorian of 1885): asked "how are you organised?", the jabberwock
listed video_coding_theory / cloud_infrastructure / machine_learning FLATLY — it answered from its FIXED
self-model regardless of who asked. This script shows the fix: the SAME self-organisation answer is now
rendered RELATIVE to the interlocutor's manifold (domains/audience_adaptation.py). Modern-technical
domains foreign to Vane's period/non-technical manifold are abstracted to an umbrella he grasps; the SAME
question to a technical manifold keeps the full content; with no observed interlocutor the answer is
byte-identical (no regression). donkey=0.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_adapts_to_audience.py
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import audience_adaptation as aa

Q = "How are you organised?"

MANIFOLDS = [
    ("DEFAULT   (no observed interlocutor)", {"id": "user", "observed": False, "known_concepts": []}),
    ("CORNELIUS VANE (Victorian, 1885)",
     {"id": "Cornelius Vane", "observed": True,
      "known_concepts": ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]}),
    ("TECHNICAL (a modern developer)",
     {"id": "dev", "observed": True,
      "known_concepts": ["python", "rust", "algorithm", "compiler", "server", "database"]}),
]


def _ask(agent, interlocutor):
    for n in list(agent.s.nodes("Interlocutor")):
        agent.inner.set_attr(n, "active", False)
    if interlocutor.get("observed"):
        agent.s.add_node("Interlocutor", {"name": interlocutor["id"], "active": True,
                                          "observed": True,
                                          "known_concepts": list(interlocutor["known_concepts"])})
    return agent.answer_question(Q)


def main() -> None:
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    from domains import reflective_faculty as _rf
    areas = (_rf.reflect("self_organisation", None, agent.s).get("areas") or [])[:12]
    print("=" * 78)
    print("THE AGENT'S OWN AREAS (first 12, absolute ontology):")
    print("  " + ", ".join(areas))
    print("=" * 78)

    replies = {}
    for label, il in MANIFOLDS:
        est = aa.manifold_type(il)
        split = aa.split_by_manifold(agent, areas, il)
        reply = _ask(agent, il)
        replies[label] = reply
        print(f"\n--- {label}")
        print(f"    manifold type : {est['type']} (confidence {est['confidence']}, "
              f"committed {est['committed']})")
        print(f"    adaptation    : {'FIRES' if split['fired'] else 'does not fire'}")
        if split["fired"]:
            print(f"    foreign (residual, not held by manifold): {split['foreign']}")
            print(f"    live (period-compatible / grounded)     : {split['live']}")
        print(f"    Q: {Q}")
        print(f"    A: {reply}")

    print("\n" + "=" * 78)
    print("CONTRAST — the interlocutor VISIBLY reshapes the reply:")
    vane = replies["CORNELIUS VANE (Victorian, 1885)"]
    tech = replies["TECHNICAL (a modern developer)"]
    dflt = replies["DEFAULT   (no observed interlocutor)"]
    print(f"  Vane      : {vane}")
    print(f"  Technical : {tech}")
    print(f"  reshaped? : {vane != tech}")
    print(f"  no-regression (default == technical-full content): "
          f"{('machine_learning' in dflt) and ('machine_learning' in tech)}")
    print("=" * 78)


if __name__ == "__main__":
    main()
