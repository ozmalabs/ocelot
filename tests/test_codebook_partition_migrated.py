"""tests/test_codebook_partition_migrated.py — the codebook-partition invariants,
gated instead of merely docstring'd.

Provenance: `docs/research/engine_substrate/CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md`,
which investigated `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a) — *"The codebook is
partitioned two different ways at once ... it is the **same need** `kind` exists to
serve."* Measurement INVERTED that premise:

  * a **node type** is the ONLY thing that partitions a `ShapeDecode` candidate pool;
  * the **`kind` attr** is a pass-through LABEL — `load_parts` reads it into
    `Part.kind_val` and reports it in the plan, and NOTHING filters on it;
  * so the two are not two ways of serving one need. Consolidating a
    `ShapeSignature*` type into `ShapeSignature{kind:...}` DELETES the only working
    isolation mechanism.

Every reason below is currently stated only in a docstring or a seed `description`
(`domains/stroke_codebook.py::grow_stroke_refinement_quantum` — *"a genuinely separate
node TYPE makes that PROVABLY impossible ... rather than merely improbable"*;
`seeds/coherence_relations.json` — *"kept in their OWN codebook_type so they never
compete with the clause-construction ShapeSignature pool"*). A claim that lives only in
a docstring is not gated. These tests gate them, using REAL seed data.

Hermetic: no boot, no daemon, no dataset — `seeds/*.json` node declarations loaded
straight into a bare `srs.Substrate`, which is exactly what `load_parts` reads.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

import substrate_rs as srs

_ROOT = Path(__file__).resolve().parent.parent
_SEEDS = _ROOT / "seeds"


# --------------------------------------------------------------------------- #
#  helpers — mechanical seed I/O + the live reading-faculty decode call shape
# --------------------------------------------------------------------------- #
def _seed_nodes(name: str) -> list[dict]:
    # reading_constructions is domain data (domain_data/, tranche 11); the rest are seeds.
    path = _SEEDS / f"{name}.json"
    if not path.exists():
        path = _ROOT / "domain_data" / f"{name}.json"
    with open(path) as f:
        return [n for n in (json.load(f).get("nodes") or []) if isinstance(n, dict)]


def _sig(node: dict):
    v = (node.get("attrs") or {}).get("signature")
    if v is None:
        return None
    return json.loads(v) if isinstance(v, str) else [list(r) for r in v]


def _build(seeds, *, merge_into: str | None = None) -> srs.Substrate:
    """`merge_into` rewrites every `ShapeSignature*` node's TYPE — i.e. it applies
    the consolidation §3.4(a) proposes, to real graph data."""
    s = srs.Substrate()
    for name in seeds:
        for nd in _seed_nodes(name):
            t = nd["type"]
            if merge_into and isinstance(t, str) and t.startswith("ShapeSignature"):
                t = merge_into
            s.add_node(t, dict(nd.get("attrs", {})))
    return s


def _decode(s: srs.Substrate, goal, codebook_type: str, **extra) -> list[tuple]:
    """`domains/discourse_coherence.py::_decode`'s call shape, verbatim."""
    term = {"type": "ShapeDecode", "goal": {"type": "Lit", "value": goal},
            "codebook_type": codebook_type, "beam": 1, "max_steps": 1, "cand_k": 4}
    term.update(extra)
    r = s._inner.evaluate(term, {})
    return [(p["part"], p["kind"], p["shape_fit"], len(p["covers"]))
            for p in (r.get("plan") or [])]


# --------------------------------------------------------------------------- #
#  1. The mechanism: `kind` does not scope a decode pool. The node type does.
# --------------------------------------------------------------------------- #
def test_kind_is_a_label_not_a_pool_filter():
    """`shape_decode.rs::load_parts` reads `kind` into `Part.kind_val` (:260, :313)
    and `eval_shape_decode` copies it into the plan step (:1380) — it is never a
    predicate on candidacy. The two filters that DO exist (`codebook_scope`,
    `exclude`) are keyed on the part's NAME.

    This is the fact the whole consolidation question turns on, so it is gated
    directly rather than inferred."""
    s = srs.Substrate()
    s.add_node("ShapeSignature", {"name": "p_alpha", "kind": "alpha",
                                  "signature": '[["AAA","x"]]'})
    s.add_node("ShapeSignature", {"name": "p_beta", "kind": "beta",
                                  "signature": '[["BBB","y"]]'})

    goal = [["BBB", "y"]]
    base = _decode(s, goal, "ShapeSignature")
    assert [p[0] for p in base] == ["p_beta"], base
    assert base[0][1] == "beta", "kind IS carried through to the plan as a label"

    # A `kind` / `codebook_kind` term key is not part of ShapeDecode's wire form.
    # It is silently DROPPED — the decode is byte-identical to the unfiltered one.
    for key in ("kind", "codebook_kind"):
        assert _decode(s, goal, "ShapeSignature", **{key: "alpha"}) == base, (
            f"a `{key}` term key changed the decode — if a kind-scoped decode has "
            "been built, CODEBOOK_PARTITION_CONSOLIDATION_RESULTS.md's central "
            "finding (and its NO-GO) must be re-measured")

    # A foreign-`kind` part in the same node type is a fully live candidate.
    assert _decode(s, [["AAA", "x"]], "ShapeSignature")[0][0] == "p_alpha"

    # What DOES scope the pool, both keyed on NAME:
    assert _decode(s, goal, "ShapeSignature",
                   codebook_scope={"type": "Lit", "value": ["p_alpha"]}) == []
    assert _decode(s, goal, "ShapeSignature",
                   exclude={"type": "Lit", "value": ["p_beta"]}) == []

    # And the node TYPE is an absolute partition.
    assert _decode(s, goal, "ShapeSignatureNoSuchPool") == []


# --------------------------------------------------------------------------- #
#  2. The one split with a stated reason — and the collision that proves it.
# --------------------------------------------------------------------------- #
def test_coherence_codebook_must_stay_its_own_node_type():
    """`seeds/coherence_relations.json`'s own description: coherence relations are
    *"kept in their OWN codebook_type so they never compete with the
    clause-construction ShapeSignature pool"*. That seed **depends_on**
    `reading_constructions`, so the two are always co-loaded — and they DO collide:

        reading_constructions  ShapeSignature{name:'conditional'}   [["IF"],["THEN"]]
        coherence_relations    ShapeSignatureCoherence{'condition_if'} [["IF"]]

    Merged into one pool, a coherence decode of a marked conditional stops
    recognising `condition_if` and recognises the clause construction instead."""
    goal = [["IF"]]
    sep = _build(["reading_constructions", "coherence_relations"])
    mer = _build(["reading_constructions", "coherence_relations"],
                 merge_into="ShapeSignature")

    before = _decode(sep, goal, "ShapeSignatureCoherence")
    after = _decode(mer, goal, "ShapeSignature")

    assert [p[0] for p in before] == ["condition_if"], before
    assert before != after, (
        "the IF collision no longer changes the verdict — the measured justification "
        "for ShapeSignatureCoherence's separate type has moved; re-measure before "
        "treating it as redundant")
    assert [p[0] for p in after] == ["conditional"], after


# --------------------------------------------------------------------------- #
#  3. The stroke grain ladder — a STRUCTURAL guarantee, not a probabilistic one.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("goal_type,pool", [
    ("ShapeSignatureCoarse", "ShapeSignatureCoarse"),
    ("ShapeSignatureMid", "ShapeSignatureMid"),
    ("ShapeSignatureFineChild", "ShapeSignatureFineChild"),
])
def test_stroke_grain_ladder_must_stay_separate_node_types(goal_type, pool):
    """All four stroke grains carry the SAME predicate vocabulary
    (`seg`/`pose_x`/`pose_y`/`pose_o`/`pose_s`) at overlapping relation counts, so
    they are the one family where a merge is unambiguously destructive.
    `stroke_codebook.grow_stroke_refinement_quantum` says exactly this — *"a
    genuinely separate node TYPE makes that PROVABLY impossible ... rather than
    merely improbable"*. Measured over the full seed: 261 of 502 held signatures
    decode DIFFERENTLY when the four types are merged, and the PRIMARY fine-grain
    verdict changes for 147/237 (coarse merged alone) and 46/237 (mid alone).

    `ShapeSignatureFineChild` is the honest exception in ONE direction: merging its
    10 children changes 0/237 fine-grain verdicts on today's seed — its guarantee is
    prophylactic, exactly as its docstring claims ("PROVABLY impossible rather than
    merely improbable"). It still changes the CHILD-goal decodes this gate measures,
    because a merged child then contends against the whole 263-part fine pool."""
    sep = _build(["stroke_shapes"])
    mer = _build(["stroke_shapes"], merge_into="ShapeSignature")
    goals = [(_sig(n), n["attrs"]["name"]) for n in _seed_nodes("stroke_shapes")
             if n["type"] == goal_type and _sig(n)]
    assert goals, f"no {goal_type} signatures in seeds/stroke_shapes.json"

    changed = sum(1 for g, _ in goals[:40]
                  if _decode(sep, g, pool) != _decode(mer, g, "ShapeSignature"))
    assert changed > 0, (
        f"merging {goal_type} into ShapeSignature no longer changes any of the "
        f"first {min(40, len(goals))} {goal_type} decodes — the measured basis for "
        "keeping the stroke grain ladder on separate node types has changed")


# --------------------------------------------------------------------------- #
#  4. The one isolation the tree gets WITHOUT a separate type — and its condition.
# --------------------------------------------------------------------------- #
def test_substroke_arity_disjointness_is_the_only_thing_separating_it_from_stroke():
    """`ShapeSignature{kind:'substroke'}` shares ONE pool with
    `ShapeSignature{kind:'stroke'}` — `domains/ink_decode.py::decode_substrokes`
    scores against the DEFAULT `codebook_type='ShapeSignature'` and justifies it as
    *"arity-distinct from every stroke-grain entry ... why this is safe without a
    companion node type"*.

    That is an EMERGENT property of the seed data, not a structural guarantee, and
    it has an exact failure condition: a signature's relation count is
    `segments + 4` (four `pose_*` singletons), so a stroke-grain quantum authored
    with `segments == SUBSTROKE_SEGMENTS (4)` would land at arity 8 and collide.
    `DEFAULT_SEGMENTS` is 12. This gate pins the disjointness so the collision is
    caught by a test rather than by a silent misrecognition."""
    from domains.stroke_codebook import DEFAULT_SEGMENTS, SUBSTROKE_SEGMENTS

    arities: dict[str, set[int]] = {}
    for nd in _seed_nodes("stroke_shapes"):
        if nd["type"] != "ShapeSignature":
            continue
        sig = _sig(nd)
        if sig:
            arities.setdefault(nd["attrs"].get("kind"), set()).add(len(sig))

    assert "stroke" in arities and "substroke" in arities, arities
    assert not (arities["stroke"] & arities["substroke"]), (
        f"stroke and substroke signatures now share a relation count "
        f"({sorted(arities['stroke'] & arities['substroke'])}). They share ONE "
        "ShapeDecode pool; arity was the only separator. Give substroke its own "
        "node type, or re-measure decode_substrokes.")
    assert DEFAULT_SEGMENTS != SUBSTROKE_SEGMENTS, (
        "DEFAULT_SEGMENTS == SUBSTROKE_SEGMENTS makes the arity separation above "
        "unreachable for any newly minted stroke quantum")

    # And the disjointness is live, not just arithmetic: no substroke goal is ever
    # fully covered by a stroke-grain part, and vice versa.
    s = _build(["stroke_shapes"])
    kind_of = {n["attrs"]["name"]: n["attrs"].get("kind")
               for n in _seed_nodes("stroke_shapes") if n["type"] == "ShapeSignature"}
    for nd in _seed_nodes("stroke_shapes"):
        if nd["type"] != "ShapeSignature" or nd["attrs"].get("kind") != "substroke":
            continue
        won = _decode(s, _sig(nd), "ShapeSignature")
        for part, _kind, _fit, _n in won:
            assert kind_of.get(part) == "substroke", (
                f"substroke goal {nd['attrs']['name']!r} recruited a "
                f"{kind_of.get(part)!r}-kind part {part!r} from the shared pool")


# --------------------------------------------------------------------------- #
#  5. The staging types — named, so a future reader does not mistake them.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("seed,staging_type,derived_kind", [
    ("register_source", "ShapeSignatureRegister", "register_sig"),
    ("format_channel", "ShapeSignatureFormat", "format_sig"),
])
def test_staging_signature_types_are_not_decode_pools(seed, staging_type, derived_kind):
    """`ShapeSignatureRegister` / `ShapeSignatureFormat` (and `ShapeSignatureMeter`)
    are NOT codebooks. `ensure_*_codebook` PROJECTS each into a plain
    `ShapeSignature{kind:'<derived>'}` decode-part carrying the SAME name and the
    SAME signature; the decode runs against the DEFAULT pool. So for this family the
    division is already the correct one — **type = pool, kind = label within a
    pool** — and merging the staging type in would create a name-duplicate of its
    own derived part inside the pool it feeds."""
    # No decode anywhere points at the staging type — in seed rule bodies OR through a
    # Python module constant (the form a seed-only grep misses, e.g.
    # `domains/trope_theme.py:111 _CODEBOOK_TYPE = "ShapeSignatureTrope"`).
    for p in (list(_SEEDS.glob("*.json")) + list((_ROOT / "domain_data").glob("*.json"))
              + list((_ROOT / "domains").glob("*.py"))):
        text = p.read_text()
        assert f'"codebook_type": "{staging_type}"' not in text, (p, staging_type)
        assert f'CODEBOOK_TYPE = "{staging_type}"' not in text, (
            f"{p.name} now names {staging_type} as a codebook_type — it was a staging "
            "type, projected into the shared ShapeSignature pool, not a pool itself")

    mod = (_ROOT / "domains" / f"{seed}.py").read_text()
    assert f'"kind": "{derived_kind}"' in mod, (
        f"{seed}.py no longer projects a ShapeSignature{{kind:'{derived_kind}'}} "
        "decode-part — the staging/pool division has changed")
    assert 'sub.add_node("ShapeSignature"' in mod
