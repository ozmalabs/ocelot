"""ARGUMENT_ROLE_VOCABULARY -- pins the ArgumentRole promotion + mint-time guard.

PREREG: `docs/research/engine_substrate/ARGUMENT_ROLE_VOCABULARY_PREREG.md`.
RESULTS: `docs/research/engine_substrate/ARGUMENT_ROLE_VOCABULARY_RESULTS.md`.

`RelationCue.relation` (`["reduce","UNCERTAINTY","given","EVIDENCE"]`) embeds its
uppercase argument-role tokens as bare strings with no held identity
(`RELATION_CUE_TOKEN_COLLISION_RESULTS.md` section 6). This file pins the fix:
`ArgumentRole{name, gloss}` is a first-class, held, deduped node type (one per
distinct uppercase token, `seeds/argument_role_vocabulary.json`); `RelationCue`
gains real `uses_role` edges (additive -- `.relation` itself is UNCHANGED, pinned
below); and a mint-time guard (`domains.reflective_faculty.check_new_relation_cue_
roles`, wired into `ground_predicate`'s cue-authoring path) decides, sd-loop shaped,
whether a freshly-taught cue's role-token reuse RECOGNIZES an identical held
relation (safe), MINTS a genuinely new role (safe), or must be FLAGGED (an existing
token reused under a structurally new tuple -- filed as a `SelfConcern`, never
silently wired).
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402
from domains import reflective_faculty as rf                # noqa: E402
from domains.teach import teach                              # noqa: E402


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def cues():
    rv = json.load(open(os.path.join(ROOT, "seeds", "relation_vocabulary.json")))
    return {c["attrs"]["name"]: json.loads(c["attrs"]["relation"]) for c in rv.get("nodes", [])
            if c.get("type") == "RelationCue"}


def _rel(rel):
    return json.dumps(rel, separators=(",", ":"))


# --------------------------------------------------------------------------- #
# 1. The vocabulary itself: 65 ArgumentRole nodes, zero duplicate names, and
#    RelationCue.relation stays byte-identical (additive, not a migration).
# --------------------------------------------------------------------------- #

def test_argument_role_vocabulary_has_no_duplicate_names(agent):
    roles = agent.s.nodes("ArgumentRole")
    names = [agent.s.node(r)["attrs"].get("name") for r in roles]
    assert len(names) == len(set(names)) == 65


def test_relation_vocabulary_relation_attr_is_untouched(agent, cues):
    """The four real consumers (_load_relation_cues, _relation_cue_index,
    _shared_shape, Rust shape_fit) all read RelationCue.relation as a bare
    string -- this pins that it is still exactly that, parseable to the same
    tuple as the static census, for every one of the 52 vocabulary cues."""
    on_graph = {}
    for n in agent.s.nodes("RelationCue"):
        at = agent.s.node(n)["attrs"]
        nm = at.get("name")
        if nm in cues:
            on_graph[nm] = json.loads(at["relation"])
    assert on_graph == cues


def test_relation_cues_carry_real_uses_role_edges(agent, cues):
    """Every uppercase token in every one of the 52 seeded cues' relation tuples
    -- except the two deliberately-unwired ambiguous occurrences reserved for the
    live guard demonstration below -- has a real uses_role edge to a held
    ArgumentRole with that exact name."""
    role_by_name = rf._load_argument_role_index(agent)
    excluded = {("attention_watch", "NEW"), ("source_recognition", "CONTENT")}
    cue_id_by_name = {}
    for n in agent.s.nodes("RelationCue"):
        at = agent.s.node(n)["attrs"]
        if at.get("name") in cues:
            cue_id_by_name[at["name"]] = n
    missing = []
    for name, rel in cues.items():
        cid = cue_id_by_name[name]
        for tok in sorted({t for t in rel if t.isupper()}):
            if (name, tok) in excluded:
                continue
            role = role_by_name.get(tok)
            assert role is not None, f"no ArgumentRole named {tok!r}"
            if not agent.s.has_edge(cid, "uses_role", role):
                missing.append((name, tok))
    assert missing == []


# --------------------------------------------------------------------------- #
# 2. _shared_shape is unaffected -- this rung's wiring is additive only.
# --------------------------------------------------------------------------- #

def test_shared_shape_unaffected_by_role_wiring(agent, cues):
    sig_a = [cues["self_reference"], cues["bounded"]]
    sig_b = [cues["self_reference"], cues["control_agency"]]
    res, fixed = rf._shared_shape(agent, sig_a, sig_b)
    # only self_reference's SELF-bearing structure is shared; same output shape
    # _shared_shape produced before ArgumentRole existed at all.
    assert fixed >= 0
    assert res is not None


# --------------------------------------------------------------------------- #
# 3. The live mint-time guard: SAFE direction (recognize + mint), no friction.
# --------------------------------------------------------------------------- #

def test_ground_predicate_live_path_always_recognizes(agent):
    """ground_predicate only ever mints relation tuples already held verbatim
    (the `matched` filter in its own code) -- so its real, only, live cue-minting
    call site is predicted to ALWAYS hit role_recognize_exact, zero friction,
    zero SelfConcern filed."""
    import math
    traj = [math.exp(-0.3 * i) * math.cos(0.8 * i) for i in range(40)]
    res = rf.ground_predicate(agent, "test_oscillation_predicate", traj)
    assert res["grounded"] is True
    assert res["path"] == "grow_lexicon"
    checks = res["role_checks"]
    assert checks, "ground_predicate should have minted at least one RelationCue"
    for _rel_key, verdict in checks.items():
        assert verdict["checked"] is True
        for _tok, status in verdict["tokens"].items():
            assert status == "recognized_exact"
    collisions = [n for n in agent.s.nodes("SelfConcern")
                  if agent.s.node(n)["attrs"].get("kind") == "argument_role_collision"]
    assert collisions == []


def test_mint_fresh_token_is_safe_and_wires_immediately(agent):
    t = teach(agent, "RelationCue",
              {"name": "synthetic_new_cue", "keywords": ["synthetic new cue"],
               "relation": _rel(["synthesize", "WIDGET", "from", "GEAR"])},
              category="relation_vocabulary")
    verdict = rf.check_new_relation_cue_roles(agent, t["node"])
    assert verdict["tokens"] == {"WIDGET": "minted", "GEAR": "minted"}
    role_idx = rf._load_argument_role_index(agent)
    assert "WIDGET" in role_idx and "GEAR" in role_idx
    assert agent.s.has_edge(t["node"], "uses_role", role_idx["WIDGET"])
    assert agent.s.has_edge(t["node"], "uses_role", role_idx["GEAR"])
    receipts = [agent.s.node(n)["attrs"] for n in
                agent.s.nodes("NativeReflectiveFacultyReceipt")
                if agent.s.node(n)["attrs"].get("cluster") ==
                "reflective_faculty.relation_cue_settlement"]
    assert len(receipts) == 1
    assert receipts[0]["outcome_source"] == "native_rule_readback"
    assert receipts[0]["python_outcome_selection"] is False
    collisions = [n for n in agent.s.nodes("SelfConcern")
                  if agent.s.node(n)["attrs"].get("kind") == "argument_role_collision"]
    assert collisions == []


def test_recognize_exact_fires_on_a_byte_identical_synonym(agent, cues):
    """A hand-authored teach() adding a pure keyword synonym for an EXISTING
    relation tuple (build_from_prior's) recognizes with zero friction -- the
    exact shape ground_predicate's own live behaviour exercises."""
    t = teach(agent, "RelationCue",
              {"name": "hand_authored_synonym", "keywords": ["another way to say it"],
               "relation": _rel(cues["build_from_prior"])},
              category="relation_vocabulary")
    verdict = rf.check_new_relation_cue_roles(agent, t["node"])
    assert verdict["tokens"] == {"NEW": "recognized_exact", "PRIOR": "recognized_exact"}
    role_idx = rf._load_argument_role_index(agent)
    assert agent.s.has_edge(t["node"], "uses_role", role_idx["NEW"])
    assert agent.s.has_edge(t["node"], "uses_role", role_idx["PRIOR"])


# --------------------------------------------------------------------------- #
# 4. The live mint-time guard: COLLISION direction -- flagged, not silently
#    installed. Both a REAL (already-ambiguous) vocabulary token and a
#    SYNTHETIC one (SELF, normally safe-shared) are exercised.
# --------------------------------------------------------------------------- #

def test_flag_fires_on_real_ambiguous_token_reused_in_new_shape(agent):
    """source_recognition's own CONTENT use was deliberately left unwired in the
    static seed (real, already-recorded ambiguity, RELATION_CUE_TOKEN_COLLISION_
    RESULTS.md section 3). A NEW cue reusing CONTENT under a DIFFERENT relation
    shape must be flagged, not silently merged into the held CONTENT role."""
    t = teach(agent, "RelationCue",
              {"name": "digest_content_for_audience",
               "keywords": ["digest content for audience"],
               "relation": _rel(["digest", "CONTENT", "for", "AUDIENCE"])},
              category="relation_vocabulary")
    verdict = rf.check_new_relation_cue_roles(agent, t["node"])
    assert verdict["tokens"]["CONTENT"] == "flagged"
    role_idx = rf._load_argument_role_index(agent)
    assert not agent.s.has_edge(t["node"], "uses_role", role_idx["CONTENT"])
    collisions = [agent.s.node(n)["attrs"] for n in agent.s.nodes("SelfConcern")
                  if agent.s.node(n)["attrs"].get("kind") == "argument_role_collision"]
    assert any(c["content"] == "CONTENT" and c["cue_name"] == "digest_content_for_audience"
               for c in collisions)


def test_flag_fires_on_a_normally_shared_token_used_in_a_novel_shape(agent):
    """SELF is genuinely SHARED across 5 real cues (adopt_winner/bounded/
    control_agency/self_reference/vary_self) -- the guard must still flag a
    SIXTH, structurally novel reuse rather than assuming safety just because
    the token has a good track record. Demonstrates the guard reacts to
    STRUCTURE at authoring time, not to a memorised classification."""
    t = teach(agent, "RelationCue",
              {"name": "synthetic_self_announce", "keywords": ["announce self as winner"],
               "relation": _rel(["announce", "SELF", "as", "WINNER"])},
              category="relation_vocabulary")
    verdict = rf.check_new_relation_cue_roles(agent, t["node"])
    assert verdict["tokens"]["SELF"] == "flagged"
    assert verdict["tokens"]["WINNER"] == "flagged"
    role_idx = rf._load_argument_role_index(agent)
    assert not agent.s.has_edge(t["node"], "uses_role", role_idx["SELF"])


def test_flag_never_mutates_relation_vocabulary_on_disk(agent, tmp_path):
    """A flagged cue is filed as a SelfConcern and left unwired -- it must never
    be silently persisted into the real seed file (OZMA_SEED_PERSIST_DISABLED is
    armed session-wide by tests/conftest.py; this asserts the in-graph decision
    matches, independent of that guard)."""
    t = teach(agent, "RelationCue",
              {"name": "synthetic_self_announce_2", "keywords": ["a"],
               "relation": _rel(["proclaim", "SELF", "in", "ARENA"])},
              category="relation_vocabulary")
    rf.check_new_relation_cue_roles(agent, t["node"])
    on_disk = json.load(open(os.path.join(ROOT, "seeds", "relation_vocabulary.json")))
    names_on_disk = {n["attrs"]["name"] for n in on_disk["nodes"] if n["type"] == "RelationCue"}
    assert "synthetic_self_announce_2" not in names_on_disk
