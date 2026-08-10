"""AN ABSENT VALUE MUST NEVER READ AS A MEASURED ONE — the static half.

Seven instances of one defect landed in a single day, and each was found by
running something rather than by reading it:

  1. an F16 surrendered axis at flat 0.0 dominating a kept axis
  2. `MIN(declared, F_max*dt/m)` pricing a weaker engine as a cheaper escape
  3. `development_configuration_changed` and 51 siblings read but never written
  4. the `*_joules` energy ledger, template-only, zero instances
  5. an `UNPRICED_COST_FLOOR_UNITS` sentinel standing in for the ledger's reach
  6. `development_evidence_window` making two retention guards vacuous
  7. `steps_to_origin` returning its bound both on "crosses here" and "never"

The engine can already tell absent from zero: a raw `Attr` on a missing key
evaluates to None, and `Eq(Attr, Lit None)` is true ONLY then, while a present
0 gives False. So this is an IDIOM problem, not an engine limitation.

THE RULE THIS MODULE ENCODES, and it is narrow on purpose:

    In a GUARD, `Plus[Attr, Lit 0]` is a bug.
    In an ACCUMULATOR, `Plus[Attr, Lit 0]` is correct.

An empty ledger really has spent nothing, so `enl_settle_energy_balance`
coalescing its posted total is right and must not be "fixed". A guard, by
contrast, decides whether to fire, and a guard that cannot tell "no reading"
from "a reading of zero" fires on blindness.

GUARD POSITIONS are (i) a rule's `where`, and (ii) the `cond` of any
`IfThenElse` reached from anywhere in the rule, including inside effects — a
conditional in an effect is still a decision, and defect 5 lived in exactly
there.

A coalesced read is EXCUSED when the same guard also null-tests the same
attribute (`Eq(Attr, Lit None)` on the same node variable and key): that
combination distinguishes the cases deliberately, which is the whole point.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "seeds"


def _walk(term: Any) -> Iterator[dict]:
    """Every dict node in a term tree, in no particular order."""
    if isinstance(term, dict):
        yield term
        for value in term.values():
            yield from _walk(value)
    elif isinstance(term, (list, tuple)):
        for item in term:
            yield from _walk(item)


def _is_lit_zero(term: Any) -> bool:
    return (isinstance(term, dict) and term.get("type") == "Lit"
            and term.get("value") == 0 and term.get("value") is not False)


def _attr_key(term: Any) -> tuple[str, str] | None:
    """(<var name>, <attr key>) for an `Attr` on a plain `Var`, else None."""
    if not isinstance(term, dict) or term.get("type") != "Attr":
        return None
    node = term.get("node")
    if not isinstance(node, dict) or node.get("type") != "Var":
        return None
    key = term.get("key")
    name = node.get("name")
    if not isinstance(key, str) or not isinstance(name, str):
        return None
    return (name, key)


def coalesced_reads(term: Any) -> set[tuple[str, str]]:
    """Attributes read through the `Plus[Attr, Lit 0]` null-coalescing idiom."""
    found: set[tuple[str, str]] = set()
    for node in _walk(term):
        if node.get("type") != "Plus":
            continue
        items = node.get("items")
        if not isinstance(items, list) or len(items) != 2:
            continue
        for a, b in ((items[0], items[1]), (items[1], items[0])):
            if _is_lit_zero(b):
                attr = _attr_key(a)
                if attr is not None:
                    found.add(attr)
    return found


def null_tested(term: Any) -> set[tuple[str, str]]:
    """Attributes explicitly compared against `Lit None` — absence, tested."""
    tested: set[tuple[str, str]] = set()
    for node in _walk(term):
        if node.get("type") != "Eq":
            continue
        a, b = node.get("a"), node.get("b")
        for x, y in ((a, b), (b, a)):
            if (isinstance(y, dict) and y.get("type") == "Lit"
                    and y.get("value") is None):
                attr = _attr_key(x)
                if attr is not None:
                    tested.add(attr)
    return tested


def guard_terms(rule: dict) -> Iterator[Any]:
    """Every term tree in GUARD position for this rule.

    The `where` clause, plus the `cond` of every `IfThenElse` anywhere in the
    rule — a conditional inside an effect is still a decision about what to
    write, and one of today's seven defects lived precisely there.
    """
    where = rule.get("where")
    if where is not None:
        yield where
    for node in _walk(rule.get("effects")):
        if node.get("type") == "IfThenElse" and node.get("cond") is not None:
            yield node["cond"]
    # An IfThenElse nested inside the `where` is already covered by `where`.


def scan_rule(rule: dict) -> set[tuple[str, str]]:
    """Coalesced guard reads in this rule that carry no null test."""
    offenders: set[tuple[str, str]] = set()
    for guard in guard_terms(rule):
        excused = null_tested(guard)
        offenders |= (coalesced_reads(guard) - excused)
    return offenders


def scan_seeds(seed_dir: Path | None = None) -> list[dict]:
    """Every coalesced, un-null-tested guard read across every seed.

    One record per (seed, rule, variable, attribute).
    """
    seed_dir = seed_dir or SEEDS
    findings: list[dict] = []
    for path in sorted(seed_dir.glob("*.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 -- a malformed seed is not this gate's business
            continue
        for rule in manifest.get("rules") or []:
            if not isinstance(rule, dict) or "match" not in rule:
                continue
            for var, key in sorted(scan_rule(rule)):
                findings.append({
                    "seed": path.stem,
                    "rule": rule.get("name"),
                    "var": var,
                    "attr": key,
                })
    return findings


def finding_id(record: dict) -> str:
    """The stable identity of a finding — what the ratchet allowlists."""
    return f"{record['rule']}::{record['var']}.{record['attr']}"


__all__ = ["coalesced_reads", "null_tested", "guard_terms", "scan_rule",
           "scan_seeds", "finding_id"]
