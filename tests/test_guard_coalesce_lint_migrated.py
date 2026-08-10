"""AN ABSENT VALUE MUST NEVER READ AS A MEASURED ONE — the ratchet.

Seven instances of this one defect landed in a single day, plus two more in the
instruments. Every one was found by RUNNING something. This gate reads instead.

The rule is narrow and mechanical, and the narrowness is the point:

    in a GUARD, `Plus[Attr, Lit 0]` is a bug
    in an ACCUMULATOR, `Plus[Attr, Lit 0]` is correct

An empty ledger really has spent nothing, so `enl_settle_energy_balance`
coalescing its posted total is right. A guard decides whether to fire, and a
guard that cannot tell "no reading" from "a reading of zero" fires on
blindness.

RATCHET, NOT ABSOLUTE. The first run found 10,279 distinct sites. A gate nobody
can turn green gets deleted, so the standing demand is "no NEW coalesced
guards" and the debt is enumerated in `results/guard_coalesce_baseline.json` --
as a LIST OF IDS, never a count, because a count can be held while the set
underneath it grows.
"""
import json
from pathlib import Path

from domains.engine_provenance import engine_preamble
engine_preamble()

from domains.guard_coalesce_lint import (                                # noqa: E402
    coalesced_reads, finding_id, guard_terms, null_tested, scan_rule, scan_seeds,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "results" / "guard_coalesce_baseline.json"


def _baseline() -> set[str]:
    return set(json.loads(BASELINE.read_text(encoding="utf-8"))["entries"])


# ------------------------------------------------------- the detector itself

def _rule(where=None, effects=None):
    return {"name": "t", "match": [["a", "e", "b"]],
            "where": where, "effects": effects or []}


def _attr(var, key):
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def _coalesced(var, key):
    return {"type": "Plus", "items": [_attr(var, key), {"type": "Lit", "value": 0}]}


def test_a_coalesced_guard_read_is_detected():
    rule = _rule(where={"type": "Gt", "a": _coalesced("x", "units"),
                        "b": {"type": "Lit", "value": 3}})
    assert scan_rule(rule) == {("x", "units")}


def test_the_idiom_is_detected_in_either_operand_order():
    flipped = {"type": "Plus", "items": [{"type": "Lit", "value": 0},
                                         _attr("x", "units")]}
    assert coalesced_reads(flipped) == {("x", "units")}


def test_a_null_test_on_the_same_attribute_excuses_it():
    """Coalescing beside an explicit absence test is the deliberate pattern."""
    rule = _rule(where={"type": "And", "items": [
        {"type": "Not", "arg": {"type": "Eq", "a": _attr("x", "units"),
                                "b": {"type": "Lit", "value": None}}},
        {"type": "Gt", "a": _coalesced("x", "units"),
         "b": {"type": "Lit", "value": 3}},
    ]})
    assert scan_rule(rule) == set()


def test_a_null_test_on_a_DIFFERENT_attribute_does_not_excuse_it():
    rule = _rule(where={"type": "And", "items": [
        {"type": "Not", "arg": {"type": "Eq", "a": _attr("x", "other"),
                                "b": {"type": "Lit", "value": None}}},
        {"type": "Gt", "a": _coalesced("x", "units"),
         "b": {"type": "Lit", "value": 3}},
    ]})
    assert scan_rule(rule) == {("x", "units")}


def test_an_accumulator_in_an_effect_is_NOT_flagged():
    """The load-bearing exemption. An empty ledger has spent nothing."""
    rule = _rule(where={"type": "Lit", "value": True}, effects=[
        ["set_attr", "ledger", "stock_units", {"__term__": _coalesced("ledger", "opening_units")}],
    ])
    assert scan_rule(rule) == set()


def test_a_conditional_INSIDE_an_effect_is_a_guard():
    """One of the seven defects lived exactly here: an `IfThenElse` in an
    effect is still a decision about what to write."""
    rule = _rule(where={"type": "Lit", "value": True}, effects=[
        ["set_attr", "c", "cost", {"__term__": {
            "type": "IfThenElse",
            "cond": {"type": "Gt", "a": _coalesced("e", "release_cost_units"),
                     "b": {"type": "Lit", "value": 0}},
            "then": {"type": "Lit", "value": 1},
            "other": {"type": "Lit", "value": 2}}}],
    ])
    assert scan_rule(rule) == {("e", "release_cost_units")}


def test_a_present_zero_literal_is_not_confused_with_false():
    assert coalesced_reads({"type": "Plus", "items": [
        _attr("x", "k"), {"type": "Lit", "value": False}]}) == set()


def test_null_tested_reads_both_operand_orders():
    assert null_tested({"type": "Eq", "a": {"type": "Lit", "value": None},
                        "b": _attr("x", "k")}) == {("x", "k")}


def test_guard_positions_include_where_and_effect_conditionals():
    rule = _rule(where={"type": "Lit", "value": True}, effects=[
        ["set_attr", "c", "k", {"__term__": {
            "type": "IfThenElse", "cond": {"type": "Lit", "value": True},
            "then": {"type": "Lit", "value": 1},
            "other": {"type": "Lit", "value": 0}}}],
    ])
    assert len(list(guard_terms(rule))) == 2


# ------------------------------------------------------------- the ratchet

def test_no_new_coalesced_guards_beyond_the_recorded_debt():
    """THE GATE. New coalesced guards are refused; the existing debt stands
    enumerated so it can be paid down one conversion at a time."""
    baseline = _baseline()
    found = {finding_id(record) for record in scan_seeds()}
    introduced = sorted(found - baseline)
    assert not introduced, (
        f"{len(introduced)} NEW coalesced guard read(s) — a guard that reads an "
        f"attribute through `Plus[Attr, Lit 0]` cannot tell 'no reading' from "
        f"'a reading of zero', so it fires on blindness. Use a null test "
        f"(`Eq(Attr, Lit None)`) where absence must not satisfy the guard, or "
        f"record the site in results/guard_coalesce_baseline.json with a "
        f"reason if it is genuinely an accumulator:\n  "
        + "\n  ".join(introduced[:40]))


def test_the_baseline_is_a_list_of_ids_never_a_count():
    """The project's own standing rule, applied to this gate's own baseline:
    a count can be held while the set underneath it grows."""
    raw = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert isinstance(raw["entries"], list)
    assert all(isinstance(entry, str) for entry in raw["entries"])
    assert len(set(raw["entries"])) == len(raw["entries"])


def test_retired_debt_is_removed_from_the_baseline_not_left_to_rot():
    """A stale baseline entry is a claim about the tree that is no longer
    true. Report them so the list stays honest rather than growing forever."""
    baseline = _baseline()
    found = {finding_id(record) for record in scan_seeds()}
    stale = sorted(baseline - found)
    assert not stale, (
        f"{len(stale)} baseline entr(ies) no longer exist — they were fixed or "
        f"renamed. Remove them from results/guard_coalesce_baseline.json so the "
        f"list keeps meaning what it says:\n  " + "\n  ".join(stale[:40]))
