"""§13 AUDIT — no hand-set threshold entered with the competitive-ownership gate.

`VISION_FIGADJ_REPLACEMENT_PREREG.md`, arm 4.

The value-flood rung established the incumbent's literal inventory by an AST walk
over every rule's term tree (`VISION_VALUE_FLOOD_RESULTS.md` §3a): eighteen `0.5`
literals, every one a boolean discriminator over a 0/1 flag (`bown`, `bg`,
`frame`, `owns`), plus one `2` against `Count(roots)` in `bo_mint_gestalt` — the
definition of a bipartition. **No literal was ever compared against `val`.**

This file re-runs that audit on v1.1.0 and asserts the replacement did not
smuggle a constant in. The claim under test is precise: the new gate compares two
MEASURED COUNTS (`R.rim` vs `n.rim`) and its tie is EQUALITY, so §13 is satisfied
by construction rather than by deriving a magic number.

It is a TERM-TREE WALK, never a substring selector — substring selectors have
failed four times in this arc, twice going red on their own docstrings. Nothing
here reads the file as text.
"""
import json
import os

from domains.engine_provenance import engine_preamble

engine_preamble()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "vision_border_ownership.json")

COMPARISONS = {"Eq", "Lt", "Lte", "Gt", "Gte"}

# Attributes that are 0/1 FLAGS. A literal compared against one of these is a
# boolean discriminator, not a threshold.
FLAG_KEYS = {"bown", "bown_own", "bown_wp", "bown_nest", "bg", "frame", "owns"}

# Attributes carrying OBSERVED or MEASURED magnitudes. A literal compared against
# any of these WOULD be a hand-set threshold, and there must be none.
MAGNITUDE_KEYS = {"val", "rim", "glabel", "cid", "members", "root"}


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


def _walk(term, path=()):
    """Yield (path, node) for every dict node in a term tree."""
    if isinstance(term, dict):
        yield path, term
        for k, v in term.items():
            yield from _walk(v, path + (k,))
    elif isinstance(term, list):
        for i, v in enumerate(term):
            yield from _walk(v, path + (i,))


def _rule_trees(seed):
    """Every term tree a rule evaluates: its `where` and every effect value."""
    for rule in seed["rules"]:
        yield rule["name"], "where", rule.get("where", {})
        for i, eff in enumerate(rule.get("effects", [])):
            for part in eff:
                if isinstance(part, dict):
                    for key, val in part.items():
                        if isinstance(val, dict) and "__term__" in val:
                            yield rule["name"], f"effect[{i}].{key}", val["__term__"]


def _describe(operand):
    """What KIND of thing is this side of a comparison?"""
    t = operand.get("type") if isinstance(operand, dict) else None
    if t == "Lit":
        return ("Lit", operand.get("value"))
    if t == "Attr":
        return ("Attr", operand.get("key"))
    return (t, None)


def _comparisons(seed):
    out = []
    for rname, where, tree in _rule_trees(seed):
        for path, node in _walk(tree):
            if node.get("type") in COMPARISONS and "a" in node and "b" in node:
                out.append({"rule": rname, "site": where, "path": list(path),
                            "op": node["type"],
                            "a": _describe(node["a"]),
                            "b": _describe(node["b"])})
    return out


def test_seed_is_current_version_with_both_predicates_present():
    seed = _seed()
    assert seed["version"] == "1.3.0"
    names = [r["name"] for r in seed["rules"]]
    assert "bo_mint_enclosed" in names          # the incumbent, retained
    assert "bo_mint_owned" in names             # the replacement
    assert "bo_rim" in names                    # perim, materialised


def test_EVERY_literal_in_a_comparison_is_a_boolean_flag_discriminator():
    """The headline §13 assertion. Every `Lit` that appears in a comparison must
    be compared against a 0/1 FLAG — never against an observed or measured
    magnitude."""
    offenders = []
    for c in _comparisons(_seed()):
        for lit_side, other in ((c["a"], c["b"]), (c["b"], c["a"])):
            if lit_side[0] != "Lit":
                continue
            if other[0] == "Attr" and other[1] in FLAG_KEYS:
                continue                                   # boolean discriminator
            if other[0] == "Count" and lit_side[1] == 2:
                continue      # bo_mint_gestalt: the DEFINITION of a bipartition
            offenders.append(c)
    assert not offenders, (
        "literal compared against something other than a 0/1 flag — a hand-set "
        f"threshold entered the seed: {json.dumps(offenders, indent=1)}")


def test_NO_literal_is_compared_against_an_observed_or_measured_magnitude():
    """Stated the other way round, so the two assertions cannot both be
    satisfied by a hole in one of them."""
    bad = []
    for c in _comparisons(_seed()):
        for lit_side, other in ((c["a"], c["b"]), (c["b"], c["a"])):
            if lit_side[0] == "Lit" and other[0] == "Attr" \
                    and other[1] in MAGNITUDE_KEYS:
                bad.append(c)
    assert not bad, (
        "a literal is compared against a magnitude — this is exactly the §13 "
        f"failure the audit exists to catch: {json.dumps(bad, indent=1)}")


def test_the_literal_INVENTORY_is_unchanged_in_KIND_from_the_incumbent():
    """The value-flood rung found exactly two kinds: `0.5` against a flag, and
    one `2` against `Count(roots)`. v1.1.0 must add no third kind."""
    kinds = set()
    for c in _comparisons(_seed()):
        for lit_side, other in ((c["a"], c["b"]), (c["b"], c["a"])):
            if lit_side[0] == "Lit":
                kinds.add((lit_side[1], other[0], other[1]))
    unexpected = {k for k in kinds
                  if not (k[0] == 0.5 and k[1] == "Attr" and k[2] in FLAG_KEYS)
                  and not (k[0] == 2 and k[1] == "Count")}
    assert not unexpected, f"new literal KIND introduced: {sorted(unexpected)}"


def test_the_OWNERSHIP_comparison_is_count_vs_count_with_no_literal():
    """The replacement's decisive comparison, located structurally: an `Lt`
    between `R.rim` and `n.rim`. Both sides are Attrs holding MEASURED counts;
    neither is a Lit. The tie (equality) is what holds a border open."""
    owned = [r for r in _seed()["rules"] if r["name"] == "bo_mint_owned"]
    assert len(owned) == 1
    rim_cmps = [n for _, n in _walk(owned[0]["where"])
                if n.get("type") == "Lt"
                and _describe(n.get("a", {})) == ("Attr", "rim")
                and _describe(n.get("b", {})) == ("Attr", "rim")]
    assert len(rim_cmps) == 1, (
        f"expected exactly ONE rim-vs-rim comparison, found {len(rim_cmps)}")
    cmp_ = rim_cmps[0]
    assert cmp_["a"]["node"]["name"] == "R"      # this component
    assert cmp_["b"]["node"]["name"] == "n"      # the abutting component's cell
    # and it is NEGATED: R is refused when it does NOT strictly win.
    parents = [n for _, n in _walk(owned[0]["where"])
               if n.get("type") == "Not" and n.get("arg") is cmp_]
    assert len(parents) == 1, "the rim comparison must sit under exactly one Not"


def test_rim_itself_is_a_COUNT_and_carries_no_literal_bound():
    """`bo_rim` must compute a Count over a Filter — a measured contour length —
    and must not compare that count against any constant."""
    rim = [r for r in _seed()["rules"] if r["name"] == "bo_rim"]
    assert len(rim) == 1
    counts = [n for _, n in _walk(rim[0]) if n.get("type") == "Count"]
    assert counts, "bo_rim computes no Count"
    for c in _comparisons({"rules": rim}):
        for lit_side, other in ((c["a"], c["b"]), (c["b"], c["a"])):
            assert not (lit_side[0] == "Lit" and other[0] == "Count"), (
                f"bo_rim bounds its own count by a literal: {c}")


def test_incumbent_gate_still_present_and_still_the_isolation_test():
    """The replacement ADDS a predicate; it does not delete the incumbent. The
    incumbent must remain available and unchanged so the A/B is within-substrate
    (the prior rung's simulation was validated under the incumbent ONLY, so it
    cannot score the replacement — the substrate must run both)."""
    inc = [r for r in _seed()["rules"] if r["name"] == "bo_mint_enclosed"][0]
    rim_refs = [n for _, n in _walk(inc["where"])
                if _describe(n) == ("Attr", "rim")]
    assert not rim_refs, "the incumbent predicate must not read `rim`"
    guards = [n for _, n in _walk(inc["where"])
              if n.get("type") == "Lt"
              and _describe(n.get("a", {})) == ("Attr", "bown_own")]
    assert len(guards) == 1, "incumbent must be OFF when the replacement is armed"
