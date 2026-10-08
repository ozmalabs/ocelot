"""Typed external causal-claim retrieval boundary.

Workers receive only an immutable topic string and return source-shaped data.
They never inspect or mutate the graph. Graph-owner commit only stages
unverified candidates; native cognition must validate identity and claim
authority before any causal relation can become answer evidence.
"""
from __future__ import annotations

import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlsplit

_API = "https://www.wikidata.org/w/api.php"
_ENTITY_ID = re.compile(r"Q[1-9][0-9]*\Z")
_CAUSE_PROPERTY = "P828"


def _valid_citation_references(value) -> bool:
    """Accept only bounded, typed source citations from the retrieval schema."""
    if not isinstance(value, list) or not value or len(value) > 32:
        return False
    for reference in value:
        if not isinstance(reference, dict) or not reference:
            return False
        if set(reference) - {"P854", "P248"}:
            return False
        for prop, entries in reference.items():
            if not isinstance(entries, list) or not entries or len(entries) > 16:
                return False
            for entry in entries:
                if not isinstance(entry, str) or not entry.strip() or len(entry) > 2048:
                    return False
                if prop == "P854":
                    try:
                        parsed = urlsplit(entry)
                        if (parsed.scheme != "https" or not parsed.hostname
                                or parsed.username or parsed.password):
                            return False
                    except ValueError:
                        return False
                elif not _ENTITY_ID.fullmatch(entry):
                    return False
    return True


def _valid_candidate_payload(payload: dict, topic: str) -> bool:
    source_id = str(payload.get("source_entity_id") or "")
    cause_id = str(payload.get("cause_entity_id") or "")
    source_label = str(payload.get("source_label") or "")
    statement_id = str(payload.get("statement_id") or "")
    return bool(
        payload.get("schema") == "causal_retrieval_candidate.v1"
        and payload.get("provider") == "wikidata"
        and payload.get("query") == topic
        and 0 < len(topic) <= 512
        and len(source_label) <= 512
        and _exact_label_key(source_label) == _exact_label_key(topic)
        and payload.get("property_id") == _CAUSE_PROPERTY
        and payload.get("rank") in {"normal", "preferred"}
        and payload.get("epistemic_status") == "candidate_unverified"
        and payload.get("authority") == "none"
        and _ENTITY_ID.fullmatch(source_id)
        and _ENTITY_ID.fullmatch(cause_id)
        and re.fullmatch(r"Q[1-9][0-9]*\$[A-Za-z0-9-]{1,128}", statement_id)
        and statement_id.startswith(source_id + "$")
        and payload.get("source_url") ==
            "https://www.wikidata.org/wiki/" + source_id
        and _valid_citation_references(payload.get("references"))
    )


def _exact_label_key(value: str) -> str:
    """Normalize only Unicode/case/spacing for exact entity-label matching.

    This narrows an ambiguous search response; it is not an identity proof.
    Candidates still carry ``candidate_unverified`` / ``authority=none`` and
    must be resolved to the graph topic by native cognition before use.
    """
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return " ".join(normalized.casefold().split())


def _http_get(url: str, timeout: int) -> dict:
    from domains.topic_grounding import _http_get as topic_http_get
    return topic_http_get(url, timeout=timeout)


def _json_get(url: str, timeout: int, getter) -> dict | None:
    if not url.startswith("https://www.wikidata.org/"):
        return None
    try:
        result = getter(url, timeout=timeout)
        value = json.loads(result.get("text") or "")
    except Exception:  # noqa: BLE001 -- retrieval failure is unresolved evidence
        return None
    return value if isinstance(value, dict) else None


def _entity_cause_payloads(entity_id: str, query: str, *, timeout: int,
                           getter) -> list[dict]:
    url = (_API + "?action=wbgetentities&ids=" + quote(entity_id)
           + "&props=claims%7Clabels&languages=en&format=json")
    data = _json_get(url, timeout, getter) or {}
    entity = ((data.get("entities") or {}).get(entity_id) or {})
    label = ((entity.get("labels") or {}).get("en") or {}).get("value")
    if (not isinstance(label, str) or not label.strip()
            or _exact_label_key(label) != _exact_label_key(query)):
        return []
    statements = ((entity.get("claims") or {}).get(_CAUSE_PROPERTY) or [])
    candidates = []
    for statement in statements:
        if not isinstance(statement, dict):
            continue
        rank = str(statement.get("rank") or "normal")
        mainsnak = statement.get("mainsnak") or {}
        value = (mainsnak.get("datavalue") or {}).get("value") or {}
        cause_id = str(value.get("id") or "") if isinstance(value, dict) else ""
        if (rank == "deprecated" or mainsnak.get("snaktype") != "value"
                or not _ENTITY_ID.fullmatch(cause_id)):
            continue
        source_refs = []
        for reference in statement.get("references") or []:
            snaks = reference.get("snaks") or {}
            source = {}
            for prop in ("P854", "P248"):
                entries = snaks.get(prop) or []
                vals = []
                for snak in entries:
                    raw = (snak.get("datavalue") or {}).get("value")
                    if isinstance(raw, str) and raw.strip():
                        vals.append(raw.strip())
                    elif isinstance(raw, dict) and raw.get("id"):
                        vals.append(str(raw["id"]))
                if vals:
                    source[prop] = vals
            if source:
                source_refs.append(source)
        # No citation-bearing source record means this remains unusable as
        # externally supported evidence, even if Wikidata contains the claim.
        if not source_refs:
            continue
        statement_id = str(statement.get("id") or "")
        candidates.append({
            "schema": "causal_retrieval_candidate.v1",
            "provider": "wikidata",
            "query": query,
            "source_entity_id": entity_id,
            "source_label": label.strip(),
            "property_id": _CAUSE_PROPERTY,
            "cause_entity_id": cause_id,
            "statement_id": statement_id,
            "rank": rank,
            "references": source_refs,
            "source_url": f"https://www.wikidata.org/wiki/{entity_id}",
            "epistemic_status": "candidate_unverified",
            "authority": "none",
        })
    return candidates


def retrieve_causal_candidate_payloads(topic: str, *, entity_id: str | None = None,
                                       timeout: int = 8,
                                       http_get=None, limit: int = 5) -> list[dict]:
    """Retrieve typed, citation-bearing Wikidata P828 claim candidates.

    This function makes no entity-selection decision and does not claim that a
    candidate denotes the graph topic. Native rules must establish that link;
    generic article summaries are not consulted or returned.
    """
    query = str(topic or "").strip()
    if not query:
        return []
    getter = http_get or _http_get
    if entity_id is not None:
        # Cognition supplies an already-bound identity. Retrieval must not
        # perform entity linking or select between homonymous search results.
        entity_ids = ([str(entity_id)] if _ENTITY_ID.fullmatch(
            str(entity_id)) else [])
    else:
        # Compatibility/data-inspection mode only. Daemon requests are
        # identity-bound and always provide ``entity_id``.
        search_url = (_API + "?action=wbsearchentities&search=" + quote(query)
                      + "&language=en&format=json&limit="
                      + str(max(1, min(10, int(limit)))))
        data = _json_get(search_url, timeout, getter) or {}
        entities = data.get("search") or []
        entity_ids = []
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            candidate_id = str(entity.get("id") or "")
            label = str(entity.get("label") or "")
            if _exact_label_key(label) != _exact_label_key(query):
                continue
            if (_ENTITY_ID.fullmatch(candidate_id)
                    and candidate_id not in entity_ids):
                entity_ids.append(candidate_id)
        entity_ids = entity_ids[:max(1, min(10, int(limit)))]
    if not entity_ids:
        return []

    def retrieve(entity_id: str) -> list[dict]:
        return _entity_cause_payloads(
            entity_id, query, timeout=timeout, getter=getter)

    if http_get is None and len(entity_ids) > 1:
        with ThreadPoolExecutor(max_workers=min(4, len(entity_ids))) as pool:
            grouped = list(pool.map(retrieve, entity_ids))
    else:
        grouped = [retrieve(entity_id) for entity_id in entity_ids]
    return [candidate for group in grouped for candidate in group]


def commit_causal_candidate_payloads(agent, request, payloads: list[dict], *,
                                     io_token: str | None = None) -> int:
    """Stage data-only candidates on the graph owner; never assert a cause."""
    native, substrate = agent.inner, agent.s
    if not native.has_node(request):
        return 0
    attrs = dict(substrate.node(request)["attrs"])
    if attrs.get("schema") != "causal_retrieval_request.v1":
        return 0
    if attrs.get("status") != "running":
        return 0
    if io_token is not None and attrs.get("causal_io_token") != io_token:
        return 0
    topic = str(attrs.get("topic") or "").strip()
    topic_entity_id = str(attrs.get("topic_entity_id") or "")
    if not topic:
        return 0
    staged = 0
    for payload in payloads or []:
        if (not isinstance(payload, dict)
                or not _valid_candidate_payload(payload, topic)
                or not _ENTITY_ID.fullmatch(topic_entity_id)
                or payload.get("source_entity_id") != topic_entity_id):
            continue
        candidate = substrate.add_node("CausalRetrievalCandidate", dict(payload))
        native.add_edge_unchecked(request, "has_candidate", candidate)
        citation_count = sum(
            len(entries)
            for reference in payload["references"]
            for entries in reference.values())
        native.set_attr(candidate, "citation_count", citation_count)
        staged += 1
    native.set_attr(request, "candidate_count", staged)
    native.set_attr(request, "status", "candidates_staged" if staged else "failed")
    native.set_attr(request, "evidence_path", (
        "CausalRetrievalRequest -> has_candidate -> citation_bearing_P828"
        if staged else "CausalRetrievalRequest -> retrieval -> no_supported_candidates"))
    return staged


__all__ = ["commit_causal_candidate_payloads",
           "retrieve_causal_candidate_payloads"]
