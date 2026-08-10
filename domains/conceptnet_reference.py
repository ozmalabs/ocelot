"""Mechanical ConceptNet → graph commonsense filler for the conversation world.

A world-adapter ingester, the SAME shape as ``dictionary_lexicon`` (WordNet),
``wiktionary_reference`` (kaikki) and ``morphology_reference`` (UniMorph): it
translates an external reference — ConceptNet 5.7, the crowd-sourced commonsense
knowledge graph — into substrate mutations, so the agent's CONJECTURE and
REASONING are upgraded with REAL commonsense facts (a dog IsA an animal; a knife
is UsedFor cutting; a cat is AtLocation a house) instead of a bare type prior.

Why ConceptNet, and where it fits the confidence continuum:
  * conjecture.py already turns a missing filler into a guess from the slot's
    type prior ("a location query expects a place"). That guess is GENERIC. With
    ConceptNet the SAME slot, anchored on a KNOWN entity, gets a CONCRETE guess
    grounded in commonsense: dog -> IsA animal/canine; dog -> AtLocation
    house/kennel. Still a CONJECTURE (low weight, basis="conceptnet IsA") — a
    weighted commonsense PRIOR, not ground truth — but no longer a bare prior.
  * epistemic_access.py routes an unresolved gap to a reference store. ConceptNet
    is added as such a store: a commonsense relation gap (where is a dog? what is
    a dog? what is a knife for?) is RESOLVABLE_VIA_ROUTE -> reference, and the
    off-path resolver grounds the ConceptNet fact as a KnownFact the order-N
    reasoner then chains over (cat IsA mammal IsA animal).

SOURCE (verified — no HF token needed). The HF ConceptNet mirrors are dead
loading-scripts and the live API is 502, but the canonical S3 dump is reachable:
  https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz
A TAB-separated edge file: ``uri \t /r/Relation \t /c/<lang>/start \t
/c/<lang>/end \t <json-metadata>``; the metadata JSON carries a crowd-sourced
``weight``. We stream the gz ONCE (498 MB — never resident), keep only
English-English edges in a chosen relation whitelist above a weight threshold,
normalize the nodes (strip /c/en/, drop a /n /a POS suffix, underscores->spaces)
and build an mmap'd SLAB. There is NO HF dependency and NO token in this env —
this is the direct S3 dump.

COLD-REFERENCE discipline (CLAUDE.md + the substrate's page_cache / mmap /
cache_aside concepts): the kept-triple slab is on disk; a lookup touches only the
OS page_cache working set, so query-time RSS is independent of the 498 MB corpus.
Grounded graph nodes are the HOT tier; the slab is consulted only on a miss.

Per CLAUDE.md this is allowed: the reference lookup is external I/O at the Python
world-adapter boundary (a graph Rule can't stream a 498 MB dump). It only GROUNDS
graph data (KnownFact + is_a / at_location edges) the existing graph-resident
rules + the conjecture / order-N machinery consume. There are NO agent decisions
over graph STATE in the ingester — only a mechanical relation whitelist + weight
threshold + node normalization over the (external) dump.

Honest scope / known residuals (stated plainly, not hidden):
  * ConceptNet is CROWD-SOURCED and NOISY. The weight threshold + relation
    whitelist cut a lot, but odd multi-word / typo nodes survive (the
    "t_shirts AtLocation drawer" kind). It is a WEIGHTED COMMONSENSE PRIOR, not
    ground truth — which is exactly why it lands in the CONJECTURE band, never as
    a high-confidence KnownFact. Reported, not hidden.
  * Coverage is whatever the dump holds for English; a missing concept returns []
    and the caller falls through exactly as before (purely additive).
"""
from __future__ import annotations

import gzip
import json
import os
import urllib.request
from pathlib import Path
from typing import Iterator, Optional

from . import reference_slab as slab

# Cache the dump under the gitignored data/ dir alongside the other references.
_ROOT = Path(__file__).resolve().parent.parent
_CACHE_DIR = _ROOT / "data" / "conceptnet"
_DUMP_URL = ("https://s3.amazonaws.com/conceptnet/downloads/2019/edges/"
             "conceptnet-assertions-5.7.0.csv.gz")

# The slab name. Keyed by the START concept -> a \x1f-joined list of
# "relation|target" values (multivalue), the same multivalue idiom the sibling
# slabs use.
_SLAB_NAME = "conceptnet_en"
_REL_SEP = "|"

# Relation whitelist — the USEFUL commonsense relations for conjecture + the
# order-N reasoner. Stored without the /r/ prefix. Everything else (RelatedTo,
# Synonym, EtymologicallyRelatedTo, the noisy bulk) is dropped at stream time.
_KEEP_RELATIONS: frozenset[str] = frozenset({
    "IsA", "AtLocation", "PartOf", "HasA", "HasProperty", "CapableOf",
    "UsedFor", "MadeOf", "HasSubevent", "Causes", "Desires",
    "MotivatedByGoal", "ReceivesAction", "SymbolOf", "DefinedAs",
    # Antonym: the low-trust crowd corroborator for figure-opposition grounding
    # (figure_grounding seed). Same weight floor (>=1.0) drops the junk tail
    # (poison/sweet 0.21, conservation/silence 0.20) before it enters the slab.
    "Antonym",
})

# Crowd-sourced weight threshold — cut the long noisy tail. ConceptNet weights
# are ~1.0 for a single annotator; >= 1.0 keeps the at-least-once-confirmed
# edges and drops the sub-1.0 fractional-confidence noise.
_WEIGHT_THRESHOLD: float = 1.0

# The English node prefix in the dump's /c/<lang>/ scheme.
_EN_PREFIX = "/c/en/"

# Per-process "tried to build" memo so we don't re-stat every call.
_BUILT = False


# ---------------------------------------------------------------------------
# Download — stream the gz to disk once (keep the gz; never the corpus in RAM).
# ---------------------------------------------------------------------------

def _dump_path() -> Path:
    return _CACHE_DIR / "assertions.csv.gz"


def _ensure_download(timeout: int = 900) -> Optional[Path]:
    """Download + cache the S3 assertions dump once. Streams the body to disk
    (we keep the gz; never the 498 MB decompressed corpus in RAM). Returns the
    cached path, or None if offline and no cache exists (caller degrades to
    None gracefully). No HF auth / token — the direct S3 dump."""
    path = _dump_path()
    if path.exists() and path.stat().st_size > 0:
        return path
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(_DUMP_URL,
                                     headers={"User-Agent": "curl/8"})
        tmp = path.with_suffix(".gz.part")
        with urllib.request.urlopen(req, timeout=timeout) as resp, \
                open(tmp, "wb") as out:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
        os.replace(tmp, path)
        return path
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Normalize — /c/en/black_hole/n -> "black hole". Mechanical, no decisions.
# ---------------------------------------------------------------------------

def _norm_concept(uri: str) -> Optional[str]:
    """Reduce a ``/c/en/...`` ConceptNet node URI to its plain surface, or None
    when the node is not English. Strips the /c/en/ prefix, drops a trailing
    POS-sense suffix (``/n``, ``/a``, ``/v``, ``/r`` and any sense disambiguator
    after it), and converts underscores to spaces. ``/c/en/black_hole/n`` ->
    ``black hole``; ``/c/en/dog`` -> ``dog``."""
    if not uri.startswith(_EN_PREFIX):
        return None
    body = uri[len(_EN_PREFIX):]
    # The first path segment after /c/en/ is the lemma; anything after the next
    # '/' is a POS / sense disambiguator we drop.
    seg = body.split("/", 1)[0]
    if not seg:
        return None
    return seg.replace("_", " ").strip()


def _rel_name(rel_uri: str) -> Optional[str]:
    """``/r/IsA`` -> ``IsA`` when whitelisted, else None."""
    if not rel_uri.startswith("/r/"):
        return None
    name = rel_uri[3:]
    return name if name in _KEEP_RELATIONS else None


def _edge_weight(meta: str) -> float:
    """Read the crowd-sourced ``weight`` off the edge's JSON metadata column.
    Defaults to 1.0 when absent / unparseable (so a metadata-less edge is kept
    at the threshold, not silently dropped)."""
    try:
        obj = json.loads(meta)
        w = obj.get("weight")
        return float(w) if w is not None else 1.0
    except Exception:
        return 1.0


# ---------------------------------------------------------------------------
# Build — stream the gz ONCE, yield (start_concept, "relation|target") pairs.
# ---------------------------------------------------------------------------

def _iter_pairs(path: Path) -> Iterator[tuple[str, str]]:
    """Stream the gz dump line by line and yield the kept (start, value) pairs.

    Keeps an edge only when: both nodes are ``/c/en/``, the relation is in the
    whitelist, and the weight >= the threshold. Never materialises the corpus —
    one line at a time, the architecture's one-time build cost; the QUERY path
    never streams. ``value`` = ``relation|target`` so the slab's multivalue list
    carries the relation alongside the target."""
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            # uri \t /r/Rel \t /c/en/start \t /c/en/end \t {json}
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            rel = _rel_name(parts[1])
            if rel is None:
                continue
            start = _norm_concept(parts[2])
            if start is None:
                continue
            end = _norm_concept(parts[3])
            if end is None or end == start:
                continue
            meta = parts[4] if len(parts) > 4 else ""
            if _edge_weight(meta) < _WEIGHT_THRESHOLD:
                continue
            yield start, f"{rel}{_REL_SEP}{end}"


def build_conceptnet_slab(timeout: int = 900, force: bool = False
                          ) -> Optional[int]:
    """Build (once) the ``conceptnet_en`` slab from the cached S3 dump.

    Streams the gz ONCE through the relation-whitelist + weight-threshold +
    English-only filter, building the start-concept -> ["relation|target", ...]
    slab. Returns the kept-triple count when it builds, the existing slab's count
    when already built, or None when the dump is unavailable offline (no cache).

    The kept-triple count is reported by counting pairs during the stream (the
    build buffers short tuples to sort — the one-time cost the architecture
    permits; the query path never does)."""
    path = _ensure_download(timeout=timeout)
    if path is None:
        # An already-built slab is still usable offline.
        if slab.slab_exists(_SLAB_NAME):
            return _kept_triple_count()
        return None

    # Fast path: slab newer than the dump -> skip the (multi-minute) re-stream.
    if not force and slab.slab_exists(_SLAB_NAME):
        keys_path = slab._paths(_SLAB_NAME)[0]
        try:
            if keys_path.stat().st_mtime >= path.stat().st_mtime:
                return _kept_triple_count()
        except OSError:
            pass

    # Count pairs as we stream (a closure so build_slab still drives the iter).
    kept = 0

    def _counted() -> Iterator[tuple[str, str]]:
        nonlocal kept
        for pair in _iter_pairs(path):
            kept += 1
            yield pair

    slab.build_slab(_SLAB_NAME, _counted(), source_path=path, force=force)
    return kept


def _kept_triple_count() -> int:
    """Total kept (start, relation, target) triples in the built slab = the sum
    of the per-key value-list lengths. A diagnostic read over the slab (the slab
    groups by start-concept, so len(slab) is the distinct-start count, not the
    triple count)."""
    sl = slab.open_slab(_SLAB_NAME)
    if sl is None:
        return 0
    total = 0
    n = len(sl)
    for i in range(n):
        try:
            _h, off, length = sl._record_at(i)
            _k, val = sl._read_value_record(off, length)
            total += len(val.split(slab._LIST_SEP)) if val else 0
        except Exception:
            continue
    return total


def _ensure_slab():
    """Build (once, lazily) and open the ConceptNet slab. Returns an open Slab
    or None when the dump is unavailable offline. Mirrors the sibling modules'
    lazy ``_ensure_slab``."""
    global _BUILT
    if not _BUILT:
        _BUILT = True
        if not slab.slab_exists(_SLAB_NAME):
            try:
                build_conceptnet_slab()
            except Exception:
                pass
    return slab.open_slab(_SLAB_NAME)


def ensure_built(timeout: int = 900) -> bool:
    """Build the slab if needed (the explicit one-time builder a script calls).
    Returns True if the slab exists afterwards."""
    try:
        build_conceptnet_slab(timeout=timeout)
    except Exception:
        pass
    return slab.slab_exists(_SLAB_NAME)


# ---------------------------------------------------------------------------
# Query — slab-backed lookups (mmap, cold). No in-RAM dict.
# ---------------------------------------------------------------------------

def conceptnet_relations(concept: str) -> list[tuple[str, str]]:
    """All kept (relation, target) pairs for ``concept`` (the START node).
    Empty on a miss (concept absent / slab not built). Normalizes the query the
    same way the keys were normalized (underscores->spaces, lowercased by the
    slab's casefold)."""
    if not concept:
        return []
    sl = _ensure_slab()
    if sl is None:
        return []
    key = concept.replace("_", " ").strip()
    out: list[tuple[str, str]] = []
    for v in sl.lookup_list(key):
        if not v or _REL_SEP not in v:
            continue
        rel, target = v.split(_REL_SEP, 1)
        if target:
            out.append((rel, target))
    return out


def _targets_for(concept: str, relation: str) -> list[str]:
    return [t for (r, t) in conceptnet_relations(concept) if r == relation]


def conceptnet_antonym(a: str, b: str) -> bool:
    """True iff (a,b) or (b,a) is a kept ConceptNet ``Antonym`` edge. Membership is
    boolean — the crowd weight floor (>=1.0) was applied at slab-build time, so the
    junk tail never appears here. Direction-symmetric (opposition is mutual)."""
    if not a or not b:
        return False
    a = a.replace("_", " ").strip().lower()
    b = b.replace("_", " ").strip().lower()
    if a == b:
        return False
    tb = {t.lower() for t in _targets_for(a, "Antonym")}
    if b in tb:
        return True
    ta = {t.lower() for t in _targets_for(b, "Antonym")}
    return a in ta


def is_a(concept: str) -> list[str]:
    """The ConceptNet IsA hypernyms of ``concept`` (dog -> [animal, canine, ...])."""
    return _targets_for(concept, "IsA")


def at_location(concept: str) -> list[str]:
    """The ConceptNet AtLocation places of ``concept`` (dog -> [house, kennel])."""
    return _targets_for(concept, "AtLocation")


def has_property(concept: str) -> list[str]:
    """The ConceptNet HasProperty attributes of ``concept``."""
    return _targets_for(concept, "HasProperty")


def used_for(concept: str) -> list[str]:
    """The ConceptNet UsedFor purposes of ``concept`` (knife -> [cut, ...])."""
    return _targets_for(concept, "UsedFor")


# The queried-slot -> ConceptNet relation map the conjecture upgrade reads: a
# 'location' query about a known entity is a ConceptNet AtLocation lookup; a type
# / identity query is an IsA lookup. Mechanical mapping, no decision over graph
# state.
SLOT_RELATION = {
    "location": "AtLocation",
    "agent": "IsA",
    "patient": "IsA",
    "topic": "IsA",
}


# ---------------------------------------------------------------------------
# The ingester — ground a concept's commonsense relations as graph data.
# ---------------------------------------------------------------------------

def ingest_conceptnet(world, concept: str,
                      relations: Optional[list[str]] = None,
                      max_per_relation: int = 3) -> int:
    """Ground ``concept``'s ConceptNet relations into ``world``'s graph as
    commonsense facts (the cache-aside HOT tier). Returns the number of grounded
    facts/edges (0 on a miss).

    Each kept (relation, target) becomes EITHER:
      * an ``is_a`` / ``at_location`` graph EDGE between Concept nodes (for the
        two relations the graph already has structural edges for — so the order-N
        reasoner + conjecture's analogy read them as edges), AND
      * a ``KnownFact`` node ``{event=<relation lowered>, agent=concept,
        patient=target, source="conceptnet", weight=...}`` so the order-N
        KnownFact chainer composes over them transitively (cat IsA mammal IsA
        animal).

    Cumulative + idempotent (skips a fact already grounded from conceptnet). Pure
    translation: the only conditional is over the (already-resolved) reference
    result + the relation whitelist, never over graph STATE decisions. HONEST:
    grounded at a commonsense weight (a prior), not as a confirmed truth — the
    KnownFact carries source="conceptnet" so the consumer can band it."""
    rels = conceptnet_relations(concept)
    if not rels:
        return 0
    wanted = set(relations) if relations else None
    grounded = 0
    # Group by relation so we can cap per-relation (cut the noisy tail per kind).
    by_rel: dict[str, list[str]] = {}
    for rel, target in rels:
        if wanted is not None and rel not in wanted:
            continue
        by_rel.setdefault(rel, [])
        if len(by_rel[rel]) < max_per_relation:
            by_rel[rel].append(target)

    for rel, targets in by_rel.items():
        event = rel.lower()
        for target in targets:
            # Idempotent: skip a conceptnet fact we already grounded.
            if _already_grounded(world, event, concept, target):
                continue
            # KnownFact (the order-N chainer reads these).
            try:
                world.s.add_node("KnownFact", {
                    "event": event,
                    "agent": concept,
                    "patient": target,
                    "language": "en",
                    "source": "conceptnet",
                    "origin": "conceptnet",
                })
                grounded += 1
            except Exception:
                pass
            # Structural edge for the two relations the graph models directly.
            edge = {"IsA": "is_a", "AtLocation": "at_location"}.get(rel)
            if edge is not None:
                try:
                    cid = world._get_or_create_concept(concept)
                    tid = world._get_or_create_concept(target)
                    world.s.add_edge(cid, edge, tid, None)
                except Exception:
                    pass
    return grounded


def reference_lookup(store: str, key: str) -> Optional[str]:
    """A world-adapter `reference_lookup(store, key)` callable for the
    epistemic_access off-path resolver (resolve_banked_gaps). For a banked
    ConceptNet reference gap, ``store`` is the ConceptNet store label and ``key``
    is the START concept; we return the first AtLocation place (the common
    'where is X' gap) else the first IsA hypernym, or None on a miss. Only the
    ConceptNet store is handled here (the dictionary route has its own resolver);
    returns None for any other store so the caller can chain resolvers."""
    if not key or "conceptnet" not in (store or "").lower():
        return None
    places = at_location(key)
    if places:
        return places[0]
    hyper = is_a(key)
    if hyper:
        return hyper[0]
    return None


def _already_grounded(world, event: str, agent: str, patient: str) -> bool:
    try:
        for nid in world.s.nodes("KnownFact"):
            a = world.s.node(nid)["attrs"]
            if (a.get("source") == "conceptnet" and a.get("event") == event
                    and a.get("agent") == agent and a.get("patient") == patient):
                return True
    except Exception:
        pass
    return False


__all__ = [
    "build_conceptnet_slab",
    "ensure_built",
    "conceptnet_relations",
    "is_a",
    "at_location",
    "has_property",
    "used_for",
    "ingest_conceptnet",
    "reference_lookup",
    "SLOT_RELATION",
    "_KEEP_RELATIONS",
    "_WEIGHT_THRESHOLD",
    "_SLAB_NAME",
]
