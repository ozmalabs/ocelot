"""source_provenance — read the agent's HELD understanding of a SOURCE off the
graph, and attach PROVENANCE (WHERE/WHO/HOW/WHAT/WHEN + the source's epistemic
status) to what it grounds by reading.

The principle: a competent reader knows WHAT they are reading. Reading "a
manifold is a topological space" IN WIKIPEDIA is different from reading it on a
tweet — understanding what Wikipedia IS frames the read (the LEAD is the
definition, 'In <field>,' is the domain frame) AND sets the EPISTEMIC WEIGHT
(consensus-tertiary: more than conjecture, attributed not derived, reliable for
established knowledge). Knowledge is frame-relative AND source-relative — where
it came from is part of what it means and how firmly it's held.

This is a WORLD-ADAPTER reader (CLAUDE.md): it makes NO decision about meaning.
It reads the SOURCE-understanding the agent HOLDS as graph DATA — the
`wikipedia` / `encyclopedia` Concept nodes seeded by
seeds/communication_concepts.json with their `provenance` template, `conventions`
structure, and `reliability` level — and hands those held values to the read /
grounding step. The reliability/conventions are READ OFF the held concepts, NOT
hardcoded numbers in Python (the only Python here is the JSON-from-attr read).

  · provenance_for_source(substrate, source) -> the held provenance template
    {source, genre, who, how, when, epistemic_status, reliability} (+ where
    filled per-read). Read off the held `<source>` Concept's `provenance` attr.
  · conventions_for_source(substrate, source) -> the genre CONVENTIONS the read
    consults (lead_defines, domain_preface) — read off the source's genus
    (its is-a chain: wikipedia is-a encyclopedia, which HOLDS the conventions).
  · epistemic_status_for_source(substrate, source) -> the {status, weight}
    grounding carries from this source (consensus/attested vs derived vs
    conjecture) — read off the held `reliability` level (a qualitative band,
    mapped to the held grounded/conjecture confidence constants, no new band).

HONEST scope (named, not hidden):
  · ONE source is modeled — Wikipedia (others — a primary paper, a tweet —
    later, the same way: seed the genre + reliability, read it off here).
  · `reliability` is a HELD QUALITATIVE LEVEL ('consensus_tertiary'), not a
    learned number; who/how are COARSE tags; the band is two-and-a-bit levels
    (reusing conjecture.py's grounded/hop constants, no parallel band invented).
"""
from __future__ import annotations

import json
from typing import Any, Optional


# A reference SOURCE label (the wiki_local `source` field / a route store name)
# -> the held Concept NAME that carries the agent's understanding of it. Coarse
# label-match (the only place a source string meets a concept name); the
# UNDERSTANDING itself is all held graph data. 'local_wiki' is the wiki_local
# store tag; 'wikipedia'/'web' are the route-store labels.
def _source_concept_name(source: str) -> Optional[str]:
    low = (source or "").lower()
    if "wiki" in low:           # local_wiki / wikipedia / web_world (wikipedia)
        return "wikipedia"
    # MATH reference databases (the cmsg102 source-by-kind registry) — the held
    # `oeis` / `lmfdb` Concepts carry the provenance template, mirroring wikipedia.
    if "oeis" in low:
        return "oeis"
    if "lmfdb" in low:
        return "lmfdb"
    # a TEMPORAL source-entity: a tweet / an X post resolves to twitter_x (the
    # SAME surface form across time — the WHEN, not the label, picks the state).
    if any(k in low for k in ("twitter", "tweet", "x_post", "x post", "xpost")) \
            or low == "x":
        return "twitter_x"
    # a GENERATIVE source — a language model. Reaped LLM content resolves to the
    # held `<model>` Concept, which carries the generative-source provenance +
    # a CALIBRATED reliability band below an attested reference (block 331: an
    # LLM is a self-published synthetic source, not a consensus-tertiary one).
    if "qwen3" in low or low == "qwen":
        return "qwen3"
    if any(k in low for k in ("language_model", "language model", "llm",
                              "generative_source", "generative source")):
        return "language_model"
    return None


def _find_concept(substrate, name: str):
    if substrate is None or not name:
        return None
    try:
        for c in substrate.nodes("Concept"):
            if substrate.node(c)["attrs"].get("name") == name:
                return c
    except Exception:
        return None
    return None


def _load_json_attr(substrate, cid, key: str) -> Optional[dict[str, Any]]:
    try:
        raw = substrate.node(cid)["attrs"].get(key)
        if isinstance(raw, str) and raw.strip():
            v = json.loads(raw)
            return v if isinstance(v, dict) else None
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# PROVENANCE — the WHERE/WHO/HOW/WHAT/WHEN the agent HOLDS for a source.
# ---------------------------------------------------------------------------

def provenance_for_source(substrate, source: str, *,
                          where: Optional[str] = None) -> Optional[dict[str, Any]]:
    """The PROVENANCE template the agent HOLDS for `source`, read off the held
    `<source>` Concept's `provenance` attr (graph data seeded in
    communication_concepts.json), with WHERE filled per-read (the article title
    — the location of the knowledge). Returns {source, genre, who, how, where,
    when, epistemic_status, reliability} or None when the source is not held /
    not modeled (HONEST: only Wikipedia is modeled so far).

    NOT a Python constant — the who/how/when/genre/reliability are READ from the
    held concept; only WHERE (the per-article location) is filled by the caller.
    Provenance is part of grounding: this is what gets attached to a grounded
    fact so the agent knows what it read."""
    cname = _source_concept_name(source)
    cid = _find_concept(substrate, cname) if cname else None
    if cid is None:
        return None
    prov = _load_json_attr(substrate, cid, "provenance")
    if prov is None:
        return None
    out = {k: v for k, v in prov.items() if not str(k).startswith("_")}
    if where:
        out["where"] = where
    out.setdefault("where", None)
    return out


# ---------------------------------------------------------------------------
# CONVENTIONS — how to READ the source (the lead IS the definition, 'In <field>,'
# IS the domain frame). Read off the source's GENRE (its is-a genus), so the
# behaviour is the agent applying its UNDERSTANDING of the genre, not a constant.
# ---------------------------------------------------------------------------

def _genus_chain(substrate, cid, max_hops: int = 6) -> list:
    """The is-a / built_from chain from `cid` upward (wikipedia -> encyclopedia
    -> reference_work -> source), so the genre that HOLDS the conventions is
    reachable from the specific source."""
    chain = [cid]
    cur = cid
    for _ in range(max_hops):
        try:
            nxt = list(substrate.neighbours(cur, "built_from"))
        except Exception:
            nxt = []
        if not nxt:
            break
        cur = nxt[0]
        chain.append(cur)
    return chain


def conventions_for_source(substrate, source: str) -> Optional[dict[str, Any]]:
    """The genre CONVENTIONS the read consults — {lead_defines, domain_preface,
    ...} — read off the source's GENRE (its is-a genus that HOLDS them). Walks
    wikipedia -> encyclopedia and reads `encyclopedia`'s `conventions` attr. So
    'the lead IS the definition' / ''In <field>,' IS the domain frame' is
    JUSTIFIED BY the held understanding of the genre, not an unexplained Python
    constant. Returns None when no held source/genre carries conventions."""
    cname = _source_concept_name(source)
    cid = _find_concept(substrate, cname) if cname else None
    if cid is None:
        return None
    for node in _genus_chain(substrate, cid):
        conv = _load_json_attr(substrate, node, "conventions")
        if conv is not None:
            return {k: v for k, v in conv.items() if not str(k).startswith("_")}
    return None


# ---------------------------------------------------------------------------
# EPISTEMIC STATUS — the trust the grounding carries FROM this source. Read off
# the held `reliability` level; mapped to the held grounded/conjecture
# confidence constants (no new band invented).
# ---------------------------------------------------------------------------

# The held qualitative RELIABILITY level -> {status, confidence}. consensus-
# tertiary (an encyclopedia) is ATTESTED/CONSENSUS: more than a conjecture,
# attributed (not self-derived), reliable for established knowledge. It maps to
# the held GROUNDED_HOP (a hop that still commits but below a self-derived 1.0)
# — an ATTESTED grounding is firmly held but DISTINCT from a fact the agent
# derived itself. A coarse, honest band reusing conjecture.py's constants.
def _reliability_band(reliability: str) -> dict[str, Any]:
    try:
        from domains import conjecture as _cj
        full = float(_cj.grounded_confidence())
        hop = float(_cj.GROUNDED_HOP)
    except Exception:
        full, hop = 1.0, 0.9
    r = (reliability or "").lower()
    if r in ("consensus_tertiary", "reliable_for_established", "consensus"):
        return {"status": "consensus", "confidence": hop,
                "why": ("attested by a consensus-tertiary reference — held more "
                        "firmly than a conjecture, attributed (not self-derived), "
                        "reliable for established knowledge / weaker on the "
                        "obscure-recent-contested")}
    # a GENERATIVE (self-published, calibrated) source — a language model. Below
    # an attested reference: it is a confident CROWD-COMPRESSION, not consensus,
    # and its content must be corroborated before it asserts alone. The
    # confidence sits at the self-published baseline (between the attested hop
    # and a conjecture) — the SAME midpoint `_compose_trust` uses for a
    # self-published platform. Per-tier trust (knowledge > concept > process) is
    # carried on the REAPED EDGES (block 332), not smeared into this source-wide
    # band; the band is the ceiling a corroborated LLM claim can reach here.
    if r in ("self_published_calibrated", "self_published_variable",
             "self_published", "generative_calibrated", "generative"):
        base = 0.5 if hop > 0.5 else hop * 0.5
        return {"status": "self_published",
                "confidence": round(base, 4),
                "why": ("a generative (self-published, calibrated) source — a "
                        "confident crowd-compression BELOW an attested reference; "
                        "corroborate before it asserts alone; per-tier trust is "
                        "carried on the reaped edges, not this source-wide band")}
    # an unrecognised reliability -> treat as attested-but-unweighted (still a
    # source, distinct from a self-derived fact). Honest fall-through.
    return {"status": "attested", "confidence": hop,
            "why": f"attested by source (reliability '{reliability}')"}


def epistemic_status_for_source(substrate, source: str,
                                when: Optional[str] = None
                                ) -> Optional[dict[str, Any]]:
    """The EPISTEMIC STATUS a grounding READ FROM `source` carries: {status,
    confidence, reliability, why}. Read off the held `<source>` (or its genus)
    `reliability` level, mapped to the held grounded/conjecture confidence band.
    'consensus' (an encyclopedia) is distinct from a self-DERIVED grounding
    (1.0) and from a CONJECTURE (~0.1). Returns None when no held source carries
    a reliability. The number is NOT hardcoded per-source in Python — it is read
    off the held qualitative level.

    TIME-INDEXED: when `source` is a TEMPORAL ENTITY (has a timeline) the status
    is DERIVED + time-sliced via context_for(source, when) — the trust composed
    over the trust-relevant events UP TO `when`, so a 2024 X post reads
    'contested' where a 2015 tweet does not. A flat-genre source (Wikipedia)
    keeps the held reliability band (no regression)."""
    cname = _source_concept_name(source)
    cid = _find_concept(substrate, cname) if cname else None
    if cid is None:
        return None
    # TEMPORAL source -> the time-sliced DERIVED trust (composed, not a constant).
    try:
        if substrate.neighbours(cid, "has_event"):
            ctx = context_for(substrate, source, when)
            if ctx is not None and ctx.get("temporal"):
                tr = ctx.get("trust", {})
                return {"status": tr.get("status"),
                        "confidence": tr.get("weight"),
                        "reliability": ctx.get("reliability"),
                        "when": ctx.get("when"),
                        "why": ("DERIVED + time-sliced: trust composed over the "
                                "trust-relevant events in the cone up to "
                                f"{ctx.get('when')} "
                                f"(lowering: {tr.get('lowering_events')})"),
                        "context": ctx}
    except Exception:
        pass
    reliability = None
    for node in _genus_chain(substrate, cid):
        r = substrate.node(node)["attrs"].get("reliability")
        if isinstance(r, str) and r.strip():
            reliability = r
            break
    if reliability is None:
        return None
    band = _reliability_band(reliability)
    band["reliability"] = reliability
    return band


# ---------------------------------------------------------------------------
# TIME-INDEXED CONTEXT — a source's context is the GROUNDING CONE of the source
# ENTITY, TIME-SLICED to the artifact's date. NOT a flat held tag: it is DERIVED
# by composing the entity's dated EVENTS (grounded facts) up to WHEN — the name
# at that time, the owner at that time, the IMPLIED concept set (the union of the
# in-cone events' grounding cones — the web the agent FOLLOWS), and a DERIVED
# trust composed over the trust-relevant events in the cone (NOT a constant).
# A 2015 tweet and a 2024 X post derive DIFFERENT contexts from the SAME surface.
# ---------------------------------------------------------------------------

def _norm_when(when: Optional[str]) -> Optional[str]:
    """An ISO-ish date string normalised for lexical comparison (which is also
    chronological for zero-padded ISO dates). Pads a bare year ('2015' ->
    '2015-01-01') / year-month so a coarse artifact date still slices the
    timeline. Returns None when no usable date."""
    if not isinstance(when, str) or not when.strip():
        return None
    s = when.strip()[:10]
    parts = s.replace("/", "-").split("-")
    try:
        y = f"{int(parts[0]):04d}"
    except Exception:
        return None
    mo = f"{int(parts[1]):02d}" if len(parts) > 1 and parts[1].isdigit() else "01"
    da = f"{int(parts[2]):02d}" if len(parts) > 2 and parts[2].isdigit() else "01"
    return f"{y}-{mo}-{da}"


def _event_grounded_concepts(substrate, enode) -> list:
    """The names of the concepts a SourceEvent is GROUNDED in (built_from) — the
    event's own cone of meaning (musk_acquisition -> elon_musk/finance/politics;
    grok_mechahitler -> ai_output_incident/public_trust/politics). Read off the
    graph; this is what a per-dimension relevance gate matches an artifact against
    (an event is relevant to an artifact iff their concepts overlap)."""
    out = []
    try:
        for g in substrate.neighbours(enode, "built_from"):
            nm = substrate.node(g)["attrs"].get("name")
            if nm:
                out.append(nm)
    except Exception:
        return out
    return sorted(set(out))


def _source_events(substrate, sid) -> list:
    """The SourceEvent nodes of source `sid` (has_event), each as
    {node, when, kind, label, sets_name, sets_owner, trust_relevant, trust_dir,
    concepts}, sorted chronologically by `when`. Read off the graph (materialized
    timeline). `concepts` = the event's grounded concepts (its built_from cone)."""
    out = []
    try:
        evs = list(substrate.neighbours(sid, "has_event"))
    except Exception:
        evs = []
    for e in evs:
        a = substrate.node(e)["attrs"]
        w = _norm_when(a.get("when"))
        out.append({"node": e, "when": w, "raw_when": a.get("when"),
                    "kind": a.get("kind"), "label": a.get("label"),
                    "id": a.get("event_id") or a.get("name"),
                    "sets_name": a.get("sets_name"),
                    "sets_owner": a.get("sets_owner"),
                    "trust_relevant": bool(a.get("trust_relevant")),
                    "trust_dir": int(a.get("trust_dir") or 0),
                    "concepts": _event_grounded_concepts(substrate, e)})
    out.sort(key=lambda d: (d["when"] or ""))
    return out


# The DERIVED trust band — composed over the trust-relevant events IN the cone.
# It is a coarse MONOTONE: start at the source's baseline (self_published for a
# social platform), and each trust-relevant event in the cone moves the weight
# in its trust_dir. The numeric weight reuses the held grounded/conjecture
# confidence constants (no parallel band invented); the qualitative LABEL is
# composed, NOT hand-set ('contested' once trust-lowering events have entered).
def _trust_constants():
    try:
        from domains import conjecture as _cj
        hop = float(_cj.GROUNDED_HOP)            # ~0.9, a committing hop
        conj = float(_cj.EPSILON)               # ~0.1, a conjecture's weight
    except Exception:
        hop, conj = 0.9, 0.1
    return hop, conj


def _compose_trust(in_cone_events: list, baseline: Optional[str]) -> dict:
    """DERIVE the trust/epistemic-weight by composing over the trust-relevant
    events in the cone. baseline = the source's default_trust label. Each trust-
    lowering (trust_dir<0) event in the cone drops the weight one coarse step;
    trust-raising events lift it. The qualitative status is COMPOSED from the
    count of trust-lowering events that have entered the cone — 'contested' once
    any has — NOT a hand-set constant. Returns {status, weight, lowering_events,
    raising_events, baseline}."""
    hop, conj = _trust_constants()
    # self-published baseline weight sits between an attested hop and a conjecture.
    base_w = 0.5 if (baseline or "").startswith("self_published") else hop
    lowering = [e for e in in_cone_events if e["trust_relevant"] and e["trust_dir"] < 0]
    raising = [e for e in in_cone_events if e["trust_relevant"] and e["trust_dir"] > 0]
    net = len(raising) - len(lowering)
    # one coarse step per trust event, bounded to [conj, hop].
    step = (hop - conj) / 4.0
    weight = max(conj, min(hop, base_w + net * step))
    if lowering and net < 0:
        status = "contested"
    elif raising and net > 0:
        status = "elevated"
    else:
        status = baseline or "self_published"
    return {"status": status, "weight": round(weight, 4),
            "lowering_events": [e["id"] for e in lowering],
            "raising_events": [e["id"] for e in raising],
            "baseline": baseline}


def context_for(substrate, source: str, when: Optional[str] = None,
                *, where: Optional[str] = None) -> Optional[dict[str, Any]]:
    """DERIVE the TIME-SLICED CONTEXT of an artifact from `source` dated `when`:
    the grounding cone of the source ENTITY composed over the events with
    when <= the artifact's when. Returns

        {source, name, owner, when, in_cone_events, future_events, implied,
         trust:{status, weight, ...}, reliability, epistemic_status, provenance,
         temporal: bool}

    DERIVED, not hand-fed:
      · `name`   — the name the entity had at `when` (latest sets_name event in
        the cone; the default_name before any) — Twitter pre-rename, X after.
      · `owner`  — the owner at `when` (latest sets_owner event in the cone;
        default_owner before any) — Dorsey-era pre-2022, Musk after.
      · `implied` — the IMPLIED concept set: the UNION of the grounding cones of
        the in-cone events (the agent FOLLOWS built_from edges from each event —
        musk -> finance/politics, an incident -> public_trust — so the web is
        IMPLIED, not summarised). A future event (when > the date) is NOT in the
        cone, so its groundings are NOT pulled in.
      · `trust`  — COMPOSED over the trust-relevant events in the cone (declining
        as moderation / verification / incident events enter), NOT a constant.

    For a source with NO timeline (Wikipedia-as-encyclopedia) this falls back to
    the FLAT held context: the provenance template + the held reliability's
    epistemic status, with `temporal=False` (no dramatic timeline -> stable
    context — the no-regression case)."""
    cname = _source_concept_name(source)
    cid = _find_concept(substrate, cname) if cname else None
    if cid is None:
        return None
    a = substrate.node(cid)["attrs"]
    prov = provenance_for_source(substrate, source, where=where)
    epi = epistemic_status_for_source(substrate, source)
    reliability = a.get("reliability")

    events = _source_events(substrate, cid)
    if not events:
        # NON-temporal source (no timeline) — the FLAT held context (no regression).
        return {"source": cname, "name": a.get("default_name") or cname,
                "owner": a.get("default_owner"), "when": _norm_when(when),
                "temporal": False, "in_cone_events": [], "future_events": [],
                "implied": sorted(_static_implied(substrate, cid)),
                "trust": ({"status": (epi or {}).get("status", reliability),
                           "weight": (epi or {}).get("confidence"),
                           "baseline": reliability}),
                "reliability": reliability, "epistemic_status": epi,
                "provenance": prov}

    nw = _norm_when(when)
    # if no artifact date is given, treat as the PRESENT (the whole timeline is in
    # the cone) — the honest default; a dated artifact slices it.
    cutoff = nw if nw is not None else (events[-1]["when"] or "9999-12-31")
    in_cone = [e for e in events if (e["when"] or "") <= cutoff]
    future = [e for e in events if (e["when"] or "") > cutoff]

    # NAME / OWNER at WHEN — the latest state-setting event in the cone.
    name = a.get("default_name") or cname
    owner = a.get("default_owner")
    for e in in_cone:
        if e["sets_name"]:
            name = e["sets_name"]
        if e["sets_owner"]:
            owner = e["sets_owner"]

    # IMPLIED SET — FOLLOW the grounding edges of the in-cone events (the cone of
    # each event), unioned. This is the web the agent IMPLIES from first
    # principles, not a hand-fed summary. A future event's groundings are absent.
    try:
        from domains import grounded_representation as _gr
        event_ids = {e["id"] for e in events}
        implied: set[str] = set()
        for e in in_cone:
            for m in _gr.cone(substrate, e["node"], "built_from"):
                node = substrate.node(m)
                # the IMPLIED CONCEPT web — not the event nodes themselves (an
                # event is in its own cone); the agent follows built_from to the
                # grounded CONCEPTS (musk, finance, politics, public_trust, ...).
                if node["type"] == "SourceEvent":
                    continue
                nm = node["attrs"].get("name")
                if nm and nm != cname and nm not in event_ids:
                    implied.add(nm)
    except Exception:
        implied = set()

    trust = _compose_trust(in_cone, a.get("default_trust") or reliability)

    return {"source": cname, "name": name, "owner": owner, "when": nw,
            "temporal": True,
            "in_cone_events": [{"id": e["id"], "when": e["raw_when"],
                                "kind": e["kind"], "label": e["label"],
                                "concepts": e["concepts"],
                                "trust_relevant": e["trust_relevant"]}
                               for e in in_cone],
            "future_events": [{"id": e["id"], "when": e["raw_when"],
                               "kind": e["kind"]} for e in future],
            "implied": sorted(implied), "trust": trust,
            "reliability": reliability, "epistemic_status": epi,
            "provenance": prov}


def _static_implied(substrate, cid) -> set:
    """The implied set for a NON-temporal source = its own grounding cone (its
    genre chain), so even the flat case carries its built_from web."""
    try:
        from domains import grounded_representation as _gr
        out = set()
        for m in _gr.cone(substrate, cid, "built_from"):
            nm = substrate.node(m)["attrs"].get("name")
            if nm:
                out.add(nm)
        return out
    except Exception:
        return set()


__all__ = [
    "provenance_for_source",
    "conventions_for_source",
    "epistemic_status_for_source",
    "context_for",
]
