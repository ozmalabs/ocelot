"""reading_corpus — THE READING CORPUS, a WORLD ADAPTER (CLAUDE.md).

The style-manifold reader (domains/cross_text_prior.py) had only ever read a
handful of TEST fables. This adapter makes the jabberwock GENUINELY well-read: it
FETCHES real, multi-genre, public-domain literature from Project Gutenberg,
STRIPS the Gutenberg boilerplate, SPLITS each source into its natural reading
UNIT (a fable, a tale, a sonnet, a lyric, a verse), and SEQUENCES those units
into the reader's `accumulate_text` so the manifold fills with REAL diversity of
genre / register / period / voice.

A WORLD ADAPTER, nothing more. It does exactly two things (CLAUDE.md):

  * INGEST — fetch external bytes (public-domain text over HTTP), mechanically
    parse them into reading units, and hand each unit to the reader's public API
    (`cross_text_prior.accumulate_text`). The parsing is I/O-boundary work: split
    on the natural unit boundary (a fable's all-caps opening, a tale's title, a
    sonnet's numeral, a scripture verse). NO conditional over graph state decides
    WHAT to read — the sequence is fixed by the source list.
  * (the reader does the reading) — the manifold mint, the feature vector, the
    locate/persist all live in cross_text_prior; this module never reasons.

donkey = 0: the ONLY external I/O is FETCHING public-domain text (urllib, no
model, no API, no embedding). The raw texts are cached to `data/reading_corpus/`
(gitignored under `data/`) so a re-run is fully offline. No agent decisions, no
graph-state conditionals, no rule engine — just fetch, cache, split, feed.

  PYTHONPATH=runners/dsl/python:.:scripts python3 \
      scripts/jabberwock_reads_a_corpus.py
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

from domains import cross_text_prior as ctp

_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = _ROOT / "data" / "reading_corpus"      # gitignored (under data/)

_GUTENBERG_URL = "https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"

_START_MARK = "*** START OF THE PROJECT GUTENBERG EBOOK"
_END_MARK = "*** END OF THE PROJECT GUTENBERG EBOOK"


# --------------------------------------------------------------------------- #
#  FETCH + CACHE — mechanical host I/O. Fetch the raw text once, cache it, reuse.
# --------------------------------------------------------------------------- #
def fetch_raw(gid: int, *, force: bool = False, timeout: float = 60.0) -> str:
    """Fetch + cache one Gutenberg text by its ebook id. The raw text is cached to
    `data/reading_corpus/pg<gid>.txt` (gitignored); a re-run reads the cache with
    NO network hit. Mechanical I/O — fetch the bytes, write the file, return the
    text. `force` re-fetches."""
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    cache = CORPUS_DIR / f"pg{gid}.txt"
    if cache.exists() and not force:
        return cache.read_text(encoding="utf-8", errors="replace")
    url = _GUTENBERG_URL.format(gid=gid)
    with urllib.request.urlopen(url, timeout=timeout) as resp:   # public-domain text
        raw = resp.read().decode("utf-8", errors="replace")
    cache.write_text(raw, encoding="utf-8")
    return raw


def strip_boilerplate(raw: str) -> str:
    """Cut the Project Gutenberg header/footer, returning only the work body.
    Mechanical: keep the lines between the `*** START OF ...` and `*** END OF ...`
    markers (inclusive-exclusive). If a marker is absent, that end is left as-is."""
    lines = raw.splitlines()
    start = 0
    end = len(lines)
    for i, ln in enumerate(lines):
        if ln.startswith(_START_MARK):
            start = i + 1
            break
    for i in range(start, len(lines)):
        if lines[i].startswith(_END_MARK):
            end = i
            break
    return "\n".join(lines[start:end])


# --------------------------------------------------------------------------- #
#  Small mechanical text helpers (I/O-boundary parsing — NO agent cognition).
# --------------------------------------------------------------------------- #
def _blocks(text: str) -> list[str]:
    """Split into paragraph blocks on runs of blank lines."""
    out: list[str] = []
    cur: list[str] = []
    for ln in text.splitlines():
        if ln.strip():
            cur.append(ln)
        elif cur:
            out.append("\n".join(cur))
            cur = []
    if cur:
        out.append("\n".join(cur))
    return out


def _first_content_token(block: str) -> str:
    """The first alphabetic token of length >= 2 in a block (skips a bare 'A')."""
    for raw_tok in block.replace("\n", " ").split():
        tok = "".join(ch for ch in raw_tok if ch.isalpha())
        if len(tok) >= 2:
            return tok
    return ""


def _one_line(s: str) -> str:
    return " ".join(s.split())


def _after_marker(text: str, marker: Optional[str], *, nth: int = 1) -> str:
    """The text after the `nth` unindented line equal to `marker` (skips front
    matter such as a table of contents; a work that lists its parts in a contents
    block AND repeats them as body headers needs nth=2 for the body). No marker =>
    the whole text."""
    if not marker:
        return text
    lines = text.splitlines()
    seen = 0
    for i, ln in enumerate(lines):
        if ln == ln.lstrip() and ln.strip() == marker:
            seen += 1
            if seen >= nth:
                return "\n".join(lines[i + 1:])
    return text


def _is_caps_title(line: str) -> bool:
    """A stand-alone ALL-CAPS title line: unindented, has letters, no lowercase,
    short (a title, not a shouted sentence)."""
    if line != line.lstrip() or not line.strip():
        return False
    s = line.strip()
    return (any(c.isalpha() for c in s) and s == s.upper()
            and len(s) <= 60 and not s.endswith((".", ",", ";", ":")))


# --------------------------------------------------------------------------- #
#  SPLITTERS — one thin heuristic per source shape (I/O-boundary parsing). Each
#  returns [(label, unit_text)]; the caller caps + tags them. NO decision over
#  graph state — pure text segmentation on the natural unit boundary.
# --------------------------------------------------------------------------- #
def split_allcaps_body_fables(text: str, *, min_words: int = 20) -> list:
    """Aesop-style: the body of each fable OPENS with an ALL-CAPS word ('A DOG,
    crossing...', 'ONE hot day...'), while the preface + table of contents do not.
    A unit = a block whose first content token is ALL-CAPS; its label is the short
    title block just before it."""
    blocks = _blocks(text)
    out = []
    for i, blk in enumerate(blocks):
        first_line = blk.splitlines()[0] if blk.splitlines() else ""
        tok = _first_content_token(first_line)
        prose = any(c.islower() for c in first_line)     # a fable line, not a title
        if (len(tok) >= 2 and tok == tok.upper() and tok.isalpha() and prose):
            if len(blk.split()) < min_words:
                continue
            label = ""
            if i > 0:
                prev = _one_line(blocks[i - 1])
                if len(prev) <= 60:
                    label = prev
            out.append((label, blk))
    return out


def split_caps_title_units(text: str, *, start_after: Optional[str] = None,
                           min_words: int = 20) -> list:
    """Grimm/Blake-style: an ALL-CAPS unindented TITLE line delimits each unit; the
    unit body is the text up to the next such title. `start_after` skips front
    matter (jump past the body header, so the contents list is not read)."""
    body = _after_marker(text, start_after)
    lines = body.splitlines()
    heads = [i for i, ln in enumerate(lines) if _is_caps_title(ln)]
    out = []
    for j, hi in enumerate(heads):
        end = heads[j + 1] if j + 1 < len(heads) else len(lines)
        label = _one_line(lines[hi])
        unit = "\n".join(lines[hi + 1:end]).strip()
        if len(unit.split()) >= min_words:
            out.append((label, unit))
    return out


def split_numeral_units(text: str, *, min_words: int = 20) -> list:
    """Sonnet-style: a stand-alone Roman-numeral line ('I', 'II', ...) delimits
    each poem; the body is the lines up to the next numeral. The numeral is the
    label."""
    _ROMAN = set("IVXLCDM")
    lines = text.splitlines()
    heads = [i for i, ln in enumerate(lines)
             if ln.strip() and set(ln.strip()) <= _ROMAN and ln == ln.lstrip()]
    out = []
    for j, hi in enumerate(heads):
        end = heads[j + 1] if j + 1 < len(heads) else len(lines)
        label = lines[hi].strip()
        unit = "\n".join(lines[hi + 1:end]).strip()
        if len(unit.split()) >= min_words:
            out.append((label, unit))
    return out


def split_scripture_verses(text: str, *, start_after: Optional[str] = None,
                           start_nth: int = 1, stop_at: Optional[str] = None,
                           min_words: int = 12) -> list:
    """KJV-style: a verse OPENS with a 'chapter:verse ' prefix and runs (over
    wrapped lines) to the next such prefix or a blank line. `start_after` /
    `stop_at` bound the slice to ONE book (its unindented header line); `start_nth`
    selects the body header (a Bible lists its books once in a contents block and
    again as body headers, so the body slice is nth=2)."""
    body = _after_marker(text, start_after, nth=start_nth)
    if stop_at:
        lines = body.splitlines()
        for i, ln in enumerate(lines):
            if ln == ln.lstrip() and ln.strip() == stop_at:
                body = "\n".join(lines[:i])
                break

    def _is_ref(tok: str) -> bool:
        if ":" not in tok:
            return False
        a, b = tok.split(":", 1)
        return a.isdigit() and b.isdigit()

    out = []
    label = ""
    buf: list[str] = []

    def _flush():
        if buf and label:
            unit = _one_line(" ".join(buf))
            if len(unit.split()) >= min_words:
                out.append((label, unit))

    for blk in _blocks(body):
        first = blk.split()[:1]
        if first and _is_ref(first[0]):
            _flush()
            label = first[0]
            buf = [blk[len(first[0]):]]
        elif buf:
            _flush()
            buf = []
            label = ""
    _flush()
    return out


# --------------------------------------------------------------------------- #
#  THE SOURCE LIST — the curated multi-genre corpus. Each descriptor is fetch +
#  split params (I/O config), NOT agent state. Curated for GENRE / REGISTER /
#  PERIOD / VOICE diversity so the manifold fills with real spread.
# --------------------------------------------------------------------------- #
SOURCES: list[dict[str, Any]] = [
    {"key": "aesop", "gid": 21, "genre": "fable", "register": "plain",
     "period": "modern-translation",
     "split": lambda t: split_allcaps_body_fables(t), "cap": 70},
    {"key": "grimm", "gid": 2591, "genre": "tale", "register": "narrative-prose",
     "period": "19c",
     "split": lambda t: split_caps_title_units(
         t, start_after="THE BROTHERS GRIMM FAIRY TALES"), "cap": 25},
    {"key": "sonnet", "gid": 1041, "genre": "verse-sonnet",
     "register": "elizabethan", "period": "early-modern",
     "split": lambda t: split_numeral_units(t), "cap": 60},
    {"key": "blake", "gid": 1934, "genre": "verse-lyric", "register": "lyric",
     "period": "romantic",
     "split": lambda t: split_caps_title_units(
         t, start_after="SONGS OF INNOCENCE"), "cap": 45},
    {"key": "kjv-ruth", "gid": 10, "genre": "scripture", "register": "archaic",
     "period": "jacobean",
     "split": lambda t: split_scripture_verses(
         t, start_after="The Book of Ruth", start_nth=2,
         stop_at="The First Book of Samuel"), "cap": 85},
]


def load_units(*, sources: Optional[list] = None, force: bool = False) -> list:
    """FETCH + STRIP + SPLIT every source into a flat list of reading units. Each
    unit is {source, genre, register, period, label, text}. Mechanical I/O — no
    graph, no agent. Returns the corpus the reader will read."""
    srcs = sources if sources is not None else SOURCES
    units: list[dict[str, Any]] = []
    for src in srcs:
        raw = fetch_raw(src["gid"], force=force)
        body = strip_boilerplate(raw)
        pairs = src["split"](body)
        cap = src.get("cap")
        if cap is not None:
            pairs = pairs[:cap]
        for label, txt in pairs:
            units.append({"source": src["key"], "genre": src["genre"],
                          "register": src.get("register", ""),
                          "period": src.get("period", ""),
                          "label": label or src["key"], "text": txt})
    return units


def units_from_cache(*, sources: Optional[list] = None) -> list:
    """Split the CACHED raw texts only (no fetch) — for an offline/deterministic
    load. Raises if a source is not cached."""
    srcs = sources if sources is not None else SOURCES
    for src in srcs:
        if not (CORPUS_DIR / f"pg{src['gid']}.txt").exists():
            raise FileNotFoundError(f"pg{src['gid']}.txt not cached")
    return load_units(sources=srcs, force=False)


# --------------------------------------------------------------------------- #
#  READ — sequence the corpus into the reader's manifold. Pure sequencing: one
#  accumulate_text per unit (the reader mints the StylePoint). NO decision.
# --------------------------------------------------------------------------- #
def read_into_manifold(agent, units: list, *, label_key: str = "genre") -> list:
    """Read every unit into the style manifold via `cross_text_prior.
    accumulate_text` (one StylePoint per unit). The label carries the genre (or
    another tag) for explainability — the MECHANISM uses the feature vector, not
    the label. Mechanical sequencing, no conditional over graph state. Returns the
    StylePoint nodes."""
    pts = []
    for u in units:
        lbl = f"{u.get(label_key, '')}:{u.get('label', '')}".strip(":")
        pts.append(ctp.accumulate_text(agent, u["text"], label=lbl))
    return pts


def genre_of_label(label: str) -> str:
    """Read the genre tag back off a manifold label ('<genre>:<title>')."""
    return (label or "").split(":", 1)[0]


__all__ = ["CORPUS_DIR", "SOURCES", "fetch_raw", "strip_boilerplate",
           "split_allcaps_body_fables", "split_caps_title_units",
           "split_numeral_units", "split_scripture_verses",
           "load_units", "units_from_cache", "read_into_manifold",
           "genre_of_label"]
