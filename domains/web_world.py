"""web_world — a simplified WEB reference interface (Wikipedia + arXiv) the
agent can consult as ``epistemic_access`` REFERENCE routes.

A WORLD ADAPTER (CLAUDE.md), the same shape as ``dictionary_lexicon`` /
``wiktionary_reference``: it translates an external reference (the live web)
into substrate mutations. The only thing it does is FETCH external text and
GROUND it as graph data (a Concept carrying the extract as a definition, plus
a KnownFact when an off-path banked gap is resolved). There are NO agent
decisions over graph state here — the comprehension / epistemic-access stack
(which is graph-resident) decides WHAT to look up and WHEN; this module is the
mechanical I/O at the boundary.

Two sources:

  * WIKIPEDIA — the REST summary endpoint + the search API. Both WORK with a
    descriptive User-Agent header (verified). Responses are cached to
    ``data/web_cache/wikipedia/<title>.json`` (gitignored) so a repeated
    lookup never re-hits the network. This is the reliable reference.

  * arXiv — the export API. BEST-EFFORT only: it has timed out in this
    sandbox before, so every call is wrapped in a short timeout and degrades
    gracefully (returns [] and reports "arxiv unreachable") — it NEVER blocks
    the agent's loop. When it does answer, it returns paper titles + abstracts.

The unified entry the epistemic_access REFERENCE route calls is
``web_lookup(query, kind)``: it tries Wikipedia (and arXiv if asked) and
returns the best ``{source, text, url}`` extract, or None.

Wiring into ``epistemic_access`` (see ``reference_lookup_for`` + the
conversation-world hookup): when a banked gap's route is a REFERENCE and the
LOCAL stores (WordNet / Wiktionary) can't supply it, the resolver falls through
to ``web_lookup`` and grounds the result. So "I know how to get it -> reference
-> the web" actually resolves off the social path, and a LATER turn can answer
the question with NO question put to the audience.

HONEST framing (stated plainly, not hidden):
  * Wikipedia is reliable here; arXiv is best-effort / often unreachable in
    this sandbox — the caller is told which source actually returned data.
  * Grounding a Wikipedia extract is NOT deep reading: it attaches the summary
    text to a Concept as a ``definition`` (and, for a banked gap, mints a
    KnownFact carrying the extract). It grows the agent's referenceable
    knowledge; it does not parse the article.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

# Cache the fetched web extracts under the gitignored data/ dir (same
# discipline as wiktionary_reference's kaikki cache).
_ROOT = Path(__file__).resolve().parent.parent
_CACHE_DIR = _ROOT / "data" / "web_cache" / "wikipedia"

# A descriptive User-Agent — Wikipedia's REST + action APIs require one (a
# bare urllib UA gets a 403). This identifies the research agent honestly.
_USER_AGENT = "gamma-substrate-agent/0.1 (research; world-adapter)"

# LOCAL-ONLY mode: when True, the on-disk Wikipedia dump is AUTHORITATIVE — a
# title absent from the local store is a definitive miss, NOT a reason to hit the
# network. The frozen 20231101.en dump IS our Wikipedia; a batch grounding run
# (e.g. the encyclopedic campaign) sets this so a miss returns instantly instead
# of a multi-second HTTP round-trip (a nonsense title was costing ~1-20s of
# retries). Default False: live callers keep the network fallback.
LOCAL_ONLY = False


def set_local_only(flag: bool = True) -> None:
    """Make the on-disk Wikipedia dump authoritative (no network fallback)."""
    global LOCAL_ONLY
    LOCAL_ONLY = bool(flag)

_WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_WIKI_SEARCH = ("https://en.wikipedia.org/w/api.php?action=query&list=search"
                "&srsearch={q}&format=json&srlimit={n}")
_ARXIV_QUERY = ("https://export.arxiv.org/api/query?search_query=all:{q}"
                "&start=0&max_results={n}")

# arXiv is best-effort: a SHORT timeout so a hang never blocks the agent loop.
_ARXIV_TIMEOUT = 8
_WIKI_TIMEOUT = 15

# Last arXiv reachability verdict, so a host/test can report it honestly.
_arxiv_last_reachable: Optional[bool] = None


def _request(url: str, timeout: int) -> Optional[bytes]:
    """GET ``url`` with the descriptive UA. Returns the body bytes, or None on
    any failure (network error / non-200 / timeout). Never raises."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Wikipedia — search + summary (cached).
# ---------------------------------------------------------------------------


def _cache_path(title: str) -> Path:
    """A filesystem-safe cache path for a title's summary JSON."""
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", title)[:180] or "_"
    return _CACHE_DIR / f"{safe}.json"


def wikipedia_search(query: str, limit: int = 5) -> list[str]:
    """Search Wikipedia, returning a list of matching page titles (best first).

    Mechanical I/O: hits the action search API with the descriptive UA. Returns
    [] on any failure (offline / no match) — the caller degrades gracefully."""
    if not query:
        return []
    # LOCAL store first (the HF 20231101.en dump) — no network. HTTP is fallback.
    try:
        from domains import wiki_local as _wl
        if _wl.present():
            hits = _wl.search(query, limit)
            if hits:
                return hits
            if LOCAL_ONLY:
                return []   # local dump authoritative — a miss is a miss
    except Exception:
        pass
    if LOCAL_ONLY:
        return []
    q = urllib.parse.quote(query)
    body = _request(_WIKI_SEARCH.format(q=q, n=int(limit)), _WIKI_TIMEOUT)
    if body is None:
        return []
    try:
        data = json.loads(body)
        return [h["title"] for h in data["query"]["search"] if h.get("title")]
    except Exception:
        return []


def wikipedia_summary(title: str) -> Optional[dict[str, Any]]:
    """Fetch (and cache) a Wikipedia page summary.

    Returns ``{title, extract, url}`` or None on a miss. The summary JSON is
    cached to ``data/web_cache/wikipedia/<title>.json`` (gitignored); a repeat
    lookup is served from disk with NO network hit. Mechanical I/O only."""
    if not title:
        return None
    # LOCAL store first (the HF 20231101.en dump) — no network at query time.
    try:
        from domains import wiki_local as _wl
        if _wl.present():
            s = _wl.summary(title)
            if s:
                return s
            if LOCAL_ONLY:
                return None   # local dump authoritative — a miss is a miss
    except Exception:
        pass
    if LOCAL_ONLY:
        return None
    path = _cache_path(title)
    if path.exists() and path.stat().st_size > 0:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return _summary_from_json(data)
        except Exception:
            pass  # corrupt cache — re-fetch below.

    t = urllib.parse.quote(title.replace(" ", "_"), safe="")
    body = _request(_WIKI_SUMMARY.format(title=t), _WIKI_TIMEOUT)
    if body is None:
        return None
    try:
        data = json.loads(body)
    except Exception:
        return None
    # A disambiguation / missing page has no usable extract.
    if not data.get("extract"):
        return None
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass
    return _summary_from_json(data)


def _summary_from_json(data: dict[str, Any]) -> Optional[dict[str, Any]]:
    extract = data.get("extract")
    if not extract:
        return None
    url = ""
    try:
        url = data["content_urls"]["desktop"]["page"]
    except Exception:
        url = data.get("title", "")
    return {"title": data.get("title", ""), "extract": extract, "url": url}


# ---------------------------------------------------------------------------
# arXiv — BEST-EFFORT (short timeout, graceful degrade, never blocks).
# ---------------------------------------------------------------------------


def arxiv_search(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """Search arXiv, returning ``[{title, abstract, url}]`` — BEST-EFFORT.

    Wrapped in a SHORT timeout; on timeout/failure returns [] and records the
    unreachable verdict (``arxiv_reachable()``). It NEVER blocks the agent's
    loop. When it does answer it parses the Atom feed for title/summary/id."""
    global _arxiv_last_reachable
    if not query:
        return []
    q = urllib.parse.quote(query)
    body = _request(_ARXIV_QUERY.format(q=q, n=int(limit)), _ARXIV_TIMEOUT)
    if body is None:
        _arxiv_last_reachable = False
        return []
    _arxiv_last_reachable = True
    return _parse_arxiv_atom(body.decode("utf-8", "replace"), limit)


def _parse_arxiv_atom(xml: str, limit: int) -> list[dict[str, Any]]:
    """Minimal Atom-feed parse (no XML dep): pull each <entry>'s title /
    summary / id. Best-effort string extraction — arXiv's feed is simple."""
    out: list[dict[str, Any]] = []
    for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
        block = m.group(1)

        def _field(tag: str) -> str:
            mm = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.S)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else ""

        title = _field("title")
        abstract = _field("summary")
        url = _field("id")
        if title:
            out.append({"title": title, "abstract": abstract, "url": url})
        if len(out) >= limit:
            break
    return out


def arxiv_reachable() -> Optional[bool]:
    """The last arXiv reachability verdict: True (answered), False (timed out /
    failed), or None (not yet tried). For honest reporting."""
    return _arxiv_last_reachable


# ---------------------------------------------------------------------------
# web_lookup — the unified entry the REFERENCE route calls.
# ---------------------------------------------------------------------------


def web_lookup(query: str, kind: str = "wikipedia"
               ) -> Optional[dict[str, Any]]:
    """The unified web reference entry: ``{source, text, url}`` or None.

    ``kind``:
      * "wikipedia" (default) — search Wikipedia for ``query``, take the best
        title, return its summary extract. The reliable path.
      * "arxiv"     — BEST-EFFORT arXiv search; on a hit returns the top
        paper's title + abstract; on timeout/failure falls through to None.
      * "both"      — try Wikipedia first, then arXiv if Wikipedia missed.

    Mechanical I/O; the decision to look up was made by the graph-resident
    epistemic-access stance. Returns the best extract for the caller to ground.
    """
    if not query:
        return None

    def _try_wikipedia() -> Optional[dict[str, Any]]:
        # The query may already be a title; try it directly, else search.
        summ = wikipedia_summary(query)
        if summ is None:
            titles = wikipedia_search(query, limit=3)
            if titles:
                summ = wikipedia_summary(titles[0])
        if summ is None:
            return None
        return {"source": "wikipedia", "text": summ["extract"],
                "url": summ["url"], "title": summ["title"]}

    def _try_arxiv() -> Optional[dict[str, Any]]:
        papers = arxiv_search(query, limit=1)
        if not papers:
            return None
        p = papers[0]
        return {"source": "arxiv", "text": p["abstract"] or p["title"],
                "url": p["url"], "title": p["title"]}

    if kind == "arxiv":
        return _try_arxiv()
    if kind == "both":
        return _try_wikipedia() or _try_arxiv()
    return _try_wikipedia()


# ---------------------------------------------------------------------------
# Grounding — translate a web hit into substrate mutations.
# ---------------------------------------------------------------------------


def ground_web_fact(world, concept_name: str, hit: dict[str, Any]) -> str:
    """Ground a web reference ``hit`` as graph data on ``world`` (a
    LanguageWorld). Mechanical translation, no decisions over graph state.

    Creates / enriches a Concept{name=concept_name} carrying the web extract
    as its ``definition`` (plus the source + url as provenance). Returns the
    concept name. The Concept is now referenceable by a later comprehension /
    QA turn (the extract IS the grounded definition)."""
    cid = world._get_or_create_concept(concept_name)
    try:
        attrs = dict(world.s.node(cid)["attrs"])
        if not attrs.get("definition"):
            world.s.set_attr(cid, "definition", hit.get("text", ""))
        if "source" not in attrs:
            world.s.set_attr(cid, "source", f"web:{hit.get('source', '')}")
        if hit.get("url") and not attrs.get("url"):
            world.s.set_attr(cid, "url", hit["url"])
        if hit.get("title") and not attrs.get("web_title"):
            world.s.set_attr(cid, "web_title", hit["title"])
    except Exception:
        pass
    return concept_name


# ---------------------------------------------------------------------------
# reference_lookup_for — the callable the epistemic_access resolver calls.
# ---------------------------------------------------------------------------


def reference_lookup_for(world, *, local_lookup=None, kind: str = "wikipedia"):
    """Build the ``reference_lookup(store, key)`` callable the conversation
    world hands to ``epistemic_access.resolve_banked_gaps``.

    Resolution order for a banked REFERENCE gap (knowing_where_vs_what — we
    hold the route, not the answer):
      1. LOCAL store first (WordNet / Wiktionary via ``local_lookup``, if the
         host supplied one) — cheapest, offline.
      2. WEB fall-through — ``web_lookup(key, kind)``. On a hit, GROUND the
         extract as a Concept definition (so a later turn can reference it) and
         return a short answer string for the banked-gap resolution to mint a
         KnownFact from. None on a miss (the gap stays pending — not faked).

    The returned string is the ANSWER the epistemic_access resolver records on
    the resolved PendingGap + the minted KnownFact. We return the Wikipedia
    title (the canonical entity name) as the answer, having grounded the full
    extract on the Concept — so "what is a rabbit?" resolves to a referenceable
    concept WITHOUT interrupting the audience."""
    def _lookup(store: str, key: str) -> Optional[str]:
        # 1. local store first (offline, cheap).
        if local_lookup is not None:
            try:
                val = local_lookup(store, key)
            except Exception:
                val = None
            if val:
                return str(val)
        # 2. web fall-through.
        hit = web_lookup(key, kind)
        if hit is None:
            return None
        ground_web_fact(world, key, hit)
        # The canonical title is the concise answer; the extract is grounded on
        # the Concept for deeper reference.
        return hit.get("title") or key

    return _lookup


__all__ = [
    "wikipedia_search", "wikipedia_summary",
    "arxiv_search", "arxiv_reachable",
    "web_lookup", "ground_web_fact", "reference_lookup_for",
]
