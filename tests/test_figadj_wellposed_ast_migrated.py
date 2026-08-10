"""M-D (§13) -- did a literal enter with the WELL-POSEDNESS conjunct?

A TERM-TREE AST WALK, never a substring selector (§12: a selector that matches
by substring is not a selector).

The claim under audit (VISION_FIGADJ_WELLPOSED_PREREG.md §2): the conjunct that
closes the speckle false-mint control is a NEGATED EXISTENTIAL over the graph's
own adjacency -- "no member cell faces two DISTINCT enclosed rivals" -- and is
therefore a HOLD-OPEN of the same kind the seed already applies to a tie, not a
bound on any measured magnitude.

The sharpest assertion here is `test_the_conjunct_contains_NO_Count_at_all`:
the obvious fix for this failure was a minimum-SIZE threshold, and a size
threshold cannot be written without bounding a count. If no `Count` appears
anywhere in the subtree, the conjunct provably is not a size test in disguise.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "vision_border_ownership.json")

COMPARISONS = {"Eq", "Lt", "Lte", "Gt", "Gte"}
FLAG_KEYS = {"bown", "bown_own", "bown_wp", "bown_nest", "bg", "frame", "owns"}
MAGNITUDE_KEYS = {"val", "rim", "glabel", "cid", "members", "root"}


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


def _rules(seed):
    return {r["name"]: r for r in seed["rules"]}


def _walk(term, path=()):
    if isinstance(term, dict):
        yield path, term
        for k, v in term.items():
            yield from _walk(v, path + (k,))
    elif isinstance(term, list):
        for i, v in enumerate(term):
            yield from _walk(v, path + (i,))


def _flag_read(node, key):
    """Is this node `Attr(PickUnique(NodesOfType(BorderOwnParams)), key)`?"""
    return (isinstance(node, dict) and node.get("type") == "Attr"
            and node.get("key") == key
            and node.get("node", {}).get("type") == "PickUnique"
            and node["node"].get("source", {}).get("node_type")
            == "BorderOwnParams")


def _wellposed_conjunct(seed):
    """Locate the conjunct STRUCTURALLY: the unique top-level `Or` in
    bo_mint_owned's `where` whose first item reads the `bown_wp` flag."""
    owned = _rules(seed)["bo_mint_owned"]
    found = [item for item in owned["where"]["items"]
             if item.get("type") == "Or"
             and any(_flag_read(sub.get("a", {}), "bown_wp")
                     for sub in item.get("items", [])
                     if isinstance(sub, dict))]
    assert len(found) == 1, (
        f"expected exactly one bown_wp-gated Or conjunct, found {len(found)}")
    return found[0]


def _body(seed):
    """The well-posedness predicate itself -- the Or's non-flag branch."""
    conj = _wellposed_conjunct(seed)
    body = [item for item in conj["items"]
            if not (item.get("type") in COMPARISONS
                    and _flag_read(item.get("a", {}), "bown_wp"))]
    assert len(body) == 1, "the Or must be exactly (flag-off | well-posed)"
    return body[0]


# --------------------------------------------------------------------------

def test_seed_is_v1_3_0_and_EVERY_flag_defaults_OFF():
    seed = _seed()
    assert seed["version"] == "1.3.0"
    params = [n for n in seed["nodes"] if n["type"] == "BorderOwnParams"]
    assert len(params) == 1
    # §9: every committed result must reproduce byte-identically by default.
    assert params[0]["attrs"]["bown_wp"] == 0.0
    assert params[0]["attrs"]["bown_own"] == 0.0
    assert params[0]["attrs"]["bown"] == 0.0
    assert params[0]["attrs"]["bown_nest"] == 0.0


def test_the_conjunct_is_a_NEGATED_EXISTENTIAL_not_a_bound():
    """A hold-open, structurally: Not(Exists member: Exists rival: Exists other
    rival). Located by shape, never by name or substring."""
    body = _body(_seed())
    assert body["type"] == "Not", "the conjunct must REFUSE, not assert"
    lvl1 = body["arg"]
    assert lvl1["type"] == "Exists"                     # some member cell
    lvl2 = lvl1["predicate"]
    assert lvl2["type"] == "Exists"                     # facing some rival
    lvl3 = [i for i in lvl2["predicate"]["items"] if i.get("type") == "Exists"]
    assert len(lvl3) == 1, "expected exactly one inner rival existential"
    assert lvl3[0]["type"] == "Exists"                  # and a DIFFERENT rival


def test_the_conjunct_contains_NO_Count_at_all():
    """THE LOAD-BEARING ASSERTION. The refused fix for this control was a
    minimum-SIZE threshold, and no size test can be written without bounding a
    count. Zero `Count` nodes in the subtree ⇒ provably not a size test."""
    counts = [n for _, n in _walk(_body(_seed()))
              if isinstance(n, dict) and n.get("type") == "Count"]
    assert not counts, (
        "a Count entered the well-posedness conjunct — a size threshold in "
        f"disguise: {json.dumps(counts, indent=1)}")


def test_EVERY_literal_in_the_conjunct_is_a_0_1_flag_discriminator():
    offenders = []
    for _p, node in _walk(_wellposed_conjunct(_seed())):
        if not (isinstance(node, dict) and node.get("type") in COMPARISONS):
            continue
        for lit, other in ((node.get("a"), node.get("b")),
                           (node.get("b"), node.get("a"))):
            if not (isinstance(lit, dict) and lit.get("type") == "Lit"):
                continue
            ok = (isinstance(other, dict) and other.get("type") == "Attr"
                  and other.get("key") in FLAG_KEYS) or _flag_read(other or {},
                                                                   "bown_wp")
            if not ok:
                offenders.append(node)
    assert not offenders, (
        "literal compared against a non-flag inside the well-posedness "
        f"conjunct: {json.dumps(offenders, indent=1)}")


def test_NO_literal_touches_a_MAGNITUDE_inside_the_conjunct():
    """Asserted the other way round, so a hole in one cannot satisfy the other."""
    bad = []
    for _p, node in _walk(_wellposed_conjunct(_seed())):
        if not (isinstance(node, dict) and node.get("type") in COMPARISONS):
            continue
        for lit, other in ((node.get("a"), node.get("b")),
                           (node.get("b"), node.get("a"))):
            if (isinstance(lit, dict) and lit.get("type") == "Lit"
                    and isinstance(other, dict)
                    and other.get("type") == "Attr"
                    and other.get("key") in MAGNITUDE_KEYS):
                bad.append(node)
    assert not bad, f"§13 violation: {json.dumps(bad, indent=1)}"


def test_every_glabel_comparison_in_the_conjunct_is_Attr_vs_Attr():
    """The rival-distinctness test must compare two MEASURED labels, with no
    literal on either side — the same shape as the ownership comparison."""
    seen = 0
    for _p, node in _walk(_body(_seed())):
        if not (isinstance(node, dict) and node.get("type") == "Eq"):
            continue
        a, b = node.get("a", {}), node.get("b", {})
        if not (isinstance(a, dict) and a.get("key") == "glabel"):
            continue
        seen += 1
        assert a.get("type") == "Attr" and b.get("type") == "Attr", node
        assert b.get("key") == "glabel", node
    # member-identity, rival-vs-R (x2), and rival-vs-rival
    assert seen >= 3, f"expected >=3 glabel comparisons, saw {seen}"


def test_the_INCUMBENT_path_never_reads_the_new_flag():
    """§9. bo_mint_enclosed must be untouched, so the incumbent reproduces."""
    inc = _rules(_seed())["bo_mint_enclosed"]
    reads = [n for _, n in _walk(inc["where"]) if _flag_read(n, "bown_wp")]
    assert not reads, "the incumbent predicate now reads bown_wp"


def test_the_well_posedness_test_is_confined_to_ENCLOSED_rivals():
    """Scope discipline (§8): the conjunct governs the rival side only. The
    ground side keeps its own, pre-existing, unmodified closure test — so this
    rung is not silently re-tightening the incumbent's ground criterion."""
    body = _body(_seed())
    bg_cmps = [n for _, n in _walk(body)
               if isinstance(n, dict) and n.get("type") == "Lt"
               and isinstance(n.get("a"), dict)
               and n["a"].get("key") == "bg"]
    # every bg test in the conjunct selects ENCLOSED cells (bg < 0.5)
    assert len(bg_cmps) >= 3, f"expected >=3 enclosure tests, saw {len(bg_cmps)}"
    for n in bg_cmps:
        assert n["b"] == {"type": "Lit", "value": 0.5}, n
