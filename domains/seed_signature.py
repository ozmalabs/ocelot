"""domains/seed_signature.py — the SEED-LEVEL STRUCTURAL SIGNATURE, per
docs/research/engine_substrate/SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md and
the charter `RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md` names for A3 (the
`_compose_experiment_rule` seed-skip pick) but does not build: *"define
seed_signature(seed_manifest) -> frozenset[(rule_name, *rule_signature_row)],
mint it alongside SeedSummary the same additive-attr way where_signature_json
was minted onto RuleSummary, and build a hand-constructed Class-A/B-style
oracle over a SAMPLE of the 661-seed population before trusting it in the
live `_compose_experiment_rule` seed-skip pick."*

WHY A SEPARATE MODULE, NOT AN EXTENSION OF `domains.rule_signature`:
`rule_signature.rule_signature`/`where_signature` flatten ONE rule's `where`
clause. A `SeedSummary` node has no `where` clause of its own — a seed is a
MANIFEST containing MANY rules. This module's `seed_where_signature` is the
union, over every rule the seed's own manifest declares (re-read from disk
via `substrate.seed_loader.manifest_for` — the exact read
`reflective_faculty._rule_seed_map` already performs for exactly this
purpose), of `rule_signature.where_signature(sub, rule["where"])`, each row
tagged with its OWNING rule's name for provenance. This is deliberately the
WHOLE manifest's rule population, not just the subset that happens to have
won a `RuleSummary` mirror (`_ensure_acting_rule_provenance` /
`_ensure_reply_rule_provenance` / `_ensure_where_literal_rule_provenance`
only mirror rules that write `chosen_action`/`reply`/a where-literal — a
small minority of the ~4100 rule declarations across the seed corpus). A
seed's structural identity should not depend on which of its rules happen to
write one of those three effect shapes.

WHY PRECOMPUTED, NOT A LIVE TERM-LEVEL JOIN (the design choice the task
brief asked to be made explicitly, not assumed): the seed-skip pick this
module feeds (`_compose_experiment_rule`'s `vary` branch) is embedded via
`{"__term__": ...}` into a `SeedDelta`'s `add_node` EFFECT inside an
INSTALLED, LIVE rule — the "mint" rule the composer authors and installs
with `add_rule`. Unlike `_pick_acting_rule`/`_pick_reply_rule` (plain Python
functions that build-then-`native.evaluate` a Term ONCE, synchronously), this
Term is evaluated by the ENGINE'S OWN `run_rules()` fixpoint whenever the
mint rule's `where` matches. A nested nested-Filter/Exists join across the
~4100-row `RuleSummary`-adjacent rule population, re-evaluated live inside
that installed rule, is real per-firing cost with no caching the engine
provides for free. Mirroring `where_signature_json`'s own precedent exactly
(precompute once, store as a plain JSON-string attr, read it back with the
SAME `StringIndexOf` the `keywords_text` overlap already uses) keeps the
mint rule's own Term at the IDENTICAL complexity class as today: one string
attr read per candidate, no nested join, no new Term type.

MEASUREMENT / production-support module, not agent decision logic — same
class as `domains/rule_signature.py` (see that module's own docstring for
the general argument, which applies here unchanged): `seed_where_signature`
is a pure function; `ensure_seed_signature` only `set_attr`s ONE new field on
EXISTING `SeedSummary` nodes another function (`substrate/boot_all.py`'s
`_mint_seed_summary`) already mints; nothing here calls `add_node`. The
DECISION (which seed the fallback picks) stays entirely inside the held Term
`reflective_faculty._compose_experiment_rule` builds and the engine
evaluates — this module supplies one more string attr for that Term to read,
exactly the role `rule_signature.ensure_where_signature` already plays for
`_pick_acting_rule`/`_pick_reply_rule`.
"""
from __future__ import annotations

import json
from typing import Any

from domains import rule_signature as _rsig


def _rows_to_jsonable(rows) -> list:
    """Same determinism convention as `rule_signature._rows_to_jsonable`
    (sorted by `repr` — rows mix scalar types at the same tuple position, so
    a plain tuple sort can raise `TypeError`; `repr` is always comparable).
    Not imported from that module to keep the two signature grains
    (rule-level vs seed-level) independently editable; the shape is
    intentionally identical."""
    return [list(row) for row in sorted(rows, key=repr)]


def seed_where_signature(sub, seed_id: str, manifest: dict) -> frozenset:
    """The seed-level structural signature: the union, over every rule
    `manifest.get('rules')` declares, of `rule_signature.where_signature`
    over that rule's OWN `where` clause, each row tagged with the owning
    rule's name (`(rule_name, *row)` — the charter's own stated shape). A
    rule whose `where`-clause makes the graph-resident signature program
    trap or exhaust fuel is SKIPPED (mirrors `ensure_where_signature`'s own
    documented behaviour for the rule grain) rather than silently degrading
    the whole seed's signature to a second, divergent implementation.

    Pure with respect to `manifest` (already a parsed dict from
    `substrate.seed_loader.manifest_for`, the exact read
    `reflective_faculty._rule_seed_map` performs) — the only graph
    interaction is `sub`/`where_signature`'s own read-only `evaluate` call
    (no `add_node`, no `set_attr` here)."""
    rows: set[tuple] = set()
    for r in (manifest.get("rules") or []):
        if not isinstance(r, dict):
            continue
        rule_name = r.get("name") or ""
        try:
            sig = _rsig.where_signature(sub, r.get("where"))
        except _rsig.SignatureProgramTrap:
            continue
        for row in sig:
            rows.add((rule_name,) + tuple(row))
    return frozenset(rows)


def ensure_seed_signature(sub) -> int:
    """Idempotent: mint/upgrade the ONE new attr `where_signature_json` on
    every EXISTING `SeedSummary` node that carries a `seed_id` but not yet a
    `where_signature_json` — the seed-grain twin of
    `rule_signature.ensure_where_signature`. A seed whose manifest cannot be
    read (deleted from disk, or a synthetic/test-only `SeedSummary` with no
    backing file — `_rule_seed_map` fails the identical way for the identical
    reason) is SKIPPED, not given a value from a guess: the fallback Term
    reads an absent attr as `None`, which the same abstain semantics
    `_pick_acting_rule`'s fallback already relies on treat as "no genuine
    structural match" — the conservative, correct default. Returns the
    number of nodes touched (0 on a second call)."""
    from substrate.seed_loader import manifest_for
    touched = 0
    for n in sub.nodes("SeedSummary"):
        at = sub.node(n)["attrs"]
        if at.get("where_signature_json") is not None:
            continue
        sid = at.get("seed_id")
        if not sid:
            continue
        try:
            manifest = manifest_for(sid)
        except Exception:
            continue
        sig = seed_where_signature(sub, sid, manifest)
        sub.set_attr(n, "where_signature_json", json.dumps(_rows_to_jsonable(sig)))
        touched += 1
    return touched
