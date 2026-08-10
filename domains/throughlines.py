"""throughlines — A THROUGHLINE IS A PERSISTENT THREAD WOVEN THROUGH N (3+) ARCS,
one level up from nested_reading's SPANNING THEME.

nested_reading's spanning theme is a SINGLE cross-episode relation between TWO
sibling StoryUnits (the reciprocity of 'The Lion and the Mouse': episode 2
reverses episode 1). A THROUGHLINE is one level up again: a thread that PERSISTS
across N (3+) arcs of a multi-arc story. Three kinds, each recognised the SAME
way -- a cross-unit token decoded against a dedicated codebook:

  1. RECURRING PROTAGONIST (kind:character). Unit-scoping (MOVE 2b) made the
     per-arc entity/actor nodes DISTINCT (the Mira of arc 1 and the Mira of arc 4
     are different graph nodes). The throughline RE-LINKS them: a NAME that is the
     ACTOR of a UnitAction in >=2 sibling StoryUnits mints a Throughline{kind:
     character} with a `spans_unit` edge to each occurrence unit. This is the
     PRIMARY throughline -- the returning protagonist is what makes the separate
     arcs ONE story.

  2. RECURRING BEAT (kind:pattern). The arcs share a repeating structure (help ->
     thank -> gift). A (rel, patient) BEAT that recurs across >=2 sibling units --
     here the help->thank beat (a helper THANKS the protagonist, arc after arc) --
     mints a Throughline{kind:pattern}.

  3. CAUSAL PAYOFF (kind:payoff). An OBJECT (a non-protagonist, non-pronoun name)
     that is introduced (as a patient) in an EARLIER unit and referenced/used
     (patient or agent) in a strictly LATER unit -- the setup->payoff loop -- mints
     a Throughline{kind:payoff}.

Then the META-THEME (one level up again): the SET of minted Throughline kinds is
itself a token decoded against a ShapeSignatureMetaTheme codebook -- the recurring
protagonist enacting the recurring beat, and the payoff closing the loop, compose
into the whole-story theme ('kindness returned' when all three thread; 'recurring
kindness' when only protagonist + beat do). A MetaTheme node is minted on the root
StoryUnit, threaded to the throughlines it composes.

ARCHITECTURE (CLAUDE.md). Each throughline is a CROSS-UNIT COLLAPSE: the token is
a mechanical existence check over the children's own minted UnitAction nodes (the
SAME shape as nested_reading._span_token, one level up), and the KIND/THEME is the
ShapeDecode's verdict (`reading_collapse._winner`), NEVER a Python if/else naming
it and NEVER a Python `for unit: decide_throughline(unit)` loop. The mint is graph
nodes/edges (Throughline / MetaTheme nodes + spans_unit / threads_throughline
edges). No `import re`; donkey = 0.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from domains import discourse_coherence as dc
from domains import reading_collapse as rc
from domains.reference_resolution import _PRONOUNS

_THR_CODEBOOK_TYPE = "ShapeSignatureThroughline"
_META_CODEBOOK_TYPE = "ShapeSignatureMetaTheme"

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _v(nid):
    return nid.value if hasattr(nid, "value") else nid


def _node_by_v(sub, node_type: str, v):
    for n in sub.nodes(node_type):
        if _v(n) == v:
            return n
    return None


# --------------------------------------------------------------------------- #
#  codebook install (mechanical seed I/O -- the SAME idiom nested_reading and
#  story_tree use). Installs the ShapeSignatureThroughline + ShapeSignatureMetaTheme
#  codebooks, each guarded by a graph-resident Seed sentinel.
# --------------------------------------------------------------------------- #
def _install_seed(sub, seed_id: str) -> None:
    for n in sub.nodes("Seed"):
        if sub.node(n)["attrs"].get("id") == seed_id:
            return
    with open(os.path.join(_ROOT, "seeds", "%s.json" % seed_id)) as f:
        manifest = json.load(f)
    for nd in manifest.get("nodes", []):
        sub.add_node(nd["type"], dict(nd.get("attrs", {})))
    sub.add_node("Seed", {"id": seed_id, "version": manifest.get("version", "1.0.0")})


def ensure_codebook(agent) -> None:
    sub, _ = _resolve(agent)
    _install_seed(sub, "throughline")
    _install_seed(sub, "throughline_meta")


# --------------------------------------------------------------------------- #
#  the sibling units + their UnitAction rows (pure graph reads off the
#  has_story_unit tree + the children's own minted UnitAction nodes).
# --------------------------------------------------------------------------- #
def _child_units(ad, root_id) -> list:
    """The leaf StoryUnits under `root_id`, in span order (mirrors
    nested_reading._child_units -- a pure graph read off the StoryUnit nodes)."""
    sub, _ = _resolve(ad)
    kids = []
    for n in sub.nodes("StoryUnit"):
        at = sub.node(n)["attrs"]
        if at.get("kind") == "root":
            continue
        kids.append((at.get("span_start") if at.get("span_start") is not None else -1,
                     _v(n)))
    kids.sort()
    return [k for _, k in kids]


def _unit_action_rows(ad, units: list) -> list:
    """Every UnitAction of the sibling units, as {unit, rel, agent, patient, order}
    where `order` is the unit's position in span order. A pure graph read (the SAME
    read nested_reading._unit_actions does, carrying the unit ORDER so payoff can
    compare early vs late)."""
    sub, _ = _resolve(ad)
    order_of = {u: i for i, u in enumerate(units)}
    rows = []
    for n in sub.nodes("UnitAction"):
        at = sub.node(n)["attrs"]
        u = at.get("unit")
        if u not in order_of:
            continue
        rows.append({"unit": u, "order": order_of[u], "rel": at.get("rel"),
                     "agent": at.get("agent"), "patient": at.get("patient")})
    return rows


# --------------------------------------------------------------------------- #
#  TOKEN BUILDERS — each a MECHANICAL existence check over the UnitAction rows,
#  building a candidate (token, name, spanned_units). Mirrors nested_reading.
#  _span_token EXACTLY (an existence check building a TOKEN; it NEVER names the
#  throughline kind -- that is the ShapeDecode's verdict). A candidate is (token,
#  name, units); the DECODE decides whether the token is a throughline and of
#  which kind.
# --------------------------------------------------------------------------- #
def _character_candidates(ad, units: list) -> list:
    """RECURRING_CHARACTER candidates: a NAME that is the ACTOR (agent) of a
    UnitAction in >=2 distinct sibling units. Read off the UnitAction rows -- the
    per-arc actor occurrences unit-scoping made distinct, re-linked. Returns
    (token, name, sorted-units) per recurring actor, most-spanning first (the
    primary protagonist spans the most arcs)."""
    rows = _unit_action_rows(ad, units)
    agent_units: dict = {}
    for r in rows:
        a = r.get("agent")
        if not a or a == r.get("patient"):
            continue
        agent_units.setdefault(a, set()).add(r["unit"])
    out = [("RECURRING_CHARACTER", name, sorted(us, key=lambda u: units.index(u)))
           for name, us in agent_units.items() if len(us) >= 2]
    out.sort(key=lambda c: -len(c[2]))
    return out


def _beat_candidates(ad, units: list) -> list:
    """RECURRING_BEAT candidates: a (rel, patient) pair that recurs as a UnitAction
    across >=2 distinct sibling units -- the repeating structural beat (the
    help->thank beat: a helper THANKS the protagonist, arc after arc). Read off the
    UnitAction rows. Returns (token, 'rel:patient', sorted-units)."""
    rows = _unit_action_rows(ad, units)
    beat_units: dict = {}
    for r in rows:
        rel, pat = r.get("rel"), r.get("patient")
        if not rel or not pat:
            continue
        beat_units.setdefault((rel, pat), set()).add(r["unit"])
    out = [("RECURRING_BEAT", "%s:%s" % (rel, pat),
            sorted(us, key=lambda u: units.index(u)))
           for (rel, pat), us in beat_units.items() if len(us) >= 2]
    out.sort(key=lambda c: -len(c[2]))
    return out


def _payoff_candidates(ad, units: list, character_names: set) -> list:
    """CAUSAL_PAYOFF candidates: an OBJECT (a non-protagonist, non-pronoun name)
    that is a PATIENT in an EARLIER unit and is referenced/used (patient OR agent)
    in a strictly LATER unit -- the setup->payoff loop. Read off the UnitAction rows
    with their unit ORDER. Protagonist names (recurring actors) and pronoun surfaces
    (reused from reference_resolution._PRONOUNS -- graph-data reuse, no re-typed
    list) are EXCLUDED: a payoff element is a gift/object, not the hero and not a
    bare pronoun. Returns (token, name, sorted-units)."""
    rows = _unit_action_rows(ad, units)
    intro_order: dict = {}          # name -> earliest unit-order it is a patient in
    intro_unit: dict = {}
    uses: dict = {}                 # name -> {(order, unit)} it is a patient/agent in
    for r in rows:
        for slot in ("patient", "agent"):
            nm = r.get(slot)
            if not nm or nm in character_names or nm.lower() in _PRONOUNS:
                continue
            uses.setdefault(nm, set()).add((r["order"], r["unit"]))
        pat = r.get("patient")
        if pat and pat not in character_names and pat.lower() not in _PRONOUNS:
            if pat not in intro_order or r["order"] < intro_order[pat]:
                intro_order[pat] = r["order"]
                intro_unit[pat] = r["unit"]
    out = []
    for nm, occ in uses.items():
        if nm not in intro_order:
            continue
        i0 = intro_order[nm]
        later = sorted({u for (o, u) in occ if o > i0}, key=lambda u: units.index(u))
        if later:
            span = [intro_unit[nm]] + later
            out.append(("CAUSAL_PAYOFF", nm, span))
    out.sort(key=lambda c: -len(c[2]))
    return out


# --------------------------------------------------------------------------- #
#  DECODE — a thin ShapeDecode shim pointed at the throughline codebook_type,
#  the SAME shim nested_reading._decode_span uses one level down.
# --------------------------------------------------------------------------- #
def _decode(ad, token: str, codebook_type: str) -> dict:
    _, native = _resolve(ad)
    term = {"type": "ShapeDecode",
            "goal": {"type": "Lit", "value": [[token]]},
            "codebook_type": codebook_type, "beam": 1, "max_steps": 1, "cand_k": 4}
    res = native.evaluate(term)
    if not isinstance(res, dict):
        return {"plan": [], "residual": [[token]], "ordered_parts": []}
    return res


def _schema_attr(ad, codebook_type: str, name: str, key: str):
    sub, _ = _resolve(ad)
    for n in sub.nodes(codebook_type):
        at = sub.node(n)["attrs"]
        if at.get("name") == name:
            return at.get(key)
    return None


def decode_throughline(ad, token: str) -> dict:
    """Public: decode ONE thread token against the ShapeSignatureThroughline
    codebook. The KIND is the decode's verdict (read off reading_collapse._winner
    -> the winning schema's own `kind` attr), never a Python assignment."""
    ensure_codebook(ad)
    res = _decode(ad, token, _THR_CODEBOOK_TYPE)
    name, fit = rc._winner(res)
    kind = _schema_attr(ad, _THR_CODEBOOK_TYPE, name, "kind") if (name and fit > 0) else None
    line = _schema_attr(ad, _THR_CODEBOOK_TYPE, name, "line") if (name and fit > 0) else None
    return {"token": token, "construction": name, "kind": kind, "line": line,
            "shape_fit": max(fit, 0)}


# --------------------------------------------------------------------------- #
#  RECOGNIZE — each candidate token is decoded; a winning verdict mints a
#  Throughline node wired by spans_unit to each occurrence unit and threaded from
#  the root. The DECISION is the decode; Python only mints the graph.
# --------------------------------------------------------------------------- #
def _mint_throughline(ad, root_id, kind: str, name: str, token: str, line: str,
                      units: list) -> dict:
    sub, native = _resolve(ad)
    tn = sub.add_node("Throughline", {
        "kind": kind, "name": name, "token": token, "line": line,
        "root": _v(root_id), "spans": json.dumps(list(units)),
        "n_units": len(units)})
    root_node = _node_by_v(sub, "StoryUnit", _v(root_id))
    if root_node is not None:
        dc._mint_edge(sub, native, root_node, tn, "has_throughline", {"kind": kind})
    for uv in units:
        un = _node_by_v(sub, "StoryUnit", uv)
        if un is not None:
            dc._mint_edge(sub, native, tn, un, "spans_unit", {})
    return {"node": _v(tn), "kind": kind, "name": name, "token": token,
            "line": line, "spans": list(units)}


def recognize_throughlines(ad, root_id) -> dict:
    """Recognise every throughline threading the arcs under `root_id`. Each
    candidate thread (recurring character / recurring beat / causal payoff) is
    built as a cross-unit token by a mechanical read over the children's UnitAction
    nodes, decoded against the ShapeSignatureThroughline codebook, and -- on a
    winning verdict -- minted as a Throughline node with spans_unit edges to each
    occurrence unit. A candidate no schema covers mints nothing (the discriminative
    null). Returns the list of minted throughlines + the honest per-kind ledger."""
    ensure_codebook(ad)
    units = _child_units(ad, root_id)
    char_cands = _character_candidates(ad, units)
    char_names = {name for (_, name, _) in char_cands}
    beat_cands = _beat_candidates(ad, units)
    payoff_cands = _payoff_candidates(ad, units, char_names)

    minted: list = []
    ledger = {"character": [], "pattern": [], "payoff": []}
    for token, name, us in (char_cands + beat_cands + payoff_cands):
        dec = decode_throughline(ad, token)
        if dec["kind"] is None or dec["shape_fit"] <= 0:
            continue
        rec = _mint_throughline(ad, root_id, dec["kind"], name, token, dec["line"], us)
        minted.append(rec)
        ledger.setdefault(dec["kind"], []).append({"name": name, "spans": list(us)})
    return {"root": _v(root_id), "units": units, "throughlines": minted,
            "ledger": ledger,
            "candidates": {"character": char_cands, "beat": beat_cands,
                           "payoff": payoff_cands}}


def read_throughlines(ad, root_id=None) -> list:
    """A pure graph read of every minted Throughline (for gates/demos)."""
    sub, _ = _resolve(ad)
    out = []
    for n in sub.nodes("Throughline"):
        at = dict(sub.node(n)["attrs"])
        if root_id is not None and at.get("root") != _v(root_id):
            continue
        at["node"] = _v(n)
        at["spans"] = json.loads(at.get("spans") or "[]")
        out.append(at)
    out.sort(key=lambda r: r.get("kind") or "")
    return out


# --------------------------------------------------------------------------- #
#  META-THEME — the SET of minted Throughline kinds is a token decoded against the
#  ShapeSignatureMetaTheme codebook. The whole-story theme is the decode's verdict;
#  a MetaTheme node is minted on the root, threaded to the throughlines it composes.
# --------------------------------------------------------------------------- #
def _meta_token(ad, root_id) -> tuple:
    """The meta token, read off the minted Throughline nodes' `kind` attrs (a
    mechanical existence check over which kinds are present). CHAR_BEAT_PAYOFF when
    character + pattern + payoff all thread; CHAR_BEAT when only character + pattern;
    else META_NONE. The token is data; the THEME is the decode's verdict, never named
    here."""
    kinds = {t["kind"] for t in read_throughlines(ad, root_id)}
    has_char = "character" in kinds
    has_beat = "pattern" in kinds
    has_payoff = "payoff" in kinds
    if has_char and has_beat and has_payoff:
        return "CHAR_BEAT_PAYOFF", sorted(kinds)
    if has_char and has_beat:
        return "CHAR_BEAT", sorted(kinds)
    return "META_NONE", sorted(kinds)


def decode_meta_theme(ad, token: str) -> dict:
    """Public: decode ONE meta token against the ShapeSignatureMetaTheme codebook.
    The THEME is the decode's verdict (reading_collapse._winner -> the winning
    schema's own `theme` attr)."""
    ensure_codebook(ad)
    res = _decode(ad, token, _META_CODEBOOK_TYPE)
    name, fit = rc._winner(res)
    theme = _schema_attr(ad, _META_CODEBOOK_TYPE, name, "theme") if (name and fit > 0) else None
    line = _schema_attr(ad, _META_CODEBOOK_TYPE, name, "line") if (name and fit > 0) else None
    return {"token": token, "construction": name, "theme": theme, "line": line,
            "shape_fit": max(fit, 0)}


def compose_meta_theme(ad, root_id) -> dict:
    """Compose the whole-story meta-theme from the SET of throughlines threading
    the arcs. The present-kinds token is decoded against the ShapeSignatureMetaTheme
    codebook (the DECIDE); a winning schema's `theme`/`line` is minted as a MetaTheme
    node on the root, threaded (threads_throughline) to every Throughline it composes.
    META_NONE mints nothing (the discriminative null -- one thread alone is not a
    whole-story theme)."""
    ensure_codebook(ad)
    sub, native = _resolve(ad)
    token, kinds = _meta_token(ad, root_id)
    dec = decode_meta_theme(ad, token)
    out = {"root": _v(root_id), "token": token, "kinds": kinds,
           "construction": dec["construction"], "theme": dec["theme"],
           "line": dec["line"], "shape_fit": dec["shape_fit"]}
    if dec["theme"] is None:
        out["minted"] = False
        return out
    threads = read_throughlines(ad, root_id)
    mt = sub.add_node("MetaTheme", {
        "root": _v(root_id), "theme": dec["theme"], "line": dec["line"],
        "construction": dec["construction"], "token": token,
        "kinds": json.dumps(kinds),
        "throughlines": json.dumps([t["node"] for t in threads])})
    root_node = _node_by_v(sub, "StoryUnit", _v(root_id))
    if root_node is not None:
        dc._mint_edge(sub, native, root_node, mt, "has_meta_theme", {"theme": dec["theme"]})
    for t in threads:
        tn = _node_by_v(sub, "Throughline", t["node"])
        if tn is not None:
            dc._mint_edge(sub, native, mt, tn, "threads_throughline", {"kind": t["kind"]})
    out["minted"] = True
    out["node"] = _v(mt)
    return out


def read_meta_theme(ad, root_id=None) -> Optional[dict]:
    sub, _ = _resolve(ad)
    for n in sub.nodes("MetaTheme"):
        at = dict(sub.node(n)["attrs"])
        if root_id is None or at.get("root") == _v(root_id):
            at["node"] = _v(n)
            at["kinds"] = json.loads(at.get("kinds") or "[]")
            return at
    return None


__all__ = ["ensure_codebook", "recognize_throughlines", "read_throughlines",
           "decode_throughline", "compose_meta_theme", "decode_meta_theme",
           "read_meta_theme"]
