"""oeis_reference — the OEIS REFERENCE-route RESOLVER for epistemic_access.

Where this sits (mirrors domains/reference_route.py for Wikipedia). The agent's
epistemic_access route-finder (domains/epistemic_access.py) decides, graph-
resident, that an integer-SEQUENCE gap is RESOLVABLE_VIA_ROUTE via the OEIS
REFERENCE store and holds knowing_where_vs_what: it has the ROUTE (the store
name + a lookup key = an OEIS id like 'A000045' or a name substring), NOT the
answer. This module is the mechanical I/O at that boundary: it FETCHES from the
REAL local OEIS dump (domains/oeis_local — the downloaded christopher/oeis
parquet) and EXTRACTS the cited fact (the sequence's ground-truth VALUES + its
prose formula/definition). No LLM, no Rust, no fabrication — a real local lookup.

The unit of resolution is ``oeis_answer(key)`` where `key` is an OEIS id
('A000045') OR a name substring ('Fibonacci numbers'):

  * resolve `key` to a sequence id (direct id, else oeis_local.by_name first hit);
  * oeis_local.definition(id) -> {name(prose), values, offset} — the REAL fetch;
  * the cited fact = the first values + the prose definition, tagged kind 'value'
    (a sequence lookup fills the queried 'the sequence' slot with the actual
    values — it coheres with the queried property, unlike an entity's bare lead).

  returns {answer, kind, title, id, values, extract, source} on a hit, or None
  (no dump / no match) so the chain falls through gracefully.

HONEST scope: the OEIS dump is FACTUAL mathematical reference data (sequence
definitions + their ground-truth values); fetching + reporting it is its
purpose. The values returned are the dataset's own — nothing hand-fed.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from domains import oeis_local as oe

# The store LABEL this resolver answers for (the route-finder tags an OEIS
# reference route with a label containing 'oeis').
_OEIS_STORE_HINTS = ("oeis",)

_ID_RE = re.compile(r"^A\d{6}$", re.IGNORECASE)


def _resolve_id(key: str) -> Optional[str]:
    """Resolve a lookup key to an OEIS id: a literal 'A012345' id, else the
    first by_name hit for a name substring ('Fibonacci' -> 'A000045')."""
    k = (key or "").strip()
    if not k:
        return None
    if _ID_RE.match(k):
        return k.upper()
    hits = oe.by_name(k, limit=1)
    return hits[0][0] if hits else None


def oeis_answer(key: str) -> Optional[dict[str, Any]]:
    """Resolve a sequence lookup key to its cited fact from the REAL OEIS dump.

    key  — an OEIS id ('A000045') OR a name substring ('Fibonacci numbers').

    Returns ``{answer, kind, title, id, values, extract, source}`` on a hit, or
    None (no dump loaded / no match). The `answer` is a short human string (the
    prose definition + the first values); `values` carries the raw ground-truth
    list; `kind` is 'value' (a sequence lookup fills the queried slot). REAL
    local fetch — the values are the dataset's, not fabricated."""
    if not key or not oe.present():
        return None
    sid = _resolve_id(key)
    if sid is None:
        return None
    d = oe.definition(sid)
    if d is None:
        return None
    prose = (d.get("name") or "").strip()
    values = d.get("values") or []
    vshow = ", ".join(str(v) for v in values[:8])
    answer = f"{sid}: {prose} First values: {vshow}." if prose else \
        f"{sid}: {vshow}."
    return {"answer": answer, "kind": "value", "title": sid, "id": sid,
            "values": values, "offset": d.get("offset", 1),
            "extract": prose, "source": "oeis"}


def reference_lookup(store: str, key: str,
                     question_text: Optional[str] = None) -> Optional[str]:
    """The OEIS link of the chained ``reference_lookup``: resolve a banked OEIS
    reference gap (``store`` names an oeis store, ``key`` is the id / name to
    look up). Returns the short answer string, or None for a non-OEIS store / a
    miss (so the chain falls through gracefully)."""
    if not key:
        return None
    low = (store or "").lower()
    if not any(h in low for h in _OEIS_STORE_HINTS):
        return None
    hit = oeis_answer(key)
    return hit["answer"] if hit else None


def reference_detail(store: str, key: str,
                     question_text: Optional[str] = None
                     ) -> Optional[dict[str, Any]]:
    """The full OEIS hit (incl. `kind` + `values` + `title`) for the queried-
    property coherence check + the provenance WHERE. None for a non-OEIS store
    / a miss."""
    if not key:
        return None
    low = (store or "").lower()
    if not any(h in low for h in _OEIS_STORE_HINTS):
        return None
    return oeis_answer(key)


__all__ = ["oeis_answer", "reference_lookup", "reference_detail"]
