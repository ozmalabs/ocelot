"""test_arc6_lit_wire_migrated — gates for the `Lit` WIRE fix (prereg A8).

WHAT WAS BROKEN.  `Substrate.evaluate()` serialised its Term dict through
`json.dumps` (`py.rs::pyobj_to_json`), and **JSON has exactly one array
type** — so a Python `list` and a Python `tuple` inside a `Lit` both
reached `persist::decode_value` as a bare array, which decodes as
`Value::Tuple`.  Harmless while `List` and `Tuple` were one Value; under
the ARC6 value layer it silently RETYPED every Python list crossing the
Term wire.  It is the root cause of the A6/A7 episode: a control comparing
a list-typed spec against a tuple-typed spec over a bare `Lit` was
comparing a spec **with itself**, and that produced one wrong prereg
amendment and one wrong pair of diagnoses.

WHAT IS FIXED.  `py.rs::pyobj_to_json_term` preserves the Python object's
actual type at encode, using the engine's own shipped tagged form
(`__tuple__` / `__list__` / `__set__` / `__fset__`, `persist.rs`) — but
ONLY for a `Lit`'s value, and ONLY on the TERM-EVALUATION wire.

WHAT IS DELIBERATELY NOT FIXED, AND IS PINNED HERE SO IT CANNOT DRIFT.
A **bare JSON array still means `Value::Tuple`**.  Prereg A8 justifies that
with "seed files never pass through `pyobj_to_json`" — **which is false**:
`load_seed_manifest(json.load(open(seed)))` is exactly that path, and there
are 68 array-valued `Lit`s across `seeds/*.json`.  The constraint is
therefore honoured by CHANNEL, not by file:

  * a Term handed over for EVALUATION is Python-originated -> type-faithful;
  * a Term installed as GRAPH DATA (seed manifest, rule, production,
    concept, checkpoint) is the persisted wire form, where a bare array
    means `Tuple` -> untouched.

`test_lw2_*` pins the data channel and `test_lw1_*` pins the evaluation
channel, so a future "global" change that collapses the two goes RED
instead of quietly retyping every seed.

EVERY GATE PINS **BOTH DIRECTIONS**, and each carries its own CAPABILITY
control — the engine's tagged form, which resolves the list/tuple
distinction on the pre-fix binary too.  A7's standing rule is the reason:
*a control must be shown capable of detecting the difference it is used to
rule out.*  A gate that only asserted "a list arrives as a list" would pass
just as happily on a channel that had silently turned everything into a
list.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_arc6_lit_wire_migrated.py \
    --confcutdir=<this worktree> -q
"""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402


def L(v):
    return {"type": "Lit", "value": v}


def native():
    return srs.Substrate()._inner


def ev(term, env=None):
    return native().evaluate(term, env or {})


# --------------------------------------------------------------- LW1
#
# Both directions, live, on every entry point that HAS a readout. The
# `tag_*` rows are the capability control.


def test_lw1_evaluate_preserves_list_and_tuple_distinctly():
    assert type(ev(L([1, 2]))) is list, "a Python list in a Lit must arrive as Value::List"
    assert type(ev(L((1, 2)))) is tuple, "a Python tuple in a Lit must arrive as Value::Tuple"
    # CAPABILITY CONTROL: the engine's own tagged form resolves the same
    # distinction on the PRE-FIX binary, so the two rows above are a
    # reading of the wire and not of a channel that cannot express it.
    assert type(ev(L({"__list__": [1, 2]}))) is list
    assert type(ev(L({"__tuple__": [1, 2]}))) is tuple


def test_lw1_the_two_are_not_the_same_spec_which_is_the_whole_point():
    """A6's 'decisive' control was `expected-as-list` vs `expected-as-tuple`
    over a bare `Lit`, reported byte-identical. It WAS identical — because
    the wire could not express the difference. This gate fails if that ever
    becomes true again."""
    assert ev({"type": "Eq", "a": L([1, 2]), "b": L((1, 2))}) is False, (
        "a list-typed Lit and a tuple-typed Lit must be DIFFERENT specs; if "
        "this is True the wire has re-collapsed and every list/tuple control "
        "in this arc is measuring the channel again")
    assert ev({"type": "Eq", "a": L([1, 2]), "b": L([1, 2])}) is True
    assert ev({"type": "Eq", "a": L((1, 2)), "b": L((1, 2))}) is True


def test_lw1_nested_containers_keep_their_own_types():
    got = ev(L([(1, 2), [3, 4]]))
    assert type(got) is list
    assert type(got[0]) is tuple and type(got[1]) is list
    got = ev(L(((1, 2), [3, 4])))
    assert type(got) is tuple
    assert type(got[0]) is tuple and type(got[1]) is list


def test_lw1_sets_now_cross_the_wire_at_all():
    """Before the fix a Python `set` in a `Lit` was not JSON-serialisable and
    raised `TypeError`. The tagged form carries it. This is also the
    differential that proves WHICH ENCODER a path uses."""
    assert ev(L({1, 2})) == {1, 2}
    assert type(ev(L({1, 2}))) is set
    assert type(ev(L(frozenset({1, 2})))) is frozenset


def test_lw1_add_term_subgraph_preserves_both_directions():
    for value, want in (([1, 2], list), ((1, 2), tuple),
                        ({"__list__": [1, 2]}, list), ({"__tuple__": [1, 2]}, tuple)):
        n = native()
        nid = n.add_term_subgraph(L(value))
        assert type(n.node(nid)["attrs"]["value"]) is want, (value, want)


def test_lw1_search_term_wire_preserves_both_directions():
    """`search`'s `accept` gates a complete leaf, so with an EMPTY `open` the
    solution count is `1 if accept else 0`. `Eq(Lit(x), Lit((1,2)))` reads
    out whether `x` arrived as a Tuple."""
    def count(v):
        n = native()
        n.add_node("Opt", {})
        return n.search(L(()), {"type": "NodesOfType", "node_type": "Opt"},
                        "assigned", None, None,
                        {"type": "Eq", "a": L(v), "b": L((1, 2))}, None)
    assert count((1, 2)) == 1, "a tuple must still read as Value::Tuple"
    assert count([1, 2]) == 0, "a list must NOT read as Value::Tuple"
    # capability control on the same path
    assert count({"__tuple__": [1, 2]}) == 1
    assert count({"__list__": [1, 2]}) == 0


def test_lw1_structural_arrays_are_still_structural():
    """The fix must tag ONLY a `Lit`'s value. A Term's children list is a
    JSON array in STRUCTURAL position and must stay a plain array, or every
    composed Term stops parsing."""
    # `And`'s children field is `items`. Asserted in BOTH directions on
    # purpose: `children_of` returns an EMPTY Vec for a missing field, so
    # `And` of nothing is True -- a misspelled field name is a SILENT
    # NO-OP that a one-sided assertion would read as a pass. (This gate
    # caught exactly that in its own first draft.)
    assert ev({"type": "And", "items": [L(True), L(True)]}) is True
    assert ev({"type": "And", "items": [L(True), L(False)]}) is False
    assert ev({"type": "Or", "items": [L(False), L(True)]}) is True
    assert ev({"type": "Or", "items": [L(False), L(False)]}) is False


def test_lw1_unwireable_values_fail_exactly_as_before():
    """The faithful encoder delegates every leaf it does not handle to the
    untouched `pyobj_to_json`, so pre-existing failures are unchanged rather
    than silently widened."""
    import pytest
    with pytest.raises(TypeError):
        ev(L(b"ab"))
    with pytest.raises(ValueError):
        ev(L(float("nan")))
    # a huge int still degrades to a float, as it always did
    assert ev(L(2 ** 70)) == float(2 ** 70)
    # an int-keyed dict is still stringified by json.dumps' own rules
    assert ev(L({1: "a"})) == {"1": "a"}


# --------------------------------------------------------------- LW2
#
# A FILE-resident `Lit` array must still decode as `Value::Tuple`.


SEED_WITH_ARRAY_LITS = "gap_awareness.json"


def _lits(o, path=""):
    if isinstance(o, dict):
        if o.get("type") == "Lit" and isinstance(o.get("value"), (list, dict)):
            yield path, o["value"]
        for k, v in o.items():
            yield from _lits(v, path + "/" + str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            yield from _lits(v, path + "/%d" % i)


def test_lw2_a_real_seeds_bare_lit_arrays_still_decode_as_tuple():
    """End to end against a REAL seed: `json.load` -> `load_seed_manifest` ->
    `export_rules`, which re-emits every installed rule through
    `persist::encode_value` — so a `Value::Tuple` comes back tagged
    `__tuple__` and a `Value::List` comes back tagged `__list__`. That
    readout distinguishes the two by construction, which is this gate's
    capability control."""
    path = os.path.join(ROOT, "seeds", SEED_WITH_ARRAY_LITS)
    manifest = json.load(open(path))
    in_file = [v for _p, v in _lits(manifest) if isinstance(v, list)]
    assert in_file, "fixture drift: %s no longer holds an array-valued Lit" % path

    n = native()
    n.load_seed_manifest(manifest, None)
    exported = n.export_rules()

    tags = {"__tuple__": 0, "__list__": 0, "bare": 0}
    for _p, v in _lits(exported):
        if isinstance(v, dict):
            for t in ("__tuple__", "__list__"):
                if t in v:
                    tags[t] += 1
        elif isinstance(v, list):
            tags["bare"] += 1
    assert tags["__tuple__"] > 0, ("no seed-resident array Lit survived to the "
                                   "export; the readout is blind: %r" % tags)
    assert tags["__list__"] == 0, (
        "a FILE-resident bare `Lit` array decoded as Value::List (%r). Every "
        "seed-resident array literal has just changed meaning — this is the "
        "blast radius A8's LW2 forbids." % tags)


def test_lw2_the_data_channel_is_still_the_legacy_encoder():
    """Pins the CHANNEL SEPARATION directly, not just its effect on one seed:
    the same bare array is a `Tuple` through `load_seed_manifest` and a
    `List` through `evaluate`. If a later change makes the data channel
    type-faithful too, this goes red and the 68 seed-resident array Lits do
    not silently retype."""
    manifest = {
        "id": "lw2_channel_probe",
        "rules": [{
            "name": "lw2_probe_rule",
            "match": [["agent", "knows", "m"]],
            "where": {"type": "In", "member": {"type": "Lit", "value": "a"},
                      "container": {"type": "Lit", "value": ["a", "b"]}},
            "then": [],
        }],
    }
    n = native()
    n.load_seed_manifest(manifest, None)
    blob = json.dumps(n.export_rules())
    assert '"__tuple__"' in blob, (
        "a bare array installed as GRAPH DATA must still be a Value::Tuple; "
        "got: %s" % blob[:400])
    assert '"__list__"' not in blob, blob[:400]
    # ...and the SAME literal is a list on the evaluation channel.
    assert type(ev(L(["a", "b"]))) is list


# --------------------------------------------------------------- LW3
#
# `_wire_rows` is now redundant. PROVED, not assumed — and NOT deleted.


def test_lw3_wire_rows_is_now_redundant_but_still_present():
    from domains.prog_synthesis import _wire_rows

    rows = [
        {"inputs": {"a": [1, 2, 3], "b": (4, 5)}, "output": [1, 3]},
        {"inputs": {"a": (1, 2), "b": [3]}, "output": (7,)},
        {"inputs": {"a": "abc"}, "output": {1, 2}, "unordered": True},
        {"inputs": {"a": [[1, 2], (3, 4)]}, "output": frozenset({9})},
    ]
    n = native()
    plain = n.evaluate(L(rows), None)
    wired = n.evaluate(L(_wire_rows(rows)), None)
    assert repr(plain) == repr(wired), (plain, wired)
    assert type(plain) is type(wired)
    # The capability control: this comparison DID separate the two paths on
    # the pre-fix engine (196 of 420 MBPP specs differed), so "equal" here
    # is a measurement and not a blind comparison. The nested types below
    # are what it resolves.
    assert type(plain[0]["inputs"]["a"]) is list
    assert type(plain[0]["inputs"]["b"]) is tuple
    assert type(plain[0]["output"]) is list
    assert type(plain[1]["output"]) is tuple
    assert type(plain[2]["output"]) is set
    assert type(plain[3]["output"]) is frozenset


def test_lw3_wire_rows_is_not_deleted_in_this_rung():
    """A8: prove redundancy first, remove later. If the symbol vanishes the
    production callers (`run_enumerate`, `_branch_arm_term`,
    `prog_moves._run_synth_enumerate`) have been rewired by something that
    did not run this gate."""
    from domains import prog_synthesis
    assert callable(getattr(prog_synthesis, "_wire_rows", None))
    assert callable(getattr(prog_synthesis, "_wire", None))
