"""self_model — the FULL SELF-MODEL MIRROR: every rule the agent holds (not
just the chosen_action-writing subset `reflective_faculty._ensure_acting_
rule_provenance` mirrors for the acting-variant composer), plus every
graph-resident Program, as queryable `RuleSummary` / `ProgramSummary` nodes —
and the SELF-QUERY handlers ('what does <rule> do?', 'which rules ... about
<topic>?', 'which parts of me touch <attr>?') that read them.

WHY a SEPARATE mirror rather than widening `_ensure_acting_rule_provenance`:
CLAUDE.md scopes this slice to UNDERSTANDING (a complete, speakable self-model)
and `domains/reflective_faculty.py` is owned by another concurrent edit right
now (composer/experiment-dispatch work) — this module must not touch that
file. It SHARES the `RuleSummary` node type + the `name` idempotency key with
the acting mirror on purpose: whichever mint runs first, the other's later
pass upgrades the SAME node to the union of both field sets (see
`ensure_rule_provenance`'s docstring) — the acting composer's Argmax over
`writes_chosen_action`/`shift_count`/`shiftable`/`rule_json` keeps working
unmodified, now over a fuller inventory (chosen_action-writers plus
everything else) instead of a disjoint one.

Pure mechanical structural reads over `export_rules()`'s own JSON dialect
(match edges / where Term-tree / effects array) and over graph-resident
`Program` nodes' own Term-tree — no interpretation of what a rule MEANS, only
what it matches / reads / writes, exactly the spirit of
`reflective_faculty._find_threshold_lits`. No agent decisions in this file:
`ensure_rule_provenance`/`ensure_program_provenance` are idempotent mirrors;
`run_self_model_rule`/`run_self_model_topic`/`run_self_model_touches` are
graph lookups (exact-name / substring overlap), never a fabricated answer.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

_RULE_SUMMARY_TYPE = "RuleSummary"
_PROGRAM_SUMMARY_TYPE = "ProgramSummary"
_SELF_PROCESS_TYPE = "SelfProcess"
_ROOT = Path(__file__).resolve().parent.parent
_SEED_DIR = _ROOT / "seeds"


# ---------------------------------------------------------------------------
# resolve (substrate, native) from whatever the caller passed — the SAME duck
# typing `reflective_faculty._resolve_agent` uses, kept LOCAL (not imported)
# so this module carries zero runtime coupling to a file under concurrent
# edit; if that file's shape changes mid-edit, this module is unaffected.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _content_hash(obj: Any) -> str:
    try:
        blob = json.dumps(obj, sort_keys=True, default=str)
    except Exception:
        blob = str(obj)
    return hashlib.sha1(blob.encode("utf-8", "replace")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# MECHANICAL STRUCTURAL READS over export_rules()'s JSON dialect (see
# runners/dsl/src/py.rs `rule_to_json`/`effect_to_json`: match = [[src_var,
# edge_type, tgt_var], ...]; where = a Term-JSON tree or null; effects = an
# array of [kind, ...args] arrays). Local reimplementation of the
# `_find_threshold_lits` shape (kept local for the same concurrent-edit
# isolation reason as `_resolve` above).
# ---------------------------------------------------------------------------
def _match_text(match_edges: Any) -> str:
    parts = []
    for me in (match_edges or []):
        if isinstance(me, (list, tuple)) and len(me) == 3:
            parts.append(f"{me[0]} -{me[1]}-> {me[2]}")
    return "; ".join(parts)


_READ_KEYS = ("key", "attr_key")           # Attr/EdgeAttr.key, NodesWhere.attr_key
_TYPE_KEYS = ("edge_type", "node_type")    # Edges/NodesOfType.*, NodesWhere.node_type


def _collect_reads(node: Any, keys_out: set, types_out: set) -> None:
    if isinstance(node, dict):
        for rk in _READ_KEYS:
            v = node.get(rk)
            if isinstance(v, str) and v:
                keys_out.add(v)
        for tk in _TYPE_KEYS:
            v = node.get(tk)
            if isinstance(v, str) and v:
                types_out.add(v)
        for v in node.values():
            _collect_reads(v, keys_out, types_out)
    elif isinstance(node, list):
        for v in node:
            _collect_reads(v, keys_out, types_out)


def _reads_text(where_json: Any) -> str:
    """The attrs/edge-types a rule's `where` clause references — a
    structural walk of the Term-JSON tree, collecting every Attr/EdgeAttr
    `key`, NodesWhere `attr_key`, and every Edges/NodesOfType/NodesWhere
    type name reachable. No meaning read from them, only which exist."""
    keys, types = set(), set()
    _collect_reads(where_json, keys, types)
    parts = []
    if keys:
        parts.append("attrs: " + ", ".join(sorted(keys)))
    if types:
        parts.append("types: " + ", ".join(sorted(types)))
    return " | ".join(parts)


_EFFECT_NODE_ADD = ("add_node", "add_node_if_absent")
_EFFECT_EDGE_ADD = ("add_edge",)
_EFFECT_EDGE_DEL = ("del_edge",)
_EFFECT_NODE_DEL = ("del_node",)
_EFFECT_SET = ("set_attr", "set_attr_if_different")
_EFFECT_KNOWN = _EFFECT_NODE_ADD + _EFFECT_EDGE_ADD + _EFFECT_EDGE_DEL + _EFFECT_NODE_DEL + _EFFECT_SET


def _effects_summary(effects: Any) -> tuple[str, set]:
    """Mechanical read of the effects array: which node TYPES get added,
    which ATTR KEYS get set, which EDGE TYPES get added/removed, whether any
    node gets deleted. Returns (writes_text, set_attr_keys) — the latter so
    callers can test 'does this rule write attr X' without re-parsing text."""
    added_nodes, set_attrs, added_edges, deled_edges = set(), set(), set(), set()
    n_deled_nodes, other_kinds = 0, set()
    for e in (effects or []):
        if not isinstance(e, list) or not e:
            continue
        kind = e[0]
        if kind in _EFFECT_NODE_ADD and len(e) >= 3:
            added_nodes.add(str(e[2]))
        elif kind in _EFFECT_EDGE_ADD and len(e) >= 4:
            added_edges.add(str(e[2]))
        elif kind in _EFFECT_EDGE_DEL and len(e) >= 4:
            deled_edges.add(str(e[2]))
        elif kind in _EFFECT_NODE_DEL:
            n_deled_nodes += 1
        elif kind in _EFFECT_SET and len(e) >= 3:
            set_attrs.add(str(e[2]))
        elif isinstance(kind, str):
            other_kinds.add(kind)
    parts = []
    if added_nodes:
        parts.append("adds " + ", ".join(sorted(added_nodes)))
    if set_attrs:
        parts.append("sets " + ", ".join(sorted(set_attrs)))
    if added_edges:
        parts.append("adds edges " + ", ".join(sorted(added_edges)))
    if deled_edges:
        parts.append("removes edges " + ", ".join(sorted(deled_edges)))
    if n_deled_nodes:
        parts.append(f"deletes {n_deled_nodes} node(s)")
    if other_kinds:
        parts.append("other: " + ", ".join(sorted(other_kinds)))
    return "; ".join(parts), set_attrs


def _find_threshold_lits(node: Any) -> list:
    """Mechanical recursive scan (mirrors reflective_faculty's own, kept
    local for concurrent-edit isolation): collect every {"type": "Lt"|"Gt",
    "b": {"type": "Lit", "value": <numeric>}} node reachable — the decision
    thresholds a rule's own effects compare against."""
    out: list = []

    def walk(n):
        if isinstance(n, dict):
            if n.get("type") in ("Lt", "Gt"):
                b = n.get("b")
                if isinstance(b, dict) and b.get("type") == "Lit":
                    v = b.get("value")
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        out.append(n)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(node)
    return out


# ---------------------------------------------------------------------------
# SEED INDEX — mechanical name->seed_id map, reusing the boot loader's
# content-hashed compact pre-pass. This avoids a second full-corpus manifest
# scan while retaining both native `rules:[{name,...}]` and encyclopedic
# `nodes:[{type:'Rule',attrs:{name}}]` declarations.
# ---------------------------------------------------------------------------
def _build_seed_rule_index(seed_dir: Optional[str] = None, *,
                           validated_index: Optional[dict] = None) -> dict:
    if validated_index is not None:
        return validated_index
    from substrate.boot_all import _read_seed_rule_name_index

    return _read_seed_rule_name_index(str(seed_dir or _SEED_DIR))


# ---------------------------------------------------------------------------
# THE FULL RULE MIRROR
# ---------------------------------------------------------------------------
def ensure_rule_provenance(agent, *, seed_dir: Optional[str] = None,
                           validated_seed_rule_index: Optional[dict] = None) -> dict:
    """Idempotent: mirror EVERY rule in `native.export_rules()` — active or
    not, chosen_action-writer or not — as one graph-resident `RuleSummary`
    {name, active, keywords_text, match_text, reads_text, writes_text,
    writes_chosen_action, from_seed, shift_count, shiftable, batch,
    match_type, rule_json, content_hash} node. Shares the node type + `name`
    key with `reflective_faculty._ensure_acting_rule_provenance`'s narrower
    (chosen_action-only) mirror by design: whichever runs first mints a
    node under that name, the other's later pass (this function, since it
    always compares `content_hash`) UPGRADES it to carry the full field set
    — the acting composer's own Argmax (which reads `writes_chosen_action`
    / `shift_count` / `shiftable` / `rule_json`, computed here identically)
    keeps working unmodified, now over the union of both mirrors.

    REFRESHES an existing RuleSummary in place (via `set_attr`, comparing
    `content_hash` against the rule's own exported JSON) so an agent-authored
    rule change (add_rule mid-session, a threshold-shifted variant, a
    tombstoned/reactivated rule) is picked up on the next call — never
    stale, never re-minted as a duplicate.

    SECOND PASS — GRAPH-RESIDENT Rule NODES (added for the composer-graph
    migration; see domains/reflective_faculty.py's `_try_graph_composer` /
    seeds/composer_*_graph.json): `native.export_rules()` only enumerates the
    STRUCT rule store (`Substrate::rules`) — a meta-rule like
    `compose_control_graph` that mints its children live via
    `run_graph_rules` never appears there (it's never `__mint__`'d itself),
    so the FIRST pass above never mirrors it, and 'what does
    compose_control_graph do?' would come back honestly-not-found forever.
    This second pass walks every graph-resident `type="Rule"` node
    (`sub.nodes("Rule")`) and mirrors any whose `id` is NOT already covered
    by a struct-store name from THIS SAME call — the meta-rules themselves,
    plus any minted child that is graph-live but not (yet, or ever, per
    `test_mint_is_acceleration_not_requirement`) compiled into the struct
    store. A child rule that HAS been `__mint__`'d is covered by the first
    pass already (same `name`/`id` value) and is deliberately SKIPPED here —
    one RuleSummary per logical rule, never two disagreeing mirrors of the
    same rule. Uses the graph-node dialect (`id`/`match`/`where`/`effect`,
    singular) but the SAME structural readers (`_match_text`/`_reads_text`/
    `_effects_summary`/`_find_threshold_lits`) as the struct-store pass —
    the two dialects share the same match-edge-list / Term-JSON / effect-
    tuple-list shapes (see runners/dsl/src/graph_rules.rs's module docstring),
    so one reader works over both. Returns {total, minted, updated, unchanged,
    struct_total, graph_total} — the first four are the UNION of both passes
    (kept as the primary return shape for existing callers); the last two
    break the union down for callers that care which population changed."""
    sub, native = _resolve(agent)
    # Exact-query indexes are snapshots of RuleSummary attributes.  A
    # provenance refresh may update an existing summary in place as well as
    # mint new ones, so invalidate any adapter-local snapshot before touching
    # the graph.
    try:
        setattr(agent, "_rule_summary_lookup_index", None)
    except Exception:
        pass
    try:
        rules = native.export_rules()
    except Exception as e:
        return {"total": 0, "minted": 0, "updated": 0, "unchanged": 0,
                "wall": f"export_rules unavailable: {type(e).__name__}: {e}"}

    # `name` is NOT a unique key in `export_rules()`'s own output: a small
    # number of rule SLOTS (observed: satisfy_goal / mark_self /
    # choose_safe_action / vit_step / vit_backtrace — two genuinely different
    # match/effects bodies sharing one name, a pre-existing property of the
    # rule store, not introduced here) collide on bare name. Full coverage
    # (one RuleSummary per SLOT, so the mirror's node count equals
    # `len(export_rules())` exactly — the gate's coverage assertion) needs a
    # key that survives that: `(name, occurrence-rank)`, rank = how many
    # times this name has been seen so far in iteration ORDER (stable across
    # calls: `export_rules()` walks the rule store in stored slot order,
    # which position-shifting elsewhere doesn't reorder). A `name` alone stays
    # the queryable/search field; ambiguity is surfaced honestly (see
    # `_find_rule_summary` / `run_self_model_rule`), never silently collapsed.
    existing: dict = {}
    for n in sub.nodes(_RULE_SUMMARY_TYPE):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if not nm:
            continue
        rank = at.get("name_rank")
        key = (nm, int(rank) if isinstance(rank, (int, float)) else 0)
        existing.setdefault(key, (n, at))

    seed_idx = _build_seed_rule_index(
        seed_dir, validated_index=validated_seed_rule_index)
    from collections import Counter
    name_counts = Counter(r.get("name") for r in rules if isinstance(r, dict) and r.get("name"))
    seen_rank: dict = {}
    minted = updated = unchanged = 0
    for r in rules:
        if not isinstance(r, dict):
            continue
        name = r.get("name")
        if not name:
            continue
        rank = seen_rank.get(name, 0)
        seen_rank[name] = rank + 1
        ambiguous = name_counts[name] > 1
        chash = _content_hash(r)
        key = (name, rank)
        if key in existing and existing[key][1].get("content_hash") == chash:
            # The exported body is the cache key for every derived structural
            # field below. Avoid walking the nested Where/effect trees or
            # serializing a RuleSummary again when no supported rule edit has
            # occurred. This keeps refresh idempotent without making the
            # summary stale: authored changes produce a different hash.
            unchanged += 1
            continue
        match_text = _match_text(r.get("match"))
        reads_text = _reads_text(r.get("where"))
        writes_text, written_attrs = _effects_summary(r.get("effects"))
        thresholds = _find_threshold_lits(r.get("effects"))
        attrs = {
            "name": name,
            "name_rank": float(rank),
            "ambiguous_name": 1.0 if ambiguous else 0.0,
            "active": 1.0 if r.get("active", True) else 0.0,
            "keywords_text": name.replace("_", " "),
            "match_text": match_text,
            "reads_text": reads_text,
            "writes_text": writes_text,
            "writes_chosen_action": 1.0 if "chosen_action" in written_attrs else 0.0,
            "from_seed": seed_idx.get(name, ""),
            "shift_count": float(len(thresholds)),
            "shiftable": 1.0 if thresholds else 0.0,
            "batch": 1.0 if r.get("batch") else 0.0,
            "match_type": r.get("match_type") or "",
            "rule_json": json.dumps(r),
            "content_hash": chash,
        }
        if key in existing:
            nid, _old = existing[key]
            for k, v in attrs.items():
                try:
                    sub.set_attr(nid, k, v)
                except Exception:
                    pass
            updated += 1
        else:
            try:
                sub.add_node(_RULE_SUMMARY_TYPE, attrs)
                minted += 1
            except Exception:
                pass

    # --- SECOND PASS: graph-resident Rule nodes not covered by export_rules() ---
    struct_names = {r.get("name") for r in rules if isinstance(r, dict) and r.get("name")}
    try:
        graph_rule_nodes = sub.nodes("Rule")
    except Exception:
        graph_rule_nodes = []
    graph_only = []
    for nid in graph_rule_nodes:
        at = sub.node(nid)["attrs"]
        rid = at.get("id")
        if not rid or rid in struct_names:
            continue   # already mirrored by the struct-store pass above (same logical rule)
        graph_only.append((nid, at, rid))
    from collections import Counter as _Counter
    name_counts_g = _Counter(rid for _, _, rid in graph_only)
    seen_rank_g: dict = {}
    graph_total = graph_minted = graph_updated = graph_unchanged = 0
    for nid, at, rid in graph_only:
        graph_total += 1
        rank = seen_rank_g.get(rid, 0)
        seen_rank_g[rid] = rank + 1
        ambiguous = name_counts_g[rid] > 1
        rule_like = {"name": rid, "match": at.get("match"), "where": at.get("where"),
                     "effects": at.get("effect")}
        chash = _content_hash(rule_like)
        key = (rid, rank)
        if key in existing and existing[key][1].get("content_hash") == chash:
            graph_unchanged += 1
            continue
        match_text = _match_text(at.get("match"))
        reads_text = _reads_text(at.get("where"))
        writes_text, written_attrs = _effects_summary(at.get("effect"))
        thresholds = _find_threshold_lits(at.get("effect"))
        g_attrs = {
            "name": rid,
            "name_rank": float(rank),
            "ambiguous_name": 1.0 if ambiguous else 0.0,
            "active": 1.0,   # a graph Rule node has no separate active/inactive concept
            "keywords_text": rid.replace("_", " "),
            "match_text": match_text,
            "reads_text": reads_text,
            "writes_text": writes_text,
            "writes_chosen_action": 1.0 if "chosen_action" in written_attrs else 0.0,
            "from_seed": seed_idx.get(rid, ""),
            "shift_count": float(len(thresholds)),
            "shiftable": 1.0 if thresholds else 0.0,
            "batch": 1.0 if at.get("batch") else 0.0,
            "match_type": at.get("match_type") or "",
            "rule_json": json.dumps(rule_like, default=str),
            "content_hash": chash,
            "graph_resident": 1.0,        # distinguishes a graph-native meta-rule/rule from a
            "graph_node_id": str(nid),    # struct-store one in the shared RuleSummary population
        }
        if key in existing:
            enid, _old = existing[key]
            for k, v in g_attrs.items():
                try:
                    sub.set_attr(enid, k, v)
                except Exception:
                    pass
            graph_updated += 1
        else:
            try:
                sub.add_node(_RULE_SUMMARY_TYPE, g_attrs)
                graph_minted += 1
            except Exception:
                pass

    return {"total": len(rules) + graph_total, "minted": minted + graph_minted,
            "updated": updated + graph_updated, "unchanged": unchanged + graph_unchanged,
            "struct_total": len(rules), "graph_total": graph_total}


# ---------------------------------------------------------------------------
# THE PROGRAM/TERM MIRROR — the same shape for graph-resident `Program` nodes
# (see reflective_faculty.teach_program, READ ONLY: {name, program: <Term-
# tree JSON string>, form}).
# ---------------------------------------------------------------------------
def _program_keywords(term_json: Any) -> str:
    ops: set = set()

    def walk(n):
        if isinstance(n, dict):
            t = n.get("type")
            if isinstance(t, str):
                ops.add(t.lower())
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(term_json)
    return " ".join(sorted(ops))


def ensure_program_provenance(agent) -> dict:
    """Idempotent: mirror every graph-resident `Program` node as one
    `ProgramSummary`{name, description, keywords_text, op_count, form,
    content_hash} — the Program/Term twin of `ensure_rule_provenance`.
    `keywords_text` is the SET of Term op-names the program's own JSON
    contains (a structural read, not an interpretation of what the ops
    compute) plus the program's own name words, so a topic search over
    RuleSummary + ProgramSummary uses the same StringIndexOf-style overlap.
    Returns {total, minted, updated, unchanged}."""
    sub, _native = _resolve(agent)
    existing: dict = {}
    for n in sub.nodes(_PROGRAM_SUMMARY_TYPE):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if nm and nm not in existing:
            existing[nm] = (n, at)

    minted = updated = unchanged = total = 0
    for pn in sub.nodes("Program"):
        at = sub.node(pn)["attrs"]
        name = at.get("name")
        if not name:
            continue
        total += 1
        prog_raw = at.get("program")
        try:
            term = json.loads(prog_raw) if isinstance(prog_raw, str) else prog_raw
        except Exception:
            term = None
        kw = _program_keywords(term) if term is not None else ""
        chash = _content_hash({"name": name, "program": prog_raw, "form": at.get("form")})
        attrs = {
            "name": name,
            "description": str(at.get("description") or at.get("form") or ""),
            "keywords_text": (name.replace("_", " ") + " " + kw).strip(),
            "op_count": float(len(kw.split())) if kw else 0.0,
            "form": str(at.get("form") or ""),
            "content_hash": chash,
        }
        if name in existing:
            nid, old = existing[name]
            if old.get("content_hash") == chash:
                unchanged += 1
                continue
            for k, v in attrs.items():
                try:
                    sub.set_attr(nid, k, v)
                except Exception:
                    pass
            updated += 1
        else:
            try:
                sub.add_node(_PROGRAM_SUMMARY_TYPE, attrs)
                minted += 1
            except Exception:
                pass
    return {"total": total, "minted": minted, "updated": updated, "unchanged": unchanged}


def ensure_self_model(agent, *, seed_dir: Optional[str] = None,
                      validated_seed_rule_index: Optional[dict] = None) -> dict:
    """Refresh BOTH mirrors (rules + programs). The one call a booted agent
    or a post-add_rule caller needs."""
    return {"rules": ensure_rule_provenance(
                agent, seed_dir=seed_dir,
                validated_seed_rule_index=validated_seed_rule_index),
            "programs": ensure_program_provenance(agent)}


# ---------------------------------------------------------------------------
# SELF-QUERY ANSWERING — reflect()-shaped handlers: (substrate, meta_arg) ->
# a state dict, the SAME signature every function in reflective_faculty.
# _DISPATCH already has (see e.g. `_run_self_organisation`). Pure graph
# lookups over the mirrors above; a name/topic/attr that matches NOTHING
# returns an honest not-found state, never a fabricated nearest-neighbour.
# ---------------------------------------------------------------------------
def _norm_name(s: Optional[str]) -> str:
    return re.sub(r"\s+", "_", (s or "").strip())


def _find_rule_summaries(sub, meta_arg: Optional[str]) -> list:
    """EXACT lookup only (name, after space->underscore normalisation, or an
    exact keywords_text match) — deliberately not a fuzzy/overlap search: a
    query naming no real rule must come back honest (see
    `run_self_model_rule`'s docstring), never a nearest guess. Returns EVERY
    match (usually 0 or 1; occasionally 2+ — a small number of rule NAMES are
    genuinely ambiguous in the rule store itself, two distinct match/effects
    bodies sharing one name; see `ensure_rule_provenance`'s comment. Ordered
    by `name_rank` so callers report them in a stable, deterministic order."""
    return _find_rule_summaries_many(sub, [meta_arg]).get(meta_arg, []) if meta_arg else []


def _find_rule_summaries_many(sub, meta_args) -> dict:
    """Resolve multiple exact rule queries in one graph pass.

    This preserves `_find_rule_summaries`' name-or-keywords equality and
    stable name-rank ordering, while avoiding repeated full RuleSummary scans
    when a parsed utterance has several candidate gap tokens.
    """
    return _find_rule_summaries_many_indexed(
        sub, meta_args, index=_build_rule_summary_exact_index(sub))


def _build_rule_summary_exact_index(sub) -> dict:
    """Snapshot the two exact lookup fields used by reflexive parsing.

    Retain only node identities, not a duplicate Python attrs dict for every
    RuleSummary.  Matching remains exact; attributes are read from the graph
    only for actual hits. Callers that retain the index must invalidate it
    after a RuleSummary refresh.
    """
    by_name = {}
    by_keywords = {}
    for node in sub.nodes(_RULE_SUMMARY_TYPE):
        attrs = sub.node(node)["attrs"]
        name = attrs.get("name")
        rank = attrs.get("name_rank", 0.0)
        if not isinstance(rank, (int, float)):
            rank = 0.0
        if name:
            by_name.setdefault(name, []).append((rank, node))
        keywords = (attrs.get("keywords_text") or "").strip().lower()
        if keywords:
            by_keywords.setdefault(keywords, []).append((rank, node))
    for rows in (*by_name.values(), *by_keywords.values()):
        rows.sort(key=lambda row: row[0])
    return {
        "name": {key: tuple(node for _rank, node in rows)
                 for key, rows in by_name.items()},
        "keywords": {key: tuple(node for _rank, node in rows)
                     for key, rows in by_keywords.items()},
    }


def _find_rule_summaries_many_indexed(sub, meta_args, *, index) -> dict:
    """Perform the batched exact query over a prebuilt summary index."""
    queries = {}
    for arg in meta_args:
        if arg:
            queries[arg] = (_norm_name(arg), arg.strip().lower())
    if not queries:
        return {}
    hits = {arg: [] for arg in queries}
    by_name = index.get("name", {}) if isinstance(index, dict) else {}
    by_keywords = index.get("keywords", {}) if isinstance(index, dict) else {}
    for arg, (guess, kw) in queries.items():
        seen = set()
        for node in (*by_name.get(guess, ()),
                     *by_keywords.get(kw, ())):
            if node not in seen:
                hits[arg].append((node, sub.node(node)["attrs"]))
                seen.add(node)
    for rows in hits.values():
        rows.sort(key=lambda t: t[1].get("name_rank", 0.0))
    return hits


def _describe_rule_summary(at: dict) -> str:
    parts = [f"my rule {at['name']!r} is " + ("active" if at.get("active") else "inactive")]
    parts.append(f"it fires when {at['match_text']}" if at.get("match_text")
                 else "it fires with no match edges (a where-only / always rule)")
    if at.get("reads_text"):
        parts.append(f"it reads {at['reads_text']}")
    if at.get("writes_text"):
        parts.append(f"it writes {at['writes_text']}")
    if at.get("from_seed"):
        parts.append(f"it comes from the {at['from_seed']!r} seed")
    return "; ".join(parts) + "."


def run_self_model_rule(substrate, meta_arg: Optional[str]) -> dict[str, Any]:
    """SELF-QUERY: 'what does <rule> do?' — states the facts `ensure_rule_
    provenance` mirrored straight off `export_rules()`'s own JSON (its match
    edges, its where-clause reads, its effects' writes). Never fabricates: a
    name with no matching RuleSummary returns an honest not-found; a name
    that names TWO distinct rule bodies (an ambiguous name in the rule store
    itself — a discovered property, not fabricated) states BOTH, honestly."""
    hits = _find_rule_summaries(substrate, meta_arg)
    if not hits:
        note = (f"I don't have a rule named {meta_arg!r} in my self-model "
                "(no RuleSummary matches it — honest, not a guess)")
        return {"note": note, "found": False,
                "self_model_query": "rule", "queried": meta_arg}
    if len(hits) > 1:
        note = (f"I hold {len(hits)} DIFFERENT rules named {hits[0][1]['name']!r} "
                "(an ambiguous name in my own rule store): "
                + " || ".join(_describe_rule_summary(at) for _, at in hits))
        return {"note": note, "found": True, "ambiguous": True, "count": len(hits),
                "rule_name": hits[0][1]["name"],
                "self_model_query": "rule", "queried": meta_arg}
    _, at = hits[0]
    note = _describe_rule_summary(at)
    # `note` FIRST: `_surface_self_state`'s generic fallback (world_adapter.py,
    # a file this task must not edit) renders only `list(state.items())[:6]`,
    # so the full composed sentence must be among the first keys or a rich
    # rule (many reads/writes) truncates before its `note` is ever reached.
    return {"note": note, "found": True, "rule_name": at["name"],
            "match": at.get("match_text"), "reads": at.get("reads_text"),
            "writes": at.get("writes_text"),
            "self_model_query": "rule", "queried": meta_arg,
            "active": bool(at.get("active")), "from_seed": at.get("from_seed")}


def _rule_search_blob(at: dict) -> str:
    return " ".join(str(at.get(k) or "") for k in
                     ("keywords_text", "from_seed", "match_text", "reads_text", "writes_text")).lower()


def run_self_model_topic(substrate, meta_arg: Optional[str]) -> dict[str, Any]:
    """SELF-QUERY: 'which rules do you have about <topic>?' — a StringIndexOf
    -style substring overlap of the topic words against every RuleSummary's
    own keywords/seed/match/reads/writes text (the SAME cheap overlap shape
    the seed-pick / acting-variant Argmax already uses elsewhere in this
    codebase; here it LISTS every match instead of picking one)."""
    topic = (meta_arg or "").strip().lower()
    words = [w for w in topic.replace("_", " ").split() if w]
    if not words:
        return {"note": "no topic words to search for", "count": 0, "matches": [],
                "self_model_query": "topic", "queried": meta_arg}
    hits = []
    for n in substrate.nodes(_RULE_SUMMARY_TYPE):
        at = substrate.node(n)["attrs"]
        blob = _rule_search_blob(at)
        if any(w in blob for w in words):
            nm = at.get("name")
            if nm:
                hits.append(nm)
    hits = sorted(set(hits))
    shown = hits[:12]
    note = (f"I have {len(hits)} rule(s) about {meta_arg!r}: "
            + (", ".join(shown) if shown else "none")
            + (", ..." if len(hits) > len(shown) else ""))
    # `note` FIRST — see `run_self_model_rule`'s comment (the world_adapter.py
    # rendering fallback this must flow through only shows the first 6 keys).
    return {"note": note, "count": len(hits), "matches": hits[:40],
            "self_model_query": "topic", "queried": meta_arg}


def _token_hit(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    return re.search(r"\b" + re.escape(needle) + r"\b", haystack) is not None


def run_self_model_touches(substrate, meta_arg: Optional[str]) -> dict[str, Any]:
    """SELF-QUERY: 'which parts of me touch <attr>?' — every RuleSummary
    whose `reads_text`/`writes_text` NAMES the attr (an exact token match
    against the 'attrs: a, b, c' / 'sets a, b' fields `ensure_rule_
    provenance` wrote, checked in both the raw form and the space-normalised
    form so 'chosen_action' and 'chosen action' both hit)."""
    attr_us = _norm_name(meta_arg).lower()
    attr_sp = (meta_arg or "").strip().lower()
    readers, writers = set(), set()
    for n in substrate.nodes(_RULE_SUMMARY_TYPE):
        at = substrate.node(n)["attrs"]
        rt = (at.get("reads_text") or "").lower()
        wt = (at.get("writes_text") or "").lower()
        nm = at.get("name")
        if not nm:
            continue
        if _token_hit(rt, attr_us) or _token_hit(rt, attr_sp):
            readers.add(nm)
        if _token_hit(wt, attr_us) or _token_hit(wt, attr_sp):
            writers.add(nm)
    readers_l, writers_l = sorted(readers), sorted(writers)
    total = sorted(readers | writers)
    note = (f"{len(total)} part(s) of me touch {meta_arg!r}: "
            f"{len(writers_l)} write it ({', '.join(writers_l[:8]) or 'none'}), "
            f"{len(readers_l)} read it ({', '.join(readers_l[:8]) or 'none'})")
    # `note` FIRST — see `run_self_model_rule`'s comment.
    return {"note": note, "count": len(total), "writers": writers_l[:40],
            "readers": readers_l[:40],
            "self_model_query": "touches", "queried": meta_arg}


# ---------------------------------------------------------------------------
# OPERATIONAL SELF-INTROSPECTION — how the agent OPERATES (its processes:
# learning, perceiving, world-attachment), distinct from how it IS
# (self_organisation, microtheories) and how it is SHAPED (self_shape,
# meta-shapes). A "how do you <verb>" process-question about a self-process the
# agent HOLDS a true self-account for reads that account here. The accounts are
# TAUGHT DATA (SelfProcess nodes, persisted by domains.teach), grounded in the
# real architecture (the collapse loop, the sd loop, the world adapter) — never
# a fabricated mechanism. A process the agent has NO held account for never
# reaches this reader: comprehend_text keeps the honest "I can't say precisely"
# floor for it (find_self_process returns None -> no self_process routing).
# ---------------------------------------------------------------------------
def _process_aliases(at: dict) -> set:
    """The words that name this held SelfProcess — its canonical `process`, its
    primary `verb`, and every alias/inflection it declares (a comma- or space-
    separated string, or a list). Pure structural read of the node's own attrs."""
    als: set = set()
    for k in ("process", "verb"):
        v = at.get(k)
        if isinstance(v, str) and v.strip():
            als.add(v.strip().lower())
    raw = at.get("aliases")
    if isinstance(raw, str):
        for a in raw.replace(",", " ").split():
            if a.strip():
                als.add(a.strip().lower())
    elif isinstance(raw, list):
        for a in raw:
            if isinstance(a, str) and a.strip():
                als.add(a.strip().lower())
    return als


def find_self_process(substrate, tokens) -> Optional[str]:
    """BOUNDARY CLASSIFIER (read-only): does the agent HOLD a self-account for any
    of the process words in `tokens` (a 'how do you <verb>' question's content
    words)? Returns the canonical `process` of the matching held SelfProcess node
    — a real graph read, never a guess — or None when nothing is held (then the
    caller keeps the honest floor). Only a genuinely held SelfProcess matches; a
    process the agent has no true self-account for returns None."""
    if substrate is None or not tokens:
        return None
    toks = {str(t).strip(",.;:?!").lower() for t in tokens}
    toks.discard("")
    if not toks:
        return None
    for n in substrate.nodes(_SELF_PROCESS_TYPE):
        at = substrate.node(n)["attrs"]
        proc = at.get("process")
        if not isinstance(proc, str) or not proc:
            continue
        if _process_aliases(at) & toks:
            return proc
    return None


def run_self_process(substrate, meta_arg: Optional[str]) -> dict[str, Any]:
    """SELF-QUERY: 'how do you <process>?' — states the TRUE self-account the
    agent HOLDS for that operational process (a SelfProcess node's `account`,
    taught from the real architecture: learning = the collapse loop, perceiving
    = the sd decode loop, world-attachment = the adapter ingest). Never
    fabricates — an unheld process normally never reaches here (comprehend_text
    routes it to the honest floor instead); if one does, an honest floor is
    returned rather than an invented mechanism."""
    key = (meta_arg or "").strip().lower()
    for n in substrate.nodes(_SELF_PROCESS_TYPE):
        at = substrate.node(n)["attrs"]
        if (at.get("process") or "").strip().lower() == key or key in _process_aliases(at):
            note = at.get("account")
            if isinstance(note, str) and note.strip():
                # `note` FIRST — the world_adapter.py rendering fallback this flows
                # through renders the faculty's own prose `note` (see
                # `run_self_model_rule`'s comment).
                return {"note": note.strip(), "found": True,
                        "self_process_query": at.get("process"),
                        "source": str(at.get("source") or "")}
    return {"note": f"I can't say precisely how I {meta_arg}." if meta_arg
            else "I can't say precisely how that comes about.",
            "found": False, "self_process_query": meta_arg}


# ---------------------------------------------------------------------------
# RUNTIME DISPATCH REGISTRATION — `domains/reflective_faculty.py` is under
# concurrent edit by another agent right now (CLAUDE.md/task constraint), so
# this module must not touch its bytes. `reflect()`'s routing table
# (`_DISPATCH`) is a plain module-level dict; registering into it from
# OUTSIDE that file (a dict mutation, not a file edit) wires these three
# meta-targets into the SAME seam `self_organisation`/`self_shape` already
# use (`substrate/world_adapter.py`'s `answer_question` -> `_rf.reflect(mt,
# ..., self.s)` for any `mt in _rf._DISPATCH`) without changing a single byte
# of reflective_faculty.py. Wrapped in try/except + `setdefault` (never
# clobbers an existing entry) so it degrades to a harmless no-op — self-model
# questions simply stay unwired — if `_DISPATCH` is ever renamed/removed by
# that concurrent edit, rather than crashing the boot.
#
# THE PERMANENT FIX (once that edit lands, if this runtime patch is ever
# considered too clever to keep): add these three lines directly to
# reflective_faculty.py's `_DISPATCH` dict literal instead of calling
# `register_self_model_dispatch()`:
#     "self_model_rule": self_model.run_self_model_rule,
#     "self_model_topic": self_model.run_self_model_topic,
#     "self_model_touches": self_model.run_self_model_touches,
# ---------------------------------------------------------------------------
def register_self_model_dispatch() -> bool:
    try:
        from domains import reflective_faculty as _rf
    except Exception:
        return False
    try:
        _rf._DISPATCH.setdefault("self_model_rule", run_self_model_rule)
        _rf._DISPATCH.setdefault("self_model_topic", run_self_model_topic)
        _rf._DISPATCH.setdefault("self_model_touches", run_self_model_touches)
        _rf._DISPATCH.setdefault("self_process", run_self_process)
        return True
    except Exception:
        return False


register_self_model_dispatch()
