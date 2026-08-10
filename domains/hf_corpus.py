"""hf_corpus — THE WIDER CORPUS, a WORLD ADAPTER (CLAUDE.md).

The reading corpus (domains/reading_corpus.py) made the jabberwock well-read on
Project Gutenberg, but the manifold came out FABLE-DOMINATED (70 fables out of
268 units), so the UNIFORM cross-text register was already fable-weighted and
PROXIMITY beat it only THINLY (confirm 0.3625 vs 0.3572). The fix is a BALANCED,
LARGER, WIDER corpus: equal-ish units across MANY genres so no single register
swamps the uniform average, and a held-out from a NON-DOMINANT genre has to be
LOCATED (not handed to it by a lop-sided prior).

This adapter fetches that balanced multi-genre corpus from HUGGING FACE and feeds
it, unit by unit, to the style-manifold reader (domains/cross_text_prior). It is a
WORLD ADAPTER, nothing more — it does exactly two things (CLAUDE.md):

  * INGEST — stream rows from public HF datasets, mechanically extract each row's
    natural reading UNIT (a poem's verse, a story, a Wikipedia lead paragraph, a
    news lead, a review, an article lead), STRIP dataset boilerplate (datelines,
    escape artefacts), and hand each unit to the reader's public API
    (`cross_text_prior.accumulate_text`). The extraction is I/O-boundary parsing:
    pick a field, clean it, take the lead. NO conditional over graph state decides
    WHAT to read — the genre list is fixed config.
  * (the reader does the reading) — the manifold mint, the feature vector, the
    locate/persist all live in cross_text_prior; this module never reasons.

BALANCE is the whole point: the same `cap` per genre, so the corpus is roughly
uniform across register/formality/period and the UNIFORM register is no longer a
single genre in disguise. Genres span the register range on purpose: VERSE
(poetry — mood/short-line), PLAIN NARRATIVE (children's stories), ENCYCLOPEDIC
(Wikipedia — latinate/formal), JOURNALISTIC (news leads), CASUAL (reviews —
contractions/second-person), LONG-FORM JOURNALISM (article leads).

donkey = 0: the ONLY external I/O is FETCHING public text from Hugging Face (the
`datasets` library over HTTPS; the HF token is DATASET ACCESS only — NOT a model,
NO embedding, NO LM). The sampled units are cached to `data/hf_corpus/` (gitignored
under `data/`) so a re-run is fully offline. No agent decisions, no graph-state
conditionals, no rule engine — just fetch, cache, split, feed.

  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reads_wide.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Optional

from domains import cross_text_prior as ctp

_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = _ROOT / "data" / "hf_corpus"           # gitignored (under data/)
_ENV_PATH = Path("/home/matt/ozma/internal/.env")


# --------------------------------------------------------------------------- #
#  HF TOKEN — mechanical host config. Read the token from the .env and put it in
#  the process environment for the `datasets` library. NEVER logged / returned /
#  printed — the value only ever lives in os.environ for the fetch.
# --------------------------------------------------------------------------- #
def load_hf_token(*, env_path: Path = _ENV_PATH) -> bool:
    """Load HF_TOKEN from the .env into os.environ (for `datasets` /
    `huggingface_hub`). Returns True iff a non-empty token is now set. The token
    VALUE is never returned or printed — this is opaque host credential I/O."""
    if os.environ.get("HF_TOKEN"):
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", os.environ["HF_TOKEN"])
        return True
    if not env_path.exists():
        return bool(os.environ.get("HF_TOKEN"))
    for ln in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln.startswith("HF_TOKEN=") and len(ln) > len("HF_TOKEN="):
            val = ln.split("=", 1)[1].strip()
            if val:
                os.environ["HF_TOKEN"] = val
                os.environ["HUGGING_FACE_HUB_TOKEN"] = val
                return True
    return bool(os.environ.get("HF_TOKEN"))


# --------------------------------------------------------------------------- #
#  Mechanical text cleaning (I/O-boundary parsing — NO agent cognition).
# --------------------------------------------------------------------------- #
def _normalize(text: str) -> str:
    """Undo dataset escape artefacts + strip carriage returns. Mechanical: literal
    backslash-n / backslash-t escapes become spaces, CRs dropped, edges trimmed."""
    if not text:
        return ""
    return (text.replace("\\n", " ").replace("\\t", " ")
                .replace("\\'", "'").replace('\\"', '"')
                .replace("\r", "").strip())


def _collapse_ws(text: str) -> str:
    """Collapse runs of whitespace to single spaces (prose units — line breaks are
    not part of the natural prose unit). Verse KEEPS its line breaks (see below)."""
    return " ".join(text.split())


def _strip_dateline(text: str) -> str:
    """News/wire lead: drop the leading 'CITY (SOURCE) -- ' dateline if it sits at
    the very front. Mechanical prefix cut on the ' -- ' / '(CNN)' marker."""
    for marker in (" -- ", " – "):
        idx = text.find(marker)
        if 0 <= idx <= 90:
            return text[idx + len(marker):].lstrip()
    if text.startswith("(CNN)"):
        return text[len("(CNN)"):].lstrip(" -").lstrip()
    return text


def _lead_words(text: str, n: int) -> str:
    """The first `n` whitespace-tokens — a clean article/encyclopedia LEAD (the
    natural readable unit of a long body). Mechanical word truncation."""
    ws = text.split()
    return " ".join(ws[:n])


# --------------------------------------------------------------------------- #
#  PER-GENRE UNIT EXTRACTION — one thin field-pick + clean per dataset shape
#  (I/O-boundary parsing). Each maps a raw row -> the readable unit text (or "").
#  NO decision over graph state — pure mechanical field extraction.
# --------------------------------------------------------------------------- #
def _unit_verse(row: dict) -> str:
    # a poem: keep the line structure (verse), just de-escape + drop CRs.
    return _normalize(str(row.get("content") or "")).replace("\\r", "")


def _unit_story(row: dict) -> str:
    return _collapse_ws(_normalize(str(row.get("text") or "")))


def _unit_wiki_lead(row: dict) -> str:
    body = _collapse_ws(_normalize(str(row.get("text") or "")))
    return _lead_words(body, 120)


def _unit_news(row: dict) -> str:
    return _collapse_ws(_normalize(str(row.get("text") or "")))


def _unit_review(row: dict) -> str:
    return _lead_words(_collapse_ws(_normalize(str(row.get("text") or ""))), 220)


def _unit_article_lead(row: dict) -> str:
    body = _collapse_ws(_normalize(str(row.get("article") or "")))
    return _lead_words(_strip_dateline(body), 120)


# --------------------------------------------------------------------------- #
#  THE GENRE LIST — the balanced, multi-genre corpus. Each descriptor is stream +
#  extract config (I/O config), NOT agent state. Curated for REGISTER / FORMALITY
#  / PERIOD spread; the SAME `cap` per genre keeps the corpus BALANCED so no genre
#  dominates the uniform register.
# --------------------------------------------------------------------------- #
GENRES: list[dict[str, Any]] = [
    {"key": "poetry", "dataset": "merve/poetry", "config": None, "split": "train",
     "genre": "poetry", "register": "verse", "period": "mixed",
     "extract": _unit_verse, "min_words": 20, "max_words": 260},
    {"key": "stories", "dataset": "roneneldan/TinyStories", "config": None,
     "split": "train", "genre": "stories", "register": "plain-narrative",
     "period": "modern", "extract": _unit_story, "min_words": 30, "max_words": 300},
    {"key": "wikipedia", "dataset": "wikimedia/wikipedia", "config": "20231101.en",
     "split": "train", "genre": "wikipedia", "register": "encyclopedic",
     "period": "modern", "extract": _unit_wiki_lead, "min_words": 30,
     "max_words": 200},
    {"key": "news", "dataset": "ag_news", "config": None, "split": "train",
     "genre": "news", "register": "journalistic", "period": "modern",
     "extract": _unit_news, "min_words": 18, "max_words": 200},
    {"key": "reviews", "dataset": "Yelp/yelp_review_full", "config": None,
     "split": "train", "genre": "reviews", "register": "casual", "period": "modern",
     "extract": _unit_review, "min_words": 25, "max_words": 240},
    {"key": "articles", "dataset": "cnn_dailymail", "config": "3.0.0",
     "split": "train", "genre": "articles", "register": "long-journalism",
     "period": "modern", "extract": _unit_article_lead, "min_words": 40,
     "max_words": 200},
]


# --------------------------------------------------------------------------- #
#  FETCH + CACHE — mechanical host I/O. Stream a dataset, extract `cap` clean
#  units, cache them to `data/hf_corpus/<key>.json` (gitignored). A re-run reads
#  the cache with NO network hit.
# --------------------------------------------------------------------------- #
def _cache_path(key: str) -> Path:
    return CORPUS_DIR / f"{key}.json"


def fetch_genre(spec: dict, *, cap: int, force: bool = False,
                scan_limit: Optional[int] = None) -> list:
    """Stream one HF dataset + extract up to `cap` clean reading units, cached to
    `data/hf_corpus/<key>.json` (gitignored). A cached genre is returned from disk
    with NO network hit (unless `force`). Mechanical I/O — stream, extract, filter
    by word count, cache, return. Each unit is {label, text}. `scan_limit` caps how
    many raw rows we look at (default cap*40) so a sparse genre still terminates."""
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    cache = _cache_path(spec["key"])
    if cache.exists() and not force:
        cached = json.loads(cache.read_text(encoding="utf-8"))
        return cached[:cap]
    load_hf_token()
    from datasets import load_dataset          # lazy — cache path needs no datasets
    ds = load_dataset(spec["dataset"], spec.get("config"),
                      split=spec.get("split", "train"), streaming=True)
    extract: Callable[[dict], str] = spec["extract"]
    lo, hi = spec.get("min_words", 20), spec.get("max_words", 400)
    limit = scan_limit if scan_limit is not None else cap * 40
    units: list[dict[str, Any]] = []
    seen = set()
    for i, row in enumerate(ds):
        if i >= limit or len(units) >= cap:
            break
        txt = extract(row)
        if not txt:
            continue
        nw = len(txt.split())
        if nw < lo:
            continue
        if nw > hi:                              # truncate an outlier to the cap
            txt = " ".join(txt.split()[:hi])
        key = txt[:80]
        if key in seen:                          # skip exact-lead duplicates
            continue
        seen.add(key)
        label = (str(row.get("title") or row.get("poem name")
                     or row.get("author") or spec["key"]))[:48]
        units.append({"label": label, "text": txt})
    cache.write_text(json.dumps(units, ensure_ascii=False), encoding="utf-8")
    return units[:cap]


def load_units(*, genres: Optional[list] = None, cap: int = 150,
               force: bool = False) -> list:
    """FETCH + EXTRACT every genre into a flat, BALANCED list of reading units (the
    same `cap` per genre). Each unit is {source, genre, register, period, label,
    text}. Mechanical I/O — no graph, no agent. Returns the corpus the reader
    reads."""
    specs = genres if genres is not None else GENRES
    units: list[dict[str, Any]] = []
    for spec in specs:
        pairs = fetch_genre(spec, cap=cap, force=force)
        for p in pairs:
            units.append({"source": spec["key"], "genre": spec["genre"],
                          "register": spec.get("register", ""),
                          "period": spec.get("period", ""),
                          "label": p["label"] or spec["key"], "text": p["text"]})
    return units


def units_from_cache(*, genres: Optional[list] = None, cap: int = 150) -> list:
    """Return the CACHED units only (no network) — offline/deterministic load.
    Raises if a genre is not cached."""
    specs = genres if genres is not None else GENRES
    for spec in specs:
        if not _cache_path(spec["key"]).exists():
            raise FileNotFoundError(f"{spec['key']}.json not cached")
    return load_units(genres=specs, cap=cap, force=False)


def cache_present(*, genres: Optional[list] = None) -> bool:
    specs = genres if genres is not None else GENRES
    return all(_cache_path(s["key"]).exists() for s in specs)


def genre_counts(units: list) -> dict:
    """{genre -> #units} — the BALANCE read-off (are the genres equal-ish?)."""
    out: dict[str, int] = {}
    for u in units:
        out[u["genre"]] = out.get(u["genre"], 0) + 1
    return out


# --------------------------------------------------------------------------- #
#  READ — sequence the corpus into the reader's manifold. Pure sequencing: one
#  accumulate_text per unit (the reader mints the StylePoint). NO decision.
# --------------------------------------------------------------------------- #
def read_into_manifold(agent, units: list, *, label_key: str = "genre") -> list:
    """Read every unit into the style manifold via `cross_text_prior.
    accumulate_text` (one StylePoint per unit). The label carries the genre for
    explainability — the MECHANISM uses the feature vector, not the label.
    Mechanical sequencing, no conditional over graph state. Returns the
    StylePoint nodes."""
    pts = []
    for u in units:
        lbl = f"{u.get(label_key, '')}:{u.get('label', '')}".strip(":")
        pts.append(ctp.accumulate_text(agent, u["text"], label=lbl))
    return pts


def genre_of_label(label: str) -> str:
    """Read the genre tag back off a manifold label ('<genre>:<title>')."""
    return (label or "").split(":", 1)[0]


__all__ = ["CORPUS_DIR", "GENRES", "load_hf_token", "fetch_genre", "load_units",
           "units_from_cache", "cache_present", "genre_counts",
           "read_into_manifold", "genre_of_label"]
