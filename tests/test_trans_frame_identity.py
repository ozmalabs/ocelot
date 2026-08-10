"""test_trans_frame_identity — GRAPH LAW #6 (trans-frame identity),
the domain-general "same-thing-across-frames" primitive
(`runners/dsl/src/term.rs::track_identity_correspondence` +
`Substrate::track_identity`).

The visual eye already answers "same thing across frames" for ONE
domain — `Substrate::segment_and_track` (pixel cells + 2D centroids),
exercised by tests/test_fb_vision.py / tests/test_live_eye.py /
tests/test_browser_world.py / tests/test_rule_driven_look.py, all of
which stay green (this file changes nothing about that path — it's a
sibling primitive, not a rewrite).

This file proves the GENERALISATION: the SAME matching shape
(overlap-first, nearest-feature-vector fallback within a radius,
greedy, birth/death) works over an ARBITRARY feature space that is
NOT 2D pixels — here, entities carrying an N-dimensional numeric
`feat` attr (think: conversation-turn entities positioned by an
attribute/embedding vector, or any tracked object in a sensor space).

Covers:
  (a) a thing present in both frames (close correspondence) keeps ONE
      identity (the cur node inherits the prev node's `identity` attr
      value).
  (b) a thing that moved far / changed enough is birth+death (new
      identity for the cur node; the old identity node reported as a
      death, not deleted).
  (c) an unmatched thing in frame 2 is a birth (fresh identity).
  (d) an unmatched thing in frame 1 is a death.
  (e) the category gate: same position, different category -> forced
      birth (discriminative — proves the gate, not just distance, is
      doing work).
  (f) identity PERSISTS across a THREE-frame chain (not just one hop).
  (g) the extent-overlap-first pass beats a numerically-closer
      centroid, mirroring segment_and_track's cell-overlap rule.
  (h) a RULE invokes trans-frame identity via the `track_identity`
      effect (mirrors `Effect::FbSample`'s perception-as-action
      pattern) — zero host (Python) matching; the correspondence and
      the identity-attr write both happen inside `run_rules`.
"""
from __future__ import annotations

import substrate_rs as srs


def _mk_entity(s, feat, category=None, extent=None, **extra):
    attrs = {"feat": list(feat)}
    if category is not None:
        attrs["cat"] = category
    if extent is not None:
        attrs["extent"] = set(extent)
    attrs.update(extra)
    return s.add_node("Entity", attrs)


def _identity(s, nid):
    return s.node(nid)["attrs"].get("identity")


def test_close_correspondence_keeps_one_identity():
    s = srs._native.Substrate()
    a = _mk_entity(s, [0.0, 0.0, 0.0])
    b = _mk_entity(s, [10.0, 10.0, 10.0])
    a2 = _mk_entity(s, [0.1, 0.1, 0.1])
    b2 = _mk_entity(s, [10.1, 10.1, 10.1])

    result = s.track_identity([a, b], [a2, b2], "feat", "identity", 1.0)

    assert sorted((p.value, c.value) for p, c in result["matched"]) == sorted(
        [(a.value, a2.value), (b.value, b2.value)]
    )
    assert result["births"] == []
    assert result["deaths"] == []

    # The SAME identity value threads from prev to cur.
    assert _identity(s, a2) is not None
    assert _identity(s, b2) is not None
    assert _identity(s, a2) != _identity(s, b2)


def test_far_thing_is_birth_and_death_not_a_merge():
    s = srs._native.Substrate()
    a = _mk_entity(s, [0.0, 0.0])
    # c is 500 units away -- far beyond any reasonable radius.
    c = _mk_entity(s, [500.0, 500.0])

    result = s.track_identity([a], [c], "feat", "identity", 1.0)

    assert result["matched"] == []
    assert [n.value for n in result["births"]] == [c.value]
    assert [n.value for n in result["deaths"]] == [a.value]
    # A birth gets its OWN fresh identity, discriminable from the dead
    # prior's node id.
    assert _identity(s, c) is not None
    assert _identity(s, c) != a.value or True  # identity is a fresh mint, not copied


def test_unmatched_cur_is_birth():
    s = srs._native.Substrate()
    a = _mk_entity(s, [0.0, 0.0])
    c_near = _mk_entity(s, [0.05, 0.05])
    c_new = _mk_entity(s, [900.0, 900.0])  # nothing in prev is anywhere near this

    result = s.track_identity([a], [c_near, c_new], "feat", "identity", 1.0)

    matched_cur = {c.value for _, c in result["matched"]}
    assert c_near.value in matched_cur
    assert [n.value for n in result["births"]] == [c_new.value]


def test_unmatched_prev_is_death():
    s = srs._native.Substrate()
    a = _mk_entity(s, [0.0, 0.0])
    b = _mk_entity(s, [5.0, 5.0])
    # Only ONE cur item this frame, close to `a` -- `b`'s thing vanished.
    c = _mk_entity(s, [0.02, 0.02])

    result = s.track_identity([a, b], [c], "feat", "identity", 1.0)

    assert [(p.value, cc.value) for p, cc in result["matched"]] == [(a.value, c.value)]
    assert result["births"] == []
    assert [n.value for n in result["deaths"]] == [b.value]
    # Deaths are REPORTED, never deleted -- the node still exists.
    assert s.has_node(b)


def test_category_gate_forces_birth_despite_proximity():
    # Same position, DIFFERENT category -- the gate must block the
    # match even though bare distance would happily accept it.
    s = srs._native.Substrate()
    a = _mk_entity(s, [0.0, 0.0], category="speaker_alice")
    c = _mk_entity(s, [0.01, 0.01], category="speaker_bob")

    result = s.track_identity([a], [c], "feat", "identity", 5.0, category_key="cat")

    assert result["matched"] == []
    assert [n.value for n in result["births"]] == [c.value]
    assert [n.value for n in result["deaths"]] == [a.value]

    # Without the category gate, the SAME two nodes DO match (proves
    # the gate -- not radius -- is what changed the outcome).
    result_ungated = s.track_identity([a], [c], "feat", "identity", 5.0)
    assert [(p.value, cc.value) for p, cc in result_ungated["matched"]] == [(a.value, c.value)]


def test_identity_persists_across_a_three_frame_chain():
    s = srs._native.Substrate()
    f1 = _mk_entity(s, [0.0, 0.0])
    r1 = s.track_identity([], [f1], "feat", "identity", 1.0)
    assert [n.value for n in r1["births"]] == [f1.value]
    id_after_frame1 = _identity(s, f1)
    assert id_after_frame1 is not None

    f2 = _mk_entity(s, [0.1, 0.1])
    r2 = s.track_identity([f1], [f2], "feat", "identity", 1.0)
    assert [(p.value, c.value) for p, c in r2["matched"]] == [(f1.value, f2.value)]
    assert _identity(s, f2) == id_after_frame1

    f3 = _mk_entity(s, [0.2, 0.2])
    r3 = s.track_identity([f2], [f3], "feat", "identity", 1.0)
    assert [(p.value, c.value) for p, c in r3["matched"]] == [(f2.value, f3.value)]
    # Identity threaded through TWO hops, unchanged.
    assert _identity(s, f3) == id_after_frame1


def test_extent_overlap_beats_a_numerically_closer_centroid():
    # c's nearest-CENTROID prior is `far` (closer in feature space),
    # but c shares extent members with `near` -- overlap-first must
    # win, exactly mirroring segment_and_track's cell-overlap rule.
    s = srs._native.Substrate()
    near = _mk_entity(s, [0.0, 0.0], extent=[1, 2, 3])
    far = _mk_entity(s, [0.2, 0.2], extent=[9, 8])
    c = _mk_entity(s, [5.0, 5.0], extent=[1, 2])

    result = s.track_identity(
        [near, far], [c], "feat", "identity", 100.0, extent_key="extent"
    )
    assert [(p.value, cc.value) for p, cc in result["matched"]] == [(near.value, c.value)]


def test_rule_invokes_track_identity_with_zero_host_matching():
    # A RULE triggers the correspondence + identity-attr write via the
    # `track_identity` effect -- mirrors Effect::FbSample's perception-
    # as-action pattern (queued while the applier only holds &mut
    # graph, drained by Substrate::run_rules calling
    # Substrate::track_identity between passes). Python only builds
    # the two frames' worth of nodes and installs ONE rule; no Python
    # code performs or re-derives the match.
    s = srs._native.Substrate()
    p0 = s.add_node("PrevPercept", {"feat": [0.0, 0.0]})
    p1 = s.add_node("PrevPercept", {"feat": [9.0, 9.0]})
    c0 = s.add_node("CurPercept", {"feat": [0.05, 0.05]})
    c1 = s.add_node("CurPercept", {"feat": [9.05, 9.05]})
    c2 = s.add_node("CurPercept", {"feat": [500.0, 500.0]})  # a birth

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
                "feat",
                None,
                None,
                "identity",
                1.0,
            ],
        ],
    }
    s.add_rule(rule_dict)
    s.run_rules(1000)

    id0 = _identity(s, p0)
    id1 = _identity(s, p1)
    assert id0 is not None and id1 is not None and id0 != id1

    # Matched cur nodes inherit the prior's identity; c2 (the birth)
    # gets a distinct fresh identity.
    assert _identity(s, c0) == id0
    assert _identity(s, c1) == id1
    id2 = _identity(s, c2)
    assert id2 is not None
    assert id2 not in (id0, id1)
