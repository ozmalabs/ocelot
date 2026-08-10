"""Fine-grained PREPOSITION -> THEMATIC-ROLE mapping, derived from the
REFERENCE (VerbNet), replacing the coarse "spatial->location, everything-
else->none" mapping in ``function_word_reference``.

THE REFERENCE
=============
VerbNet (Kipper et al.) tags PP prepositions with thematic roles in its
frame syntax. Each verb class's ``FRAMES/FRAME/SYNTAX`` holds a sequence of
syntactic elements; a ``PREP`` element with a ``value`` (space-separated
prepositions) immediately followed by an ``NP`` element whose ``value`` is
the thematic role records (preposition -> role). Aggregating across all 429
classes gives a ``preposition -> Counter(role)`` table; the dominant MAPPED
role wins.

This is a WORLD-ADAPTER ingester (CLAUDE.md): it translates external
reference data (the VerbNet corpus, via nltk) into a cached table that the
``function_word_reference`` grounding reads. It makes NO new agent decision —
the prep->role mapping is read off VerbNet, not hand-authored, and the role
INVENTORY itself is taught as graph concepts (seeds/thematic_roles.json).

HONESTY — VerbNet noise
=======================
VerbNet thematic roles are VERB-FRAME-dependent, so the aggregated prep->role
table has noise. We take the dominant MAPPED role and document which
prepositions are CLEAN vs NOISY:

  CLEAN (dominant role is unambiguous, large margin):
    to    -> recipient   (Recipient 48, the plurality)
    with  -> instrument  (Instrument 46)
    from  -> source      (Source 23 + Material 13, both -> source)
    for   -> beneficiary  (Beneficiary 12; Theme 13 is the noise sink, demoted)
    about -> topic       (Topic 44)

  SPATIAL -> location (kept COARSE; VerbNet confirms several):
    on/in/at/under/over/below/above/near/inside/onto/into-as-location ->
    location. VerbNet's in/on/at skew to Theme (verb-frame-dependent NOISE),
    so for the SPATIAL subset we KEEP the existing coarse->location behaviour
    rather than trust VerbNet; VerbNet positively confirms under/over/through
    -> Location. into/onto are destinations in VerbNet but we treat them as
    spatial->location for the substrate's coarse location slot.

  NOISY (VerbNet plurality is a junk/uncovered role -> we drop or demote):
    of    -> Recipient/Theme noise; left UNMAPPED (no clean role).
    into/onto -> Oblique/Patient2 dominate; mapped to location (spatial).

ROLE-NAME -> SUBSTRATE INVENTORY
================================
VerbNet uses many role names; we collapse them to the taught substrate role
inventory (seeds/thematic_roles.json):
    Recipient            -> recipient
    Destination/Goal     -> goal
    Instrument           -> instrument
    Source               -> source
    Material             -> source
    Beneficiary          -> beneficiary
    Location/Initial_Location/Destination(spatial) -> location
    Theme/Theme1/Theme2  -> theme
    Patient/Patient1/Patient2 -> patient
    Cause                -> cause
    Asset                -> asset
    Extent               -> extent
    Topic                -> topic
    Agent/Actor/Actor1/Actor2 -> agent
    Co-Agent/Co-Patient/Co-Theme -> comitative
Roles with no inventory entry (Oblique, Predicate, Product, Attribute,
Stimulus, Value, ...) are treated as NOISE and skipped when picking the
dominant mapped role.

CANONICAL CHOICE — recipient vs goal: VerbNet's ``to`` is dominantly
Recipient (animate transfer), so we canonicalise ``to`` -> ``recipient``.
Destination (spatial endpoint) -> ``goal`` is kept distinct in the inventory
but no clean preposition selects it over recipient/location in the test bank.

es / ja CORRESPONDENCE
======================
VerbNet is English-only. For es/ja we map via the ENGLISH role: a small,
DOCUMENTED preposition<->preposition correspondence bridges the foreign
preposition to its English counterpart, then VerbNet's English prep->role
applies. This bridge is the only hand-authored part for es/ja and is stated
as such (a closed-class correspondence, ~6 entries per language):
    es: a->recipient/goal, de->source, con->instrument, para->beneficiary,
        en/sobre->location
    ja: case particles already carry role via the grounded grammar
        (function_word_reference._JA_PARTICLE_ROLE); the only addition here
        is reverse production (role -> particle).
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional


_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "verbnet"
_CACHE_PATH = _DATA_DIR / "prep_roles.json"


# ---------------------------------------------------------------------------
# VerbNet role name -> substrate role inventory. The taught inventory lives
# in seeds/thematic_roles.json; this is the mechanical name collapse.
# ---------------------------------------------------------------------------

_ROLE_MAP: dict[str, str] = {
    "recipient": "recipient",
    "destination": "goal",
    "goal": "goal",
    "instrument": "instrument",
    "source": "source",
    "initial_location": "source",
    "material": "source",
    "beneficiary": "beneficiary",
    "location": "location",
    "theme": "theme",
    "theme1": "theme",
    "theme2": "theme",
    "patient": "patient",
    "patient1": "patient",
    "patient2": "patient",
    "cause": "cause",
    "asset": "asset",
    "extent": "extent",
    "topic": "topic",
    "agent": "agent",
    "actor": "agent",
    "actor1": "agent",
    "actor2": "agent",
    "co-agent": "comitative",
    "co-patient": "comitative",
    "co-theme": "comitative",
}

# Roles that are the "noise sink" in the aggregated counts — present in many
# frames as a catch-all, so when a cleaner fine-grained role is also present
# for a preposition we prefer the fine-grained one. (theme is VerbNet's most
# promiscuous role; oblique/predicate/etc. have no inventory entry and are
# already dropped by _ROLE_MAP.) Demoted, NOT removed.
_NOISE_SINK_ROLES = {"theme"}

# Prepositions whose VerbNet plurality is WRONG/NOISE for the substrate's
# purposes — left UNMAPPED rather than trusting a tiny, mis-aggregated count.
# ``of`` is the clear case: VerbNet records a handful of Recipient/Theme frames
# (count <=6) but ``of`` is overwhelmingly a possession/partitive marker, not a
# thematic-role preposition. Mapping it would mis-tag "the leg of the table".
# Documented as VerbNet noise (honest); ``of`` gets no role.
_NOISE_PREPOSITIONS = {"of", "as"}

# The SPATIAL preposition class — kept COARSE -> location regardless of what
# VerbNet's verb-frame-dependent counts say (VerbNet's in/on/at skew to Theme,
# which is noise for these clearly spatial words). VerbNet positively confirms
# under/over/through/below -> Location; the rest are spatial by their lexical
# class. into/onto are VerbNet Destinations but we fold them into the coarse
# location slot the substrate uses.
_SPATIAL_PREPOSITIONS = {
    "en": {"on", "in", "at", "under", "above", "below", "over", "inside",
           "beside", "near", "onto", "into", "through", "within"},
    "es": {"en", "sobre", "bajo", "dentro", "encima", "debajo", "entre"},
}

# es / ja preposition <-> English-role bridge. DOCUMENTED hand-authored
# closed-class correspondence (the only non-VerbNet part for es; ~6 entries).
# es preposition -> substrate role, derived from the es<->en preposition
# correspondence plus VerbNet's English prep->role:
#   de  ~ en "from"/"of" -> source
#   con ~ en "with" -> instrument
#   para ~ en "for" -> beneficiary
#   en/sobre ~ en "on"/"in"/"over" -> location (spatial)
#
# HONEST es WRINKLE — the "personal a": Spanish ``a`` is GENUINELY AMBIGUOUS
# between the dative/recipient ("dar a Juan" = give to John) and the PERSONAL-A
# object marker that precedes an animate DIRECT OBJECT ("ama a Juan" = loves
# John, where Juan is the patient, NOT a recipient). Disambiguating needs the
# verb's argument structure (subcategorization), which the substrate doesn't
# yet ground. So ``a`` is LEFT UNMAPPED here (no role) — the noun it precedes
# falls to patient, preserving "ama a Juan" -> patient:John. Fine es roles come
# from de/con/para only until verb subcategorization is grounded. Documented,
# not faked.
_ES_PREP_ROLE = {
    "de": "source",
    "con": "instrument",
    "para": "beneficiary",
    "en": "location",
    "sobre": "location",
}

# Reverse: role -> preposition for PRODUCTION, per language. en derived from
# the VerbNet table (the dominant prep for each role); es from the bridge; ja
# from the grounded case particles (production reads those from the grammar,
# but we expose the mapping here for completeness).
_ROLE_PREP = {
    "en": {
        "recipient": "to",
        "goal": "to",
        "instrument": "with",
        "source": "from",
        "beneficiary": "for",
        "location": "on",
        "topic": "about",
        "comitative": "with",
    },
    "es": {
        "recipient": "a",
        "goal": "a",
        "instrument": "con",
        "source": "de",
        "beneficiary": "para",
        "location": "en",
    },
    "ja": {
        # Case particles (attach AFTER the noun); production emits these from
        # the grounded grammar, mirrored here for the role->marker reverse.
        "recipient": "に",
        "goal": "に",
        "source": "から",
        "location": "に",
        "agent": "が",
        "patient": "を",
        "topic": "は",
    },
}


# ---------------------------------------------------------------------------
# VerbNet extraction (cached). Walk every class's FRAMES/FRAME/SYNTAX; for
# each PREP element with a value followed by an NP element whose value is the
# thematic role, record (preposition -> role).
# ---------------------------------------------------------------------------


def _extract_from_verbnet() -> dict[str, dict[str, int]]:
    """Aggregate preposition -> Counter(role) across all VerbNet classes.
    Returns a plain {prep: {role: count}} dict (JSON-serialisable)."""
    from nltk.corpus import verbnet as vn  # local import — nltk is heavy

    prep_role: dict[str, Counter] = defaultdict(Counter)
    for cid in vn.classids():
        try:
            vnclass = vn.vnclass(cid)
        except Exception:
            continue
        for frame in vnclass.findall("FRAMES/FRAME"):
            syntax = frame.find("SYNTAX")
            if syntax is None:
                continue
            kids = list(syntax)
            for i, el in enumerate(kids):
                if el.tag != "PREP":
                    continue
                preps = (el.get("value") or "").strip()
                if not preps:
                    continue
                # The next NP element's value is the thematic role.
                role = None
                for j in range(i + 1, len(kids)):
                    if kids[j].tag == "NP":
                        role = kids[j].get("value")
                        break
                if not role:
                    continue
                for p in preps.split():
                    prep_role[p.lower()][role] += 1
    return {p: dict(c) for p, c in prep_role.items()}


def _dominant_mapped_role(role_counts: dict[str, int]) -> Optional[str]:
    """Pick the dominant SUBSTRATE role for a preposition's VerbNet role
    counts: map each VerbNet role through ``_ROLE_MAP``, aggregate by
    substrate role, then take the highest-count role — but demote the
    noise-sink (theme) so a cleaner fine-grained role wins when present.
    Returns None when no VerbNet role maps to the inventory."""
    agg: Counter = Counter()
    for vn_role, cnt in role_counts.items():
        sub = _ROLE_MAP.get(vn_role.lower())
        if sub is not None:
            agg[sub] += cnt
    if not agg:
        return None
    # Prefer the best NON-noise-sink role if one exists with any count.
    non_sink = {r: c for r, c in agg.items() if r not in _NOISE_SINK_ROLES}
    pool = non_sink if non_sink else agg
    return max(pool.items(), key=lambda kv: kv[1])[0]


def _build_table() -> dict[str, Any]:
    """Build the cached table: {raw: {prep: {role: count}},
    prep_role: {prep: substrate_role}}. en only (VerbNet is English)."""
    raw = _extract_from_verbnet()
    prep_role: dict[str, str] = {}
    for prep, counts in raw.items():
        # Documented VerbNet-noise prepositions get no role.
        if prep in _NOISE_PREPOSITIONS:
            continue
        # Spatial prepositions are forced to location (coarse), bypassing the
        # noisy VerbNet counts for these clearly-spatial words.
        if prep in _SPATIAL_PREPOSITIONS["en"]:
            prep_role[prep] = "location"
            continue
        role = _dominant_mapped_role(counts)
        if role is not None:
            prep_role[prep] = role
    # Ensure the spatial set is present even if a member never appeared in a
    # VerbNet PREP frame (e.g. "above").
    for prep in _SPATIAL_PREPOSITIONS["en"]:
        prep_role.setdefault(prep, "location")
    return {"raw": raw, "prep_role": prep_role}


# Module-level cache (loaded once).
_TABLE: Optional[dict[str, Any]] = None


def load_table(rebuild: bool = False) -> dict[str, Any]:
    """Load the cached VerbNet prep->role table, building + caching it on
    first use (or when ``rebuild``). Cache lives under data/verbnet/ which is
    gitignored. The nltk read is cheap but we cache per the task spec."""
    global _TABLE
    if _TABLE is not None and not rebuild:
        return _TABLE
    if _CACHE_PATH.exists() and not rebuild:
        try:
            with open(_CACHE_PATH) as f:
                _TABLE = json.load(f)
            return _TABLE
        except Exception:
            pass
    table = _build_table()
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_PATH, "w") as f:
            json.dump(table, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    _TABLE = table
    return _TABLE


# ---------------------------------------------------------------------------
# Public API — preposition -> role (comprehension) and role -> preposition
# (production). Per-language.
# ---------------------------------------------------------------------------


def preposition_role(prep: str, language: str) -> Optional[str]:
    """The fine-grained thematic role a preposition marks on its noun, in
    ``language``. en is VerbNet-derived (cached); es is the documented
    bridge; ja particles carry role via the grounded grammar (handled in
    function_word_reference) so this returns None for ja here. Returns None
    when the preposition has no clean role."""
    p = prep.lower()
    if language == "en":
        return load_table()["prep_role"].get(p)
    if language == "es":
        return _ES_PREP_ROLE.get(p)
    return None


def role_preposition(role: str, language: str) -> Optional[str]:
    """The preposition (or, for ja, the case particle) that marks a thematic
    role in ``language`` — the reverse map used by PRODUCTION. None when the
    role has no marker in that language."""
    return _ROLE_PREP.get(language, {}).get(role)


def is_spatial(prep: str, language: str) -> bool:
    """Whether ``prep`` is in the coarse spatial-preposition class (-> the
    location role) for ``language``."""
    return prep.lower() in _SPATIAL_PREPOSITIONS.get(language, set())


# Roles that fill a frame slot of their own (the fine-grained oblique roles)
# — as opposed to "location" which the comprehension stack already handled.
# Production emits a preposition for these; comprehension tags the PP noun.
FINE_ROLES = {"recipient", "goal", "instrument", "source", "beneficiary",
              "topic", "comitative", "cause", "asset", "extent"}


__all__ = [
    "preposition_role",
    "role_preposition",
    "is_spatial",
    "load_table",
    "FINE_ROLES",
]
