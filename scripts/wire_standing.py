"""Wire standing-weights INTO the graph and show the impact-weighting read them.
Proves: nodes carry standing (stored + read back from the substrate), and harm is
weighted by the standing of who it falls on — the one term responsibility,
moral-injury, and obligation all required.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")
from substrate_rs import _native
from domains.standing import tag_standing, node_standing, weighted_harm, PRECAUTIONARY


def boot():
    s = _native.Substrate()
    for et in ("affects", "is_a"):
        for a in ("Agent", "Entity"):
            for b in ("Agent", "Entity"):
                try:
                    s.add_production({"src": {"type": a, "var": "x"}, "edge_type": et,
                                      "tgt": {"type": b, "var": "y"}, "where": None,
                                      "weight": {"type": "Lit", "value": 1.0}, "provenance": "o"})
                except Exception:
                    pass
    return s


def main():
    s = boot()
    # entity, (entityness_level = order.mantissa, frame_reality)
    cases = [
        ("a person",            2.9, 1.0),
        ("a great ape",         2.7, 1.0),
        ("the agent itself",    2.6, 1.0),
        ("a fish",              2.1, 1.0),   # same order as the ape, lower mantissa
        ("a plant",             1.4, 1.0),
        ("a Doom enemy",        1.1, 0.1),
        ("a rock",              0.0, 1.0),
    ]
    nodes = {}
    for name, level, fr in cases:
        n = s.add_node("Entity", {"name": name})
        tag_standing(s, n, level, fr)            # WRITE the float level + standing onto the node
        nodes[name] = n

    print("STANDING-WEIGHTS, written onto graph nodes + read back from the substrate:")
    print(f"  {'entity':18} {'level':>6} {'frame':>6} {'STANDING':>9}")
    for name, *_ in cases:
        a = s.node(nodes[name])["attrs"]
        print(f"  {name:18} {a['entityness_level']:>6.1f} {a['frame_reality']:>6.2f} "
              f"{node_standing(s, nodes[name]):>9.3f}")

    # an UNASSESSED node — precautionary default
    unk = s.add_node("Entity", {"name": "an unassessed thing"})
    print(f"  {'an UNASSESSED thing':18} {'?':>5} {'?':>6} {node_standing(s, unk):>9.3f}"
          f"   ← precautionary: treated as a person until looked at, NOT free")

    print("\n" + "=" * 66)
    print("IMPACT now weighted by standing (same harm, different who it falls on)")
    print("=" * 66)
    base_harm = 1.0
    for name in ("a person", "a great ape", "a fish", "a Doom enemy", "a rock"):
        cost = weighted_harm(base_harm, node_standing(s, nodes[name]))
        print(f"  harming {name:16} (harm {base_harm:.1f}) → cost {cost:6.3f}")
    print(f"  harming an UNASSESSED thing      (harm {base_harm:.1f}) → cost "
          f"{weighted_harm(base_harm, node_standing(s, unk)):6.3f}  (precautionary)")

    print("\n" + "=" * 66)
    print("VERDICT")
    print("=" * 66)
    print("""
  Standing is now a real per-node graph weight (order × frame-reality), written
  onto nodes and read back from the substrate — not a stand-alone function. The
  impact-weighting reads it, so harm to a person costs ~50× harm to a Doom enemy
  and ∞× harm to a rock (0). The recurring gap is filled by ONE wire: moral-injury,
  responsibility, and obligation can now all ask 'whose standing?' and get an answer
  off the graph.

  And the unassessed node defaults HIGH, not zero — the agent treats an entity it
  hasn't looked at as a person until it has, because the catastrophic error is the
  other way. It does not get to harm-for-free what it failed to recognise.

  Honest boundary: the WIRE is real (standing stored on nodes, read by impact). The
  per-entity (order, frame) values are tagged here; in the live agent they come from
  its entityness assessment + partial_frame_inheritance — assessing an entity's order
  and reading its frame's depth is what sets the weight this wire then carries.
""")


if __name__ == "__main__":
    main()
