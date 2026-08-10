"""test_synth_enumerate_migrated — P4-A gates for the `SynthEnumerate` Term
(the Rust port of domains/generator.py::synthesize, unguided path).

Gates (PROGRAM_SYNTHESIS_PLAN.md §4-P4; the task's parity contract):

  PARITY vs generator.py — on generator.py's OWN exercised specs
    (scripts/generator.py's demo battery: x*x+1, max(a,b), a*b+c,
    |x−2|), SynthEnumerate must find the SAME term as the Python
    synthesize (or an observationally-equal one of the same size).
    Because the port reproduces the enumeration ORDER (vars in
    first-appearance order — identical here since the spec dicts are
    alphabetically keyed — then consts; ops in DEFAULT_OPS order;
    same size partitions; same register order), the gate asserts
    EXACT term_str parity plus counter parity
    (explored == tested, distinct == distinct), with the
    observational-equality fallback kept as the documented weaker
    bound.
  BUDGET HONESTY — max_candidates (a COUNT — generator.py's timeout_s
    has no Rust twin; wall clocks are not in-frame integers) exhausts
    to found:false / halt_reason:"budget" / tested == budget, never an
    exception, never a fabricated term.
  REFLECT ROUND-TRIP — the returned Term-JSON is directly usable graph
    data: add_term_subgraph → term_subgraph_json is canonical-identical
    and idempotent, and the reflected term still evaluates correctly.
  DETERMINISM — same inputs → same full result dict (term bytes
    included), across fresh substrates.

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest tests/test_synth_enumerate_migrated.py \
    --confcutdir=. -q
"""

from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs

from domains.generator import synthesize, DEFAULT_OPS


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------

def SYNTH(examples, ops=None, consts=None, exclude=None, max_size=0, max_candidates=0,
          saturate_k=0, field=""):
    """Term-JSON for a SynthEnumerate call (mirrors substrate/dsl.py)."""
    return {
        "type": "SynthEnumerate",
        "examples": {"type": "Lit", "value": examples},
        "ops": {"type": "Lit", "value": list(ops)} if ops is not None else None,
        "consts": {"type": "Lit", "value": list(consts)} if consts is not None else None,
        "exclude": {"type": "Lit", "value": list(exclude)} if exclude is not None else None,
        "max_size": max_size,
        "max_candidates": max_candidates,
        "saturate_k": saturate_k,
        "field": field,
    }


def rows(examples):
    """generator.py's spec [(env, out), ...] → SynthEnumerate rows.

    ARC6 PRUNING FIX (2026-08-03) — THE SPEC WIRE MUST CARRY THE SPEC'S
    TYPES.  `Substrate.evaluate()` serialises its Term dict through JSON,
    and JSON has ONE array type, so a Python `list` and a Python `tuple`
    inside a `Lit` both decode as `Value::Tuple`.  Harmless while list and
    tuple were one Value; under the ARC6 value layer it silently retypes
    every list-valued expected output as a TUPLE, and the search is then
    asked for something the correct list-producing candidate cannot make.
    `domains.prog_synthesis._wire_rows` is the shipped write side of the
    engine's own tagged form (`persist.rs`), already used by every
    production caller.  Scalar/string specs are byte-unchanged by it, and
    a bare `Lit` array still means `Tuple`."""
    from domains.prog_synthesis import _wire_rows
    return _wire_rows([{"inputs": dict(env), "output": out}
                       for env, out in examples])


def _synth_enumerate_live() -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(SYNTH([]), {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _synth_enumerate_live():
    pytest.skip(
        "SynthEnumerate Term not present in the installed substrate_rs binary — "
        "rebuild runners/dsl (cargo build --release + sync "
        "python/substrate_rs/_native.abi3.so). Honest skip, not a fake pass.",
        allow_module_level=True)


@pytest.fixture()
def sub():
    return srs.Substrate()


def run_synth(sub, examples, **kw):
    out = sub._inner.evaluate(SYNTH(rows(examples), **kw), {})
    assert isinstance(out, dict), f"SynthEnumerate must return a Dict, got {type(out)}"
    return out


def norm_num(v):
    """Fold engine outputs to a comparable number (bool → 1/0)."""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    return float(v)


# ---------------------------------------------------------------------------
# generator.py's OWN exercised specs (scripts/generator.py's demo battery),
# verbatim: (name, true_fn, train_envs, heldout_envs, max_size).
# ---------------------------------------------------------------------------

GENERATOR_PY_SPECS = [
    (
        "f(x) = x*x + 1",
        lambda x: x * x + 1,
        [{"x": v} for v in (0, 1, 2, 3, 4)],
        [{"x": v} for v in (5, 7, 10, -3, 12)],
        7,
    ),
    (
        "f(a,b) = max(a,b)",
        lambda a, b: max(a, b),
        [{"a": a, "b": b} for (a, b) in [(1, 2), (5, 3), (0, 0), (7, 9), (4, 1), (2, 8)]],
        [{"a": a, "b": b} for (a, b) in [(11, 4), (3, 30), (-5, -2), (100, 99)]],
        7,
    ),
    (
        "f(a,b,c) = a*b + c",
        lambda a, b, c: a * b + c,
        [{"a": a, "b": b, "c": c} for (a, b, c) in
         [(1, 2, 3), (2, 3, 1), (0, 5, 4), (3, 3, 0), (2, 2, 2), (4, 1, 5)]],
        [{"a": a, "b": b, "c": c} for (a, b, c) in
         [(5, 5, 5), (7, 2, 1), (10, 0, 3), (6, 6, 6)]],
        7,
    ),
    (
        "f(x) = |x - 2|",
        lambda x: abs(x - 2),
        [{"x": v} for v in (-3, -1, 0, 1, 2, 3, 5)],
        [{"x": v} for v in (10, -8, 6, 2, -20)],
        7,
    ),
]


@pytest.mark.parametrize(
    "name,true_fn,train,heldout,max_size",
    GENERATOR_PY_SPECS,
    ids=[s[0] for s in GENERATOR_PY_SPECS],
)
def test_parity_with_generator_py(sub, name, true_fn, train, heldout, max_size):
    """The parity gate: SynthEnumerate finds the SAME term as
    generator.py's synthesize on generator.py's own specs — exact
    term_str + size + enumeration counters (the port reproduces the
    order, so the counters are part of the claim); observational
    equality on train AND held-out inputs closes the loop."""
    examples = [(env, true_fn(**env)) for env in train]

    r_py = synthesize(sub, examples, ops=DEFAULT_OPS, max_size=max_size,
                      timeout_s=60.0)
    assert r_py is not None and r_py["fits"], f"generator.py failed on {name}"

    out = run_synth(sub, examples, max_size=max_size)
    assert out["found"] is True, f"SynthEnumerate failed on {name}: {out}"

    # Same size (the MDL claim) — a same-size observational equal would
    # be admissible per the contract, but the faithful order gives the
    # exact same term; assert the strong form and keep the weak one too.
    assert out["size"] == r_py["size"], (name, out["size"], r_py["size"])
    assert out["term_str"] == r_py["term_str"], (name, out["term_str"], r_py["term_str"])
    # Enumeration parity: same candidates tested, same distinct
    # behaviours committed.
    assert out["tested"] == r_py["explored"], (name, out["tested"], r_py["explored"])
    assert out["distinct"] == r_py["distinct"], (name, out["distinct"], r_py["distinct"])

    # Observational equality on train + held-out inputs (the weaker
    # bound the contract names, asserted on top).
    term = json.loads(out["term"])
    for env in list(train) + list(heldout):
        got = norm_num(sub._inner.evaluate(term, env))
        want_py = norm_num(r_py["term"].evaluate(env, sub))
        assert got == pytest.approx(want_py, abs=1e-9), (name, env, got, want_py)
        assert got == pytest.approx(float(true_fn(**env)), abs=1e-9), (name, env, got)


def test_op_inventory_is_the_callers(sub):
    """The held-Terms discipline: the caller's op list bounds what may
    compose. A Plus-only inventory must express doubling as (x + x); a
    Times-only inventory as (x * 2)."""
    examples = [({"x": 1}, 2), ({"x": 2}, 4), ({"x": 3}, 6)]
    out_plus = run_synth(sub, examples, ops=["Plus"], max_size=7)
    assert out_plus["found"] is True
    assert out_plus["term_str"] == "(x + x)"
    out_times = run_synth(sub, examples, ops=["Times"], max_size=7)
    assert out_times["found"] is True
    assert out_times["term_str"] == "(x * 2)"
    assert '"Plus"' not in out_times["term"]


def test_budget_honesty(sub):
    """max_candidates is a COUNT budget: exhaustion → found:false,
    halt_reason:'budget', tested == budget — honest counters, never an
    exception, never a term."""
    examples = [({"x": 0}, 1), ({"x": 1}, 2), ({"x": 2}, 3)]
    out = run_synth(sub, examples, max_size=7, max_candidates=3)
    assert out["found"] is False
    assert out["halt_reason"] == "budget"
    assert out["tested"] == 3
    assert out["term"] is None
    assert out["size"] is None
    assert out["saturated"] is False
    # The same spec under an adequate budget solves — the budget was
    # the only thing in the way.
    ok = run_synth(sub, examples, max_size=7)
    assert ok["found"] is True and ok["halt_reason"] == "solved"


def test_saturation_honesty(sub):
    """A closed op inventory that mints no new behaviours halts as
    'saturated' with found:false — the early-stop is honest, not a
    silent max_size walk."""
    examples = [({"x": 1}, 2.5), ({"x": 2}, 2.5)]  # unreachable target
    out = run_synth(sub, examples, ops=["Abs"], max_size=9)
    assert out["found"] is False
    assert out["saturated"] is True
    assert out["halt_reason"] == "saturated"


def test_returned_term_reflect_round_trip(sub):
    """The returned Term-JSON is graph data: add_term_subgraph →
    term_subgraph_json canonical round-trip is idempotent, and the
    reflected term still computes the spec."""
    examples = [({"x": 0}, 1), ({"x": 1}, 2), ({"x": 2}, 3)]
    out = run_synth(sub, examples, max_size=7)
    assert out["found"] is True
    term = json.loads(out["term"])

    nid = sub._inner.add_term_subgraph(term)
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    nid2 = sub._inner.add_term_subgraph(c1)
    c2 = json.loads(sub._inner.term_subgraph_json(nid2))
    assert c1 == c2, "reflect round-trip must be idempotent"
    assert norm_num(sub._inner.evaluate(c1, {"x": 41})) == 42.0


def test_synth_enumerate_term_itself_reflects(sub):
    """The per-variant reflect law for the NEW variant: a SynthEnumerate
    term round-trips through the subgraph reflection canonically."""
    sample = SYNTH([{"inputs": {"x": 1}, "output": 2}], ops=["Plus"],
                   max_size=5, max_candidates=100, saturate_k=2, field="found")
    nid = sub._inner.add_term_subgraph(sample)
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    assert c1["type"] == "SynthEnumerate"
    nid2 = sub._inner.add_term_subgraph(c1)
    c2 = json.loads(sub._inner.term_subgraph_json(nid2))
    assert c1 == c2, "reflect round-trip must be idempotent"
    # The reflected term still RUNS (field selector engaged).
    assert sub._inner.evaluate(c1, {}) is True


def test_determinism_same_inputs_same_term(sub):
    """Same inputs → byte-identical result (term JSON included), across
    fresh substrates — no wall clock, no randomness anywhere."""
    examples = [({"a": a, "b": b, "c": c}, a * b + c) for (a, b, c) in
                [(1, 2, 3), (2, 3, 1), (0, 5, 4), (3, 3, 0), (2, 2, 2), (4, 1, 5)]]
    out1 = run_synth(sub, examples, max_size=7)
    out2 = run_synth(srs.Substrate(), examples, max_size=7)
    assert out1 == out2
    assert out1["found"] is True


def test_invalid_examples_are_honest(sub):
    """A malformed spec is an honest found:false / 'invalid_examples',
    never an exception (generator.py would raise — registered
    divergence: a graph-resident primitive must return)."""
    out = sub._inner.evaluate(
        SYNTH([{"inputs": {"x": 1}}]), {})  # row without output
    assert out["found"] is False
    assert out["halt_reason"] == "invalid_examples"
    out = sub._inner.evaluate(
        {"type": "SynthEnumerate", "examples": {"type": "Lit", "value": 5},
         "ops": None, "consts": None, "max_size": 0, "max_candidates": 0,
         "saturate_k": 0, "field": ""}, {})
    assert out["halt_reason"] == "invalid_examples"


# ---------------------------------------------------------------------------
# Q1 (PROGRAM_SYNTHESIS_ARC2_PLAN.md §2-Q1) — value-domain widening +
# the `exclude` parameter.
# ---------------------------------------------------------------------------

def test_string_output_spec_is_no_longer_invalid(sub):
    """The arc-1 floor: a non-numeric spec output was `invalid_examples`.
    Q1 widens the target domain — str is now a valid spec output."""
    examples = [({"x": "ab"}, "ab")]  # trivial identity, just checks acceptance
    out = run_synth(sub, examples, ops=["Eq"], max_size=3)
    assert out["halt_reason"] != "invalid_examples"


def test_str_spec_finds_a_string_method_compose(sub):
    """Typed enumeration: a spec whose every variable AND output is
    string-shaped, with NO caller-declared `ops`, composes over the
    TYPED default inventory (Concat/CaseFold/Eq/IfThenElse) instead of
    arithmetic DEFAULT_OPS — 'a str spec never enumerates BitAnd'."""
    # f(x) = lower(x) -- CaseFold is the only op that can possibly reach
    # this behaviour; DEFAULT_OPS (arithmetic) cannot express it at all.
    examples = [
        ({"x": "AB"}, "ab"),
        ({"x": "CD"}, "cd"),
        ({"x": "ef"}, "ef"),
    ]
    out = run_synth(sub, examples, max_size=5)  # no explicit ops
    assert out["found"] is True, out
    assert out["term_str"] == "lower(x)"
    parsed = json.loads(out["term"])
    assert parsed["type"] == "CaseFold"


def test_str_spec_composes_concat(sub):
    """f(x) = x + '!' -- Concat is the typed default's binary op; the
    trailing '!' const must come from the spec-derived string consts
    (a literal observed in some row's output), never a global alphabet."""
    examples = [
        ({"x": "hi"}, "hi!"),
        ({"x": "yo"}, "yo!"),
    ]
    out = run_synth(sub, examples, max_size=5)
    assert out["found"] is True, out
    assert out["term_str"] == "(x + '!')"


def test_explicit_ops_overrides_the_typed_default(sub):
    """An explicit `ops` ALWAYS wins over the string-shaped default —
    even for a string spec."""
    examples = [({"x": "ab"}, "ab")]
    out = run_synth(sub, examples, ops=["Eq"], max_size=3)
    assert out["found"] is True
    assert out["term_str"] == "(x == x)" or out["term_str"] == "x"
    # Whichever the search finds first, the term JSON must never
    # contain a Concat/CaseFold when they weren't declared.
    js = out["term"]
    assert "StringConcat" not in js and "CaseFold" not in js


def test_exclude_prunes_an_already_refuted_candidate(sub):
    """The P7-B repair lever: excluding the FIRST-found term makes the
    search skip straight past it to the NEXT distinct solving term (or
    fail honestly if none exists within budget)."""
    examples = [({"x": 1}, 2), ({"x": 2}, 4), ({"x": 3}, 6)]
    first = run_synth(sub, examples, ops=["Plus", "Times"], max_size=7)
    assert first["found"] is True
    out = sub._inner.evaluate(
        SYNTH(rows(examples), ops=["Plus", "Times"], exclude=[first["term"]],
              max_size=7),
        {})
    if out["found"]:
        assert out["term_str"] != first["term_str"], (
            "excluded term must not be re-proposed")
        # And the excluded behaviour is truly gone: evaluating the
        # excluded term against the same spec would ALSO solve it
        # (it's a real solution, just refuted) -- prove that, so the
        # test isn't vacuous.
        excl_term = json.loads(first["term"])
        for env, y in examples:
            got = sub._inner.evaluate(excl_term, env)
            assert got == y
    else:
        # Honest: an over-narrow op inventory can exhaust with nothing
        # else observationally distinct to offer -- acceptable as long
        # as it's not simply re-finding the excluded term.
        assert out["halt_reason"] in ("saturated", "max_size", "budget")


def test_exclude_blocks_const_resurrection(sub):
    """The exact P7-B gap this closes: excluding a bare CONSTANT must
    stop it from being silently reintroduced by the auto-appended-
    consts step (every integer-valued output is auto-appended as a
    leaf) -- proven by excluding the constant output of a
    single-row spec whose only possible size-1 solution IS that
    constant, then checking the engine does not re-propose it as a
    same-behaviour leaf."""
    examples = [({"x": 0}, 5), ({"x": 1}, 5)]  # f(x) = 5, a constant function
    first = run_synth(sub, examples, ops=["Plus"], max_size=3)
    assert first["found"] is True
    assert first["term_str"] == "5"  # the constant leaf itself
    out = sub._inner.evaluate(
        SYNTH(rows(examples), ops=["Plus"], exclude=[first["term"]], max_size=3),
        {})
    # The constant is excluded; no OTHER term of this tiny op inventory
    # produces the same constant behaviour differently within size 3 —
    # so the search must NOT find "5" again under any guise.
    if out["found"]:
        assert out["term_str"] != "5"
    else:
        assert out["halt_reason"] in ("saturated", "max_size", "budget")


def test_malformed_exclude_entry_is_skipped_not_fatal(sub):
    """An exclude entry that references an unknown variable, or isn't
    valid JSON, or isn't in this call's own op table, is SKIPPED —
    `exclude` is a soft refutation hint, never part of the spec
    contract that can crash a call."""
    examples = [({"x": 1}, 2), ({"x": 2}, 4)]
    bad_entries = [
        "not valid json {{{",
        json.dumps({"type": "Var", "name": "nonexistent_var_zzq"}),
        json.dumps({"type": "Lambda", "body": None}),  # unknown op (outside OP_TABLE)
        json.dumps({"type": "Plus"}),  # missing required "items" field
    ]
    out = sub._inner.evaluate(
        SYNTH(rows(examples), ops=["Plus", "Times"], exclude=bad_entries, max_size=7),
        {})
    assert out["found"] is True, "malformed exclude entries must not break the search"
    assert out["halt_reason"] == "solved"


def test_exclude_empty_list_is_a_no_op(sub):
    examples = [({"x": 0}, 1), ({"x": 1}, 2), ({"x": 2}, 3)]
    baseline = run_synth(sub, examples, max_size=7)
    out = sub._inner.evaluate(SYNTH(rows(examples), exclude=[], max_size=7), {})
    assert out["found"] == baseline["found"]
    assert out["term_str"] == baseline["term_str"]
    assert out["tested"] == baseline["tested"]


def test_synth_enumerate_exclude_field_reflects(sub):
    """The `exclude` field round-trips through subgraph reflection like
    every other field (the per-variant reflect law)."""
    sample = SYNTH([{"inputs": {"x": 1}, "output": 2}], ops=["Plus"],
                   exclude=[json.dumps({"type": "Var", "name": "x"})],
                   max_size=5, field="found")
    nid = sub._inner.add_term_subgraph(sample)
    c1 = json.loads(sub._inner.term_subgraph_json(nid))
    assert c1["type"] == "SynthEnumerate"
    assert c1["exclude"] is not None
    nid2 = sub._inner.add_term_subgraph(c1)
    c2 = json.loads(sub._inner.term_subgraph_json(nid2))
    assert c1 == c2, "reflect round-trip must be idempotent"


# ---------------------------------------------------------------------------
# Arc4-S4: list/iteration composition (search reach). See
# PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md for the diagnosis + reach measurement
# this widening is sized against; these are the Python-facing (pyo3
# boundary) parity/contract gates for the same engine change already
# covered at the Rust unit level in runners/dsl/src/synth_enumerate.rs.
# ---------------------------------------------------------------------------

def test_list_len_via_python_boundary(sub):
    """`Len` reaches through the SAME pyo3 `evaluate()` boundary
    `domains.prog_synthesis.run_enumerate` uses — a Python list argument
    (JSON array on the wire) round-trips to a list-shaped spec var."""
    examples = [({"xs": [1, 2, 3]}, 3), ({"xs": [4, 5]}, 2), ({"xs": []}, 0)]
    out = run_synth(sub, examples, ops=["Len"], max_size=9)
    assert out["found"] is True, out
    assert out["term_str"] == "len(xs)"


def test_list_sum_via_python_boundary(sub):
    examples = [({"xs": [1, 2, 3]}, 6), ({"xs": [4, 5]}, 9), ({"xs": []}, 0)]
    out = run_synth(sub, examples, ops=["SumList"], max_size=9)
    assert out["found"] is True, out


def test_list_filter_and_len_composes_count_positives(sub):
    """The exact shape of MBPP task 66 ('count the number of positive
    numbers in a list'): Len(FilterList(xs, item, item > -1))."""
    examples = [
        ({"xs": [1, -2, 3, -4]}, 2),
        ({"xs": [-1, -2]}, 0),
        ({"xs": [5, 6, 7]}, 3),
    ]
    out = run_synth(sub, examples, ops=["Len", "FilterList"], max_size=9)
    assert out["found"] is True, out
    term = json.loads(out["term"])
    for env, y in examples:
        assert sub._inner.evaluate(term, env) == y


def test_list_max_minus_min_composes_with_existing_arithmetic(sub):
    """A list-reduction's SCALAR output composes further with a
    PRE-EXISTING arithmetic op (task 145's shape: max - min)."""
    examples = [
        ({"xs": [3, 1, 9, 2]}, 8),
        ({"xs": [5, 5]}, 0),
        ({"xs": [-2, 4, 1]}, 6),
    ]
    out = run_synth(sub, examples, ops=["MaxList", "MinList", "Minus"], max_size=9)
    assert out["found"] is True, out


def test_list_map_extracts_per_element(sub):
    """task 460's shape: first element of each sublist, via MapList +
    the IndexAt(item, 0) template.

    2026-08-03 (arc6 pruning fix): the winning term's SHAPE is asserted,
    not just `found`.  This gate went red after the value layer and was
    registered as a GENERATION regression ("never enumerated at any
    budget").  Measured, it is neither: the term is enumerated in 25
    candidates, and the red was the LOSSY SPEC WIRE retyping this spec's
    list-valued expected output to a tuple, which `MapList` (correctly, a
    Python list comprehension is a list) cannot produce.  With the spec's
    own type delivered intact it solves at tested=25, distinct=17 -- the
    arm-A figures exactly."""
    examples = [
        ({"lists": [[1, 2], [3, 4]]}, [1, 3]),
        ({"lists": [[9], [7, 8, 9]]}, [9, 7]),
    ]
    out = run_synth(sub, examples, ops=["MapList"], max_size=9)
    assert out["found"] is True, out
    # FX2: the CORRECT term, not merely A term. MapList over IndexAt(_,0).
    term = json.loads(out["term"])
    assert term["type"] == "MapList", term
    assert term["value"]["type"] == "IndexAt", term
    assert term["value"]["index"] == {"type": "Lit", "value": 0}, term
    assert term["source"] == {"type": "Var", "name": "lists"}, term


def test_tuple_typed_variant_of_the_map_spec_is_refused(sub):
    """THE REFUTING DIRECTION of the gate above, and the reason it was
    re-pinned rather than widened: byte-identical rows with a TUPLE-typed
    expected output are NOT solved, because a list comprehension does not
    build a tuple.  Before the ARC6 value layer these two specs were
    indistinguishable; if a later change re-collapses list and tuple in
    the spec-target relation, this goes red."""
    examples = [
        ({"lists": [[1, 2], [3, 4]]}, (1, 3)),
        ({"lists": [[9], [7, 8, 9]]}, (9, 7)),
    ]
    out = run_synth(sub, examples, ops=["MapList"], max_size=9)
    assert out["found"] is False, out["term_str"]


def test_list_shaped_default_ops_reach_without_explicit_ops(sub):
    """The third typed default (`spec_is_list_shaped`): a list-valued
    spec with NO explicit `ops` still reaches a list op — parity with
    the string-shaped default's own established behaviour."""
    examples = [({"xs": [1, 2, 3]}, 3), ({"xs": [4, 5]}, 2), ({"xs": []}, 0)]
    out = run_synth(sub, examples, max_size=9)  # no explicit ops
    assert out["found"] is True, out


def test_non_list_spec_is_byte_unchanged_by_the_widening(sub):
    """Parity gate: a plain scalar spec's default search is UNCHANGED —
    same term, same size, same tested count as before this widening
    (the arc-1 generator.py parity case, re-asserted standalone)."""
    examples = [({"x": 0}, 1), ({"x": 1}, 2), ({"x": 2}, 3)]
    out = run_synth(sub, examples, max_size=7)
    assert out["found"] is True
    assert out["term_str"] == "(x + 1)"
    assert out["size"] == 3


def test_typed_pruning_list_ops_over_scalar_spec_find_nothing(sub):
    """A scalar-only spec explicitly requesting list ops must find
    NOTHING to draw on (typed pruning: list ops only ever see
    `list_by_size`, which stays empty for a scalar spec) — honest
    halt, never a panic, never a spurious find."""
    examples = [({"x": 1}, 2), ({"x": 2}, 4), ({"x": 3}, 6)]
    out = run_synth(sub, examples, ops=["Len", "SumList", "FilterList", "MapList"],
                    max_size=9)
    assert out["found"] is False
    assert out["halt_reason"] in ("saturated", "max_size")


def test_list_op_term_evaluates_after_json_round_trip(sub):
    """The exact contract `domains.prog_synthesis.run_enumerate` relies
    on: `json.loads(out['term'])` is a plain dict usable directly as a
    Term-JSON node (e.g. nested in a ProgReturn), and evaluates
    correctly when re-driven through `sub._inner.evaluate`."""
    examples = [({"xs": [1, 2, 3]}, 3), ({"xs": [4, 5]}, 2), ({"xs": []}, 0)]
    out = run_synth(sub, examples, ops=["Len"], max_size=9)
    assert out["found"] is True
    term = json.loads(out["term"])
    assert term["type"] == "Count"
    assert sub._inner.evaluate(term, {"xs": [10, 20, 30, 40]}) == 4
