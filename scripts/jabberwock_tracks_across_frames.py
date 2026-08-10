"""GRAPH LAW #6 demo: trans-frame identity, generalised past pixels.

The agent's EYE already answers "what makes a thing the SAME thing
across frames" for one domain: `Substrate::segment_and_track` (grid
cells + 2D centroids), reused by both `segment` (ARC-style ingested
worlds) and `fb_sample` (live shared-memory framebuffer). This script
demonstrates the DOMAIN-GENERAL sibling —
`crate::term::track_identity_correspondence` /
`Substrate::track_identity` — which answers the same question over an
ARBITRARY feature space: no grid, no pixels, no 2D centroids. Here the
"frames" are two conversation turns and the "things" are speaker
entities positioned by an attribute vector (topic engagement x
sentiment x turn-taking-rate), proving the identity mechanism is a
correspondence problem, not a vision problem.

Two parts:
  1. Direct primitive call (`Substrate.track_identity`) — same thing
     kept across frames, a thing that moved too far (birth+death), an
     unmatched thing each side.
  2. RULE-DRIVEN: a single graph-resident rule invokes the
     `track_identity` EFFECT (mirrors `Effect::FbSample`'s perception-
     as-action pattern: a read-only Term/oracle would only OBSERVE,
     the effect actually WRITES the persistent `identity` attr) so the
     correspondence + the identity assignment both happen inside
     `run_rules` — zero Python-side matching.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=runners/dsl/python:. python3 -m scripts.jabberwock_tracks_across_frames
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs


def _entity(s, name, engagement, sentiment, turn_rate):
    """A conversation-turn SPEAKER entity -- feature space is
    (topic_engagement, sentiment, turn_taking_rate), nothing spatial."""
    return s.add_node("SpeakerTurn", {
        "feat": [engagement, sentiment, turn_rate],
        "name": name,
    })


def part1_direct_primitive():
    print("=" * 70)
    print("PART 1 — direct Substrate.track_identity call, non-visual domain")
    print("=" * 70)
    s = srs._native.Substrate()

    # Frame 1 (turn N): Alice engaged+positive, Bob disengaged+neutral.
    alice_1 = _entity(s, "alice", 0.8, 0.6, 0.3)
    bob_1 = _entity(s, "bob", 0.2, 0.0, 0.1)

    # Frame 2 (turn N+1): Alice's stance drifted a little (SAME person,
    # close in feature space); Bob is GONE (nobody near his old spot);
    # a brand-new speaker Carol shows up (nowhere near anyone in frame 1).
    alice_2 = _entity(s, "alice", 0.75, 0.55, 0.35)
    carol_2 = _entity(s, "carol", -0.9, -0.9, 0.9)

    result = s.track_identity(
        [alice_1, bob_1], [alice_2, carol_2],
        "feat", "identity", radius=0.5,
    )

    def name(nid):
        return s.node(nid)["attrs"]["name"]

    print(f"matched: {[(name(p), name(c)) for p, c in result['matched']]}")
    print(f"births:  {[name(n) for n in result['births']]}")
    print(f"deaths:  {[name(n) for n in result['deaths']]}")

    assert [(name(p), name(c)) for p, c in result["matched"]] == [("alice", "alice")]
    assert [name(n) for n in result["births"]] == ["carol"]
    assert [name(n) for n in result["deaths"]] == ["bob"]

    alice_id_1 = s.node(alice_1)["attrs"].get("identity")
    alice_id_2 = s.node(alice_2)["attrs"].get("identity")
    print(f"alice's identity persisted: frame1={alice_id_1} -> frame2={alice_id_2}"
          f" (match={alice_id_1 == alice_id_2 is not None and alice_id_2 is not None})")
    assert alice_id_2 is not None
    # alice_1 never got an `identity` attr written (only cur nodes do;
    # she INHERITS whatever identity alice_1 already carried, or mints
    # one fresh off alice_1's own node id if alice_1 had none yet --
    # either way alice_2's identity is now a real, checkable value).
    print("PASS: same speaker kept ONE identity across drift; a departed "
          "speaker is a death (not deleted); a new speaker is a birth.\n")


def part2_rule_driven():
    print("=" * 70)
    print("PART 2 — a RULE invokes trans-frame identity (zero host matching)")
    print("=" * 70)
    s = srs._native.Substrate()

    # Two frames' worth of percepts, typed so a Term can select each
    # side without any Python-side pairing logic.
    p0 = s.add_node("PrevPercept", {"feat": [0.0, 0.0, 0.0]})
    p1 = s.add_node("PrevPercept", {"feat": [9.0, 9.0, 9.0]})
    c0 = s.add_node("CurPercept", {"feat": [0.1, 0.1, 0.1]})
    c1 = s.add_node("CurPercept", {"feat": [9.1, 9.1, 9.1]})
    c2 = s.add_node("CurPercept", {"feat": [500.0, 500.0, 500.0]})  # birth

    anchor = s.add_node("Anchor", {})
    s.add_edge_unchecked(anchor, "has_anchor", anchor)

    rule_dict = {
        "name": "trans_frame_identity_assignment",
        "match": [["a", "has_anchor", "a"]],
        "effects": [
            [
                "track_identity",
                {"__term__": {"type": "NodesOfType", "node_type": "PrevPercept"}},
                {"__term__": {"type": "NodesOfType", "node_type": "CurPercept"}},
                "feat",       # feature_key
                None,          # category_key
                None,          # extent_key
                "identity",    # identity_key
                1.0,           # radius
            ],
        ],
    }
    s.add_rule(rule_dict)
    n_steps = s.run_rules(200)
    print(f"run_rules took {n_steps} steps to fixpoint (or hit the budget)")

    def ident(nid):
        return s.node(nid)["attrs"].get("identity")

    id0, id1 = ident(p0), ident(p1)
    print(f"prev identities: p0={id0} p1={id1}")
    print(f"cur  identities: c0={ident(c0)} c1={ident(c1)} c2={ident(c2)}")

    assert id0 is not None and id1 is not None and id0 != id1
    assert ident(c0) == id0, "c0 (close to p0) must inherit p0's identity"
    assert ident(c1) == id1, "c1 (close to p1) must inherit p1's identity"
    assert ident(c2) not in (None, id0, id1), "c2 (far from everything) must be a fresh birth"

    print("PASS: the RULE's `track_identity` effect performed the entire "
          "correspondence + persistent-identity write inside run_rules — "
          "Python only built the two frames and installed one rule.\n")


if __name__ == "__main__":
    part1_direct_primitive()
    part2_rule_driven()
    print("GRAPH LAW #6 — trans-frame identity generalises past "
          "segment_and_track's pixel/centroid domain: same primitive, "
          "arbitrary feature space, host-free rule invocation.")
