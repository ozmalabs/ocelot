"""lmfdb_local — the LMFDB REFERENCE-route fetch world-adapter for arithmetic
objects (elliptic curves / torsion subgroups over a number field).

Where this sits (mirrors domains/reference_route.py for Wikipedia and
domains/oeis_reference.py for OEIS). The agent's epistemic_access route-finder
decides, graph-resident, that an ELLIPTIC-CURVE / TORSION-SUBGROUP gap is
RESOLVABLE_VIA_ROUTE via the LMFDB store and holds knowing_where_vs_what: it has
the ROUTE (the store + a lookup key = a number-field label like '2.0.3.1' for
Q(sqrt(-3))), NOT the answer. This module is the mechanical I/O at that boundary.

THE FETCH (architecture-faithful — Python is the world-adapter; CLAUDE.md):
  · TRY THE REAL LMFDB API (https://www.lmfdb.org/api/ec_nfcurves) — fetch the
    elliptic curves over the field + their `torsion_structure` / `torsion_order`.
    REAL data; nothing fabricated.
  · CACHE every successful fetch to data/lmfdb/<field>.json (gitignored, like
    data/nlab) so the compute-over-data is reproducible offline.
  · COMPUTE over the fetched/cached curves: the LARGEST NON-CYCLIC torsion
    PRESENT (a 2-generator torsion_structure [m, n], its order m*n) — the
    EMPIRICAL / EXISTENCE maximum over the database.

TWO HONESTY RAILS (read in epistemic_access wiring + the demo):
  1. The fetch is a REAL lookup. If the API is unreachable OR bot-gated
     (LMFDB serves a reCAPTCHA challenge to sustained programmatic access), we
     do NOT fake a value — `fetch_field_curves` returns a `boundary` marker and
     the compute reports what (if anything) the cache holds. The route is wired;
     the live pull is the honestly-named seam.
  2. EMPIRICAL vs RIGOROUS. The largest non-cyclic torsion PRESENT in LMFDB's
     curves over Q(sqrt(-3)) is the EMPIRICAL/EXISTENCE max (fetched + computed
     over the data, = Z/3 x Z/6 = 18). The RIGOROUS maximality (no curve ANYWHERE
     has larger) is the CLASSIFICATION theorem (Najman 2010,
     doi:10.1016/j.jnt.2009.12.008) — a READ-CITE, not a database scan. This
     module returns the empirical max only; the rigorous caveat is reported by
     the caller, distinguished.

  lmfdb_answer(key, question_text=None) -> {answer, kind, ...} | None  (the
    resolver unit: the empirical-max torsion fact for a field key, or the
    boundary). Used by the epistemic_access reference resolver.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

_ROOT = Path(__file__).resolve().parent.parent
_CACHE = _ROOT / "data" / "lmfdb"            # gitignored (data/ in .gitignore)

# The store LABEL this resolver answers for (the route-finder tags an LMFDB
# reference route with a label containing 'lmfdb').
_LMFDB_STORE_HINTS = ("lmfdb",)

# Q(sqrt(-3)) = Q(zeta_3): LMFDB number-field label. The route key for the
# elliptic-curve torsion question maps onto this field.
FIELD_Q_SQRT_MINUS3 = "2.0.3.1"

# A coarse map from a human field surface -> the LMFDB field label (the lookup
# key the route carries). Mechanical surface match; no decision over graph state.
_FIELD_SURFACE = {
    "q(sqrt(-3))": FIELD_Q_SQRT_MINUS3,
    "q(sqrt-3)": FIELD_Q_SQRT_MINUS3,
    "q(zeta_3)": FIELD_Q_SQRT_MINUS3,
    "q(zeta3)": FIELD_Q_SQRT_MINUS3,
    "sqrt(-3)": FIELD_Q_SQRT_MINUS3,
    "sqrt-3": FIELD_Q_SQRT_MINUS3,
}

_API = "https://www.lmfdb.org/api/ec_nfcurves/"
_UA = "ozma-jabberwock-research/1.0 (math reference fetch; polite, rate-limited)"
_LAST_FETCH = [0.0]
_MIN_INTERVAL = 2.0          # polite: >= 2s between live LMFDB requests.


# ---------------------------------------------------------------------------
# field-label resolution.
# ---------------------------------------------------------------------------

def resolve_field_label(key: str) -> Optional[str]:
    """A lookup key -> an LMFDB number-field label. A literal label ('2.0.3.1')
    passes through; a human surface ('Q(sqrt(-3))') maps via _FIELD_SURFACE."""
    k = (key or "").strip()
    if not k:
        return None
    # a literal n.r.d.i label (e.g. 2.0.3.1).
    parts = k.split(".")
    if len(parts) == 4 and all(p.lstrip("-").isdigit() for p in parts):
        return k
    low = k.lower().replace(" ", "")
    return _FIELD_SURFACE.get(low)


# ---------------------------------------------------------------------------
# THE REAL FETCH — the live LMFDB API, cached to data/lmfdb (gitignored).
# ---------------------------------------------------------------------------

def _cache_path(field_label: str) -> Path:
    return _CACHE / f"ec_nfcurves_{field_label}.json"


def _load_cache(field_label: str) -> Optional[list[dict[str, Any]]]:
    p = _cache_path(field_label)
    if not p.exists():
        return None
    try:
        with open(p) as f:
            doc = json.load(f)
        rows = doc.get("curves")
        return rows if isinstance(rows, list) else None
    except Exception:
        return None


def _save_cache(field_label: str, curves: list[dict[str, Any]],
                meta: dict[str, Any]) -> None:
    try:
        _CACHE.mkdir(parents=True, exist_ok=True)
        with open(_cache_path(field_label), "w") as f:
            json.dump({"field_label": field_label, "curves": curves,
                       "meta": meta}, f)
    except Exception:
        pass


def _api_get(params: dict[str, Any], timeout: float = 30.0
             ) -> Optional[dict[str, Any]]:
    """One polite GET to the LMFDB API. Returns the parsed JSON, or None when
    the response is NOT JSON (the reCAPTCHA bot-gate serves HTML — the live-fetch
    boundary; we do NOT fake past it) / the request fails."""
    # rate-limit: be polite to the LMFDB API.
    dt = time.time() - _LAST_FETCH[0]
    if dt < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - dt)
    url = _API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": _UA,
                                               "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
        _LAST_FETCH[0] = time.time()
    except Exception:
        return None
    try:
        return json.loads(body)
    except Exception:
        # NOT JSON -> the reCAPTCHA bot-gate (HTML) or an error page. The
        # honestly-named live-fetch boundary; no fabrication past it.
        return None


def fetch_field_curves(field_label: str, *, max_pages: int = 6,
                       page: int = 100, allow_live: bool = True
                       ) -> dict[str, Any]:
    """Fetch the elliptic curves over `field_label` + their torsion data. REAL
    LMFDB API (cached to data/lmfdb). Returns:

        {field_label, curves:[{label, torsion_structure, torsion_order}, ...],
         source: 'live' | 'cache' | 'none', reachable: bool, boundary: str|None}

    Order: a populated CACHE is used first (offline-reproducible); else (with
    `allow_live`) the live API is paged politely. If the live API is unreachable
    or BOT-GATED (HTML reCAPTCHA, not JSON), `source='none'`, `reachable=False`,
    and `boundary` names the seam — NO fabricated curves."""
    cached = _load_cache(field_label)
    if cached:
        return {"field_label": field_label, "curves": cached,
                "source": "cache", "reachable": True, "boundary": None}
    if not allow_live:
        return {"field_label": field_label, "curves": [], "source": "none",
                "reachable": False,
                "boundary": "no cache + live fetch disabled (allow_live=False)"}
    curves: list[dict[str, Any]] = []
    fields = "label,torsion_structure,torsion_order"
    gated = False
    got_any = False
    for pg in range(max_pages):
        doc = _api_get({"field_label": field_label, "_format": "json",
                        "_limit": page, "_offset": pg * page,
                        "_fields": fields})
        if doc is None:
            # boundary: unreachable or bot-gated (no JSON). Stop; honest seam.
            gated = (pg == 0)            # gated from the first page = no data at all
            break
        got_any = True
        data = doc.get("data") or []
        for r in data:
            curves.append({
                "label": r.get("label"),
                "torsion_structure": r.get("torsion_structure"),
                "torsion_order": r.get("torsion_order"),
            })
        if not doc.get("next") or not data:
            break
    if curves:
        _save_cache(field_label, curves,
                    {"fetched_pages": "<=%d" % max_pages, "via": "lmfdb_api"})
        return {"field_label": field_label, "curves": curves,
                "source": "live", "reachable": True, "boundary": None}
    boundary = ("LMFDB API bot-gated (served a reCAPTCHA HTML challenge, not "
                "JSON) — the route + fetch are wired; the live pull is the seam"
                if gated else
                "LMFDB API returned no curves (unreachable / empty)")
    return {"field_label": field_label, "curves": [], "source": "none",
            "reachable": got_any, "boundary": boundary}


# ---------------------------------------------------------------------------
# THE COMPUTE — the EMPIRICAL/existence max non-cyclic torsion over the data.
# ---------------------------------------------------------------------------

def largest_noncyclic_torsion(curves: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Compute the LARGEST NON-CYCLIC torsion subgroup PRESENT among `curves`
    (the empirical/existence max). A non-cyclic torsion is a 2-generator
    structure [m, n] (m | n, m > 1); its order is m*n. Returns
    {structure:[m,n], order, label} for the maximal-order non-cyclic curve, or
    None if no non-cyclic torsion is present in the data. Pure computation over
    the FETCHED values — not fed."""
    best = None
    for r in curves:
        ts = r.get("torsion_structure")
        if not (isinstance(ts, list) and len(ts) >= 2):
            continue                     # cyclic (1 generator) -> skip
        try:
            ms = [int(x) for x in ts]
        except Exception:
            continue
        order = 1
        for m in ms:
            order *= m
        if best is None or order > best["order"]:
            best = {"structure": ms, "order": order, "label": r.get("label")}
    return best


# ---------------------------------------------------------------------------
# lmfdb_answer — the resolver unit. key (field) -> the empirical-max fact.
# ---------------------------------------------------------------------------

def lmfdb_answer(key: str, question_text: Optional[str] = None
                 ) -> Optional[dict[str, Any]]:
    """Resolve an elliptic-curve / torsion lookup key (a field label or surface,
    e.g. 'Q(sqrt(-3))' / '2.0.3.1') to the EMPIRICAL-MAX non-cyclic torsion fact
    fetched + computed over LMFDB's curves over that field.

    Returns ``{answer, kind, title, structure, order, label, field_label,
    source, reachable, boundary}`` — on a real fetch+compute, `kind='value'`
    (the order fills the queried 'largest order' slot) and `answer` states the
    empirical max ('Z/3 x Z/6 = 18 (the largest non-cyclic torsion present in
    LMFDB over Q(sqrt(-3)))'). When the live API is unreachable / bot-gated and
    no cache holds the field, returns the boundary marker (kind='boundary',
    answer=None) — NO fabricated value. Architecture-faithful: the agent's
    route-finder routed; this is the world-adapter fetch."""
    field_label = resolve_field_label(key)
    if field_label is None:
        return None
    fetched = fetch_field_curves(field_label)
    curves = fetched.get("curves") or []
    best = largest_noncyclic_torsion(curves)
    if best is None:
        # No non-cyclic torsion present (boundary, or the data slice lacks it).
        return {"answer": None, "kind": "boundary", "title": field_label,
                "structure": None, "order": None, "label": None,
                "field_label": field_label,
                "n_curves": len(curves),
                "source": fetched.get("source"),
                "reachable": fetched.get("reachable"),
                "boundary": fetched.get("boundary") or
                ("fetched %d curves but none with non-cyclic torsion present "
                 "in the slice" % len(curves))}
    m, n = best["structure"][0], best["structure"][1]
    answer = (f"Z/{m} x Z/{n} (order {best['order']}) is the largest non-cyclic "
              f"torsion subgroup present in LMFDB's elliptic curves over the "
              f"field {field_label}.")
    return {"answer": answer, "kind": "value", "title": field_label,
            "structure": best["structure"], "order": best["order"],
            "label": best["label"], "field_label": field_label,
            "n_curves": len(curves),
            "source": fetched.get("source"), "reachable": True,
            "boundary": None,
            "extract": answer, "id": best.get("label")}


def reference_lookup(store: str, key: str,
                     question_text: Optional[str] = None) -> Optional[str]:
    """The LMFDB link of the chained ``reference_lookup``: resolve a banked LMFDB
    reference gap. Returns the empirical-max answer string on a real fetch, or
    None for a non-LMFDB store / a miss / the live-fetch boundary (so the chain
    falls through gracefully and the boundary is reported by reference_detail)."""
    if not key:
        return None
    low = (store or "").lower()
    if not any(h in low for h in _LMFDB_STORE_HINTS):
        return None
    hit = lmfdb_answer(key, question_text)
    if hit is None or hit.get("kind") == "boundary":
        return None
    return hit.get("answer")


def reference_detail(store: str, key: str,
                     question_text: Optional[str] = None
                     ) -> Optional[dict[str, Any]]:
    """The full LMFDB hit (incl. `kind`, the empirical-max `order`/`structure`,
    `source`/`reachable`/`boundary`) for the queried-property coherence check +
    the honest boundary report. None for a non-LMFDB store / a bad key."""
    if not key:
        return None
    low = (store or "").lower()
    if not any(h in low for h in _LMFDB_STORE_HINTS):
        return None
    return lmfdb_answer(key, question_text)


__all__ = ["FIELD_Q_SQRT_MINUS3", "resolve_field_label", "fetch_field_curves",
           "largest_noncyclic_torsion", "lmfdb_answer",
           "reference_lookup", "reference_detail"]
