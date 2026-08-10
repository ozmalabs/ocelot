#!/usr/bin/env python3
"""certify — the SHARED construct->CERTIFY->compute guard idiom, written ONCE.

THE COMPRESSION THIS IS (CONSOLIDATION). Every self-contained construct-compute faculty
(bounded enumeration; graph count; element-order count; named-space Betti; minimal-
generators; pi_n rank; ...) ends its compute the SAME way: it derives a value PLUS one or
more INDEPENDENT cross-check quantities, and emits the value ONLY when every cross-check
passes — otherwise it returns a value-less Result carrying a NAMED failure detail (the
honest stall that keeps false positives at zero). Each faculty had hand-rolled that guard:

    if got != want:
        out.detail = f"...self-check FAILED for {label}: ...{got}... != ...{want}... -> no value"
        return out

repeated ~14 times across 7 files, byte-for-byte the same control flow differing only in
the check name, the two quantities, and the label. That is duplication, not capability.

This module writes the guard ONCE:
  · `Check(name, got, want, ok=None)` — one certificate test. `ok` defaults to (got == want)
    equality (the dominant case: a constructed quantity must equal its known/independent
    value); pass an explicit `ok` for a predicate check (d^2 == 0, grid-stability, in-range).
  · `first_failure(label, checks)` — run the checks in order; return the standard NAMED
    failure-detail string for the FIRST that fails (or None if all pass). The failure-message
    format ("<label>: <name> self-check FAILED — got <got> vs want <want> -> not certified,
    no value") is written here ONCE; faculties no longer each spell it.
  · `guard(out, label, checks)` — the whole tail: if a check fails, set out.detail to the
    NAMED failure and return out (the caller `return guard(...) or <continue>` short-circuits);
    return None when all pass so the caller proceeds to emit.

ASSAY-NEUTRAL (the discipline). The router scores on a faculty's `value` and on the router's
own fixed stall `bucket` — NEVER on the faculty's internal `out.detail`. So consolidating the
guard changes WHICH path is taken IDENTICALLY (same checks, same order, same pass/fail) and
only rewords the (unscored) detail string. The per-question (value, bucket) assay is therefore
preserved exactly; the only change is -N lines of duplicated control flow.

FAITHFUL (CLAUDE.md): pure world-adapter plumbing. No math decision, no graph state, no key —
it only formats the honest-stall message and routes control flow that the faculties already
had. The certificates' CONTENT (what is checked) stays in each faculty; only the SHAPE of the
emit-or-stall is shared.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class Check:
    """One certificate test: a NAMED independent cross-check the constructed value must pass.
    `ok` defaults to equality (got == want); pass an explicit boolean for a predicate check."""
    name: str
    got: object
    want: object
    ok: Optional[bool] = None

    def passed(self) -> bool:
        return (self.got == self.want) if self.ok is None else bool(self.ok)


def first_failure(label: str, checks: Sequence[Check]) -> Optional[str]:
    """Run the checks in order; return the standard NAMED failure-detail for the FIRST that
    fails, or None if all pass. The honest-stall wording is written here ONCE."""
    for c in checks:
        if not c.passed():
            return (f"{label}: {c.name} self-check FAILED — got {c.got!r} vs "
                    f"want {c.want!r} -> not certified, no value")
    return None


def guard(out, label: str, checks: Sequence[Check]):
    """The shared emit-or-stall TAIL. If any check fails, set out.detail to the NAMED failure
    and return `out` (so the caller does `r = certify.guard(out, ...); if r: return r`); return
    None when every check passes so the caller proceeds to read off + emit the certified value.
    No value is ever set here — emission stays in the faculty (its provenance, its detail)."""
    detail = first_failure(label, checks)
    if detail is not None:
        out.detail = detail
        return out
    return None


__all__ = ["Check", "first_failure", "guard"]
