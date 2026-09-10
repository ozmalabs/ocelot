"""Mechanical loader for the LANGUAGE-AGNOSTIC communication concepts seed.

Installs seeds/communication_concepts.json as graph data: a `communication`
Microtheory + one Concept node per communicative function (the stative/'be'
cluster, participant roles, speech functions, logical operators, reference/
quantification), each carrying its participant ROLES. These are the universal
concepts a language SERIALIZES; the grammar is taught to map surface forms onto
them (the renderer / W_j principle). NO surface words, no decisions — a JSON->
graph install, idempotent. World-adapter mechanics only.

RE-AUTHORED (block 334000) as an ADDITIVE seed-builder. The module was removed
with the python-core purge so it could not be accidentally re-used as decision
logic; this restoration is deliberately scoped to the mechanical materialization
ONLY (JSON -> Microtheory/Concept/SourceEvent nodes + has_concept/has_event/
built_from edges). It holds NO decision logic, is imported by NOTHING on any
auto-load / daemon / core path, and only runs when a script explicitly calls
install_communication_concepts_seed(substrate). The reader side it feeds
(source_provenance.context_for / _source_events / _compose_trust, and the
SourceEvent/has_event node+edge types) is already live in the checkout; only
this writer was missing, which is why several scripts import it. The timeline ->
SourceEvent materialization (_install_source_timelines) is what unlocks the
time-sliced DERIVED trust band for a temporal source-entity (e.g. `qwen3`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_SEED = Path(__file__).resolve().parent.parent / "seeds" / \
    "communication_concepts.json"


def install_communication_concepts_seed(substrate, path: Path = _SEED) -> Any:
    """JSON -> Microtheory('communication') + Concept nodes (kind/gloss/roles)
    + has_concept edges. Idempotent (skips a concept whose name already exists).
    Returns the microtheory node id (or None on a read failure)."""
    try:
        data = json.loads(Path(path).read_text())
    except Exception:
        return None

    mt_name = data.get("microtheory", "communication")
    mt = None
    for nid in substrate.nodes("Microtheory"):
        if substrate.node(nid)["attrs"].get("name") == mt_name:
            mt = nid
            break
    if mt is None:
        try:
            mt = substrate.add_node("Microtheory",
                                    {"name": mt_name, "origin": "communication_concepts"})
        except Exception:
            mt = None

    by_name = {substrate.node(c)["attrs"].get("name"): c
               for c in substrate.nodes("Concept")}
    stats = {"created": 0, "linked": 0}
    # Extra DECLARATIVE attrs a concept may carry beyond the universal four. The
    # SOURCE/provenance concepts (source/reference_work/encyclopedia/wikipedia)
    # hold their RELIABILITY, their genre CONVENTIONS, and a PROVENANCE template
    # as graph DATA the agent reads — persisted verbatim so the held
    # understanding (NOT a Python constant) drives the read + the epistemic
    # weight. Stored as JSON for the dict-valued ones (like `structure`).
    _extra_str = ("reliability", "combination", "default_name",
                  "default_owner", "default_trust")
    _extra_json = ("conventions", "provenance", "timeline")
    for c in data.get("concepts", []):
        name = c.get("name")
        if not name:
            continue
        cid = by_name.get(name)
        if cid is None:
            # genuinely MISSING prime -> create it as the basis concept.
            try:
                attrs = {
                    "name": name,
                    "kind": c.get("kind", ""),
                    "definition": c.get("gloss", ""),
                    "roles": json.dumps(c.get("roles", [])),
                    "category": "communication_concept",
                    "language_agnostic": 1,
                }
                # A concept may carry an explicit STRUCTURE the agent HOLDS as
                # graph data (e.g. `definition` carries its genus-differentia
                # parse structure — the markers comprehension reads). Persist it
                # verbatim so the held understanding drives the application.
                if c.get("structure") is not None:
                    attrs["structure"] = json.dumps(c["structure"])
                for k in _extra_str:
                    if c.get(k) is not None:
                        attrs[k] = str(c[k])
                for k in _extra_json:
                    if c.get(k) is not None:
                        attrs[k] = json.dumps(c[k])
                cid = substrate.add_node("Concept", attrs)
                by_name[name] = cid
                stats["created"] += 1
            except Exception:
                continue
        else:
            # the prime already exists (often in a domain seed) -> LINK it into
            # the basis rather than duplicate; tag it so the grammar can find it.
            try:
                a = substrate.node(cid)["attrs"]
                if not a.get("comm_prime"):
                    substrate.set_attr(cid, "comm_prime", c.get("kind", ""))
                # carry an explicit STRUCTURE onto a pre-existing concept too.
                if c.get("structure") is not None and not a.get("structure"):
                    substrate.set_attr(cid, "structure", json.dumps(c["structure"]))
                for k in _extra_str:
                    if c.get(k) is not None and not a.get(k):
                        substrate.set_attr(cid, k, str(c[k]))
                for k in _extra_json:
                    if c.get(k) is not None and not a.get(k):
                        substrate.set_attr(cid, k, json.dumps(c[k]))
                stats["linked"] += 1
            except Exception:
                pass
        # link into the communication microtheory (the single grammar target).
        if mt is not None and cid is not None:
            try:
                substrate.add_edge(mt, "has_concept", cid)
            except Exception:
                pass
    # GROUND the concepts that declare a `built_from` (the is-a chain): the
    # SOURCE/provenance cluster grounds wikipedia is-a encyclopedia is-a
    # reference_work is-a source, bottoming out at the epistemic primitives
    # (knowledge/belief). This makes the agent's UNDERSTANDING of what an
    # encyclopedia / Wikipedia IS structural (grounded), not just a gloss — the
    # same admissible Concept->Concept built_from edge grounded_representation
    # opens. Done in a second pass so every part concept already exists.
    try:
        from domains import grounded_representation as _gr
        _gr.open_grounding_productions(substrate)
        idx = {substrate.node(c)["attrs"].get("name"): c
               for c in substrate.nodes("Concept")}
        for c in data.get("concepts", []):
            parts = c.get("built_from")
            name = c.get("name")
            if name and isinstance(parts, list) and parts:
                _gr.ground_concept(substrate, name, parts,
                                   c.get("combination"), index=idx,
                                   create_missing=True)
    except Exception:
        pass
    # MATERIALIZE the TIMELINE of a temporal source-entity as graph data: each
    # dated event becomes a SourceEvent node carrying its WHEN + state-changes,
    # linked to the source by has_event, and GROUNDED (built_from) in the concepts
    # it grounds in — so the agent IMPLIES the web by FOLLOWING grounding edges
    # from an in-cone event (musk -> finance, politics; an incident -> public_
    # trust), not from a hand-fed summary. The event is a grounded FACT (an input);
    # the time-sliced CONTEXT is composed over these by source_provenance.context_
    # for. World-adapter mechanics: a JSON->graph install, no decision.
    try:
        _install_source_timelines(substrate, data)
    except Exception:
        pass
    try:
        substrate.set_attr(mt, "basis_stats", json.dumps(stats))
    except Exception:
        pass
    return mt


def _install_source_timelines(substrate, data: dict) -> int:
    """For each seeded concept carrying a `timeline`, materialize its dated
    EVENTS as SourceEvent graph nodes: a node per event with its WHEN + kind +
    label + any state it sets (sets_name / sets_owner) + the trust signal, linked
    from the source by `has_event`, and grounded (built_from) in each concept it
    grounds_in (created if missing — they are seeded concepts). Idempotent on the
    event id. Returns the number of events installed."""
    from domains import grounded_representation as _gr
    _gr.open_grounding_productions(substrate)
    # admit the source -has_event-> SourceEvent + SourceEvent -built_from-> Concept
    for prod in (
        {"src": {"type": "Concept", "var": "s"}, "edge_type": "has_event",
         "tgt": {"type": "SourceEvent", "var": "e"}, "where": None,
         "provenance": "communication_concepts:timeline"},
        {"src": {"type": "SourceEvent", "var": "e"}, "edge_type": "built_from",
         "tgt": {"type": "Concept", "var": "c"}, "where": None,
         "provenance": "communication_concepts:timeline"},
    ):
        try:
            substrate.add_production(prod)
        except Exception:
            pass
    by_name = {substrate.node(c)["attrs"].get("name"): c
               for c in substrate.nodes("Concept")}
    existing = {substrate.node(e)["attrs"].get("event_id")
                for e in substrate.nodes("SourceEvent")}
    n = 0
    for c in data.get("concepts", []):
        tl = c.get("timeline")
        sname = c.get("name")
        if not isinstance(tl, dict) or not sname:
            continue
        sid = by_name.get(sname)
        if sid is None:
            continue
        for ev in tl.get("events", []):
            eid = ev.get("id")
            if not eid or eid in existing:
                continue
            attrs = {"name": eid, "event_id": eid, "when": ev.get("when", ""),
                     "kind": ev.get("kind", ""), "label": ev.get("label", ""),
                     "source": sname, "origin": "communication_concepts"}
            for k in ("sets_name", "sets_owner"):
                if ev.get(k) is not None:
                    attrs[k] = str(ev[k])
            if ev.get("trust_relevant"):
                attrs["trust_relevant"] = 1
                attrs["trust_dir"] = int(ev.get("trust_dir", 0))
            try:
                enode = substrate.add_node("SourceEvent", attrs)
            except Exception:
                continue
            existing.add(eid)
            n += 1
            try:
                substrate.add_edge(sid, "has_event", enode)
            except Exception:
                pass
            # GROUND the event in the concepts it grounds_in (built_from) — this
            # is the web the agent FOLLOWS to imply the context.
            for gname in ev.get("grounds_in", []):
                gid = by_name.get(gname)
                if gid is None:
                    try:
                        gid = substrate.add_node(
                            "Concept", {"name": gname,
                                        "origin": "communication_concepts"})
                        by_name[gname] = gid
                    except Exception:
                        continue
                try:
                    substrate.add_edge(enode, "built_from", gid)
                except Exception:
                    pass
    return n
