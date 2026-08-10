"""M-D (§13) -- did a literal enter with the CONTAINMENT SCOPE?

A TERM-TREE AST WALK, never a substring selector (§12: four substring-selector
failures are recorded in this arc, two of them going red on their own
docstrings). Nothing here reads the seed as text.

The claim under audit (VISION_FIGADJ_NESTING_PREREG.md §1.4): the conjunct that
scopes the rival set to R's OUTER CONTOUR is a POSITIVE EXISTENTIAL over the
graph's own adjacency -- "this rival has a neighbour that is neither itself nor
R", i.e. it is not a hole in R -- and is therefore a correction to a
QUANTIFIER'S RANGE, not a bound on any measured magnitude.

The sharpest assertion is `test_the_conjunct_contains_NO_Count_at_all`: the
standing refused fix in this line of work is a minimum-SIZE threshold, and no
size test can be written without bounding a count. Zero `Count` nodes in the
subtree ⇒ provably not a size test in disguise.

`test_the_scope_is_SIZE_BLIND_by_construction` states the same claim from the
other side: the conjunct reads only `glabel` and `bg`, never `rim`, `val`,
`cid`, `members` or `root` -- so it cannot be sensitive to how big anything is.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "vision_border_ownership.json")

COMPARISONS = {"Eq", "Lt", "Lte", "Gt", "Gte"}
FLAG_KEYS = {"bown", "bown_own", "bown_wp", "bown_nest", "bg", "frame", "owns"}
MAGNITUDE_KEYS = {"val", "rim", "glabel", "cid", "members", "root"}
FLAG = "bown_nest"


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


def conjunct_paths(seed=None):
    """Locate EVERY containment-scope conjunct STRUCTURALLY: an `Or` whose first
    item reads the `bown_nest` flag. Located by SHAPE, never by substring.

    Returns [(path, node)] -- the path is what the injection control mutates,
    so a plant that lands somewhere else is detectable."""
    seed = seed if seed is not None else _seed()
    owned = _rules(seed)["bo_mint_owned"]
    out = []
    for path, node in _walk(owned["where"]):
        if (isinstance(node, dict) and node.get("type") == "Or"
                and any(_flag_read(sub.get("a", {}), FLAG)
                        for sub in node.get("items", [])
                        if isinstance(sub, dict))):
            out.append((path, node))
    return out


def _bodies(seed=None):
    """The containment predicates themselves -- each Or's non-flag branch."""
    bodies = []
    for _p, conj in conjunct_paths(seed):
        body = [i for i in conj["items"]
                if not (i.get("type") in COMPARISONS
                        and _flag_read(i.get("a", {}), FLAG))]
        assert len(body) == 1, "each Or must be exactly (flag-off | scope)"
        bodies.append(body[0])
    return bodies


# --------------------------------------------------------------------------

def test_seed_is_v1_3_0_and_the_new_flag_defaults_OFF():
    seed = _seed()
    assert seed["version"] == "1.3.0"
    params = [n for n in seed["nodes"] if n["type"] == "BorderOwnParams"]
    assert len(params) == 1
    # §9: every committed result must reproduce byte-identically by default.
    assert params[0]["attrs"][FLAG] == 0.0


def test_there_are_exactly_THREE_scoped_rival_sites():
    """PREREG §1.3: ONE definition of `rival`, used by BOTH conjuncts -- the
    ownership comparison's `n`, and the well-posedness conjunct's `n1` and `n2`.
    Fewer means the two conjuncts disagree about what a rival is; more means
    something else was scoped."""
    assert len(conjunct_paths()) == 3


def test_the_conjunct_is_a_POSITIVE_EXISTENTIAL_over_adjacency():
    """Structurally: Exists member-of-rival: Exists neighbour: (not rival, not
    R). A quantifier range correction, located by shape."""
    for body in _bodies():
        assert body["type"] == "Exists"
        assert body["source"]["type"] == "Filter"
        inner = body["predicate"]
        assert inner["type"] == "Exists"
        assert inner["source"]["type"] == "Neighbours"
        neg = [i for i in inner["predicate"]["items"]
               if i.get("type") == "Not"]
        assert len(neg) == 2, "must exclude BOTH the rival itself and R"


def test_the_conjunct_contains_NO_Count_at_all():
    """THE LOAD-BEARING ASSERTION. The standing refused fix in this line of work
    is a minimum-SIZE threshold, and no size test can be written without
    bounding a count. Zero `Count` nodes in the subtree ⇒ provably not a size
    test in disguise."""
    counts = [n for body in _bodies() for _p, n in _walk(body)
              if isinstance(n, dict) and n.get("type") == "Count"]
    assert not counts, (
        "a Count entered the containment conjunct — a size threshold in "
        f"disguise: {json.dumps(counts, indent=1)}")


def test_the_scope_is_SIZE_BLIND_by_construction():
    """The same claim from the other side, so a hole in one cannot satisfy the
    other: the conjunct READS only `glabel` and `bg`. It therefore cannot
    distinguish a 1-cell hole from a 200-cell hole, and cannot exclude a rival
    for being small."""
    keys = {n["key"] for body in _bodies() for _p, n in _walk(body)
            if isinstance(n, dict) and n.get("type") == "Attr"
            and "key" in n}
    assert keys == {"glabel", "bg"}, f"the scope reads more than it claims: {keys}"


def test_EVERY_literal_in_the_conjunct_is_a_0_1_flag_discriminator():
    offenders = []
    for _p, conj in conjunct_paths():
        for _q, node in _walk(conj):
            if not (isinstance(node, dict)
                    and node.get("type") in COMPARISONS):
                continue
            for lit, other in ((node.get("a"), node.get("b")),
                               (node.get("b"), node.get("a"))):
                if not (isinstance(lit, dict) and lit.get("type") == "Lit"):
                    continue
                ok = (isinstance(other, dict) and other.get("type") == "Attr"
                      and other.get("key") in FLAG_KEYS) or _flag_read(
                          other or {}, FLAG)
                if not ok:
                    offenders.append(node)
    assert not offenders, (
        "literal compared against a non-flag inside the containment conjunct: "
        f"{json.dumps(offenders, indent=1)}")


def test_NO_literal_touches_a_MAGNITUDE_inside_the_conjunct():
    bad = []
    for _p, conj in conjunct_paths():
        for _q, node in _walk(conj):
            if not (isinstance(node, dict)
                    and node.get("type") in COMPARISONS):
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
    """Containment is decided by comparing two MEASURED labels, with no literal
    on either side — the same shape as the ownership comparison."""
    seen = 0
    for body in _bodies():
        for _p, node in _walk(body):
            if not (isinstance(node, dict) and node.get("type") == "Eq"):
                continue
            a, b = node.get("a", {}), node.get("b", {})
            if not (isinstance(a, dict) and a.get("key") == "glabel"):
                continue
            seen += 1
            assert a.get("type") == "Attr" and b.get("type") == "Attr", node
            assert b.get("key") == "glabel", node
    # per site: member-of-rival identity, neighbour-vs-rival, neighbour-vs-R
    assert seen == 9, f"expected 9 glabel comparisons over 3 sites, saw {seen}"


def test_the_INCUMBENT_and_the_OTHER_rules_never_read_the_new_flag():
    """§9. Only bo_mint_owned may read `bown_nest`, so every other committed
    path reproduces."""
    rules = _rules(_seed())
    for name, rule in rules.items():
        if name == "bo_mint_owned":
            continue
        reads = [n for _p, n in _walk(rule.get("where", {}))
                 if _flag_read(n, FLAG)]
        assert not reads, f"{name} now reads {FLAG}"


def test_the_containment_scope_is_confined_to_ENCLOSED_rivals():
    """Scope discipline (§8): the correction governs the rival side only. Every
    `bg` test inside it selects ENCLOSED cells, so the ground-side closure test
    is untouched and this rung is not silently re-tightening it."""
    for body in _bodies():
        bg = [n for _p, n in _walk(body)
              if isinstance(n, dict) and n.get("type") == "Lt"
              and isinstance(n.get("a"), dict) and n["a"].get("key") == "bg"]
        assert len(bg) == 1, f"expected 1 enclosure test per site, saw {len(bg)}"
        assert bg[0]["b"] == {"type": "Lit", "value": 0.5}
